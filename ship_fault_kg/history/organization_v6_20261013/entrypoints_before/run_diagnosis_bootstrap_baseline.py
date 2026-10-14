"""Run the unchanged V5 probe on synthetic inputs; keep reference labels separate."""
import argparse
import collections
import hashlib
import json
import math
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT))
from ship_fault_kg.v5.retrieve import retrieve

OUT = ROOT / 'ship_fault_kg/diagnosis_bootstrap/v1'
DB = ROOT / 'ship_fault_kg/output/v5/ship_fault_kg.sqlite'


def read_rows(name):
    return [json.loads(line) for line in (OUT/name).read_text(encoding='utf-8').splitlines() if line.strip()]


def run(split, k):
    manifest=json.loads((OUT/'dataset_manifest.json').read_text(encoding='utf-8'))
    if hashlib.sha256(DB.read_bytes()).hexdigest()!=manifest['graph_sqlite_sha256']:
        raise ValueError('Graph changed since labels were built; review/regenerate labels before running baseline')
    labels={l['report_id']:l for l in read_rows('retrieval_reference_labels.jsonl')}
    results=[]
    for row in read_rows('retrieval_inputs.jsonl'):
        label=labels[row['report_id']]
        if split!='all' and label['split']!=split: continue
        start=time.perf_counter()
        # The reference label is NEVER passed to the retriever.
        pack=retrieve(row['diagnosis_text'],k=k)
        elapsed=time.perf_counter()-start
        ids={f['id'] for r in pack['results'] for f in r['facts']}
        reference=set(label['reference_assertion_ids'])
        hits=sorted(ids & reference)
        rank=next((i for i,r in enumerate(pack['results'],1)
                   if r['fault_id']==label['intended_target_concept_id']),None)
        results.append(dict(report_id=row['report_id'],sample_type=label['sample_type'],system=label['system'],split=label['split'],
            intended_target_name=label['intended_target_name'],intended_target_kind=label['intended_target_kind'],
            candidate_target_rank=rank,candidate_metric_eligible=label['intended_target_kind']=='Fault',
            returned_candidates=[dict(fault_id=r['fault_id'],fault_name=r['fault_name'],lexical_score=r['lexical_score'],
                fact_count=len(r['facts']),assertion_ids=[f['id'] for f in r['facts']],
                scope_ids=sorted({f['scope_id'] for f in r['facts']})) for r in pack['results']],
            distinct_returned_assertions=len(ids),partial_reference_count=len(reference),partial_reference_hits=hits,
            partial_reference_coverage=len(hits)/len(reference) if reference else None,
            evidence_output_warning=pack['warning'],latency_seconds=round(elapsed,6),
            behavior_review_required=label['intended_target_concept_id'] is None,
            expected_behavior=label['expected_behavior'],
            evaluation_note='预设目标出现及部分参考声明覆盖，仅为合成开发基线；不等于独立检索质量或诊断正确率。'))
    def aggregate(rows):
        eligible=[r for r in rows if r['candidate_metric_eligible']]
        covered=[r['partial_reference_coverage'] for r in rows if r['partial_reference_coverage'] is not None]
        latencies=sorted(r['latency_seconds'] for r in rows)
        return dict(reports=len(rows),fault_target_reports=len(eligible),
            intended_fault_target_hits=sum(r['candidate_target_rank'] is not None for r in eligible),
            intended_fault_target_hit_rate=sum(r['candidate_target_rank'] is not None for r in eligible)/len(eligible) if eligible else None,
            partial_reference_coverage_macro=statistics.mean(covered) if covered else None,
            no_candidate_reports=sum(not r['returned_candidates'] for r in rows),
            no_fact_reports=sum(r['distinct_returned_assertions']==0 for r in rows),
            behavior_reviews_required=sum(r['behavior_review_required'] for r in rows),
            latency_median_seconds=statistics.median(latencies) if latencies else None,
            latency_p95_seconds=latencies[max(0,math.ceil(len(latencies)*0.95)-1)] if latencies else None)
    summary=dict(method='unchanged_v5_alias_character_bigram_and_scope_expansion',k=k,split=split,
        graph_sqlite_sha256=manifest['graph_sqlite_sha256'],dataset_version=manifest['dataset_version'],
        overall=aggregate(results),
        by_type={key:aggregate([r for r in results if r['sample_type']==key]) for key in sorted({r['sample_type'] for r in results})},
        by_system={key:aggregate([r for r in results if r['system']==key]) for key in sorted({r['system'] for r in results})},
        interpretation='只记录合成预设目标命中与部分参考集合覆盖；State不能作为当前Fault候选，单独标为不适用。边界题不自动判为拒答正确或错误。',
        graph_sqlite_unchanged=hashlib.sha256(DB.read_bytes()).hexdigest()==manifest['graph_sqlite_sha256'])
    (OUT/'baseline_v5.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in results),encoding='utf-8')
    (OUT/'baseline_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    markdown=['# V5基线结果与检索启动建议','',
        '输入为本批合成初始报告，参考标签单独关联；未修改V5检索代码或知识图谱。',
        '本次分区：`%s`；Top-K：%d；报告数量：%d。' % (split,k,len(results)),'',
        '## 1. 明确名称与症状报告对比','',
        '| 报告类型 | 报告数 | 可按Fault候选计分 | 预设目标出现在前K项 | 部分参考声明平均覆盖 |',
        '| --- | ---: | ---: | ---: | ---: |']
    for typ,title in [('explicit_fault','明确候选名称'),('symptom_only','仅描述症状')]:
        a=summary['by_type'].get(typ)
        if a:
            markdown.append('| %s | %d | %d | %d/%d | %.2f%% |' % (title,a['reports'],a['fault_target_reports'],
                a['intended_fault_target_hits'],a['fault_target_reports'],100*a['partial_reference_coverage_macro']))
    markdown+=['','每类另有State目标时，不纳入当前仅Fault候选的目标出现率。部分参考声明集合不完整，覆盖比例不能当作完整Recall；以上也不是独立测试或诊断准确率。','',
        '## 2. 未出现在Fault候选中的预设目标','',
        '| 报告 | 子系统 | 题型 | 预设目标 | 返回候选 |','| --- | --- | --- | --- | --- |']
    for r in results:
        if r['candidate_metric_eligible'] and r['candidate_target_rank'] is None:
            markdown.append('| %s | %s | %s | %s | %s |' % (r['report_id'],r['system'],r['sample_type'],
                r['intended_target_name'],'、'.join(c['fault_name'] for c in r['returned_candidates'])))
    markdown+=['','这类结果优先用于检查设备约束、状态/参数入口和症状召回；不能仅凭预设目标未返回，判定其他候选是错误诊断。','',
        '## 3. 边界样本人工复核清单','',
        '| 报告 | 类型 | 当前候选 | 后续应检查的行为 |','| --- | --- | --- | --- |']
    behavior_names={
        'negated_normal':'是否保留否定，未将排除项写成肯定诊断',
        'missing_fields':'是否指出缺失且未编造数值、分数或唯一根因',
        'competing_hypotheses':'是否给出鉴别检查，未把非特异性症状确诊为唯一根因',
        'unsupported_threshold':'是否索取适用型号/手册，未编造精确阈值、扭矩和运行时长'}
    for r in results:
        if r['behavior_review_required']:
            markdown.append('| %s | %s | %s | %s |' % (r['report_id'],r['sample_type'],
                '、'.join(c['fault_name'] for c in r['returned_candidates']),behavior_names[r['sample_type']]))
    markdown+=['','当前检索器只返回候选和证据，尚无生成阶段。返回条件性参考本身不等于错误；上表需要在后续证据组织/报告生成阶段核验，不自动报告“拒答准确率”。','',
        '## 4. 建议的第一轮检索改进','',
        '1. 扩展设备、状态、物理量入口，并保留否定与缺失语义。',
        '2. 对事实按问题相关性和适用性筛选，控制证据总量。',
        '3. 加入原文片段召回，区分文本证据与已建图声明。',
        '4. 对同一批输入重复运行，比较目标出现、部分参考覆盖和边界行为；人工复核后再形成正式金标准。','']
    (OUT/'基线结果与检索启动建议.md').write_text('\n'.join(markdown),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--split',choices=['bootstrap_dev','bootstrap_check','all'],default='bootstrap_dev')
    p.add_argument('--top-k',type=int,default=3)
    args=p.parse_args()
    if args.top_k<1: p.error('top-k must be positive')
    run(args.split,args.top_k)
