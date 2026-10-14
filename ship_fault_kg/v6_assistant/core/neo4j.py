"""Scoped atomic deployment and full-property restore. Never stores credentials."""
import argparse, base64, collections, getpass, hashlib, json, sys
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from pathlib import Path
from .preprocess import KG,OUT,write_json
from .schema import KINDS,RELATIONS

BACKUP=KG/'history/v4_3_before_v5_rebuild_20261009'

class Client:
    def __init__(self,password,url='http://127.0.0.1:7474',database='shipfaultkg'):
        self.url=url.rstrip('/')+'/db/'+database+'/query/v2'
        self.auth='Basic '+base64.b64encode(('neo4j:'+password).encode()).decode()
        self.bookmarks=[]
    def run(self,query,params=None):
        body=json.dumps(dict(statement=query,parameters=params or {},bookmarks=self.bookmarks)).encode()
        req=Request(self.url,data=body,headers={'Authorization':self.auth,'Content-Type':'application/json'})
        try:
            with urlopen(req,timeout=120) as response: result=json.load(response)
        except HTTPError as error:
            raise RuntimeError('Neo4j HTTP '+str(error.code)+'; verify local instance/authentication') from None
        if result.get('errors'): raise RuntimeError(str(result['errors']))
        self.bookmarks=result.get('bookmarks',self.bookmarks)
        d=result.get('data',{})
        return [dict(zip(d.get('fields',[]),v)) for v in d.get('values',[])]

def snapshot(client):
    return dict(database='shipfaultkg',nodes=client.run('MATCH (n:ShipKG) RETURN n.id AS id, labels(n) AS labels, properties(n) AS properties ORDER BY n.id'),
        edges=client.run('MATCH (a:ShipKG)-[r]->(b:ShipKG) RETURN r.id AS id, a.id AS source,type(r) AS relation,b.id AS target,properties(r) AS properties ORDER BY r.id'),
        constraints=client.run('SHOW CONSTRAINTS'))

def signature(snap):
    nodes=sorted([dict(n,labels=sorted(n['labels'])) for n in snap['nodes']],key=lambda n:n['id'])
    edges=sorted(snap['edges'],key=lambda e:e['id'])
    return hashlib.sha256(json.dumps(dict(nodes=nodes,edges=edges),sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def deployment_query(old,new):
    for snap in (old,new):
        for name in ('nodes','edges'):
            ids=[row['id'] for row in snap[name]]
            if any(not ident for ident in ids) or len(set(ids))!=len(ids):raise ValueError('Missing/duplicate IDs: refusing destructive deployment')
    groups=collections.defaultdict(list)
    for node in new['nodes']:
        labels=node['labels']
        if 'ShipKG' not in labels or not all(x in set(KINDS)|{'ShipKG'} for x in labels): raise ValueError('Unsafe node labels')
        groups[('node',tuple(labels))].append(node)
    for edge in new['edges']:
        if edge['relation'] not in RELATIONS and edge['relation'] not in {'IN_SYSTEM','BELONGS_TO_SYSTEM','IN_SUBSYSTEM','BELONGS_TO_SUBSYSTEM','AFFECTS_COMPONENT','HAS_EQUIPMENT','OF_VESSEL_TYPE','TESTS_FAULT','AT_LOAD','HAS_RUN','HAS_CHANNEL','HAS_STATUS','SHOWS_CONDITION','HAS_RECOMMENDED_ACTION','CONTRIBUTED_TO','LEADS_TO','PRECEDED','PROMPTS','REDUCES_EFFECTIVENESS_OF','LIMITS_DETECTION_OF','MAY_CONTRIBUTE_TO','INCREASES_SEVERITY_OF','TRIGGERS','MONITORS'}:
            raise ValueError('Unsafe relation')
        groups[('edge',edge['relation'])].append(edge)
    # A single Query API request = one atomic transaction. Non-ShipKG neighbours
    # cause DELETE to fail and roll back, rather than silently DETACH deleting them.
    params=dict(old_nodes=[n['id'] for n in old['nodes']],old_edges=[e['id'] for e in old['edges']])
    calls=['CALL () { MATCH (a:ShipKG)-[r]->(b:ShipKG) WHERE r.id IN $old_edges DELETE r RETURN count(*) AS removed_edges }',
           'CALL () { MATCH (n:ShipKG) WHERE n.id IN $old_nodes DELETE n RETURN count(*) AS removed_nodes }']
    for i,((category,label),rows) in enumerate(groups.items()):
        key='batch'+str(i);params[key]=rows
        if category=='node':
            clause=':'+':'.join(label)
            query=f'UNWIND ${key} AS row CREATE (n{clause}) SET n = row.properties RETURN count(*) AS created_{i}'
        else:
            query=f'UNWIND ${key} AS row MATCH (a:ShipKG {{id:row.source}}),(b:ShipKG {{id:row.target}}) CREATE (a)-[r:{label}]->(b) SET r = row.properties RETURN count(*) AS created_{i}'
        calls.append('CALL () { '+query+' }')
    return '\n'.join(calls)+'\nRETURN true AS committed',params

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['snapshot','apply','verify','restore']);p.add_argument('--snapshot')
    args=p.parse_args()
    if not sys.stdin.isatty(): raise SystemExit('Run from an interactive terminal; no password file is accepted.')
    client=Client(getpass.getpass('Local Neo4j password: '))
    live=snapshot(client)
    if args.mode=='snapshot':
        path=BACKUP/'neo4j_live_before_v5.json'
        if path.exists(): raise SystemExit('Backup already exists; refusing overwrite.')
        write_json(path,live);write_json(BACKUP/'neo4j_live_backup_digest.json',dict(sha256=signature(live),nodes=len(live['nodes']),edges=len(live['edges'])))
        print(json.dumps(dict(snapshot=str(path),nodes=len(live['nodes']),edges=len(live['edges']))));return
    if args.mode=='verify':
        expected=json.loads((OUT/'neo4j_snapshot_v5.json').read_text(encoding='utf-8'))
        result=dict(nodes=len(live['nodes']),edges=len(live['edges']),exact_property_match=signature(live)==signature(expected),
            classes=dict(sorted(collections.Counter(n['properties'].get('kind','unknown') for n in live['nodes']).items())),
            constraints=live['constraints'])
        write_json(OUT/'neo4j_verify_result.json',result)
        if result['exact_property_match'] and not (OUT/'last_deployed_snapshot.json').exists():
            write_json(OUT/'last_deployed_snapshot.json',live)
        print(json.dumps(result));return
    if args.mode=='restore':
        new=json.loads(Path(args.snapshot or BACKUP/'neo4j_live_before_v5.json').read_text(encoding='utf-8'))
        # Old labels may include Run/Sensor/Cause etc. Explicit checked whitelist.
        global KINDS
        KINDS=dict(KINDS,Run='试验',Sensor='测点',Cause='原因',Condition='工况',Symptom='症状',Consequence='后果')
        write_json(OUT/'neo4j_live_before_restore.json',live)
    else:
        backup=json.loads((BACKUP/'neo4j_live_before_v5.json').read_text(encoding='utf-8'))
        new=json.loads((OUT/'neo4j_snapshot_v5.json').read_text(encoding='utf-8'))
        if signature(live)==signature(new): print('V5 already matches; no mutation.');return
        previous=OUT/'last_deployed_snapshot.json'
        accepted={signature(backup)}
        if previous.exists(): accepted.add(signature(json.loads(previous.read_text(encoding='utf-8'))))
        if signature(live) not in accepted: raise SystemExit('Live graph changed after the last recorded deployment. Refusing replacement; re-audit required.')
        validation=json.loads((OUT/'verification_report.json').read_text(encoding='utf-8'))
        if not validation.get('passed') or validation.get('snapshot_sha256')!=signature(new):
            raise SystemExit('Run the independent V5 verification on this exact build before deployment.')
        archive=OUT/'deployment_backups';archive.mkdir(exist_ok=True)
        before=archive/(signature(live)+'.json')
        if not before.exists():write_json(before,live)
    # Verify the live fingerprint again immediately before committing.
    if signature(snapshot(client))!=signature(live): raise SystemExit('Concurrent edit detected; refusing mutation.')
    query,params=deployment_query(live,new)
    client.run(query,params)
    after=snapshot(client)
    result=dict(mode=args.mode,nodes=len(after['nodes']),edges=len(after['edges']),exact_property_match=signature(after)==signature(new))
    write_json(OUT/('neo4j_restore_result.json' if args.mode=='restore' else 'neo4j_import_result.json'),result)
    if not result['exact_property_match']: raise RuntimeError('Post-deployment verification mismatch')
    if args.mode=='apply':write_json(OUT/'last_deployed_snapshot.json',after)
    print(json.dumps(result))

if __name__=='__main__': main()
