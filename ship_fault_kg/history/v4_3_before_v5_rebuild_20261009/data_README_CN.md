# 船舶动力系统故障知识图谱资料包

更新：2026-10-08；适用当前图谱V4.3。

> 原资料版权和再分发许可不因进入本资料包而改变。尤其中文转载语料和厂家资料需核实授权；见[免责声明](../DISCLAIMER.md)。

## 当前活动目录

| 目录 | 内容 | 建图作用 |
| --- | --- | --- |
| `01_datasets/Marine_Engine_Fault_Data_v1/` | Marine Engine Fault Dataset受控试验CSV、变量字典和元数据 | 试验工况、故障标签、15个核心测点；不是19起实船事故的来源 |
| `01_datasets/marine_diesel_RAG_corpus_All_data/All_data/` | 1275篇中文md：train1020、val127、test128 | 全量全文检索、候选关系审核、4篇文章的原文核对建图试点 |
| `02_reports/` | 26份官方事故报告、厂家通函及技术文档 | 事故事实、检查措施、参考机理与PDF页级溯源 |
| `03_papers/` | 5篇有效论文；本次加入电网振荡论文 | 本体与方法参考、实验解释、电网振荡观察；不能直接冒充实船确诊根因 |
| `04_code_and_schemas/` | TSRF、Marine weak thermal fault、HFACS-KG三份代码/模式资料 | TSRF健康状态知识；弱故障与抽取/GraphRAG设计参考。代码并非都已集成运行 |
| `05_metadata/` | 来源清单、原下载包SHA清单、下载脚本 | 核对出处与分类；构建程序依清单路径读取PDF |
| `downloads_tmp/` | 历史临时/损坏文件隔离目录 | 不作为图谱知识来源 |

原Azimuth Thruster CBM与UCI Naval Propulsion CBM已移到项目 `ship_fault_kg/history/v4_2_before_data_revision_20261008/removed_datasets/`，活动01_datasets只保留两类资料。不是不可恢复的物理销毁；历史资料不进入当前构建。

## 保留资料出处

- Marine Engine Fault Dataset：[Zenodo 19857425](https://zenodo.org/records/19857425)，DOI 10.5281/zenodo.19857425。
- Marine diesel intelligent operation and maintenance RAG corpus：[Zenodo 20258638](https://zenodo.org/records/20258638)。资料包下载入口不等于每篇转载文章的原始发表来源。
- 电网振荡论文：*Comparative Case Study on Oscillatory Behavior in Power Systems of Marine Vessels With High Power Converters*，[Frontiers论文入口](https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.529756/full)，DOI 10.3389/fenrg.2020.529756。
- TSRF：[TS-RF/TSRF](https://github.com/TS-RF/TSRF)。
- 弱热故障代码：[Marine diesel engine explainable weak thermal fault diagnosis](https://github.com/xiezaimi-png/Marine-diesel-engine-explainable-weak-thermal-fault-diagnosis)。
- HFACS-KG：[yijie-sjtu/HFACS-KG](https://github.com/yijie-sjtu/HFACS-KG)。

全部报告、手册、论文的具体标题和入口见 `05_metadata/source_manifest.csv` 与 `source_manifest_v3.csv`。历史ZIP清单中某些归档包已不存在活动目录，不能把下载时SHA清单理解为当前所有文件完整性证明；当前中文文章SHA见 `ship_fault_kg/output/corpus_inventory.json`。

## 中文语料怎么用于图谱

全部文章 → 全文分块 → 句子候选筛选 → 核对主客体、否定、因果强弱和机型 → 审核事实配置 → 图谱关系与证据。

当前全文索引覆盖全部1275篇，不再局限145篇；候选句不是图谱事实。4篇试点22条诊断关系已核对原文，但仍标为二次语料、待专家确认。不能将转载文章描述的船或事故当作已核实Case，也不能从试验数据标签自动推出机械因果链。

原train/val/test已全部参与知识检索，因此本项目后续独立评测必须另划分专家标注测试集。

## 移动论文后的路径

现在位置：`03_papers/Frontiers_2021_marine_converter_oscillations.pdf`。
文件内容不改；来源清单、下载脚本、PDF读取与页级检查程序已随之调整。文件名和原图谱证据ID保持稳定。

详细构建、运行、同步与恢复步骤见 [统一项目说明](../ship_fault_kg/README_CN.md)。修订前的完整资料说明保存在 `ship_fault_kg/history/v4_2_before_data_revision_20261008/data_README_CN.md`。
