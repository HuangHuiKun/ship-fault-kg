# 船舶故障实验知识图谱 V5

更新：2026-10-09。当前默认构建器、数据库快照和检索入口均为 V5。

目标：为上游初步诊断提供故障机理、症状、检查、运维及出处证据，供可替换的知识图谱增强诊断实验使用。不是训练完成的大模型或实船安全决策系统。

## 当前结果

- 1,356 个节点、3,343 条关系；12 类实体、23 种业务关系＋溯源关系。
- 168 个通用故障概念＋48 条事故内故障记录，350 个状态、110 个影响因素、143 个检查、170 个运维措施。
- 5 个功能子系统＋1 个动力系统根节点；19 个原有正式案例、8 条具名船舶、46 个实际使用来源。
- 关系中含 1,381 条溯源边、352 条因果类声明，不应把全部关系当成不同故障机理。
- Passage、Assertion 在本地 SQLite/JSONL 中，不作为 Neo4j 节点。试验工况保留为本地资料索引，不建 Run 节点。
- Neo4j 已实际更新 shipfaultkg，1,356/3,343，全部节点和关系属性与本地快照一致。后续状态以 output/v5/neo4j_verify_result.json 为准。

## 从哪里读起

| 文件 | 用途 |
| --- | --- |
| [构建与建库报告](output/v5/新版知识图谱构建与建库报告_V5.md) | 每一步做法与缘由、统计、来源、限制、回滚 |
| [实体关系属性清单](output/v5/entity_inventory_v5.md) | 当前类别、属性及关系统计 |
| output/v5/ship_fault_kg.sqlite | V5 唯一本地图谱主数据 |
| [中文逐关系表](output/v5/知识图谱_关系节点属性_V5.csv) | 实体－关系－实体、出处、确定性及引用；构建自动刷新 |
| [Neo4j 查询](output/v5/queries_v5.cypher) | 子系统总览、拉缸局部、逐跳因果与溯源 |
| output/v5/retrieval_example.json | 真实运行的诊断文本检索证据包 |
| v5/schema.py、v5/curation.py | 类别/关系规则、新增知识声明 |
| [文件导航](FILE_LAYOUT.md) | 当前与历史文件分工 |

## 运行命令

在安装 pypdf 的 Python 环境中，从项目根目录运行。本次实际环境为 Python 3.12.14、pypdf 6.10.0；锁定依赖见 v5/requirements.txt。先用 python -c "import pypdf, sqlite3" 检查，缺失时执行 python -m pip install -r ship_fault_kg/v5/requirements.txt。

```powershell
cd D:\RAGQnASystem\RAGQnASystem-main
python ship_fault_kg/manage_v5.py build
python ship_fault_kg/manage_v5.py verify
python ship_fault_kg/manage_v5.py retrieve "主机可能拉缸，排气温度升高"
# Neo4j Desktop 启动后，终端隐藏输入密码：
python ship_fault_kg/manage_v5.py neo4j apply
python ship_fault_kg/manage_v5.py neo4j verify
python ship_fault_kg/manage_v5.py report
```

build.py、retrieve.py、import_neo4j.py 是兼容入口，均已指向 V5。不要运行 history 中的旧构建器更新当前数据库。SQLite 通过 HTTP Query API 直接同步，CSV 仅用于阅读，不是导入必经环节。

数据库连接：http://127.0.0.1:7474/browser/；Bolt 端口 7687；数据库 shipfaultkg。项目未修改端口和 Browser 自定义颜色。可选样式 output/v5/shipkg_v5.grass 沿用旧类别配色；若需要手动导入，并把 ShipKG 标签优先级放在业务标签之后。

## 回滚

旧版文件、代码、中间数据与实时数据库备份：history/v4_3_before_v5_rebuild_20261009/。原始资料包未改变。

```powershell
python ship_fault_kg/manage_v5.py neo4j restore
```

该操作恢复旧 ShipKG 节点与关系及属性，并先备份当前图谱；不自动还原 Browser 样式或清除约束。旧文件复位方法和备份 SHA256 清单见构建报告与 history 下 backup_manifest.json。

## 必须知道的边界

全部 1,275 篇中文语料已索引，但正式建图目前用 18 篇，不能说全部已审核入图。来源定位与结构检查通过，不代表专家已验证所有机理；专家复核数为 0。

当前检索是别名＋词法匹配＋同范围关系扩展，未实现语义向量、成熟混合重排或 LLM 联调。旧 38/24 题的 ID 与标签已不适用；新开发样例不等同独立检索评测。后续需新金标准、语义检索与诊断报告质量评价。

科研方法原型，实船操作必须依据适用厂家规程与专业审核。第三方资料保留原有权利；参见[项目免责声明](../DISCLAIMER.md)。本次未提交或推送 Git。
更新：2026-10-08。当前知识版本 **V4.3**。

> 科研方法原型，不用于无人审核的船舶运维决策。第三方资料保留原有权利；公开仓库、引用与免责声明不构成再分发许可。见[项目免责声明](../DISCLAIMER.md)。

## 1. 目标与交付

本项目将事故调查报告、厂家通函、论文和受控试验资料整理为小规模、有证据和适用范围的知识图谱，辅助增强前级模型的初步诊断文本。交付的是图谱、可复现的构建与检索程序、证据包和评测记录，不是训练完成的新诊断大模型。

```text
官方报告 / 厂家手册 / 论文 ──人工整理、原文锚点核对──┐
保留的实验数据 ──字段、工况、故障标签映射──────────┤
全部中文语料 ──分块检索 + 候选句筛选 + 原文审核────┤
                                                     ↓
                实体、关系、证据、文本片段 → SQLite 主数据
                                         ├→ Neo4j 直接同步与可视化
前级模型的诊断文本 → 实体对齐 + 文本匹配 + 同单元路径检索
                                         ↓
                          Evidence Pack：来源、位置、确定性、适用范围
                                         ↓
                             LLM辅助生成 + 人工核验（待实际联调）
```

## 2. 当前规模与本次变化

| 内容 | V4.3 |
| --- | ---: |
| 节点 / 关系 | 491 / 1200 |
| 实体类型 / 实际关系类型 | 15 / 28 |
| 正式历史事故 / 原有故障参考单元 | 19 / 12 |
| 核心测点 / 试验运行 | 15 / 16 |
| 来源节点 | 33：资料级29、文章级4；记录级0 |
| 证据记录 / 可检索文本片段 | 335 / 4406 |
| 中文语料文章 / 中文语料分块 | 1275 / 3699 |
| 中文语料建图试点 | 4篇文章、22条诊断关系，全部待专家核验 |

两个数据集已从活动资料包移出：Azimuth Thruster CBM、UCI Naval Propulsion CBM。它们的独有节点和相关关系、证据不再参与当前图谱构建。**原有12条记录级Source来自Azimuth，因此本次一并移出**，没有改成12起真实事故。被保留的同名或共享知识，仅能通过其他仍保留的来源支持。

原有图谱与原始资料可从 `history/v4_2_before_data_revision_20261008/` 恢复。中文语料仅增加文章级知识单元，不增加无法核实船名的事故Case。节点总数与旧版同为491是移出和新增相抵，不表示未修改。

电网振荡论文移到 `ship_fault_kg_data/03_papers/Frontiers_2021_marine_converter_oscillations.pdf`，文件名及原证据ID不变；读取路径由清单决定，不能再硬编码到02_reports。

## 3. 文件分工

| 文件 | 用途 |
| --- | --- |
| `build.py` | 唯一默认构建入口；不修改Neo4j |
| `schema.py` | 类型、关系、确定性与版本定义 |
| `curated_cases.py`、`expanded_cases.py` | 19起正式案例的来源锚点和事实 |
| `fault_profiles.py` | 12个参考故障机理单元、保留测点清单 |
| `redesign.py`、`naming_v4.json`、`refinement_v4_1.json` | 既有稳定ID的命名与本体整理规则；旧数据命名条目保留作历史映射，不等于仍参与建图 |
| `corpus_knowledge.py` | 全量中文语料索引、候选句筛选、4篇原文核对试点 |
| `output/ship_fault_kg.sqlite` | 当前主数据：nodes、edges、evidence、passages四表 |
| `output/build_report.json` | 实际规模和构建状态；CSV是否成功覆盖也在这里 |
| `output/corpus_inventory.json` | 全部文章的路径、指纹、重复项、分块ID和资料包原始分组 |
| `output/corpus_candidates_pending_review.json` | 25762条因果/运维候选句；**不是图谱边，也不是已审核的金标准** |
| `output/知识图谱_关系节点属性.csv` | 当前新版易读表；文件被占用时构建器保留旧表并输出带版本号的备用表 |
| `output/entity_inventory_v4.md`、`graph_inventory_v4.json` | 当前实体/关系清单，v4代表本体主版本 |
| `sync_data_revision.py` | V4.2→V4.3范围受限、先备份、单事务同步 |
| `import_neo4j.py` | 新空库的直接导入；SQLite→HTTP Query API，不必经过CSV |
| `retrieve.py` | 本地SQLite检索与LLM提示词组装 |
| `verify_revision.py` / `verify_v4.py` | 当前版本回归测试；旧测试保存在历史备份 |
| `evaluate.py`、`evaluate_fault_v3.py` | 38题案例/数据开发自检和24题参考故障开发自检 |
| `output/neo4j_import_result.json` | 只有实际同步核验成功才更新的Neo4j回执 |

`history`仅作归档，不参与默认构建；之前的PPT和V4.2检索报告属于历史版本，没有冒充V4.3结果。旧版完整说明与连接排错过程在本次备份内的README_CN.md。

## 4. 为什么这样使用中文语料

所有1275篇文章均全文检查并分块，单块最多1400个字符、相邻块重叠150字符。不再按标题关键词每类选12篇，也不再截掉6000字符之后的内容。重复文章标注在清单中，保留文件溯源，不擅自删除原文。

因果/运维关键词只用于筛候选句，不能证明因果。只有 `corpus_knowledge.py` 内逐条配置且引文能在原文精确找到的22条诊断关系进入试点；会区分可能关系、风险关系和处置关系，限定共享回路或特定机型。

来源层级：`Source(source_level=文章级)` → `Source(source_level=资料级)` → 本地文章与Zenodo资料包入口。文中没有可核实的原始报告/作者链接时，不虚构原始来源。

所有试点标注 `knowledge_layer=corpus_secondary`、`expert_review=pending`，关系确定性为 `corpus_statement`。它表示“文章这样记载”，不表示厂家认可或本船根因确诊。温度、压力、力矩、清洗或运行参数不能跨机型照搬；运维输出需核对本机手册。

原资料包train/val/test只记录文章所在目录。现在全部参与检索，**不能把原test目录当作本项目独立测试集**。今后应按来源/事故划分独立专家标注测试集。

## 5. 构建、测试与同步命令

在项目根目录，用已安装pypdf的Python运行。下面的python可替换成当前实际解释器路径。

```powershell
python ship_fault_kg/build.py
python ship_fault_kg/verify_v4.py
python ship_fault_kg/test_export_readable_csv.py
python ship_fault_kg/audit_sources.py
python ship_fault_kg/export_inventory.py
python ship_fault_kg/export_graphml.py
python ship_fault_kg/visualize_graph.py
python ship_fault_kg/evaluate.py
python ship_fault_kg/evaluate_fault_v3.py
```

先在Neo4j Desktop启动ShipFaultKG实例，再同步现有V4.2库：

```powershell
python ship_fault_kg/sync_data_revision.py --apply
```

交互输入密码，不保存密码。该程序先核对本地历史快照与数据库ID；只允许删除由两个指定移出来源独立支持的节点。发现未知节点/关系或删除节点连着外部关系会拒绝同步或回滚，不使用全库清空。所有增删改置于一笔事务，不调整Browser已有配色。

日常本地图谱再次修改后需要基于新的明确快照审核差异，不应将这条V4.2迁移命令当作任意修改的通用强制覆盖。空库用 `import_neo4j.py`；对非空旧库仅MERGE不会去除过时节点。

Browser地址：`http://127.0.0.1:7474/browser/`，连接地址：`neo4j://127.0.0.1:7687`，数据库选择 `shipfaultkg`。

## 6. 检索示例与边界

```powershell
python ship_fault_kg/retrieve.py --query "空压机高压冷却器渗漏，副机冷却水中断并高温停机" --prompt
```

当前是实体名称/别名对齐、字符n-gram TF-IDF匹配、上下文分数融合与同知识单元内的有向路径检索。**尚未部署向量语义模型、交叉编码器重排序或自动LLM抽取**，不能把关键词匹配称为完整语义检索。

输出包含实体匹配、事故或参考单元、事实、因果路径、全文分块、来源URL及locator、确定性、适用范围和覆盖提醒。只有文本匹配、没有已建图事实时标为text_evidence_only，不能输出已证实因果链。LLM提示词将补充文本和结构化事实分开。不同事故/文章的路径不拼接为一条已证实因果链。中文文章不伪造PDF页码，使用文章相对路径和标准化字符区间定位。

38题和24题是同源人工编写的开发测试，不是独立泛化实验，也不是诊断正确率。全量文本召回已经扩展，但新增语料的专家标注、独立测试及LLM生成质量评价仍需继续建设。

## 7. 恢复与Git

旧输出、代码、元数据、移出资料在 `history/v4_2_before_data_revision_20261008/`。Neo4j同步前还会在其中保存 `neo4j_snapshot.json`。恢复需将代码与数据快照作为同一版本处理，不能只导入旧SQLite后又运行新版构建。

本次不自动提交或推送Git；原有未提交PPT、报告及用户变更均保留。
