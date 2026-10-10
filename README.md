# 船舶动力系统故障知识图谱

本目录保留船舶动力系统故障知识图谱的构建代码、原始资料和研究介绍材料。

> 公开科研仓库，非经认证的船舶诊断或控制产品。第三方资料保留原有权利；部分材料的再分发许可尚未核实，公开及本声明不构成授权。使用前请阅读[免责声明与第三方资料权利说明](DISCLAIMER.md)。

- [构建、检索、评估与 Neo4j 使用说明](ship_fault_kg/README_CN.md)
- [资料包说明](ship_fault_kg_data/README_CN.md)
- `ship_fault_kg/output/v5/`：当前V5的SQLite、JSONL、数据库快照、独立校验与逐边中文CSV；CSV随构建刷新
- [目录整理和归档索引](ship_fault_kg/FILE_LAYOUT.md)
- `ship_fault_kg/history/`：前几版本快照、旧查询、截图、评估及汇报材料；不用于当前默认导入
- [Git版本管理、更新与回退方法](VERSION_CONTROL.md)

V5默认入口是 `ship_fault_kg/manage_v5.py`。目前交付图谱与词法/同范围路径检索探针，尚未完成新版LLM联调；旧版生成演示已归档。原 Ollama 模型保存在 `D:\OllamaModels`，不在本目录的 `model/` 中。图谱在 Neo4j Desktop 2 的 `ShipFaultKG` 实例、`shipfaultkg` 数据库中；HTTP 端口为 7474，Bolt 端口为 7687。
