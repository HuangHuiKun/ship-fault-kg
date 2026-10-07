# 文件重复检查（2026-10-07）

检查 548 个文件，发现 116 组内容完全相同的文件，额外副本 289 份。

按字节长度与 SHA256 判定；不按文件名判断。缓存目录和本次自动生成的清单不参与统计。
未删除任何重复文件：历史快照中的副本保留，以便独立恢复。理论冗余字节数不是可安全删除容量。
特别注意：`entity_inventory_v3 copy.md` 与 `entity_inventory_v3.md` 内容不同，不能当作重复文件删除。

## 完全重复组

### 1. 6 份，16777 字节

SHA256：`00d348cf8bbcbd504c13e7af4370b107745233902a1a296fc3f9147d3e88f3ee`

- `curated_cases.py`
- `history/v1_20261004/curated_cases.py`
- `history/v2_before_fault_focus_20261005/curated_cases.py`
- `history/v3_before_redesign_20261006/curated_cases.py`
- `history/v4_1_before_source_merge_20261006/curated_cases.py`
- `history/v4_before_refinement_20261006/curated_cases.py`

### 2. 3 份，78864 字节

SHA256：`01001c2fc270243d835dbcff1e2f7dff9811e642e16ff8d4e326a91344a755f8`

- `history/organization_20261007/v1_artifacts/output/v1_legacy/evidence.csv`
- `history/v1_20261004/output/evidence.csv`
- `history/v2_before_fault_focus_20261005/output/v1_legacy/evidence.csv`

### 3. 2 份，19462 字节

SHA256：`05e2f36b9398175e0aa735de80fc8e613d1e348acf9ba88b1b0994fbb11d8c0d`

- `history/organization_20261007/v2_artifacts/output/eval_queries_v2.json`
- `history/v2_before_fault_focus_20261005/output/eval_queries_v2.json`

### 4. 3 份，15185 字节

SHA256：`06678c5f20e0fb7b38aa1cc5368fbbfaa18f7c622d357f93dc897ea31160952c`

- `history/v4_1_before_source_merge_20261006/output/retrieval_evaluation_v4.json`
- `history/v4_before_refinement_20261006/output/retrieval_evaluation_v4.json`
- `output/retrieval_evaluation_v4.json`

### 5. 4 份，296 字节

SHA256：`0f95308d1541458db997282d816801f172c198386720445482104fdb0904fb92`

- `history/organization_20261007/sensor_maintenance/output/neo4j_sensor_archive_v3.cypher`
- `history/organization_20261007/sensor_maintenance/output/neo4j_sensor_cleanup_v3.cypher`
- `history/organization_20261007/sensor_maintenance/output/neo4j_sensor_preview_v3.cypher`
- `history/organization_20261007/sensor_maintenance/output/neo4j_sensor_unarchive_v3.cypher`

### 6. 2 份，186221 字节

SHA256：`1339154abb0e11c62b861c917425df8d824634681b577220850347a7d01c729d`

- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/final-slide-04.png`
- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/slide-04.png`

### 7. 2 份，127952 字节

SHA256：`135836bb1b8b352f678d441f6e2b0e6916060763308cec36c33e433800fa1301`

- `history/organization_20261007/v2_artifacts/output/entity_inventory_v2.md`
- `history/organization_20261007/v3_artifacts/output/entity_inventory_v3.md`

### 8. 5 份，907 字节

SHA256：`14e530d0e5c800aa6b3942c03697a36a3083ed769a901f9b05552ccfbe0af4a6`

- `serve_output.py`
- `history/v2_before_fault_focus_20261005/serve_output.py`
- `history/v3_before_redesign_20261006/serve_output.py`
- `history/v4_1_before_source_merge_20261006/serve_output.py`
- `history/v4_before_refinement_20261006/serve_output.py`

### 9. 3 份，3114 字节

SHA256：`1749d6583387116b277ce3fb04f7f53553a1e2d0237d6cf96461b45727aac833`

- `evaluate_fault_v3.py`
- `history/v4_1_before_source_merge_20261006/evaluate_fault_v3.py`
- `history/v4_before_refinement_20261006/evaluate_fault_v3.py`

### 10. 4 份，59182 字节

SHA256：`1ecda155496bbc81168eaf0213e13ea30a23d077d37d0f17f7b8bbd7aefa043d`

- `history/organization_20261007/v3_artifacts/output/neo4j_v3_scuffing.jpg`
- `history/v3_before_redesign_20261006/output/neo4j_v3_scuffing.jpg`
- `history/v4_1_before_source_merge_20261006/output/neo4j_v3_scuffing.jpg`
- `history/v4_before_refinement_20261006/output/neo4j_v3_scuffing.jpg`

### 11. 2 份，5235 字节

SHA256：`203f3f7190712cc5a899342375b5c188e9cef2811a406e8f8c409130b30de7a1`

- `history/organization_20261007/v2_artifacts/output/shipkg_v2.grass`
- `history/organization_20261007/v3_artifacts/output/shipkg_v3.grass`

### 12. 2 份，114365 字节

SHA256：`217d10dc75e3111235a797885916f010f87aa117a5f139eabc69c29dae7e2047`

- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/final-slide-05.png`
- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/slide-05.png`

### 13. 3 份，6957 字节

SHA256：`21d37fbd8050d5707948497cd8221721947ad4a5bb44b132fa42570224dc08ae`

- `generate_demo.py`
- `history/v4_1_before_source_merge_20261006/generate_demo.py`
- `history/v4_before_refinement_20261006/generate_demo.py`

### 14. 12 份，293 字节

SHA256：`25053806acee8c3b5f33d11a0b9982fcaa7fad3e68508b1609f095593f0bc219`

- `history/v3_before_redesign_20261006/output/neo4j_sensor_archive_v3.cypher`
- `history/v3_before_redesign_20261006/output/neo4j_sensor_cleanup_v3.cypher`
- `history/v3_before_redesign_20261006/output/neo4j_sensor_preview_v3.cypher`
- `history/v3_before_redesign_20261006/output/neo4j_sensor_unarchive_v3.cypher`
- `history/v4_1_before_source_merge_20261006/output/neo4j_sensor_archive_v3.cypher`
- `history/v4_1_before_source_merge_20261006/output/neo4j_sensor_cleanup_v3.cypher`
- `history/v4_1_before_source_merge_20261006/output/neo4j_sensor_preview_v3.cypher`
- `history/v4_1_before_source_merge_20261006/output/neo4j_sensor_unarchive_v3.cypher`
- `history/v4_before_refinement_20261006/output/neo4j_sensor_archive_v3.cypher`
- `history/v4_before_refinement_20261006/output/neo4j_sensor_cleanup_v3.cypher`
- `history/v4_before_refinement_20261006/output/neo4j_sensor_preview_v3.cypher`
- `history/v4_before_refinement_20261006/output/neo4j_sensor_unarchive_v3.cypher`

### 15. 4 份，40751 字节

SHA256：`26799eb190a0fa6f2ca66de476c2d94daa4c77a7e3ec7e75256d2a8dc8c91908`

- `history/organization_20261007/v3_artifacts/output/neo4j_v3_archive.jpg`
- `history/v3_before_redesign_20261006/output/neo4j_v3_archive.jpg`
- `history/v4_1_before_source_merge_20261006/output/neo4j_v3_archive.jpg`
- `history/v4_before_refinement_20261006/output/neo4j_v3_archive.jpg`

### 16. 2 份，18045 字节

SHA256：`28b1a38cc65cbc09b811f8b26b50568e1c0408a4c32072b8685cfee18616d590`

- `history/docs_before_consolidation_20261005/REPORT_KG_V2_UPGRADE_CN.md`
- `history/v2_before_fault_focus_20261005/REPORT_KG_V2_UPGRADE_CN.md`

### 17. 3 份，35375 字节

SHA256：`28ececd6007d4a492e65df321a249f02af7441bcd69c3ed9edde9d1f9d07c058`

- `history/organization_20261007/v1_artifacts/output/v1_legacy/nodes.csv`
- `history/v1_20261004/output/nodes.csv`
- `history/v2_before_fault_focus_20261005/output/v1_legacy/nodes.csv`

### 18. 2 份，18387 字节

SHA256：`29a37951aa0117ca3ab60c84e5052aad3a45d1dba1e12c2050c5c343da9fce48`

- `history/organization_20261007/v2_artifacts/output/demo_v2_cpp.json`
- `history/v2_before_fault_focus_20261005/output/demo_v2_cpp.json`

### 19. 3 份，7253 字节

SHA256：`2a54df52dab5ea2532062feea30b55826609dfbeb6781b696b94f409fd335aeb`

- `history/v3_before_redesign_20261006/output/shipkg_v2_json.grass`
- `history/v4_1_before_source_merge_20261006/output/shipkg_v2_json.grass`
- `history/v4_before_refinement_20261006/output/shipkg_v2_json.grass`

### 20. 2 份，5728 字节

SHA256：`2e61c7450205c7c74e8f4339918fa7ce905e072e2bed8958edca3e6d85cbbd6c`

- `history/docs_before_consolidation_20261005/README_CN.md`
- `history/docs_before_consolidation_20261005/README_ORIGINAL_WORKING_COPY.md`

### 21. 6 份，10990 字节

SHA256：`32ef274b50cade1bfb50e7d98ff23b0e348ad63d5239e5c2dc72bb5d61101fdb`

- `history/v3_before_redesign_20261006/output/fault_retrieval_evaluation_v3.json`
- `history/v4_1_before_source_merge_20261006/output/fault_retrieval_evaluation_v3.json`
- `history/v4_1_before_source_merge_20261006/output/fault_retrieval_evaluation_v4.json`
- `history/v4_before_refinement_20261006/output/fault_retrieval_evaluation_v3.json`
- `history/v4_before_refinement_20261006/output/fault_retrieval_evaluation_v4.json`
- `output/fault_retrieval_evaluation_v4.json`

### 22. 4 份，266266 字节

SHA256：`36e31fdb216824035452c70f609dbe91e6bfaf8a4b938c2299d10dad9631d019`

- `history/organization_20261007/source_review/output/source_review_v3/STAMFORD_AGN039_marine_shaft_generators_page2.png`
- `history/v3_before_redesign_20261006/output/source_review_v3/STAMFORD_AGN039_marine_shaft_generators_page2.png`
- `history/v4_1_before_source_merge_20261006/output/source_review_v3/STAMFORD_AGN039_marine_shaft_generators_page2.png`
- `history/v4_before_refinement_20261006/output/source_review_v3/STAMFORD_AGN039_marine_shaft_generators_page2.png`

### 23. 6 份，40263 字节

SHA256：`3727bb846cd578c5855e8d8f7bad4e5b608029b78746cadb95800617fc2b9672`

- `history/organization_20261007/v1_artifacts/output/v1_legacy/neo4j_admin_import/nodes_admin.csv`
- `history/v1_20261004/output/neo4j_admin_import/nodes_admin.csv`
- `history/v2_before_fault_focus_20261005/output/v1_legacy/neo4j_admin_import/nodes_admin.csv`
- `history/v3_before_redesign_20261006/output/v1_legacy/neo4j_admin_import/nodes_admin.csv`
- `history/v4_1_before_source_merge_20261006/output/v1_legacy/neo4j_admin_import/nodes_admin.csv`
- `history/v4_before_refinement_20261006/output/v1_legacy/neo4j_admin_import/nodes_admin.csv`

### 24. 2 份，3912648 字节

SHA256：`37cdc8989515033bbab2b8c4d0dd30fdf98cacf80605d846e7fea5d80aed0917`

- `history/organization_20261007/v2_artifacts/output/graph_inventory_v2.json`
- `history/organization_20261007/v3_artifacts/output/graph_inventory_v3.json`

### 25. 3 份，1374234 字节

SHA256：`3a8de47c782781f656dc1b95ea90fbd4778684039cfb71f940a9c97542f66b6e`

- `history/v3_before_redesign_20261006/output/v1_legacy/passages.csv`
- `history/v4_1_before_source_merge_20261006/output/v1_legacy/passages.csv`
- `history/v4_before_refinement_20261006/output/v1_legacy/passages.csv`

### 26. 6 份，61391 字节

SHA256：`3ef6d358044f451ef67af355740795e19bd3cfd20afb66552546de2b9d6f6571`

- `history/organization_20261007/v3_artifacts/output/ollama_shipkg.stderr.log`
- `history/v1_20261004/output/ollama_shipkg.stderr.log`
- `history/v2_before_fault_focus_20261005/output/ollama_shipkg.stderr.log`
- `history/v3_before_redesign_20261006/output/ollama_shipkg.stderr.log`
- `history/v4_1_before_source_merge_20261006/output/ollama_shipkg.stderr.log`
- `history/v4_before_refinement_20261006/output/ollama_shipkg.stderr.log`

### 27. 5 份，4495 字节

SHA256：`456083d8175c58917332bf4734dae6f179594b9733fa6b6acc300b79316bc480`

- `eval_queries.json`
- `history/v1_20261004/eval_queries.json`
- `history/v2_before_fault_focus_20261005/eval_queries.json`
- `history/v4_1_before_source_merge_20261006/eval_queries.json`
- `history/v4_before_refinement_20261006/eval_queries.json`

### 28. 3 份，133173 字节

SHA256：`4919ff63a9b57a86ccd8a3aecfeb4c813f49f4ffe81f16995ec472b5582d76b5`

- `history/v3_before_redesign_20261006/output/maintenance_20261005/deleted_sensors_backup.json`
- `history/v4_1_before_source_merge_20261006/output/maintenance_20261005/deleted_sensors_backup.json`
- `history/v4_before_refinement_20261006/output/maintenance_20261005/deleted_sensors_backup.json`

### 29. 2 份，150546 字节

SHA256：`4a0794cd5f39be6bc7b16cae5ab0df84128873635afa81355dc5c2f284ba70b1`

- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/final-slide-07.png`
- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/slide-07.png`

### 30. 2 份，147921 字节

SHA256：`4bc694d627f20d1a2d1c7ee056565d39c34ffcb77c49fb58cb54037c9e11d29b`

- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/final-slide-03.png`
- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/slide-03.png`

### 31. 3 份，2286 字节

SHA256：`4d31f567c7ca435fd8f07aedad56794e6b9c3fafc277696da9f12b79e227d8b0`

- `history/v3_before_redesign_20261006/output/demo_v2_cpp.md`
- `history/v4_1_before_source_merge_20261006/output/demo_v2_cpp.md`
- `history/v4_before_refinement_20261006/output/demo_v2_cpp.md`

### 32. 5 份，2306 字节

SHA256：`4e1a00dd5973e3afb89f6eba60165fd02aa7cedf02de739195a9995c2a2cbce0`

- `history/organization_20261007/v2_artifacts/output/viewer_verification_v2.json`
- `history/v2_before_fault_focus_20261005/output/viewer_verification_v2.json`
- `history/v3_before_redesign_20261006/output/viewer_verification_v2.json`
- `history/v4_1_before_source_merge_20261006/output/viewer_verification_v2.json`
- `history/v4_before_refinement_20261006/output/viewer_verification_v2.json`

### 33. 3 份，2538 字节

SHA256：`51d381af3ae0525c3700029d0ae28586dcfbc36dee89327e20f6f2de12d4bff2`

- `history/v3_before_redesign_20261006/output/v1_legacy/demo_kg_rag_report.md`
- `history/v4_1_before_source_merge_20261006/output/v1_legacy/demo_kg_rag_report.md`
- `history/v4_before_refinement_20261006/output/v1_legacy/demo_kg_rag_report.md`

### 34. 3 份，18816 字节

SHA256：`5205c2f4e3e660cb453946bd258443c6fc54e317488df2e9fec24155a10eb66f`

- `history/v4_1_before_source_merge_20261006/output/eval_queries_v4.json`
- `history/v4_before_refinement_20261006/output/eval_queries_v4.json`
- `output/eval_queries_v4.json`

### 35. 3 份，2569 字节

SHA256：`52c98164555c7a48237164541e672e049405e1766bfd6b746985cac29bc2b878`

- `history/organization_20261007/v1_artifacts/output/v1_legacy/demo_kg_rag_report.md`
- `history/v1_20261004/output/demo_kg_rag_report.md`
- `history/v2_before_fault_focus_20261005/output/v1_legacy/demo_kg_rag_report.md`

### 36. 3 份，109969 字节

SHA256：`52e3270b6b37d7c3f3f3244cfdf4d5b986f28c545ca66384fa0051c961616053`

- `history/v3_before_redesign_20261006/output/retrieval_examples_v3.json`
- `history/v4_1_before_source_merge_20261006/output/retrieval_examples_v3.json`
- `history/v4_before_refinement_20261006/output/retrieval_examples_v3.json`

### 37. 3 份，21728 字节

SHA256：`567d1dbbc2f05c6bc27654e92034439df1b5f4fc124a96ec6da96f4617303e77`

- `retrieve.py`
- `history/v4_1_before_source_merge_20261006/retrieve.py`
- `history/v4_before_refinement_20261006/retrieve.py`

### 38. 4 份，6923 字节

SHA256：`5ffba21b8f0490885a20e108ef5d196cfaffca34e2ffa2d21de6b13c955bb763`

- `download_fault_sources.py`
- `history/v3_before_redesign_20261006/download_fault_sources.py`
- `history/v4_1_before_source_merge_20261006/download_fault_sources.py`
- `history/v4_before_refinement_20261006/download_fault_sources.py`

### 39. 4 份，44881 字节

SHA256：`65291171056fb05a8b9630a70ba87c2038f4009ea09b7482d958913b7f02ac1c`

- `history/organization_20261007/connection_maintenance/output/neo4j_connection_repair_20261005/browser_connected.png`
- `history/v3_before_redesign_20261006/output/neo4j_connection_repair_20261005/browser_connected.png`
- `history/v4_1_before_source_merge_20261006/output/neo4j_connection_repair_20261005/browser_connected.png`
- `history/v4_before_refinement_20261006/output/neo4j_connection_repair_20261005/browser_connected.png`

### 40. 3 份，13994 字节

SHA256：`6c34c604548a6dd2d915b79421fe69505be3b3878a474af21ac7015769ee4ce9`

- `visualize_graph.py`
- `history/v4_1_before_source_merge_20261006/visualize_graph.py`
- `history/v4_before_refinement_20261006/visualize_graph.py`

### 41. 3 份，8041 字节

SHA256：`6cc7b15199ccec6c6125eb429cd2597dbcd9feb323481a1397da5b202dd8690f`

- `history/v3_before_redesign_20261006/purge_archived_sensors.py`
- `history/v4_1_before_source_merge_20261006/purge_archived_sensors.py`
- `history/v4_before_refinement_20261006/purge_archived_sensors.py`

### 42. 3 份，35140 字节

SHA256：`6ed92e588912f2938115f08774fad3e175cd083e19458ece7667569c2d10ee00`

- `history/v3_before_redesign_20261006/output/v1_legacy/nodes.csv`
- `history/v4_1_before_source_merge_20261006/output/v1_legacy/nodes.csv`
- `history/v4_before_refinement_20261006/output/v1_legacy/nodes.csv`

### 43. 4 份，55546 字节

SHA256：`7798b81e7c1f847e735145dd905cb2969db504583083c84d5d579b13caeb4327`

- `history/organization_20261007/sensor_maintenance/output/maintenance_20261005/neo4j_colors.png`
- `history/v3_before_redesign_20261006/output/maintenance_20261005/neo4j_colors.png`
- `history/v4_1_before_source_merge_20261006/output/maintenance_20261005/neo4j_colors.png`
- `history/v4_before_refinement_20261006/output/maintenance_20261005/neo4j_colors.png`

### 44. 3 份，78692 字节

SHA256：`7b68f9663c155ed357e70c8b227252c62a5faa006cb4b2a2e6065abd6b1abea7`

- `history/v3_before_redesign_20261006/output/v1_legacy/evidence.csv`
- `history/v4_1_before_source_merge_20261006/output/v1_legacy/evidence.csv`
- `history/v4_before_refinement_20261006/output/v1_legacy/evidence.csv`

### 45. 4 份，127354 字节

SHA256：`7c8ea0df50ae5a9e9b1a134706980c9363a9f566cdb301fd20c282afd9fc67b5`

- `history/organization_20261007/v3_artifacts/output/entity_inventory_v3 copy.md`
- `history/v3_before_redesign_20261006/output/entity_inventory_v3 copy.md`
- `history/v4_1_before_source_merge_20261006/output/entity_inventory_v3 copy.md`
- `history/v4_before_refinement_20261006/output/entity_inventory_v3 copy.md`

### 46. 4 份，441 字节

SHA256：`7d06a9304f59af9ff163f082ce4cf4e7c45eb5e79773fe0aa0777a45ddf2b56a`

- `history/organization_20261007/sensor_maintenance/output/sensor_cleanup_guide_v3.html`
- `history/v3_before_redesign_20261006/output/sensor_cleanup_guide_v3.html`
- `history/v4_1_before_source_merge_20261006/output/sensor_cleanup_guide_v3.html`
- `history/v4_before_refinement_20261006/output/sensor_cleanup_guide_v3.html`

### 47. 3 份，18897 字节

SHA256：`7e07d44a3c1f7950a9e573d0356ad4601ccfe0d0e9f8cf3e03e2e3bf4337077f`

- `history/v3_before_redesign_20261006/output/v1_legacy/demo_kg_rag_report.json`
- `history/v4_1_before_source_merge_20261006/output/v1_legacy/demo_kg_rag_report.json`
- `history/v4_before_refinement_20261006/output/v1_legacy/demo_kg_rag_report.json`

### 48. 2 份，2317 字节

SHA256：`801e24b6557dc5a1e007db9c99322f1ffd19c8219b6c6700fff8a46bd36e0c91`

- `history/organization_20261007/v2_artifacts/output/demo_v2_cpp.md`
- `history/v2_before_fault_focus_20261005/output/demo_v2_cpp.md`

### 49. 4 份，40286 字节

SHA256：`8090c7f099237b7769c4211d1d135a69fb9691548ef08f1e2a2595474fd2e851`

- `history/organization_20261007/v3_artifacts/output/neo4j_v3_counts.jpg`
- `history/v3_before_redesign_20261006/output/neo4j_v3_counts.jpg`
- `history/v4_1_before_source_merge_20261006/output/neo4j_v3_counts.jpg`
- `history/v4_before_refinement_20261006/output/neo4j_v3_counts.jpg`

### 50. 3 份，15211 字节

SHA256：`8243e346c3e02c32b188fe355c779460c888b66561164844045d076b891cc8d4`

- `history/v3_before_redesign_20261006/output/retrieval_evaluation_lexical.json`
- `history/v4_1_before_source_merge_20261006/output/retrieval_evaluation_lexical.json`
- `history/v4_before_refinement_20261006/output/retrieval_evaluation_lexical.json`

### 51. 3 份，2630 字节

SHA256：`826f3d9a46d972caeea89cd57fc1a1fa94010e21808fc0a6218f07d50a987965`

- `history/organization_20261007/legacy_tools/queries_v3.cypher`
- `history/v4_1_before_source_merge_20261006/queries_v3.cypher`
- `history/v4_before_refinement_20261006/queries_v3.cypher`

### 52. 2 份，2151384 字节

SHA256：`82d01bfd30cfb76adeb9b1b3ad788ea417569818028f2bb8f78ac66333bd79bf`

- `history/v4_before_refinement_20261006/neo4j_snapshot.json`
- `history/v4_before_refinement_20261006/output/neo4j_snapshot_v4.json`

### 53. 5 份，34708 字节

SHA256：`82f76ebe40cd9b80d36a2368e7aed450d35e6b622d11a70354ed4789056f85db`

- `expanded_cases.py`
- `history/v2_before_fault_focus_20261005/expanded_cases.py`
- `history/v3_before_redesign_20261006/expanded_cases.py`
- `history/v4_1_before_source_merge_20261006/expanded_cases.py`
- `history/v4_before_refinement_20261006/expanded_cases.py`

### 54. 5 份，38191 字节

SHA256：`83e426eff13af448fc609cb222d2002891695a4ad47b265e6867c75e3c38e136`

- `history/organization_20261007/v2_artifacts/output/neo4j_v2_graph.jpg`
- `history/v2_before_fault_focus_20261005/output/neo4j_v2_graph.jpg`
- `history/v3_before_redesign_20261006/output/neo4j_v2_graph.jpg`
- `history/v4_1_before_source_merge_20261006/output/neo4j_v2_graph.jpg`
- `history/v4_before_refinement_20261006/output/neo4j_v2_graph.jpg`

### 55. 3 份，18713 字节

SHA256：`86e57ed60440a702af2c189d7e547a046e5f120a6c2e2a21972de14b9d740c5f`

- `history/v3_before_redesign_20261006/output/eval_queries_v2.json`
- `history/v4_1_before_source_merge_20261006/output/eval_queries_v2.json`
- `history/v4_before_refinement_20261006/output/eval_queries_v2.json`

### 56. 3 份，15183 字节

SHA256：`8b088c3d128b47d4bd8c2c9c64b81e4781956d5f74a0e58a36fb2ff05f5c1d08`

- `history/v3_before_redesign_20261006/output/retrieval_evaluation.json`
- `history/v4_1_before_source_merge_20261006/output/retrieval_evaluation.json`
- `history/v4_before_refinement_20261006/output/retrieval_evaluation.json`

### 57. 5 份，3004 字节

SHA256：`8b3ea39d1498f8ab6081e600a82996b8c086d80883c41dd8dd782e8ad8c1cb3e`

- `eval_cases_v2.py`
- `history/v2_before_fault_focus_20261005/eval_cases_v2.py`
- `history/v3_before_redesign_20261006/eval_cases_v2.py`
- `history/v4_1_before_source_merge_20261006/eval_cases_v2.py`
- `history/v4_before_refinement_20261006/eval_cases_v2.py`

### 58. 3 份，677 字节

SHA256：`8c0ce9ad130721957df41c7f7b416ee71447a1e3234d55a2dbbb358b00391560`

- `history/v3_before_redesign_20261006/output/maintenance_20261005/purge_receipt.json`
- `history/v4_1_before_source_merge_20261006/output/maintenance_20261005/purge_receipt.json`
- `history/v4_before_refinement_20261006/output/maintenance_20261005/purge_receipt.json`

### 59. 4 份，41204 字节

SHA256：`8c8a825e293ee9488c9aeb3a185552927dcbdf6204d0b3443981094fd822ed96`

- `history/organization_20261007/connection_maintenance/output/neo4j_connection_repair_20261005/neo4j.conf.before_desktop_url_fix`
- `history/v3_before_redesign_20261006/output/neo4j_connection_repair_20261005/neo4j.conf.before_desktop_url_fix`
- `history/v4_1_before_source_merge_20261006/output/neo4j_connection_repair_20261005/neo4j.conf.before_desktop_url_fix`
- `history/v4_before_refinement_20261006/output/neo4j_connection_repair_20261005/neo4j.conf.before_desktop_url_fix`

### 60. 4 份，3330 字节

SHA256：`911d55d99ae664f9f697628ee0281b45280ada53ce4fbc82e9aa8c670ab89357`

- `history/organization_20261007/legacy_tools/verify_v3.py`
- `history/v3_before_redesign_20261006/verify_v3.py`
- `history/v4_1_before_source_merge_20261006/verify_v3.py`
- `history/v4_before_refinement_20261006/verify_v3.py`

### 61. 5 份，139164 字节

SHA256：`92d333cf07defad3133037240b8b0ab833f506ff7d403802d43c16c2db0d8aed`

- `history/organization_20261007/v2_artifacts/output/viewer_v2_evidence.jpg`
- `history/v2_before_fault_focus_20261005/output/viewer_v2_evidence.jpg`
- `history/v3_before_redesign_20261006/output/viewer_v2_evidence.jpg`
- `history/v4_1_before_source_merge_20261006/output/viewer_v2_evidence.jpg`
- `history/v4_before_refinement_20261006/output/viewer_v2_evidence.jpg`

### 62. 3 份，363065 字节

SHA256：`9413a60b20752c0f3b94f7166d726a05247ba635930ef30b1d70fd9c6ac4e9e2`

- `history/v3_before_redesign_20261006/output/new_source_pages_v3.json`
- `history/v4_1_before_source_merge_20261006/output/new_source_pages_v3.json`
- `history/v4_before_refinement_20261006/output/new_source_pages_v3.json`

### 63. 3 份，12468 字节

SHA256：`94175dd68c3f502f4b6a1cab27398c6e0b15e0d9e24040560ff99c139c1ff6c6`

- `history/v3_before_redesign_20261006/output/revision_changes_v3.json`
- `history/v4_1_before_source_merge_20261006/output/revision_changes_v3.json`
- `history/v4_before_refinement_20261006/output/revision_changes_v3.json`

### 64. 3 份，172 字节

SHA256：`9446e498af3a6662e6aac346160857c736b39b94e8f20855c8e430c6dda24280`

- `history/v3_before_redesign_20261006/output/source_anchor_audit_v3.json`
- `history/v4_1_before_source_merge_20261006/output/source_anchor_audit_v3.json`
- `history/v4_before_refinement_20261006/output/source_anchor_audit_v3.json`

### 65. 2 份，2101 字节

SHA256：`958a3b19e680efb9ef6265f6e79735a51298dceb91a705461a9957d6ef27a9e9`

- `history/v2_before_fault_focus_20261005/export_graphml.py`
- `history/v3_before_redesign_20261006/export_graphml.py`

### 66. 3 份，2130 字节

SHA256：`981f5ca79a3d7c9884c7c8cf41dc3c88366d58fc40210ffd2071d1075d59f523`

- `history/v3_before_redesign_20261006/output/demo_v3_scuffing.md`
- `history/v4_1_before_source_merge_20261006/output/demo_v3_scuffing.md`
- `history/v4_before_refinement_20261006/output/demo_v3_scuffing.md`

### 67. 4 份，37606 字节

SHA256：`996d3ad314f9a5859644a8d48aa531546c786c8d6676ad096d01c208f212de7e`

- `history/organization_20261007/sensor_maintenance/output/maintenance_20261005/neo4j_native_style_restored.png`
- `history/v3_before_redesign_20261006/output/maintenance_20261005/neo4j_native_style_restored.png`
- `history/v4_1_before_source_merge_20261006/output/maintenance_20261005/neo4j_native_style_restored.png`
- `history/v4_before_refinement_20261006/output/maintenance_20261005/neo4j_native_style_restored.png`

### 68. 3 份，141667 字节

SHA256：`9baff77888803960e7ea1ffece1f294e347209096b4944f00237916e1000e11a`

- `naming_v4.json`
- `history/v4_1_before_source_merge_20261006/naming_v4.json`
- `history/v4_before_refinement_20261006/naming_v4.json`

### 69. 4 份，4002 字节

SHA256：`9cc4b73d77871fb8f22d94f5b17ded71001efe511ef465da167070e58adb0675`

- `check_neo4j_connection.py`
- `history/v3_before_redesign_20261006/check_neo4j_connection.py`
- `history/v4_1_before_source_merge_20261006/check_neo4j_connection.py`
- `history/v4_before_refinement_20261006/check_neo4j_connection.py`

### 70. 2 份，140647 字节

SHA256：`a1259f52b4445b939f7b0c7b4abe2fe974fd235de9769a4e66c442a090f5524d`

- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/final-slide-10.png`
- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/slide-10.png`

### 71. 6 份，3885621 字节

SHA256：`a4022095cbb1c0ecc944f0a388023f0b84dd84dfbe0732c1f0a6d44851c2afa4`

- `history/v3_before_redesign_20261006/output/graph_inventory_v2.json`
- `history/v3_before_redesign_20261006/output/graph_inventory_v3.json`
- `history/v4_1_before_source_merge_20261006/output/graph_inventory_v2.json`
- `history/v4_1_before_source_merge_20261006/output/graph_inventory_v3.json`
- `history/v4_before_refinement_20261006/output/graph_inventory_v2.json`
- `history/v4_before_refinement_20261006/output/graph_inventory_v3.json`

### 72. 3 份，18112 字节

SHA256：`a713fbdb0a5bae78ce920c858e20b788122a751ddbac921d25e2e6796971c4a5`

- `history/v3_before_redesign_20261006/output/demo_v2_cpp.json`
- `history/v4_1_before_source_merge_20261006/output/demo_v2_cpp.json`
- `history/v4_before_refinement_20261006/output/demo_v2_cpp.json`

### 73. 6 份，5179 字节

SHA256：`a8362d25c59c27d5545fe45e0130ae3f580ef909b5cd44f5310a49079fa64cfa`

- `history/v3_before_redesign_20261006/output/shipkg_v2.grass`
- `history/v3_before_redesign_20261006/output/shipkg_v3.grass`
- `history/v4_1_before_source_merge_20261006/output/shipkg_v2.grass`
- `history/v4_1_before_source_merge_20261006/output/shipkg_v3.grass`
- `history/v4_before_refinement_20261006/output/shipkg_v2.grass`
- `history/v4_before_refinement_20261006/output/shipkg_v3.grass`

### 74. 2 份，117669 字节

SHA256：`a86ea36369c4e7895e2e4a2a2875be12f0275639213f6045cac8c69e3dbd4510`

- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/final-slide-08.png`
- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/slide-08.png`

### 75. 2 份，2086038 字节

SHA256：`aab20a5b02e38adcfdd457adcfb2df75a902e814b90589b52d49b6af65d8f9a0`

- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/candidate.pptx`
- `history/organization_20261007/presentations/presentations/group_meeting_v3_output/船舶故障知识图谱构建与RAG增强诊断_组会汇报_20261005.pptx`

### 76. 3 份，1374723 字节

SHA256：`ad95da8c853bad161474a035c1b03b304c89a1c4e9c876bf02269cf927553246`

- `history/organization_20261007/v1_artifacts/output/v1_legacy/passages.csv`
- `history/v1_20261004/output/passages.csv`
- `history/v2_before_fault_focus_20261005/output/v1_legacy/passages.csv`

### 77. 4 份，266957 字节

SHA256：`ae380be97f2c9f669430259e5cbd95ff4eeb43a508981d1645e6fe992f1e7e10`

- `history/organization_20261007/source_review/output/source_review_v3/MAN_SL2016_633_piston_rings_scuffing_page2.png`
- `history/v3_before_redesign_20261006/output/source_review_v3/MAN_SL2016_633_piston_rings_scuffing_page2.png`
- `history/v4_1_before_source_merge_20261006/output/source_review_v3/MAN_SL2016_633_piston_rings_scuffing_page2.png`
- `history/v4_before_refinement_20261006/output/source_review_v3/MAN_SL2016_633_piston_rings_scuffing_page2.png`

### 78. 4 份，2357 字节

SHA256：`aeb2b833e775d9e2b169d4e33967b777e7f7f6de576fe08a5e250d90e8571ea9`

- `history/organization_20261007/legacy_tools/queries_v2.cypher`
- `history/v2_before_fault_focus_20261005/queries_v2.cypher`
- `history/v4_1_before_source_merge_20261006/queries_v2.cypher`
- `history/v4_before_refinement_20261006/queries_v2.cypher`

### 79. 3 份，15797 字节

SHA256：`aec5ec900228e9656a04f11ecaf92c73c1d0ea4db54da0a02c5cfda2139c9e01`

- `history/v3_before_redesign_20261006/output/demo_v3_scuffing.json`
- `history/v4_1_before_source_merge_20261006/output/demo_v3_scuffing.json`
- `history/v4_before_refinement_20261006/output/demo_v3_scuffing.json`

### 80. 8 份，41328 字节

SHA256：`b0f4da537232bf6e49d43295e37050bbbae2c2820093d14ed2f302dd33ca9d40`

- `history/organization_20261007/connection_maintenance/output/neo4j_connection_repair_20261005/neo4j.conf`
- `history/organization_20261007/connection_maintenance/output/neo4j_connection_repair_20261005/neo4j.conf.desktop-fixed`
- `history/v3_before_redesign_20261006/output/neo4j_connection_repair_20261005/neo4j.conf`
- `history/v3_before_redesign_20261006/output/neo4j_connection_repair_20261005/neo4j.conf.desktop-fixed`
- `history/v4_1_before_source_merge_20261006/output/neo4j_connection_repair_20261005/neo4j.conf`
- `history/v4_1_before_source_merge_20261006/output/neo4j_connection_repair_20261005/neo4j.conf.desktop-fixed`
- `history/v4_before_refinement_20261006/output/neo4j_connection_repair_20261005/neo4j.conf`
- `history/v4_before_refinement_20261006/output/neo4j_connection_repair_20261005/neo4j.conf.desktop-fixed`

### 81. 2 份，15663 字节

SHA256：`b0f7d6dc24f24d169e4866f0c9008ef5a194942b791fb8a2618f3430ed8611e2`

- `history/organization_20261007/v3_artifacts/output/retrieval_evaluation.json`
- `history/v2_before_fault_focus_20261005/output/retrieval_evaluation.json`

### 82. 2 份，15691 字节

SHA256：`b927213c3c5176d4cce1e3623cf5c6e6f37f7348a5f53f1b39c404052f227d33`

- `history/organization_20261007/v3_artifacts/output/retrieval_evaluation_lexical.json`
- `history/v2_before_fault_focus_20261005/output/retrieval_evaluation_lexical.json`

### 83. 3 份，43625 字节

SHA256：`bd44bd04c21fcc89ace7daa071437bd89fcc0a53adb1ebf696abc03b4323d991`

- `history/organization_20261007/v1_artifacts/output/v1_legacy/edges.csv`
- `history/v1_20261004/output/edges.csv`
- `history/v2_before_fault_focus_20261005/output/v1_legacy/edges.csv`

### 84. 5 份，222 字节

SHA256：`be0437bb7fe678f179d2580f53d85fa84dc2a39d83a9f371b2d1982ad38055d5`

- `example_diagnosis.json`
- `history/v1_20261004/example_diagnosis.json`
- `history/v2_before_fault_focus_20261005/example_diagnosis.json`
- `history/v4_1_before_source_merge_20261006/example_diagnosis.json`
- `history/v4_before_refinement_20261006/example_diagnosis.json`

### 85. 2 份，264257 字节

SHA256：`c0b38d4874f542ac03e98ec18256c8ffe2815efc9fcbd7d27fbff90095bb43c8`

- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/final-slide-06.png`
- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/slide-06.png`

### 86. 6 份，127349 字节

SHA256：`c157ed4ace1162440179532c73974f15faabd009d0dc1a74fe6a9d8e83e2d5f2`

- `history/v3_before_redesign_20261006/output/entity_inventory_v2.md`
- `history/v3_before_redesign_20261006/output/entity_inventory_v3.md`
- `history/v4_1_before_source_merge_20261006/output/entity_inventory_v2.md`
- `history/v4_1_before_source_merge_20261006/output/entity_inventory_v3.md`
- `history/v4_before_refinement_20261006/output/entity_inventory_v2.md`
- `history/v4_before_refinement_20261006/output/entity_inventory_v3.md`

### 87. 4 份，1751 字节

SHA256：`c2c9ce316d9c9eaf326de5230ba194b760417ac93fdcfe669106523d70c6888f`

- `audit_sources.py`
- `history/v3_before_redesign_20261006/audit_sources.py`
- `history/v4_1_before_source_merge_20261006/audit_sources.py`
- `history/v4_before_refinement_20261006/audit_sources.py`

### 88. 3 份，2313 字节

SHA256：`c2eef1c6fc529a2545d806921500f630d16dc3b186bba1622f9edb7ede54038f`

- `history/v3_before_redesign_20261006/output/neo4j_connection_repair_20261005/login_check_after_desktop_fix.json`
- `history/v4_1_before_source_merge_20261006/output/neo4j_connection_repair_20261005/login_check_after_desktop_fix.json`
- `history/v4_before_refinement_20261006/output/neo4j_connection_repair_20261005/login_check_after_desktop_fix.json`

### 89. 3 份，1312 字节

SHA256：`c36fce5ef76794f115f73b3361594d4b2ef30758ddf4e70c4992a758bd9dfd4f`

- `export_inventory.py`
- `history/v4_1_before_source_merge_20261006/export_inventory.py`
- `history/v4_before_refinement_20261006/export_inventory.py`

### 90. 2 份，6883 字节

SHA256：`c947c193b42429fb833315f8cf708436caec27dcfd483d17a441444a3a4d049c`

- `history/v4_1_before_source_merge_20261006/output/shipkg_v4_json.grass`
- `history/v4_before_refinement_20261006/output/shipkg_v4_json.grass`

### 91. 2 份，4530 字节

SHA256：`cba30c100f1d46c6e8503c8c73bce2da2af1a86773e0686a09122a3c9468a8d8`

- `history/v2_before_fault_focus_20261005/evaluate.py`
- `history/v3_before_redesign_20261006/evaluate.py`

### 92. 2 份，84406 字节

SHA256：`cc383be78353837f79a873f101f395c684da5fdf88dc884a00949b7d8e225e52`

- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/final-slide-02.png`
- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/slide-02.png`

### 93. 3 份，2155 字节

SHA256：`ce60e60fc39626d3d2fd5aa2942d8e0db9a3d5384a554af554f20c12bb68e2ca`

- `export_graphml.py`
- `history/v4_1_before_source_merge_20261006/export_graphml.py`
- `history/v4_before_refinement_20261006/export_graphml.py`

### 94. 3 份，695 字节

SHA256：`d07dbc849942694d0df4adc2be581510e28b6566c1f063a3fd93a9274bde0518`

- `history/v3_before_redesign_20261006/review_source_pages.py`
- `history/v4_1_before_source_merge_20261006/review_source_pages.py`
- `history/v4_before_refinement_20261006/review_source_pages.py`

### 95. 2 份，2149218 字节

SHA256：`d50bb01e928a59a156f9c420cd52e1817d7609d203c11ec4207f593c4871c92c`

- `history/v4_1_before_source_merge_20261006/neo4j_snapshot.json`
- `history/v4_1_before_source_merge_20261006/output/neo4j_snapshot_v4.json`

### 96. 3 份，5186 字节

SHA256：`d74513f301de0fd845961a82718cede8f5728cfec493d209a5f428c16fad27bb`

- `evaluate.py`
- `history/v4_1_before_source_merge_20261006/evaluate.py`
- `history/v4_before_refinement_20261006/evaluate.py`

### 97. 4 份，41168 字节

SHA256：`d86a7f9cf253aecc57a7b0c5c7f9a61a38497e40edf0ffd8f6657e367a5bc37c`

- `history/organization_20261007/connection_maintenance/output/neo4j_connection_repair_20261005/neo4j.conf.before`
- `history/v3_before_redesign_20261006/output/neo4j_connection_repair_20261005/neo4j.conf.before`
- `history/v4_1_before_source_merge_20261006/output/neo4j_connection_repair_20261005/neo4j.conf.before`
- `history/v4_before_refinement_20261006/output/neo4j_connection_repair_20261005/neo4j.conf.before`

### 98. 2 份，4920 字节

SHA256：`d8fc3a0508ae7acb1b60ac7b674a3b11d6917ee3a6bdb8a83f5a25e108cd243e`

- `history/v4_1_before_source_merge_20261006/output/shipkg_v4.grass`
- `history/v4_before_refinement_20261006/output/shipkg_v4.grass`

### 99. 4 份，5657 字节

SHA256：`daa7712c6b9f059e241778c4683319779789b7eb22c3c2f57da606a1dac18307`

- `history/organization_20261007/legacy_tools/revision_v3.py`
- `history/v3_before_redesign_20261006/revision_v3.py`
- `history/v4_1_before_source_merge_20261006/revision_v3.py`
- `history/v4_before_refinement_20261006/revision_v3.py`

### 100. 4 份，4389 字节

SHA256：`de2a82f17fe4999916fecf599c1337379547654755da17704ad1b60fcd7393b4`

- `history/organization_20261007/legacy_tools/verify_v2.py`
- `history/v3_before_redesign_20261006/verify_v2.py`
- `history/v4_1_before_source_merge_20261006/verify_v2.py`
- `history/v4_before_refinement_20261006/verify_v2.py`

### 101. 4 份，76634 字节

SHA256：`e3dd4ef5f0055370899c8f10c9d2a2b354f4b6f18e6bb460def71d5ec9328a65`

- `history/organization_20261007/sensor_maintenance/output/maintenance_20261005/neo4j_full_counts.png`
- `history/v3_before_redesign_20261006/output/maintenance_20261005/neo4j_full_counts.png`
- `history/v4_1_before_source_merge_20261006/output/maintenance_20261005/neo4j_full_counts.png`
- `history/v4_before_refinement_20261006/output/maintenance_20261005/neo4j_full_counts.png`

### 102. 2 份，116831 字节

SHA256：`e3e9e9a2062ea4770232d27bd2554ccd28ae9208b22c5821b190e8de95b7d732`

- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/final-slide-09.png`
- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/slide-09.png`

### 103. 2 份，1153795 字节

SHA256：`e77780825b5df31a70d89a3dc50f81c04dec670ea3d95a91db0bde47f1e4af06`

- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/final-slide-01.png`
- `history/organization_20261007/presentations/presentations/group_meeting_v3_build/slide-01.png`

### 104. 4 份，142203 字节

SHA256：`e7f66143fb99f1b148b14900efc97128bb6f00266934b6c0f34a2b33ba13606b`

- `history/organization_20261007/v3_artifacts/output/viewer_v3_scuffing.jpg`
- `history/v3_before_redesign_20261006/output/viewer_v3_scuffing.jpg`
- `history/v4_1_before_source_merge_20261006/output/viewer_v3_scuffing.jpg`
- `history/v4_before_refinement_20261006/output/viewer_v3_scuffing.jpg`

### 105. 2 份，23327 字节

SHA256：`ea1e61eb96f416b3c67e98ee77a181ff9501e400defd0ae81f47c0fe9073065c`

- `history/docs_before_consolidation_20261005/REPORT_KG_BUILD_NEO4J_CN.md`
- `history/v2_before_fault_focus_20261005/REPORT_KG_BUILD_NEO4J_CN.md`

### 106. 6 份，3799 字节

SHA256：`ee61a48b73ca9e7463b1f3d523cd763a74db32b9266607a8db2fa629a4112cbd`

- `prepare_neo4j_admin_import.py`
- `history/v1_20261004/prepare_neo4j_admin_import.py`
- `history/v2_before_fault_focus_20261005/prepare_neo4j_admin_import.py`
- `history/v3_before_redesign_20261006/prepare_neo4j_admin_import.py`
- `history/v4_1_before_source_merge_20261006/prepare_neo4j_admin_import.py`
- `history/v4_before_refinement_20261006/prepare_neo4j_admin_import.py`

### 107. 2 份，27175 字节

SHA256：`ee7f8502775518ba4905e31c7fce427dfdf575ccc4bb28c907aa9c8357a0be34`

- `history/docs_before_consolidation_20261005/REPORT_KG_CONTENT_AND_LIMITS_CN.md`
- `history/v2_before_fault_focus_20261005/REPORT_KG_CONTENT_AND_LIMITS_CN.md`

### 108. 5 份，71358 字节

SHA256：`ef0ed3a72e1f1419311f029dfbb2d1a41a5f7890b27012a44d3dcf46cd695eff`

- `history/organization_20261007/v2_artifacts/output/neo4j_v2_counts.jpg`
- `history/v2_before_fault_focus_20261005/output/neo4j_v2_counts.jpg`
- `history/v3_before_redesign_20261006/output/neo4j_v2_counts.jpg`
- `history/v4_1_before_source_merge_20261006/output/neo4j_v2_counts.jpg`
- `history/v4_before_refinement_20261006/output/neo4j_v2_counts.jpg`

### 109. 3 份，32545 字节

SHA256：`ef9183c1a210f895f9fd89eba07d2068833276ae11f2c3b85f6f501605e88853`

- `build.py`
- `history/v4_1_before_source_merge_20261006/build.py`
- `history/v4_before_refinement_20261006/build.py`

### 110. 6 份，203514 字节

SHA256：`f3f09e205d7059f38145c385119a02c4a4f8e75e4dfa2455890a5d682415fe2b`

- `history/organization_20261007/v1_artifacts/output/v1_legacy/neo4j_admin_import/relationships_admin.csv`
- `history/v1_20261004/output/neo4j_admin_import/relationships_admin.csv`
- `history/v2_before_fault_focus_20261005/output/v1_legacy/neo4j_admin_import/relationships_admin.csv`
- `history/v3_before_redesign_20261006/output/v1_legacy/neo4j_admin_import/relationships_admin.csv`
- `history/v4_1_before_source_merge_20261006/output/v1_legacy/neo4j_admin_import/relationships_admin.csv`
- `history/v4_before_refinement_20261006/output/v1_legacy/neo4j_admin_import/relationships_admin.csv`

### 111. 4 份，17112 字节

SHA256：`f41c885d1023d52e1251e41205e91c2ddf52d0740bcb2e2547181ae75b903179`

- `fault_profiles.py`
- `history/v3_before_redesign_20261006/fault_profiles.py`
- `history/v4_1_before_source_merge_20261006/fault_profiles.py`
- `history/v4_before_refinement_20261006/fault_profiles.py`

### 112. 4 份，302530 字节

SHA256：`f56909996420cc0f606f13ffc8af73e6fff0684c067b30013eb65d39ed60ff11`

- `history/organization_20261007/source_review/output/source_review_v3/Frontiers_2021_marine_converter_oscillations_page6.png`
- `history/v3_before_redesign_20261006/output/source_review_v3/Frontiers_2021_marine_converter_oscillations_page6.png`
- `history/v4_1_before_source_merge_20261006/output/source_review_v3/Frontiers_2021_marine_converter_oscillations_page6.png`
- `history/v4_before_refinement_20261006/output/source_review_v3/Frontiers_2021_marine_converter_oscillations_page6.png`

### 113. 6 份，376 字节

SHA256：`f83043b4e220fb138487f17c4847e51e8391025a5c8629f99fa7b06790fe4560`

- `history/organization_20261007/v3_artifacts/output/ollama_shipkg.stdout.log`
- `history/v1_20261004/output/ollama_shipkg.stdout.log`
- `history/v2_before_fault_focus_20261005/output/ollama_shipkg.stdout.log`
- `history/v3_before_redesign_20261006/output/ollama_shipkg.stdout.log`
- `history/v4_1_before_source_merge_20261006/output/ollama_shipkg.stdout.log`
- `history/v4_before_refinement_20261006/output/ollama_shipkg.stdout.log`

### 114. 3 份，1161 字节

SHA256：`fbd0a4832e43b9d57ed2551a8601576ccf9277f7315045dd22637fdfd4745525`

- `history/v3_before_redesign_20261006/check_neo4j_ready.ps1`
- `history/v4_1_before_source_merge_20261006/check_neo4j_ready.ps1`
- `history/v4_before_refinement_20261006/check_neo4j_ready.ps1`

### 115. 3 份，19158 字节

SHA256：`fc0b37ec08b0c129b0e499e982874efb07f8d8fa93893e0910159b562c1e2bfe`

- `history/organization_20261007/v1_artifacts/output/v1_legacy/demo_kg_rag_report.json`
- `history/v1_20261004/output/demo_kg_rag_report.json`
- `history/v2_before_fault_focus_20261005/output/v1_legacy/demo_kg_rag_report.json`

### 116. 3 份，43299 字节

SHA256：`fd53084013eb739ed3dbdba0377bc6f26c46f7a0fb03bd58ad368852d73ee901`

- `history/v3_before_redesign_20261006/output/v1_legacy/edges.csv`
- `history/v4_1_before_source_merge_20261006/output/v1_legacy/edges.csv`
- `history/v4_before_refinement_20261006/output/v1_legacy/edges.csv`
