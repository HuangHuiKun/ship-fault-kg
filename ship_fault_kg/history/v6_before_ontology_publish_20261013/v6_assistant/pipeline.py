"""Resume current-assistant curation without altering V5 or the running database.

Statements are authored in batches/*.py after the assistant has read the text.
This program validates, assembles and exports; it does NOT perform inference.
"""
import argparse
import collections
import copy
import hashlib
import importlib.util
import json
import re
import sqlite3
from pathlib import Path

from ..v5 import build as core
from ..v5.preprocess import Registry, hid, norm
from ..v5.schema import KINDS, RELATIONS, ENDPOINTS, CAUSAL
from .subsystems import add_grounded_leaf_links

KG = Path(__file__).resolve().parents[1]
BASE = KG / 'output/v5'
OUT = KG / 'output/v6_assistant'
BATCHES = Path(__file__).parent / 'batches'
VERSION = '6.0-assistant-in-progress'

def rows(path):
    with path.open(encoding='utf-8-sig') as f:
        return [json.loads(line) for line in f if line.strip()]

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def jsonl(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for row in data:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')

def registry():
    r = Registry()
    r.sources = {s['id']: s for s in rows(BASE / 'sources.jsonl')}
    for s in r.sources.values():
        for path in s['paths']:
            r.by_path[path] = s['id']; r.by_file[Path(path).name] = s['id']
    for p in rows(BASE / 'preprocessed_pages.jsonl'):
        r.pages[(p['source_id'], p['page_key'])] = (p['raw'], p['text'], p['locator'])
    r.passages = {p['id']: p for p in rows(BASE / 'passages.jsonl')}
    r.records = rows(BASE / 'dataset_records.jsonl')
    r.parameters = rows(BASE / 'parameter_dictionary.jsonl')
    return r

def batches():
    result = []
    for path in sorted(BATCHES.glob('batch_*.py')):
        spec = importlib.util.spec_from_file_location('curation_' + path.stem, path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        for record in module.RECORDS:
            result.append(dict(record, batch=path.name,
                batch_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return result

def baseline_fingerprint():
    return {name: hashlib.sha256((BASE/name).read_bytes()).hexdigest()
        for name in ('entities.jsonl', 'relationships.jsonl', 'assertions.jsonl',
                     'ship_fault_kg.sqlite', 'neo4j_snapshot_v5.json')}

def gate(record, r):
    """Structural/evidence gates do not replace semantic or expert review."""
    sid = record['source_id']
    if sid not in r.sources: raise ValueError('Unknown source ' + sid)
    if record.get('review') not in {'full_text','representative_excerpt'}:
        raise ValueError('Unrecorded source review')
    source_path = r.sources[sid]['paths'][0]
    if source_path.lower().endswith('.pdf') and record['review']=='full_text':
        page_keys={page for (s,page) in r.pages if s==sid}
        if set(record.get('reviewed_page_keys',[]))!=page_keys:
            raise ValueError('A full PDF review must explicitly list every read page key')
    if record['review']=='representative_excerpt':
        if not record.get('reviewed_excerpts'):raise ValueError('Missing actually read excerpts')
        for excerpt in record['reviewed_excerpts']:
            r.locate(source_path,excerpt['text'],excerpt.get('page'))
    actual = KG.parent / 'ship_fault_kg_data' / source_path
    if hashlib.sha256(actual.read_bytes()).hexdigest()!=r.sources[sid]['sha256']:
        raise ValueError('Raw source changed since V5 preprocessing: ' + source_path)
    if record.get('source_sha256') and record['source_sha256'] != r.sources[sid]['sha256']:
        raise ValueError('Source hash changed')
    if not record['facts'] and not record.get('exclusion_reason'):
        raise ValueError('A no-claim review must state its exclusion reason')
    for fact in record['facts']:
        a, rel, b, quote = fact[:4]
        if len(fact)>6:
            if record.get('case') or not re.fullmatch(r'[a-z0-9_-]{1,40}',fact[6]):
                raise ValueError('Evidence groups must be explicit safe IDs in non-case articles')
        ak, an, _ = core.classify(a); bk, bn, _ = core.classify(b)
        if not an or not bn or rel not in RELATIONS: raise ValueError('Invalid typed claim')
        if ak not in ENDPOINTS[rel][0] or bk not in ENDPOINTS[rel][1]:
            raise ValueError(f'Invalid endpoints: {ak} {rel} {bk}')
        if rel in {'INSTANCE_OF', 'DOCUMENTED_BY', 'IS_SUBSYSTEM_OF', 'PRECEDES'}:
            raise ValueError('This batch format reserves index/time edges for explicit rules')
        r.locate(source_path, quote, fact[5] if len(fact)>5 else record.get('page'))
        if record['review']=='representative_excerpt' and not any(
                norm(quote) in norm(x['text']) for x in record['reviewed_excerpts']):
            raise ValueError('Claim evidence is outside the actually reviewed excerpts')
        if len(norm(quote)) < 8: raise ValueError('Insufficient quote context')
    fact_tokens={core.classify(t)[:2] for f in record['facts'] for t in (f[0],f[2])}
    for prop in record.get('parameter_properties',[]):
        kind,name,_=core.classify(prop['token'])
        if kind!='Parameter' or (kind,name) not in fact_tokens:
            raise ValueError('Parameter property must annotate a grounded claim endpoint')
        if not prop.get('unit') or prop['unit'] not in norm(prop['quote']):
            raise ValueError('Parameter unit must occur literally in its evidence quote')
        if prop.get('quantity') not in {'长度','压力','温度','角度','流量','转速','浓度'}:
            raise ValueError('Unknown physical quantity')
        r.locate(source_path,prop['quote'],record.get('page'))

def assemble():
    before = baseline_fingerprint(); r = registry(); records = batches()
    # Hydrate the existing V5 graph, preserving every baseline ID and property.
    b = core.Builder(r)
    b.nodes = {n['id']: copy.deepcopy(n) for n in rows(BASE/'entities.jsonl')}
    b.edges = {e['id']: copy.deepcopy(e) for e in rows(BASE/'relationships.jsonl')}
    b.assertions = {a['id']: copy.deepcopy(a) for a in rows(BASE/'assertions.jsonl')}
    b.provenance = {(e['source'], e['props']['source_id']) for e in b.edges.values()
                    if e['relation']=='DOCUMENTED_BY'}
    core.VERSION = VERSION
    audits = []; added_claims = []; seen = set()
    for record in records:
        gate(record, r)
        sid = record['source_id']
        if sid in seen: raise ValueError('Duplicate full source review: ' + sid)
        seen.add(sid)
        if not record['facts']:
            audits.append(dict(source_id=sid,title=record['title'],
                locator=r.sources[sid]['paths'][0],review_status='assistant_no_claim',
                batch=record['batch'],source_sha256=r.sources[sid]['sha256'],
                review_extent=record['review'],
                reviewed_excerpts=record.get('reviewed_excerpts',[]),
                authored_claims=0,total_added_assertions=0,
                exclusion_reason=record['exclusion_reason'],expert_review='not_performed'))
            continue
        loc = r.sources[sid]['paths'][0]
        prefix = 'case:assistant:' if record.get('case') else 'article:assistant:'
        scope = prefix + sid
        ff=record['facts'][0]
        first = r.locate(loc, ff[3], ff[5] if len(ff)>5 else record.get('page'))
        eq = b.node('Equipment', record['equipment'], applicability=record['scope'])
        system = b.node('System', core.SYS[record['system']], system_level='functional_subsystem')
        b.documented(eq, first, scope)
        b.edge(eq, 'SERVES_SYSTEM', system, first, scope,
               nature='functional_classification', applicability=record['scope'])
        entry = dict(equipment=eq)
        if record.get('case'):
            case = b.node('Case', record['title'], scope=scope,
                case_code='X' + f'{len(audits)+1:03d}', case_id=scope,
                vessel_identity_status='按二手文章记录；不冒充官方事故调查',
                applicability=record['scope'])
            b.documented(case, first, scope)
            b.edge(case, 'INVOLVES', eq, first, scope, nature='asset_index')
            entry['case'] = case
        b.case_equipment[scope] = entry
        count_before = len(b.assertions)
        direct_ids = []
        for i, fact in enumerate(record['facts']):
            a, rel, target, quote = fact[:4]
            certainty = fact[4] if len(fact)>4 else 'secondary_stated'
            fact_scope=scope+':group:'+fact[6] if len(fact)>6 else scope
            if fact_scope!=scope:b.case_equipment[fact_scope]=entry
            p = r.locate(loc, quote, fact[5] if len(fact)>5 else record.get('page'))
            nature = ('source_recommendation' if a.startswith('A|') else
                      'source_check' if a.startswith('C|') else 'secondary_source_statement')
            old_ids = set(b.assertions)
            b.declaration(a, rel, target, p, fact_scope, certainty, nature, record['scope'])
            new_ids = set(b.assertions) - old_ids
            ids = [aid for aid in new_ids if b.assertions[aid]['statement_nature']==nature]
            if len(ids)!=1: raise ValueError(f'Duplicate/unexpected authored claim: {sid}:{i}')
            aid = ids[0]; direct_ids.append(aid)
            claim = b.assertions[aid]
            claim.update(extraction_actor='current_chat_assistant',
                extraction_method='current_session_source_reading',
                extraction_batch=record['batch'], semantic_review='assistant_only',
                expert_review='not_performed')
            b.edges[hid('edge',aid)]['props'].update(
                extraction_actor='current_chat_assistant',
                extraction_batch=record['batch'], semantic_review='assistant_only')
            added_claims.append(dict(source_id=sid, subject=a, relation=rel,
                object=target, quote=p['text'], assertion_id=aid, passage_id=p['id'],
                certainty=certainty, scope_id=fact_scope, batch=record['batch'],
                source_sha256=r.sources[sid]['sha256']))
        for prop in record.get('parameter_properties',[]):
            nid=b.token(prop['token']);p=r.locate(loc,prop['quote'],record.get('page'))
            props=b.nodes[nid]['props']
            evidence=dict(unit=prop['unit'],quantity=prop['quantity'],source_id=sid,
                passage_id=p['id'],quote=p['text'],source_sha256=r.sources[sid]['sha256'],
                applicability=record['scope'],semantic_review='assistant_only',
                expert_review='not_performed')
            evidence_records=json.loads(props.get('source_property_evidence_json','[]'))
            evidence_records.append(evidence)
            # Neo4j properties cannot contain nested dictionaries. Retain the
            # full structured evidence as JSON text, also available in SQLite.
            props['source_property_evidence_json']=json.dumps(evidence_records,ensure_ascii=False)
            # Never overwrite a baseline or earlier unit. Numeric limits remain
            # in source context and are not made into universal node thresholds.
            if not props.get('unit'):props['unit']=prop['unit']
            if not props.get('quantity'):props['quantity']=prop['quantity']
        audits.append(dict(source_id=sid, title=record['title'], locator=loc,
            review_status=('assistant_full_text_review' if record['review']=='full_text' else
                           'assistant_excerpt_review'), batch=record['batch'],
            batch_sha256=record['batch_sha256'], source_sha256=r.sources[sid]['sha256'],
            reviewed_characters=(sum(len(t) for (s,_),(raw,t,_) in r.pages.items() if s==sid)
                if record['review']=='full_text' else sum(len(x['text']) for x in record['reviewed_excerpts'])),
            review_extent=record['review'],
            reviewed_excerpts=record.get('reviewed_excerpts',[]),
            authored_claims=len(direct_ids), parameter_property_records=len(record.get('parameter_properties',[])),
            total_added_assertions=len(b.assertions)-count_before,
            scope=record['scope'], cautions=record.get('notes',''),
            expert_review='not_performed'))
    detailed_system_matches = add_grounded_leaf_links(b, r)
    report = b.validate()
    for node in b.nodes.values():
        node['props']['graph_version'] = VERSION
        scope=node['props'].get('scope_id','')
        case=b.case_equipment.get(scope,{}).get('case')
        if case and node['props']['entity_level']=='context_record':
            code=b.nodes[case]['props']['case_code']
            node['props']['display_name']=node['name']+'〔'+code+'〕'
            node['props']['case_code']=code
    for edge in b.edges.values(): edge['props']['graph_version'] = VERSION
    nodes = sorted(b.nodes.values(), key=lambda n:n['id'])
    edges = sorted(b.edges.values(), key=lambda e:e['id'])
    report.update(graph_version=VERSION, status='partial_expansion_not_all_sources_reviewed',
        baseline=dict(version='5.0', nodes=1356, edges=3343),
        growth=dict(nodes=round(len(nodes)/1356,3),edges=round(len(edges)/3343,3)),
        new_direct_knowledge_statements=len(added_claims),
        current_assistant_full_documents_reviewed=sum(x['review']=='full_text' for x in records),
        current_assistant_sources_reviewed=len(audits),
        total_graph_sources=len({e['props']['source_id'] for e in edges}),
        local_model_calls=0, external_model_api_calls=0, published_to_neo4j=False,
        schema_extensions=['extraction_actor','extraction_batch','semantic_review','source_property_evidence_json'],
        duplicate_claim_policy='dedup within same evidence scope; separate evidence may support same triple',
        detailed_system_classifications=len(detailed_system_matches),
        detailed_system_classification_method='literal equipment-name rule; ontology index only, not a source causal claim')
    baseline_direct=sum(a['statement_nature'].startswith(('source_','secondary_','migration_'))
                        for a in rows(BASE/'assertions.jsonl'))
    report.update(explicit_knowledge_statements=baseline_direct+len(added_claims),
                  baseline_direct_knowledge_statements=baseline_direct,
                  new_parameter_property_records=sum(len(r.get('parameter_properties',[])) for r in records),
                  corpus_new_articles=len(records),
                  excluded_legacy_statements=json.loads((BASE/'build_report.json').read_text(encoding='utf-8')).get('excluded_legacy_statements',0))
    graph_used = {e['props']['source_id'] for e in edges}
    old_used = {e['props']['source_id'] for e in rows(BASE/'relationships.jsonl')}
    audit_ids = {a['source_id'] for a in audits}
    full_review_ids = {x['source_id'] for x in records if x['review']=='full_text'}
    audit_status={a['source_id']:a['review_status'] for a in audits}
    coverage = [dict(source_id=s['id'],title=s['title'],paths=s['paths'],
        status=audit_status[s['id']] if s['id'] in audit_ids else
        'baseline_selected_evidence_only' if s['id'] in old_used else 'pending_assistant_review',
        used_in_graph=s['id'] in graph_used) for s in r.sources.values()]
    original_passages = rows(BASE/'passages.jsonl')
    bound={a['passage_id'] for a in b.assertions.values()}
    pcoverage = [dict(passage_id=p['id'],source_id=p['source_id'],
        source_text_reviewed=p['source_id'] in full_review_ids,
        directly_bound_to_graph=p['id'] in bound,
        exact_quote=bool(p.get('exact_quote'))) for p in original_passages]
    report.update(source_review_counts=dict(collections.Counter(c['status'] for c in coverage)),
        original_passages_total=len(original_passages),
        original_fixed_chunks_reviewed=sum(p['source_text_reviewed'] and not p['exact_quote'] for p in pcoverage),
        used_exact_passages=len({a['passage_id'] for a in b.assertions.values()}))
    snapshot=dict(database='shipfaultkg',nodes=[dict(id=n['id'],labels=[n['kind'],'ShipKG'],
        properties=dict(n['props'],id=n['id'],kind=n['kind'],name=n['name'],aliases=n['aliases'])) for n in nodes],
        edges=[dict(id=e['id'],source=e['source'],relation=e['relation'],target=e['target'],properties=e['props']) for e in edges])
    jsonl(OUT/'entities.jsonl', nodes); jsonl(OUT/'relationships.jsonl', edges)
    jsonl(OUT/'assertions.jsonl', b.assertions.values())
    jsonl(OUT/'authored_statements.jsonl', added_claims)
    jsonl(OUT/'reviewed_sources.jsonl', audits)
    jsonl(OUT/'source_review_coverage.jsonl', coverage)
    jsonl(OUT/'original_passage_review_coverage.jsonl', pcoverage)
    jsonl(OUT/'sources.jsonl', r.sources.values()); jsonl(OUT/'passages.jsonl', r.passages.values())
    save(OUT/'neo4j_snapshot.json', snapshot)
    path=OUT/'ship_fault_kg.staging.sqlite'; conn=sqlite3.connect(path)
    conn.executescript('DROP TABLE IF EXISTS nodes;DROP TABLE IF EXISTS edges;DROP TABLE IF EXISTS assertions;DROP TABLE IF EXISTS sources;DROP TABLE IF EXISTS passages;DROP TABLE IF EXISTS dataset_records;DROP TABLE IF EXISTS parameter_dictionary;'
        'CREATE TABLE nodes(id TEXT PRIMARY KEY,kind TEXT,name TEXT,aliases TEXT,props TEXT);'
        'CREATE TABLE edges(id TEXT PRIMARY KEY,source TEXT,relation TEXT,target TEXT,assertion_id TEXT,props TEXT);'
        'CREATE TABLE assertions(id TEXT PRIMARY KEY,source_id TEXT,passage_id TEXT,scope_id TEXT,data TEXT);'
        'CREATE TABLE sources(id TEXT PRIMARY KEY,data TEXT);CREATE TABLE passages(id TEXT PRIMARY KEY,source_id TEXT,text TEXT,data TEXT);'
        'CREATE TABLE dataset_records(id TEXT PRIMARY KEY,data TEXT);CREATE TABLE parameter_dictionary(id TEXT PRIMARY KEY,data TEXT);'
        'CREATE INDEX node_kind ON nodes(kind);CREATE INDEX edge_source ON edges(source);CREATE INDEX edge_target ON edges(target);')
    dump=lambda v:json.dumps(v,ensure_ascii=False)
    conn.executemany('INSERT INTO nodes VALUES(?,?,?,?,?)',[(n['id'],n['kind'],n['name'],dump(n['aliases']),dump(n['props'])) for n in nodes])
    conn.executemany('INSERT INTO edges VALUES(?,?,?,?,?,?)',[(e['id'],e['source'],e['relation'],e['target'],e['props']['assertion_id'],dump(e['props'])) for e in edges])
    conn.executemany('INSERT INTO assertions VALUES(?,?,?,?,?)',[(a['id'],a['source_id'],a['passage_id'],a['scope_id'],dump(a)) for a in b.assertions.values()])
    conn.executemany('INSERT INTO sources VALUES(?,?)',[(s['id'],dump(s)) for s in r.sources.values()])
    conn.executemany('INSERT INTO passages VALUES(?,?,?,?)',[(p['id'],p['source_id'],p['text'],dump(p)) for p in r.passages.values()])
    for table, rr in [('dataset_records',r.records),('parameter_dictionary',r.parameters)]:
        conn.executemany(f'INSERT INTO {table} VALUES(?,?)',[(p['record_id'],dump(p)) for p in rr])
    conn.commit(); report['sqlite_integrity']=conn.execute('PRAGMA integrity_check').fetchone()[0]
    conn.close(); path.replace(OUT/'ship_fault_kg.sqlite')
    if report['sqlite_integrity']!='ok': raise ValueError('SQLite integrity check failed')
    if baseline_fingerprint()!=before: raise ValueError('V5 files changed during build')
    report['baseline_files_unchanged']=True; save(OUT/'baseline_fingerprints.json',before)
    save(OUT/'build_report.json', report)
    print(json.dumps(report,ensure_ascii=False,indent=2))

def read_sources(start, limit, maxchars, focus='', include_baseline=False):
    r=registry(); reviewed={x['source_id'] for x in batches()}
    used={e['props']['source_id'] for e in rows(BASE/'relationships.jsonl')}
    selected=[dict(source_id=s,locator=loc,text=t) for (s,page),(raw,t,loc) in r.pages.items()
        if s not in reviewed and (include_baseline or s not in used)
        and loc.endswith('.md') and 350<len(t)<=maxchars
        and (bool(re.search(focus,loc)) if focus else
             any(w in loc for w in ('故障','原因','汽蚀','烧','失电','漏','磨损','报警','振动','轴承','诊断')))]
    print(json.dumps(selected[start:start+limit],ensure_ascii=False,indent=2))

def read_passages(start,limit,source_id=''):
    """Display evidence for assistant reading; never mark it reviewed automatically."""
    r=registry();reviewed={b['source_id'] for b in batches()}
    selected=[pp for pp in rows(BASE/'passages.jsonl') if not pp.get('exact_quote') and
              (pp['source_id']==source_id if source_id else pp['source_id'] not in reviewed)]
    displayed=[]
    for pp in selected[start:start+limit]:
        page=str(pp['page']) if pp['page'] is not None else ''
        raw,text,loc=r.pages[(pp['source_id'],page)]
        begin=pp['normalized_start'];end=pp['normalized_end']
        displayed.append(dict(source_id=pp['source_id'],passage_id=pp['id'],
            title=r.sources[pp['source_id']]['title'],locator=loc,page=pp['page'],
            text=pp['text'],preceding_context=text[max(0,begin-180):begin],
            following_context=text[end:end+180],automatically_marked_reviewed=False))
    print(json.dumps(displayed,ensure_ascii=False,indent=2))

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','read','read-passages'])
    p.add_argument('--start',type=int,default=0);p.add_argument('--limit',type=int,default=3)
    p.add_argument('--maxchars',type=int,default=2200)
    p.add_argument('--focus',default='');p.add_argument('--include-baseline',action='store_true')
    p.add_argument('--source-id',default='');a=p.parse_args()
    if a.command=='read':read_sources(a.start,a.limit,a.maxchars,a.focus,a.include_baseline)
    elif a.command=='read-passages':read_passages(a.start,a.limit,a.source_id)
    else:assemble()

if __name__=='__main__':main()
