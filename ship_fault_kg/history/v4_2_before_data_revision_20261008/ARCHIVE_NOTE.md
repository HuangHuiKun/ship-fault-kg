# 2026-10-08资料修订前的V4.2可恢复归档

此目录不是当前运行入口，也不参与build.py的默认资料扫描。

- 根目录代码、配置、说明与output：修改前复制，保留V4.2图谱主数据。
- 05_metadata：修改前来源与下载清单。
- data_README_CN.md：修改前完整资料包说明。
- removed_datasets/Azimuth_Thruster_CBM_Dataset、UCI_Naval_Propulsion_CBM：本次从活动01_datasets移动到此，不是永久删除。
- neo4j_snapshot.json：同步前实时ShipKG节点、关系、属性和约束快照；不包含密码。
- intermediate_exports：本轮CSV受到占用时生成的中间备用表，不是V4.2基线快照。

恢复时须将代码、元数据、原数据目录与SQLite按版本配套恢复，再审核Neo4j同步差异。只把归档SQLite拷回后再次运行新版构建，会重新生成V4.3，因此不算完整恢复。

不要对未核验的数据库直接执行全库删除。当前修订记录见../../output/资料修订与语料建图报告_V4.3_20261008.md。
