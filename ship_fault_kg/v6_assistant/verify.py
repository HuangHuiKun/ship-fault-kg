"""Read-only graph checks plus negative evidence/type tests, not expert review."""
import copy
import hashlib
import json
import sqlite3
from . import pipeline as p
from .core import retrieve as probe

INDEX_RELATIONS={'DOCUMENTED_BY','INSTANCE_OF','INVOLVES','HAS_CASE','APPLIES_TO',
                 'OCCURS_ON','SERVES_SYSTEM','IS_SUBSYSTEM_OF','IS_A'}

def main():
    results=[]
    def check(name,condition,detail=None):
        results.append(dict(name=name,passed=bool(condition),detail=detail))
    registry=p.registry();records=p.batches()
    nodes=p.rows(p.OUT/'entities.jsonl');edges=p.rows(p.OUT/'relationships.jsonl')
    claims=p.rows(p.OUT/'assertions.jsonl');authored=p.rows(p.OUT/'authored_statements.jsonl')
    report=json.loads((p.OUT/'build_report.json').read_text(encoding='utf-8'))
    node_map={n['id']:n for n in nodes};claim_map={c['id']:c for c in claims}
    check('unique_entity_ids',len(node_map)==len(nodes))
    check('unique_edge_ids',len({e['id'] for e in edges})==len(edges))
    check('unique_assertion_ids',len(claim_map)==len(claims))
    check('every_edge_has_entities_and_assertion',all(e['source'] in node_map and
          e['target'] in node_map and e['props']['assertion_id'] in claim_map for e in edges))
    check('valid_relation_endpoints',all(e['relation'] in p.RELATIONS and
        node_map[e['source']]['kind'] in p.ENDPOINTS[e['relation']][0] and
        node_map[e['target']]['kind'] in p.ENDPOINTS[e['relation']][1] for e in edges))
    failures=[]
    for record in records:
        try:p.gate(record,registry)
        except Exception as exc:failures.append(str(exc))
    check('all_authored_records_pass_raw_source_quote_and_type_gates',not failures,failures)
    check('authored_statement_count',len(authored)==sum(len(r['facts']) for r in records)
          ==report['new_direct_knowledge_statements'])
    check('all_authored_claims_mark_assistant_not_expert',all(
        claim_map[a['assertion_id']].get('extraction_actor')=='current_chat_assistant' and
        claim_map[a['assertion_id']]['expert_review']=='not_performed' for a in authored))
    check('all_authored_quotes_match_exported_claim',all(
        claim_map[a['assertion_id']]['quote']==a['quote'] and
        claim_map[a['assertion_id']]['source_id']==a['source_id'] for a in authored))
    check('baseline_nodes_preserved',all(n['id'] in node_map for n in p.rows(p.BASE/'entities.jsonl')))
    check('baseline_edges_preserved',{e['id'] for e in p.rows(p.BASE/'relationships.jsonl')}
          <= {e['id'] for e in edges})
    check('baseline_files_unchanged_since_build',p.baseline_fingerprint()==
        json.loads((p.OUT/'baseline_fingerprints.json').read_text(encoding='utf-8')))
    archive=p.KG/'history/v5_before_v6_expansion_20261013'
    manifest=json.loads((archive/'backup_manifest.json').read_text(encoding='utf-8'))
    bad_archive=[]
    for item in manifest['files']:
        path=archive/item['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
            bad_archive.append(item['path'])
    check('archived_v5_files_match_manifest',not bad_archive,
          dict(checked_files=len(manifest['files']),mismatches=bad_archive))
    check('archived_v5_graph_matches_current_v5',all(
        (archive/'output/v5'/name).is_file() and
        hashlib.sha256((archive/'output/v5'/name).read_bytes()).hexdigest()==sha
        for name,sha in p.baseline_fingerprint().items()))
    conn=sqlite3.connect(f'file:{(p.OUT/"ship_fault_kg.sqlite").as_posix()}?mode=ro',uri=True)
    check('sqlite_integrity',conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok')
    check('sqlite_export_counts_agree',all(conn.execute('SELECT count(*) FROM '+table).fetchone()[0]==count
        for table,count in [('nodes',len(nodes)),('edges',len(edges)),('assertions',len(claims))]))
    check('sqlite_entity_values_agree',all(json.loads(props)==node_map[ident]['props']
        for ident,props in conn.execute('SELECT id,props FROM nodes')))
    conn.close()
    snapshot=json.loads((p.OUT/'neo4j_snapshot.json').read_text(encoding='utf-8'))
    from .schema import NODE_REQUIRED,EDGE_REQUIRED
    from .subsystems import classify_equipment
    from .core.neo4j import signature
    check('v6_required_entity_attributes',all(NODE_REQUIRED<=set(n['props']) for n in nodes))
    check('v6_required_relation_attributes',all(EDGE_REQUIRED<=set(e['props']) for e in edges))
    check('ontology_retains_12_classes_24_relations',len(p.KINDS)==12 and len(p.RELATIONS)==24)
    system_ids={n['id'] for n in nodes if n['kind']=='System'}
    parents={e['source']:e['target'] for e in edges if e['relation']=='IS_SUBSYSTEM_OF'}
    check('every_system_reaches_single_root_without_cycle',all(
        _reaches_root(s,parents,system_ids) for s in system_ids))
    check('multi_role_equipment_classification',len(classify_equipment('副机高压燃油泵调节机构'))>=1 and
          len(classify_equipment('主机启动与盘车装置'))>=1 and
          len(classify_equipment('主机海水冷却与舱底排水装置'))>=2)
    check('generic_model_not_assigned_invented_detail',not classify_equipment('MTU956柴油机'))
    check('snapshot_entity_ids_agree',{n['id'] for n in snapshot['nodes']}==set(node_map))
    check('snapshot_edge_ids_agree',{e['id'] for e in snapshot['edges']}=={e['id'] for e in edges})
    def neo4j_property(value):
        if value is None or isinstance(value,(str,int,float,bool)):return True
        return isinstance(value,list) and all(isinstance(v,(str,int,float,bool)) for v in value)
    badprops=[]
    for n in snapshot['nodes']:
        for key,value in n['properties'].items():
            if not neo4j_property(value):badprops.append((n['id'],key))
    check('snapshot_properties_do_not_contain_nested_maps',not badprops,badprops)
    for title,mutator in [
        ('reject_unknown_source',lambda r:r.update(source_id='src:unknown-test')),
        ('reject_unrecorded_review',lambda r:r.update(review='title_only')),
        ('reject_invented_quote',lambda r:r['facts'].__setitem__(0,
            (r['facts'][0][0],r['facts'][0][1],r['facts'][0][2],'不存在的核验测试引句_0123456789','stated'))),
        ('reject_action_as_causal_subject',lambda r:r['facts'].__setitem__(0,
            ('A|错误类型测试','CAUSES','F|错误类型测试',r['facts'][0][3],'stated'))),
    ]:
        r=copy.deepcopy(records[0]);mutator(r)
        try:p.gate(r,registry);rejected=False
        except (ValueError,KeyError):rejected=True
        check(title,rejected)
    coverage=p.rows(p.OUT/'source_review_coverage.jsonl')
    from .selection_077 import SOURCE_IDS
    round_records=[r for r in records if r['source_id'] in SOURCE_IDS]
    check('round_077_exactly_77_unique_processed_sources',
          len(round_records)==77 and {r['source_id'] for r in round_records}==set(SOURCE_IDS))
    audit_rows=p.rows(p.OUT/'reviewed_sources.jsonl')
    audit_map={r['source_id']:r for r in audit_rows}
    check('round_077_partial_review_and_exclusion_extent_preserved',all(
          r['review']=='representative_excerpt' and
          audit_map[r['source_id']]['review_extent']==r['review'] and
          audit_map[r['source_id']]['reviewed_excerpts']==r['reviewed_excerpts']
          for r in round_records))
    partial=next(copy.deepcopy(r) for r in records if r['review']=='full_text' and
        len({f[3] for f in r['facts']})>1)
    partial['review']='representative_excerpt'
    partial['reviewed_excerpts']=[{'text':partial['facts'][0][3]}]
    try:p.gate(partial,registry);outside_rejected=False
    except ValueError as exc:
        outside_rejected='outside the actually reviewed excerpts' in str(exc)
    check('reject_claim_evidence_outside_declared_reviewed_excerpt',outside_rejected)
    check('coverage_lists_all_registered_sources',len(coverage)==len(registry.sources)==1308)
    queue=p.rows(p.OUT/'source_complete_reading_queue.jsonl')
    check('reading_queue_covers_every_registered_source_without_claiming_review',
        len(queue)==len(registry.sources) and
        {x['source_id'] for x in queue}==set(registry.sources) and
        all(x['representative_excerpts'] and x['excerpt_selection_model_reviewed'] is False for x in queue))
    check('reading_queue_excerpts_are_literal_source_text',all(
        excerpt['exact_excerpt'] in registry.pages[(x['source_id'],str(excerpt['page_key']))][1]
        for x in queue for excerpt in x['representative_excerpts']))
    coverage_map={c['source_id']:c['status'] for c in coverage}
    check('reading_queue_review_status_matches_current_coverage',all(
        x['prior_status']==coverage_map[x['source_id']] for x in queue))
    check('only_actually_curated_sources_marked_full_review',
        {c['source_id'] for c in coverage if c['status']=='assistant_full_text_review'}==
        {r['source_id'] for r in records if r['facts'] and r['review']=='full_text'})
    check('only_actually_curated_sources_marked_excerpt_review',
        {c['source_id'] for c in coverage if c['status']=='assistant_excerpt_review'}==
        {r['source_id'] for r in records if r['facts'] and r['review']=='representative_excerpt'})
    prop_records=[v for n in nodes for v in json.loads(n['props'].get('source_property_evidence_json','[]'))]
    check('parameter_property_evidence_count',len(prop_records)==report['new_parameter_property_records'])
    # Smoke probes only. These are not new test-set labels or quality scores.
    probe.OUT=p.OUT
    queries=['凸轮轴轴承烧伤','连杆大端击穿机体','发电机电刷卡住','精密偶件卡紧咬死',
             'VIT电气转换器失效','供电副机因燃油进气停车','舵桨离合器接排失败',
             '发电机输入端轴承保持架碎裂','ME-V阀驱动活塞卡阻','柴油机启动超速']
    probes=[]
    for query in queries:
        answer=probe.retrieve(query,k=1);answer['graph_version']=p.VERSION
        probes.append(answer)
        check('retrieval_smoke:'+query,bool(answer['results']) and
              answer['results'][0]['fault_name']==query and bool(answer['results'][0]['facts']))
    p.save(p.OUT/'retrieval_smoke_examples.json',probes)
    generic={e['source']:e['target'] for e in edges if e['relation']=='INSTANCE_OF'}
    unique_triples={(generic.get(e['source'],e['source']),e['relation'],
                    generic.get(e['target'],e['target'])) for e in edges
                    if e['relation'] not in INDEX_RELATIONS}
    output=dict(graph_version=p.VERSION,checks=results,
        snapshot_sha256=signature(snapshot),
        passed_checks=sum(r['passed'] for r in results),total_checks=len(results),
        all_passed=all(r['passed'] for r in results),
        mechanism_and_maintenance_edges=sum(e['relation'] not in INDEX_RELATIONS for e in edges),
        unique_concept_business_triples=len(unique_triples),
        note='测试只核验存储、类型、引句定位与样例可检索，不证明声明机理正确，不代表专家审核或正式Recall/MRR评价。')
    p.save(p.OUT/'verification_report.json',output)
    print(json.dumps(output,ensure_ascii=False,indent=2))
    if not output['all_passed']:raise SystemExit(1)

def _reaches_root(s,parents,system_ids):
    seen=set()
    while s in parents:
        if s in seen:return False
        seen.add(s);s=parents[s]
    roots=system_ids-set(parents)
    return len(roots)==1 and s in roots

if __name__=='__main__':main()
