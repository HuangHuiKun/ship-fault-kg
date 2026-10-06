# 船舶动力系统故障知识图谱构建与 Neo4j 导入方法汇报

> **版本提醒：本文是V1的历史方法记录。** 2026-10-05已完成V2扩充和在线合并，默认SQLite直接导入Neo4j，不再需要CSV中转。当前方法、规模、源资料与操作步骤以[完整V2升级说明](REPORT_KG_V2_UPGRADE_CN.md)为准。

> 版本：2026-10-04；对象：本项目 `ship_fault_kg` 可运行原型。本文说明**代码已经实现的流程**，并将尚未完成的研究设想单独列出。图谱用于辅助检索与报告生成，不等同于可直接用于船舶现场处置的诊断系统。

## 一、先用一句话说明方法

本项目从公开船舶事故调查报告、故障实验数据和相关文本出发，**先定义故障图谱的实体与关系，再人工核对关键事故事实及其原文页码，随后用程序统一生成节点、关系和证据，经过校验后导入独立的 Neo4j 数据库**。这样得到的不是一堆没有出处的“故障常识”，而是一张可以回答“哪个案例、什么条件、何种故障、带来什么后果、证据在哪一页”的小规模、可追溯图谱。

```text
公开报告/实验数据/文本语料
          ↓  来源登记、确定范围
人工核对事故事实 + 设计实体/关系
          ↓  稳定 ID、案例范围、确定性、来源页码
Python 构建与校验
          ├─ SQLite + CSV + GraphML + 规模报告
          ├─ 轻量检索与评价（当前主要读取 SQLite）
          └─ Neo4j 专用 CSV → neo4j-admin 首次离线导入
                                      ↓
                         Neo4j 查询与图形可视化
```

选择“小而可核验”的路径，是因为目前尚无项目组真实的轴带发电—电网耦合故障标注资料；在缺少直接证据时批量自动生成因果关系，容易把一般机械故障、仿真工况和真实轴带系统故障混为一谈。这是本项目的工程取舍，**并不是证明人工方法在所有任务上优于自动抽取**。

## 二、数据从哪里来，以及为什么分层

数据来源登记在 [`ship_fault_kg_data/05_metadata/source_manifest.csv`](../ship_fault_kg_data/05_metadata/source_manifest.csv)。每条记录保存标题、本地文件、原始链接、类别和许可/复用说明。构建脚本实际读取了下表中的一部分来源；“下载过”不等于“已抽成图谱事实”。

| 来源层 | 实际使用方式 | 为什么这样用 |
| --- | --- | --- |
| 英国 MAIB 船舶事故调查报告 | 人工整理 7 起具体事故的事实、因果与行动；8 份报告按页形成 406 个检索片段 | 报告有可核查的事件经过和调查结论，适合建立带出处的案例主干；安全摘要只作检索文本，不冒充人工核实的三元组 |
| Marine Engine Fault Dataset | 用 `dataset_index.csv`、`variable_dictionary.csv` 建立 16 个运行/参考文件、5 类故障及 70 个测点 | 给诊断输入提供“故障类别—负载—测点—样本文件”的结构化接口；不由标签反推真实故障因果 |
| 匿名化方位推进器状态监测汇总 | 按表格行建立观察、故障/状态和建议行动 | 保留现场汇总的研究价值，同时用 `data_origin` 标明匿名汇总，不伪装成逐船事故调查 |
| UCI 舰船推进与 TSRF 热力数据 | 建立数据集及其仿真故障类别 | 用于扩充工况和检索覆盖；明确标注为仿真，不能直接当作现场证据 |
| 中文船机 RAG 语料 | 选出 82 篇与动力故障相关的文章，作为文本片段 | 可为后续文本召回提供背景；许可和事实质量未逐条核准，未直接写成因果边 |

构建图谱时引用的船机故障知识图谱论文，提供了“故障现象—原因—处置”的建模思路；项目并未复制论文中的训练模型或其图谱。该论文采用 BiLSTM-CRF 做知识抽取并存入 Neo4j，而本项目当前的事故因果主干采用人工整理与页码锚点校验。[论文原文](https://www.mdpi.com/2077-1312/13/4/693)

## 三、第一步：确定图谱要表达什么

### 3.1 实体（节点）

[`build.py`](build.py) 用 `kind` 指明节点类型。当前图谱有 17 类节点，较重要的有：

| 层次 | 节点类型 | 作用 |
| --- | --- | --- |
| 案例定位 | `Vessel`、`Case`、`System`、`Equipment`、`Component` | 回答“哪条船、哪次事故、哪个系统和部件”，防止不同事故的事实混接 |
| 诊断解释 | `Symptom`、`Condition`、`Cause`、`Fault`、`Consequence` | 串起症状、条件、原因、故障和后果；这些概念不可一概视为同义词 |
| 检查处置 | `Check`、`Action` | 把“如何核查”和“如何处理”与故障条件相连 |
| 数据对齐 | `Dataset`、`Run`、`Sensor`、`Observation` | 关联实验文件、负载、测点和匿名观察记录 |
| 来源 | `Source` | 保存资料标题、原始链接、本地文件和复用信息 |

这样设计比只保留“症状—故障—措施”三类节点更适合后续的船舶动力系统诊断：同一故障在不同设备、负载、船型和事故中可能有不同含义。另一方面，类型较多也增加了建模和维护成本，需要持续统一命名。

### 3.2 关系（有方向的边）

程序只接受 [`build.py`](build.py) 中 `RELATIONS` 白名单内的关系。核心关系如：`CONTRIBUTED_TO`（促成）、`LEADS_TO`（导致）、`PRECEDED`（先于）、`CHECKS`（检查）、`ADDRESSES`（应对）。另有 `HAS_CASE`、`INVOLVES`、`HAS_RUN`、`HAS_CHANNEL` 等组织性关系。**组织性关系不是因果关系**：例如 `INVOLVES` 仅表示节点属于某事故，不能据此推断“导致”。

节点 ID 用“类型 + 名称”的 SHA-1 摘要生成，边 ID 用“起点 + 关系 + 终点 + 证据 + 案例”生成。因此相同输入可以稳定重建；但名称改动会改变 ID，且截短摘要并非形式上的零碰撞保证，规模扩大时应增加别名对齐和冲突检查。

## 四、第二步：把事故报告变成有证据的事实

人工核对后的 7 起案例写在 [`curated_cases.py`](curated_cases.py)，每个案例包含案例 ID、船舶、系统、来源 PDF、摘要页及一组事实。每条事实明确写出：

`起点实体 | 关系 | 终点实体 | PDF 页码 | 原文定位短语 | 确定性等级`

例如 Kommandor Susan 案例中，程序记录“非原厂轴承材料粘结较弱 → 促成 → 连杆大端轴瓦失效”，标为 `probable`，而不是写成绝对确定的结论。随后可沿同一案例继续检索“轴瓦失效 → 发电机失效 → 全船失电/失去推进”等边。报告中提到的检查或整改建议另以 `CHECKS`、`ADDRESSES` 表示，避免把“推荐行动”写成已发生的故障原因。

[`build.py`](build.py) 的 `pdf_evidence()` 会读取指定 PDF 页、检查定位短语是否真的出现，再截取附近原文。页码越界或短语缺失时构建直接报错。这一步的缘由是**把事实录入与原始材料绑在一起**：即使日后 PDF 替换、页码变化或人工误抄，也应先停下复核，不应静默生成无出处的边。这个校验只能证明短语在指定页出现，**不能自动证明人工对因果语义的解释一定正确**，所以仍需要轮机领域专家复核。

每条边还带有 `case_id`、`evidence_id` 和 `certainty`。`reported` 表示报告明示；`probable`、`possible` 保留报告的概率措辞；`reported_action` 表示报告中明确的行动；`derived_action` 是研究者依据报告整理的建议，必须与报告原句区分。数据集标签和仿真关系另使用 `dataset_label`、`simulated`。这些标签是**证据性质**，不是经过概率标定的数值置信度。

## 五、第三步：接入表格与文本，但不越界推断

`build_engine_dataset()` 读取实验数据索引，生成 `Dataset → HAS_RUN → Run → TESTS_FAULT → Fault`、`Run → AT_LOAD → Condition` 和 `Dataset → HAS_CHANNEL → Sensor`。`Run` 保留样本行数、字段数、异常状态编码；`Sensor` 保留单位和所属类别。原因是未来的标准化诊断报告可以先匹配设备、工况、故障类别和测点，再决定哪些事故证据有参考价值。程序**没有**从故障标签自动推断某传感器必然升高或降低。

`build_azimuth_dataset()` 将方位推进器汇总表逐行转成 `Observation` 及其故障、建议关系；`build_other_datasets()` 将 UCI 和 TSRF 的类别纳入图谱，并标清仿真来源。`build_passages()` 则把事故报告按 PDF 页、中文语料按选定文章做成文本片段。文本片段与图谱事实分层保存：全文检索可以利用片段，因果路径只能沿已核验的边走。

## 六、第四步：统一生成、校验和保存

运行入口是 [`build.py`](build.py)。它依次执行事故案例、实验数据、匿名汇总、其他数据集、文本片段的构建，最后运行 `validate()`。主要校验包括：

1. 边两端节点必须存在；否则图会出现悬空关系。
2. 边必须引用现有证据；否则无法解释结论从哪里来。
3. 关系类型、确定性值必须在受控集合内；否则相同含义会被写成多种拼法。
4. 人工登记的 PDF 页码和定位短语必须匹配；否则不接受该事实。

输出位于 [`output/`](output/)：

| 文件 | 内容及理由 |
| --- | --- |
| `ship_fault_kg.sqlite` | 本地结构化主数据；有 `nodes`、`edges`、`evidence`、`passages` 四张表，不启动 Neo4j 也能查询和做检索实验 |
| `nodes.csv`、`edges.csv`、`evidence.csv`、`passages.csv` | 人可审阅、可迁移的中间格式，便于检查和重新导入 |
| `build_report.json` | 规模、类型分布、来源页数及校验结果，便于每次重建后比较 |
| `ship_fault_kg.graphml` | 由 [`export_graphml.py`](export_graphml.py) 另行生成，便于在 Gephi 等工具中查看 |

截至本文核对时，[`build_report.json`](output/build_report.json) 显示 **7 起人工整理事故、234 个节点、325 条关系、171 条证据、488 个文本片段**（其中报告页 406、中文语料文章 82）；`validation_errors` 为空。节点中包括 41 个 `Fault`、70 个 `Sensor`、16 个 `Run`。这是**原型规模与内部校验结果**，不能解读为“覆盖所有船舶故障”或“诊断准确率”。

## 七、第五步：为什么采用 Neo4j 离线批量导入

### 7.1 从 SQLite 转为 Neo4j 专用 CSV

[`prepare_neo4j_admin_import.py`](prepare_neo4j_admin_import.py) 读取 SQLite，对节点 ID 唯一性、关系 ID 唯一性、关系端点、证据引用和关系类型再做一轮检查，然后生成 `nodes_admin.csv` 与 `relationships_admin.csv`。节点 CSV 用 `id:ID(ShipKG)`、`:LABEL` 等 Neo4j 批量导入列；每个节点带统一 `ShipKG` 标签和自己的类型标签（例如 `Case`、`Fault`）。关系 CSV 用 `:START_ID(ShipKG)`、`:END_ID(ShipKG)`、`:TYPE` 指向两端节点，并将来源文件、链接、页码、摘录、确定性写成**关系属性**。这样点开一条边即可追溯到原文。

注意：171 条证据在 SQLite 中独立存表，但当前 Neo4j 映射并未把证据做成 171 个独立节点，而是将有关证据字段复制到关系属性；488 个文本片段目前也**没有导入 Neo4j**。这避免了把“Neo4j 图谱”和“整个检索语料库”误说成完全相同的数据。

### 7.2 首次导入的顺序及缘由

1. 在 Neo4j Desktop 2 新建本地实例 `ShipFaultKG`，与原有数据库隔离。该实例使用 HTTP `7475`、Bolt `7690`，避免与另一服务的默认端口冲突。
2. 用上述脚本生成两份 CSV。先运行 `neo4j-admin database import full --dry-run` 检查文件格式、列头和关系端点；干运行不写数据库。[Neo4j 官方说明](https://neo4j.com/docs/operations-manual/current/import/full-import/)
3. 停止目标 Neo4j 实例，对**尚不存在的数据库名**运行 `neo4j-admin database import full`。离线导入适合一次性把已清洗的整图写成原生数据库文件；实际导入日志记录创建 234 个节点、325 条关系。
4. 重新启动实例，在 `system` 数据库执行 `CREATE DATABASE shipfaultkg`，将预先导入的数据库文件注册到 DBMS。Neo4j 官方文档说明：无额外选项时，`CREATE DATABASE` 会尝试挂载已有数据库文件。[数据库创建说明](https://neo4j.com/docs/operations-manual/current/database-administration/standard-databases/create-databases/)
5. 在 Query 页面**选择 `shipfaultkg`**（不是默认 `neo4j`），运行数量与样例查询。网页地址 `http://localhost:7475`；连接需要新实例的正确管理员凭据。**连接失败与源数据文件缺失是不同问题**。

已存在的 `shipfaultkg` **不能直接再次执行 `full import`**。Neo4j 官方文档明确：要向已有目标执行全量导入，必须使用会删除既有数据库文件的 `--overwrite-destination`；本项目不把它作为日常更新方法，以免误覆盖人工修改。[全量导入限制](https://neo4j.com/docs/operations-manual/current/import/full-import/) 后续少量新增事实应先在本地重建/复核，再通过 [`import_neo4j.py`](import_neo4j.py) 的 `MERGE` 思路在线合并，或者使用官方驱动实现受控增量更新；不要反复重建生产库。当前在线脚本依赖旧版 `py2neo`，与 Neo4j 2026 的实际兼容性应单独测试，不能把“代码存在”当作“增量导入已在新版本验证通过”。Neo4j 当前官方 Python Driver 6.x 明确支持 2026.x，可作为后续替换方案。[驱动兼容说明](https://neo4j.com/docs/python-manual/current/install/)

### 7.3 核验查询

在 Neo4j Query 中连接 `ShipFaultKG` 并选择数据库 `shipfaultkg` 后，初始全量导入应得到：

```cypher
MATCH (n:ShipKG) RETURN count(n) AS nodes;
```

```cypher
MATCH (:ShipKG)-[r]->(:ShipKG) RETURN count(r) AS relationships;
```

期望值分别为 234 和 325。查看具体案例：

```cypher
MATCH (c:ShipKG:Case)-[r:INVOLVES]->(n:ShipKG)
WHERE c.case_id = 'kommandor_susan_dg1_2025'
RETURN c,r,n LIMIT 60;
```

在结果区切换 **Graph/图形** 视图即可看节点与连线；再点击边查看 `case_id`、`certainty`、`source_file`、`page`、`quote`。这比单看漂亮的图形更能证明数据可追溯。若节点数为 0，优先检查是否误选默认 `neo4j`；若出现“saved credentials unsuccessful”，先处理新实例的登录凭据，不要因此重做或覆盖数据库。

## 八、它如何服务后续的知识增强诊断

当前 [`retrieve.py`](retrieve.py) **直接读取 SQLite，而不是在线查询 Neo4j**。它通过中文/英文别名、术语扩展和字符级 TF-IDF 对案例、事实边及文本片段评分，再在同一 `case_id` 内搜索因果路径，形成带证据编号、原文摘录、来源 URL 和页码的 Evidence Pack。这样能在没有独立向量模型、无独显的本地电脑上运行；代价是对深层语义改写、跨语言复杂表达的召回能力有限。Neo4j 当前承担图形展示、Cypher 查询和今后在线图检索的基础，而非当前检索脚本的唯一后端。

[`eval_queries.json`](eval_queries.json) 的 12 道开发题用于冒烟测试。[`retrieval_evaluation.json`](output/retrieval_evaluation.json) 记录：9 道事故题的案例 Recall@1、MRR@3 均为 1.0；人工标注关系的平均 Recall@5 为 0.9074、Precision@5 为 0.5333、Recall@10 为 1.0。题目由同一批资料编写，**不能当成独立专家盲评、跨船型泛化结果或与其他论文的公平性能比较**。本地 3B 模型演示见 [`generate_demo.py`](generate_demo.py)：它选择证据编号，程序核查编号、关系及案例归属后再组装诊断草稿，不让模型凭空决定最终事实。

## 九、与其他常见路线的区别、优势和不足

以下是方法机制比较，**不是同一数据集上的实测排名**。

| 路线 | 常见做法 | 与本项目相比的优势 | 与本项目相比的不足/适用边界 |
| --- | --- | --- | --- |
| 纯人工知识库/规则库 | 专家逐条录入规则与三元组 | 事实质量和术语可控，适合小规模高风险领域 | 扩张慢、成本高，复杂报告中的来源、确定性、案例隔离仍需自行设计；本项目用程序化生成与校验减轻重复劳动 |
| 监督式信息抽取 | 标注语料，训练 NER/关系抽取模型，如船机故障论文中的 BiLSTM-CRF | 一旦有足够领域标注，可比逐条手工录入更快扩展；适合大量同类型文档 | 需要标注集和模型维护，抽取正确不等于因果判断正确；本项目目前没有训练这样的抽取模型。[船机故障论文](https://www.mdpi.com/2077-1312/13/4/693) |
| LLM 自动建图 | PDF 切块，提供 schema，由 LLM 抽实体/关系并写入图 | 起步快、模式灵活，适合探索大文档库；Neo4j 官方 KG Builder 已提供相应组件 | 会产生候选事实的人工核查、合并消歧、成本与上下文管理问题；在船舶事故因果结论上不能省略页码和专家确认。[Neo4j KG Builder](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html) |
| 纯文本/向量 RAG | 切块、向量化、相似度召回后给 LLM | 建库门槛低，对措辞变化较灵活 | 相似段落不自动给出明确因果链、案例边界和确定性；本项目的图谱边可补足结构化解释，但当前字符检索弱于成熟向量召回。可考虑两者融合。[Neo4j GraphRAG 检索器](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html) |
| 大规模自动 GraphRAG | 实体抽取、图聚类/摘要、图与文本联合召回 | 更适合跨大量文档的全局问题和复杂发现 | 构建与运行复杂、资源和校验成本高；本项目目前优先解决小范围、可审计的故障案例检索，尚未实现社区摘要或图向量索引。[Microsoft GraphRAG 论文](https://www.microsoft.com/en-us/research/publication/from-local-to-global-a-graph-rag-approach-to-query-focused-summarization/) |

Neo4j 导入方式也有不同取舍：

| 方式 | 更适合 | 本项目选择/限制 |
| --- | --- | --- |
| `neo4j-admin database import full` | 首次、离线、数据已清洗的整库导入 | 本次采用；格式检查严格、速度适合整图；不能随意重复写入现有库，更不能在未备份时加 `--overwrite-destination`。[官方说明](https://neo4j.com/docs/operations-manual/current/import/full-import/) |
| `LOAD CSV` + Cypher | 已运行的数据库、较小或分批更新 | 便于在线转换字段和逐批调试，但要管理本地文件访问、导入顺序和数据类型。[官方说明](https://neo4j.com/docs/cypher-manual/current/clauses/load-csv/) |
| Neo4j Data Importer 图形界面 | 不想写脚本、数据表结构清楚的试验 | 直观映射节点和关系；但本项目的页码锚点、确定性分级、跨文件校验仍需在界面导入前先完成。[官方说明](https://neo4j.com/docs/data-importer/current/) |
| `MERGE` 在线脚本/官方驱动 | 已有库的受控增量合并 | 稳定 ID 可避免重复新增；宜配合唯一性约束。现有 `py2neo` 脚本还需对 Neo4j 2026 实机兼容性验证。[`MERGE` 官方说明](https://neo4j.com/docs/cypher-manual/current/clauses/merge/) |

## 十、按本机环境复现的操作清单

以下命令用于**从现有资料重建本地输出**。在 PowerShell 中逐行执行；不要把密码写进命令或文档。重建会更新 `ship_fault_kg/output` 中由程序生成的文件，执行前应先保存自己修改过的输出。项目组的原始报告和数据集不会因此被删除。

```powershell
Set-Location 'D:\RAGQnASystem\RAGQnASystem-main'
$pythonExe = 'C:\Users\18270\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $pythonExe .\ship_fault_kg\build.py
& $pythonExe .\ship_fault_kg\prepare_neo4j_admin_import.py
& 'C:\Users\18270\anaconda3\envs\ragqna\python.exe' .\ship_fault_kg\export_graphml.py
```

当前 `ragqna` Conda 环境曾缺少 `pypdf`，但有 `networkx`；上面的前两步使用具备 `pypdf` 的 Python，GraphML 导出使用具备 `networkx` 的 `ragqna` 环境。若改用自己的 Python，须先确认相应依赖。命令执行后先打开 `output/build_report.json`，检查数量与 `validation_errors`，再进行数据库导入；若数量突变或页码锚点校验失败，应先查源数据，不能直接导入。

**仅在要新建一个空数据库时**，先在 Desktop 停止 `ShipFaultKG` 实例，再使用本机该实例的 `neo4j-admin.ps1`。下面选用从未使用过的示例名称 `shipfaultkg_rebuild`；如果这个名称已经存在，应另选新名称，不能加 `--overwrite-destination` 偷懒覆盖。PowerShell 中的路径是本机实例路径，其他电脑的实例 ID 会不同。

```powershell
$neo4jAdmin = 'C:\Users\18270\.Neo4jDesktop2\Data\dbmss\dbms-956da0b3-4eec-4a04-aa01-484899f94108\bin\neo4j-admin.ps1'
$nodeCsv = 'D:\RAGQnASystem\RAGQnASystem-main\ship_fault_kg\output\neo4j_admin_import\nodes_admin.csv'
$relCsv = 'D:\RAGQnASystem\RAGQnASystem-main\ship_fault_kg\output\neo4j_admin_import\relationships_admin.csv'
& $neo4jAdmin database import full --dry-run --path-pattern-style=none --nodes=$nodeCsv --relationships=$relCsv shipfaultkg_rebuild
```

只有干运行通过，才对同一个**尚不存在**的名称执行实际导入：

```powershell
& $neo4jAdmin database import full --path-pattern-style=none --nodes=$nodeCsv --relationships=$relCsv shipfaultkg_rebuild
```

然后在 Desktop 启动实例，在 Query 页面连接新实例、切换到 `system` 数据库，执行：

```cypher
CREATE DATABASE shipfaultkg_rebuild;
```

等待它显示 `online` 后，切换到 `shipfaultkg_rebuild`，运行第七节的计数和案例查询。若**只想给现有 `shipfaultkg` 增加/更新少量事实**，不要走上述全量路径；应采用经过本机兼容性验证的 `MERGE` 在线合并流程。Neo4j 官方将 `LOAD CSV`、图形 Data Importer 和程序驱动作为其他导入选择，具体取决于数据规模与更新频率。

## 十一、结论与下一阶段工作

本方法当前最有价值的交付，是**一套证据可追溯的小规模船舶故障知识组织与导入流程**：原文页码可回查，事故案例不跨案乱连，实验/仿真/真实报告来源可区分，SQLite 可离线实验，Neo4j 可查询和展示。它不是训练完成的船舶故障大模型，也不能直接预测低速机轴带系统的重大隐蔽故障。

主要短板有三点：① 仅 7 起人工整理事故，缺少真实轴带发电、电网耦合振荡等直接案例；② 人工抽取和当前字符级检索难以大规模泛化；③ Neo4j 在线增量导入、图数据库驱动检索以及专家盲评尚需完善。拿到项目组真实数据后，建议先扩展“轴带电机—联轴器—轴系—变流器—电网”本体与带时序的故障事件，并由领域专家核对来源；再把向量/全文召回与案例约束图路径结合，使用独立测试集评价召回、排序、证据准确性和最终报告的事实一致性。
