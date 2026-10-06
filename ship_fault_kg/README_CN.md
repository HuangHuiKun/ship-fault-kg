# 船舶动力系统故障知识图谱：统一项目说明

更新日期：2026-10-05。知识版本：V3.0；本轮为维护修订，没有新增知识事实。

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
| Neo4j全库节点 / 关系 | **500 / 1201** | 55归档测点及86条边已实际删除，全库与活动图谱一致 |
| 实体类型 / 实际关系类型 | 20 / 32 | 允许的关系词表不等于实际出现的类型 |
| 历史事故 / 经典故障入口 | 19 / 12 | 参考机理不是新增事故 |
| 船舶记录 / 船型标签 | 17 / 10 | 8具名记录、9身份未公开事件记录，不保证17条不同实船 |
| 动力架构 / 功能子系统 | 3 / 5 | 架构和功能分类不同；子系统可交叉 |
| 核心Sensor / 归档Sensor | 15 / 0 | 原始数据的70字段未删除 |
| 诊断关系 / 因果类关系 | 244 / 133 | 检查、措施、先后等不都属于因果 |
| 来源证据 / 可检索片段 | 332 / 852 | SQLite独立表，不另算为Neo4j节点 |

852片段包括545报告页、145中文语料文章、162参考页。证据字段复制在Neo4j关系上，全文片段仍由SQLite检索。规模符合200～500实体、600～1500关系、3～5子系统的原型目标，但不能据此宣称知识完备或诊断准确。

本轮Neo4j实查：全库500节点、1201关系、15个Sensor、0个ArchivedSensor；若Desktop侧栏仍显示555，请刷新统计或断开后重连，旧结果帧也需要重新运行。

![当前数据库全库统计](output/maintenance_20261005/neo4j_full_counts.png)

上一轮按类型重新配色已按用户要求撤回，以下为最新样式：恢复Neo4j原生配色，仅降低ShipKG优先级，并略加大、加深FaultType。

![恢复原生配色后Fault与FaultType的对比](output/maintenance_20261005/neo4j_native_style_restored.png)

## 2. 资料来源和文件分工

### 2.1 为什么自建，资料怎样用

在已调研范围内找到相关论文和代码，但未找到可直接下载复用、同时满足船舶故障、因果解释、来源审计和本地检索测试要求的完整图谱，故选择自建。不是断言船舶知识图谱研究不存在，也不把论文中的结果当成本项目结果。

| 来源 | 代表资料 | 实际用途和限制 |
| --- | --- | --- |
| 实机受控实验 | Marine Engine Fault Dataset、变量字典、运行索引 | 建设备/故障标签、运行条件和测点；不从标签推断事故根因 |
| 监测汇总 | Azimuth Thruster CBM方位推进器匿名汇总 | 按行建Observation、状态与建议；未获取的原始FFT不冒充已下载 |
| 仿真/代码资料 | UCI Naval Propulsion CBM、TSRF及弱热诊断参考 | 明确simulated来源，不当成实船事故 |
| 中文船机语料 | 船用柴油机RAG语料 | 当前精选145篇作为背景检索文本，未经核对的全文不直接转因果边 |
| MAIB调查及摘要 | Wight Sky、Kommandor Susan、Windcat 8、Finlandia Seaways、Spirit of Discovery、Pride、Queen Mary 2、Stena Europe及Safety Digest | 建19起历史事故，保留报告物理页、原文、调查概率措辞 |
| 厂家资料 | MAN服务通函、STAMFORD/AvK Application Guidance Notes | 补拉缸、烧瓦、冷却、扭振、轴带对中、电蚀和绝缘等参考知识，限定机型/构型 |
| 论文/方法代码 | 船机知识图谱论文、电网振荡论文、HFACS-KG等 | 参考模式和检索/抽取思路；阅读不等于集成、训练或复现全部算法 |

故障导向扩充新增下载16份PDF，15份支撑结构化事实；AGN232只进入参考文本，不强行抽边。来源清单保存网址、本地文件、许可、SHA256和页数；正常TLS校验未关闭。下载资料不等于全部进入图谱。

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
| `output/entity_inventory_v3.md` / `graph_inventory_v3.json` | 全部500实体、1201关系、属性和证据详单 |
| `import_neo4j.py` / `output/neo4j_direct_plan.json` / `neo4j_direct_import.cypher` / `neo4j_import_guide.html` | SQLite直接生成和执行MERGE/SET；CSV非必需 |
| `visualize_graph.py` / `output/shipkg_v3.grass` / `graph_viewer.html` / `export_graphml.py` | Neo4j样式、离线图谱、GraphML |
| `queries_v3.cypher` | 图谱统计、故障/案例/来源查询 |
| `retrieve.py` / `generate_demo.py` / `example_diagnosis.json` | 轻量混合检索、标准输入和约束报告原型 |
| `evaluate.py` / `evaluate_fault_v3.py` / `verify_v2.py` / `verify_v3.py` | 开发评价和结构回归测试 |
| `purge_archived_sensors.py` / `output/maintenance_20261005/` | 本轮55测点真实删除、外部备份及恢复入口 |
| `check_neo4j_ready.ps1` / `check_neo4j_connection.py` | 只读服务/认证检查，不保存密码 |
| `history/` / `output/v1_legacy/` | 历史代码文档和旧格式，不是当前默认导入包 |

完整清单见[实体清单](D:/RAGQnASystem/RAGQnASystem-main/ship_fault_kg/output/entity_inventory_v3.md)及[结构JSON](D:/RAGQnASystem/RAGQnASystem-main/ship_fault_kg/output/graph_inventory_v3.json)。本文不粘贴500个实例，避免重复。

## 3. 构建步骤及每一步缘由

1. **限定研究任务和证据层。** 面向初步诊断增强，区分调查、实机试验、仿真、监测汇总、厂家指导和论文观察，避免同等看待来源。
2. **设计实体、关系、上下文。** 建设备/部件、原因/条件、症状/故障/后果、检查/措施及案例/来源；增加FaultType检索入口。历史case_id与knowledge:*机理单元隔离，分类不表因果。
3. **按物理页核对原文。** 逐条登记起点、关系、终点、页码、定位短语和确定性。物理页从封面计数，可能与印刷页不同。关键词缺失或页码越界时构建停止。命中定位词只证明文本存在，不能代替工程语义审核。
4. **拆成最小事实并保留措辞。** “可能”仍是可能；PRECEDED只表先后；CHECKS/ADDRESSES是检查/行动，不是已发生原因。derived_action是研究者整理建议，不冒充原文命令。
5. **接入数据与文本但不越界。** 从实验索引建Dataset/Run/负载/故障标签，从变量字典保留15测点；匿名汇总按行处理；仿真明确标注。PDF和文章片段用于召回，不自动生成未经核验因果边。
6. **稳定ID、去重与可读属性。** ID主要基于类型及规范名，边包括端点、类型、证据和上下文。重建同输入可复现，但改规范名可能产生新ID，需别名与人工对齐。显示名变化保留原ID和身份状态。
7. **校验并生成SQLite快照。** 检查端点、证据、类型、确定性和定位。四表保存知识与文本，成功后输出规模；CSV为可选审阅副本，GraphML/HTML另生成。
8. **先节点后关系，受控在线合并。** 建唯一约束，以ID MERGE、SET补属性，不清空现有库。MERGE不会自动删除旧点，过期内容另做差异审核和备份。
9. **实时核验而非打印源数量。** 查询Neo4j全库、核心测点、归档残留，并比较全部活动ID与SQLite。展示时点开边看原文和适用机型，而不是只看一张漂亮图。

共享故障或后果节点可被不同案例使用；查询路径必须约束同一case_id/context_id，不能因整图视觉连接而拼接不存在的事故链。

## 4. 实体、关系、属性及约束

### 4.1 20类实体与当前数量

共同字段：id、kind、name、aliases；SQLite props为JSON，含display_name、kind_zh、graph_version及类型字段。Neo4j同时有ShipKG与具体类型标签，保存props_json，并展开可标量化属性。

| 类型 | 数量 | 含义 | 共同显示字段外的实际属性键集合 |
| --- | ---: | --- | --- |
| Vessel | 17 | 船舶记录 | anonymous、original_name、vessel_identity_status |
| VesselType | 10 | 船型标签 | 无 |
| System | 3 | 动力架构 | 无 |
| Subsystem | 5 | 功能子系统 | classification_basis |
| Case | 19 | 历史事故 | case_id、data_origin、anonymous_vessel、original_name、vessel_identity_status |
| Equipment | 19 | 设备 | 无 |
| Component | 33 | 部件 | 无 |
| Fault | 105 | 故障/事件/状态 | semantic_class |
| FaultType | 12 | 经典故障入口 | knowledge_id、applicability、coupling_domains、data_origin |
| Cause | 10 | 原因 | 无 |
| Condition | 73 | 工况/条件 | 无 |
| Symptom | 13 | 症状 | 无 |
| Consequence | 20 | 后果 | 无 |
| Check | 33 | 检查 | 无 |
| Action | 51 | 措施 | 无 |
| Dataset | 4 | 数据集 | data_origin、instances |
| Run | 16 | 试验运行文件 | anomaly_state、columns、data_origin、data_rows、schema_type |
| Sensor | 15 | 核心测点 | category、unit、in_reference、in_scenario_files、note、selection_reason |
| Observation | 12 | 汇总观察 | data_origin、record、reference_class、warning_hours、warning_months |
| Source | 30 | 结构化事实来源 | category、license、local_item、url |

同类型不是每个实例都有全部可选键。props_json不是自动建索引的对象。Fault仍包含正常参照、预警、退化和保护动作，105个Fault不能报成105类确诊故障。

### 4.2 当前32种实际关系

| 类型 | 数量 | 意义 / 边界 |
| --- | ---: | --- |
| INVOLVES | 288 | 涉及上下文，不表因果 |
| BELONGS_TO_SUBSYSTEM | 309 | 归属子系统，研究者分类 |
| IN_SUBSYSTEM | 69 | 涉及子系统，分类 |
| ASSOCIATED_WITH | 5 | 相关，不确认根因 |
| AFFECTS_COMPONENT | 33 | 影响部件 |
| TESTS_FAULT | 15 | 测试故障标签 |
| PROMPTS | 2 | 应触发行动 |
| AT_LOAD | 16 | 负载条件 |
| LEADS_TO | 87 | 导致，需保留确定性 |
| CONTRIBUTED_TO | 15 | 促成 |
| MAY_CONTRIBUTE_TO | 17 | 可能促成 |
| ADDRESSES | 43 | 措施应对问题 |
| HAS_CHANNEL | 15 | 包含核心测点 |
| HAS_CASE | 31 | 包含案例/观察 |
| HAS_RUN | 16 | 包含运行文件 |
| HAS_EQUIPMENT | 19 | 涉及设备 |
| HAS_COMPONENT | 33 | 包含部件 |
| IN_SYSTEM | 10 | 动力架构归属 |
| PRECEDED | 6 | 先于，不等于导致 |
| HAS_RECOMMENDED_ACTION | 12 | 汇总记录建议 |
| SHOWS_CONDITION | 20 | 呈现状态标签 |
| TRIGGERS | 3 | 触发 |
| REDUCES_EFFECTIVENESS_OF | 2 | 削弱效果 |
| DOCUMENTED_BY | 40 | 记载于来源 |
| LIMITS_DETECTION_OF | 13 | 妨碍发现 |
| OF_VESSEL_TYPE | 19 | 船型分类 |
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

certainty不是概率：reported明示558条、probable很可能8、possible可能2、reported_action原文行动41、derived_action整理建议22、dataset_label实验标签24、simulated仿真8、curated_classification非因果分类488、guidance厂家指导48、research_observation论文观察2。

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

原先55点只改为ArchivedSensor/ArchivedShipKG，所以全库仍555。本轮按用户最新要求核对精确55个ID和86条直接边ID，导出完整标签/属性/端点，备份读回后在一条受保护事务中DETACH DELETE。删除后全库500/1201，Sensor15、ArchivedSensor0，全部活动ID与SQLite一致，故障链未变。

备份：`output/maintenance_20261005/deleted_sensors_backup.json`；记录：`purge_receipt.json`。Neo4j删除不能直接撤销，但可用外部备份重建；原始数据未删除。日常导入不会加回55点，因为SQLite只保留15点。

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

已下载通常无需重下载。以上只准备主数据/导入包，不自动删除旧点。已登录Browser可执行neo4j_import_guide.html中的约束、导入和核验，或运行 `& $kgPython .\ship_fault_kg\import_neo4j.py` 在终端隐藏输入密码。

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

所有活动点有ShipKG及具体类型标签。样式是**浏览器会话设置，不是数据库全局属性**。根据最新要求，已撤销上一轮人为指定的分类配色，恢复此Browser原生配色；不再将离线HTML配色套用到Neo4j。仅把ShipKG设为最低优先级，并将FaultType设为30px、深紫色#b5a6e0，与Fault的25px、浅紫色#e5dfff区分，其余原生类型颜色和尺寸不变。中文名称仍使用节点caption=display_name、关系caption=name。

本机新版Browser是后匹配规则优先，因此文件中ShipKG规则放在具体类型之前，效果才是“优先级最低”；不要把文件位置最后与显示优先级最低混淆。离线HTML已撤回上一轮新增的七种颜色，保留原有样式，它与Neo4j是两个独立展示入口。

当前127.0.0.1网页版已应用。Desktop内嵌Query或localhost是不同会话，需各导入一次：[shipkg_v3.grass](D:/RAGQnASystem/RAGQnASystem-main/ship_fault_kg/output/shipkg_v3.grass)。

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

期望500、1201、15、0。元数据可能仍列曾使用的ArchivedSensor标签名，不表示还有节点，是否残留以MATCH数量为准。

### 故障入口、机理与来源

```cypher
MATCH (f:ShipKG:FaultType)-[r:IN_SUBSYSTEM]->(s:ShipKG:Subsystem)
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
MATCH (n:ShipKG) OPTIONAL MATCH (n)-[r]->(m:ShipKG) RETURN n,r,m;
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

最后需Ollama运行且已有模型，无需下载更大模型。既有3B文件约1.9GB、使用较短上下文与受限输出，图谱/字符检索无需GPU；文件大小不保证运行内存要求。V3草稿见demo_v3_scuffing.md/json。V2曾拒绝4个不合规措施编号，说明LLM选择不保证正确。

### 9.2 如何接师兄的任务

拟确定输入：设备型号/构型、初步诊断文本、症状/异常特征、候选故障、置信信息。输出增强报告、引用和不确定性；评价模块反馈一致性、解释和遗漏，再补检索/修订。目前真实接口与闭环尚未联调。资料只支持参考机理时，不替前级模型强行确认本船根因。

### 9.3 已有质量检查和指标

来源定位296锚点通过、V2回归7项/V3专项6项通过；定位不等于专家确认机理，回归不等于现场诊断准确率。本轮删除后全部活动ID与SQLite一致；最新样式回退已在实际Browser核验，原生配色保留，FaultType为30px深紫、Fault为25px浅紫。

V2开发38题：33事故题、2数据定位题、3边界题。字符排序/混合检索Recall@5为0.6717/0.7727，Recall@10为0.9192/0.9697，Precision@5为0.4000/0.4606，案例MRR@3均1.0000。只标必需事实，未标注返回项不能一概算错。

V3开发24题（12故障名+12改写）：MRR@3=1、Recall@5=0.9107、Recall@10=1、Precision@5/@10=1。题与建图同源且用别名，相关事实按命中单元确定，不能宣称独立测试或诊断100%。V3 Precision分母为实际返回数、最多K；旧版固定K，不能直接比较。

```powershell
& $kgPython .\ship_fault_kg\verify_v2.py
& $kgPython .\ship_fault_kg\verify_v3.py
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
| **本轮维护后** | **全库500/1201、15Sensor、0归档Sensor** | 真实删除55/86，外部备份；修正颜色并合并文档 |

本次知识仍3.0，颜色/文档不虚增故障数量。当前记录：

- `output/maintenance_20261005/purge_receipt.json`：删除及ID一致性。
- `output/maintenance_20261005/deleted_sensors_backup.json`：完整外部恢复资料。
- `output/maintenance_20261005/neo4j_native_style_restored.png`：最新原生配色恢复、Fault与FaultType对比。
- `output/maintenance_20261005/neo4j_colors.png`：上一轮配色截图，已撤回，仅作历史记录；`neo4j_full_counts.png`为删除后全库统计。
- `output/neo4j_connection_repair_20261005/`：连接修正、配置备份、无密码检查结果。
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
