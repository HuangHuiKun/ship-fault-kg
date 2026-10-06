# 船舶动力系统故障知识图谱 V2：扩充、导入与检索验证

核验日期：2026-10-05。项目：`D:\RAGQnASystem\RAGQnASystem-main\ship_fault_kg`。

## 1. 本次已完成什么

V2 在 V1 基础上增加真实报告中的案例、部件、症状、原因、检查和措施，保持原有稳定 ID。已合并进入本机 Neo4j 的 **shipfaultkg**，不是只生成了待导入文件。

| 内容 | V1 | V2 | 口径说明 |
| --- | ---: | ---: | --- |
| 事故案例 | 7 | 19 | 同一事故在摘要和专门报告中重复出现，不重复建案例 |
| 船舶记录 | 5 | 17 | V2 为8条有船名记录＋9条匿名事件对应记录；无法保证匿名记录代表9条不同真实船 |
| 船型标签 | 未显式建点 | 10 | 含宽泛的货船与更细船型，不是互斥的标准船型分类体系 |
| 功能子系统 | 未显式建点 | 5 | 研究用途分类，与整船动力架构不同 |
| 动力架构类型 | 3 | 3 | 柴油机机械推进、柴油发电电力推进、柴油发电吊舱推进；匿名资料不足时不指定架构 |
| 节点 | 234 | 451 | 包括案例、数据集、测点、来源等，不能全部称为故障实体 |
| 关系 | 325 | 1034 | 包含组织、分类、数据和诊断关系，不能全部称为因果关系 |
| 诊断关系 | — | 180 | 包括因果、症状关联、检查、措施、妨碍检测等 |
| 因果类关系 | — | 100 | 包括导致、促成、风险增加、加剧及带不确定性的因果关系 |
| 独立证据记录 | 171 | 325 | 一条原文证据可以支持多条边；证据不是325起事故 |
| 可检索文本片段 | 488 | 690 | 545个非空PDF页＋145篇中文语料文章 |

满足“3～5个子系统、200～500节点、600～1500关系”的目标。规模达标不等于知识完备，更不等于具备现场预测能力。

五个子系统：燃油与进排气、润滑与轴承、冷却与海水、传动与推进、电力与控制。同一事故可以涉及多个子系统。例如喷油火灾同时涉及燃油管路、排气热表面和机舱安全。

## 2. 为什么这样扩充

原图偏重轴瓦、连杆与主机失效。若后续输入是燃油泄漏、CPP控制失灵、海水进舱或电气失电，容易只能检索到相似字词，却找不到对应机理。

本次增加燃油法兰、液压背压阀、盘车联锁、控制空气、海水阀、冷却管和谐波滤波器案例，使检索面对的是不同故障机制，而不是反复复制同类轴瓦知识来凑数量。

分类边不是因果证据：`BELONGS_TO_SUBSYSTEM`、`IN_SUBSYSTEM`、`OF_VESSEL_TYPE` 明确标记为 `curated_classification`，表示研究者组织知识的方式。分类使用名称、别名和关键词规则，尚需专家逐项复核，不能用于证明工程因果。

## 3. 原有和新增案例清单

| 案例ID | 内容 | 原始依据 |
| --- | --- | --- |
| kommandor_susan_dg1_2025 | Kommandor Susan DG1轴瓦失效、机舱火灾与失电 | MAIB 2026/10 |
| windcat8_port_engine_2017 | Windcat 8左舷主机连杆大端轴瓦失效 | MAIB 2018/1 |
| wight_sky_me_2017 | Wight Sky重装后轴承断油与失效 | MAIB 2018/14 |
| finlandia_seaways_me_2018 | Finlandia Seaways连杆小端疲劳断裂 | MAIB 2021/2 |
| wight_sky_me2_2018 | Wight Sky ME2主轴承与曲柄销断油 | MAIB 2022/4 |
| wight_sky_me4_2018 | Wight Sky ME4轴承盖错装 | MAIB 2022/4 |
| spirit_of_discovery_pods_2023 | Spirit of Discovery大风浪下吊舱推进丧失 | MAIB 2026/6 |
| sd2013_02_control_air | 匿名滚装客船控制空气不足、离合器脱开、撞泊位 | Safety Digest 2/2013案例2，PDF14–15页 |
| sd2013_03_turning_gear | 匿名专用货船盘车未脱开，联锁失效后启动损坏 | 同上案例3，PDF16–18页 |
| sd2013_05_missing_filter | 匿名货船漏装滑油滤芯，污染、抱轴、活塞卡死 | 同上案例5，PDF21–23页 |
| sd2013_12_oily_rag | 匿名双体客船含油抹布落至排气歧管起火 | 同上案例12，PDF40–42页 |
| sd2016_05_cpp_backup | 匿名滚装客船误按CPP备用按钮、失控撞泊位 | Safety Digest 1/2016案例5，PDF19–21页 |
| sd2016_08_generator_oil | 匿名滚装客船滑油泵堵头松脱、喷油起火 | 同上案例8，PDF26–28页 |
| sd2016_09_cpp_response | 匿名化学品船CPP倒车参数错误、响应迟缓、撞码头 | 同上案例9，PDF29–30页 |
| sd2016_14_sea_valve | 匿名货船检修压载泵时隔离失效、机舱进水 | 同上案例14，PDF40–42页 |
| sd2016_22_cooling_pipe | 匿名拖网渔船疑似海水冷却管失效、进水沉没 | 同上案例22，PDF59–60页 |
| pride_can_cpp_2014 | Pride of Canterbury背压阀卡滞、超压、法兰破裂火灾 | MAIB 2015/22，PDF27、29、30、35页 |
| queen_mary2_hf_2010 | Queen Mary 2滤波电容退化爆炸与失电 | MAIB 2011/28，PDF13、62、64、69、70页 |
| stena_europe_fuel_2023 | Stena Europe燃油法兰松动、喷至热表面起火 | MAIB 2024/20，PDF7、27、29、31、32页 |

Pride of Canterbury也出现在2016摘要案例12中，但只按专门报告建一个事故。匿名名称采用“船型＋摘要编号”，不是新造船名。页码均为PDF物理页，可能与报告印刷页不同。

补充下载的三份专门报告位于 `ship_fault_kg_data/02_reports`：[Queen Mary 2报告](https://assets.digital.cabinet-office.gov.uk/media/547c6fa6ed915d4c10000031/QM2Report.pdf)、[Pride of Canterbury报告](https://assets.digital.cabinet-office.gov.uk/media/563092daed915d566d000002/MAIBInvReport-22_2015.pdf)、[Stena Europe报告](https://assets.publishing.service.gov.uk/media/6756db0ba63e1781efb87793/2024-20-StenaEurope.pdf)。已更新来源清单。

## 4. 实际执行的构建步骤与缘由

1. **备份V1。** 将原输出、代码和说明存入 `history/v1_20261004`。这样扩充失败仍可检查旧版，不需要先删除现有Neo4j库。
2. **核对已有资料，补充3份MAIB报告。** 安全摘要已有案例可以利用；电气失电、燃油和CPP液压故障用专门报告补强，避免无依据地自动造知识。
3. **定义本体和关系名称。** `schema.py`统一19种实体类型、关系中文名、5子系统及确定性。英文关系类型用于Cypher，中文`name`用于展示。
4. **人工整理新增12起事故。** `expanded_cases.py`逐条记录实体、关系、PDF页、原文定位词和确定性。原7起仍在`curated_cases.py`，避免覆盖原事实。
5. **核对原文定位。** `audit_sources.py`检查232处摘要、部件和事实定位词；全部命中指定PDF页。曾发现PDF换行导致“over- pressurised”带空格，修正定位词后通过。此检查证明定位存在，不能自动证明中文解释在语义上完全正确。
6. **去重、建立稳定ID和案例边界。** 同类型同规范名使用稳定ID；边同时保留`case_id`、证据和确定性。共享“机舱火灾”节点可以被不同案例使用，但路径检索必须限定同一案例，防止拼接出不存在的事故链。
7. **补充子系统和船型组织。** 生成分类关系，并与真正诊断关系区分。匿名摘要未明确动力架构时不加`IN_SYSTEM`，防止把“船上有发电机”误当成“整船电力推进”。
8. **补充可读属性。** 所有节点添加`display_name`、`kind_zh`；所有边添加中文`name`、`is_causal`和版本号。`Fault`另加`semantic_class`，区分正常参考、警告、退化和故障事件；85个Fault记录并不等于85种真实事故故障。
9. **构建SQLite和文本层。** 原PDF按非空页建检索片段，中文语料仅作辅助文本；未把其全文自动变成确定因果关系。SQLite临时文件成功构建后再替换主文件，降低半成品覆盖风险。
10. **直接导入Neo4j。** 读取SQLite，先节点后关系，按稳定ID用`MERGE`合并，`SET`补属性。没有清空数据库、改密码或使用CSV中转。
11. **实时核验。** Neo4j返回新增217节点、709关系；查询确认总量451/1034，451个节点和1034条边均具备名称属性，100条边为因果类。创建`ShipKG.id`唯一约束，避免同一ID重复节点。
12. **验证检索及LLM流程。** 扩充开发问题集，增加口语化问法、证据不足问题和字符检索基线对比，再用已安装的Qwen 3B做一份新案例诊断草稿。

## 5. 当前实体构成

| 英文类型 | 中文含义 | 数量 |
| --- | --- | ---: |
| Vessel / VesselType | 船舶记录 / 船型标签 | 17 / 10 |
| System / Subsystem | 整船动力架构 / 功能子系统 | 3 / 5 |
| Case | 事故案例 | 19 |
| Equipment / Component | 设备 / 部件 | 19 / 33 |
| Fault / Cause | 故障、状态事件 / 原因 | 85 / 7 |
| Condition / Symptom | 工况条件 / 症状 | 50 / 10 |
| Consequence | 后果 | 18 |
| Check / Action | 检查 / 措施 | 19 / 39 |
| Dataset / Run | 数据集 / 试验运行文件 | 4 / 16 |
| Sensor / Observation | 测点 / 汇总观察 | 70 / 12 |
| Source | 来源 | 15 |

完整实体、边、属性和证据都在SQLite四张表中；`output/graph_inventory_v2.json`与`output/entity_inventory_v2.md`便于逐项审阅。

## 6. 关系、因果和来源如何区分

诊断边示例：`LEADS_TO`导致、`CONTRIBUTED_TO`促成、`MAY_CONTRIBUTE_TO`可能促成、`TRIGGERS`触发、`CHECKS`检查、`ADDRESSES`应对、`LIMITS_DETECTION_OF`妨碍发现。组织边示例：`HAS_CASE`、`INVOLVES`、`HAS_COMPONENT`、`DOCUMENTED_BY`。子系统和船型是分类边。实际已出现的31种关系及数量见`build_report.json`。

典型链：

- Pride：背压阀磨损卡滞 → CPP超压 → 回油法兰破裂 → 液压油喷向热排气管 → 机舱火灾。
- Stena：燃油法兰螺钉松动 → 压力燃油泄漏 → 燃油喷向裸露高温歧管 → 机舱火灾 → 主机数周不能工作。
- 匿名滤芯事故：在线滤芯缺失 → 滑油污染 → 主轴承咬死与瓦片转位 → 油道堵塞/断油 → 活塞卡死。
- Queen Mary 2：电容退化 → 内部电弧与介质汽化 → 内压升高、壳体破裂 → 滤波器爆炸；爆炸与电网不稳定、失电之间保留“很可能”，不能改写为已完全证实的精确电网机理。

每条边都能追溯`evidence_id`、文件、URL、PDF页、定位和摘录；确定性保留原报告限制。217条证据来自报告，101条来自数据集元数据，7条来自开源代码/说明。不能把仿真状态视作真实事故，也未把70个测点凭空连接成故障原因。

## 7. 可视化的改进与使用

Neo4j已应用名称样式：节点显示`display_name`，边显示`name`；故障红、后果橙、条件黄、检查蓝、措施绿。`ShipKG`是通用标签，应放在具体类型之后，避免所有节点被同一颜色覆盖。样式是浏览器会话设置，您在Neo4j Desktop的另一浏览器会话中需要重新导入，并非数据库全局设置。

在Neo4j运行`:style`，点击Upload，选择`output/shipkg_v2.grass`，然后在预览框点击**Import**。只上传文件还未完成应用。新旧版本识别的尺寸字段不同，样式同时提供`diameter/size`和`shaft-width/width`；实际预览提示为准。有关自定义名称与优先级见[Neo4j官方样式说明](https://neo4j.com/docs/browser/operations/browser-styling/)。

节点过大会缩短边的可用空间，边名可能被压缩；当前演示把Fault和Consequence设为42px，便于观察“导致”。整图451节点一起展示仍会拥挤，建议按一个案例或一条路径查看，用`queries_v2.cypher`逐段查询。名称过长时Neo4j会省略部分文字，点击节点查看完整属性。

另提供`output/graph_viewer.html`，可直接双击，无需Neo4j、网络或密码。按案例切换，可选诊断/因果/全部组织关系，每条边显示中文名称；点击实体看属性、点击边看证据。可选层级布局或三列紧凑阅读布局。图很长时使用横向滚动，避免强行缩小到无法阅读。它是SQLite快照，不冒充Neo4j实时页面。19起事故已逐一切换核验，诊断边数量合计180，每条边都有中文标签；关系标签点击后能显示原文、文件和PDF页。验收记录见`output/viewer_verification_v2.json`。

![Neo4j实时规模核验](output/neo4j_v2_counts.jpg)

![Neo4j燃油故障链](output/neo4j_v2_graph.jpg)

![离线图谱关系点击后的证据显示](output/viewer_v2_evidence.jpg)

## 8. CSV是否必需，如何再次导入

**不必需。** CSV只是文件交换格式，Neo4j也可以接受参数化Cypher查询。当前默认路线是“SQLite读取 → 分组参数 → MERGE/SET → 核验”，省去CSV生成、列头转换和服务器import目录管理。[Neo4j Query API](https://neo4j.com/docs/query-api/current/query/)支持提交查询和参数。

```powershell
cd D:\RAGQnASystem\RAGQnASystem-main
$kgPython = 'C:\Users\18270\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $kgPython .\ship_fault_kg\audit_sources.py
& $kgPython .\ship_fault_kg\build.py
& $kgPython .\ship_fault_kg\import_neo4j.py
```

最后一步在交互终端安全输入当前密码，不显示、不写入文件；连接默认HTTP7475、数据库shipfaultkg。脚本使用官方HTTP Query API，不再依赖旧py2neo。HTTP返回成功状态仍需检查`errors`，脚本已处理该情况。本次实际执行的是已登录Browser中的同样MERGE语句，未读取或保存您的密码；参数化HTTP写入路径本次没有使用真实凭据单独实测。

若不想在终端输入密码，可运行`import_neo4j.py --prepare-only`生成`output/neo4j_direct_import.cypher`和独立复制页面`neo4j_import_guide.html`。在已登录Browser选好shipfaultkg：先运行唯一约束，再复制整段导入语句并Run，最后执行核验语句。当前新版Browser的`:play`对自定义向导解析不兼容，因此使用独立复制页面，不依赖`:play`。

`build.py --export-csv`仅在需要审阅CSV时使用。数百万节点的全量首次建库可考虑离线`neo4j-admin import`；现有库中的千条关系升级更适合在线合并。无需每次重新导入：日常只启动Neo4j实例并连接数据库即可。查看本地HTML不需要启动任何服务。

## 9. 检索实验与LLM增强结果

当前混合检索是“名称/别名实体匹配＋中文英文字符TF-IDF＋术语扩展＋案例相关性融合＋同一案例因果路径补全＋检查/措施补充＋ID去重”。这属于可运行轻量基线，**不是**已经完成神经向量语义检索。SQLite用于本地检索，Neo4j用于在线图查询和展示；两者来自同一份构建结果。

38题包括33道事故题、2道数据文件定位题和3道覆盖边界题。新增事故题的必需事实从人工整理事实中选取；其余相关事实未完整标注，Precision不能解释为“剩余全部错误”。

| 开发集指标 | 字符事实排序基线 | 图谱混合检索 |
| --- | ---: | ---: |
| 案例MRR@3 | 1.0000 | 1.0000 |
| 必需事实Recall@5 | 0.6717 | 0.7727 |
| 必需事实Recall@10 | 0.9192 | 0.9697 |
| 对已标注必需事实Precision@5 | 0.4000 | 0.4606 |

这说明路径补全和检查/措施补充在这套开发题上有帮助，不能声称对未知船舶也达到相同指标。两组问题和标签相同，未开展独立专家盲评、留出事故泛化、显著性检验或生成质量综合评价。

本机已用`qwen2.5:3b-instruct`对Pride案例进行实际调用：模型选择证据编号，程序校验关系类别及案例一致性，再从已核对事实生成带引用的草稿。模型误把4个不合规编号放入运维措施，程序已拒绝；原输出与拒绝记录保留在`demo_v2_cpp.json`。最终正文见`demo_v2_cpp.md`。这是“LLM选择＋约束模板生成”，不是自由生成式诊断已完全成熟。

硬件上继续使用已有1.9GB的3B模型、2048上下文和低生成上限，没有下载更大模型，也没有训练参数。当前图谱规模无需GPU。7项自动回归测试通过：目标规模、端点/证据、V1保留、直接导入计划、GraphML一致性、案例与路径边界、无证据问题、LLM编号校验（部分合并为同一测试）。

```powershell
& $kgPython .\ship_fault_kg\evaluate.py
& $kgPython .\ship_fault_kg\evaluate.py --strategy lexical
& $kgPython .\ship_fault_kg\verify_v2.py
& $kgPython .\ship_fault_kg\retrieve.py --query 'CPP背压阀卡滞后超压和喷油火灾，原因与检查建议？' --prompt
```

## 10. 当前限制与下一步

1. 缺少低速机轴带发电、电网耦合振荡、联轴器断裂等项目核心系统的直接案例。Queen Mary 2只是邻近电气案例，不能作为轴带故障机理已解决的证明。
2. MAIB资料为主，案例选择存在偏倚；中文转述、本体粒度和关键词分类仍需船机专家复核。定位词命中不能代替语义审核。
3. 共享规范名节点有利于检索，但没有完整区分“故障概念”与“某船某次故障实例”。目前必须依靠边的case_id隔离路径。
4. 部件多为案例限定命名，跨船同义词与部件层级还需统一；船型标签的层级和互斥性待规范。
5. PDF按页切片偏长，字符TF-IDF难处理真正的同义语义推理。后续可引入小型中文/多语嵌入模型、章节级切片和独立重排模型，先与现有基线公平比较。
6. 目前输入仍是文本化线索，没有实时测点时序、阈值规则、真实前端诊断模型接口，不能用于自动控制或无人审核的维修决策。
7. 标签不完整，后续需按“问题—实体—相关事实—正确路径—可引用来源”标注专家测试集，按事故留出，不把建库用例当泛化结果。
8. 中文语料再发布许可不明确；当前仅供内部研究检索，不应把整个语料包公开上传。生成报告须区分历史事故与本船待验证假设。

本次交付是**可扩充的图谱、建库与检索代码、质量检查和增强报告原型**，不是训练完成的新诊断大模型。
