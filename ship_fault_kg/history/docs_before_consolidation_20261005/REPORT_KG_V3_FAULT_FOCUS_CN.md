# 船舶动力系统故障知识图谱 V3：故障导向优化与可恢复归档

更新日期：2026-10-05。目标是支持“文本化诊断结果 → 知识检索 → 解释、检查与运维建议 → 来源证据”的研究原型，不是训练新的故障诊断模型，也不是生产船舶自动控制系统。

## 1. 本次改了什么

| 指标 | V2 | V3活动图谱 |
| --- | ---: | ---: |
| 节点 | 451 | 500 |
| 关系 | 1034 | 1201 |
| 历史事故案例 Case | 19 | 19 |
| 经典故障参考入口 FaultType | 0 | 12 |
| 功能子系统 Subsystem | 5 | 5 |
| 活动 Sensor | 70 | 15 |
| 来源证据记录 | 325 | 332 |
| 可检索文本片段 | 690 | 852 |

新增104节点、253关系；55个非核心测点及86条直接关系移出活动图谱。这是净增量与归档的合成结果，并非只增加49个实体。Neo4j中的55个测点仍在，其原属性及关系保留；SQLite当前活动快照不含它们，完整旧版已备份。

“332条证据”与“1201条关系”不相等：同一来源页段可支持多条关系；分类、归属等组织关系也计入关系总数。新增64条诊断事实，连同旧事实共244条诊断关系；并非1201条都是因果断言。105个Fault节点包括具体失效、状态和保护事件，不能报成105类经过独立验证的故障。

## 2. 为什么改成以故障为入口

原图谱主要按事故、船舶、部件组织。输入“疑似拉缸”时，未必能命中某条船的事故名称，导致难以直接找到机理、检查和参考措施。

V3增加FaultType作为面向问题的检索入口，但不废弃原19起事故：

```text
诊断文本中的故障名/别名
  → FaultType故障知识入口
  → 原因、条件、具体故障、症状、后果、检查、措施
  → 关系上的来源文件、PDF物理页、原文定位、确定性、适用机型
  → Evidence Pack
  → LLM选择证据 + 程序核查 + 约束报告

具体历史事故 Case：单独保留自己的事实与因果链，不与一般机理跨案例拼接。
```

这允许“故障检索”和“历史案例检索”并存。FaultType不是新编造的事故；INSTANCE_OF仅表示术语分类，不证明所有同类故障具有相同根因。

## 3. 新增12个故障参考入口及因果知识

下表是摘要，逐条事实、原文定位和限定条件见[fault_profiles.py](fault_profiles.py)及[实体与关系清单](output/entity_inventory_v3.md)。箭头中的“可能”不能在报告中删掉。

| 故障入口 | 代表性路径/内容 | 主要证据与边界 |
| --- | --- | --- |
| 拉缸 | 表面抛光/涂抹 → 油膜难以维持 → 可能缸套黏着拉伤 → 表面硬化；缸况检查、泄放油铁含量与磨损 | MAN SL2016-633、SL2019-685、SL2023-737；主要为MAN B&W两冲程机，不将所有活塞咬死视为已证实拉缸 |
| 烧瓦与轴承咬死 | 异物经滑油进入主轴承 → 咬死；未响应磨损报警加重损伤；曲轴/机座维修、BWM核验 | MAN SL2013-569；烧瓦为工程检索统称，不把所有轴瓦疲劳或转位直接确认成烧瓦 |
| 冷却水通道堵塞与热过载 | 水质/处理不当 → 结垢堵塞 → 换热下降 → 可能热过载 → 可能阀座开裂泄漏 | MAN SL2016-623；四冲程闭式淡水冷却，水质与添加剂按具体机型 |
| 冷却回路汽蚀 | 扫气冷却器流量低 → 可能局部沸腾 → 可能冷却水管路汽蚀；扫气温度升高与磨损 | MAN辅助系统效率资料；不是所有冷却泵汽蚀的统一证明 |
| 扭振减振器失效 | 润滑不足/污染、水分及超速等 → 减振器失效风险；异常噪声、振动变化与检查 | MAN SL2017-654；维护周期不可推广到通函未列机型 |
| 轴带发电机对中异常与振动损伤 | 齿轮箱热膨胀改变对中；风浪船体挠曲 → 对中变化 → 可能振动损伤 | STAMFORD AGN039；侧重齿轮传动构型，不概括所有同轴无轴承方案 |
| 发电机轴承机械磨损 | 缺脂、对中异常、轴向振动微动磨损等 → 滚动轴承失效 | STAMFORD AGN076；区别于主机滑动轴瓦烧瓦 |
| 电机与发电机轴承电蚀 | 不对称磁场 → 轴电压/闭合轴电流路径 → 轴承电蚀 | STAMFORD AGN033；接地刷、绝缘轴承按制造商与机型，不认定所有机型均需绝缘轴承 |
| 发电机绕组绝缘劣化 | 潮湿/污染 → 绝缘电阻下降；故障电流热应力与清除时间 → 绝缘损伤风险 | STAMFORD AGN040、AGN035；隔离后由合格人员按本机手册检测IR/PI，不给通用操作阈值 |
| 联轴器故障 | 紧定螺钉缺少锁固 → CPP执行器联轴器松动 → 传动失败 → 螺距控制丧失 | MAIB Hebrides 2017/20；是执行器小联轴器，不是主轴联轴器断裂事故 |
| 轴系扭振与联轴器过载风险 | 燃烧脉动 → 扭振共振风险 → 轴系/传动链疲劳磨损风险；短路/不同步冲击转矩 | STAMFORD AGN235、AGN039；需TVA及试验验证，未建立大型船主轴联轴器断裂的已证实事故链 |
| 船舶电网耦合振荡 | 原动机转矩/负荷波动与控制参数 → 可能电压频率振荡；轴带化学品船实测控制相关振荡 | Frontiers 2021，DOI 10.3389/fenrg.2020.529756；三类船实测，不是三起新增事故；部分振荡未超限 |

覆盖原5个功能子系统：燃油与进排气、润滑与轴承、冷却与海水、传动与推进、电力与控制。热—机—电是耦合域属性，不是额外虚构的设备层。

## 4. 新下载的资料如何转为图谱

### 第一步：寻找可追溯的一手资料

通过MAN官方服务通函、STAMFORD/AvK官方Application Guidance Notes、MAIB调查报告及原始研究论文补充资料，而不是把网页摘要或AI生成机制当作事实。新下载16份PDF，其中15份用于结构化事实；AGN232只进入参考文本片段，未强行抽取无明确支持的关系。

文件在`ship_fault_kg_data/02_reports`；下载程序为[download_fault_sources.py](download_fault_sources.py)，元数据为`ship_fault_kg_data/05_metadata/source_manifest_v3.csv`。原资料包及原清单未删除。下载使用正常TLS校验，记录网址、文件大小、SHA256及页数，见[新资料页级索引](output/new_source_pages_v3.json)。

### 第二步：按PDF物理页阅读和提取

提取页文本，并检查关键页的真实版面。物理页指阅读器从封面起计数的第几页，可能不同于印刷页码。MAN效率资料存在一张PDF页放两张印刷页的情况，引用统一使用物理页避免查错。

将机理拆成最小可审查事实，例如“低水流量可能造成局部沸腾”，不直接扩写成“冷却泵已经损坏”。保留精确英文定位词、文件、页号、来源URL。`derived_action`表示依据来源整理的建议，不冒充报告原文直接命令。

### 第三步：构建带来源的故障知识单元

[fault_profiles.py](fault_profiles.py)中每个单元指定故障名、别名、所属子系统、耦合域、适用边界及事实。事实连接Cause/Condition/Fault/Symptom/Consequence/Check/Action等实体。

关系保存`case_id/context_id`、`knowledge_layer`、`data_origin`、`applicability`、`coupling_domains`、`certainty`、`evidence_id`、`source_file`、`source_url`、`page`、`locator`及原文片段。`knowledge:*`是参考知识单元，历史事故使用原案例ID。

### 第四步：稳定ID、分类、去重与完整性检查

实体按类型和名称产生稳定ID，原实体ID不因显示名改动而变化。检查关系两端实体是否存在、来源是否可定位；相同事实融合时保留上下文，不把“同名故障”自动合并成同一事故。

先整理原事故子系统分类，再加入新知识并分类，防止新增关系排序改变旧分类证据ID。差异核对证明：移出活动图谱的旧关系都直接连接55个非核心Sensor，没有意外移除旧事故链。

### 第五步：生成活动主数据与检索副本

[build.py](build.py)输出SQLite四表：`nodes`实体、`edges`关系、`evidence`来源证据、`passages`文本片段。文本片段共852条，不将整份PDF或所有时序样本膨胀成图节点。

SQLite为可重建、可审计的活动主数据；Neo4j为相同图结构的在线查询/可视化副本。当前检索仍从SQLite读取结构化事实和文本，而非已全部改成Neo4j在线向量检索。

### 第六步：直接增量导入Neo4j

不需要SQLite→CSV→Neo4j中转。`import_neo4j.py`按节点类型和关系类型形成58个批次，使用稳定ID的MERGE及SET。已登录Browser可执行一次事务导入脚本；命令行可通过HTTP Query API导入，密码只在本地交互输入。

先建立`ShipKG.id`唯一约束；V2升级先归档旧测点，再导入。MERGE不会自动移除旧数据，因此只导入新快照不等于完成传感器筛选。最后必须实时统计数据库，而不是把导入脚本末尾的“源文件规模”当作数据库核验。

本机`shipfaultkg`已完成导入并实时核验：500活动节点、1201活动关系、15活动Sensor、12FaultType、19Case；归档55节点和86关系；显示名“匿名”前缀剩余0。实际结果记录见[导入核验记录](output/neo4j_import_result.json)。

![Neo4j实时活动图谱核验](output/neo4j_v3_counts.jpg)

![Neo4j可恢复归档核验](output/neo4j_v3_archive.jpg)

## 5. 55个非核心测点如何隐藏、如何恢复

本次按用户要求采用可恢复归档，不执行DETACH DELETE。

归档只针对[差异清单](output/revision_changes_v3.json)中55个精确ID，将`ShipKG:Sensor`标签改为`ArchivedShipKG:ArchivedSensor`，保留属性、原始关系及归档原因。活动查询需使用`ShipKG`标签；不加标签的`MATCH (n)`仍可能看见归档节点。

- [预览](output/neo4j_sensor_preview_v3.cypher)：确认精确目标。
- [归档脚本](output/neo4j_sensor_archive_v3.cypher)：已用于V2升级；重复执行不会新增删除。
- [恢复脚本](output/neo4j_sensor_unarchive_v3.cypher)：复制到同一数据库运行，即恢复原标签和原关系。
- [归档/恢复操作页面](output/sensor_cleanup_guide_v3.html)：无永久删除步骤。

旧的永久清理脚本入口已禁用为注释。原始时序数据所有字段仍保留；旧完整图谱备份位于`history/v2_before_fault_focus_20261005`。恢复后活动规模会增至555节点、1287关系、70Sensor；V3 SQLite快照不会随之自动改变。

保留的15个测点：发动机转速、1缸最高缸压、增压空气压力、燃油流量、1缸排气温度、冷却水进口温度、冷却水出口温度Ⅰ、滑油进口温度、滑油出口温度、滑油循环泵压力原始电压、淡水冷却压力原始电压、主机冷却水流量、增压空气冷却器出口空气温度、轴转矩、轴功率。

选择理由：减少重复缸/重复出口与派生效率项，保留燃烧、润滑、冷却及传动的关键观察。**两个压力字段原单位为V，未经标定不能当bar/Pa。原70个字段没有实际电网测点，所选15个并不覆盖完整电域监测。** 电压、电流、频率、THD、绕组温度、轴承振动、轴电流等须后续拿到真实数据再接入，不伪造测点节点。

## 6. 去掉“匿名”后仍保留真实身份边界

9个Vessel和9个Case的显示名前缀已去除，VesselType显示名检查也无此前缀。保留原ID、`original_name`、`anonymous/anonymous_vessel`及`vessel_identity_status`。

例如“滚装客船（SD2016-05）”是来源案例关联船舶记录，不是真实船名。17个Vessel包含8个具名记录和9个未公开身份记录，不能确认它们对应17条互不相同的实船。

## 7. 检索、增强生成与已完成的验证

当前方法：故障别名/实体匹配 + 中文字符TF-IDF + 术语扩展 + 上下文排序 + 图关系/路径补全。命中明确故障入口时，Evidence Pack限制在该参考知识单元内；历史案例另列，禁止随意跨来源拼接因果链。尚未部署神经语义向量模型和学习式重排序器。

已检查296个来源定位锚点，无定位错误；V2回归7项、V3专项6项均通过。定位正确并不等于所有机理已通过船舶专家审核。

24道开发问题覆盖12个名称和12个改写：MRR@3=1.000，Recall@5=0.9107，Recall@10=1.000，Precision@5/@10=1.000。结果见[开发检索评价](output/fault_retrieval_evaluation_v3.json)。

这些问题来自同一整理资料，且已使用故障别名；相关事实标注按已命中的知识单元确定。Precision分母是实际返回条数（最多K），不能直接与旧评价的固定K分母比较。**这些数值只证明原型功能通过开发自测，不能宣称独立测试达到100%、诊断准确率100%或已经泛化到真实船舶。** 下一阶段需要专家标注、未知故障、近似干扰问题、多故障组合与独立船舶报告。

本机已有`qwen2.5:3b-instruct`通过Ollama完成拉缸示例：检索7条事实，LLM选择因果解释、检查、措施的证据编号，程序校验来源与上下文后生成[带引用诊断草稿](output/demo_v3_scuffing.md)。这是低资源验证流程，不是模型训练；报告正文由证据约束模板生成，不是未经核验的自由诊断。

## 8. 在Neo4j中查看与溯源

连接`http://localhost:7475/browser/`，数据库选择`shipfaultkg`。逐段运行[queries_v3.cypher](queries_v3.cypher)。返回节点和关系才能选择Graph；仅返回数量或字符串显示Table。

故障总览：

```cypher
MATCH (f:ShipKG:FaultType)-[r:IN_SUBSYSTEM]->(s:ShipKG:Subsystem)
RETURN f,r,s;
```

拉缸机理/检查/措施：

```cypher
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE r.case_id='knowledge:liner_scuffing'
  AND type(r) IN ['CONTRIBUTED_TO','MAY_CONTRIBUTE_TO','LEADS_TO',
                 'CHECKS','ADDRESSES','INDICATES']
RETURN a,r,b;
```

溯源表：

```cypher
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE r.case_id='knowledge:liner_scuffing' AND r.knowledge_layer='reference'
RETURN a.name,r.name,b.name,r.certainty_zh,r.applicability,
       r.source_file,r.page,r.quote,r.source_url;
```

节点显示`display_name`，关系显示`name`。在Browser执行`:style`，上传[shipkg_v3.grass](output/shipkg_v3.grass)后点击Import。若同节点多标签导致颜色覆盖，调整标签样式优先级；中文名称和来源不受影响。避免一次画全部1201条边造成“毛线团”，优先“故障入口总览 → 单故障机理 → 单事故 → 来源表”逐层展示。

[离线交互可视化](output/graph_viewer.html)无需Neo4j：分别选择“机理｜”与“事故｜”，可看因果/诊断关系及点击证据。此页面展示活动快照，不包含归档55个测点。

本机Browser已导入V3样式，并将通用ShipKG标签置于样式优先级末尾，避免覆盖具体实体类型的颜色。已验证拉缸Graph视图及12个参考知识入口的离线视图，关系点击能显示来源、物理页与适用范围。长名称在Neo4j圆形节点中可能缩略；点击属性可查看全名，离线矩形图更适合完整中文阅读。

![Neo4j拉缸知识链](output/neo4j_v3_scuffing.jpg)

## 9. 重建、归档与导入的命令

```powershell
cd D:\RAGQnASystem\RAGQnASystem-main
$kgPython = 'C:\Users\18270\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $kgPython .\ship_fault_kg\download_fault_sources.py
& $kgPython .\ship_fault_kg\audit_sources.py
& $kgPython .\ship_fault_kg\build.py
& $kgPython .\ship_fault_kg\revision_v3.py
& $kgPython .\ship_fault_kg\import_neo4j.py --prepare-only
& $kgPython .\ship_fault_kg\visualize_graph.py
& $kgPython .\ship_fault_kg\export_graphml.py
& $kgPython .\ship_fault_kg\export_inventory.py
& $kgPython .\ship_fault_kg\verify_v2.py
& $kgPython .\ship_fault_kg\verify_v3.py
& $kgPython .\ship_fault_kg\evaluate_fault_v3.py
```

已下载资料通常无需重复下载。上述命令准备活动快照与导入包，不会自行归档Neo4j节点。在V2库执行精确归档后，通过已登录Browser导入向导；或本地交互运行`import_neo4j.py`。全新空库直接导入，无需执行55测点归档。不得使用旧CSV/旧离线导入包覆盖新版。

## 10. 优点、局限及后续方向

优点：与纯文本RAG相比，显式保留故障—原因—检查—措施关系和上下文；与LLM全自动抽取相比，页级可核查、确定性和机型边界明确；与为扩规模而加无证据边相比，更适合做可解释与可溯源研究。

代价：人工整理慢，覆盖仍有限；字符TF-IDF对隐含语义与长报告不够稳健；关系计数包括大量组织关系；机理的适用性尚需船舶专家审核。权威资料也不能替代本船实时证据，历史通函不是当前机型统一运维指令。

优先下一步：①真实报告和设备构型对齐；②补实际电域/振动测点；③补大型船主轴联轴器断裂、低速主机轴带系统的真实事故证据；④引入本地嵌入模型与重排序并比较消融；⑤独立专家标注实体、事实、正确因果路径及无证据问题；⑥评价报告证据一致性、因果解释合理性、遗漏与不确定性，而不只看Recall/Precision；⑦上线版本管理和审核状态。

下载资料受各自许可约束：制造商文档用于本地内部研究，勿整包公开转发；论文与MAIB报告按对应许可及第三方内容条款使用。PDF阅读与关键页版面核对用于加强来源审查，没有用生成式文字替代原始证据。
