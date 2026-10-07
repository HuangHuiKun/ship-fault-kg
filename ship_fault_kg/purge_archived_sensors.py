"""Scoped cleanup explicitly requested on 2026-10-05, with a restorable JSON backup.

No password is persisted. Delete mode uses exact V3 sensor IDs and one guarded
transaction. Restore is opt-in and refuses pre-existing sensor IDs.
"""
import argparse
from datetime import datetime
import getpass
import json
from pathlib import Path
import re
import sqlite3
from import_neo4j import QueryClient

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / 'history' / 'organization_20261007' / 'sensor_maintenance' / 'output'
OUT = ARCHIVE / 'maintenance_20261005'
CHANGES = ARCHIVE / 'revision_changes_v3.json'
COUNTS = '''
CALL () { MATCH (n) RETURN count(n) AS all_nodes }
CALL () { MATCH ()-[r]->() RETURN count(r) AS all_relationships }
CALL () { MATCH (n:ShipKG) RETURN count(n) AS active_nodes }
CALL () { MATCH (:ShipKG)-[r]->(:ShipKG) RETURN count(r) AS active_relationships }
CALL () { MATCH (n:Sensor) RETURN count(n) AS sensors }
CALL () { MATCH (n:ArchivedSensor) RETURN count(n) AS archived_sensors }
RETURN all_nodes, all_relationships, active_nodes, active_relationships, sensors, archived_sensors
'''


def checked_backup(client, ids):
    before = client.run(COUNTS)[0]
    expected = {'all_nodes': 555, 'all_relationships': 1287, 'active_nodes': 500,
                'active_relationships': 1201, 'sensors': 15, 'archived_sensors': 55}
    if before != expected:
        raise RuntimeError(f'Database changed; refuse deletion: {before}')
    rows = client.run('''MATCH (n:ArchivedShipKG:ArchivedSensor) WHERE n.id IN $ids
                        RETURN n.id AS id, labels(n) AS labels, properties(n) AS properties
                        ORDER BY n.id''', {'ids': ids})
    if len(rows) != 55 or {row['id'] for row in rows} != set(ids):
        raise RuntimeError('Archived target ID set does not match the 55 expected sensors')
    if any('ShipKG' in row['labels'] or 'Sensor' in row['labels'] for row in rows):
        raise RuntimeError('A target is active; refuse deletion')
    edges = client.run('''MATCH (n:ArchivedShipKG:ArchivedSensor)-[r]-(m)
                         WHERE n.id IN $ids WITH DISTINCT r
                         RETURN type(r) AS type, startNode(r).id AS source,
                         endNode(r).id AS target, properties(r) AS properties
                         ORDER BY properties.id''', {'ids': ids})
    expected_edges = set(json.loads(CHANGES.read_text(encoding='utf-8'))['removed_edges'])
    if len(edges) != 86 or {r['properties'].get('id') for r in edges} != expected_edges:
        raise RuntimeError('Relationships do not match the 86 expected direct sensor edges')
    backup = {'timestamp': datetime.now().isoformat(), 'database': 'shipfaultkg',
              'before': before, 'nodes': rows, 'relationships': edges,
              'restore_note': 'Use this script --restore after reviewing the scope; raw datasets untouched.'}
    path = OUT / 'deleted_sensors_backup.json'
    if path.exists():
        raise RuntimeError('Backup already exists; refuse overwriting')
    OUT.mkdir(exist_ok=True)
    path.write_text(json.dumps(backup, ensure_ascii=False, indent=2), encoding='utf-8')
    # Confirm persisted backup can be decoded before any graph mutation.
    loaded = json.loads(path.read_text(encoding='utf-8'))
    assert len(loaded['nodes']) == 55 and len(loaded['relationships']) == 86
    return backup


def delete(client, ids):
    backup = checked_backup(client, ids)
    query = '''
    MATCH (n:ArchivedShipKG:ArchivedSensor) WHERE n.id IN $ids
    WITH collect(n) AS targets
    WHERE size(targets) = 55 AND all(n IN targets WHERE NOT n:ShipKG AND NOT n:Sensor)
    CALL (targets) {
      UNWIND targets AS n OPTIONAL MATCH (n)-[r]-()
      RETURN count(DISTINCT r) AS rel_count
    }
    WITH targets, rel_count WHERE rel_count = 86
    UNWIND targets AS n DETACH DELETE n
    RETURN count(*) AS deleted_nodes, max(rel_count) AS deleted_relationships
    '''
    result = client.run(query, {'ids': ids})
    if result != [{'deleted_nodes': 55, 'deleted_relationships': 86}]:
        raise RuntimeError(f'Scoped deletion guard did not pass: {result}')
    after = client.run(COUNTS)[0]
    expected = {'all_nodes': 500, 'all_relationships': 1201, 'active_nodes': 500,
                'active_relationships': 1201, 'sensors': 15, 'archived_sensors': 0}
    if after != expected:
        raise RuntimeError(f'Post-delete counts need review: {after}')
    # Every active ID must still match the current SQLite master, not merely its count.
    with sqlite3.connect(f"file:{(HERE / 'output/ship_fault_kg.sqlite').as_posix()}?mode=ro", uri=True) as conn:
        node_ids = {r[0] for r in conn.execute('SELECT id FROM nodes')}
        edge_ids = {r[0] for r in conn.execute('SELECT id FROM edges')}
    actual_nodes = {r['id'] for r in client.run('MATCH (n:ShipKG) RETURN n.id AS id')}
    actual_edges = {r['id'] for r in client.run('MATCH (:ShipKG)-[r]->(:ShipKG) RETURN r.id AS id')}
    if actual_nodes != node_ids or actual_edges != edge_ids:
        raise RuntimeError('Active graph ID consistency failed')
    receipt = {'operation': 'delete_55_archived_sensors', 'before': backup['before'],
               'after': after, 'deleted': result[0], 'active_ids_match_sqlite': True,
               'raw_datasets_deleted': False, 'restore_backup': str(OUT / 'deleted_sensors_backup.json')}
    (OUT / 'purge_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


def restore(client):
    backup = json.loads((OUT / 'deleted_sensors_backup.json').read_text(encoding='utf-8'))
    ids = [r['id'] for r in backup['nodes']]
    found = client.run('MATCH (n) WHERE n.id IN $ids RETURN count(n) AS n', {'ids': ids})[0]['n']
    if found:
        raise RuntimeError('Some target IDs already exist; refuse restoring duplicates')
    for row in backup['nodes']:
        if any(not re.fullmatch('[A-Za-z][A-Za-z0-9_]*', label) for label in row['labels']):
            raise RuntimeError('Invalid label in backup')
    for row in backup['relationships']:
        if not re.fullmatch('[A-Za-z][A-Za-z0-9_]*', row['type']):
            raise RuntimeError('Invalid relationship type in backup')
    # Use one Query API transaction statement to restore all saved nodes/edges.
    clauses, params = [], {}
    for i, row in enumerate(backup['nodes']):
        params[f'n{i}'] = row['properties']
        labels = ':'.join(row['labels'])
        clauses.append(f'CALL () {{ CREATE (n:{labels}) SET n = $n{i} }}')
    for i, row in enumerate(backup['relationships']):
        params[f's{i}'], params[f't{i}'], params[f'r{i}'] = row['source'], row['target'], row['properties']
        clauses.append(f'CALL () {{ MATCH (a {{id:$s{i}}}), (b {{id:$t{i}}}) CREATE (a)-[r:{row["type"]}]->(b) SET r = $r{i} }}')
    client.run('\n'.join(clauses) + '\nRETURN 55 AS restored_nodes, 86 AS restored_relationships', params)
    print(json.dumps(client.run(COUNTS)[0], ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delete', action='store_true', help='User-requested irreversible Neo4j deletion, backed up externally')
    parser.add_argument('--restore', action='store_true', help='Opt-in restore from backup; never run as part of ordinary import')
    args = parser.parse_args()
    if args.delete and args.restore:
        parser.error('Choose at most one operation')
    password = getpass.getpass('Neo4j password (hidden, not saved): ')
    client = QueryClient('http://127.0.0.1:7474', 'shipfaultkg', 'neo4j', password)
    changes = json.loads(CHANGES.read_text(encoding='utf-8'))
    ids = sorted(row['id'] for row in changes['removed_nodes'])
    if len(ids) != 55 or len(set(ids)) != 55:
        raise RuntimeError('Invalid target list')
    if args.delete:
        delete(client, ids)
    elif args.restore:
        restore(client)
    else:
        print(json.dumps(client.run(COUNTS)[0], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
