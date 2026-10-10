# 船舶动力系统故障知识图谱：统一项目说明

> 科研方法原型，不用于无人审核的船舶运维决策。第三方资料保留原有权利，部分材料的再分发许可尚未核实。请先阅读[免责声明与第三方资料权利说明](../DISCLAIMER.md)。

更新日期：2026-10-07。知识版本：V4.2；按用户确认将12个Observation统一为记录级Source，原30个Source设为资料级；保留每条记录ID、状态、建议及来源关系，没有新增事故或知识事实。

目录整理：旧版本查询、展示和评价产物已归档至`history/organization_20261007/`；当前主数据与运行入口不变。详见[文件组织与归档索引](FILE_LAYOUT.md)，逐文件位置及SHA256见`history/organization_20261007/move_manifest.json`。历史快照中的重复文件保留，没有删除图谱数据。

项目目录：`D:\RAGQnASystem\RAGQnASystem-main\ship_fault_kg`；Desktop实例：`ShipFaultKG`；数据库：`shipfaultkg`。

本文统一原README、构建/导入报告、内容与局限报告、V2升级报告、V3故障导向报告及连接指南。原六份文档保存在 `history/docs_before_consolidation_20261005/`，仅用于追溯，不再作为当前操作入口。

## 1. 目标、成果与边界

从事故报告、厂家技术通函、论文及实验资料中整理有来源、限定条件和上下文的故障知识，构建小规模图谱，用它增强前级模型输出的初步诊断报告。主要交付是**知识图谱、检索增强方法、报告原型和实验记录**，不是训练完成的新诊断大模型，也不是无人审核的船舶控制/维修系统。

```text
报告、手册、数据、论文 → 页级核对、最小事实 → 实体/关系/证据 → SQLite主数据
                                                           ├→ Neo4j查询与可视化
                                                           └→ 实体/文本/图路径检索
师兄的初步诊断文本 ──────────────────────────────────────────→ Evidence Pack
                                                               ↓
                                                  已有LLM选证据 + 程序校验
                                                               ↓
                                       增强报告：解释、检查/措施、来源、不确定性
                                                               ↓（拟联调）
                                                    评价反馈 → 补检索/修正
```

### 当前实际规模

| 内容 | 数量 | 统计边界 |
| --- | ---: | --- |
| Neo4j ShipKG节点 / 关系 | **491 / 1185** | 同步后逐一比对本地和数据库的节点ID、关系ID、端点、名称、版本、证据编号，实际结果见核验回执 |
| 实体类型 / 实际关系类型 | 15 / 29 | 允许的关系词表不等于实际出现的类型 |
| 历史事故 / 经典故障入口 | 19 / 12 | 参考机理不是新增事故 |
| 统一Vessel / 统一System | 22 / 8 | Vessel含17船舶记录、5个剩余船型入口；System含3架构、5功能系统 |
| 统一Fault | 114 | 12故障类别入口、102具体故障或事件；不是114种确诊故障 |
| 统一Source | 42 | 资料级30 / 记录级12；记录ID、状态、建议、预警字段和来源定位保留 |
| 核心Sensor / 归档Sensor | 15 / 0 | 原始数据的70字段未删除 |
| 诊断关系 / 因果类关系 | 244 / 133 | 检查、措施、先后等不都属于因果 |
| 来源证据 / 可检索片段 | 332 / 852 | SQLite独立表，不另算为Neo4j节点 |

852片段包括545报告页、145中文语料文章、162参考页。证据字段复制在Neo4j关系上，全文片段仍由SQLite检索。规模符合200～500实体、600～1500关系、3～5子系统的原型目标，但不能据此宣称知识完备或诊断准确。

V4.2当前目标与核验数量：ShipKG节点491、关系1185、核心Sensor15、Source42；FaultType、Dataset、VesselType、Subsystem、Observation不再作为节点标签使用。实际建库成功以`output/neo4j_import_result.json`的version=4.2、verified=true为准。若Desktop仍显示旧数量或标签，请刷新、重连并重新运行旧结果帧；不能凭旧帧判断当前数据。

![历史V3数据库统计（500/1201，非当前V4）](history/organization_20261007/sensor_maintenance/output/maintenance_20261005/neo4j_full_counts.png)

仍保留既有原生配色及ShipKG最低显示优先级；FaultType已合并为Fault，不再单独设置其标签颜色和大小。以下截图仅说明历史V3显示效果，不代表V4结果。

![历史V3原生配色：Fault与FaultType合并前](history/organization_20261007/sensor_maintenance/output/maintenance_20261005/neo4j_native_style_restored.png)

### V4.0重新设计做了什么（前一轮）

1. **合并类型，不混淆身份。** VesselType→Vessel、Subsystem→System、FaultType→Fault。分别用`entity_level`、`system_level`、`fault_level`保留角色；不把船型概念等同于某条实船，也不把一般故障类别等同于已发生事件。原始500节点中没有需要删除的重复船舶/船型身份；不同案例里的同名设备、部件仍保留独立ID。
2. **按确认清单改显示名称。** 案例、设备、部件去掉开头船名/案例编码；23个全英文故障、5个英文措施、15个测点改中文；16个试验运行和12个监测摘要采用可读名称。ID不变，`original_name`、别名、`original_file_name`、`original_column_name`保留旧检索和CSV定位能力。
3. **删除4个Dataset入口而不丢来源。** 51条数据内容组织关系改为内容节点直接`DOCUMENTED_BY`资料来源，保留原数据集名、原关系、来源性质；仅删除4条旧Dataset→Source入口边。因此500→496节点，1201→1197关系，而非丢掉51条知识。原始数据文件、332证据、852文本片段均保留。
4. **规范故障与关系语义。** 3个正常参照状态从Fault移到Condition；故障类别12与具体故障/事件102统一为Fault。`INSTANCE_OF`仍表示分类而非因果，跨类型的`INVOLVES`采用“涉及故障/原因/检查方法”等中文显示名，系统归属统一；可能、很可能等措辞不被强化。
5. **本地重建后受控同步。** SQLite直接经Neo4j Query API同步，不经CSV。先备份、审核ID差异，再在一个事务中替换过期关系、移除旧类型标签、按稳定ID更新；只删除已批准的4个Dataset节点，不清空数据库。
6. **同步检索和展示。** 检索改用`knowledge_id`识别参考知识入口，不再依赖FaultType标签；更新HTML、GraphML、GraSS、完整清单及当前查询文件。10项回归测试通过，24题故障开发检索结果保留；这不是诊断准确率验证。

当前入口：[完整V4实体关系清单](D:/RAGQnASystem/RAGQnASystem-main/ship_fault_kg/output/entity_inventory_v4.md)、[Neo4j核验回执](D:/RAGQnASystem/RAGQnASystem-main/ship_fault_kg/output/neo4j_import_result.json)、[V4查询](D:/RAGQnASystem/RAGQnASystem-main/ship_fault_kg/queries_v4.cypher)。本轮合并前的V4.1完整数据库备份在`history/v4_1_before_source_merge_20261006/neo4j_snapshot.json`，旧SQLite、代码和输出也在同目录；更早的V3/V4.0备份仍保留。仅备份不等于自动回退，恢复应先检查差异再定向导入，不要混用普通MERGE造成新旧关系并存。

### V4.1清理与设备命名（前一轮）

删除的只是5个不带案例编号的船型入口：**专用货船、化学品船、双体客船、拖网渔船、滚装客船**。带SD编号的船舶记录和真实船名没有删除，它们代表不同案例里的船，不能按相似名称合并。普通货船、工程调查船、滚装货船、风电船员转运船、邮轮这5个未明确要求删除的入口暂保留。

原5个入口关联12条`OF_VESSEL_TYPE`分类边，已将船型名称保存为对应Vessel的`vessel_type`/`vessel_types`与Case的`vessel_type`；原边ID、类型节点ID、case_id、certainty和evidence_id保留在`vessel_type_provenance`中。Neo4j可直接查询标量`vessel_type`；`vessel_types`和嵌套的`vessel_type_provenance`保存在节点`props_json`内，不是Neo4j顶层列表/对象属性。12条原分类边删除，故障/原因/检查/措施的边不变。V4.0的496/1197变为491/1185，证据332与片段852不变。船型属性仍可查询和用于适用范围筛选，但本轮没有新增按船型过滤的检索算法。

设备类Equipment有12个以“系统”结尾的显示名。统一改为贴合原资料范围的“装置”，表示设备或装置集合，而System仍表示功能分类或动力架构。没有把集合硬改成某台泵、某个控制器等未经报告支持的单件设备；后续拿到设备台账后可以进一步拆分。另将“2017故障主机”改成“故障主机”；年份仍在原案例和旧名称中，不丢失时间背景。

| 原设备名称 | 新设备名称 |
| --- | --- |
| 柴油发电机润滑与排气系统 | 柴油发电机润滑与排气装置 |
| 左舷主机排气系统 | 左舷主机排气装置 |
| 2017故障主机 | 故障主机 |
| 右舷可调螺距桨液压系统 | 右舷可调螺距桨液压装置 |
| 海水压载与机舱排水系统 | 海水压载与机舱排水装置 |
| 主机启动与盘车系统 | 主机启动与盘车装置 |
| ME3燃油与排气系统 | ME3主机燃油供给与排气装置 |
| 主机海水冷却与舱底系统 | 主机海水冷却与舱底排水装置 |
| 可调螺距推进控制系统 | 可调螺距桨推进控制装置 |
| 控制空气与主机离合系统 | 控制空气供给与主机离合装置 |
| 主机润滑系统 | 主机润滑装置 |
| 吊舱推进系统 | 吊舱推进装置 |
| 可调螺距推进系统 | 可调螺距桨推进装置 |

设备ID、关联部件、来源和案例不变；`original_name`保留最初原名，`previous_display_name`保留V4.0显示名，旧显示名也加入别名。规则在`refinement_v4_1.json`，每次重建会再次应用，不会把旧名字和已删除的5个入口加回来。颜色方案未改动。

### V4.2本轮Source分层合并

用户已确认将12个Observation改为Source并设`source_level=记录级`；原30个Source设`source_level=资料级`。12条记录的旧ID（包括shipkg:observation命名空间）、名称、别名、record行号、预警时间、reference_class、source_id、data_origin及原始名称全部保留；`legacy_kind=Observation`仅作为历史属性，不是节点标签。另增加`source_record_type=监测摘要`便于识别记录性质。

合并是**类别统一，而非记录压缩**。12条SHOWS_CONDITION、12条HAS_RECOMMENDED_ACTION、12条DOCUMENTED_BY、7条系统归属关系的ID、端点、类型、证据编号和确定性不变。记录级Source仍通过DOCUMENTED_BY指向资料级Source。全图491节点、1185关系不变；Source30→42、实体类型16→15，证据332/文本片段852不变。本轮不新增监测记录检索算法；现有故障/案例检索和实验定位仍须回归检查。

`redesign.py`的`apply_source_levels()`在原始资料与命名整理后执行分层，避免改动源标注而产生新ID。原始构建代码仍暂用Observation中间类型，最后阶段统一为Source；输出SQLite、Neo4j、清单、HTML、GraphML和当前查询均使用Source。重建不会重新添加Observation标签。

## 2. 资料来源和文件分工

### 2.1 为什么自建，资料怎样用

在已调研范围内找到相关论文和代码，但未找到可直接下载复用、同时满足船舶故障、因果解释、来源审计和本地检索测试要求的完整图谱，故选择自建。不是断言船舶知识图谱研究不存在，也不把论文中的结果当成本项目结果。

| 来源 | 代表资料 | 实际用途和限制 |
| --- | --- | --- |
| 实机受控实验 | Marine Engine Fault Dataset、变量字典、运行索引 | 建设备/故障标签、运行条件和测点；不从标签推断事故根因 |
| 监测汇总 | Azimuth Thruster CBM方位推进器匿名汇总 | 按行建记录级Source、状态与建议；未获取的原始FFT不冒充已下载 |
| 仿真/代码资料 | UCI Naval Propulsion CBM、TSRF及弱热诊断参考 | 明确simulated来源，不当成实船事故 |
| 中文船机语料 | 船用柴油机RAG语料 | 当前精选145篇作为背景检索文本，未经核对的全文不直接转因果边 |
| MAIB调查及摘要 | Wight Sky、Kommandor Susan、Windcat 8、Finlandia Seaways、Spirit of Discovery、Pride、Queen Mary 2、Stena Europe及Safety Digest | 建19起历史事故，保留报告物理页、原文、调查概率措辞 |
| 厂家资料 | MAN服务通函、STAMFORD/AvK Application Guidance Notes | 补拉缸、烧瓦、冷却、扭振、轴带对中、电蚀和绝缘等参考知识，限定机型/构型 |
| 论文/方法代码 | 船机知识图谱论文、电网振荡论文、HFACS-KG等 | 参考模式和检索/抽取思路；阅读不等于集成、训练或复现全部算法 |

故障导向扩充下载16份PDF，15份支撑结构化事实；AGN232只进入参考文本，不强行抽边。来源清单保存网址、本地文件、许可、SHA256和页数；正常TLS校验未关闭。下载资料不等于全部进入图谱。

### 2.2 当前主要文件

以下路径相对于本项目目录，原资料在上一级 `ship_fault_kg_data/`。

| 文件 / 目录 | 作用 |
| --- | --- |
| `../ship_fault_kg_data/01_datasets/`、`02_reports/`、`03_papers/`、`04_code_and_schemas/` | 原数据、报告、论文及代码参考 |
| `../ship_fault_kg_data/05_metadata/source_manifest.csv`、`source_manifest_v3.csv` | 资料来源和复用说明 |
| `curated_cases.py` / `expanded_cases.py` | 原7起 / 新增12起事故的已整理事实 |
| `fault_profiles.py` / `schema.py` | 12故障入口、适用边界 / 实体关系词表与中文名 |
| `download_fault_sources.py` / `audit_sources.py` / `build.py` | 下载补充来源 / 定位检查 / 构建校验 |
| `output/ship_fault_kg.sqlite` | nodes、edges、evidence、passages四表，当前主数据 |
| `output/build_report.json` / `source_anchor_audit_v3.json` / `new_source_pages_v3.json` | 规模、来源定位与物理页索引 |
| `naming_v4.json` / `redesign.py` | 经确认的稳定ID命名规则 / 最后阶段类型与来源迁移 |
| `refinement_v4_1.json` | 本轮5个船型入口精确ID及13个设备改名规则 |
| `output/entity_inventory_v4.md` / `graph_inventory_v4.json` | 全部491实体、1185关系、属性和证据详单；文件名v4表示主版本，内容版本4.2 |
| `output/知识图谱_关系节点属性.csv` / `export_readable_csv.py` | 中文关系、两端节点主要属性及来源定位表；每次构建或导出清单时刷新，也可单独刷新 |
| `import_neo4j.py` / `output/neo4j_direct_plan.json` / `neo4j_direct_import.cypher` / `neo4j_import_guide.html` | SQLite直接生成和执行MERGE/SET；CSV非必需 |
| `sync_neo4j_v4.py` / `output/neo4j_import_result.json` | 已有V3/V4库定向同步 / 实际数据库核验回执 |
| `visualize_graph.py` / `output/shipkg_v4.grass` / `graph_viewer.html` / `export_graphml.py` | Neo4j样式、离线图谱、GraphML |
| `queries_v4.cypher` | 当前类型与角色的统计、故障/案例/来源查询 |
| `retrieve.py` / `generate_demo.py` / `example_diagnosis.json` | 轻量混合检索、标准输入和约束报告原型 |
| `evaluate.py` / `evaluate_fault_v3.py` / `verify_v4.py` | 开发评价和V4结构/检索回归；旧V2/V3测试是历史版本的断言 |
| `purge_archived_sensors.py` / `history/organization_20261007/sensor_maintenance/output/maintenance_20261005/` | 历史55测点真实删除备份及显式恢复入口，非日常步骤 |
| `check_neo4j_ready.ps1` / `check_neo4j_connection.py` | 只读服务/认证检查，不保存密码 |
| `history/` / `FILE_LAYOUT.md` | 历史代码文档、旧产物及归档索引，不是当前默认导入包 |

完整清单见[实体清单](D:/RAGQnASystem/RAGQnASystem-main/ship_fault_kg/output/entity_inventory_v4.md)及[结构JSON](D:/RAGQnASystem/RAGQnASystem-main/ship_fault_kg/output/graph_inventory_v4.json)。V2/V3文件和截图为历史产物，不作为当前导入依据。

### 中文关系节点属性CSV的使用与更新

`output/知识图谱_关系节点属性.csv`是一行一条有向关系的易读表：起点节点、起点类型、起点主要属性、关系名称、终点节点、终点类型、终点主要属性。后面附关系性质、证据性质、案例或知识单元、来源文件、物理页或记录位置、来源链接及稳定ID。当前1185行关系覆盖全部491节点。以后有孤立节点时，也会单独列出“暂无关联关系”，不会漏掉。

节点属性只展示主要业务字段，如船型、系统层级、故障层级、适用范围、来源层级、记录行、测点单位、试验数据行数等。空白表示没有相应业务属性。完整别名、旧名称和迁移审计属性仍见`graph_inventory_v4.json`，不把大段JSON堆进这份易读表。关系确定性保留“可能”“很可能”等区别，分类和检查关系不冒充因果结论。

每次成功执行`build.py`，以及执行`export_inventory.py`时，都会从本次SQLite主数据刷新同名CSV。只是改了源代码但未重建时，CSV不会先于图谱变化。单独刷新无需重建、无需连接Neo4j：

```powershell
$kgPython='C:\Users\18270\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $kgPython .\ship_fault_kg\export_readable_csv.py
```

CSV采用UTF-8 BOM，方便Excel/WPS读取中文。更新前关闭正在打开这份CSV的Excel/WPS窗口；文件被占用时保留上一份完整CSV并报错，关闭后重试即可。CSV是展示产物，直接改它不会写回图谱，下次刷新会覆盖手改内容。仅在Neo4j里改节点不会自动写回SQLite或CSV，应先把获批修改落实到构建事实/规则并重建，再同步数据库。本次未增加后台监控任务，也未改动Neo4j。

## 3. 构建步骤及每一步缘由

1. **限定研究任务和证据层。** 面向初步诊断增强，区分调查、实机试验、仿真、监测汇总、厂家指导和论文观察，避免同等看待来源。
2. **设计实体、关系、上下文。** 建设备/部件、原因/条件、症状/故障/后果、检查/措施及案例/来源；Fault用角色属性区分参考故障入口与具体事件。历史case_id与knowledge:*机理单元隔离，分类不表因果。
3. **按物理页核对原文。** 逐条登记起点、关系、终点、页码、定位短语和确定性。物理页从封面计数，可能与印刷页不同。关键词缺失或页码越界时构建停止。命中定位词只证明文本存在，不能代替工程语义审核。
4. **拆成最小事实并保留措辞。** “可能”仍是可能；PRECEDED只表先后；CHECKS/ADDRESSES是检查/行动，不是已发生原因。derived_action是研究者整理建议，不冒充原文命令。
5. **接入数据与文本但不越界。** 从实验索引建Run/负载/故障标签，从变量字典保留15测点；监测汇总按行处理；仿真明确标注。Dataset仅在原始构建阶段作为中间入口，V4最后阶段移除并把内容直接连到Source。PDF和文章片段用于召回，不自动生成未经核验因果边。
6. **稳定ID、去重与可读属性。** 源标注保留旧类型/原名以生成稳定ID，最终应用`naming_v4.json`改变显示名和标签，保留ID与别名。去前缀后的同名设备可能来自不同案例，不按同名盲目合并。新来源节点没有命名规则时构建停止，需补充审核规则。
7. **校验并生成SQLite快照。** 检查端点、证据、类型、确定性和定位。四表保存知识与文本，成功后输出规模；CSV为可选审阅副本，GraphML/HTML另生成。
8. **先节点后关系，受控在线合并。** 建唯一约束，以ID MERGE、SET补属性，不清空现有库。MERGE不会自动删除旧点，过期内容另做差异审核和备份。
9. **实时核验而非打印源数量。** 查询Neo4j全库、核心测点、归档残留，并比较全部活动ID与SQLite。展示时点开边看原文和适用机型，而不是只看一张漂亮图。

共享故障或后果节点可被不同案例使用；查询路径必须约束同一case_id/context_id，不能因整图视觉连接而拼接不存在的事故链。

## 4. 实体、关系、属性及约束

### 4.1 15类实体与当前数量

共同字段：id、kind、name、aliases；SQLite props为JSON，含display_name、kind_zh、graph_version及类型字段。Neo4j同时有ShipKG与具体类型标签，保存props_json，并展开可标量化属性。

| 类型 | 数量 | 含义 | 共同显示字段外的实际属性键集合 |
| --- | ---: | --- | --- |
| Vessel | 22 | 实船记录17 / 剩余船型5 | entity_level、anonymous、original_name、vessel_identity_status、vessel_type、vessel_types、vessel_type_provenance |
| System | 8 | 动力架构3 / 功能系统5 | system_level、classification_basis |
| Case | 19 | 历史事故 | case_id、data_origin、anonymous_vessel、original_name、vessel_identity_status |
| Equipment | 19 | 设备及装置集合 | original_name、previous_display_name、equipment_scope、case_ids、case_id（单一上下文时） |
| Component | 33 | 部件 | original_name、case_ids、case_id（单一上下文时） |
| Fault | 114 | 故障类别12 / 具体故障或事件102 | fault_level、semantic_class、knowledge_id、knowledge_layer、applicability、coupling_domains、data_origin |
| Cause | 10 | 原因 | 无 |
| Condition | 76 | 工况/条件/正常参照 | semantic_class（正常参照时） |
| Symptom | 13 | 症状 | 无 |
| Consequence | 20 | 后果 | 无 |
| Check | 33 | 检查 | 无 |
| Action | 51 | 措施 | 无 |
| Run | 16 | 试验运行文件 | original_file_name、anomaly_state、columns、data_origin、data_rows、schema_type |
| Sensor | 15 | 核心测点 | original_column_name、category、unit、in_reference、in_scenario_files、note、selection_reason |
| Source | 42 | 资料级30 / 记录级12 | source_level；资料级有original_title、category、license、local_item、url；记录级有source_record_type、source_id、data_origin、record、reference_class、warning_hours、warning_months |

同类型不是每个实例都有全部可选键；新增共同属性还有legacy_kind、original_name（改名时）。props_json不是自动建索引的对象。3个正常参照已移到Condition；Fault仍包含预警、退化和保护事件，114个节点不能报成114类确诊故障。12个记录级Source是监测汇总证据入口，不是12次新事故；16个Run是受控试验文件/工况入口，不是16条实船事故；12个类别Fault是参考机理检索入口，不代表12条本船已确认根因。

### 4.2 当前29种实际关系

| 类型 | 数量 | 意义 / 边界 |
| --- | ---: | --- |
| INVOLVES | 288 | 涉及上下文，不表因果 |
| BELONGS_TO_SYSTEM | 309 | 归属系统，研究者分类 |
| ASSOCIATED_WITH | 5 | 相关，不确认根因 |
| AFFECTS_COMPONENT | 33 | 影响部件 |
| TESTS_FAULT | 15 | 测试故障标签 |
| PROMPTS | 2 | 应触发行动 |
| AT_LOAD | 16 | 负载条件 |
| LEADS_TO | 87 | 导致，需保留确定性 |
| CONTRIBUTED_TO | 15 | 促成 |
| MAY_CONTRIBUTE_TO | 17 | 可能促成 |
| ADDRESSES | 43 | 措施应对问题 |
| HAS_CASE | 19 | 船舶发生案例 |
| HAS_EQUIPMENT | 19 | 涉及设备 |
| HAS_COMPONENT | 33 | 包含部件 |
| IN_SYSTEM | 79 | 69条涉及功能系统 / 10条采用动力架构，中文显示名区分 |
| PRECEDED | 6 | 先于，不等于导致 |
| HAS_RECOMMENDED_ACTION | 12 | 汇总记录建议 |
| SHOWS_CONDITION | 12 | 呈现状态标签 |
| TRIGGERS | 3 | 触发 |
| REDUCES_EFFECTIVENESS_OF | 2 | 削弱效果 |
| DOCUMENTED_BY | 87 | 来源于资料；新增51条内容直接连来源，删除4条数据集入口边 |
| LIMITS_DETECTION_OF | 13 | 妨碍发现 |
| OF_VESSEL_TYPE | 7 | 剩余船型入口的分类；另12条已转为属性和来源记录 |
| CHECKS | 33 | 检查目标 |
| INSTANCE_OF | 12 | 归入故障类别，非因果 |
| INCREASES_RISK_OF | 6 | 增加风险，非必然 |
| WORSENS | 4 | 加重后果 |
| INDICATES | 7 | 指示，非确认 |
| INCREASES_SEVERITY_OF | 1 | 加剧严重度 |

词表还允许CAUSES、HAS_STATUS、MONITORS，但当前没有实际关系，不能宣称已建成。

### 4.3 属性与证据性质

SQLite边固定字段：id、source、relation、target、evidence_id、case_id、certainty、props。Neo4j边复制name、版本、ID、确定性中文名、source_file/source_url/page/locator/quote，方便直接点边溯源。

边扩展键实际包括：applicability、classification_basis、classification_rule、context_id、coupling_domains、data_origin、graph_version、is_causal、knowledge_layer、name。可选字段不是每条边都有。

certainty不是概率：reported明示554条、probable很可能8、possible可能2、reported_action原文行动41、derived_action整理建议22、dataset_label实验标签24、simulated仿真8、curated_classification非因果分类476、guidance厂家指导48、research_observation论文观察2。12条旧分类边的确定性已保存到属性，不能重复算在1185条边里。可能/很可能也体现在边的中文name中，不强改成确定结论。

332证据包括报告222、数据集46、厂家指导50、代码7、论文7。同一原文支持多条边，不等于332次事故。文本片段也不是图节点。

### 4.4 约束的三个层次

| 层次 | 已有 | 缺少 / 注意 |
| --- | --- | --- |
| 程序 | 类型白名单、端点/证据存在、定位检查、稳定ID去重 | 不能自动判断工程因果，关系起止类型规则待完善 |
| SQLite | 四表id主键；edges.source/target/case_id普通索引 | 无显式外键/CHECK，依赖构建校验 |
| Neo4j | ShipKG.id唯一约束；ID MERGE | 不自动消歧/删除旧点，可用SHOW CONSTRAINTS实查 |
| 检索/报告 | 同上下文路径、编号/类别校验、未知问题无证据 | 无完整型号适用性与专家审核闭环 |

## 5. 事故、经典故障与因果链

### 5.1 19起事故清单

| case_id | 内容 | 来源 |
| --- | --- | --- |
| kommandor_susan_dg1_2025 | Kommandor Susan DG1轴瓦失效、火灾与失电 | MAIB 2026/10 |
| windcat8_port_engine_2017 | Windcat 8左舷主机轴瓦失效 | MAIB 2018/1 |
| wight_sky_me_2017 | Wight Sky重装后断油失效 | MAIB 2018/14 |
| finlandia_seaways_me_2018 | Finlandia Seaways连杆小端疲劳断裂 | MAIB 2021/2 |
| wight_sky_me2_2018 | Wight Sky ME2主轴承/曲柄销断油 | MAIB 2022/4 |
| wight_sky_me4_2018 | Wight Sky ME4轴承盖错装 | MAIB 2022/4 |
| spirit_of_discovery_pods_2023 | 风浪下吊舱推进丧失 | MAIB 2026/6 |
| sd2013_02_control_air | 滚装客船控制空气不足、离合器脱开、撞泊位 | Safety Digest 2/2013例2，物理页14–15 |
| sd2013_03_turning_gear | 专用货船盘车未脱开、联锁失效、启动损坏 | 同上例3，16–18 |
| sd2013_05_missing_filter | 货船漏装滤芯、污染抱轴、活塞卡死 | 同上例5，21–23 |
| sd2013_12_oily_rag | 双体客船含油抹布落至排气歧管起火 | 同上例12，40–42 |
| sd2016_05_cpp_backup | 滚装客船误按CPP备用按钮、失控撞泊位 | Safety Digest 1/2016例5，19–21 |
| sd2016_08_generator_oil | 滚装客船滑油泵堵头松脱、喷油火灾 | 同上例8，26–28 |
| sd2016_09_cpp_response | 化学品船CPP倒车参数错误、响应迟缓 | 同上例9，29–30 |
| sd2016_14_sea_valve | 货船压载泵检修隔离失效、机舱进水 | 同上例14，40–42 |
| sd2016_22_cooling_pipe | 拖网渔船疑似海水冷却管失效、沉没 | 同上例22，59–60 |
| pride_can_cpp_2014 | Pride背压阀卡滞、超压法兰破裂火灾 | MAIB 2015/22 |
| queen_mary2_hf_2010 | Queen Mary 2滤波电容退化爆炸、失电 | MAIB 2011/28 |
| stena_europe_fuel_2023 | Stena Europe燃油法兰松动、热表面喷油火灾 | MAIB 2024/20 |

Wight Sky有三起案例；Pride同时出现在摘要和专门报告，只计一例。9个摘要事件的船型编号不是公开船名。

### 5.2 12个故障入口与参考机理

| 入口 | 代表链 / 知识 | 来源与适用边界 |
| --- | --- | --- |
| 拉缸 | 表面抛光/涂抹→油膜难维持→可能黏着拉伤→表面硬化；缸况与泄放油铁含量检查 | MAN SL2016-633、2019-685、2023-737；主要MAN B&W两冲程 |
| 烧瓦与轴承咬死 | 滑油异物→主轴承咬死；未响应磨损报警加重损伤；BWM核验 | MAN SL2013-569；工程检索统称，非所有轴瓦问题均为烧瓦 |
| 冷却水通道堵塞与热过载 | 水处理不当→结垢堵塞→换热下降→可能热过载/阀座裂漏 | MAN SL2016-623；四冲程闭式冷却按机型核对 |
| 冷却回路汽蚀 | 扫气冷却器低流量→可能局部沸腾→可能管路汽蚀 | MAN辅助效率资料；非所有泵汽蚀的一般结论 |
| 扭振减振器失效 | 润滑不足/污染、水分或超速→失效风险 | MAN SL2017-654；不可推广维护周期 |
| 轴带发电机对中异常与振动损伤 | 齿轮箱热膨胀/风浪船体挠曲→对中变化→可能振动损伤 | STAMFORD AGN039；重点齿轮传动构型 |
| 发电机轴承机械磨损 | 缺脂、对中异常、轴向振动微动磨损→滚动轴承失效 | AGN076；区别于主机滑动轴瓦 |
| 电机与发电机轴承电蚀 | 不对称磁场→轴电压/闭合轴电流→轴承电蚀 | AGN033；绝缘和接地按机型 |
| 发电机绕组绝缘劣化 | 潮湿/污染→绝缘电阻下降；故障电流热应力→损伤风险 | AGN040/035；无无机型依据的通用阈值 |
| 联轴器故障 | 锁固不足→CPP执行器小联轴器松动→传动失效→螺距控制丧失 | MAIB Hebrides 2017/20；不是主轴断裂事故 |
| 轴系扭振与联轴器过载风险 | 燃烧脉动→共振风险→疲劳磨损；短路/不同步冲击转矩 | AGN235/039；须TVA/试验验证 |
| 船舶电网耦合振荡 | 转矩/负荷及控制参数→可能电压频率振荡；轴带化学品船观察 | Frontiers DOI 10.3389/fenrg.2020.529756；部分未超限，非三起新事故 |

5子系统：燃油与进排气、润滑与轴承、冷却与海水、传动与推进、电力与控制。热—机—电是耦合域属性，不是额外虚构设备层。

### 5.3 典型历史链与限制

- Kommandor Susan：非原厂材料粘结较弱**很可能促成**轴瓦失效，**很可能导致**发电机灾难性失效→失电→失去推进。
- Windcat 8：轴瓦失效→连杆击穿曲轴箱→火灾；高温报警是先后，不是致因。
- Wight Sky 2017：油道碎屑**很可能促成**瓦片转位→断油→主机失效→火灾；断路器失电是另一分支。
- Finlandia Seaways：轴套更换应力集中→增加疲劳断裂风险→主机失效→火灾；风险非必然。
- Wight Sky ME2：瓦片转位→曲轴/曲柄销断油→失效；污染/不对中是可能促成。
- Wight Sky ME4：轴承盖错配→微动磨损→螺栓松动断裂→失效。
- Spirit of Discovery：风浪→桨出水→扭矩骤降→超速→保护跳闸→失去推进；进水停机为并行分支。
- Pride：背压阀卡滞→CPP超压→法兰破裂→喷油至热排气管→火灾。
- Stena：燃油法兰松动→压力燃油泄漏→喷至裸露热表面→火灾→主机无法工作。
- Queen Mary 2：电容退化→内弧/介质汽化→壳体破裂/爆炸；与失电关系保留“很可能”。

完整边和页码见SQLite、结构JSON或Neo4j属性；以上参考链不是本船在线根因确认。

## 6. 15测点与55归档节点的真实删除

保留：发动机转速、1缸最高缸压、增压空气压力、燃油流量、1缸排气温度、冷却水进口温度、冷却水出口温度Ⅰ、滑油进口温度、滑油出口温度、滑油循环泵压力原始电压、淡水冷却压力原始电压、主机冷却水流量、增压空气冷却器出口空气温度、轴转矩、轴功率。

选择理由是减少重复缸/出口和派生效率项，保留燃烧、润滑、冷却和传动观察。两个原始压力通道单位V，未经标定不能当bar/Pa；原70字段无实际电网测点，15个不能说覆盖完整电域。

原先55点只改为ArchivedSensor/ArchivedShipKG，所以全库仍555。2026-10-05按用户要求核对精确55个ID和86条直接边ID，导出完整标签/属性/端点，备份读回后在一条受保护事务中DETACH DELETE。当时删除后全库500/1201，Sensor15、ArchivedSensor0；V4再删除4个Dataset入口后为496/1197。本轮未再次删除测点，故障链未变。

备份：`history/organization_20261007/sensor_maintenance/output/maintenance_20261005/deleted_sensors_backup.json`；同目录记录：`purge_receipt.json`。Neo4j删除不能直接撤销，但可用外部备份重建；原始数据未删除。日常导入不会加回55点，因为SQLite只保留15点。

旧“取消归档”脚本只能改标签，不能恢复已删除节点。需要回退本轮删除时，审阅备份后显式运行（不是日常操作）：

```powershell
python .\ship_fault_kg\purge_archived_sensors.py --restore
```

脚本拒绝重复目标ID，恢复后仍使用归档标签。不要全量导入旧V2来恢复，可能加回过时知识。

9个Vessel和9个Case显示名已去“匿名”前缀，原ID/original_name/匿名身份状态保留。显示名“船型+摘要编号”不是实际船名，不能改变来源身份边界。

## 7. Neo4j连接、导入与排障

### 7.1 日常启停

Desktop 2 → Local instances → ShipFaultKG → 点一次Start → 等RUNNING → 打开 [localhost:7474](http://localhost:7474/browser/) 或 [127.0.0.1:7474](http://127.0.0.1:7474/browser/) → 使用现有neo4j账号密码 → 选shipfaultkg。

连接地址 `neo4j://127.0.0.1:7687`，本机单实例也可用 `bolt://127.0.0.1:7687`。7474是网页，7687是数据库；不要用旧7475/7690。关网页不等于停止数据库；结束时Desktop点Stop，等待STOPPED。正常启动曾约46秒，不固定；不要重复启动或同时运行neo4j console。

### 7.2 已修正配置

配置文件：`C:\Users\18270\.Neo4jDesktop2\Data\dbmss\dbms-956da0b3-4eec-4a04-aa01-484899f94108\conf\neo4j.conf`。

```properties
server.default_listen_address=127.0.0.1
server.default_advertised_address=127.0.0.1
server.bolt.listen_address=:7687
server.bolt.advertised_address=:7687
server.http.listen_address=:7474
server.http.advertised_address=:7474
```

该Desktop将主机与boltListenAddress直接拼接，故连接器只写端口，避免 `127.0.0.1127.0.0.1`。只监听本机，认证保持开启。配置验证、正确服务器地址、5次认证查询及实际Browser登录已通过，密码未保存。历史成功不保证将来服务不停止。

### 7.3 重建与直接导入

```powershell
cd D:\RAGQnASystem\RAGQnASystem-main
$kgPython = 'C:\Users\18270\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $kgPython .\ship_fault_kg\audit_sources.py
& $kgPython .\ship_fault_kg\build.py
& $kgPython .\ship_fault_kg\import_neo4j.py --prepare-only
```

已下载通常无需重下载。以上只准备主数据/导入包，不自动删除旧点。**新空库**可执行neo4j_import_guide.html中的语句，或运行 `& $kgPython .\ship_fault_kg\import_neo4j.py` 在终端隐藏输入密码。**已有本项目V3/V4库的受控同步**应使用下列命令，否则旧标签/旧关系会残留：

```powershell
& $kgPython .\ship_fault_kg\verify_v4.py
& $kgPython .\ship_fault_kg\sync_neo4j_v4.py --apply
& $kgPython .\ship_fault_kg\export_inventory.py
& $kgPython .\ship_fault_kg\export_graphml.py
& $kgPython .\ship_fault_kg\visualize_graph.py
```

同步脚本默认以`history/v4_1_before_source_merge_20261006/output/ship_fault_kg.sqlite`为V4.1基线，适用于本项目V4.1→V4.2或当前V4.2重复同步，发现未知ID或缺失内容会停止，不用于任意数据库的强制覆盖。如明确从已备份V3/V4.0迁移，需另指定对应`--baseline-backup`目录，不要对任意旧库强制运行。密码只在终端隐藏输入。完整标签、属性、端点和约束信息备份至`history/v4_1_before_source_merge_20261006/neo4j_snapshot.json`，既有备份不覆盖；旧代码及SQLite已另外保存。一个自动提交事务内完成迁移，然后逐一比对所有当前节点/关系及完整props_json并保存回执；事务原子性见[Neo4j Query API事务文档](https://neo4j.com/docs/query-api/current/transactions/)。若最终核验失败，不应当作完成，应检查已提交状态再定向修正。

默认HTTP `http://127.0.0.1:7474`、数据库shipfaultkg；可用--url/--database或环境变量覆盖。Query API另检查errors，不能只看HTTP状态。新空库直接导入，现有库用ID MERGE，不清空用户手工内容。

**SQLite→CSV→Neo4j不是必须。** 现为SQLite→参数化Cypher→MERGE/SET。CSV仅--export-csv可选。V1离线neo4j-admin/full import及旧py2neo是历史路线，当前不依赖它们；已有库不要反复full import或随意overwrite-destination。

### 7.4 排障与只读检查

| 现象 | 优先检查 |
| --- | --- |
| 拒绝连接 | 实例是否RUNNING、网页是否7474，不是先改密码 |
| 网页可开但连不上 | Bolt7687、服务就绪、地址是否重复、账号与正确实例 |
| Unauthorized | 账号密码；不要关闭认证或连续错误重试 |
| store_lock冲突 | 同数据目录是否有另一进程；不要删除锁文件 |
| 端口占用 | 旧Windows服务或另一实例；不要终止所有Java |
| Desktop仍显示555 | 刷新数据库统计/重连/切换库，可能是缓存；不能因此再次宽范围删除 |

旧Windows neo4j服务此前为Stopped/Disabled，本次未启动，不要让它抢默认端口。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ship_fault_kg\check_neo4j_ready.ps1
& $kgPython .\ship_fault_kg\check_neo4j_connection.py
```

前者不启动第二实例；后者提示隐藏密码，检查HTTP、Bolt握手与认证查询。握手不等于完整Bolt认证，Browser登录另核验。

## 8. 可视化颜色、中文名称和查询

所有活动点有ShipKG及具体类型标签。样式是**浏览器会话设置，不是数据库全局属性**。ShipKG保持最低优先级；FaultType已统一为Fault，因此V4只使用Fault既有25px、浅紫色#e5dfff，其余原生类型颜色和尺寸不变，不引入新的多色方案。中文名称仍使用节点caption=display_name、关系caption=name。

本机新版Browser是后匹配规则优先，因此文件中ShipKG规则放在具体类型之前，效果才是“优先级最低”；不要把文件位置最后与显示优先级最低混淆。离线HTML已撤回上一轮新增的七种颜色，保留原有样式，它与Neo4j是两个独立展示入口。

V4文件已生成：[shipkg_v4.grass](D:/RAGQnASystem/RAGQnASystem-main/ship_fault_kg/output/shipkg_v4.grass)。本轮已通过数据库API核验名称与标签，但浏览器工具受访问策略限制，未在当前Browser会话重导入样式；Desktop内嵌Query或网页版是不同会话，需要时各导入一次。

1. 运行`:style`，点击Upload GraSS styles，选文件。
2. 预览后点击**Import**，只上传不等于应用。
3. 重新查询；版本优先级不同则在Results overview的Update styling priority中让具体类型高于ShipKG。

保留ShipKG标签/唯一约束，不能为配色破坏查询。当前文件顺序针对新版Browser实测，不套用旧版第一条永远优先的经验。重生成 `& $kgPython .\ship_fault_kg\visualize_graph.py` 不会恢复旧覆盖顺序。

### 全库真实统计

```cypher
CALL () { MATCH (n) RETURN count(n) AS nodes }
CALL () { MATCH ()-[r]->() RETURN count(r) AS relationships }
CALL () { MATCH (s:Sensor) RETURN count(s) AS sensors }
CALL () { MATCH (a:ArchivedSensor) RETURN count(a) AS archived_sensors }
RETURN nodes,relationships,sensors,archived_sensors;
```

期望491、1185、15、0（本项目专用数据库没有其他用户节点时）。元数据可能仍列曾使用的旧标签名，不表示还有节点，是否残留以MATCH数量为准。

### 故障入口、机理与来源

```cypher
MATCH (f:ShipKG:Fault)-[r:IN_SYSTEM]->(s:ShipKG:System)
WHERE f.fault_level='故障类别' AND s.system_level='功能系统'
RETURN f,r,s;
```

```cypher
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE r.case_id='knowledge:liner_scuffing'
  AND type(r) IN ['CONTRIBUTED_TO','MAY_CONTRIBUTE_TO','LEADS_TO','CHECKS','ADDRESSES','INDICATES']
RETURN a,r,b;
```

拉缸局部返回9实体、7关系。溯源表：

```cypher
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE r.case_id='knowledge:liner_scuffing' AND r.knowledge_layer='reference'
RETURN a.name,r.name,b.name,r.certainty_zh,r.applicability,r.source_file,r.page,r.quote,r.source_url;
```

### 单事故和全图

```cypher
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE r.case_id='pride_can_cpp_2014' AND type(r) IN ['LEADS_TO','CONTRIBUTED_TO','CHECKS','ADDRESSES']
RETURN a,r,b;
```

```cypher
MATCH (n:ShipKG)
OPTIONAL MATCH (n)-[r]->(m:ShipKG)
RETURN n, r, m;
```


节点/关系返回可用Graph，数量/字符串用Table。全图可能受显示上限或拥挤影响，应分层演示故障入口→单机理→单事故→来源；不要把毛线团当质量证明。圆形长名/拥挤边可缩略，点击属性看全文。

离线 [graph_viewer.html](D:/RAGQnASystem/RAGQnASystem-main/ship_fault_kg/output/graph_viewer.html) 可双击，无需Neo4j/网络/密码；按机理和事故切换、看因果/诊断/组织边、点边看证据。它是SQLite快照，不冒充实时Neo4j。

## 9. 检索、LLM和开发评价

### 9.1 已实现路线

SQLite读取 → 名称/别名实体匹配 → 中文英文字符TF-IDF和术语扩展 → 上下文相关性融合、去重 → 同上下文路径、检查/措施补全 → Evidence Pack → 本机Ollama的qwen2.5:3b-instruct选证据编号 → 核对编号/类别/上下文 → 约束模板草稿。

Evidence Pack是带来源的证据包，保存事实、路径、证据编号、文件/URL/物理页/摘录、确定性和适用机型。文本检索与结构事实分层。当前**没有训练NER、神经嵌入和学习式重排**，Neo4j也不是当前脚本的在线向量后端。

```powershell
& $kgPython .\ship_fault_kg\retrieve.py --query '主机疑似拉缸，如何补充机理解释和检查建议？' --prompt
& $kgPython .\ship_fault_kg\retrieve.py --input-json .\ship_fault_kg\example_diagnosis.json --prompt
& $kgPython .\ship_fault_kg\generate_demo.py --query '主机疑似拉缸，如何补充机理解释和检查建议？' --output-name my_scuffing_demo
```

最后需Ollama运行且已有模型，无需下载更大模型。既有3B文件约1.9GB、使用较短上下文与受限输出，图谱/字符检索无需GPU；文件大小不保证运行内存要求。历史V3草稿见`history/organization_20261007/v3_artifacts/output/demo_v3_scuffing.md`及同名json。V2曾拒绝4个不合规措施编号，说明LLM选择不保证正确。

### 9.1.1 记录级Source的作用、实际检索覆盖及已执行合并

**它是什么？** 原12个Observation来自方位推进器CBM资料包中的`table3_lti_by_fault_type_anonymised.csv`，V4.2已统一为`Source {source_level:'记录级'}`。每个节点对应一行匿名监测汇总或参考条目，不是本项目接入的实时传感器数据，也不是12起已确诊事故。`build.py`的`build_azimuth_dataset()`保存发动机/设备对象、行号record、warning_hours、warning_months和reference_class，随后由`redesign.py`统一类别。不是每行都有预警时间，空值不能当零。

**两级Source有什么区别？** 资料级Source回答“哪份资料提供了证据”；记录级Source回答“这份资料中哪一条记录、记录了什么状态和建议”。同一资料可有多条记录，每条的对象、状态、预警时间、建议不一定相同。不能把它们混合成单一故障案例。

```text
Source：方位推进器匿名CBM资料包（资料级来源）
  ↑ 来源于 DOCUMENTED_BY
Source：第1条 CAT C7轴系减速器监测摘要（案例A，记录级来源）
  ├─ 呈现状态 SHOWS_CONDITION → 结构松动
  ├─ 建议采取 HAS_RECOMMENDED_ACTION → 仅振动状态监测：每125小时检测
  └─ 属性：record=1；warning_hours=525.0；reference_class=LTI_operational
```

上面是资料第1条的字段和值，不代表本船必然有525小时提前量，也不是适用于所有设备的125小时维修指令。状态和建议边共享证据`ev:596b2f398d646f0b`，定位到该CSV第1行；`DOCUMENTED_BY`也带同一行证据。全12条记录有12条状态边、12条建议边、12条来源边及7条研究者系统归属边。它们不是故障因果边。

**后续能用来做什么？** 对“轴系减速器结构松动、怎么安排状态监测”等问题，可检索相近对象和状态，再取同一记录下的建议、预警字段、原资料行号，作为LLM报告的补充参考证据。必须说明对象/设备范围、来源性质和字段缺失，不能推成当前船舶的预测结论；不同记录的状态与建议不能随意拼接。

**当前代码已经用到多少？** `retrieve.py`的主上下文索引仅收录Case及含knowledge_id的故障机理入口；诊断事实索引只收录具有case_id且属于DIAGNOSTIC_RELS的边。记录级Source不属于这两类入口，它的状态/建议边也不在诊断事实索引；`dataset_matches()`只按Run→TESTS_FAULT→Fault定位实验CSV。因此当前没有专门的监测记录召回通道，不应宣称12条监测摘要已自动进入Evidence Pack或当前24/38题检索指标。现阶段它主要保存图谱中的记录级信息并供Neo4j查询展示；本轮只改模式，不扩展检索算法。

**已经怎样合并？** 用户确认后，采用“统一类别、保留层级”方案：原30个Source设为资料级，12个Observation改为记录级Source；ID、名称、行号、状态、建议、预警字段和来源边不变。Source共42个，实体类型16→15，总491节点/1185关系不变。没有把12条记录压缩成一个资料节点，也没有把不同记录的状态与建议混接。

合并只是模式整理，不会自动改善召回。后续如接入监测记录检索，仍应按`source_level=记录级`建立独立索引，以同一记录ID返回状态、建议和资料级来源，并将这类补充证据与历史事故因果证据分区呈现。图谱中旧ID含`shipkg:observation:`是为保留稳定身份，不代表还存在Observation实体类型；残留标签应以MATCH数量判断。

### 9.2 如何接师兄的任务

拟确定输入：设备型号/构型、初步诊断文本、症状/异常特征、候选故障、置信信息。输出增强报告、引用和不确定性；评价模块反馈一致性、解释和遗漏，再补检索/修订。目前真实接口与闭环尚未联调。资料只支持参考机理时，不替前级模型强行确认本船根因。

### 9.3 已有质量检查和指标

来源定位296锚点通过属于既有来源检查；本轮V4.2回归12项通过，其中Source合并检查逐一核对12条记录ID、名称、别名、原属性和关联边，核对资料级30/记录级12以及父来源一致性。Neo4j与SQLite的491节点、1185关系ID、端点、中文名称、标签、版本、证据ID及完整props_json核验结果见当前导入回执。定位不等于专家确认机理，回归不等于现场诊断准确率。V4样式沿用原生配色，不添加新类别颜色；记录级与资料级Source使用同一Source样式。

V4事故/数据开发38题：33事故题、2数据定位题、3覆盖边界题。混合检索Recall@5=0.7374、Recall@10=0.8788、Precision@5=0.4364，案例MRR@3=1.0000，数据定位=1.0000。金标准显示名按已确认映射更新；旧Q12因现在已有参考机理，覆盖标签改为reference_knowledge，但仍不确认本船根因。只标必需事实，未标注返回项不能一概算错。相较历史V2回归，部分事实排序下降，后续应针对近义故障、事件级消歧与案例内排序优化，不能只报最好的24题结果。

V4故障开发24题（12故障名+12改写）：MRR@3=1、Recall@5=0.9107、Recall@10=1、Precision@5/@10=1。金标准使用稳定实体ID，改中文名称不会让正确事实被误判。题与建图同源且用别名，相关事实按命中单元确定，不能宣称独立测试或诊断100%。此组Precision分母为实际返回数、最多K；事故38题固定K，不能直接比较。

```powershell
& $kgPython .\ship_fault_kg\verify_v4.py
& $kgPython .\ship_fault_kg\evaluate.py
& $kgPython .\ship_fault_kg\evaluate_fault_v3.py
```

下一阶段先独立标注“问题→正确实体→相关事实→正确路径→来源”，按事故留出并加入未知/相近/多故障问题。Recall@K看漏召，Precision@K看干扰，MRR看首条相关排序；路径另评边与上下文正确性。报告另评引用、证据一致性、解释合理性、遗漏/幻觉和建议安全性，不能用检索分数代替诊断质量。

## 10. 方法对比、问题与下一步

### 常见路线的机制比较（非实测排名）

| 路线 | 常见优势 | 与本项目的区别 / 代价 |
| --- | --- | --- |
| 纯人工规则/三元组 | 专家可控、适合审核 | 本项目程序化ID和页级校验减重复劳动，仍人工慢、覆盖有限 |
| 监督式抽取 | 标注充分可批量扩展 | 当前不训练BiLSTM-CRF等；抽取正确不等于因果正确 |
| LLM自动建图 | 快速产生候选知识 | 当前先核对关键事实，减少无来源断言；后续可用LLM提候选再审 |
| 文本/向量RAG | 对文本建库直接、措辞相似召回灵活 | 本项目显式存路径/确定性/案例边界；当前字符方法弱，拟融向量 |
| 大规模社区摘要GraphRAG | 面向跨大量文档全局问题 | 本项目先局部可审计故障链，未实现社区摘要/图向量/全局总结 |

离线neo4j-admin适合首次清洗整库；LOAD CSV/Importer适合表格映射；SQLite参数化MERGE适合小库增量。所有路线都需要来源审查，未做同数据公平实验前不宣称本法一定更优。

### 主要问题

1. 缺真实低速机轴带系统、主轴联轴器断裂完整事故链和实时测点；邻近案例或厂家指导不能确认本船根因。
2. Fault仍混正常、退化、预警、保护动作，概念/实例和船型层级待规范。
3. 型号、别名、同名部件的跨来源对齐粗，共享点靠case_id隔离路径。
4. 证据等级、适用构型及专家审核状态不完整。
5. 没独立Passage/Evidence图节点、在线向量索引及完整OCR。
6. 字符检索与模板原型尚无独立生成质量和真实端到端验证。
7. 显示样式按会话保存，整图拥挤；图形展示不能替代证据核对。
8. 中文语料复用许可未逐条核明，制造商资料不宜整包公开转发。

### 两条线并行推进

| 方向 | 要什么 | 做什么 | 输出 / 验收 |
| --- | --- | --- | --- |
| 图谱修订 | 真报告、手册、型号、专家意见 | 增删改实体边、补来源/适用性/审核 | 版本图谱、差异清单、可追溯证据 |
| 检索实验 | 独立问题及正确实体/事实/路径 | 比关键词、语义、图路径、混合，融合重排 | Recall/Precision/MRR、消融、错误分析 |
| 生成评价 | 同批初步诊断和人工解释 | 比无检索/文本RAG/图谱增强 | 引用、一致性、解释、遗漏/幻觉 |
| 模块联调 | 师兄标准诊断、评价反馈 | 确定接口、构型对齐、补检索和迭代 | 端到端增强报告、代码配置/阶段报告 |

优先补真实电压/电流/频率/THD/振动/轴电流等测点、主轴断裂证据及专家标注，不以AI构造事实填来源缺口。

## 11. 版本沿革与当前维护记录

| 阶段 | 当时状态 | 当前如何看待 |
| --- | --- | --- |
| V1 | 234/325、7事故、70Sensor、171证据、488片段 | 初始主干及离线CSV历史 |
| V2 | 451/1034、19事故、70Sensor、325证据、690片段 | 扩12事故和5子系统，直接在线导入 |
| V3活动快照 | 500/1201、15Sensor、12入口、332证据、852片段 | 新104节点/253关系，移出55Sensor/86关系 |
| V3原Neo4j全库 | 555/1287，活动500/1201 | 55仍归档，Desktop显示555 |
| V3维护后（2026-10-05） | 全库500/1201、15Sensor、0归档Sensor | 真实删除55/86，外部备份；修正颜色并合并文档 |
| V4.0（2026-10-06） | 496/1197、16类实体、29种关系、Fault114 | 合并4组类型、去船名前缀、中文命名；移除Dataset4，来源重连51，证据与文本不丢失 |
| V4.1（2026-10-06） | 491/1185、Vessel22、Equipment19、Observation12 | 删除5个船型入口，12条分类转属性并保留证据；改13个设备名，Observation当时保留 |
| **V4.2当前（2026-10-06）** | **491/1185、15类实体、Source42** | Observation统一为Source；资料级30/记录级12，全部记录ID、状态/建议/来源关系保留 |

本次版本4.2属于来源实体分层整理，不虚增故障事实数量。当前核验见`output/neo4j_import_result.json`、`output/neo4j_snapshot_v4.json`、`output/build_report.json`。以下是历史维护记录，不代表当前491/1185的截图：

- `history/organization_20261007/sensor_maintenance/output/maintenance_20261005/purge_receipt.json`：历史删除及ID一致性。
- `history/organization_20261007/sensor_maintenance/output/maintenance_20261005/deleted_sensors_backup.json`：完整外部恢复资料。
- `history/organization_20261007/sensor_maintenance/output/maintenance_20261005/neo4j_native_style_restored.png`：V3原生配色恢复、Fault与FaultType合并前对比。
- `history/organization_20261007/sensor_maintenance/output/maintenance_20261005/neo4j_colors.png`：上一轮配色截图，已撤回，仅作历史记录；同目录`neo4j_full_counts.png`为删除后全库统计。
- `history/organization_20261007/connection_maintenance/output/neo4j_connection_repair_20261005/`：历史连接修正、配置备份、无密码检查结果。
- `history/docs_before_consolidation_20261005/`：原六文档；旧端口/数量/归档说明已过时。

## 12. 官方与原始资料参考

- [Neo4j Query API参数与事务](https://neo4j.com/docs/query-api/current/query/)
- [Browser样式与标签优先级](https://neo4j.com/docs/browser/operations/browser-styling/)
- [网络连接器与默认端口](https://neo4j.com/docs/operations-manual/current/configuration/connectors/)
- [Desktop实例管理](https://neo4j.com/docs/desktop/current/operations/instance-management/)
- [官方Knowledge Graph Builder](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html)
- [船机故障知识图谱论文](https://doi.org/10.3390/jmse13040693)
- [船舶电力振荡论文](https://doi.org/10.3389/fenrg.2020.529756)
- [MAN拉缸通函](https://www.man-es.com/docs/default-source/service-letters/sl2016-633.pdf)
- [HFACS-KG代码参考](https://github.com/yijie-sjtu/HFACS-KG)

完整网址/许可/文件位置以资料清单为准。当前图谱、草稿和内部自测用于研究与专业审核，有出处不等于本船根因已确认。
