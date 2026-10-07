"""V3 schema, provenance, intentional removals and fault-entry retrieval smoke tests."""
import json
from pathlib import Path
import unittest
from retrieve import Retriever, read_store
from schema import CAUSAL_RELS
from fault_profiles import PROFILES, IMPORTANT_SENSORS
from build import clean

HERE=Path(__file__).resolve().parent
class V3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store=read_store(); cls.retriever=Retriever()
        cls.pages={x['file']:x['pages'] for x in json.loads((HERE/'output'/'new_source_pages_v3.json').read_text(encoding='utf-8'))}

    def test_sensor_selection_and_unchanged_original_data(self):
        sensors=[n for n in self.store['nodes'].values() if n['kind']=='Sensor']
        self.assertEqual(len(sensors),15)
        self.assertEqual({n['name'] for n in sensors},set(IMPORTANT_SENSORS))
        for n in sensors:
            if '原始电压' in json.loads(n['props'])['display_name']:
                self.assertEqual(json.loads(n['props'])['unit'],'V')

    def test_name_prefix_and_identity_preserved(self):
        for n in self.store['nodes'].values():
            if n['kind'] in {'Vessel','VesselType','Case'}:
                self.assertFalse(n['name'].startswith('匿名'))
        anonymous=[n for n in self.store['nodes'].values() if n['kind']=='Vessel' and json.loads(n['props']).get('anonymous')]
        self.assertEqual(len(anonymous),9)
        self.assertTrue(all('SD20' in n['name'] for n in anonymous))

    def test_new_sources_exact_anchors(self):
        for p in PROFILES:
            for _,_,_,file,page,anchor,_ in p['facts']:
                self.assertIn(clean(anchor).casefold(),self.pages[file][page-1].casefold())

    def test_fault_reference_units_not_invented_accidents(self):
        self.assertEqual(sum(n['kind']=='Case' for n in self.store['nodes'].values()),19)
        self.assertEqual(sum(n['kind']=='FaultType' for n in self.store['nodes'].values()),12)
        for p in PROFILES:
            for e in self.store['edges'].values():
                if e['case_id']==p['id'] and e['relation'] in CAUSAL_RELS:
                    props=json.loads(e['props'])
                    self.assertEqual(props['knowledge_layer'],'reference')
                    self.assertTrue(props['applicability'])

    def test_all_fault_entries_have_retrievable_evidence(self):
        for p in PROFILES:
            r=self.retriever.search(p['name'],top_facts=12)
            self.assertEqual(r['coverage'],'reference_knowledge',p['name'])
            self.assertTrue(r['knowledge_units'])
            self.assertEqual(r['knowledge_units'][0]['knowledge_id'],p['id'],p['name'])
            self.assertTrue(any(f['context_id']==p['id'] for f in r['facts']))
            self.assertTrue(any(f['relation']=='CHECKS' for f in r['facts']))
            for fact in r['facts']:
                self.assertTrue(fact['source_url']);self.assertTrue(fact['page'])
            for path in r['causal_paths']:
                self.assertTrue(all(self.store['edges'][x]['case_id']==path['case_id'] for x in path['edge_ids']))

    def test_unknown_query_does_not_create_evidence(self):
        self.assertEqual(self.retriever.search('冠状动脉狭窄治疗')['coverage'],'no_evidence')

if __name__=='__main__':
    unittest.main(verbosity=2)
