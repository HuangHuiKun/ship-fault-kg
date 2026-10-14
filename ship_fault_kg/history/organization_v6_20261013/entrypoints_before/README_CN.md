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

旧 PPT、旧版本 CSV/统计和 output/v5 报告仍是历史内容，不能用来代表 V6 的实时规模。本次未更新 PPT 或旧 CSV；当前清单以以上 V6 输出为准。

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

build.py、retrieve.py、import_neo4j.py 已指向 V6。manage_v5.py 保留历史版显式入口。
v5/ 和 output/v5 是冻结基线，也是 V6 构建依赖，不应删除或移动。

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
