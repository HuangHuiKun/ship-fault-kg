"""Read-only retrieval audit; write a report and reproducible results, not KG data.

Does not connect to Neo4j, invoke Ollama, or run the evaluation scripts' writers.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / 'ship_fault_kg'
sys.path.insert(0, str(KG))
from retrieve import Retriever, make_prompt
from build import node_id
from fault_profiles import PROFILES
from evaluate_fault_v3 import PARAPHRASES
from schema import RELATION_ZH, CAUSAL_RELS, DIAGNOSTIC_RELS


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def mean(values):
    return round(sum(values) / len(values), 4)


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', '<br>')


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(map(cell, headers)) + ' |',
                     '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                    ['| ' + ' | '.join(map(cell, row)) + ' |' for row in rows])


def pct(value):
    return f'{value * 100:.2f}%'


def main():
    now = datetime.now(timezone(timedelta(hours=8)))
    stamp = now.strftime('%Y%m%d')
    report_path = KG / 'output' / f'检索流程报告_V4.2_{stamp}.md'
    data_path = KG / 'output' / f'检索流程报告_复核数据_V4.2_{stamp}.json'
    template = (Path(__file__).with_name('retrieval_report_template.md')).read_text(encoding='utf-8')
    watched = [KG/'output'/name for name in ('ship_fault_kg.sqlite', 'build_report.json',
               'eval_queries_v4.json', 'retrieval_evaluation_v4.json', 'fault_retrieval_evaluation_v4.json')]
    before = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in watched}
    r = Retriever()
    questions = read_json(KG/'output/eval_queries_v4.json')
    saved_case = read_json(KG/'output/retrieval_evaluation_v4.json')
    saved_fault = read_json(KG/'output/fault_retrieval_evaluation_v4.json')
    naming = read_json(KG/'naming_v4.json')['nodes']
    names = {x['oldName']:x['name'] for x in naming.values() if not x['delete']}
    case_records = []
    for item in questions:
        result = r.search(item['query'], top_facts=10)
        row = {'id':item['id'], 'query':item['query'],
               'top_case':result['cases'][0]['case_id'] if result['cases'] else None,
               'coverage':result['coverage']}
        gold = []
        if 'case_id' in item:
            ranks = [x['case_id'] for x in result['cases']]
            rr = 1/(ranks.index(item['case_id'])+1) if item['case_id'] in ranks else 0
            gold = list(dict.fromkeys((item['case_id'], names.get(f[0],f[0]),f[1],names.get(f[2],f[2])) for f in item['gold']))
            found = [(f['case_id'],f['subject'],f['relation'],f['object']) for f in result['facts']]
            hits = {k:len(set(gold).intersection(found[:k])) for k in (5,10)}
            row.update(case_rr=rr, gold_count=len(gold), fact_hits_5=hits[5], fact_hits_10=hits[10],
                       recall_at_5=hits[5]/len(gold), recall_at_10=hits[10]/len(gold), precision_at_5=hits[5]/5)
        if 'dataset_run' in item:
            row['dataset_hit'] = any(m['run_file']==item['dataset_run'] and m['data_rows']==item['expected_rows']
                                     for m in result['dataset_matches'])
        if 'coverage' in item:
            row['coverage_hit'] = result['coverage']==item['coverage']
        case_records.append({'question':item, 'gold_after_name_mapping':gold, 'evaluation':row, 'retrieval':result})
    rows = [x['evaluation'] for x in case_records]
    case_rows = [x for x in rows if 'case_rr' in x]
    summary = {'strategy':'hybrid', 'question_count':len(rows), 'case_question_count':len(case_rows),
               'case_mrr_at_3':mean([x['case_rr'] for x in case_rows]),
               'case_recall_at_1':mean([x['case_rr']==1 for x in case_rows]),
               'fact_recall_at_5':mean([x['recall_at_5'] for x in case_rows]),
               'fact_recall_at_10':mean([x['recall_at_10'] for x in case_rows]),
               'fact_precision_at_5':mean([x['precision_at_5'] for x in case_rows]),
               'dataset_lookup_accuracy':mean([x['dataset_hit'] for x in rows if 'dataset_hit' in x]),
               'coverage_warning_accuracy':mean([x['coverage_hit'] for x in rows if 'coverage_hit' in x])}
    fault_records = []
    for index,(profile,paraphrase) in enumerate(zip(PROFILES,PARAPHRASES),1):
        gold = list(dict.fromkeys((node_id(*f[0].split('|')[:2]),f[1],node_id(*f[2].split('|')[:2])) for f in profile['facts']))
        for suffix,wording,query in [('A','名称',profile['name']),('B','改写',paraphrase)]:
            result = r.search(query, top_facts=12)
            units = [x['knowledge_id'] for x in result['knowledge_units']]
            rr = 1/(units.index(profile['id'])+1) if profile['id'] in units else 0
            found = [(r.edges[f['id']]['source'],f['relation'],r.edges[f['id']]['target']) for f in result['facts']]
            row = {'query':query, 'query_kind':wording, 'expected_context':profile['id'],
                   'gold_fact_count':len(gold), 'returned_fact_count':len(found), 'mrr_at_3':rr,
                   'coverage':result['coverage'], 'focused_reference':result['focused_reference']}
            for k in (5,10):
                hits = sum(x in gold for x in found[:k])
                row[f'recall_at_{k}'] = hits/len(gold)
                row[f'precision_at_{k}'] = hits/len(found[:k]) if found[:k] else 0
            fault_records.append({'report_id':f'F{index:02d}-{suffix}', 'evaluation':row,
                                  'gold_node_id_triples':gold, 'retrieval':result})
    fault_summary = {'question_count':len(fault_records), 'reference_unit_count':len(PROFILES)}
    for key in ('mrr_at_3','recall_at_5','recall_at_10','precision_at_5','precision_at_10'):
        fault_summary[key] = mean([x['evaluation'][key] for x in fault_records])
    summary_matches = all(saved_case['summary'][k]==v for k,v in summary.items()) and fault_summary==saved_fault['summary']
    details_match = rows==saved_case['details'] and [x['evaluation'] for x in fault_records]==saved_fault['details']
    if not summary_matches or not details_match:
        raise RuntimeError('Current retrieval differs from saved evaluation; report must be reviewed instead of claiming equivalence.')
    assert len(questions)==38 and len(fault_records)==24
    assert len(case_rows)==33 and len({x['question']['case_id'] for x in case_records if 'case_id' in x['question']})==19
    after = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in watched}
    if before!=after:
        raise RuntimeError('Read-only source inputs changed during report generation.')
    records = {x['question']['id']:x for x in case_records}
    replacements = {}
    replacements['{{STAMP}}'] = now.strftime('%Y-%m-%d %H:%M:%S（北京时间）')
    replacements['{{AUDIT_JSON}}'] = data_path.name
    replacements['{{CASE_METRICS}}'] = table(['指标','参与题数','本次复核值','评价对象'], [
        ['case MRR@3',33,summary['case_mrr_at_3'],'历史案例候选列表，非混合上下文总列表'],
        ['case Recall@1',33,pct(summary['case_recall_at_1']),'目标历史案例是否为案例列表第1名'],
        ['fact Recall@5',33,pct(summary['fact_recall_at_5']),'标注事实在前5条的覆盖率'],
        ['fact Recall@10',33,pct(summary['fact_recall_at_10']),'标注事实在前10条的覆盖率'],
        ['fact Precision@5',33,pct(summary['fact_precision_at_5']),'命中标注事实数 / 固定5'],
        ['dataset lookup accuracy',2,pct(summary['dataset_lookup_accuracy']),'文件相对路径和行数同时匹配'],
        ['coverage accuracy',3,pct(summary['coverage_warning_accuracy']),'覆盖状态字符串匹配，不评价警告文字质量']])
    replacements['{{FAULT_METRICS}}'] = table(['指标','参与题数','本次复核值','评价对象'],[
        [key,24,pct(value) if key!='mrr_at_3' else value,'参考单元排序' if key=='mrr_at_3' else '该单元全部标注诊断关系']
        for key,value in fault_summary.items() if key not in {'question_count','reference_unit_count'}])
    gold_total = sum(x['gold_count'] for x in case_rows)
    hits5_total = sum(x['fact_hits_5'] for x in case_rows)
    hits10_total = sum(x['fact_hits_10'] for x in case_rows)
    replacements['{{AGGREGATE_WORKED}}'] = (
        f"案例组33题的gold计数合计{gold_total}条（重复问题的gold也各自计入），前5条命中计数合计{hits5_total}，前10条合计{hits10_total}。"
        f"因此当前Precision@5的宏平均恰好等于{hits5_total}/(33×5)={pct(summary['fact_precision_at_5'])}；"
        f"Recall@5则是每题先除以本题gold数再平均，得到{pct(summary['fact_recall_at_5'])}，"
        f"不是把{hits5_total}/{gold_total}={pct(hits5_total/gold_total)}当作当前结果。"
        f"案例MRR是33个RR=1的平均，即33/33=1；参考MRR是24个RR=1的平均，即24/24=1。"
    )
    case_table = []
    for item in questions:
        evaluation = records[item['id']]['evaluation']
        if 'case_id' in item:
            target = r.case_names[item['case_id']]
            detail = f"gold={evaluation['gold_count']}；命中@5={evaluation['fact_hits_5']}；@10={evaluation['fact_hits_10']}"
            kind = '案例事实'
        elif 'dataset_run' in item:
            target = f"{item['dataset_run']}；{item['expected_rows']}行"
            detail = '命中' if evaluation['dataset_hit'] else '未命中'
            kind = '实验索引'
        else:
            target = item['coverage']; detail = '匹配预期状态' if evaluation['coverage_hit'] else '状态不匹配'; kind='覆盖边界'
        case_table.append([item['id'],kind,item['query'],target,detail])
    replacements['{{CASE_QUESTIONS}}'] = table(['编号','类型','完整问题','目标答案/上下文','本次结果'],case_table)
    replacements['{{FAULT_QUESTIONS}}'] = table(['报告编号','题型','完整问题','目标单元','gold条数','实际返回','R@5 / R@10'],[
        [x['report_id'],x['evaluation']['query_kind'],x['evaluation']['query'],x['evaluation']['expected_context'],
         x['evaluation']['gold_fact_count'],x['evaluation']['returned_fact_count'],
         pct(x['evaluation']['recall_at_5'])+' / '+pct(x['evaluation']['recall_at_10'])] for x in fault_records])
    replacements['{{PROFILE_TABLE}}'] = table(['故障参考单元','主要诊断事实数','适用范围'],[
        [p['name'],len(set((node_id(*f[0].split('|')[:2]),f[1],node_id(*f[2].split('|')[:2])) for f in p['facts'])),p['applicability']]
        for p in PROFILES])
    replacements['{{INDEX_COUNTS}}'] = table(['检索内容','实际数量','说明'],[
        ['上下文文档',len(r.case_index.docs),'19个历史案例 + 12个参考机理单元'],
        ['诊断事实文档',len(r.fact_edges),'只包含有上下文且属于DIAGNOSTIC_RELS的边'],
        ['因果类事实',sum(e['relation'] in CAUSAL_RELS for e in r.fact_edges.values()),'用于同一上下文路径搜索，是诊断事实的子集'],
        ['文本片段文档',len(r.passage_index.docs),'全部852片段建索引；每片段文本最多取前4000字符'],
        ['对齐实体',sum(n['kind'] in {'Fault','FaultType','Cause','Condition','Symptom','Component'} for n in r.nodes.values()),
         '名称/别名子串匹配；当前无FaultType标签'],
        ['实验故障运行关联',sum(e['relation']=='TESTS_FAULT' for e in r.edges.values()),'15个故障试验文件；另1个参照运行不作为故障命中']])
    replacements['{{EXAMPLES}}'] = '\n\n'.join(example_section(label,x) for label,x in [
        ('案例 A：Q01，柴油发电机轴瓦磨损—失电',records['Q01']),
        ('案例 B：Q08，大风浪下推进保护跳闸',records['Q08']),
        ('案例 C：参考故障改写题，主机疑似拉缸',{'question':{'query':fault_records[1]['evaluation']['query']},'retrieval':fault_records[1]['retrieval']}),
        ('案例 D：Q10，查询实验文件与行数',records['Q10']),
        ('案例 E：Q12，轴带—电网问题的证据边界',records['Q12']),
        ('案例 F：NEG1，图谱范围外问题',records['NEG1'])])
    q1 = records['Q01']; ev=q1['evaluation']
    gold_set = set(map(tuple,q1['gold_after_name_mapping']))
    replacements['{{Q01_HITS}}'] = table(['实际顺序','返回事实','是否在Q01 gold中'],[
        [i,f['subject']+' —'+f['relation_zh']+'→ '+f['object'],
         '命中' if (f['case_id'],f['subject'],f['relation'],f['object']) in gold_set else '未列入本题gold（不等于错误）']
        for i,f in enumerate(q1['retrieval']['facts'],1)])
    replacements['{{Q01_FORMULA}}'] = f"本次Q01：gold共{ev['gold_count']}条，前5条命中{ev['fact_hits_5']}条，前10条命中{ev['fact_hits_10']}条。故Recall@5={ev['fact_hits_5']}/{ev['gold_count']}={pct(ev['recall_at_5'])}；Recall@10={ev['fact_hits_10']}/{ev['gold_count']}={pct(ev['recall_at_10'])}；Precision@5={ev['fact_hits_5']}/5={pct(ev['precision_at_5'])}。目标案例在历史案例列表第1名，RR=1。"
    replacements['{{GOLD_APPENDIX}}'] = gold_appendix(case_records,r)
    replacements['{{DIAGNOSTIC_RELATIONS}}'] = '、'.join(f'`{x}`（{RELATION_ZH[x]}）' for x in sorted(DIAGNOSTIC_RELS))
    for key,value in replacements.items():
        template = template.replace(key,value)
    if '{{' in template:
        raise RuntimeError('Unexpanded report placeholder')
    audit = {'created_beijing':now.isoformat(),'graph_version':'4.2','read_only':True,
             'no_neo4j_connection':True,'no_llm_invocation':True,'saved_summaries_match':summary_matches,
             'saved_per_question_results_match':details_match,'input_sha256':before,
             'case_summary':summary,'reference_summary':fault_summary,
             'case_dataset_questions':case_records,'reference_fault_questions':fault_records,
             'scuffing_prompt_example':make_prompt(fault_records[1]['retrieval'])}
    data_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    report_path.write_text(template,encoding='utf-8')
    print(json.dumps({'report':str(report_path),'audit':str(data_path),'questions_replayed':len(rows)+len(fault_records),
                      'matches_saved_evaluations':summary_matches and details_match,
                      'source_inputs_unchanged':before==after,'report_characters':len(template)},ensure_ascii=False))


def example_section(label,record):
    result=record['retrieval']
    lines=['### '+label,'','输入：'+record['question']['query'],'',
           f"输出状态：`{result['coverage']}`；主上下文：`{result['primary_context']}`；参考单元锁定：`{result['focused_reference']}`。",'']
    if result['coverage_warning']:
        lines += ['边界提醒：'+result['coverage_warning'],'']
    ranked=result['cases']+result['knowledge_units']
    if ranked:
        lines += ['分开的候选列表（下表不是二者混合排序）：','',table(['列表','名称','上下文ID','得分'],[
            ['历史案例' if 'case_id' in x else '参考单元',x['name'],x.get('case_id',x.get('knowledge_id')),x['score']] for x in ranked]),'']
    if result['facts']:
        lines += ['按实际输出顺序列出全部返回事实；不同单元的事实不能拼成同一事故链：','',table(['序号','主体—关系—客体','所属单元','确定性','来源及物理页','得分'],[
            [i,f['subject']+' —'+f['relation_zh']+'→ '+f['object'],f['case_name'],f['certainty'],f['source_file']+'；第'+str(f['page'])+'页',f['score']]
            for i,f in enumerate(result['facts'],1)]),'']
    if result['causal_paths']:
        lines += ['完整保留下来的同上下文路径：','']
        for path in result['causal_paths']:
            lines += ['- '+path['chain']+f"（{len(path['edge_ids'])}条边；评分{path['score']}；上下文`{path['case_id']}`）"]
        lines += ['']
    elif result['facts']:
        lines += ['本次没有返回完整保留的2～5边因果路径；事实列表仍可包含单条诊断关系。','']
    if result['dataset_matches']:
        lines += ['实验数据匹配：','',table(['文件','负载','行数','列数','来源性质'],[
            [x['run_file'],x['load'],x['data_rows'],x['columns'],x['data_origin']] for x in result['dataset_matches']]),'']
    if result['passages']:
        lines += ['返回的原文片段索引（完整摘录见配套JSON）：','',table(['文件','标题','页/片段位置','得分'],[
            [x['source_file'],x['title'],x['page'] or '语料文章，无PDF页',x['score']] for x in result['passages']]),'']
    if not result['facts'] and not result['dataset_matches']:
        lines += ['事实、路径、实验匹配与文本片段为空；程序不据此给出确诊根因。','']
    return '\n'.join(lines)


def gold_appendix(records,retriever):
    groups={}
    for record in records:
        gold=record['gold_after_name_mapping']
        if not gold:
            continue
        signature=tuple(sorted(map(tuple,gold)))
        groups.setdefault(signature,[]).append(record['question']['id'])
    lines=[]
    for signature,ids in groups.items():
        lines += ['### '+ '、'.join(ids)+'：'+retriever.case_names[signature[0][0]],'']
        for _,subject,relation,obj in signature:
            lines += ['- '+subject+' —'+RELATION_ZH[relation]+f'（`{relation}`）→ '+obj]
        lines += ['']
    return '\n'.join(lines)


if __name__=='__main__':
    main()
