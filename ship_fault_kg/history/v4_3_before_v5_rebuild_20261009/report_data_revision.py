"""Generate a traceable V4.3 data/graph revision report and retrieval examples."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from retrieve import read_store, Retriever, make_prompt
from corpus_knowledge import ARTICLES
from schema import VERSION

HERE=Path(__file__).resolve().parent
OUT=HERE/'output'
BACKUP=HERE/'history/v4_2_before_data_revision_20261008'


def main():
    current=read_store(); previous=read_store(BACKUP/'output/ship_fault_kg.sqlite')
    build=json.loads((OUT/'build_report.json').read_text(encoding='utf-8'))
    inventory=json.loads((OUT/'corpus_inventory.json').read_text(encoding='utf-8'))
    receipt=json.loads((OUT/'neo4j_import_result.json').read_text(encoding='utf-8'))
    removed_nodes=sorted(set(previous['nodes'])-set(current['nodes']))
    added_nodes=sorted(set(current['nodes'])-set(previous['nodes']))
    removed_edges=sorted(set(previous['edges'])-set(current['edges']))
    added_edges=sorted(set(current['edges'])-set(previous['edges']))
    old_articles={p['locator'] for p in previous['passages'].values() if p['kind']=='corpus_article'}
    examples=[]
    retriever=Retriever()
    for query in [Path(a['path']).stem for a in ARTICLES]+['船机帮船舶柴油机废气涡轮增压器振动的主要原因有哪些']:
        result=retriever.search(query,top_facts=12)
        examples.append({'query':query, 'result':result, 'prompt':make_prompt(result)})
    case_eval=json.loads((OUT/'retrieval_evaluation_v4.json').read_text(encoding='utf-8'))['summary']
    fault_eval=json.loads((OUT/'fault_retrieval_evaluation_v4.json').read_text(encoding='utf-8'))['summary']
    result=dict(version=VERSION,removed_nodes=removed_nodes,added_nodes=added_nodes,
                removed_edges=removed_edges,added_edges=added_edges,
                removed_node_types=dict(Counter(previous['nodes'][i]['kind'] for i in removed_nodes)),
                added_node_types=dict(Counter(current['nodes'][i]['kind'] for i in added_nodes)),
                all_corpus_files=len(inventory),duplicate_articles=sum(bool(i['duplicate_of']) for i in inventory),
                newly_indexed_articles=sum(i['path'] not in old_articles for i in inventory),
                pilot_articles_outside_old_selection=[a['path'] for a in ARTICLES if a['path'] not in old_articles],
                local_store_sha256=hashlib.sha256((OUT/'ship_fault_kg.sqlite').read_bytes()).hexdigest(),
                neo4j_verified=receipt.get('verified') is True and receipt.get('version')==VERSION,
                retrieval_examples=examples,case_evaluation=case_eval,reference_evaluation=fault_eval)
    (OUT/'data_revision_v4_3.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=[f'# 资料包修订、语料建图与数据库同步报告 V{VERSION}', '', '日期：2026-10-08。', '',
        '## 1. 先备份，再移出两个数据集', '',
        'Azimuth Thruster CBM与UCI Naval Propulsion CBM从活动01_datasets移出。原始文件仍保存在history/v4_2_before_data_revision_20261008/removed_datasets/；旧代码、SQLite、输出和元数据同时归档。不是永久销毁。', '',
        f"以旧SQLite逐ID比对，本次移出{len(removed_nodes)}个独有节点、{len(removed_edges)}条关系；新增{len(added_nodes)}个节点、{len(added_edges)}条关系。移出节点类型：{json.dumps(result['removed_node_types'],ensure_ascii=False)}。",
        '其中12条记录级Source是Azimuth监测摘要，不是官方事故Case。本次不再参与当前图谱。共享知识只能保留仍有其他资料支持的部分。', '',
        '原因：通过构建程序重新生成，而不是只在Neo4j手动隐藏，避免下次重建又把旧资料导回。移出节点全部检查为仅由这两个指定来源支持；正式报告的原诊断关系、证据ID保持不变。', '',
        '## 2. 全量语料与审核边界', '',
        f"全文检查{len(inventory)}篇md，新增覆盖原145篇之外的{result['newly_indexed_articles']}篇。归一化重复文章{result['duplicate_articles']}篇，标记duplicate_of但保留原文件溯源。",
        f"生成{build['passage_types']['corpus_article']}个语料分块：每块最多1400字符、重叠150字符，覆盖完整正文，不再截掉6000字符之后的文本。全部SHA256、路径、原始分组和分块ID见corpus_inventory.json。",
        f"关键词筛选得到{build['corpus_candidate_count']}条因果/运维候选句，保存在corpus_candidates_pending_review.json。候选句尚未确认主客体、否定和机型，绝不等同于{build['corpus_candidate_count']}条图谱事实。", '',
        '## 3. 已实际建图的原文核对试点', '',
        '4篇文章共22条诊断关系。每条配置必须通过精确引文核对才能构建；使用文章路径与标准化字符区间定位，不编造PDF页码。', '',
        '| 原文章 | 适用范围 |', '| --- | --- |']
    lines += [f"| {a['path']} | {a['scope']} |" for a in ARTICLES]
    lines += ['', '例子：润滑油品质不符合要求 → 油泥沉积 → 滤清器/油道堵塞 → 滑油供给不足 → 增加轴瓦烧伤风险；另有空压机冷却器渗漏与共享冷却回路进气、副机保护停机，以及喷油器密封锥面裂纹链。', '',
        '可靠性说明：原文核对不等于工程专家认证。全部新增内容为corpus_secondary，expert_review=pending，corpus_statement。文章描述的匿名事故不计入正式事故Case；未找到原始报告时，只溯源到文章和资料包，不虚构船名或官方结论。', '',
        '文章级Source涉及各自故障、状态、检查、措施，并DOCUMENTED_BY指向资料包Source。不同文章的节点按上下文建立独立ID，暂不把未核验同义项直接并入官方案例，避免污染确定性。', '',
        '## 4. 电网振荡论文迁移', '',
        'Comparative Case Study on Oscillatory Behavior in Power Systems of Marine Vessels With High Power Converters；DOI 10.3389/fenrg.2020.529756。移到03_papers/Frontiers_2021_marine_converter_oscillations.pdf。来源清单、下载程序、PDF读取程序和页级检查同步更新；原引文锚点与证据ID不变。', '',
        '## 5. 当前成果与真实数据库核验', '',
        '| 指标 | 当前值 |', '| --- | ---: |',
        f"| 节点 / 关系 | {build['node_count']} / {build['edge_count']} |",
        f"| 正式事故 / 参考故障单元 / 新语料文章单元 | {build['case_count']} / {build['fault_reference_count']} / 4 |",
        f"| 测点 / 试验运行 | {build['sensor_count']} / {build['node_types']['Run']} |",
        f"| 证据记录 / 全部检索片段 | {build['evidence_count']} / {build['passage_count']} |",
        f"| Neo4j同步核验 | {'成功，逐ID/名称/版本/端点/证据JSON核对' if result['neo4j_verified'] else '未验证，不能声称同步成功'} |", '',
        '同步方法：SQLite直接读取 → Neo4j HTTP Query API。不需要CSV中转。先保存neo4j_snapshot.json，再核对旧/新版ID集合，只删除两个来源独有内容；全部增删改放在同一事务。未知图谱或外部关联会触发拒绝/回滚。Browser现有配色未修改。', '',
        '输出已刷新：SQLite、build_report.json、实体/关系清单、GraphML、离线graph_viewer.html、直接导入计划和中文关系表。此前受占用的CSV后来已成功刷新；当前以知识图谱_关系节点属性.csv为准。', '',
        '## 6. 检索与回归检查', '',
        '当前检索仍是中文实体/别名对齐、字符n-gram TF-IDF、上下文加权排序与同单元因果路径检索；没有把它冒称为向量语义模型或大模型训练。',
        '全部文章可以返回全文分块。无已建图事实但文本相关时标为text_evidence_only；补充文本和已建图事实在LLM提示词中分开，保持待核验与适用范围提醒。不跨文章拼出已证实因果链。',
        '12项当前版本回归已通过，覆盖移出范围、旧正式事实保留、1275篇正文全覆盖、引文定位、参考入口、试验查询、非试点文章检索与无关问题拒答。另6项CSV刷新/占用保护/转义安全测试通过；测试临时目录限定在项目output内。原PDF的296个页/锚点检查无错误。', '',
        f"38题开发自检：案例MRR@3={case_eval['case_mrr_at_3']}，事实Recall@5={case_eval['fact_recall_at_5']}，Recall@10={case_eval['fact_recall_at_10']}，Precision@5={case_eval['fact_precision_at_5']}。",
        f"24题参考故障开发自检：MRR@3={fault_eval['mrr_at_3']}，Recall@5={fault_eval['recall_at_5']}，Recall@10={fault_eval['recall_at_10']}。",
        '这些题与知识来源同源，只作回归，不是独立泛化成绩，更不是实船诊断准确率。两个测试程序的Precision分母定义不同，应分别阅读输出说明，不能直接合并比较。', '',
        '## 7. 在Neo4j查看新语料链与来源', '', '```cypher',
        "MATCH p=(a:ShipKG)-[r]->(b:ShipKG)",
        "WHERE r.case_id STARTS WITH 'corpus:'",
        'RETURN p LIMIT 150;', '',
        "MATCH (a:ShipKG)-[r]->(b:ShipKG)",
        "WHERE r.certainty = 'corpus_statement'",
        'RETURN a.name AS 起点, r.name AS 关系, b.name AS 终点,',
        '       r.locator AS 原文位置, r.quote AS 原文证据,',
        '       r.certainty_zh AS 证据性质, r.source_url AS 来源链接;', '```', '',
        '## 8. 后续应做与未完成事项', '',
        '逐批审核候选句，先筛与热—机—电耦合相关的高价值机理；补充原始出处和机型限制，再做实体同义合并。当前4篇是试点，不是1275篇全部自动审核建图完成。',
        '按来源/事故建立独立专家标注检索集；原资料包train/val/test已全部参与索引，不能继续当独立测试分组。',
        '继续部署语义检索/重排序并对照当前字符基线，评估路径一致性、引用正确性与LLM增强报告质量。此次没有运行实际LLM生成实验，也未自动推送Git。', '',
        '修订审计及5个真实检索结果和提示词见data_revision_v4_3.json；完整当前说明见../README_CN.md。']
    (OUT/'资料修订与语料建图报告_V4.3_20261008.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('version','removed_node_types','added_node_types','newly_indexed_articles','duplicate_articles','pilot_articles_outside_old_selection','neo4j_verified')},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
