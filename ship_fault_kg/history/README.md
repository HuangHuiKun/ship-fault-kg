# 历史版本与归档

当前默认版本是上一级的V4.2，主数据在`../output/ship_fault_kg.sqlite`。
history用于保存恢复依据，不是日常导入目录。

| 目录 | 含义 |
| --- | --- |
| `v1_20261004/` | 初始版本资料与产物 |
| `v2_before_fault_focus_20261005/` | 故障导向扩充前的V2快照 |
| `v3_before_redesign_20261006/` | 实体类型重设计前V3，当前回归测试读取其中SQLite |
| `v4_before_refinement_20261006/` | 船型精简和设备改名之前V4.0快照 |
| `v4_1_before_source_merge_20261006/` | Observation合并Source之前V4.1，当前测试和同步默认基线仍依赖此目录 |
| `docs_before_consolidation_20261005/` | 合并统一说明之前的旧README/REPORT文档 |
| `organization_20261007/` | 本次从当前目录移入的旧查询、旧产物、旧PPT、审核和维护材料 |

已有快照内部的文件、哈希和相对布局均未修改。不要随意删除V3或V4.1基线：它们被当前测试引用。
历史快照里仍可能重复保存更早产物，本次保留原样，避免破坏独立恢复。

本次归档的每个移动位置与完整性校验见 `organization_20261007/move_manifest.json`。
重复检查见 `organization_20261007/DUPLICATES.md`。
当前目录导航见 [文件组织说明](../FILE_LAYOUT.md)。

恢复旧知识数据不等于恢复Neo4j数据库。应在独立测试目录和空数据库验证，正式替换须先备份并审核差异。
不得把历史文件一股脑复制进当前output，或运行归档的旧修订脚本覆盖当前数据。
