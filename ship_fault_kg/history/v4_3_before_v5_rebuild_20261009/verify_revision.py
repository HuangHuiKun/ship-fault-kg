"""V4.3 regression: removed-source isolation, full corpus, provenance and retrieval."""
import hashlib
import json
from pathlib import Path
import re
import unittest
from retrieve import Retriever, read_store, make_prompt
from schema import VERSION, KIND_ZH
from corpus_knowledge import ARTICLES, SOURCE, normalize
from fault_profiles import PROFILES, IMPORTANT_SENSORS

HERE=Path(__file__).resolve().parent
REMOVED={'Azimuth_Thruster_CBM_Dataset.zip','UCI_Naval_Propulsion_CBM.zip'}
BASE=HERE/'history/v4_2_before_data_revision_20261008/output/ship_fault_kg.sqlite'
CORPUS=HERE.parent/'ship_fault_kg_data/01_datasets/marine_diesel_RAG_corpus_All_data/All_data'


class RevisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store=read_store()
        cls.old=read_store(BASE)
        cls.retriever=Retriever()
        cls.inventory=json.loads((HERE/'output/corpus_inventory.json').read_text(encoding='utf-8'))

    def test_scope_and_scale(self):
        self.assertEqual(len(self.store['nodes']),491)
        self.assertEqual(len(self.store['edges']),1200)
        self.assertEqual({n['kind'] for n in self.store['nodes'].values()},set(KIND_ZH))
        self.assertEqual(sum(n['kind']=='Case' for n in self.store['nodes'].values()),19)
        self.assertEqual(sum(n['kind']=='Sensor' for n in self.store['nodes'].values()),15)
        self.assertFalse(any(n['kind'] in ('Observation','Dataset') for n in self.store['nodes'].values()))

    def test_deleted_nodes_only_supported_by_removed_sources(self):
        gone=set(self.old['nodes'])-set(self.store['nodes'])
        self.assertTrue(gone)
        for ident in gone:
            supports={self.old['evidence'][e['evidence_id']]['source_file'] for e in self.old['edges'].values() if ident in (e['source'],e['target'])}
            self.assertTrue(supports,ident)
            self.assertTrue(supports <= REMOVED,(ident,supports))

    def test_no_removed_source_assertions(self):
        for table in ('evidence','passages'):
            self.assertFalse(any(x['source_file'] in REMOVED for x in self.store[table].values()))
        self.assertFalse(any(json.loads(n['props']).get('source_level')=='记录级' for n in self.store['nodes'].values()))

    def test_official_diagnostic_facts_preserved(self):
        for ident,e in self.old['edges'].items():
            ev=self.old['evidence'][e['evidence_id']]
            if e['case_id'] and ev['source_file'] not in REMOVED:
                self.assertIn(ident,self.store['edges'])
                new=self.store['edges'][ident]
                for key in ('source','target','relation','evidence_id','certainty','case_id'):
                    self.assertEqual(e[key],new[key])
        for ident,ev in self.old['evidence'].items():
            if ev['source_file'] not in REMOVED:
                self.assertEqual(ev,self.store['evidence'][ident])

    def test_all_entities_have_chinese_captions_and_version(self):
        for n in self.store['nodes'].values():
            p=json.loads(n['props'])
            self.assertEqual(p['graph_version'],VERSION)
            self.assertEqual(p['display_name'],n['name'])
            if n['kind'] in ('Fault','Action','Sensor'):
                self.assertRegex(n['name'],r'[\u4e00-\u9fff]')
        for e in self.store['edges'].values():
            self.assertIn(e['source'],self.store['nodes']);self.assertIn(e['target'],self.store['nodes'])
            self.assertIn(e['evidence_id'],self.store['evidence'])
            self.assertRegex(json.loads(e['props'])['name'],r'[\u4e00-\u9fff]')

    def test_all_corpus_files_indexed_and_fully_covered(self):
        self.assertEqual(len(self.inventory),1275)
        self.assertEqual({x['path'] for x in self.inventory},{p.relative_to(CORPUS).as_posix() for p in CORPUS.rglob('*.md')})
        for item in self.inventory:
            raw=(CORPUS/item['path']).read_bytes()
            self.assertEqual(item['sha256'],hashlib.sha256(raw).hexdigest())
            text=normalize(raw.decode('utf-8-sig'))
            reconstructed=''
            end=0
            for ident in item['passages']:
                p=self.store['passages'][ident]
                a,b=map(int,p['locator'].split(':normalized_chars=')[1].split(':'))
                self.assertLessEqual(a,end)
                self.assertEqual(p['text'],text[a:b])
                reconstructed+=p['text'][max(0,end-a):]
                end=b
            self.assertEqual(reconstructed,text)

    def test_corpus_assertions_have_exact_quote_and_review_flag(self):
        facts=[e for e in self.store['edges'].values() if e['certainty']=='corpus_statement']
        self.assertTrue(facts)
        for e in facts:
            ev=self.store['evidence'][e['evidence_id']]
            self.assertEqual(ev['source_kind'],'corpus_secondary')
            path,span=ev['locator'].split(':normalized_chars=')
            a,b=map(int,span.split(':'))
            text=normalize((CORPUS/path).read_text(encoding='utf-8-sig'))
            self.assertEqual(text[a:b],ev['quote'])
        self.assertEqual(sum(x['graph_article'] for x in self.inventory),4)

    def test_candidate_sentences_never_auto_asserted(self):
        candidates=json.loads((HERE/'output/corpus_candidates_pending_review.json').read_text(encoding='utf-8'))
        self.assertTrue(candidates)
        self.assertTrue(all(x['status']=='pending_review' and not x['graph_assertion'] for x in candidates))
        self.assertFalse(set(x['id'] for x in candidates)&set(self.store['edges']))

    def test_reference_entries_and_experimental_lookup(self):
        for profile in PROFILES:
            r=self.retriever.search(profile['name'],top_facts=12)
            self.assertEqual(r['coverage'],'reference_knowledge',profile['name'])
            self.assertEqual(r['knowledge_units'][0]['knowledge_id'],profile['id'])
            self.assertTrue(any(f['relation']=='CHECKS' for f in r['facts']))
        r=self.retriever.search('增压空气冷却器污损 75%')
        self.assertTrue(any(x['run_file']=='AC_Fouling/AC_Fouling_75_Load.csv' for x in r['dataset_matches']))

    def test_corpus_retrieval_paths_and_provenance(self):
        for article in ARTICLES:
            r=self.retriever.search(Path(article['path']).stem,top_facts=12)
            self.assertEqual(r['coverage'],'corpus_secondary')
            self.assertTrue(r['facts']);self.assertTrue(r['causal_paths'])
            for f in r['facts']:
                if f['certainty']=='corpus_statement':
                    self.assertTrue(f['locator']);self.assertFalse(f['page'])
            for path in r['causal_paths']:
                self.assertTrue(all(self.store['edges'][i]['case_id']==path['case_id'] for i in path['edge_ids']))
            self.assertIn('待专业人员复核',make_prompt(r))

    def test_paper_moved_without_changing_evidence_id(self):
        data=HERE.parent/'ship_fault_kg_data'
        name='Frontiers_2021_marine_converter_oscillations.pdf'
        self.assertTrue((data/'03_papers'/name).exists())
        self.assertFalse((data/'02_reports'/name).exists())
        matches=[n for n in self.store['nodes'].values() if name in n['aliases']]
        self.assertEqual(len(matches),1)
        self.assertEqual(json.loads(matches[0]['props'])['local_item'],'03_papers/'+name)

    def test_non_pilot_article_retrievable_and_prompt_separates_unreviewed_text(self):
        query='船机帮船舶柴油机废气涡轮增压器振动的主要原因有哪些'
        r=self.retriever.search(query)
        self.assertTrue(any(p['title']==query for p in r['passages']))
        self.assertIn('补充文本',make_prompt(r))
        for q in ('冠状动脉狭窄治疗','航天器太阳能电池的辐射衰减原因是什么？'):
            self.assertEqual(self.retriever.search(q)['coverage'],'no_evidence')


if __name__=='__main__':
    unittest.main(verbosity=2)
