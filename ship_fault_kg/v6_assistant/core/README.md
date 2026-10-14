# V6 共用底层实现

本目录保存 V6 实际依赖的基础实现，由原 V5 的 build、preprocess、schema、curation、retrieve、neo4j 模块整理而来。
只修正 preprocess 的项目根路径与冻结基线输出路径；其余规则保持不变，避免目录整理改变图谱事实和旧对照实验。

- 原始 V5 完整代码：history/organization_v6_20261013/v5。
- 冻结 V5 数据：history/organization_v6_20261013/output/v5，仍是 V6 重建输入，不可删除。
- 当前 V6 构建入口：manage_v6.py；不要直接执行本目录中的旧 build.main 或 neo4j.main。
- V6 retrieve 外层包装器显式使用当前 V6 SQLite；旧诊断对照试验直接调用 core.retrieve，仍读取冻结 V5 SQLite。

这是复用底层代码，不是额外一套图谱，也不会在 output 下重新生成 V5。
