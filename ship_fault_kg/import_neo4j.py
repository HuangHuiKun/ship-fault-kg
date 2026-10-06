"""SQLite -> Neo4j directly, using the official HTTP Query API (no CSV/py2neo).

--prepare-only also generates an authenticated Browser import guide. No
password is stored; MERGE preserves other graphs and supports repeated runs.
"""
from collections import defaultdict
import argparse
import base64
import getpass
import html
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from schema import VERSION, KIND_ZH, RELATION_ZH, CERTAINTY_ZH

OUTPUT = Path(__file__).resolve().parent / 'output'


def literal(value):
    if isinstance(value, dict):
        return '{' + ','.join('`' + k.replace('`', '``') + '`:' + literal(v) for k, v in value.items()) + '}'
    if isinstance(value, list):
        return '[' + ','.join(map(literal, value)) + ']'
    return json.dumps(value, ensure_ascii=False)


def load_plan():
    conn = sqlite3.connect(f"file:{(OUTPUT / 'ship_fault_kg.sqlite').as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        nodes = [dict(r) for r in conn.execute('SELECT * FROM nodes ORDER BY id')]
        edges = [dict(r) for r in conn.execute('SELECT * FROM edges ORDER BY id')]
        evidence = {r['id']: dict(r) for r in conn.execute('SELECT * FROM evidence')}
    finally:
        conn.close()
    groups = defaultdict(list)
    for node in nodes:
        props = json.loads(node['props'])
        simple = {k: v for k, v in props.items() if isinstance(v, (str, int, float, bool))}
        simple.update(id=node['id'], kind=node['kind'], name=node['name'], aliases=node['aliases'],
                      display_name=props.get('display_name', node['name']),
                      kind_zh=KIND_ZH[node['kind']], graph_version=VERSION, props_json=node['props'])
        groups[('node', node['kind'])].append({'id': node['id'], 'properties': simple})
    for edge in edges:
        ev = evidence[edge['evidence_id']]
        props = json.loads(edge['props'])
        simple = {k: v for k, v in props.items() if isinstance(v, (str, int, float, bool))}
        name = RELATION_ZH[edge['relation']]
        if edge['certainty'] in ('probable', 'possible') and not name.startswith('可能'):
            name = CERTAINTY_ZH[edge['certainty']] + name
        simple.update(id=edge['id'], name=name, graph_version=VERSION,
                      case_id=edge['case_id'], certainty=edge['certainty'],
                      certainty_zh=CERTAINTY_ZH[edge['certainty']], evidence_id=edge['evidence_id'],
                      source_file=ev['source_file'], source_url=ev['source_url'], page=str(ev['page']),
                      locator=ev['locator'], quote=ev['quote'], props_json=edge['props'])
        groups[('edge', edge['relation'])].append({'id': edge['id'], 'source': edge['source'],
                                                'target': edge['target'], 'properties': simple})
    plan = []
    for (category, label), rows in groups.items():
        if not re.fullmatch('[A-Za-z][A-Za-z0-9_]*', label):
            raise ValueError('Invalid label/type')
        if category == 'node':
            query = f'UNWIND $rows AS row MERGE (n:ShipKG:{label} {{id:row.id}}) SET n += row.properties RETURN count(n) AS processed'
        else:
            query = ('UNWIND $rows AS row MATCH (a:ShipKG {id:row.source}), (b:ShipKG {id:row.target}) '
                     f'MERGE (a)-[r:{label} {{id:row.id}}]->(b) SET r += row.properties RETURN count(r) AS processed')
        for start in range(0, len(rows), 100):
            plan.append({'statement': query, 'parameters': {'rows': rows[start:start+100]},
                         'category': category, 'label': label})
    return nodes, edges, plan


def prepare(nodes, edges, plan):
    (OUTPUT / 'neo4j_direct_plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
    calls = []
    for i, batch in enumerate(plan):
        query = batch['statement'].replace('$rows', literal(batch['parameters']['rows']))
        query = query.replace('AS processed', f'AS processed_{i}')
        calls.append('CALL () { ' + query + ' }')
    query = '\n'.join(calls) + f"\nRETURN {len(nodes)} AS source_nodes, {len(edges)} AS source_relationships, '{VERSION}' AS version;"
    (OUTPUT / 'neo4j_direct_import.cypher').write_text(query, encoding='utf-8')
    constraint = 'CREATE CONSTRAINT shipkg_id IF NOT EXISTS FOR (n:ShipKG) REQUIRE n.id IS UNIQUE;'
    verify = (f"MATCH (n:ShipKG {{graph_version:'{VERSION}'}}) WITH count(n) AS nodes "
              f"MATCH (:ShipKG)-[r]->(:ShipKG) WHERE r.graph_version='{VERSION}' "
              "RETURN nodes, count(r) AS relationships, count(CASE WHEN r.name IS NOT NULL THEN 1 END) AS labelled_edges;")
    body = '<!doctype html><html><head><meta charset="utf-8"></head><body><article class="guide">'
    body += f'<h2>船舶故障图谱 V{VERSION} · SQLite 直接导入</h2><p>请选择 shipfaultkg。仅 MERGE/SET，不清空数据库。当前SQLite保留15个核心Sensor；既有数据库的额外节点不会自动删除，需单独核对、备份和维护。55个旧归档测点已完成外部备份及定向删除，详见 ../README_CN.md。全新库直接导入即可。此页面不依赖 :play。</p>'
    for title, statement in [('1. 唯一约束', constraint), ('2. 一次事务导入全部实体和关系', query), ('3. 核验真实数据库数量', verify)]:
        body += '<h3>' + title + '</h3><button onclick="navigator.clipboard.writeText(this.nextElementSibling.textContent)">复制此步代码</button><pre style="max-height:260px;overflow:auto;white-space:pre-wrap">' + html.escape(statement) + '</pre>'
    body += f'<p>目标：{len(nodes)}节点，{len(edges)}关系。第二步返回的是源文件规模，第三步才是实时核验。</p></article></body></html>'
    (OUTPUT / 'neo4j_import_guide.html').write_text(body, encoding='utf-8')


class QueryClient:
    def __init__(self, url, database, user, password):
        self.url = url.rstrip('/') + '/db/' + database + '/query/v2'
        self.auth = 'Basic ' + base64.b64encode((user + ':' + password).encode()).decode()
        self.bookmarks = []

    def run(self, statement, parameters=None):
        body = json.dumps({'statement': statement, 'parameters': parameters or {}, 'bookmarks': self.bookmarks}).encode()
        request = Request(self.url, data=body, headers={'Authorization': self.auth, 'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=120) as response:
                result = json.load(response)
        except HTTPError as error:
            raise RuntimeError(f'Neo4j HTTP {error.code}; check connection, user and password locally') from None
        if result.get('errors'):
            raise RuntimeError(json.dumps(result['errors'], ensure_ascii=False))
        self.bookmarks = result.get('bookmarks', self.bookmarks)
        data = result.get('data', {})
        return [dict(zip(data.get('fields', []), values)) for values in data.get('values', [])]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--url', default=os.getenv('NEO4J_URL', 'http://127.0.0.1:7474'))
    parser.add_argument('--database', default=os.getenv('NEO4J_DBNAME', 'shipfaultkg'))
    parser.add_argument('--user', default=os.getenv('NEO4J_USER', 'neo4j'))
    args = parser.parse_args()
    nodes, edges, plan = load_plan()
    prepare(nodes, edges, plan)
    if args.prepare_only:
        print(json.dumps({'nodes': len(nodes), 'edges': len(edges), 'batches': len(plan), 'csv_required': False}))
        return
    password = os.getenv('NEO4J_PASSWORD')
    if not password:
        if not sys.stdin.isatty():
            raise RuntimeError('请在交互终端运行，安全输入当前密码；也可通过已登录 Browser 运行生成的导入向导。')
        password = getpass.getpass('当前 Neo4j 密码（不显示，不保存）：')
    client = QueryClient(args.url, args.database, args.user, password)
    client.run('RETURN 1 AS connected')
    if not args.verify_only:
        client.run('CREATE CONSTRAINT shipkg_id IF NOT EXISTS FOR (n:ShipKG) REQUIRE n.id IS UNIQUE')
        for batch in plan:
            result = client.run(batch['statement'], batch['parameters'])
            if result[0]['processed'] != len(batch['parameters']['rows']):
                raise RuntimeError('Incomplete batch: endpoint missing; import not verified')
    count_nodes = client.run('MATCH (n:ShipKG) WHERE n.id IN $ids RETURN count(n) AS n', {'ids': [n['id'] for n in nodes]})[0]['n']
    count_edges = client.run('MATCH (:ShipKG)-[r]->(:ShipKG) WHERE r.id IN $ids RETURN count(r) AS n', {'ids': [e['id'] for e in edges]})[0]['n']
    result = {'database': args.database, 'source_nodes': len(nodes), 'source_edges': len(edges),
              'matched_nodes': count_nodes, 'matched_edges': count_edges, 'csv_required': False,
              'method': 'Neo4j HTTP Query API', 'verified': count_nodes == len(nodes) and count_edges == len(edges)}
    if not result['verified']:
        raise RuntimeError(json.dumps(result))
    (OUTPUT / 'neo4j_import_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
