"""V4 ontology, identity, provenance and retrieval regression checks."""
import json
from pathlib import Path
import unittest
from retrieve import Retriever, read_store, is_reference
from schema import KIND_ZH, CAUSAL_RELS
from fault_profiles import PROFILES, IMPORTANT_SENSORS

HERE=Path(__file__).resolve().parent


class V4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store=read_store()
        cls.old=read_store(HERE/'history/v3_before_redesign_20261006/output/ship_fault_kg.sqlite')
        cls.retriever=Retriever()

    def test_counts_and_unified_types(self):
        self.assertEqual(len(self.store['nodes']),491)
        self.assertEqual(len(self.store['edges']),1185)
        self.assertEqual({n['kind'] for n in self.store['nodes'].values()},set(KIND_ZH))
        self.assertEqual(len(KIND_ZH),15)
        faults=[n for n in self.store['nodes'].values() if n['kind']=='Fault']
        self.assertEqual(len(faults),114)
        self.assertEqual(sum(is_reference(n) for n in faults),12)

    def test_identity_and_evidence_preserved(self):
        removed={n['id'] for n in self.old['nodes'].values() if n['kind']=='Dataset'}
        removed.update(json.loads((HERE/'refinement_v4_1.json').read_text(encoding='utf-8'))['remove_vessel_types'])
        self.assertEqual(set(self.store['nodes']),set(self.old['nodes'])-removed)
        self.assertEqual(self.store['evidence'],self.old['evidence'])
        self.assertEqual(self.store['passages'],self.old['passages'])
        for e in self.store['edges'].values():
            old=self.old['edges'][e['id']]
            self.assertEqual(e['evidence_id'],old['evidence_id'])
            self.assertEqual(e['case_id'],old['case_id'])
            self.assertEqual(e['certainty'],old['certainty'])
            self.assertIn(e['source'],self.store['nodes']);self.assertIn(e['target'],self.store['nodes'])
            if e['certainty'] in {'possible','probable'}:
                self.assertTrue(json.loads(e['props'])['name'].startswith(('可能','很可能')))

    def test_dataset_provenance_migration(self):
        moved=[e for e in self.store['edges'].values() if json.loads(e['props']).get('original_dataset_id')]
        self.assertEqual(len(moved),51)
        for e in moved:
            self.assertEqual(e['relation'],'DOCUMENTED_BY')
            self.assertEqual(self.store['nodes'][e['target']]['kind'],'Source')
            self.assertNotEqual(e['source'],e['target'])
            self.assertFalse(json.loads(e['props'])['is_causal'])

    def test_role_properties_and_normal_states(self):
        ns=list(self.store['nodes'].values())
        self.assertEqual(sum(n['kind']=='Vessel' for n in ns),22)
        self.assertEqual(sum(n['kind']=='Vessel' and json.loads(n['props'])['entity_level']=='船型' for n in ns),5)
        self.assertEqual(sum(n['kind']=='System' and json.loads(n['props'])['system_level']=='功能系统' for n in ns),5)
        self.assertEqual(sum(n['kind']=='System' and json.loads(n['props'])['system_level']=='动力架构' for n in ns),3)
        normal=[n for n in ns if json.loads(n['props']).get('semantic_class')=='normal_reference']
        self.assertEqual(len(normal),3);self.assertTrue(all(n['kind']=='Condition' for n in normal))

    def test_chinese_names_original_variables_and_units(self):
        ns=list(self.store['nodes'].values())
        sensors=[n for n in ns if n['kind']=='Sensor']
        self.assertEqual(len(sensors),15)
        self.assertEqual({json.loads(n['props'])['original_column_name'] for n in sensors},set(IMPORTANT_SENSORS))
        for n in ns:
            if n['kind'] in {'Sensor','Fault','Action'}:
                self.assertRegex(n['name'],r'[\u4e00-\u9fff]')
        for n in sensors:
            if '原始电压' in n['name']:
                self.assertEqual(json.loads(n['props'])['unit'],'V')

    def test_no_ship_prefix_in_case_equipment_component(self):
        ships=[n['name'] for n in self.old['nodes'].values() if n['kind']=='Vessel' and not json.loads(n['props']).get('anonymous')]
        for n in self.store['nodes'].values():
            if n['kind'] in {'Case','Equipment','Component'}:
                self.assertFalse(any(n['name'].startswith(x) for x in ships),n['name'])
                self.assertNotRegex(n['name'],r'^SD\d{4}-\d{2}')

    def test_all_reference_entries_and_causal_scopes(self):
        for p in PROFILES:
            r=self.retriever.search(p['name'],top_facts=12)
            self.assertEqual(r['coverage'],'reference_knowledge',p['name'])
            self.assertEqual(r['knowledge_units'][0]['knowledge_id'],p['id'],p['name'])
            self.assertTrue(any(f['relation']=='CHECKS' for f in r['facts']),p['name'])
            self.assertTrue(r['facts'])
            for f in r['facts']:
                self.assertEqual(f['context_role'],'reference')
                self.assertTrue(f['source_url']);self.assertTrue(f['page'])
            for path in r['causal_paths']:
                self.assertTrue(all(self.store['edges'][i]['case_id']==path['case_id'] for i in path['edge_ids']))

    def test_experiment_lookup_old_english_and_chinese_alias(self):
        for query in ['Air-cooler fouling 75%', '增压空气冷却器污损 75%']:
            rows=self.retriever.search(query)['dataset_matches']
            self.assertTrue(any(r['run_file']=='AC_Fouling/AC_Fouling_75_Load.csv' for r in rows),query)

    def test_reference_category_edges_not_causal(self):
        for e in self.store['edges'].values():
            if e['relation']=='INSTANCE_OF':
                self.assertEqual(self.store['nodes'][e['source']]['kind'],'Fault')
                self.assertEqual(self.store['nodes'][e['target']]['kind'],'Fault')
                self.assertTrue(is_reference(self.store['nodes'][e['target']]))
                self.assertFalse(json.loads(e['props'])['is_causal'])

    def test_negative_query(self):
        self.assertEqual(self.retriever.search('冠状动脉狭窄治疗')['coverage'],'no_evidence')

    def test_refinement_classification_provenance(self):
        config=json.loads((HERE/'refinement_v4_1.json').read_text(encoding='utf-8'))
        old_edges=[e for e in self.old['edges'].values() if e['target'] in config['remove_vessel_types']]
        self.assertEqual(len(old_edges),12)
        for edge in old_edges:
            self.assertNotIn(edge['id'],self.store['edges'])
            self.assertIn(edge['evidence_id'],self.store['evidence'])
            props=json.loads(self.store['nodes'][edge['source']]['props'])
            proof=[p for p in props['vessel_type_provenance'] if p['former_edge_id']==edge['id']]
            self.assertEqual(len(proof),1)
            self.assertEqual(proof[0]['evidence_id'],edge['evidence_id'])
            self.assertIn(config['remove_vessel_types'][edge['target']],props['vessel_types'])
        for ident, (previous,current) in config['equipment_names'].items():
            node=self.store['nodes'][ident]
            self.assertEqual(node['name'],current)
            self.assertIn(previous,node['aliases'])
            self.assertIn('original_name',json.loads(node['props']))
        equipment=[n for n in self.store['nodes'].values() if n['kind']=='Equipment']
        self.assertEqual(len(equipment),19)
        self.assertTrue(all(not n['name'].endswith('系统') for n in equipment))

    def test_approved_source_merge_preserves_record_scope(self):
        old=read_store(HERE/'history/v4_1_before_source_merge_20261006/output/ship_fault_kg.sqlite')
        observations={n['id'] for n in old['nodes'].values() if n['kind']=='Observation'}
        sources={n['id'] for n in old['nodes'].values() if n['kind']=='Source'}
        self.assertEqual(len(observations),12)
        self.assertEqual(len(sources),30)
        self.assertEqual(set(self.store['nodes']),set(old['nodes']))
        self.assertEqual(set(self.store['edges']),set(old['edges']))
        self.assertFalse(any(n['kind']=='Observation' for n in self.store['nodes'].values()))
        self.assertEqual(sum(n['kind']=='Source' for n in self.store['nodes'].values()),42)
        for ident in sources:
            self.assertEqual(json.loads(self.store['nodes'][ident]['props'])['source_level'],'资料级')
        for ident in observations:
            self.assertEqual(self.store['nodes'][ident]['kind'],'Source')
            self.assertEqual(self.store['nodes'][ident]['name'],old['nodes'][ident]['name'])
            self.assertEqual(self.store['nodes'][ident]['aliases'],old['nodes'][ident]['aliases'])
            current=json.loads(self.store['nodes'][ident]['props'])
            self.assertEqual(current['source_level'],'记录级')
            self.assertEqual(current['source_record_type'],'监测摘要')
            for key,value in json.loads(old['nodes'][ident]['props']).items():
                if key not in {'graph_version','kind_zh'}:
                    self.assertEqual(current[key],value)
            parents=[e for e in self.store['edges'].values() if e['source']==ident and e['relation']=='DOCUMENTED_BY']
            self.assertEqual(len(parents),1)
            self.assertIn(parents[0]['target'],sources)
            self.assertEqual(current['source_id'],parents[0]['target'])
        observation_edges={i:e for i,e in old['edges'].items() if e['source'] in observations or e['target'] in observations}
        for ident,edge in observation_edges.items():
            current=self.store['edges'][ident]
            for key in ('source','target','relation','evidence_id','case_id','certainty'):
                self.assertEqual(current[key],edge[key])


if __name__=='__main__':
    unittest.main(verbosity=2)
