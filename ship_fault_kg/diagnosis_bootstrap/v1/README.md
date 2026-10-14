# 初始诊断报告模板与开发数据集 v1.0

日期：2026-10-12。承接“深度学习诊断结果＋中间层物理量→规范化初始报告→知识检索”。

## 交付与规模

100份完整初始报告，五个子系统各20份：燃油与进排气、润滑与轴承、冷却与海水、传动与推进、电力与控制。
40个基础场景分别提供明确候选故障、仅描述症状两种表达，共80份。另有否定/正常、字段缺失、非唯一解释、精确参数证据不足各5份。

| 文件 | 用法 |
| --- | --- |
| [诊断报告模板.md](诊断报告模板.md) | 与师兄确认固定格式及字段语义 |
| [接口对接说明.md](接口对接说明.md) | 四项上游成果到本接口的字段映射与后续增强接口 |
| [样例报告_明确故障与症状配对.md](样例报告_明确故障与症状配对.md) | 先查看一组完整输入报告 |
| [初始诊断报告集_100份.md](初始诊断报告集_100份.md) | 所有报告阅读版；包含初始证据链，不包含图谱答案 |
| [数据集索引.md](数据集索引.md) | 按系统、题型及分区定位 |
| initial_reports.jsonl | 100份结构化上游报告 |
| initial_report.schema.json | JSON Schema；接口候选版本，不是船级社标准 |
| retrieval_inputs.jsonl | 只含report_id和diagnosis_text；直接送入检索器 |
| retrieval_reference_labels.jsonl | 单独保存目标概念、声明/段落/来源、候选路径及行为要求 |
| scenario_catalog.jsonl | 40个基础场景的设计和依据 |
| inputs_bootstrap_dev.jsonl / labels_bootstrap_dev.jsonl | 60份开发分区 |
| inputs_bootstrap_check.jsonl / labels_bootstrap_check.jsonl | 40份检查分区 |
| dataset_manifest.json / validation_report.json | 版本指纹、统计与自动校验 |
| baseline_v5.jsonl / baseline_summary.json | 原V5检索器的初始基线；由单独命令生成 |
| [基线结果与检索启动建议.md](基线结果与检索启动建议.md) | 基线解读、漏召回样本及20份边界样本的复核清单 |

## 样本依据与限制

所有报告、船舶编号、模型ID、工况、数值及分数均为助手构造的合成数据，不是历史事故记录、实测信号或已训练模型输出。数值只为测试接口和同基线趋势，不提供厂家阈值。中间层预测与仿真观测用channel_role分开；未提供的模型、分布、标准差、型号和厂家阈值使用null。不能将人工分数称为师兄的随机性约束置信度方法。

基础场景检索目标存在于当前V5，参考证据直接来自指定scope的实际声明，保留原文、定位、确定性和适用范围。场景症状和数值为假设性构造，来源只支持一般知识声明，不支持该合成船舶的观测数值。候选路径严格同scope、同source_id且方向一致，但仍未经过专家语义审查。

标签是部分、待复核的银标，不是独立专家金标准，也不是唯一或完整相关答案。仅症状报告可对应多种故障，预设目标只是用于测试能否找回该场景的一个参考概念。边界样本只标行为要求，不伪造相关事实集合。

60/40按基础场景分组，配对报告不会跨分区。边界样本仍复用了基础场景设备/表述，两分区存在来源重叠，因此检查集用于初步回归而非独立泛化评测。检索库中保留知识文档是正常的；未来需要新的人工编写问题、真实上游输出以及按来源/场景隔离的优化和锁定评测。

本批不用于估计实船故障发生率、诊断准确率、物理阈值或概率校准效果；不包含原始时序波形。固定字段名称尚需师兄确认，术语尚需后续与船级社文档核对。

## 立即开展检索

从项目根目录运行。只读调用retrieve函数，避免命令行逐题覆盖retrieval_example.json：

```powershell
python tools/build_diagnosis_bootstrap.py --validate
python tools/run_diagnosis_bootstrap_baseline.py --split bootstrap_dev
python tools/run_diagnosis_bootstrap_baseline.py --split all
```

在Python中：

```python
import json
from ship_fault_kg.v6_assistant.core.retrieve import retrieve
with open("ship_fault_kg/diagnosis_bootstrap/v1/retrieval_inputs.jsonl", encoding="utf-8") as f:
    for line in f:
        sample = json.loads(line)
        evidence_pack = retrieve(sample["diagnosis_text"], k=3)
        # 用report_id关联输出；参考标签只在评测端读取。
```

优先比较明确故障与症状配对的目标出现率、事实数量、参考声明找回情况；后者只能称“部分参考集合覆盖”，不能称完整Recall。否定/缺失/非唯一解释/参数证据不足需要单独人工检查。检索返回排除故障的条件性参考本身不一定错误，应检查后续是否把它写成肯定诊断。

## 与师兄的接口替换

1. 初始报告固定保留诊断结果、依据物理量、诊断置信度、初步诊断溯源四个核心部分。
2. 他提供真实或仿真模型输出后，替换upstream_model、physical_quantities和diagnosis，保留缺失信息及否定。
3. 随机性约束方法落地后填入confidence.method/method_version/stochastic_constraint_result，保留校准状态，避免检索分数覆盖模型分数。
4. 你负责检索参考机理、检查/措施和出处；增强报告追加这些内容，并明确适用条件及未证实部分。
5. 如将数据用于生成模型训练，应另建真正独立的测试集，不继续把本批检查分区当最终评测。

## 可复现生成

```powershell
python tools/build_diagnosis_bootstrap.py
```

生成器只读V5 SQLite，输出到本目录；不更新图谱和Neo4j。重新生成会刷新本目录固定交付文件，人工标注修订请另存新版本。

本次知识图谱SQLite SHA256：`40390f5a8935690c6d811ded89ed49b00ba8566ddaed47dd903210856158c218`。
