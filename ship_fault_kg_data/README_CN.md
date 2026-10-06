# 船舶动力系统故障知识图谱资料包

整理日期：2026-09-28
最后修订：2026-10-06（逐目录核对磁盘实际内容后更新，修订项汇总见第 10 节）
保存位置：`D:\RAGQnASystem\RAGQnASystem-main\ship_fault_kg_data`
本说明文件位置：`ship_fault_kg_data\README_CN.md`（位于资料包根目录，不在 `05_metadata/` 内）

## 1. 这批资料能做什么

公开网络上几乎没有"下载后即可导入 Neo4j"的完整船舶动力系统故障知识图谱。本资料包因此按知识图谱构建流程收集了四类可用原料：

1. **实验与状态监测数据**：提供设备、工况、传感器、故障类别和异常状态。
2. **事故调查报告与厂商技术文档**：提供故障现象、原因、事件链、后果、处置和可追溯证据。
3. **论文**：提供故障分类、知识图谱本体、实体关系设计和诊断方法。
4. **代码、提示词和模式参考**：提供信息抽取、因果路径分析、评价和 GraphRAG 的实现参考。

推荐的核心图谱链路是：

`船舶/动力系统 → 设备 → 部件 → 工况 → 症状/传感器异常 → 故障 → 原因 → 影响 → 检查方法 → 运维措施 → 来源证据`

当前规模：6 个顶层目录，4 个数据集，32 个 PDF（27 份报告/技术文档 + 4 篇论文 + 1 份已隔离的损坏文件），3 个开源代码仓库，共 1455 个文件。

## 2. 目录结构

实际磁盘结构（含真实嵌套层级，解压后多套一层同名目录）：

```text
ship_fault_kg_data/
├─ README_CN.md                     本说明
├─ 01_datasets/                     4 个数据集（已解压）
│  ├─ Marine_Engine_Fault_Data_v1/
│  │  └─ Marine_Engine_Fault_Data/  实机试验数据本体
│  ├─ marine_diesel_RAG_corpus_All_data/
│  │  └─ All_data/{train,val,test}/ 1275 篇中文 Markdown
│  ├─ Azimuth_Thruster_CBM_Dataset/ data/ figures/ code/ metadata/ licenses/ ...
│  └─ UCI_Naval_Propulsion_CBM/
│     ├─ UCI CBM Dataset/           data.txt / Features.txt / README.txt
│     └─ __MACOSX/                  解压残留垃圾目录（见第 8 节）
├─ 02_reports/                      27 个 PDF（平铺，无子目录）
├─ 03_papers/                       4 个 PDF（平铺，无子目录）
├─ 04_code_and_schemas/             3 个仓库（各多套一层目录）
│  ├─ TSRF_main/TSRF-main/
│  ├─ Marine_weak_thermal_fault_main/Marine-diesel-engine-explainable-weak-thermal-fault-diagnosis-main/
│  └─ HFACS_KG_main/HFACS-KG-main/
├─ 05_metadata/                     来源清单 2 份、哈希清单 1 份、辅助脚本 4 个
└─ downloads_tmp/                   仅存 1 个下载中断损坏的 PDF，已隔离未使用
```

`05_metadata/` 具体包含：

| 文件 | 作用 |
|---|---|
| `source_manifest.csv` | 首批 23 条来源清单（数据集、MAIB 报告、论文、代码仓库），含标题、URL、DOI/编号、许可、校验状态 |
| `source_manifest_v3.csv` | 扩充批 16 条来源清单（MAN 7、STAMFORD 7、Frontiers 1、MAIB Hebrides 1），含物理页数 |
| `sha256_manifest.csv` | 20 条 SHA-256 记录（见第 8 节的重要说明） |
| `download_zenodo_parallel.ps1` | Zenodo 分片并行下载脚本 |
| `extract_legacy_zip_names.py` | 修复 GBK 编码 ZIP 的中文文件名 |
| `inspect_pdf_pages.py` | 按页提取 PDF 文本并做关键词定位，用于人工核对证据 |
| `repair_strathprints_pdf.ps1` | 修复 Strathprints 下载中断文件的脚本（未成功，产物已隔离） |

## 3. 数据集

| 优先级 | 本地路径 | 内容与规模（已核对） | 对知识图谱的价值 | 注意事项 |
|---|---|---|---|---|
| A | `01_datasets/Marine_Engine_Fault_Data_v1/Marine_Engine_Fault_Data/` | Matsui Iron Works **MU323DGSC** 船用柴油机实机试验；1 个参考工况文件 + 5 类故障共 15 个工况文件；合计 **114,770 行数据**（参考 25,302 + 故障 89,468）；故障文件统一 73 列，参考文件 70 列 | 可建立"故障—工况—传感器—异常表现"关系，并生成标准化诊断输入样例 | CC BY 4.0（Zenodo DOI 为预留，记录将在论文接收后开放）；三行表头；参考文件与故障文件列集不同，需分开预处理 |
| A | `01_datasets/marine_diesel_RAG_corpus_All_data/All_data/` | **1,275 篇中文 Markdown**（全部为 `.md`）；train 1020、val 127、test 128 | 可做中文实体/关系抽取、向量检索、RAG 语料和故障术语词典 | Zenodo 记录未声明许可证；部分内容可能来自网络文章，仅建议内部科研，公开再分发前需逐条核验来源 |
| B | `01_datasets/Azimuth_Thruster_CBM_Dataset/` | 沿海拖轮方位推进系统匿名化多模态 CBM 数据：`data/` 10 个 CSV（推进架构、润滑油交叉验证、按故障类型的提前期 LTI、诊断区间经济性、敏感性检查、代表性 FFT 特征、SSS 公式参数与回归汇总、案例级元数据、测量计数）；`figures/` 8 组图各 3 种格式（PDF/PNG/TIF）；`code/` 2 个脚本；`metadata/` 6 个文件含数据字典 | 可补充推进器、振动频谱、润滑油指标、故障提前量和运维决策关系 | 原始逐点 FFT 因保密与数据所有权限制未公开；数据 CC BY 4.0，代码 MIT；已按发动机族（CAT C7 / 3516C / 3508B-C）匿名化，船名、运营方、港口班期、合同级可用性记录均已移除 |
| B | `01_datasets/UCI_Naval_Propulsion_CBM/UCI CBM Dataset/` | `data.txt` 共 **11,934 行**护卫舰燃气轮机推进**仿真**记录，16 个输入特征 + 压气机/涡轮退化系数；另含 `Features.txt`、`README.txt` | 可建立"工况—部件退化—测量特征"的基线图谱和诊断测试集 | UCI 页面与压缩包内旧版说明的许可表述不一致，暂按科研使用，发表或商用前再次核验；目录内含 `__MACOSX/` 解压残留 |

### 3.1 实机故障数据集的类别与负载程序（逐文件核对）

以 `dataset_index.csv` 为权威索引，各类故障的负载条件**并不一致**：

| 故障类别 | 中文含义 | 文件数 | 负载条件 | 异常标注 |
|---|---|---|---|---|
| `AF_Clogging` | 压气机空气滤器堵塞 | 4 | 40% / 60% / 75% / 85% | 二值（0=异常前，1=异常） |
| `AC_Fouling` | 空冷器 fouling | 4 | 40% / 60% / 75% / 85% | 二值 |
| `Turbine_Degradation` | 涡轮退化（排气侧背压升高诱导） | 3 | 40% / 60% / **85%**（无 75%） | 二值 |
| `Pump_Cavitation` | 冷却水泵气蚀（吸入侧加压空气模拟） | 2 | **60% / 85%**（无 40%/75%） | 二值 |
| `Injector_Nozzle` | 喷油阀喷孔堵塞 | 2 | 单孔堵塞：40%→60%→85% 阶梯；双孔堵塞：变负载程序（约 40–85%） | **全程为异常**，无基线段 |

读取时必须注意的四点：

1. **三行表头**：第 1 行完整变量名（作为列键）、第 2 行简写符号、第 3 行单位，数据从第 4 行开始。简写符号有复用（如 `Pmax`、`Pmin`、`We`、`Wi` 在 1–3 缸重复），预处理时应同时保留全名行与简写行。
2. **参考文件列集不同**：`Reference_Data.csv` 无 `Anomaly State` 列，用 `Time`（`T`, s）而非 `Time_abs`/`Time_rel`，共 70 列；故障文件为 73 列（前两列时间 + `Anomaly State` + 70 个测量通道）。
3. **两个通道存在但未记录**：`Compressor Filter Loss`（`dPf`, Pa）与 `Turbine Back Pressure`（`dPex`, Pa）在所有故障文件中都有列，但在 5 次试验中未采集，因此为空（NaN）：`AC_Fouling_85_Load.csv`、`Clogged_Injector_Nozzle1_40_60_85_Load.csv`、`Clogged_Injector_Nozzle2_LoadProgram.csv`、`CW_Pump_Cavitation_60_Load.csv`、`CW_Pump_Cavitation_85_Load.csv`。**空值表示"该次未测量"，不是"数值为 0"**。
4. **单位混用**：SI 与工程单位并存（`kgf/cm2`、`kgf`、`m3/h`、`°C`）；`Pl_lo`、`Pl_fuel`、`Pl_water1`、`Pl_water2`、`Pl_loturb`、`Pl_valve` 存的是**原始电压信号（V）**而非标定后的压力，应作为原始传感器输出处理。

编码统一为 UTF-8（无 BOM）、LF 换行。加载示例：

```python
import pandas as pd

# 故障文件：用全名行作列，跳过简写与单位行
df = pd.read_csv("AF_Clogging/AF_Clogging_60_Load.csv",
                 header=0, skiprows=[1, 2], encoding="utf-8")
pre, fault = df[df["Anomaly State"] == 0], df[df["Anomaly State"] == 1]

# 参考文件：同样的表头约定，但列集不同（70 列）
ref = pd.read_csv("Reference_Data.csv", header=0, skiprows=[1, 2], encoding="utf-8")
```

配套文件：`variable_dictionary.csv`（变量级字典，含逐文件采集情况与数据类型）、`dataset_index.csv`（文件级索引，含 schema 类型、场景、负载、行列数、异常状态类型）、`provenance/normalize.py`（v1.0 归一化脚本，可复现从原始台架导出到本发布版的全部转换；测量值本身未被改动）、`CITATION.cff`、`LICENSE`、`README.md`。

引用要求（数据集与配套 Data Descriptor 需同时引用）：

> BahooToroody, A., Bondarenko, O., Abaei, M. M., Niki, Y., & Zio, E. (2026). *Marine Engine Fault Dataset* (Version 1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.19857425

> 同作者 (2026). *Marine Engine Fault Dataset: Open-Access Data under Controlled Reference and Fault Scenario Conditions*. Scientific Data（投稿中），预印本 arXiv:2607.19444。

### 3.2 数据集下载来源

- Marine Engine Fault Dataset：<https://zenodo.org/records/19857425>
- Marine diesel RAG corpus：<https://zenodo.org/records/20258638>
- Azimuth Thruster CBM Dataset：<https://zenodo.org/records/20101612>
- UCI Naval Propulsion CBM：<https://archive.ics.uci.edu/dataset/316/condition%2Bbased%2Bmaintenance%2Bof%2Bnaval%2Bpropulsion%2Bplants>

RAG 语料 ZIP 原使用旧式 GBK 文件名编码，解压目录已通过 `05_metadata/extract_legacy_zip_names.py` 恢复为正常中文文件名。

## 4. 报告与厂商技术文档

`02_reports/` 共 **27 个 PDF**，来自四类机构，**并非全部为 MAIB 事故报告**。三类的建图用途差异很大，建议分别对待：

- **MAIB 事故调查报告（12 份）**：唯一能提供完整"故障—原因—事件—后果—建议"可追溯证据链的真实事故数据，是因果三元组抽取的主力来源。
- **MAN 技术服务公告（7 份）**：厂商侧的故障机理、磨损监测与检修判据，适合抽取"部件—失效模式—检查方法—运维措施"。
- **STAMFORD 应用指南（7 份）**：发电机与电气侧（轴电流、绝缘、轴承、联轴器、扭振、故障保护），适合补充电力系统分支。
- **期刊论文（1 份）**：大功率变流器船舶电力系统振荡行为对比案例研究，属研究文献，误置于本目录，建图时按论文处理。

### 4.1 MAIB 事故调查报告（12 份）

| 本地文件 | 报告编号 | 重点内容 | 建议抽取 |
|---|---|---|---|
| `MAIB_2026_10_Kommandor_Susan_generator_bearing_failure.pdf` | MAIB 2026-10 | 发电机轴承异常磨损、灾难性故障、火灾、全船失电和失去推进 | 轴承、非原厂备件、润滑/磨损、发电机、失电、推进丧失 |
| `MAIB_2026_06_Spirit_of_Discovery_propulsion_loss.pdf` | MAIB 2026-06 | 大风浪中螺旋桨出水、超速保护停机、推进失效（逾百人受伤、1 人死亡） | 海况、转速、保护逻辑、吊舱推进、人员后果 |
| `MAIB_2024_20_Stena_Europe_fuel_spray_fire.pdf` | MAIB 20/2024 | 加压燃油喷射引发机舱火灾 | 燃油管法兰、高温表面、隔热屏蔽、检查 |
| `MAIB_2022_04_Wight_Sky_multiple_engine_failures.pdf` | MAIB 2022-04 | 多台发动机灾难性失效、轴承咬死及维修监测问题 | 多故障关联、轴承、维护程序、状态监测 |
| `MAIB_2021_02_Finlandia_Seaways_connecting_rod_failure.pdf` | MAIB 2021-02 | 连杆维护不当导致发动机失效和火灾 | 连杆、紧固/装配、维护错误、曲轴箱、火灾 |
| `MAIB_2018_14_Wight_Sky_engine_bearing_fire.pdf` | MAIB 2018-14 | 主机轴承故障及火灾 | 轴承、润滑、温度、火灾、检查措施 |
| `MAIB_2018_01_Windcat8_bearing_failure_fire.pdf` | MAIB 2018-01 | 连杆大端轴瓦失效及火灾 | 连杆、轴瓦、润滑、裂纹/磨损、火灾 |
| `MAIB_2017_20_Hebrides_CPP_coupling.pdf` | MAIB 20/2017 | 可调螺距螺旋桨（CPP）执行机构联轴器失效（38 页） | CPP、执行机构、联轴器、推进控制 |
| `MAIB_2016_Safety_Digest_generator_oil_fire.pdf` | Safety Digest 1/2016 | 发电机润滑油喷到高温排气部件引发火灾 | 泄漏、高温表面、点火、隔热、检查 |
| `MAIB_2015_22_Pride_of_Canterbury_CPP_hydraulic_fire.pdf` | MAIB 22/2015 | CPP 液压超压及火灾 | CPP 阀件磨损、液压保护、推进控制 |
| `MAIB_2013_Safety_Digest_lubrication_bearing_cases.pdf` | Safety Digest 2/2013 | 润滑与轴承损伤案例集 | 润滑不足、污染、轴承损伤、预防措施 |
| `MAIB_2011_28_Queen_Mary_2_harmonic_filter_failure.pdf` | MAIB 28/2011 | 谐波滤波器电容器失效导致全船失电 | 高压谐波滤波器、保护整定、失电、推进丧失 |

MAIB 文本通常按英国 Open Government Licence v3.0 使用，但第三方图片或材料可能例外。使用时应准确引用报告标题、编号、年份和来源。主要来源页：

- Kommandor Susan：<https://www.gov.uk/maib-reports/catastrophic-engine-failure-and-subsequent-fire-on-board-the-site-investigation-vessel-kommandor-susan>
- Finlandia Seaways：<https://www.gov.uk/maib-reports/engine-failure-and-subsequent-fire-on-ro-ro-cargo-vessel-finlandia-seaways-with-1-person-injured>
- Spirit of Discovery：<https://www.gov.uk/maib-reports/loss-of-propulsion-in-heavy-weather-experienced-by-the-passenger-vessel-spirit-of-discovery-leading-to-over-100-injuries-and-one-fatality>
- 其余各篇的直链见 `05_metadata/source_manifest.csv` 与 `source_manifest_v3.csv` 的 `source_url` 字段。

### 4.2 MAN 技术服务公告（7 份）

| 本地文件 | 编号与主题 | 页数 |
|---|---|---|
| `MAN_SL2013_569_bearing_wear_monitoring.pdf` | SL2013-569 轴承磨损监测与轴承咬死 | 4 |
| `MAN_SL2016_623_cooling_water.pdf` | SL2016-623 冷却水处理与定期检测 | 4 |
| `MAN_SL2016_633_piston_rings_scuffing.pdf` | SL2016-633 硬涂层活塞环与缸套擦伤 | 8 |
| `MAN_SL2017_654_torsional_damper.pdf` | SL2017-654 曲轴扭振减振器 | 1 |
| `MAN_SL2019_685_ring_coating_wear.pdf` | SL2019-685 金属陶瓷活塞环的视情检修 | 3 |
| `MAN_SL2023_737_cylinder_lubrication.pdf` | SL2023-737 气缸润滑更新 | 9 |
| `MAN_main_engine_auxiliary_efficiency.pdf` | 主机与辅助系统效率改进 | 23 |

### 4.3 STAMFORD 应用指南（7 份）

| 本地文件 | 编号与主题 | 页数 |
|---|---|---|
| `STAMFORD_AGN033_bearing_currents.pdf` | AGN033 轴轴承电流 | 4 |
| `STAMFORD_AGN035_fault_protection.pdf` | AGN035 过载与故障保护、瞬态耦合扭矩 | 11 |
| `STAMFORD_AGN039_marine_shaft_generators.pdf` | AGN039 船用轴带发电机 | 11 |
| `STAMFORD_AGN040_winding_insulation.pdf` | AGN040 绕组绝缘系统 | 9 |
| `STAMFORD_AGN076_alternator_bearings.pdf` | AGN076 交流发电机轴承 | 9 |
| `STAMFORD_AGN232_coupling_arrangements.pdf` | AGN232 发电机组联轴器布置 | 8 |
| `STAMFORD_AGN235_torsional_analysis.pdf` | AGN235 发电机组扭振分析 | 11 |

### 4.4 期刊论文（1 份，误置）

| 本地文件 | 主题 | 许可 |
|---|---|---|
| `Frontiers_2021_marine_converter_oscillations.pdf` | 大功率变流器船舶电力系统振荡行为对比案例研究（14 页，DOI 10.3389/fenrg.2020.529756） | CC BY，需署名原作者与 DOI |

> 说明：4.2–4.4 的主题与页数取自 `source_manifest_v3.csv` 的标题字段与页数校验记录，未逐页通读全文；正式抽取前应按正文核对具体结论与适用机型。

**厂商文档许可边界（重要）**：MAN 与 STAMFORD 的 14 份 PDF 版权均归厂商，仅可本地内部研究使用，**不得公开再分发完整 PDF**，二次发布只能引用编号与摘要。

## 5. 论文

`03_papers/` 共 4 个可正常解析的 PDF：

| 本地文件 | 用途 | 来源 |
|---|---|---|
| `2025_Marine_Diesel_Fault_Knowledge_Graph.pdf` | 最直接的船用柴油机故障知识图谱参考：本体设计、BiLSTM-CRF 抽取、Neo4j 存储和故障因果展示 | <https://doi.org/10.3390/jmse13040693>（CC BY 4.0） |
| `2026_Marine_Engine_Fault_Dataset.pdf` | 与实机故障数据集配套，理解试验平台、故障注入、变量和数据质量 | <https://arxiv.org/abs/2607.19444> |
| `2024_Survey_Data_Driven_Fault_Diagnosis_Marine_Diesel_Engines.pdf` | 梳理柴油机故障类别、数据来源、诊断算法和研究空白 | <https://arxiv.org/abs/2404.10363> |
| `2018_Marine_Diesel_Engine_Failure_Simulator.pdf` | 柴油机故障模拟器、故障工况生成和特征变化参考 | <https://zenodo.org/records/14620906> |

另有 1 份下载中断导致内部结构损坏的文件，已隔离在 `downloads_tmp/invalid_2024_Data_Driven_Marine_Engine_Fault_Diagnosis.pdf`（来源 <https://strathprints.strath.ac.uk/90777/>，有合法 `%PDF-` 文件头但正文截断），**未用于图谱或论文分析**，`05_metadata/repair_strathprints_pdf.ps1` 为其修复尝试脚本。若需要该文献，应重新下载而非使用本地副本。

## 6. 代码与模式参考

| 本地路径 | 实际内容（已核对） | 可复用点 | 限制 |
|---|---|---|---|
| `04_code_and_schemas/TSRF_main/TSRF-main/` | `data/` 6 个 CSV（Head-crack、Linner-wear、Piston-ablation、Ring-adhesion、Ring-wear、Normal）；`main.py`、`interactive_shap.py`、`run_interactive_shap.bat`；`src/` 5 个模块（data_loader、models、shap_analysis、visualization、`__init__`）；`requirements.txt`、`LICENSE`、`README.md` | 6 类燃烧室状态数据 + 随机森林/SVM/KNN 与 SHAP 可解释诊断的完整可运行链路 | 数据主要来自热力仿真；代码 MIT |
| `04_code_and_schemas/Marine_weak_thermal_fault_main/Marine-diesel-engine-explainable-weak-thermal-fault-diagnosis-main/` | 17 个 `.py` + `Engine_dataset.csv`；含 `config.py` 与多组对比实验脚本（CNN-LSTM、CNN-GRU-KAN、WCNN-LSTM、TSRF 对比、均值/趋势变体等） | 弱热故障诊断模型与对比实验设计 | **仓库未见明确 LICENSE**，暂仅内部科研参考，不得直接再分发 |
| `04_code_and_schemas/HFACS_KG_main/HFACS-KG-main/` | `prompts/` 4 个文件（stage1.md + stage1_schema.json、stage2.md + stage2_schema.json）；`keywords/categories.json`（29 类语义分组正则，首个匹配生效，兜底类 `Other / Unclassified` 覆盖 18.9% 因子）；`analysis/` 16 个脚本；`LICENSE`（MIT）、`README.md` | 两阶段零样本 LLM 抽取提示词与 JSON Schema、HFACS 四层分类映射、R000–R007 全套分析（含因果路径 R006、敏感性分析 R007）、`compute_metrics.py` 精度/召回/F1、`gen_validation_sample.py` 47 份分层验证样本、`graphrag_demo.py` 的 Q1–Q3 演示查询 | **不含原始 IMO GISIS 报告 PDF，也不含最终知识图谱导出**；分析脚本需自备 `kg_export/` 下 11 个 CSV（6 类节点 + 5 类关系）；抽取需 OpenAI 兼容接口与 `DASHSCOPE_API_KEY`（原实现用 Qwen-Max，可换 GPT-4o / Claude 3.5 Sonnet 等支持 JSON 输出的模型）；GISIS 源报告受 IMO Casualty Investigation Code 约束，需自行从 <https://gisis.imo.org> 获取 |

来源：

- TSRF：<https://github.com/TS-RF/TSRF>
- Marine weak thermal fault diagnosis：<https://github.com/xiezaimi-png/Marine-diesel-engine-explainable-weak-thermal-fault-diagnosis>
- HFACS-KG：<https://github.com/yijie-sjtu/HFACS-KG>（配套论文 *Knowledge Graph Construction and Causal Analysis for Maritime Safety: An HFACS-Guided Zero-Shot LLM Approach*，Xi & Yin，*Ocean Engineering*，2026，审稿中）

HFACS-KG 的分析脚本需按 R001 → R002b → R003 → R004 → R005 → R006 → R007 顺序运行，输出写入本地 `results/`；依赖 `pandas numpy scipy matplotlib openai pdfplumber`，建议 Python 3.10+（作者已测 3.13 / 3.14）。

## 7. 建议的使用顺序

### 第一步：先定图谱模式

参考 `2025_Marine_Diesel_Fault_Knowledge_Graph.pdf` 和 `HFACS_KG_main/prompts/`，先定义：

- 实体：船舶、系统、设备、部件、工况、传感器、症状、故障、原因、影响、检查、措施、报告、证据片段。
- 关系：属于、安装于、监测、表现为、指示、导致、影响、通过检查、建议措施、来源于。
- 证据属性：`source_id`、`document_title`、`page`、`quote_or_summary`、`year`、`confidence`。

`HFACS_KG_main/prompts/stage1_schema.json` 与 `stage2_schema.json` 可直接作为 JSON 输出约束的起点；`keywords/categories.json` 的 29 类正则可作为中文故障术语分组的参照结构。

### 第二步：用结构化数据建立基础节点

优先导入 Marine Engine Fault Dataset 的 `dataset_index.csv`、`variable_dictionary.csv` 和 15 个故障 CSV；把故障类别、负载、测点、单位和异常状态变成节点或属性。注意各类负载条件不一致（见 3.1），按负载匹配参考工况时会出现无法对齐的组合。UCI 和 TSRF 数据用来补充推进系统退化与燃烧室故障，Azimuth 数据补充推进器振动、润滑油与运维经济性维度。

### 第三步：从报告和中文语料抽取因果知识

把文本切分为带来源编号的段落，用规则、词典或大模型抽取三元组，例如：

```text
(连杆大端轴瓦失效)-[导致]->(主机停机)
(润滑油泄漏)-[接触]->(高温排气表面)
(高温排气表面)-[导致]->(机舱火灾)
(检查润滑油压力与金属碎屑)-[用于检查]->(轴承异常磨损)
```

每条关系必须保留报告文件名、页码和证据片段，避免大模型生成无法追溯的结论。可用 `05_metadata/inspect_pdf_pages.py PDF --pages 12,13 关键词` 快速定位并核对页级证据。MAIB 报告与 MAN/STAMFORD 技术公告的证据强度不同：前者是具体事件的调查结论，后者是厂商通用指导，建议在证据属性中区分 `evidence_type=accident_investigation / manufacturer_guidance / research_paper`。

### 第四步：建立混合检索和评价

1. 实体匹配：设备名、部件名、故障名及同义词。
2. 关键词检索：适合型号、报警码、部件名。
3. 语义检索：适合自然语言症状描述。
4. 图路径检索：沿"症状→故障→原因→措施"和"故障→影响→后果"检索。
5. 用标注问题计算 Recall@K、Precision@K、MRR，并调节各路检索权重和重排序。可直接复用 `HFACS_KG_main/analysis/compute_metrics.py`。

### 第五步：生成可解释诊断报告

给大模型的上下文只放入重排序后的证据，固定输出：故障判定、关键依据、因果链、建议检查、运维建议、来源证据和不确定性说明。

## 8. 校验与清单现状

**2026-09-28 整理时的校验结论**：

- 4 个数据集 ZIP、3 个代码 ZIP：全部可打开并完成解压。
- 大文件使用分片续传，并按服务器公布的 Content-Length 校验。
- 当时 12 个 PDF 可正常解析；另 1 篇有合法文件头但内部结构因下载中断损坏，已移入 `downloads_tmp/`。

**2026-10-06 复核后的实际状态（与上述结论不一致，需注意）**：

- **原始 ZIP 已不在磁盘上**：全目录递归搜索 `*.zip` 结果为 0。`sha256_manifest.csv` 的 20 条记录中有 7 条指向已不存在的 ZIP（4 个数据集 + 3 个代码包），因此**这 7 条哈希已无法用于验证**，仅 13 条 PDF 记录仍与磁盘文件对应。
- **哈希覆盖不完整**：`sha256_manifest.csv` 只登记了 8 份 MAIB 报告 + 4 篇论文 + 1 份损坏文件；另外 4 份 MAIB 报告（Queen Mary 2、Pride of Canterbury、Hebrides、Stena Europe）以及全部 MAN、STAMFORD、Frontiers 文档**没有 SHA-256 记录**。若后续要做完整性校验，需重新生成清单。
- **来源清单覆盖完整**：`source_manifest.csv`（23 条）+ `source_manifest_v3.csv`（16 条）合计覆盖 `02_reports/` 全部 27 个 PDF，无遗漏项。两份清单是先后两批下载的记录，`v3` 为扩充批，**不是** `source_manifest.csv` 的替代版本，合并使用时需注意 Hebrides 一篇在两批中的归类不同。
- **PDF 总数已增至 32**：`02_reports/` 27 + `03_papers/` 4 + `downloads_tmp/` 1。
- **解压残留**：`01_datasets/UCI_Naval_Propulsion_CBM/__MACOSX/` 含 3 个 macOS 元数据文件（`._.DS_Store`、`._Features.txt`、`._README.txt`），对建图无用，可安全删除；删除前建议确认无脚本按原路径遍历。

本次复核方式：递归枚举全部文件与扩展名统计、逐文件读取 `dataset_index.csv` 与各仓库 `README.md`、按清单逐条验证文件存在性。未对 PDF 做全文重新解析，页数沿用 `source_manifest_v3.csv` 的既有校验记录。

## 9. 重要边界

- 这些资料是"建图原料与方法参考"，不是已经完成的船舶动力故障知识图谱；不存在可直接导入 Neo4j 的成品节点/关系文件。
- 仿真数据不能冒充真实船舶故障数据；图谱中建议增加 `data_origin=simulation/experiment/field_report/manufacturer_guidance`。本包内 UCI 与 TSRF 为仿真，Marine Engine Fault Dataset 为实机试验，MAIB 为现场事故调查，MAN/STAMFORD 为厂商指导，Azimuth 为匿名化现场数据。
- 匿名化推进器数据不含受限的原始逐点 FFT，只有汇总级频谱特征与严重度评分。
- **许可分层**：CC BY 4.0（Marine Engine Fault Dataset、Azimuth 数据、Frontiers 论文、故障知识图谱论文）可自由使用但需署名；MIT（TSRF、HFACS-KG 代码、Azimuth 代码）可再分发；OGL v3.0（MAIB，第三方材料除外）需准确引用；**厂商版权（MAN 7 份、STAMFORD 7 份）仅限本地内部研究，禁止公开再分发完整 PDF**；**许可未明（RAG 语料、弱热故障仓库）与许可表述冲突（UCI）只能先做内部研究**，公开论文、演示系统或二次发布前必须逐条重新核验许可证和引用要求。
- 事故报告中的调查结论有具体船舶和事件背景，不能不加限定地推广为所有船型的确定性规则。
- Marine Engine Fault Dataset 的 Zenodo DOI 为预留状态，记录将在配套 Data Descriptor 论文接收后开放；引用前确认 DOI 是否已可解析。
- `Injector_Nozzle` 两个文件全程为异常段、无基线，不能用于需要"异常前 vs 异常"对照的分析；`Pump_Cavitation` 由吸入侧加压空气模拟，属"类气蚀"而非真实气蚀。

## 10. 本次修订记录（2026-10-06）

修订均基于对磁盘实际内容的逐目录核对，未改变任何数据文件。

1. **第 4 节重大更正**：原文称"报告均来自英国 MAIB"且只列出 8 份，实际 `02_reports/` 有 **27 个 PDF**，来自四类机构。已补全 4 份遗漏的 MAIB 报告（Queen Mary 2 2011、Pride of Canterbury 2015、Hebrides 2017、Stena Europe 2024），并新增 MAN 7 份、STAMFORD 7 份、Frontiers 1 份的完整清单，同时补充厂商文档"禁止公开再分发"的许可边界。
2. **第 8 节校验结论更正**：原文称 7 个 ZIP 已校验通过，实际 **ZIP 已全部不在磁盘上**，`sha256_manifest.csv` 中 7 条记录失效；并说明哈希清单只覆盖 13 个 PDF、来源清单需两份合并才完整。
3. **第 2 节目录结构更正**：补上真实嵌套层级（各数据集与代码仓库解压后多套一层同名目录）、`README_CN.md` 位于根目录而非 `05_metadata/`、`05_metadata/` 的 7 个文件逐一说明、`downloads_tmp/` 实际只剩 1 个损坏 PDF（原文"分片下载临时目录；当前下载已完成"已过时）。
4. **第 3 节数据集细化**：把"约 11.5 万条采样、约 70 个测量通道"替换为核对后的精确值（114,770 行；故障文件 73 列 = 3 个元信息列 + 70 个测量通道，参考文件 70 列）；新增 3.1 节纠正"每类故障都有 40/60/75/85 四档负载"的误解（Pump_Cavitation 仅 60/85%，Turbine_Degradation 无 75%，Injector_Nozzle 为阶梯/变负载程序）；补充三行表头、`dPf`/`dPex` 在 5 次试验中为空、6 个通道为原始电压信号、单位混用、加载代码、归一化脚本与引用要求；补充 Azimuth 的匿名化范围与 UCI 的 `__MACOSX/` 残留。
5. **第 6 节代码参考细化**：补充各仓库确切文件构成（TSRF 18 个文件、弱热故障 17 个 py + 1 个 csv、HFACS-KG 24 个文件）；补上原文遗漏的 `R006_causal_paths.py`、`R007_sensitivity_analyses.py`、`redraw_*` 与 `run_review.py`；明确 HFACS-KG 需自备 `kg_export/` 的 11 个 CSV、需 `DASHSCOPE_API_KEY`、29 类关键词正则的兜底占比，以及 IMO GISIS 报告受 Casualty Investigation Code 约束。
6. **第 5、9 节补充**：第 5 节改为表格并注明许可与损坏文件的处置方式；第 9 节新增按来源类型的许可分层、`data_origin` 取值建议扩充为四类、Zenodo DOI 预留状态提示，以及 Injector_Nozzle 无基线段与 Pump_Cavitation 为模拟气蚀两条数据使用限制。
