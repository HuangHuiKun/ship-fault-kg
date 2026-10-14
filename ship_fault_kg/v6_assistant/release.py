"""Generate an auditable V6 release report from actual build/deployment files."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'output' / 'v6_assistant'

def load(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))

def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                       '| ' + ' | '.join('---' for _ in headers) + ' |'] +
                      ['| ' + ' | '.join(str(x).replace('|', '/') for x in row) + ' |' for row in rows])

def main():
    report, schema, checks = load('build_report.json'), load('schema.json'), load('verification_report.json')
    deployed = load('neo4j_verify_result.json')
    same = checks['snapshot_sha256'] == deployed['snapshot_sha256'] and deployed['exact_property_match']
    if not same or not checks['all_passed'] or not report['published_to_neo4j']:
        raise SystemExit('Cannot document successful publication: verification or deployment is missing.')
    nodes = [json.loads(line) for line in (OUT / 'entities.jsonl').read_text(encoding='utf-8').splitlines() if line]
    edges = [json.loads(line) for line in (OUT / 'relationships.jsonl').read_text(encoding='utf-8').splitlines() if line]
    names = {n['id']: n['name'] for n in nodes}
    hierarchy = [(names[e['source']], names[e['target']]) for e in edges if e['relation'] == 'IS_SUBSYSTEM_OF']
    class_rows = [(key, label, report['node_types'][key], report['concept_counts'].get(key, '—'))
                  for key, label in schema['classes'].items()]
    relation_rows = [(key, label, report['relations'].get(key, 0),
                      ', '.join(schema['endpoints'][key]['subject']),
                      ', '.join(schema['endpoints'][key]['object']))
                     for key, label in schema['relations'].items()]
    system_rows = sorted(hierarchy, key=lambda item: (item[1], item[0]))
    property_section = '\n\n'.join('### ' + label + '（' + kind + '）\n\n' +
        '、'.join('`' + field + '`' for field in schema['entity_property_fields_by_class'][kind])
        for kind, label in schema['classes'].items())
    text = f'''# 新版船舶故障知识图谱：架构复核、构建与建库报告 V6

发布日期：2026-10-13。数据库：`shipfaultkg`。本报告由实际构建、校验和导入结果生成，不以计划数量冒充完成数量。

## 1. 本次结论与定位

本次基于**已经整理的 3,274 条直接知识声明**完成重建，没有追加新一轮资料阅读，也没有为凑规模补写故障机理。
保留 **12 类主体实体、24 类关系**（23 类业务关系加 1 类溯源关系）；调整系统分类与证据属性即可容纳新增知识，不必把每个技术名词新增为实体类。
图谱服务于“初步诊断结果 → 检索机理、症状、检查、措施与来源 → LLM 增强诊断报告”，是可替代的实验知识底座，不是工业化诊断产品或训练好的大模型。

| 对比口径 | V5 已发布 | 本次 V6 已发布 |
| --- | --- | --- |
| 节点 | 1,356 | {report['nodes']:,} |
| 关系 | 3,343 | {report['edges']:,} |
| 直接知识声明 | 726 | {report['explicit_knowledge_statements']:,} |

节点约为旧版 {report['growth']['nodes']} 倍，关系约为旧版 {report['growth']['edges']} 倍。关系总数包含溯源、适用范围和实例归属，**不能说成 14,334 条独立故障机理**。
本次架构复核前的实验文件为 5,581 节点、14,071 关系；复核后增加 10 个系统节点及净增 263 条分类/层级关系，直接声明数量仍为 3,274。

## 2. 为什么仍用 12 类实体、24 类关系

故障名称归 Fault；异常现象、结果或状态归 State；诱因、条件归 Factor；操作性检查归 Check；维修预防措施归 Action。
设备和部件描述物理对象；System 描述功能组织；Parameter 描述测量变量；Case 保留来源内案例边界；Source 提供追溯。
因此新资料增加的是这些类别内部的具体内容，而不是新的顶层概念体系。

{table(['类名', '中文', '节点数（含情境）', '概念节点数'], class_rows)}

不是每个节点都代表一个不同故障种类：Fault 的 1,021 个节点中有 765 个概念，其余为来源/案例情境记录。
全图有 811 个情境记录，通过 INSTANCE_OF 连接概念，避免把不同船型、工况、案例的证据拼成一条“已证实”因果链。
State 和 Factor 相比旧版已得到充分补充；概念数与 Fault 的比例分别约 1.665、0.502。
Check 比例 0.774、Action 比例 0.825，仍低于原规划下限 0.8、1.0，后续应补充可靠原文中的检查与措施，而不是制造实体达标。
船舶和系统数量不应机械追平故障数量：它们本来就是共享组织节点。

### 系统类调整：28 个节点

28 = 1 个根系统 + 5 个大系统 + 22 个细分系统，27 条上级系统关系。以功能层次组织，而不是为每个型号建立一个系统。
新增/补足起动空气、气缸润滑、滑油净化、喷油定时等索引范围；一个设备可同时服务多个功能系统。
保留旧有资料上下文分类；只在设备名称存在明确功能词时增加细分归属。名称只有型号、功能不明确的设备不强行归入叶节点。
系统层次与功能归属是**整理者设计的检索索引，不是原文直接给出的故障因果证据**，用 classification_role 加以区分。

{table(['系统节点', '上级系统'], system_rows)}

### 关系类型及端点约束

{table(['关系代码', '中文含义', '数量', '起点允许类型', '终点允许类型'], relation_rows)}

CAUSES（导致）、CONTRIBUTES_TO（促成）、INCREASES_RISK_OF（增加风险）与 ASSOCIATED_WITH（相关联）不能互相替代。
PRECEDES 表示先后，并不自动表示因果。DOCUMENTED_BY 是来源导航；具体引用原文、页码和声明状态主要保留在业务边的属性中。
24 类名称和允许端点沿用原模式，由构建校验检查类型，不是靠 Neo4j 的颜色或节点名称来判断类别。

## 3. 使用了多少资料，证据如何产生

全部资料注册表仍有 1,308 个来源；实际图中使用 299 个来源。不能说“全部资料已审阅并入图”。
当前助手阅读记录覆盖 262 个来源：162 个全文阅读且有声明，91 个代表性节选阅读且有声明，9 个阅读后未纳入；其中全文阅读总计 168 个。
另有 46 个来源沿用 V5 选定证据；阅读来源与旧证据来源存在重叠，因此不能直接相加。
仍有 1,000 个来源未完成本轮助手阅读。资料包括正式事故调查、厂家技术资料、论文、维修语料及参数数据，各自可信性不同。

直接声明 = 旧版 726 + 助手新增 2,548 = 3,274。它们由助手在实际阅读原文后整理为代码中的结构化声明，不是您亲自人工审核的结果，也不是本地 3B 模型批量推断。
本次运行外部模型 API 0 次、本地模型 0 次；不代表这些声明已经得到船舶专家认可。当前专家审核数为 0。

原固定切片 6,358 个；当前文本片段表有 7,845 条，包含后来增加的精确证据片段，不能全部称为原固定切片。
实际引用的精确片段为 2,085 个；本轮登记阅读的原固定片段为 288 个，二者口径不同，不能相加或直接计算“6358 使用率”。

## 4. 从声明到图谱：透明的处理链

```text
原始文件（保持不变）
   ↓ 读取文字、登记标题/链接/文件指纹/原文位置
来源注册表 + 文本片段表
   ↓ 助手阅读、摘录原文、整理直接知识声明
subject_kind / subject / relation / object_kind / object
   + source_id / quote / locator / scope / certainty / applicability
   ↓ 原文定位核验、实体类与关系端点校验
统一概念实体 + 来源/案例内情境实体
   ↓ 生成稳定 ID、实例归属、来源边、系统检索索引
entities.jsonl / relationships.jsonl / assertions.jsonl
   ↓ SQLite 存储 + JSON 图快照
独立校验 → 备份实时数据库 → 单事务 Query API 导入 → 全属性对照
Neo4j shipfaultkg
```

**实体从哪里来：**直接声明明确填写实体类别和名称；构建程序规范化、按稳定键生成 ID。同一个概念可在多个来源复用；局部案例记录保留 scope_id。
**关系从哪里来：**声明明确填写业务关系；代码不根据两个节点靠得近就推断因果。实例、溯源、分类是按规则添加的辅助边。
**属性从哪里来：**来自原文摘录与元数据、声明中的确定性/适用范围/审核状态，以及构建版本和 ID 等程序字段。并不是每个实体都填满所有字段。
**3,274 如何变为 14,334：**直接事实之外还需加入来源、对象适用范围、案例涉及、概念实例、设备系统等连接。最终每条边对应一条结构化记录，因此 assertions 表为 14,334 条；这不等于助手额外推理出了同样多的直接声明。

### 关键代码及中间产物

| 路径（相对 ship_fault_kg） | 作用 |
| --- | --- |
| v6_assistant/pipeline.py | 合并冻结 V5 与新增声明，定位核验，生成节点、边、SQLite 与快照 |
| v6_assistant/schema.py | 沿用 12/24 规范，加入证据状态属性约束 |
| v6_assistant/subsystems.py | 多功能系统索引，明确标记整理者分类 |
| v6_assistant/verify.py | 独立结构、证据、比例、系统层次与检索探针核验 |
| v6_assistant/neo4j.py | 实时备份、导入前防护、单事务同步、全属性核对 |
| v6_assistant/retrieve.py | 从当前 V6 SQLite 读取并执行词法实体检索和同范围扩展 |
| output/v6_assistant/entities.jsonl | 每个节点的 ID、类别、名称、别名、属性 |
| output/v6_assistant/relationships.jsonl | 每条边的起终点、关系和证据属性 |
| output/v6_assistant/assertions.jsonl | 与边对应的结构化声明及原文证据 |
| output/v6_assistant/sources.jsonl、passages.jsonl | 来源注册与文本片段；不全转换成 Neo4j 节点 |
| output/v6_assistant/schema.json | 实际类、关系、端点及属性清单 |
| output/v6_assistant/ship_fault_kg.sqlite | 当前完整本地存储，含图结构和证据表 |
| output/v6_assistant/neo4j_snapshot.json | 待导入 Neo4j 的节点/边/属性 JSON 表示 |
| output/v6_assistant/verification_report.json | {checks['passed_checks']}/{checks['total_checks']} 项检查结果 |
| output/v6_assistant/neo4j_import_result.json | 本次真实导入及对照结果 |

SQLite 是便于批量处理、查询和测试的本地数据库；JSON 快照是可读、可比较、可备份的图交换格式；Neo4j 是可视化与图查询的执行库。
不需要经过 CSV 转换，直接通过 Query API 将快照中的结构写入 Neo4j。
Passage、Assertion 只留在本地证据存储，不作为 Neo4j 节点；不重新引入 Run、Sensor、Dataset 类。

## 5. 属性优化和事实边界

Neo4j 节点公共基础字段：{', '.join(schema['neo4j_entity_base_fields'])}。
此外所有类别合计出现 {len(schema['entity_property_fields'])} 种 props 字段；关系合计 {len(schema['relation_property_fields'])} 种属性。这是字段并集，不是每个节点/边的字段数。

主要新字段：

- schema_version：本体模式版本，与原稳定 ID 区分。保留 shipkg5 前缀的 ID 是为了兼容，不代表数据仍是 V5。
- source_review_extent：全文、代表性节选、旧版选定证据，防止把“看过一段”说成“审过全文”。
- certainty_group：保留原 certainty，同时规范化陈述、观察、假设和建议等层级。
- classification_role：source_context、ontology_hierarchy、curator_functional_membership，区分来源上下文与整理者索引。
- action_status：区分案例实际实施的动作与参考建议。动作的实施状态主要在关系/声明属性上，不把通用 Action 概念一概标为“已执行”。

实体字段并集：{'、'.join('`'+x+'`' for x in schema['entity_property_fields'])}。

关系字段并集：{'、'.join('`'+x+'`' for x in schema['relation_property_fields'])}。

{property_section}

## 6. 建库核验与可恢复性

Neo4j 已发布：{deployed['nodes']:,} 个节点、{deployed['edges']:,} 条关系。全节点、全边、全部属性规范化后指纹一致，exact_property_match=true。
快照指纹：`{deployed['snapshot_sha256']}`。
保留 ShipKG.id 唯一约束。只替换属于本项目的 ShipKG 图；遇到项目外直接关联或并发修改会拒绝替换，不清空整个数据库。
先保存实时旧库，再执行单事务替换；写入后再次读取全图对照。未更改 Browser 的配色。

备份位置：

- history/v6_publication_20261013/neo4j_live_before_v6.json：发布前真实 V5 数据库，1,356 节点、3,343 关系，含所有属性。
- history/v6_before_ontology_publish_20261013/：复核前 V6 代码/中间数据和原默认入口、版本指针、说明文件。
- history/v5_before_v6_expansion_20261013/：扩充前 V5 归档，保留用于回滚。
- history/organization_v6_20261013/output/v5：冻结 V5 输入已归档，但仍是 V6 构建依赖，不可删除。
- history/organization_v6_20261013/v5：旧代码整体归档；V6 需要的底层实现已复制整理到 v6_assistant/core。
- history/organization_v6_20261013/output/v6_expansion：无有效声明的早期提取检查点，不参与当前构建，不合并进正式主数据。

### 常用命令

在项目根目录运行（python 应使用有项目依赖的解释器）：

```powershell
python ship_fault_kg/manage_v6.py retrieve "主机起动后超速" --top-k 3
python ship_fault_kg/manage_v6.py verify
python ship_fault_kg/manage_v6.py report
python ship_fault_kg/manage_v6.py neo4j verify
```

仅在修改声明/模式后需要重新生成本地文件时运行 `python ship_fault_kg/manage_v6.py build`，然后运行 verify。
build 不修改 Neo4j，并把发布状态重置为未发布；本地重建之后不要以旧导入日志判断新文件已同步。
当前 snapshot/apply 默认备份固定为本次发布前备份，若数据库与该备份已不一致会拒绝替换。这是保护，未来版本应建立新的发布备份路径后再发布，勿删除旧备份绕过防护。

回滚数据库（会交互式要求密码，先保存当前数据库快照）：

```powershell
python ship_fault_kg/manage_v6.py neo4j restore --snapshot ship_fault_kg/history/v6_publication_20261013/neo4j_live_before_v6.json
```

该命令只恢复数据库图数据，**不自动回滚本地默认入口、SQLite、版本指针或文档**。完整回滚还需恢复对应 V5 入口与版本文件，并运行 V5 核验；切勿将数据库恢复后仍宣称 V6 本地文件与它一致。
默认入口已切为 V6；旧 manage_v5.py 已归档，完整回滚应从归档恢复原目录结构后再用旧入口。未上传 GitHub，本次不含 Git 推送。

## 7. 检索试验、局限与下一步

当前是“故障概念名称/别名 → 字符与二元组词法排名 → 同 scope 扩展机理、状态、检查、措施 → 原文证据包”。
还不是向量语义混合检索、训练模型或端到端生成式诊断系统。例子保存于 retrieval_example.json，可见故障候选、词法分数、三元组、引用、来源链接、范围及确定性。
独立结构检查 {checks['passed_checks']}/{checks['total_checks']} 项通过；10 个开发检索探针通过。这是冒烟验证，不是 Recall@K、Precision@K、MRR 的正式评测，也不能证明每条机理语义正确。
业务机理/检查/措施边口径为 {checks['mechanism_and_maintenance_edges']:,} 条，概念业务三元组去重后 {checks['unique_concept_business_triples']:,} 组；因果类记录为 {report['causal_assertions']:,} 条。

下一步应优先：

1. 由领域人员审核高风险机理、近义实体和运维措辞；按来源等级、设备构型、条件筛选证据，标明不确定性。
2. 继续补充检查与措施证据，处理同义表达重复，不按比例硬造节点；完善电力、电网耦合领域的可靠资料覆盖。
3. 从上游诊断结果构建独立标注测试集，避免问题和参考答案都源于同一脚本造成泄漏。
4. 增加关键词/向量多路召回、融合去重和排序；用 Recall@K、Precision@K、MRR 评价实体/证据召回，再单独评价报告事实性、引用和解释。
5. 将同一范围的证据包交给 LLM 输出增强报告，明确诊断假设、证据与待检查项，禁止把跨资料路径当成已确认的实船因果链。

所有“来源覆盖 100%”只指已入图边有可定位来源，不表示 1,308 个资料都被使用或所有知识都获专家认证。
'''
    (OUT / '新版架构复核与建库报告_V6.md').write_text(text, encoding='utf-8')
    inventory = '# V6 节点与关系完整清单\n\n此表由当前 JSONL 自动生成；以后重建后运行 report 更新。\n\n'
    inventory += table(['ID', '类型', '中文名称', '层级', '范围'],
        ((n['id'], n['kind'], n['name'], n['props']['entity_level'], n['props']['scope_id']) for n in nodes))
    inventory += '\n\n## 关系\n\n' + table(['起点', '关系', '终点', '声明ID', '来源ID', '范围'],
        ((names[e['source']], e['props']['name'], names[e['target']], e['props']['assertion_id'],
          e['props']['source_id'], e['props']['scope_id']) for e in edges))
    (OUT / '节点关系完整清单_V6.md').write_text(inventory, encoding='utf-8')
    print(json.dumps(dict(report=str(OUT/'新版架构复核与建库报告_V6.md'),
                         inventory=str(OUT/'节点关系完整清单_V6.md'), published=True), ensure_ascii=False))

if __name__ == '__main__':
    main()
