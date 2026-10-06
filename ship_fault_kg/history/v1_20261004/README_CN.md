# 船舶动力系统故障知识图谱（可运行原型）

数据根目录：`D:\RAGQnASystem\RAGQnASystem-main\ship_fault_kg_data`  
本项目目录：`D:\RAGQnASystem\RAGQnASystem-main\ship_fault_kg`

## 已完成的交付

- `output/ship_fault_kg.sqlite`：无需启动服务即可查询的本地图谱，包含节点、关系、证据和检索文本。
- `output/ship_fault_kg.graphml`：可用 Gephi 等图工具打开的完整图谱交换文件。
- `output/nodes.csv`、`edges.csv`、`evidence.csv`、`passages.csv`：可审阅、可迁移的数据表。
- `output/build_report.json`：规模、关系类型、来源页数和校验结果。
- `output/retrieval_evaluation.json`：开发阶段的检索测试逐题结果与汇总。
- `output/demo_kg_rag_report.json` 和 `output/demo_kg_rag_report.md`：本机 Qwen 3B 选择证据编号、程序核查后生成的诊断草稿。
- `import_neo4j.py`：把上述图谱写入现有 Neo4j；只合并 `ShipKG` 标签的数据，不改动其他图谱。

## 构建步骤和每一步的作用

### 1. 确定图谱范围与本体

参考 `ship_fault_kg_data/03_papers/2025_Marine_Diesel_Fault_Knowledge_Graph.pdf` 中“故障现象—原因—处置”结构，把实体扩展为 `Vessel`、`System`、`Case`、`Fault`、`Cause`、`Condition`、`Symptom`、`Consequence`、`Check`、`Action`、`Sensor`、`Run`、`Dataset`、`Source`。主要关系包括 `LEADS_TO`、`CONTRIBUTED_TO`、`TRIGGERS`、`CHECKS`、`ADDRESSES`、`PRECEDED`。实体使用统一 ID，避免同名词重复建点。

### 2. 从真实报告建立因果主干

人工核查 MAIB 报告后，在 `curated_cases.py` 录入七起具体事件。关系不跨事故串接，每条关系有 `case_id`、来源文件、PDF 页码、英文证据摘录和确定性等级。构建程序会检查定位词是否真的出现在指定 PDF 页；不匹配就停止，不会把未经验证的关系写入图谱。

已覆盖的案例：Kommandor Susan DG1、Windcat 8、Finlandia Seaways、Wight Sky 2017、Wight Sky ME2、Wight Sky ME4、Spirit of Discovery。2013/2016 安全摘要作为检索文本收录，尚未人工抽取为因果三元组。

确定性分级：`reported`（报告明确记载）、`probable`（报告表述为很可能）、`possible`（可能促成）、`reported_action`（报告明确行动）、`derived_action`（从报告缺陷中整理出的待检查或改进方向）。生成报告时要保留这些差异。

### 3. 接入结构化实验数据

读取 `Marine Engine Fault Dataset` 的 `dataset_index.csv` 和 `variable_dictionary.csv`，建立 16 个运行/参考文件、5 类故障、负载和 70 个测点。`Run` 节点保留样本行数、字段数和异常状态编码，便于把前端标准化诊断结果与实验工况对齐。读取方位推进器匿名化汇总表，纳入振动、润滑和维护观察；再加入 UCI 推进仿真数据及 TSRF 燃烧室仿真类别。`data_origin` 明确区分实机受控试验、现场匿名汇总和仿真。

注意：这里只把数据集实际存在的类别、工况和测点纳入图谱，没有根据一条故障标签自行推断传感器变化方向或真实船舶的故障原因。

### 4. 建立检索文本层

把八份 MAIB 报告按 PDF 页收录为可检索片段，共 406 页；另外从中文船机 RAG 语料中按与动力故障相关的题名选择 82 篇，作为内部科研检索文本。后者的开放再发布许可尚不明确，不能直接当作公开知识图谱关系。所有已人工确认的图谱边仍以 MAIB 报告页码为准。

### 5. 生成本地图谱与可导入文件

运行：

```powershell
& 'C:\Users\18270\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\ship_fault_kg\build.py
```

程序输出 SQLite、CSV、规模报告并检查：关系两端必须存在、关系类型必须在白名单内、每条边必须有证据、PDF 页码定位必须成功。当前生成 234 个节点、325 条关系和 171 条证据。若需要 GraphML，再运行 `python .\ship_fault_kg\export_graphml.py`。重复构建会重新生成本地输出文件，不影响原始下载资料。

### 6. 实体检索、文本检索与因果路径检索

`retrieve.py` 使用中文/英文别名、字符 TF-IDF、术语扩展和案例范围内的图路径重排序。检索结果为一个 Evidence Pack，包含相关案例、因果路径、事实关系、确定性、证据摘录、来源 URL 和 PDF 页码。它也能查询实验数据文件的故障类别、负载、样本量。当前文本相似度是轻量级字符方法，适合这台 16 GB 内存、无独显的电脑；还没有接入独立的神经语义向量模型。

例如：

```powershell
python .\ship_fault_kg\retrieve.py --query '柴油发电机轴瓦磨损后全船失电，原因和建议？' --prompt
python .\ship_fault_kg\retrieve.py --query '空气冷却器污损在60%负荷有多少样本？'
python .\ship_fault_kg\retrieve.py --input-json .\ship_fault_kg\example_diagnosis.json --prompt
```

输出的 LLM 提示词要求区分“历史案例”与“本船已证实事实”，保持可能/很可能等限定词，并对每个关键结论引用证据编号。

### 7. 检索测试

`eval_queries.json` 含 12 道开发题：九道事故因果题、两道数据工况题和一道轴带发电覆盖边界题。运行：

```powershell
python .\ship_fault_kg\evaluate.py
```

当前结果见 `output/retrieval_evaluation.json`：九道事故题的案例 Recall@1 和 MRR@3 均为 1.0；人工标注关系的平均 Recall@5 为 0.9074、Recall@10 为 1.0、Precision@5 为 0.5333；两道数据题和一道覆盖边界题均通过。这些题根据同一批资料编写，是功能冒烟测试，**不是**独立专家盲评或跨船型泛化性能。

### 8. 本地 3B 模型生成诊断草稿

当 Ollama 已运行且安装 `qwen2.5:3b-instruct` 时：

```powershell
python .\ship_fault_kg\generate_demo.py
```

脚本只向本机 `127.0.0.1:11434` 发送 Evidence Pack，使用 2048 上下文和低温度。3B 模型只选择证据编号；程序检查编号、关系类别和案例归属，再从图谱事实与页码组装可追溯诊断草稿。生成的建议仍应由轮机专业人员审核；它不能替代现场检查、制造商手册或安全程序。

## Neo4j 导入与可视化

已在 Neo4j Desktop 2 中新建本地实例 `ShipFaultKG`，并将本图谱导入独立数据库 `shipfaultkg`。导入时创建了 234 个节点、325 条关系；原有 Neo4j 数据和密码均未修改。新实例使用 HTTP `7475`、Bolt `7690`。启动 Desktop 中的 `ShipFaultKG` 实例后，可在 Desktop 的 Query 页面选择数据库 `shipfaultkg`，或访问 <http://localhost:7475> 并用新实例创建时设置的密码登录。不要误选默认的空数据库 `neo4j`。

在 `shipfaultkg` 中核对导入数量：

```cypher
MATCH (n:ShipKG) RETURN count(n) AS nodes
```

```cypher
MATCH ()-[r]->() RETURN count(r) AS relationships
```

可视化一条事故案例：

```cypher
MATCH (c:ShipKG:Case)-[r:INVOLVES]->(n:ShipKG)
WHERE c.case_id = 'kommandor_susan_dg1_2025'
RETURN c,r,n LIMIT 60
```

查询结果切换为 Graph/图形视图，即可看到节点与连线。若要看一条具体因果链：

```cypher
MATCH p=(a:ShipKG)-[:CONTRIBUTED_TO|LEADS_TO*1..4]->(b:ShipKG)
WHERE a.name = '非原厂轴承材料粘结较弱'
  AND all(r IN relationships(p) WHERE r.case_id = 'kommandor_susan_dg1_2025')
RETURN p LIMIT 10
```

本次采用 Neo4j 的离线批量导入：`prepare_neo4j_admin_import.py` 将 SQLite 图谱转换为 `output/neo4j_admin_import/` 下的两份 CSV，校验节点 ID、关系端点和证据后，由 `neo4j-admin database import full` 写入全新的数据库文件，最后在 Desktop 的 `system` 数据库执行 `CREATE DATABASE shipfaultkg` 注册并启动。**不要对已经建成的 `shipfaultkg` 重复执行 full import**，否则会与现有数据库文件冲突。

下面的导入程序可用于将图谱合并进已有 Neo4j 数据库，它会提示输入该数据库的密码；本次新实例不需要再运行它。默认地址为 `http://localhost:7475`，数据库为 `shipfaultkg`，可通过 `NEO4J_URL`、`NEO4J_DBNAME` 等环境变量覆盖：

```powershell
& 'C:\Users\18270\anaconda3\envs\ragqna\python.exe' .\ship_fault_kg\import_neo4j.py
```

导入程序使用稳定 ID、`MERGE` 和 `ShipKG` 标签，不会清空其他图谱。

## 目前覆盖不到的内容

图谱目前没有真实的低速机轴带发电、电网耦合振荡、轴带联轴器断裂的直接故障案例。对此类问题，检索结果会标注 `related_cases_only`，只把相邻动力系统案例作为参考，不会声称已经找到直接根因。获得项目组真实报告后，优先新增轴带发电机、变流器、电网、联轴器、轴系扭振等实体，以及带监测时序的故障事件，再组织专家标注独立测试集。

论文《Data-driven model for marine engine fault diagnosis》此前下载的 PDF 内部结构不完整，本图谱构建没有使用它，也没有从该文件抽取事实。
