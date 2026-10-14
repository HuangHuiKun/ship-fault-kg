"""Guarded local V6 publication: live backup, atomic replacement and verification.

Credentials are entered with getpass and never saved in files or arguments.
Only ShipKG-owned entities/edges in the explicitly named local database change.
"""
import argparse,collections,getpass,json,sys
from pathlib import Path
from .pipeline import KG,OUT,save,VERSION
from ..v5.neo4j import Client,snapshot,signature,deployment_query

BACKUP=KG/'history/v6_publication_20261013'

def expected_snapshot():
 return json.loads((OUT/'neo4j_snapshot.json').read_text(encoding='utf-8'))

def validate_local(new):
 v=json.loads((OUT/'verification_report.json').read_text(encoding='utf-8'))
 if not v.get('all_passed') or v.get('snapshot_sha256')!=signature(new):
  raise SystemExit('Independent verification does not match this exact snapshot; refusing publication.')

def guard_external_links(client):
 result=client.run('MATCH (n:ShipKG)-[r]-(m) WHERE NOT m:ShipKG RETURN count(r) AS count')
 if result[0]['count']:raise SystemExit('ShipKG has non-project neighbours; refusing replacement.')

def write_backup(live,path):
 digest=signature(live)
 if path.exists():
  if signature(json.loads(path.read_text(encoding='utf-8')))!=digest:
   raise SystemExit('Existing backup differs; refusing overwrite.')
 else:save(path,live)
 save(path.with_name(path.stem+'_digest.json'),dict(sha256=digest,nodes=len(live['nodes']),
       edges=len(live['edges']),database='shipfaultkg',includes_all_properties=True))

def verify_live(client,new):
 live=snapshot(client)
 info=dict(graph_version=VERSION,database='shipfaultkg',url='http://127.0.0.1:7474',
  nodes=len(live['nodes']),edges=len(live['edges']),
  exact_property_match=signature(live)==signature(new),snapshot_sha256=signature(new),
  live_sha256=signature(live),classes=dict(sorted(collections.Counter(
   n['properties'].get('kind','unknown') for n in live['nodes']).items())),
  relation_types=dict(sorted(collections.Counter(e['relation'] for e in live['edges']).items())),
  constraints=live['constraints'])
 save(OUT/'neo4j_verify_result.json',info)
 if not info['exact_property_match']:raise RuntimeError('Post-deployment full-property mismatch')
 save(OUT/'last_deployed_snapshot.json',live)
 report=json.loads((OUT/'build_report.json').read_text(encoding='utf-8'))
 report.update(published_to_neo4j=True,status='published_reviewed_subset',
               deployed_snapshot_sha256=signature(new))
 save(OUT/'build_report.json',report)
 return info

def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['snapshot','apply','verify','restore'])
 p.add_argument('--snapshot');args=p.parse_args()
 client=Client(getpass.getpass('Local Neo4j password (hidden): '))
 live=snapshot(client);guard_external_links(client)
 backup=BACKUP/'neo4j_live_before_v6.json'
 if args.mode=='snapshot':
  write_backup(live,backup)
  print(json.dumps(dict(backup=str(backup),nodes=len(live['nodes']),edges=len(live['edges']))));return
 new=expected_snapshot()
 if args.mode=='verify':
  print(json.dumps(verify_live(client,new),ensure_ascii=False));return
 if args.mode=='restore':
  new=json.loads(Path(args.snapshot or backup).read_text(encoding='utf-8'))
  write_backup(live,BACKUP/('before_restore_'+signature(live)+'.json'))
 else:
  validate_local(new)
  if signature(live)==signature(new):
   print(json.dumps(verify_live(client,new),ensure_ascii=False));return
  if not backup.exists():raise SystemExit('First take the live snapshot; refusing unbacked replacement.')
  if signature(json.loads(backup.read_text(encoding='utf-8')))!=signature(live):
   raise SystemExit('Live graph changed since the backup; re-audit required.')
 if signature(snapshot(client))!=signature(live):
  raise SystemExit('Concurrent graph modification detected; refusing replacement.')
 query,params=deployment_query(live,new)
 client.run(query,params)
 if args.mode=='restore':
  after=snapshot(client);result=dict(mode='restore',nodes=len(after['nodes']),edges=len(after['edges']),
    exact_property_match=signature(after)==signature(new))
  save(OUT/'neo4j_restore_result.json',result)
  if not result['exact_property_match']:raise RuntimeError('Restore mismatch')
 else:
  result=verify_live(client,new);result.update(mode='apply',backup=str(backup),atomic_transaction=True)
  save(OUT/'neo4j_import_result.json',result)
 print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
