# 船舶故障实验知识图谱 V6

更新：2026-10-13。当前默认版本为 V6，已发布到本机 Neo4j 的 shipfaultkg 数据库。

## 当前成果

- 5,591 个节点、14,334 条关系；12 类实体、24 类关系（包括溯源）。
- 3,274 条直接知识声明；765 个故障概念、1,021 个 Fault 节点（含情境记录）。
- System 共 28 个：1 个根系统、5 个大系统、22 个细分系统。
- 使用 299 个资料来源；注册表共有 1,308 个来源，仍有 1,000 个未完成本轮助手阅读。
- 50 项结构/定位/样例检查通过，Neo4j 与本地快照全部节点、边、属性一致。
- 专家审核数为 0；这不是实船诊断系统，也不是训练好的大模型。

图谱用于为上游初步诊断提供机理、症状、检查、运维与出处证据，支撑可替换的知识图谱增强诊断实验。系统分类是整理者设计的检索索引，不应当作原文因果事实。

## 从这里开始

| 路径 | 用途 |
| --- | --- |
| [架构复核与建库报告](output/v6_assistant/新版架构复核与建库报告_V6.md) | 类别、系统、属性、声明、流程、规模、限制、恢复方法 |
| [节点关系完整清单](output/v6_assistant/节点关系完整清单_V6.md) | 全部节点与关系，运行 report 后自动更新 |
| [模式清单](output/v6_assistant/schema.json) | 12 类、24 类、端点约束和属性 |
| [可视化查询](output/v6_assistant/queries_v6.cypher) | 系统层次、保持架局部、同范围因果链、证据表 |
| output/v6_assistant/ship_fault_kg.sqlite | 当前本地存储；包含图结构和证据 |
| output/v6_assistant/neo4j_import_result.json | 真实导入统计及指纹核验 |
| output/CURRENT_VERSION.json | 当前版本导航 |
| FILE_LAYOUT.md | 文件导航与历史说明 |

output 下的 [关系节点属性 CSV](output/知识图谱_关系节点属性.csv)、[质量评价文档](output/船舶故障知识图谱_质量评价标准与实施方案_V6_20261013.md)和[汇报 PPT](output/船舶动力系统故障知识图谱_流程与构建汇报_V6_20261013_更新版.pptx)已按当前 V6 更新。CSV 每行一条关系，包含 22 列及节点、关系属性 JSON。PPT 沿用的局部截图已标注为历史截图，整体统计使用 V6 可编辑图表。

旧输出备份在 history/output_refresh_v6_20261013，不能用于代表 V6 实时规模。以后重建图谱后，可运行 `python -m ship_fault_kg.v6_assistant.update_quality` 刷新质量统计与文档，运行 `node ship_fault_kg/v6_assistant/export_readable_csv.mjs` 刷新 CSV（需使用本机已配置的 Node 和 Artifact Tool 运行环境）；PPT 不会自动随建库更新，需另行更新。

## 日常命令

在项目根目录，用安装了项目依赖的 Python 解释器运行：

~~~powershell
python ship_fault_kg/manage_v6.py retrieve "柴油机启动超速" --top-k 3
python ship_fault_kg/manage_v6.py verify
python ship_fault_kg/manage_v6.py report
python ship_fault_kg/manage_v6.py neo4j verify
~~~

检索目前为实体别名/字符词法匹配与同 scope 关系扩展，尚不是语义向量混合检索。返回原文引用、出处、范围及确定性；不要跨案例拼接原因。

只有修改声明或模式后才需运行 build。build 只重建本地文件，不更新 Neo4j；之后必须 verify，再另行发布。
本次 Neo4j 导入器有实时备份和并发修改保护，未来再发布应准备新版本备份路径；不能删除旧备份绕过保护。

build.py、retrieve.py、import_neo4j.py 已指向 V6。manage_v5.py 已归档到 history/organization_v6_20261013/entrypoints_before，不应直接在归档目录运行相对路径敏感的旧入口。
V6 必需的底层函数现位于 v6_assistant/core；冻结 V5 输入现位于 history/organization_v6_20261013/output/v5。原 v5 代码整体归档到 history/organization_v6_20261013/v5。
history 中的冻结基线仍是 V6 重建依赖，不能删除。diagnosis_bootstrap 的旧 V5 对照试验已修正路径，仍使用同一份 V5 基线，未偷偷改为 V6 试验。
早期 v6_expansion 无有效声明、不参与当前构建，已移至 history/organization_v6_20261013/output/v6_expansion，不合并进 V6 主数据。

## 备份与恢复

- history/v6_publication_20261013/neo4j_live_before_v6.json：发布前真实 V5 图，包含所有属性。
- history/v6_before_ontology_publish_20261013/：本轮架构复核前代码、中间输出、默认入口和说明文件。
- history/v5_before_v6_expansion_20261013/：扩充前 V5 归档。

数据库恢复命令及完整回滚步骤见架构报告。只恢复数据库不会自动恢复本地版本指针和默认入口。
未在本次任务中上传 GitHub。

## 安全及来源声明

资料用于研究与实验，不意味着获得再分发授权；请遵守各来源许可。
助手整理并定位核验不等于领域专家审核。建议、假设、案例观察与已实施措施必须区分。
不能仅凭本实验图谱或 LLM 输出执行实船维修、安全操作或故障处置。
