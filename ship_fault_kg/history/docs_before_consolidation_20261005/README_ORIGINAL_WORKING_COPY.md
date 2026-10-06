# 船舶动力系统故障知识图谱 V3（故障导向）

当前活动图谱已更新本机Neo4j的 **shipfaultkg**：500节点、1201关系、19起历史事故、12个经典故障参考入口、15个核心Sensor、332证据、852文本片段，覆盖5个功能子系统。55个非核心Sensor及其86条关系在Neo4j中可恢复归档，没有永久删除。详细变更、资料、故障链、验证和恢复方法见[V3说明](REPORT_KG_V3_FAULT_FOCUS_CN.md)。V2备份在`history/v2_before_fault_focus_20261005`；[V2报告](REPORT_KG_V2_UPGRADE_CN.md)是历史版本，不代表当前规模。

## 常用入口

- [离线可视化](output/graph_viewer.html)：双击HTML即可使用；按故障机理/历史事故切换，点击属性和证据。
- [Neo4j查询示例](queries_v3.cypher)：选择shipfaultkg，逐段运行。
- [拉缸增强诊断草稿](output/demo_v3_scuffing.md)：本机Qwen 3B选择证据，程序检查后生成。
- [规模及校验](output/build_report.json)、[V3开发检索评价](output/fault_retrieval_evaluation_v3.json)。旧retrieval_evaluation文件为V2开发结果，不是V3独立测试。
- [实体清单](output/entity_inventory_v3.md)、[完整结构与证据JSON](output/graph_inventory_v3.json)。
- [55测点归档/恢复](output/sensor_cleanup_guide_v3.html)：只改活动标签，保留节点及原关系。

## 从资料到图谱的流程

MAIB报告/厂家通函/研究论文/实验数据 → 页级事实审核 → 稳定ID及历史事故/参考机理隔离 → 故障入口和子系统分类 → SQLite活动主数据 → 实体/文本/因果路径检索 → Evidence Pack → LLM与程序约束输出。

SQLite → Neo4j使用直接MERGE/SET，不需要CSV中转。Neo4j是相同结构化知识的在线查询和可视化副本，文本片段仍由SQLite检索；没有把整份PDF、时序样本全部变成图节点。

## 主要文件

| 文件 | 用途 |
| --- | --- |
| curated_cases.py / expanded_cases.py | 原7起／新增12起事故的人工整理事实 |
| fault_profiles.py / download_fault_sources.py | 12个经典故障参考单元／16份新一手资料下载 |
| schema.py | 中文显示名、实体类型、关系和5子系统分类 |
| audit_sources.py / build.py | 核对PDF定位词／验证端点证据并构建SQLite |
| output/ship_fault_kg.sqlite | nodes、edges、evidence、passages四张表，当前主数据 |
| import_neo4j.py | 标准库HTTP Query API直接入库；或生成Browser用Cypher |
| output/shipkg_v3.grass | 节点名和关系名的Neo4j样式；在`:style`上传后点Import |
| visualize_graph.py / export_graphml.py | 生成无需联网的HTML和GraphML |
| retrieve.py | 别名实体匹配＋字符TF-IDF＋术语扩展＋案例内路径补全 |
| evaluate.py / eval_cases_v2.py | 38道开发问题及基线对照，不是独立专家测试集 |
| verify_v2.py / verify_v3.py | 7项旧案例回归／6项V3专项测试 |
| evaluate_fault_v3.py / revision_v3.py | 24道故障入口开发自测／精确变更及可恢复归档脚本 |
| generate_demo.py | 现有本机3B模型选择证据，再核查和生成可引用草稿 |
| output/v1_legacy/ | 旧CSV、离线管理员导入包和旧演示；不能代表V2现状 |

## 重建与导入

日常查看无需重新建库，只启动Neo4j Desktop中的ShipFaultKG实例，连接数据库。HTML可离线直接打开。

```powershell
cd D:\RAGQnASystem\RAGQnASystem-main
$kgPython = 'C:\Users\18270\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $kgPython .\ship_fault_kg\audit_sources.py
& $kgPython .\ship_fault_kg\build.py
& $kgPython .\ship_fault_kg\revision_v3.py
& $kgPython .\ship_fault_kg\import_neo4j.py --prepare-only
& $kgPython .\ship_fault_kg\visualize_graph.py
& $kgPython .\ship_fault_kg\export_graphml.py
& $kgPython .\ship_fault_kg\export_inventory.py
& $kgPython .\ship_fault_kg\evaluate_fault_v3.py
& $kgPython .\ship_fault_kg\verify_v2.py
& $kgPython .\ship_fault_kg\verify_v3.py
```

构建与PDF审核需要pypdf；其余脚本仅使用Python标准库。导入默认HTTP7475、数据库shipfaultkg，交互终端输入当前密码，不保存。若改了连接端口，使用`--url`与`--database`。

上述命令只准备导入。已登录Browser通过`output/neo4j_import_guide.html`执行约束、导入、实时统计。V2升级先执行可恢复归档55个目标；新空库不需要。MERGE不会自动隐藏旧Sensor。也可在本地交互终端运行`import_neo4j.py`安全输入密码。不要把导入末尾源数量当作实时核验。

仅需要审阅CSV时运行`build.py --export-csv`；CSV为可选副本。旧`prepare_neo4j_admin_import.py`不是V3默认步骤；不要用旧离线包覆盖现有库。

## 检索与本地LLM

```powershell
& $kgPython .\ship_fault_kg\retrieve.py --query 'Pride of Canterbury CPP背压阀卡滞后超压喷油起火，如何检查？' --prompt
& $kgPython .\ship_fault_kg\retrieve.py --input-json .\ship_fault_kg\example_diagnosis.json --prompt
& $kgPython .\ship_fault_kg\generate_demo.py --query 'CPP背压阀磨损卡滞、系统超压、回油法兰破裂喷油火灾，给出参考故障链与建议。' --output-name my_cpp_demo
```

最后一步需Ollama已运行且已有`qwen2.5:3b-instruct`，不需要重新下载。流程是LLM选择证据编号＋程序校验＋约束模板正文，不应称作已训练新的诊断模型。

V3新增轴带对中、轴承电蚀、电网振荡等厂家/论文参考知识，但仍不能证明本船根因。电网论文包含实测振荡而非所有振荡均超限；主轴联轴器断裂仍缺真实事故链。当前语义相似度是字符TF-IDF，尚无神经嵌入及学习式重排序。详见V3说明第10节。
