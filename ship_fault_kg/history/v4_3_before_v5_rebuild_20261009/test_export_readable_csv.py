"""Read-only current-graph checks and disposable refresh/CSV safety tests."""
import csv
from contextlib import closing
import hashlib
import io
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from export_readable_csv import HEADERS, export_csv, make_rows, safe_cell, summary
from schema import VERSION

DB = Path(__file__).resolve().parent / 'output' / 'ship_fault_kg.sqlite'


class ReadableCSVTests(unittest.TestCase):
    def test_all_graph_entities_edges_and_evidence(self):
        rows, info = make_rows(DB)
        report=json.loads(DB.with_name('build_report.json').read_text(encoding='utf-8'))
        self.assertEqual(info['node_count'], report['node_count'])
        self.assertEqual(info['relationship_count'], report['edge_count'])
        self.assertEqual(info['graph_version'], VERSION)
        self.assertEqual(len(rows), info['relationship_count'] + info['isolated_node_count'])
        self.assertTrue(all(len(row) == len(HEADERS) for row in rows))
        mapped = [dict(zip(HEADERS, row)) for row in rows]
        with closing(sqlite3.connect(f'file:{DB.as_posix()}?mode=ro', uri=True)) as conn:
            nodes = dict(conn.execute('SELECT id,name FROM nodes'))
            edges = {r[0]: r[1:] for r in conn.execute('SELECT id,source,target,evidence_id FROM edges')}
        actual_nodes = set()
        for row in mapped:
            actual_nodes.add(row['起点ID'])
            self.assertEqual(row['起点节点'], nodes[row['起点ID']])
            if row['终点ID']:
                actual_nodes.add(row['终点ID'])
                self.assertEqual(row['终点节点'], nodes[row['终点ID']])
                self.assertEqual((row['起点ID'],row['终点ID'],row['证据ID']),edges[row['关系ID']])
        self.assertEqual(actual_nodes, set(nodes))
        self.assertEqual({r['关系ID'] for r in mapped if r['关系ID']}, set(edges))

    def test_repeated_export_replaces_same_file_and_keeps_sqlite_unchanged(self):
        before = hashlib.sha256(DB.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix='shipkg-csv-test-', dir=DB.parent.resolve()) as work:
            target = Path(work) / 'table.csv'
            export_csv(DB, target)
            first = target.read_bytes()
            export_csv(DB, target)
            self.assertEqual(target.read_bytes(), first)
            self.assertTrue(first.startswith(b'\xef\xbb\xbf'))
            self.assertEqual(list(csv.reader(io.StringIO(first.decode('utf-8-sig'))))[0], HEADERS)
        self.assertEqual(hashlib.sha256(DB.read_bytes()).hexdigest(), before)

    def test_refresh_node_name_property_and_added_isolated_node(self):
        with tempfile.TemporaryDirectory(prefix='shipkg-csv-test-', dir=DB.parent.resolve()) as work:
            db = Path(work) / 'copy.sqlite'
            shutil.copy2(DB, db)
            with closing(sqlite3.connect(db)) as conn:
                ident, raw = conn.execute('SELECT id,props FROM nodes ORDER BY id LIMIT 1').fetchone()
                props = json.loads(raw)
                props['note'] = '新增测试属性'
                conn.execute('UPDATE nodes SET name=?,props=? WHERE id=?',
                             ('改名测试节点', json.dumps(props, ensure_ascii=False), ident))
                conn.execute('INSERT INTO nodes VALUES(?,?,?,?,?)',
                             ('test:isolated','Fault','新增孤立节点','',json.dumps({'graph_version':VERSION},ensure_ascii=False)))
                conn.commit()
            result = export_csv(db)
            with Path(result['output']).open(encoding='utf-8-sig', newline='') as handle:
                rows = list(csv.DictReader(handle))
            matches = [r for r in rows if r['起点ID']==ident or r['终点ID']==ident]
            self.assertTrue(matches)
            for row in matches:
                side = '起点' if row['起点ID']==ident else '终点'
                self.assertEqual(row[side+'节点'], '改名测试节点')
                self.assertIn('新增测试属性',row[side+'主要属性'])
            isolated = next(r for r in rows if r['起点ID']=='test:isolated')
            self.assertEqual(isolated['关系名称'], '暂无关联关系')

    def test_csv_special_characters_and_formula_guard(self):
        self.assertEqual(safe_cell('=1+1'), "'=1+1")
        self.assertEqual(safe_cell(' @SUM(A1)'), "' @SUM(A1)")
        self.assertEqual(safe_cell('正常节点'), '正常节点')
        text = '带逗号,引号"和\n换行'
        handle = io.StringIO(newline='')
        csv.writer(handle).writerow([safe_cell(text)])
        self.assertEqual(next(csv.reader(io.StringIO(handle.getvalue())))[0], text)

    def test_missing_and_zero_attributes_not_confused(self):
        node={'aliases':'','properties':{'warning_hours':0,'warning_months':None,'anonymous':False}}
        result=summary(node)
        self.assertIn('预警时间（小时）：0', result)
        self.assertIn('船舶身份未公开：否', result)
        self.assertNotIn('预警时间（月）', result)

    def test_locked_export_retains_last_valid_file(self):
        with tempfile.TemporaryDirectory(prefix='shipkg-csv-test-', dir=DB.parent.resolve()) as work:
            target=Path(work)/'table.csv'
            export_csv(DB,target)
            before=target.read_bytes()
            with patch('export_readable_csv.atomic_replace', side_effect=PermissionError('locked')):
                with self.assertRaises(PermissionError):
                    export_csv(DB,target)
            self.assertEqual(target.read_bytes(),before)
            self.assertEqual(list(Path(work).glob('*.tmp')),[])


if __name__=='__main__':
    unittest.main(verbosity=2)
