# 已构建船舶动力系统故障知识图谱：内容、结构、因果链与改进方向

> 核对日期：2026-10-04。本文描述 `ship_fault_kg` 当前磁盘文件中的**实际内容**，不是未来计划中的完整船舶动力系统图谱。建议与[构建和 Neo4j 导入方法汇报](REPORT_KG_BUILD_NEO4J_CN.md)配合阅读。

## 1. 先说明“建好了什么”

当前原型有 **234 个节点、325 条关系、171 条证据记录、488 个文本片段**。节点分为 **17 种类型**，已出现的关系有 **28 种类型**；人工整理了 **7 起事故案例**，涉及 **5 条船、3 类动力系统**。488 个片段包括 406 个报告 PDF 页和 82 篇中文船机文章。当前构建报告的 `validation_errors` 为空；对 CSV 再检查，节点/关系 ID 无重复，关系端点与证据引用均存在。

这张图谱的定位是**故障诊断知识原型**：可以展示案例中的设备、条件、原因、故障、后果及报告出处，也可以作为后续 RAG 的证据来源。但它**不是**完整船舶动力系统故障分类库，更不是经过现场验证的自动预测模型。尤其缺少项目重点关注的低速机轴带发电、电网耦合振荡和联轴器断裂的直接故障案例。

## 2. 图谱由哪些文件组成

图谱不是单独一个 `.db` 文件，而是“原始来源 → 人工整理的事实 → 构建程序 → 多种输出格式”的组合。以下路径均相对于项目根目录 `D:\RAGQnASystem\RAGQnASystem-main`。

| 层次 | 文件或目录 | 实际用途 | 是否直接进入当前 Neo4j |
| --- | --- | --- | --- |
| 原始资料 | [`ship_fault_kg_data/02_reports/`](../ship_fault_kg_data/02_reports/) | 事故调查 PDF，供人工核对及构建时验证页码、定位短语 | 不是整份 PDF 入库；有关事实的摘录被复制到关系属性 |
| 实验与语料 | [`ship_fault_kg_data/01_datasets/`](../ship_fault_kg_data/01_datasets/)、[`ship_fault_kg_data/04_code_and_schemas/`](../ship_fault_kg_data/04_code_and_schemas/) | 实机实验索引、测点字典、匿名推进器汇总、仿真类别及中文语料 | 仅被抽取出的结构化节点和边入库；原始时序 CSV、文章全文未入库 |
| 来源清单 | [`ship_fault_kg_data/05_metadata/source_manifest.csv`](../ship_fault_kg_data/05_metadata/source_manifest.csv) | 记录来源名称、原始 URL、本地位置和复用说明 | 部分来源转为 `Source` 节点；清单本身不作为图节点 |
| 人工确认的案例 | [`curated_cases.py`](curated_cases.py) | 7 起事故的事实、关系、页码、原文定位词和确定性等级 | 经构建后成为案例、故障等节点及边 |
| 核心构建程序 | [`build.py`](build.py) | 合并各来源，生成稳定 ID，验证证据，输出数据 | 间接决定 Neo4j 内容 |
| SQLite 主数据 | [`output/ship_fault_kg.sqlite`](output/ship_fault_kg.sqlite) | 四张表：`nodes`、`edges`、`evidence`、`passages`；当前本地检索程序直接读取它 | 前三张表经转换后参与 Neo4j 导入；`passages` 未进入 |
| 可审阅的 CSV | [`output/nodes.csv`](output/nodes.csv)、[`edges.csv`](output/edges.csv)、[`evidence.csv`](output/evidence.csv)、[`passages.csv`](output/passages.csv) | SQLite 内容的表格副本；其中 `nodes.csv` 逐一列出全部 234 个实体实例 | 不是直接送给 `neo4j-admin` 的最终格式 |
| Neo4j 批量 CSV | [`prepare_neo4j_admin_import.py`](prepare_neo4j_admin_import.py) 及 [`output/neo4j_admin_import/`](output/neo4j_admin_import/) | 生成带 `:ID`、`:START_ID`、`:END_ID`、`:TYPE`、`:LABEL` 列头的节点/关系文件 | **是**首次离线批量导入所用文件 |
| 图交换格式 | [`output/ship_fault_kg.graphml`](output/ship_fault_kg.graphml)、[`export_graphml.py`](export_graphml.py) | 便于 Gephi 等图工具读取；现存文件含 234 节点、325 边 | 否，属于另一种可视化/交换格式 |
| 质量记录 | [`output/build_report.json`](output/build_report.json) | 类型数量、来源页数、校验结果 | 否，负责核查而非业务图节点 |
| 应用与测试 | [`retrieve.py`](retrieve.py)、[`evaluate.py`](evaluate.py)、[`generate_demo.py`](generate_demo.py) 及相应 `output` 结果 | 本地检索、开发题评价和 3B 模型证据演示 | 当前检索读 SQLite，不是直接查询 Neo4j |
| 在线合并程序 | [`import_neo4j.py`](import_neo4j.py) | 用 `MERGE` 思路向已有 Neo4j 库增量合并 | 与首次 `neo4j-admin full import` 不同；旧版 `py2neo` 对 Neo4j 2026 的兼容性仍需验证 |

需要特别区分三个层次：**原始资料**是证据来源；**SQLite/CSV**是可复现的构建结果；**Neo4j**是其中“节点 + 关系 + 关系证据属性”的图数据库呈现。删除某个中间文件后，是否能重建，取决于原始资料、`curated_cases.py` 和构建脚本是否仍在；不能仅凭 Neo4j 页面是否连接成功判断图谱文件已丢失。

## 3. 图谱的数据模型：实体、关系和属性

### 3.1 节点的共同属性

在 SQLite `nodes` 表中，每个实体实例都有 `id`、`kind`、`name`、`aliases` 和 `props`：

- `id`：稳定标识，格式类似 `shipkg:fault:...`。程序依据“节点类型 + 规范化后的名称”计算摘要；同类型同名实体会复用一个节点。
- `kind`：实体类型，如 `Fault`、`Case`、`Sensor`。
- `name`：主要展示名，可为中文或英文。
- `aliases`：检索时使用的别名、英文表达或编号；目前只是字符串，尚无独立的同义词本体。
- `props`：JSON 字符串，存放类型特有属性。大多数故障、原因、动作节点的 `props` 目前为 `{}`。

首次批量导入 Neo4j 时，每个节点带共同标签 `:ShipKG` 和类型标签（如 `:Fault`），并保存 `id`、`kind`、`name`、`aliases`、`props_json`，另将 `case_id`、`data_origin`、`data_rows` 中已有的值展平成属性。**Neo4j 中的 `props_json` 是 JSON 文本，不是把其中每个字段都自动建成独立可索引属性。**

### 3.2 当前 17 类实体逐项盘点

下表的“专有属性”指 SQLite `props` 中实际出现的键；不重复列共同字段。数量来自 [`build_report.json`](output/build_report.json)，全部实例可在 [`nodes.csv`](output/nodes.csv) 逐一查看。

| 类型 | 数量 | 含义与示例 | `props` 中实际出现的键 |
| --- | ---: | --- | --- |
| `Action` | 14 | 整改/运维行动，如“使用原厂零件重建并大修发电机组” | 无 |
| `Case` | 7 | 一次有边界的事故/故障案例，如 Kommandor Susan DG1 | `case_id`, `data_origin` |
| `Cause` | 5 | 调查指出的原因或风险根源，如“油道残留碎屑” | 无 |
| `Check` | 4 | 待检查项目，如核验轴承与大修零件来源 | 无 |
| `Component` | 8 | 具体部件，如吊舱推进电机、连杆大端轴瓦 | 无 |
| `Condition` | 19 | 工况、状态或背景条件，如大风浪纵摇、负载 60% | 无 |
| `Consequence` | 6 | 后果，如全船失电、失去推进、机舱火灾 | 无 |
| `Dataset` | 4 | 数据来源集合，如 Marine Engine Fault Dataset | `data_origin`, `instances`（并非每个节点都有 `instances`） |
| `Equipment` | 7 | 案例中的设备，如 DG1 柴油发电机、某主机 | 无 |
| `Fault` | 41 | 故障、异常或数据集状态标签；**不全是已确认故障** | 无 |
| `Observation` | 12 | 方位推进器匿名汇总表的逐行观察 | `data_origin`, `record`, `reference_class`, `warning_hours`, `warning_months` |
| `Run` | 16 | 实验数据文件/运行工况 | `anomaly_state`, `columns`, `data_origin`, `data_rows`, `schema_type` |
| `Sensor` | 70 | 实验数据字典中的测点/通道 | `category`, `in_reference`, `in_scenario_files`, `unit` |
| `Source` | 10 | 被结构化边引用的报告或数据集来源 | `category`, `license`, `local_item`, `url` |
| `Symptom` | 3 | 可观察症状/预警，如机油高温报警 | 无 |
| `System` | 3 | 柴油机机械推进、柴油发电—电力推进、电力—吊舱推进 | 无 |
| `Vessel` | 5 | Kommandor Susan、Windcat 8、Wight Sky、Finlandia Seaways、Spirit of Discovery | 无 |

其中 Wight Sky 关联三个不同事故案例，因此“5 条船”与“7 起案例”并不矛盾。`Source` 只有 10 个，并不表示来源清单仅 10 条：部分资料只被收录为文本片段，没有成为已核验事实边的来源节点。

### 3.3 关系的共同属性、证据属性和 28 个关系类型

SQLite `edges` 表每条关系都有 `id`、`source`、`relation`、`target`、`evidence_id`、`case_id`、`certainty`、`props`。当前 325 条边的 `props` 全部为 `{}`。`evidence_id` 指向 `evidence` 表，那里有 `source_file`、`source_url`、`source_kind`、`page`、`locator`、`quote`。首次导入 Neo4j 时，这些证据字段被**复制为边的属性**，便于直接点边看页码和摘录；171 条证据并未另建 171 个 Neo4j 节点。

下表列出数据库里**实际出现**的所有关系类型。“常见两端”描述已出现的节点类型，某些关系还存在同类节点之间的连接；完整逐边清单见 [`edges.csv`](output/edges.csv)。

| 关系 | 数量 | 大意与常见两端 |
| --- | ---: | --- |
| `ADDRESSES` | 7 | `Action → Cause/Condition/Fault`：行动针对问题 |
| `AFFECTS_COMPONENT` | 8 | `Fault → Component`：故障影响部件 |
| `ASSOCIATED_WITH` | 1 | `Fault → Condition`：相关，不直接等于因果 |
| `AT_LOAD` | 16 | `Run → Condition`：运行文件的负载工况 |
| `CHECKS` | 4 | `Check → Cause/Condition`：检查目标 |
| `CONTRIBUTED_TO` | 4 | `Cause/Condition → Fault/Condition`：促成，保留证据措辞 |
| `DOCUMENTED_BY` | 11 | `Case/Dataset → Source`：来源 |
| `HAS_CASE` | 19 | `Vessel → Case` 或 `Dataset → Observation`：归属案例/记录 |
| `HAS_CHANNEL` | 70 | `Dataset → Sensor`：测点通道 |
| `HAS_COMPONENT` | 8 | `Equipment → Component`：设备包含部件 |
| `HAS_EQUIPMENT` | 7 | `Case → Equipment`：案例设备 |
| `HAS_RECOMMENDED_ACTION` | 12 | `Observation → Action`：匿名记录的建议行动 |
| `HAS_RUN` | 16 | `Dataset → Run`：数据文件/运行记录 |
| `IN_SYSTEM` | 7 | `Case → System`：所属动力系统 |
| `INCREASES_RISK_OF` | 1 | `Cause → Fault`：增加风险，并非必然发生 |
| `INCREASES_SEVERITY_OF` | 1 | `Condition → Fault`：加剧故障严重度 |
| `INDICATES` | 1 | `Symptom → Cause`：症状提示原因 |
| `INVOLVES` | 64 | `Case → 故障/条件/原因/后果/动作等`：纳入某案例，不表因果 |
| `LEADS_TO` | 23 | 故障/条件/后果等之间的“导致”或后果传递 |
| `LIMITS_DETECTION_OF` | 1 | `Condition → Fault`：妨碍故障发现 |
| `MAY_CONTRIBUTE_TO` | 2 | `Cause/Condition → Fault`：可能促成，须保留不确定性 |
| `PRECEDED` | 2 | `Symptom → Fault`：时间上先于故障，**不代表症状导致故障** |
| `PROMPTS` | 1 | `Symptom → Action`：症状应触发行动 |
| `REDUCES_EFFECTIVENESS_OF` | 1 | `Condition → Action`：使处置行动失效或减效 |
| `SHOWS_CONDITION` | 20 | `Dataset/Observation → Fault`：数据集或记录呈现某标签/状态 |
| `TESTS_FAULT` | 15 | `Run → Fault`：实验文件测试的故障类别 |
| `TRIGGERS` | 2 | `Condition/Fault → Fault`：触发保护或停机事件 |
| `WORSENS` | 1 | `Fault → Consequence`：加重后果 |

325 条边中，160 条带事故 `case_id`，165 条没有 `case_id`（主要是数据集和组织结构关系）；人工整理的**因果类边共 34 条**。其余多为结构、数据集标签、检查或行动关系，不能统称为“因果链”。代码白名单中允许 `CAUSES`，但当前数据里 **`CAUSES` 实际出现 0 条**，不能在汇报中说它已建成具体事实。

### 3.4 确定性与来源字段怎样理解

`certainty` 实际取值及边数为：`reported` 275、`probable` 4、`possible` 2、`reported_action` 7、`derived_action` 5、`dataset_label` 24、`simulated` 8。它标示**信息性质/报告措辞**，不是模型预测概率；`reported` 的 275 条中也包括许多 `HAS_CHANNEL` 等结构边，绝不能解释成“275 条经调查确认的因果关系”。

171 条 `evidence` 记录按 `source_kind` 分为：事故报告 63、数据集 101、代码/仿真说明 7。不同边可以引用同一条证据，因此“证据数”与“边数”不相同。488 个 `passages` 是检索文本，不是 488 个图节点；它们没有被当前 Neo4j 离线导入。

## 4. 船舶动力系统故障究竟有几类

先区分三种口径：

1. **系统口径：3 类**，即柴油机机械推进、柴油发电—电力推进、电力—吊舱推进。这是 `System` 节点的分类，不是故障数量。
2. **标签口径：41 个 `Fault` 节点**。它们来自四组来源，且包含“正常”和“未确认预警”，所以不能称为 41 类已确诊故障。
3. **实验口径：5 个柴油机实机受控试验故障场景**。这是一个特定数据集的五类标签，不代表全船动力系统只有五类故障。

为使“41”可审查，以下把**全部 41 个 `Fault` 名称**按进入图谱的来源列出；这是一种来源分组，不是已写进数据库的正式 `FaultClass` 层级：

| 来源组 | 数量 | 当前 `Fault` 节点名称 |
| --- | ---: | --- |
| 7 起 MAIB 人工整理事故涉及的故障/事件 | 16 | 柴油发电机灾难性失效、吊舱转至90度停放、进水停机序列启动、连杆大端轴承断油、连杆大端轴瓦失效、连杆盖螺栓松动与断裂、连杆盖配合面微动磨损、连杆小端疲劳断裂、曲轴箱被连杆击穿、曲轴主轴承与曲柄销断油、推进电机保护跳闸、推进电机超速、推进电机扭矩骤降、轴承快速磨损、主机灾难性失效、主轴承瓦片转位 |
| Marine Engine Fault Dataset 实机受控试验 | 5 | `Air-cooler fouling`、`Air-filter clogging (compressor)`、`Cooling-water pump cavitation`、`Injection-valve nozzle clogging`、`Turbine degradation` |
| 方位推进器匿名监测汇总 | 12 | `Additive depletion`、`Babbitt wear (Pb)`、`Coupling resonance`、`Fuel dilution`、`Gear mesh anomaly`、`High-harmonic impact train`、`Mass imbalance`、`Normal operation`、`Normal wear trend`、`Structural looseness`、`Unconfirmed bearing-related spectral anomaly`、`Unconfirmed bearing-related warning` |
| 仿真类别：UCI 2 + TSRF 6 | 8 | `燃气轮机涡轮退化`、`燃气轮机压气机退化`；`Head-crack`、`Liner-wear`、`Normal`、`Piston-ablation`、`Ring-adhesion`、`Ring-wear` |

当前 `Fault` 标签混装了真正的故障、保护动作、退化、风险提示以及 `Normal` / `Normal operation` / `Normal wear trend`。这是原型的重要本体缺陷；后续宜拆分为 `FailureMode`、`Degradation`、`ProtectiveEvent`、`Warning`、`OperatingState` 等层级，并区分“已证实”“疑似”“正常参照”，否则按 `Fault` 数量做统计会误导。

## 5. 已记录的因果链：7 起案例分别是什么

下面只总结当前数据中**有边支撑**的链条；箭头旁的“可能/很可能”来自边的 `certainty`。这不是把七起事故拼成一条全局因果链。每条原始边的来源文件、页码、英文摘录见 [`edges.csv`](output/edges.csv) + [`evidence.csv`](output/evidence.csv)，或在 Neo4j 点击边的属性。

| 案例 | 核心链条 | 需要保留的边界 |
| --- | --- | --- |
| **Kommandor Susan DG1** | 非原厂轴承材料粘结较弱 **很可能促成** 连杆大端轴瓦失效 → **很可能导致** 柴油发电机灾难性失效 → 全船失电 → 失去推进；发电机失效也通向机舱火灾，全船失电又通向电动锚机无法释放锚 | 轴承材料与轴瓦失效、轴瓦与发电机失效两边为 `probable`（报告第 5 页）；“非原厂零件超出适用保养周期 → 轴瓦失效”是另一条促成边（第 8 页）。图中“未核验零件真伪 → 装入非原厂轴承”是独立分支，未直接接到轴瓦失效边上 |
| **Windcat 8 左舷主机** | 连杆大端轴瓦失效 → 连杆击穿曲轴箱 → 机舱火灾 | 报告中“机油高温报警 `PRECEDED` 轴瓦失效”只是先后关系；“轴瓦本体可能存在薄弱点”被写作 `ASSOCIATED_WITH`，不能擅自改成确定根因 |
| **Wight Sky 2017 主机** | 油道残留碎屑 **很可能促成** 主轴承瓦片转位 → 连杆大端轴承断油 → 主机灾难性失效 → 机舱火灾 | 第一条为 `probable`（第 14 页）；“关键断路器置于手动位 → 关键设备失电”是同一案例的另一分支，不是上述机械故障链的中间环节 |
| **Finlandia Seaways 主机** | 连杆小端轴套更换产生应力集中 → **增加** 连杆小端疲劳断裂风险 → 主机灾难性失效 → 机舱火灾 | `INCREASES_RISK_OF` 不是必然因果；“连杆小端刻痕”是指示信息，不是导致应力集中的边 |
| **Wight Sky ME2** | 主轴承瓦片转位 → 曲轴主轴承与曲柄销断油 → 主机灾难性失效 | “油路磨粒与污染”和“主机不对中与异常振动”只标为 `possible` 促成因素（第 84 页）；并联机组拖转标为加剧严重度，润滑油压力下降为先于失效的症状 |
| **Wight Sky ME4** | 连杆大端轴承盖配对错装 → 连杆盖配合面微动磨损 → 连杆盖螺栓松动与断裂 → 主机灾难性失效 | 本链在事故报告第 84 页有定位证据；检查配对编号是 `Check`，不是事故已发生的原因 |
| **Spirit of Discovery 吊舱推进** | 主支：大风浪纵摇 → 螺旋桨出水 → 推进电机扭矩骤降 → 电机超速 → 保护跳闸 → 失去推进。另一支：舱底传感器位置偏低 → 进水停机序列启动 → 吊舱转至 90° 停放 → 加重失去操纵能力 | 两支分别反映超速保护与进水停机序列；目前图中没有一条边把两支机械地串成单一路径。前一支主要见第 42 页，后一支见第 42、43、51 页 |

上述表是**案例证据链**，不是“本船正在发生相同故障”的在线诊断结论。它也不应把 `CHECKS`、`ADDRESSES` 或 `PRECEDED` 与 `LEADS_TO` 混算为同一类因果边。

## 6. 图谱在文件与 Neo4j 里长什么样

图谱是**带方向、带类型和属性的多关系网络**，不是普通 Excel 关系表，也不是一张静态图片。其局部结构可以理解为：

```text
(Vessel 船舶) --HAS_CASE--> (Case 事故) --IN_SYSTEM--> (System 系统)
                                  │
                                  ├──HAS_EQUIPMENT──> (Equipment) --HAS_COMPONENT--> (Component)
                                  ├──INVOLVES───────> (Fault/Condition/Cause/...)
                                  └──DOCUMENTED_BY──> (Source 报告)

(Cause/Condition) --CONTRIBUTED_TO/LEADS_TO--> (Fault) --LEADS_TO--> (Consequence)
       ↑                                                       ↑
     CHECKS                                                   AFFECTS_COMPONENT
       │                                                       │
     (Check)                                                (Component)

每条业务边还可携带：case_id、certainty、source_file、page、quote 等。
```

文件呈现有三种：① [`ship_fault_kg.sqlite`](output/ship_fault_kg.sqlite) 是便于程序检索的四表数据库；② CSV 可逐行审核；③ GraphML 可用图可视化软件打开。Neo4j 中每个实体是圆形节点、每种有向关系是箭头，显示颜色和布局取决于浏览器设置，并非图谱语义本身。相同名称的 `Fault` 节点可能被不同案例复用，因此整图上案例之间可能通过共享节点看起来相连；**查询具体因果时必须按关系的 `case_id` 过滤**。

Neo4j Query 页面先选择数据库 `shipfaultkg`（不要选默认 `neo4j`），再执行下面的只读查询，并把结果切到 Graph/图形视图：

```cypher
MATCH (c:ShipKG:Case)-[r:INVOLVES]->(n:ShipKG)
WHERE c.case_id = 'kommandor_susan_dg1_2025'
RETURN c,r,n LIMIT 60;
```

如果只看 Spirit of Discovery 案例中的故障/后果链：

```cypher
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE r.case_id = 'spirit_of_discovery_pods_2023'
  AND type(r) IN ['LEADS_TO','TRIGGERS','WORSENS']
RETURN a,r,b LIMIT 30;
```

一张图的外观只能说明“节点与边可显示”，还要点击边查看 `page`、`quote`、`certainty`，才能判断它是否是可追溯的有效知识。

## 7. 已实现的约束，与尚未实现的约束

“约束”在这里有**程序校验、SQLite 数据库约束、Neo4j 图数据库约束**三个层次，不能混为一谈。

| 层次 | 当前实际情况 | 仍缺什么 |
| --- | --- | --- |
| 构建程序 | `build.py` 对关系类型使用白名单；检查关系两端、证据引用、确定性取值；PDF 页码或定位短语不存在时停止；字典按稳定 ID 去重 | 不能自动判定报告语义是否被正确解释，也未做完整领域规则验证（如每种关系允许哪些起止类型） |
| Neo4j CSV 预处理 | `prepare_neo4j_admin_import.py` 复查节点/关系 ID、关系端点、证据及关系类型，生成导入列头 | 不校验所有属性类型和事故之间的概念冲突；不将全文片段导入图 |
| SQLite | `nodes.id`、`edges.id`、`evidence.id`、`passages.id` 是 `PRIMARY KEY`；`edges.source`、`edges.target`、`edges.case_id` 有普通索引 | SQLite 表定义中**没有显式外键、CHECK 或唯一业务名约束**；孤立边主要靠构建程序阻止 |
| Neo4j | 首次 `neo4j-admin full import` 依赖导入 ID 将边连向节点；现有在线脚本含 `CREATE CONSTRAINT shipkg_id IF NOT EXISTS FOR (n:ShipKG) REQUIRE n.id IS UNIQUE` | 离线 CSV 预处理本身**不创建该约束**；不能仅据脚本存在就断言当前库已经启用。应在目标库运行 `SHOW CONSTRAINTS` 实查，必要时在确认无重复 ID 后再建立 |

节点 ID 基于 `kind + name`，边 ID 基于起点、关系、终点、证据和案例，因此重复构建同一份输入通常得到相同 ID；但**改名可能生成新 ID**，同一实体多种拼写也可能分裂为多个点。报告页码锚点只证明文本存在，不证明因果解释必然成立。更大规模应用需要规范词表、实体对齐、专家复核与版本管理。

## 8. 当前存在的主要问题

1. **重点对象覆盖不足。** 已有柴油机、发电机及吊舱推进相邻案例，但缺少真实低速机轴带发电、轴带电机磨损、联轴器断裂和电网耦合振荡事故的直接因果资料。相关查询只能提供相邻系统参考，不能称为已定位根因。
2. **`Fault` 本体过宽。** 正常状态、未确认预警、退化趋势、保护跳闸也被标为 `Fault`；正式统计和模型训练前必须拆类，否则“故障种类数”含义不清。
3. **来源异质性大。** 事故调查、实机受控实验、匿名监测和仿真不能赋予同样的现场证据权重。`data_origin` 与 `certainty` 已有初步区分，但缺少统一的证据等级和适用条件规则。
4. **人工事实规模小。** 仅 7 起事故、34 条因果类边；不够支撑复杂故障的普适预测，也未覆盖厂家手册、历史工单和船舶时序数据。
5. **实体规范化有限。** 当前以类型 + 名称计算 ID，中文/英文同义词、不同型号与同名部件的跨来源对齐仍较粗；已有共享故障节点可能让全图视觉上误连案例。
6. **文本与图谱没有完全打通。** 488 个片段留在 SQLite；Neo4j 中无独立 `Passage`/`Evidence` 节点，也无边到原文片段的直接跳转。关系属性虽有页码与摘录，但不便做完整的“实体—证据—文档”图遍历。
7. **检索与数据库分离。** 当前 `retrieve.py` 读 SQLite，使用别名、术语扩展和字符 TF-IDF，不使用 Neo4j 的图查询、全文/向量索引；对深层语义改写和复杂跨案例问题仍弱。
8. **约束与评测未闭环。** SQLite 未声明外键；Neo4j 约束是否实际启用需查询。现有 12 道测试题与构建资料同源，只能作开发冒烟测试，不能宣称真实船舶上的诊断性能。
9. **源文质量与许可。** PDF 文本提取依赖可解析文字，没有 OCR 流程；中文语料的开放再发布许可未逐条核明，因此不能直接公开分发全文或把未核对文本自动当成事实。

## 9. 改善方向：建议按顺序推进

| 阶段 | 具体要做什么 | 为什么优先 |
| --- | --- | --- |
| A. 清理本体与数据 | 拆分 `Fault` 中的正常、预警、退化、保护动作；制定设备/部件/故障编码、别名和型号规则；对 7 起案例请轮机专家复审 | 先确保标签含义正确，避免后续自动抽取和模型训练放大错误 |
| B. 补齐真实轴带链 | 收集项目组真实故障报告、监测时序、运维记录及制造商手册；新增轴带发电机、联轴器、轴系、变流器、电网、扭振等实体与可核验边 | 直接支撑项目核心问题，而不是长期依赖柴油机/吊舱相邻案例外推 |
| C. 强化证据结构 | 将证据或文档片段建为可独立查询节点；增加报告版本、事件时间、设备工况、页码/段落定位、专家签核和适用范围 | 支持更严格的来源审计，以及诊断结论逐句引用 |
| D. 建立数据库约束与更新流程 | 在 Neo4j 实查并创建适用的唯一约束/索引；引入官方兼容驱动、增量 `MERGE`、导入前后差异报告与备份 | 让“能重复导入”变成可控的日常更新，而非覆盖整库 |
| E. 提升检索 | 在现有案例约束路径检索之外加入全文/向量召回、实体消歧和重排序；明确区分“直接案例”“相邻参考”和“无证据” | 提高自然语言诊断报告接入后的召回能力，同时防止跨案例拼接 |
| F. 独立评价 | 另建由专家标注、与构建资料分离的测试集；评价实体对齐、证据 Recall@K/Precision@K/MRR、因果链正确性、报告引用与建议安全性 | 才能真正比较改进是否有效，而不是只看内部样例命中率 |

## 10. 汇报时可以使用的总结

目前我们已经做出一个**有来源、可核验、可查询的小规模船舶动力系统故障知识图谱**。它包含 7 起事故、234 个实体节点和 325 条关系，保留了事实的案例范围、报告页码和确定性；还接入实验工况和测点，能为后续诊断报告提供结构化证据。但 41 个 `Fault` 节点并不等于 41 类已证实故障，轴带发电与电网耦合的真实案例仍缺失。下一步应先规范故障本体和补齐项目真实数据，再推进 Neo4j 在线检索、向量/图混合召回及独立专家评价。

