"""Executable integrity and retrieval regression tests (no live credentials)."""
import json
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET
from import_neo4j import load_plan
from retrieve import Retriever, read_store
from schema import CAUSAL_RELS

HERE = Path(__file__).resolve().parent


class GraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = read_store()
        cls.retriever = Retriever()

    def test_target_and_no_dangling_references(self):
        s = self.store
        self.assertTrue(200 <= len(s['nodes']) <= 500)
        self.assertTrue(600 <= len(s['edges']) <= 1500)
        self.assertEqual(sum(n['kind']=='Subsystem' for n in s['nodes'].values()), 5)
        for e in s['edges'].values():
            self.assertIn(e['source'], s['nodes'])
            self.assertIn(e['target'], s['nodes'])
            self.assertIn(e['evidence_id'], s['evidence'])
            self.assertTrue(json.loads(e['props'])['name'])

    def test_v1_preserved(self):
        old = read_store(HERE / 'history' / 'v1_20261004' / 'output' / 'ship_fault_kg.sqlite')
        self.assertTrue(set(old['nodes']).issubset(self.store['nodes']))
        self.assertTrue(set(old['edges']).issubset(self.store['edges']))

    def test_direct_import_plan_complete(self):
        nodes, edges, plan = load_plan()
        self.assertEqual(sum(len(b['parameters']['rows']) for b in plan), len(nodes)+len(edges))
        for batch in plan:
            self.assertNotIn('DELETE', batch['statement'])
            self.assertNotIn('LOAD CSV', batch['statement'])
            for row in batch['parameters']['rows']:
                self.assertEqual(row['properties']['graph_version'], '2.0')

    def test_graphml_current(self):
        root = ET.parse(HERE / 'output' / 'ship_fault_kg.graphml')
        ns = {'g':'http://graphml.graphdrawing.org/xmlns'}
        self.assertEqual(len(root.findall('.//g:node', ns)), len(self.store['nodes']))
        self.assertEqual(len(root.findall('.//g:edge', ns)), len(self.store['edges']))

    def test_cases_and_paths(self):
        questions = json.loads((HERE / 'output' / 'eval_queries_v2.json').read_text(encoding='utf-8'))
        for q in questions:
            result = self.retriever.search(q['query'])
            if 'case_id' in q:
                self.assertEqual(result['cases'][0]['case_id'], q['case_id'])
            if 'coverage' in q:
                self.assertEqual(result['coverage'], q['coverage'])
            facts = {f['id'] for f in result['facts']}
            for p in result['causal_paths']:
                self.assertTrue(set(p['edge_ids']).issubset(facts))
                edges = [self.store['edges'][i] for i in p['edge_ids']]
                self.assertTrue(all(e['case_id']==p['case_id'] and e['relation'] in CAUSAL_RELS for e in edges))
                self.assertTrue(all(a['target']==b['source'] for a,b in zip(edges, edges[1:])))

    def test_unknown_queries_empty(self):
        for q in ('', '心脏冠状动脉狭窄如何治疗？', '航天器太阳能电池的辐射衰减原因是什么？'):
            result = self.retriever.search(q)
            self.assertEqual(result['coverage'], 'no_evidence')
            self.assertFalse(result['facts'])

    def test_llm_selection_evidence_checked(self):
        result = json.loads((HERE / 'output' / 'demo_v2_cpp.json').read_text(encoding='utf-8'))
        self.assertEqual(result['model'], 'qwen2.5:3b-instruct')
        facts = result['retrieval']['facts']
        for field, nums in result['validated_selection'].items():
            for number in nums:
                self.assertEqual(facts[number-1]['case_id'], 'pride_can_cpp_2014')
                if field == 'fault_chain':
                    self.assertIn(facts[number-1]['relation'], CAUSAL_RELS | {'PRECEDED'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
