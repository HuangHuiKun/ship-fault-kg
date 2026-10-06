"""Scoped, backed-up and atomic Neo4j synchronization for the reviewed V4 graph.

Only ShipKG nodes with IDs in the current/baseline local store are affected.
No password is saved. No CSV is required. A failed Cypher statement rolls back
the entire mutation; DELETE (not DETACH DELETE) protects unknown extra edges.
"""
import argparse
import getpass
import json
from pathlib import Path
from import_neo4j import QueryClient, load_plan, prepare
from retrieve import read_store
from schema import VERSION, LEGACY_KIND_ZH

HERE = Path(__file__).resolve().parent
BACKUP = HERE / 'history' / 'v4_1_before_source_merge_20261006'


def snapshot(client):
    return {
        'database':'shipfaultkg',
        'nodes':client.run('MATCH (n:ShipKG) RETURN n.id AS id, labels(n) AS labels, properties(n) AS properties ORDER BY id'),
        'edges':client.run('MATCH (a:ShipKG)-[r]->(b:ShipKG) RETURN r.id AS id, a.id AS source, b.id AS target, type(r) AS type, properties(r) AS properties ORDER BY id'),
        'constraints':client.run('SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties RETURN name, type, labelsOrTypes, properties'),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--url',default='http://127.0.0.1:7474')
    parser.add_argument('--baseline-backup',type=Path,default=BACKUP)
    args=parser.parse_args()
    backup=args.baseline_backup.resolve()
    password=getpass.getpass('Neo4j password (not saved): ')
    client=QueryClient(args.url,'shipfaultkg','neo4j',password)
    before=snapshot(client)
    if not before['nodes'] or len({n['id'] for n in before['nodes']}) != len(before['nodes']):
        raise RuntimeError('Missing/duplicate ShipKG IDs; inspect before synchronization')
    backup.mkdir(parents=True,exist_ok=True)
    backupfile=backup/'neo4j_snapshot.json'
    if not backupfile.exists():
        backupfile.write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'backup':str(backupfile),'live_nodes':len(before['nodes']),'live_edges':len(before['edges'])}),flush=True)
    if not args.apply:
        return
    baseline=read_store(backup/'output'/'ship_fault_kg.sqlite')
    refinement=json.loads((HERE/'refinement_v4_1.json').read_text(encoding='utf-8'))
    approved_vessel_ids=set(refinement['remove_vessel_types'])
    nodes,edges,plan=load_plan()
    target_nodes={n['id']:n for n in nodes}
    target_edges={e['id']:e for e in edges}
    live_node_ids={n['id'] for n in before['nodes']}
    baseline_ids=set(baseline['nodes'])
    if live_node_ids not in (baseline_ids,set(target_nodes)):
        raise RuntimeError('Live ShipKG has unknown/missing nodes; no changes made')
    if {e['id'] for e in before['edges']} not in (set(baseline['edges']),set(target_edges)):
        raise RuntimeError('Live ShipKG has unknown/missing edges; no changes made')
    remove_nodes=sorted(live_node_ids-set(target_nodes))
    if any(baseline['nodes'][i]['kind']!='Dataset' and i not in approved_vessel_ids for i in remove_nodes):
        raise RuntimeError('Deletion outside the approved Dataset/vessel-type scope')
    remove_edges=[]
    for e in before['edges']:
        target=target_edges.get(e['id'])
        if not target or (e['source'],e['type'],e['target']) != (target['source'],target['relation'],target['target']):
            remove_edges.append(e['id'])
    params={'remove_nodes':remove_nodes,'remove_edges':remove_edges,'node_ids':sorted(target_nodes)}
    parts=[
        'CALL () { MATCH (:ShipKG)-[r]->(:ShipKG) WHERE r.id IN $remove_edges DELETE r RETURN count(*) AS removed_relationships }',
        'CALL () { MATCH (n:ShipKG) WHERE n.id IN $remove_nodes DELETE n RETURN count(*) AS removed_nodes }',
        'CALL () { MATCH (n:ShipKG) WHERE n.id IN $node_ids REMOVE n:' + ':'.join(LEGACY_KIND_ZH) + ' RETURN count(*) AS relabelled_nodes }',
    ]
    for i,batch in enumerate(plan):
        key=f'rows_{i}'
        params[key]=batch['parameters']['rows']
        parts.append('CALL () { '+batch['statement'].replace('$rows','$'+key).replace('AS processed',f'AS processed_{i}')+' }')
    aliases=', '.join(f'processed_{i}' for i in range(len(plan)))
    parts.append('RETURN removed_nodes, removed_relationships, relabelled_nodes, '+aliases)
    client.run('CREATE CONSTRAINT shipkg_id IF NOT EXISTS FOR (n:ShipKG) REQUIRE n.id IS UNIQUE')
    client.run('EXPLAIN ' + '\n'.join(parts),params)
    # One Query API request = one auto-commit transaction, including the cleanup.
    result=client.run('\n'.join(parts),params)[0]
    for i,batch in enumerate(plan):
        if result[f'processed_{i}'] != len(batch['parameters']['rows']):
            raise RuntimeError('Unexpected processed count; verify database immediately')
    after=snapshot(client)
    actual_nodes={n['id']:n for n in after['nodes']}
    actual_edges={e['id']:e for e in after['edges']}
    if set(actual_nodes)!=set(target_nodes) or set(actual_edges)!=set(target_edges):
        raise RuntimeError('Post-import ID sets mismatch')
    for ident,n in target_nodes.items():
        live=actual_nodes[ident]
        if n['kind'] not in live['labels'] or any(k in live['labels'] for k in ('FaultType','Dataset','VesselType','Subsystem','Observation')):
            raise RuntimeError('Retired labels remain')
        p=live['properties']
        if p['name']!=n['name'] or p['kind']!=n['kind'] or p['graph_version']!=VERSION:
            raise RuntimeError('Node name/version mismatch')
        if p.get('props_json')!=n['props']:
            raise RuntimeError('Node complete property JSON mismatch: '+ident)
    for ident,e in target_edges.items():
        live=actual_edges[ident]
        if (live['source'],live['type'],live['target'])!=(e['source'],e['relation'],e['target']):
            raise RuntimeError('Relationship endpoints/type mismatch')
        if live['properties']['name']!=json.loads(e['props'])['name']:
            raise RuntimeError(f'Relationship caption mismatch: {ident}')
        if live['properties']['evidence_id']!=e['evidence_id']:
            raise RuntimeError('Evidence ID mismatch')
        if live['properties'].get('props_json')!=e['props']:
            raise RuntimeError('Relationship complete property JSON mismatch: '+ident)
    report={'verified':True,'database':'shipfaultkg','version':VERSION,'nodes':len(after['nodes']),
            'relationships':len(after['edges']),
            'removed_dataset_nodes':sum(baseline['nodes'][i]['kind']=='Dataset' for i in baseline_ids-set(target_nodes)),
            'removed_vessel_type_nodes':len((baseline_ids-set(target_nodes)) & approved_vessel_ids),
            'removed_nodes_this_run':len(remove_nodes),
            'removed_or_replaced_relationships':len(remove_edges),'single_atomic_transaction':True,
            'source_levels':{level:sum(n['kind']=='Source' and json.loads(n['props']).get('source_level')==level for n in nodes)
                             for level in ('资料级','记录级')},
            'csv_required':False,'backup':str(backupfile),'method':'Neo4j HTTP Query API'}
    (HERE/'output'/'neo4j_import_result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (HERE/'output'/'neo4j_snapshot_v4.json').write_text(json.dumps(after,ensure_ascii=False,indent=2),encoding='utf-8')
    prepare(nodes,edges,plan)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
