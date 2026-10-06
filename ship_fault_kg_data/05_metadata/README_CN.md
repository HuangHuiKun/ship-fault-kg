# 船舶动力系统故障知识图谱资料包

整理日期：2026-09-28  
保存位置：`D:\RAGQnASystem\RAGQnASystem-main\ship_fault_kg_data`

## 1. 这批资料能做什么

公开网络上几乎没有“下载后即可导入 Neo4j”的完整船舶动力系统故障知识图谱。本资料包因此按知识图谱构建流程收集了四类可用原料：

1. **实验与状态监测数据**：提供设备、工况、传感器、故障类别和异常状态。
2. **真实事故调查报告**：提供故障现象、原因、事件链、后果、处置和可追溯证据。
3. **论文**：提供故障分类、知识图谱本体、实体关系设计和诊断方法。
4. **代码、提示词和模式参考**：提供信息抽取、因果路径分析、评价和 GraphRAG 的实现参考。

推荐的核心图谱链路是：

`船舶/动力系统 → 设备 → 部件 → 工况 → 症状/传感器异常 → 故障 → 原因 → 影响 → 检查方法 → 运维措施 → 来源证据`

## 2. 目录结构

```text
ship_fault_kg_data/
├─ 01_datasets/             数据集及解压后的文件
├─ 02_reports/              官方事故调查和安全报告
├─ 03_papers/               论文
├─ 04_code_and_schemas/     开源代码、提示词和图谱模式参考
├─ 05_metadata/             本说明、来源清单、哈希和下载辅助脚本
└─ downloads_tmp/           分片下载临时目录；当前下载已完成
```

## 3. 数据集

| 优先级 | 本地内容 | 内容与规模 | 对知识图谱的价值 | 注意事项 |
|---|---|---|---|---|
| A | `Marine_Engine_Fault_Data_v1` | MU323DGSC 船用柴油机实机试验；参考工况和 5 类故障；约 11.5 万条采样、约 70 个测量通道、16 个主要 CSV | 可建立“故障—工况—传感器—异常表现”关系，并生成标准化诊断输入样例 | CC BY 4.0；CSV 为三行表头，异常文件与参考文件字段数不同 |
| A | `marine_diesel_RAG_corpus_All_data` | 1,275 篇中文 Markdown；train 1020、val 127、test 128 | 可做中文实体/关系抽取、向量检索、RAG 语料和故障术语词典 | Zenodo 页面未明确许可证；部分内容可能来自网络文章，仅建议内部科研，公开再分发前需逐条核验来源 |
| B | `Azimuth_Thruster_CBM_Dataset` | 拖轮方位推进系统匿名化振动、润滑油、可用性、诊断区间和经济性数据 | 可补充推进器、振动频谱、润滑油指标、故障提前量和运维决策关系 | 原始逐点 FFT 因保密未公开；公开数据 CC BY 4.0，代码 MIT |
| B | `UCI_Naval_Propulsion_CBM` | 11,934 条护卫舰燃气轮机推进仿真记录，16 个输入特征和压气机/涡轮退化系数 | 可建立“工况—部件退化—测量特征”的基线图谱和诊断测试集 | 当前 UCI 页面与压缩包内旧版说明的许可表述不一致；暂按科研使用，发表或商用前再次核验 |

下载来源：

- Marine Engine Fault Dataset：<https://zenodo.org/records/19857425>
- Marine diesel RAG corpus：<https://zenodo.org/records/20258638>
- Azimuth Thruster CBM Dataset：<https://zenodo.org/records/20101612>
- UCI Naval Propulsion CBM：<https://archive.ics.uci.edu/dataset/316/condition%2Bbased%2Bmaintenance%2Bof%2Bnaval%2Bpropulsion%2Bplants>

说明：RAG 语料 ZIP 使用旧式 GBK 文件名编码。下载包保持原样，解压目录已通过 `extract_legacy_zip_names.py` 恢复为正常中文文件名。

## 4. 官方事故调查和安全报告

报告均来自英国 Marine Accident Investigation Branch（MAIB），适合抽取可追溯的“故障—原因—事件—后果—建议”链。每个 PDF 已通过 `%PDF-` 文件头检查。

| 本地文件 | 重点内容 | 建议抽取 |
|---|---|---|
| `MAIB_2026_10_Kommandor_Susan_generator_bearing_failure.pdf` | 发电机轴承异常磨损、灾难性故障、火灾、全船失电和失去推进 | 轴承、非原厂备件、润滑/磨损、发电机、失电、推进丧失 |
| `MAIB_2026_06_Spirit_of_Discovery_propulsion_loss.pdf` | 大风浪中螺旋桨出水、超速保护停机、推进失效 | 海况、转速、保护逻辑、吊舱推进、人员后果 |
| `MAIB_2022_04_Wight_Sky_multiple_engine_failures.pdf` | 多台发动机灾难性失效、轴承咬死及维修监测问题 | 多故障关联、轴承、维护程序、状态监测 |
| `MAIB_2021_02_Finlandia_Seaways_connecting_rod_failure.pdf` | 连杆维护不当导致发动机失效和火灾 | 连杆、紧固/装配、维护错误、曲轴箱、火灾 |
| `MAIB_2018_14_Wight_Sky_engine_bearing_fire.pdf` | 主机轴承故障及火灾 | 轴承、润滑、温度、火灾、检查措施 |
| `MAIB_2018_01_Windcat8_bearing_failure_fire.pdf` | 连杆大端轴瓦失效及火灾 | 连杆、轴瓦、润滑、裂纹/磨损、火灾 |
| `MAIB_2016_Safety_Digest_generator_oil_fire.pdf` | 发电机润滑油喷到高温排气部件引发火灾 | 泄漏、高温表面、点火、隔热、检查 |
| `MAIB_2013_Safety_Digest_lubrication_bearing_cases.pdf` | 润滑与轴承损伤案例 | 润滑不足、污染、轴承损伤、预防措施 |

主要来源页：

- Kommandor Susan：<https://www.gov.uk/maib-reports/catastrophic-engine-failure-and-subsequent-fire-on-board-the-site-investigation-vessel-kommandor-susan>
- Finlandia Seaways：<https://www.gov.uk/maib-reports/engine-failure-and-subsequent-fire-on-ro-ro-cargo-vessel-finlandia-seaways-with-1-person-injured>
- Spirit of Discovery：<https://www.gov.uk/maib-reports/loss-of-propulsion-in-heavy-weather-experienced-by-the-passenger-vessel-spirit-of-discovery-leading-to-over-100-injuries-and-one-fatality>

MAIB 文本通常按英国 Open Government Licence v3.0 使用，但第三方图片或材料可能例外。使用时应准确引用报告标题、编号、年份和来源。

## 5. 论文

| 本地文件 | 用途 |
|---|---|
| `2025_Marine_Diesel_Fault_Knowledge_Graph.pdf` | 最直接的船用柴油机故障知识图谱参考：本体设计、BiLSTM-CRF 抽取、Neo4j 存储和故障因果展示 |
| `2026_Marine_Engine_Fault_Dataset.pdf` | 与实机故障数据集配套，理解试验平台、故障注入、变量和数据质量 |
| `2024_Survey_Data_Driven_Fault_Diagnosis_Marine_Diesel_Engines.pdf` | 梳理柴油机故障类别、数据来源、诊断算法和研究空白 |
| `downloads_tmp/invalid_2024_Data_Driven_Marine_Engine_Fault_Diagnosis.pdf` | 下载中断导致 PDF 内部损坏；已隔离，未用于图谱或论文分析 |
| `2018_Marine_Diesel_Engine_Failure_Simulator.pdf` | 柴油机故障模拟器、故障工况生成和特征变化参考 |

论文来源：

- 故障知识图谱：<https://doi.org/10.3390/jmse13040693>
- Marine Engine Fault Dataset：<https://arxiv.org/abs/2607.19444>
- 数据驱动综述：<https://arxiv.org/abs/2404.10363>
- 数据驱动诊断论文：<https://strathprints.strath.ac.uk/90777/>
- 故障模拟器：<https://zenodo.org/records/14620906>

## 6. 代码与模式参考

| 本地目录 | 可复用内容 | 限制 |
|---|---|---|
| `TSRF_main` | 6 类燃烧室状态 CSV、随机森林/SVM/KNN、SHAP 可解释诊断 | 数据主要来自热力仿真；代码 MIT |
| `Marine_weak_thermal_fault_main` | `Engine_dataset.csv` 和弱热故障诊断模型代码 | 仓库未见明确 LICENSE，暂仅科研参考 |
| `HFACS_KG_main` | 两阶段 LLM 抽取提示词、JSON Schema、因果路径脚本、评价指标和 GraphRAG 示例 | 不含原始 IMO GISIS 报告和最终知识图谱；代码 MIT |

来源：

- TSRF：<https://github.com/TS-RF/TSRF>
- Marine weak thermal fault diagnosis：<https://github.com/xiezaimi-png/Marine-diesel-engine-explainable-weak-thermal-fault-diagnosis>
- HFACS-KG：<https://github.com/yijie-sjtu/HFACS-KG>

## 7. 建议的使用顺序

### 第一步：先定图谱模式

参考 `2025_Marine_Diesel_Fault_Knowledge_Graph.pdf` 和 `HFACS_KG_main/prompts/`，先定义：

- 实体：船舶、系统、设备、部件、工况、传感器、症状、故障、原因、影响、检查、措施、报告、证据片段。
- 关系：属于、安装于、监测、表现为、指示、导致、影响、通过检查、建议措施、来源于。
- 证据属性：`source_id`、`document_title`、`page`、`quote_or_summary`、`year`、`confidence`。

### 第二步：用结构化数据建立基础节点

优先导入 Marine Engine Fault Dataset 的 `dataset_index.csv`、`variable_dictionary.csv` 和故障 CSV；把故障类别、负载、测点、单位和异常状态变成节点或属性。UCI 和 TSRF 数据用来补充推进系统退化与燃烧室故障。

### 第三步：从报告和中文语料抽取因果知识

把文本切分为带来源编号的段落，用规则、词典或大模型抽取三元组，例如：

```text
(连杆大端轴瓦失效)-[导致]->(主机停机)
(润滑油泄漏)-[接触]->(高温排气表面)
(高温排气表面)-[导致]->(机舱火灾)
(检查润滑油压力与金属碎屑)-[用于检查]->(轴承异常磨损)
```

每条关系必须保留报告文件名、页码和证据片段，避免大模型生成无法追溯的结论。

### 第四步：建立混合检索和评价

1. 实体匹配：设备名、部件名、故障名及同义词。
2. 关键词检索：适合型号、报警码、部件名。
3. 语义检索：适合自然语言症状描述。
4. 图路径检索：沿“症状→故障→原因→措施”和“故障→影响→后果”检索。
5. 用标注问题计算 Recall@K、Precision@K、MRR，并调节各路检索权重和重排序。

### 第五步：生成可解释诊断报告

给大模型的上下文只放入重排序后的证据，固定输出：故障判定、关键依据、因果链、建议检查、运维建议、来源证据和不确定性说明。

## 8. 校验结果

- 4 个数据集 ZIP：全部可打开并完成解压。
- 3 个代码 ZIP：全部可打开并完成解压。
- 12 个 PDF 可正常解析；另一篇虽有 PDF 文件头，但内部结构因下载中断而损坏，已移入 `downloads_tmp/invalid_...pdf`，未用于图谱。
- 大文件使用分片续传，并按服务器公布的 Content-Length 校验。
- `sha256_manifest.csv` 保存原始 ZIP/PDF 的 SHA-256，可用于以后确认文件没有损坏。

## 9. 重要边界

- 这些资料是“建图原料与方法参考”，不是已经完成的船舶动力故障知识图谱。
- 仿真数据不能冒充真实船舶故障数据；图谱中建议增加 `data_origin=simulation/experiment/field_report`。
- 匿名化推进器数据不含受限的原始逐点 FFT。
- 未明确许可的语料和代码只能先做内部研究；公开论文、演示系统或二次发布前，应再次核验许可证和引用要求。
- 事故报告中的调查结论有具体船舶和事件背景，不能不加限定地推广为所有船型的确定性规则。
