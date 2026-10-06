# 船舶动力系统故障知识图谱 V2

当前版本已更新本机Neo4j的 **shipfaultkg**：19起事故、451节点、1034关系、325证据、690文本片段，覆盖5个功能子系统。详细过程、规模口径、案例清单、检索指标与限制见[升级说明](REPORT_KG_V2_UPGRADE_CN.md)。原V1已保存在`history/v1_20261004`。

## 常用入口

- [离线可视化](output/graph_viewer.html)：双击HTML即可使用；按案例切换，节点/边显示名称，点击查看属性和证据。
- [Neo4j查询示例](queries_v2.cypher)：在Browser选择shipfaultkg，逐段复制查询。
- [增强诊断草稿](output/demo_v2_cpp.md)：本机Qwen 3B选择证据，程序检查后生成。
- [规模及校验](output/build_report.json)、[混合检索评价](output/retrieval_evaluation.json)、[字符检索基线](output/retrieval_evaluation_lexical.json)。
- [实体清单](output/entity_inventory_v2.md)、[完整结构与证据JSON](output/graph_inventory_v2.json)。

## 从资料到图谱的流程

MAIB报告/实验数据 → 人工核对事实和页码 → 稳定ID与案例隔离 → 子系统分类 → SQLite主数据 → 实体/文本/因果路径混合检索 → Evidence Pack → LLM与程序约束输出。

SQLite → Neo4j使用直接MERGE/SET，不需要CSV中转。Neo4j是相同结构化知识的在线查询和可视化副本，文本片段仍由SQLite检索；没有把整份PDF、时序样本全部变成图节点。

## 主要文件

| 文件 | 用途 |
| --- | --- |
| curated_cases.py / expanded_cases.py | 原7起／新增12起事故的人工整理事实 |
| schema.py | 中文显示名、实体类型、关系和5子系统分类 |
| audit_sources.py / build.py | 核对PDF定位词／验证端点证据并构建SQLite |
| output/ship_fault_kg.sqlite | nodes、edges、evidence、passages四张表，当前主数据 |
| import_neo4j.py | 标准库HTTP Query API直接入库；或生成Browser用Cypher |
| output/shipkg_v2.grass | 节点名和关系名的Neo4j样式；在`:style`上传后点Import |
| visualize_graph.py / export_graphml.py | 生成无需联网的HTML和GraphML |
| retrieve.py | 别名实体匹配＋字符TF-IDF＋术语扩展＋案例内路径补全 |
| evaluate.py / eval_cases_v2.py | 38道开发问题及基线对照，不是独立专家测试集 |
| verify_v2.py | 7项完整性和回归测试 |
| generate_demo.py | 现有本机3B模型选择证据，再核查和生成可引用草稿 |
| output/v1_legacy/ | 旧CSV、离线管理员导入包和旧演示；不能代表V2现状 |

## 重建与导入

日常查看无需重新建库，只启动Neo4j Desktop中的ShipFaultKG实例，连接数据库。HTML可离线直接打开。

```powershell
cd D:\RAGQnASystem\RAGQnASystem-main
$kgPython = 'C:\Users\18270\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $kgPython .\ship_fault_kg\audit_sources.py
& $kgPython .\ship_fault_kg\build.py
& $kgPython .\ship_fault_kg\import_neo4j.py
& $kgPython .\ship_fault_kg\visualize_graph.py
& $kgPython .\ship_fault_kg\export_graphml.py
& $kgPython .\ship_fault_kg\export_inventory.py
& $kgPython .\ship_fault_kg\evaluate.py
& $kgPython .\ship_fault_kg\evaluate.py --strategy lexical
& $kgPython .\ship_fault_kg\verify_v2.py
```

构建与PDF审核需要pypdf；其余脚本仅使用Python标准库。导入默认HTTP7475、数据库shipfaultkg，交互终端输入当前密码，不保存。若改了连接端口，使用`--url`与`--database`。

已登录Browser可用`import_neo4j.py --prepare-only`准备Cypher，再通过生成的独立复制页面复制三步代码。保持数据库选对。不要把`neo4j_direct_import.cypher`中的返回源数量当成实时核验，仍要运行第三步统计。

仅需要审阅CSV时运行`build.py --export-csv`；CSV为可选审计副本。旧`prepare_neo4j_admin_import.py`保留供研究，不是V2默认步骤；不要用旧离线包覆盖现有库。

## 检索与本地LLM

```powershell
& $kgPython .\ship_fault_kg\retrieve.py --query 'Pride of Canterbury CPP背压阀卡滞后超压喷油起火，如何检查？' --prompt
& $kgPython .\ship_fault_kg\retrieve.py --input-json .\ship_fault_kg\example_diagnosis.json --prompt
& $kgPython .\ship_fault_kg\generate_demo.py --query 'CPP背压阀磨损卡滞、系统超压、回油法兰破裂喷油火灾，给出参考故障链与建议。' --output-name my_cpp_demo
```

最后一步需Ollama已运行且已有`qwen2.5:3b-instruct`，不需要重新下载。流程是LLM选择证据编号＋程序校验＋约束模板正文，不应称作已训练新的诊断模型。

当前不包含轴带发电/电网耦合振荡的直接故障证据。检索提示“邻近案例”时，不能声称已经判明本船根因。详细不足和改善方向见升级说明第10节。
