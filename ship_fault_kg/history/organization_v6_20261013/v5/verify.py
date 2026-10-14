"""Independent snapshot/SQLite/raw-source integrity gates and small smoke suite."""
import collections, hashlib, json, sqlite3
from .preprocess import OUT,DATA,write_json
from .schema import KINDS,RELATIONS,ENDPOINTS,CAUSAL
from .retrieve import retrieve
from .neo4j import signature

def main():
    c=sqlite3.connect(f'file:{(OUT/"ship_fault_kg.sqlite").as_posix()}?mode=ro',uri=True);c.row_factory=sqlite3.Row
    nodes={r['id']:dict(r,props=json.loads(r['props'])) for r in c.execute('SELECT * FROM nodes')}
    edges=[dict(r,props=json.loads(r['props'])) for r in c.execute('SELECT * FROM edges')]
    claims={r['id']:json.loads(r['data']) for r in c.execute('SELECT * FROM assertions')}
    sources={r['id']:json.loads(r['data']) for r in c.execute('SELECT * FROM sources')}
    passages={r['id']:json.loads(r['data']) for r in c.execute('SELECT * FROM passages')}
    errors=[]
    if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok':errors.append('SQLite integrity')
    c.close()
    if set(n['kind'] for n in nodes.values())!=set(KINDS):errors.append('Class coverage')
    for a in claims.values():
        if a['source_id'] not in sources or a['passage_id'] not in passages:errors.append('Missing source/passage')
        else:
            p=passages[a['passage_id']]
            if a['quote']!=p['text'] or p['source_id']!=a['source_id']:errors.append('Passage mismatch')
        if a['review_status']!='accepted_for_experiment' or a['expert_review']!='not_performed':errors.append('Misleading review')
    used_sources={a['source_id'] for a in claims.values()}
    for sid in used_sources:
        src=sources[sid]
        for path in src['paths']:
            raw=DATA/path
            if not raw.exists() or hashlib.sha256(raw.read_bytes()).hexdigest()!=src['sha256']:errors.append('Raw source changed '+path)
    for e in edges:
        a=nodes[e['source']];b=nodes[e['target']];rel=e['relation']
        if rel not in RELATIONS or a['kind'] not in ENDPOINTS[rel][0] or b['kind'] not in ENDPOINTS[rel][1]:errors.append('Bad endpoint '+e['id'])
        if e['assertion_id'] not in claims:errors.append('Missing edge assertion')
        if e['props']['name']!=RELATIONS[rel]:errors.append('Wrong Chinese caption')
        if rel in CAUSAL:
            if e['props']['statement_nature'].endswith(('classification','index')):errors.append('Classification misrepresented as cause')
            contexts={n['props']['scope_id'] for n in (a,b) if n['props']['entity_level']=='context_record'}
            if len(contexts)>1:errors.append('Cross-case cause')
    tests=[('拉缸','缸套黏着拉伤'),('轴瓦烧伤','轴瓦烧伤'),('压气机喘振','压气机喘振'),
        ('排气阀烧损','排气阀烧损'),('离合器打滑','离合器打滑'),('喷油器喷嘴堵塞','喷油器喷嘴堵塞'),
        ('共轨冲洗单向阀止回失效','共轨冲洗单向阀止回失效'),('测速板整形比较器输出故障','测速板整形比较器输出故障'),
        ('发电机内部短路','发电机内部短路'),('主轴承咬死','主轴承咬死'),
        ('缸套裂纹','缸套裂纹'),('海水泵轴封失效','海水泵轴封失效'),
        ('主机可能拉缸，排气温度升高，冷却水出口温度偏高','缸套黏着拉伤')]
    smoke=[]
    for query,gold in tests:
        result=retrieve(query,k=3);rank=next((i for i,r in enumerate(result['results'],1) if r['fault_name']==gold),None)
        smoke.append(dict(query=query,gold_name=gold,rank=rank,found=rank is not None,
            returned_faults=[r['fault_name'] for r in result['results']],
            evidence_assertions=sum(len(r['facts']) for r in result['results'])))
    if not all(t['found'] for t in smoke):errors.append('Smoke retrieval failure')
    report=json.loads((OUT/'build_report.json').read_text(encoding='utf-8'))
    if not all(v['within_planning_range'] for v in report['class_ratios_vs_fault_concepts'].values()):
        errors.append('Current release class proportions outside approved planning ranges')
    # Business triples deduplication, rather than pretending distinct evidence =
    # distinct causal mechanisms. Different scopes remain distinct assertions.
    triples={(e['source'],e['relation'],e['target']) for e in edges}
    scopes={(e['source'],e['relation'],e['target'],e['props']['scope_id']) for e in edges}
    snap=json.loads((OUT/'neo4j_snapshot_v5.json').read_text(encoding='utf-8'))
    if len(snap['nodes'])!=len(nodes) or len(snap['edges'])!=len(edges):errors.append('Snapshot count mismatch')
    result=dict(passed=not errors,errors=errors,snapshot_sha256=signature(snap),raw_sources_verified=len(used_sources),
        edges=len(edges),unique_business_triples=len(triples),unique_scoped_triples=len(scopes),
        smoke_tests=smoke,smoke_passed=sum(t['found'] for t in smoke),
        evaluation_note='12个故障短词加1个诊断文本样例仅为开发冒烟测试，不是独立检索质量评估；旧38/24题尚未迁移，不能沿用旧指标。')
    write_json(OUT/'verification_report.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
