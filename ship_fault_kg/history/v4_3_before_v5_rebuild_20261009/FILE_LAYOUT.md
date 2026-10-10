# 文件组织与历史归档索引

整理日期：2026-10-07；知识修订：2026-10-08。当前知识版本 **V4.3**，491个节点、1200条关系。
V4.3移出两个数据集独有内容，全量接入中文语料；旧快照见 `history/v4_2_before_data_revision_20261008/`。不自动提交或推送Git。

## 一、现在从哪里开始

| 入口 | 用途 |
| --- | --- |
| `README_CN.md` | 当前统一项目说明：构建、检索、建库、评价、局限 |
| `output/ship_fault_kg.sqlite` | 当前唯一默认图谱主数据；不要用history中的SQLite日常导入 |
| `output/entity_inventory_v4.md`、`graph_inventory_v4.json` | 当前实体、关系、属性和证据详单 |
| `output/知识图谱_关系节点属性.csv` | 当前中文易读关系表；构建或导出清单时自动刷新，单独刷新用`export_readable_csv.py` |
| `queries_v4.cypher` | 当前Neo4j查询；不要再用旧V2/V3标签查询判断当前库 |
| `output/graph_viewer.html`、`ship_fault_kg.graphml`、`shipkg_v4*.grass` | 当前离线展示、交换格式、Neo4j样式 |
| `output/neo4j_import_result.json`、`neo4j_snapshot_v4.json` | 当前数据库V4.3同步后的核验回执与快照 |
| `output/corpus_inventory.json`、`corpus_candidates_pending_review.json` | 全量语料溯源清单和待审核候选句；候选句不是图谱关系 |
| `history/README.md` | 各历史阶段与归档的用途、恢复注意事项 |
| `history/organization_20261007/move_manifest.json` | 每个文件整理前后的位置、SHA256、长度及移动核验结果 |
| `history/organization_20261007/DUPLICATES.md`、`duplicates.json` | 完全重复文件检查的可读报告及机器清单 |

## 二、当前目录分工

```text
ship_fault_kg/
├─ README_CN.md / FILE_LAYOUT.md       当前说明和文件导航
├─ build.py / schema.py               构建入口、模式与版本
├─ curated_cases.py / expanded_cases.py  案例事实
├─ fault_profiles.py                  经典故障与核心测点
├─ naming_v4.json / refinement_v4_1.json / redesign.py
│                                    当前重建所必需的命名及迁移规则
├─ retrieve.py / generate_demo.py     检索与报告增强原型
├─ evaluate.py / evaluate_fault_v3.py / eval_cases_v2.py
│                                    当前评价入口与开发查询
├─ verify_v4.py                       当前版本回归测试
├─ import_neo4j.py / sync_neo4j_v4.py  当前直接导入及定向同步
├─ queries_v4.cypher                  当前可视化和核验查询
├─ output/                           当前产物，历史展示已移走
└─ history/                          历史快照、维护备份、旧材料
```

保留根目录的脚本平铺，是为了不破坏现有Python模块导入和`Path(__file__).parent`路径计算。
本次没有为了外观把运行模块拆进新的子包，也不改变用户原有运行命令。
`__pycache__`是Python自动生成缓存，不属于历史版本，Git忽略它，本次不删除。

### 文件名带旧版本号，不一定是旧文件

- `eval_cases_v2.py`仍被`evaluate.py`导入，必须保留。
- `evaluate_fault_v3.py`仍是当前故障评价入口，实际输出是`fault_retrieval_evaluation_v4.json`，必须保留。
- `output/new_source_pages_v3.json`与`source_anchor_audit_v3.json`由当前下载/来源核验脚本生成；资料适用于当前知识，因此保留。
- `refinement_v4_1.json`是当前V4.3重建要应用的规则，不是可以随意移走的旧备份。
- `prepare_neo4j_admin_import.py`是可选的离线CSV准备工具；当前直接导入不依赖它，仍保留备用。
- `purge_archived_sensors.py`保留显式恢复入口，已改为读取history中的55点备份。**不要日常执行删除或恢复命令**；旧删除计数防护针对V3，不适用于当前V4.3。
- `review_source_pages.py`以后生成新来源截图到`output/source_review/`；已有V3截图在history中。

## 三、历史文件移到了哪里

本轮统一放入 `history/organization_20261007/`，已有完整版本快照不移动、不改内容。
为了能准确找回，归档内部保留原相对路径，例如：

`output/neo4j_v3_scuffing.jpg` → `history/organization_20261007/v3_artifacts/output/neo4j_v3_scuffing.jpg`。

| 子目录 | 保存内容 |
| --- | --- |
| `legacy_tools/` | 旧V2/V3查询、旧验证脚本、V3阶段修订工具 |
| `v1_artifacts/output/v1_legacy/` | 早期CSV等旧格式产物 |
| `v2_artifacts/output/` | V2清单、评价、草稿、样式、截图 |
| `v3_artifacts/output/` | V3清单、草稿、评价、截图及当时Ollama日志 |
| `sensor_maintenance/output/` | 55点维护备份、回执、旧查询及修订ID清单 |
| `connection_maintenance/output/` | 旧端口和连接修复的配置备份及检查记录 |
| `source_review/output/source_review_v3/` | 当时原资料页的核验截图 |
| `presentations/presentations/` | 旧PPT、讲稿、生成脚本和渲染素材 |
| `design_review/review_v4_20261006/` | V4重设计前的待确认方案和审核材料 |

旧生成脚本和历史讲稿可能保留当时的绝对路径与计数，它们作为历史记录冻结保存。
**不要直接执行归档里的旧构建/修订脚本来覆盖当前output**。如需复现实验，在独立目录复制对应完整快照、恢复其相对布局并检查当时依赖。移动位置映射见manifest。

## 四、重复文件怎样判断和处理

按文件字节长度和SHA256检查全目录（不含Python缓存及自动生成的审计清单）。
同名不意味着相同，名称不同也可能内容完全一样。

已确认例子：旧V2/V3实体清单、旧V2/V3完整JSON清单、V2/V3部分样式；旧PPT候选文件与正式副本；部分`slide-*`与`final-slide-*`图片。
`entity_inventory_v3 copy.md`与原`entity_inventory_v3.md`**不同**，保留并归档，未擅自舍弃用户修改。

本次不删除重复内容。历史快照保留重复运行代码是为了让每个版本相对独立；仅凭哈希去重会破坏回退所需目录。
“额外副本”只是相同内容的统计，不等于垃圾文件数量。要节省空间，应另行批准归档压缩或存储去重方案。

可用当前Python执行：

```powershell
python .\ship_fault_kg\organize_files.py          # 查看本轮尚未移动的固定计划
python .\ship_fault_kg\organize_files.py --scan   # 重新生成重复检查报告，不删除文件
python .\ship_fault_kg\verify_v4.py               # 检查当前结构和检索
```

`--apply`只处理本次审核的固定路径，拒绝覆盖已有归档；整理完后再执行不会二次搬运。
它不是任意未来版本自动归档工具。新的版本应另行确认归档清单。
