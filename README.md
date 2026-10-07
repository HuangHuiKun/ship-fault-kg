# 船舶动力系统故障知识图谱

本目录保留船舶动力系统故障知识图谱的构建代码、原始资料和研究介绍材料。

- [构建、检索、评估与 Neo4j 使用说明](ship_fault_kg/README_CN.md)
- [资料包说明](ship_fault_kg_data/README_CN.md)
- `ship_fault_kg/output/`：当前V4.2的SQLite、GraphML、直接导入文件和评估结果；CSV仅按需生成
- [目录整理和归档索引](ship_fault_kg/FILE_LAYOUT.md)
- `ship_fault_kg/history/`：前几版本快照、旧查询、截图、评估及汇报材料；不用于当前默认导入
- [Git版本管理、更新与回退方法](VERSION_CONTROL.md)

生成诊断草稿时使用 Ollama 的 `qwen2.5:3b-instruct`。模型文件保存在 `D:\OllamaModels`，不在本目录的 `model/` 中。船舶图谱在 Neo4j Desktop 2 的 `ShipFaultKG` 实例、`shipfaultkg` 数据库中；HTTP 端口为 7474，Bolt 端口为 7687。
