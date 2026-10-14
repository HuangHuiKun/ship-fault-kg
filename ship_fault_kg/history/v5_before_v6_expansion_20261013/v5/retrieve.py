"""Small scope-safe lexical retrieval probe, not embedding or trained diagnosis."""
import argparse, collections, json, math, re, sqlite3
from .preprocess import OUT,write_json
from .schema import CAUSAL

def grams(text):
    text=re.sub(r'\s+','',text.casefold())
    return set(text[i:i+2] for i in range(max(0,len(text)-1)))|set(text)

def retrieve(query,k=5,max_depth=3):
    conn=sqlite3.connect(f'file:{(OUT/"ship_fault_kg.sqlite").as_posix()}?mode=ro',uri=True)
    conn.row_factory=sqlite3.Row
    nodes={r['id']:dict(r,props=json.loads(r['props']),aliases=json.loads(r['aliases'])) for r in conn.execute('SELECT * FROM nodes')}
    edges=[dict(r,props=json.loads(r['props'])) for r in conn.execute('SELECT * FROM edges')]
    claims={r['id']:json.loads(r['data']) for r in conn.execute('SELECT * FROM assertions')}
    sources={r['id']:json.loads(r['data']) for r in conn.execute('SELECT * FROM sources')};conn.close()
    q=grams(query);rank=[]
    for n in nodes.values():
        if n['kind']!='Fault' or n['props']['entity_level']!='concept':continue
        aliases=set(n['aliases'])|{token for alias in n['aliases'] for token in re.split(r'[\s,，、;；]+',alias) if len(token)>=2}
        text=n['name']+' '+' '.join(sorted(aliases));g=grams(text)
        score=len(q&g)/max(1,math.sqrt(len(q)*len(g)))
        score+=2 if any(a and (a in query or query.strip() in a) for a in aliases) else 0
        if score:rank.append((score,n['id']))
    rank=sorted(rank,key=lambda row:(-row[0],nodes[row[1]]['name']))[:k]
    packs=[]
    for score,fid in rank:
        seed={fid}|{e['source'] for e in edges if e['relation']=='INSTANCE_OF' and e['target']==fid}
        selected=[];scope_nodes=collections.defaultdict(set)
        for e in edges:
            if e['relation'] not in {'DOCUMENTED_BY','INSTANCE_OF','INVOLVES','HAS_CASE'} and (e['source'] in seed or e['target'] in seed):
                scope_nodes[e['props']['scope_id']].update(seed)
        # Expand separately for each source/incident. A shared concept never
        # creates a cross-document concatenation presented as established cause.
        for scope,frontier in scope_nodes.items():
            visited=set(frontier)
            for _ in range(max_depth):
                additions=set()
                for e in edges:
                    if e['props']['scope_id']!=scope or e['relation'] not in CAUSAL|{'HAS_MANIFESTATION','INDICATES','CHECKS','ADDRESSES','ASSOCIATED_WITH','DESCRIBED_BY_PARAMETER','USES_PARAMETER'}:continue
                    if e['source'] in frontier or e['target'] in frontier:
                        selected.append(e);additions.update([e['source'],e['target']])
                frontier=additions-visited;visited.update(additions)
                if not frontier:break
        unique={e['id']:e for e in selected}
        facts=[]
        for e in sorted(unique.values(),key=lambda e:(e['props']['scope_id'],e['id'])):
            c=claims[e['assertion_id']];src=sources[c['source_id']]
            facts.append(dict(subject=nodes[e['source']]['name'],relation=e['props']['name'],object=nodes[e['target']]['name'],
                **{key:c[key] for key in ('id','scope_id','certainty','statement_nature','action_status','quote','applicability','expert_review','page','locator','normalized_start','normalized_end')},
                source_title=src['title'],source_url=src['url'],source_tier=src['source_tier'],source_sha256=src['sha256']))
        packs.append(dict(fault_id=fid,fault_name=nodes[fid]['name'],lexical_score=round(score,4),facts=facts))
    return dict(graph_version='5.0',query=query,method='实体别名+字/二元组词法相似度+同scope关系扩展（非语义向量检索）',
        results=packs,warning='检索证据不等同已确诊根因；病例、构型和来源范围不能混合推因果；实船操作须专家确认')

def main():
    p=argparse.ArgumentParser();p.add_argument('query');p.add_argument('--top-k',type=int,default=3);args=p.parse_args()
    result=retrieve(args.query,args.top_k)
    write_json(OUT/'retrieval_example.json',result)
    print(json.dumps(dict(query=args.query,results=[dict(name=r['fault_name'],facts=len(r['facts'])) for r in result['results']],output=str(OUT/'retrieval_example.json')),ensure_ascii=False))

if __name__=='__main__':main()
