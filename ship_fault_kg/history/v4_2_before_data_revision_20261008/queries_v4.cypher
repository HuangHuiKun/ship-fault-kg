// V4.2当前查询；先在Browser选择shipfaultkg。逐段复制执行。
// 全图中文显示：node caption=display_name; relationship caption=name。
// GraSS为output/shipkg_v4.grass。数量用Table，节点/关系用Graph。

// 1. 当前数据统计：491 / 1185 / 114 / 15。
CALL () { MATCH (n:ShipKG) RETURN count(n) AS nodes }
CALL () { MATCH (:ShipKG)-[r]->(:ShipKG) RETURN count(r) AS relationships }
CALL () { MATCH (f:ShipKG:Fault) RETURN count(f) AS faults }
CALL () { MATCH (s:ShipKG:Sensor) RETURN count(s) AS sensors }
RETURN nodes, relationships, faults, sensors;

// 2. 实体类别分布：15类；故障类别与事件统一为Fault，监测摘要统一为Source。
MATCH (n:ShipKG)
RETURN n.kind_zh AS 实体类型, n.kind AS 类型代码, count(*) AS 数量
ORDER BY 数量 DESC;

// 3. 关系类别分布：29种。中文name允许按语境和确定性细化。
MATCH (:ShipKG)-[r]->(:ShipKG)
RETURN type(r) AS 关系代码, collect(DISTINCT r.name) AS 中文名称, count(*) AS 数量
ORDER BY 数量 DESC;

// 4. 故障类别12；具体故障或事件102（不是102种确诊故障）。
MATCH (f:ShipKG:Fault)
RETURN f.fault_level AS 故障角色, count(*) AS 数量;

// 5. 查看经典故障入口及5个功能系统（不再查询FaultType/Subsystem）。
MATCH (f:ShipKG:Fault)-[r:IN_SYSTEM]->(s:ShipKG:System)
WHERE f.fault_level='故障类别' AND s.system_level='功能系统'
RETURN f, r, s;

// 6. 拉缸参考机理：包含诊断、检查、措施；不代表某条船确诊。
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE r.case_id='knowledge:liner_scuffing'
  AND type(r) IN ['CONTRIBUTED_TO','MAY_CONTRIBUTE_TO','LEADS_TO','CHECKS','ADDRESSES','INDICATES']
RETURN a, r, b;

// 7. 同一知识单元的溯源；页码为PDF物理页。
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE r.case_id='knowledge:liner_scuffing' AND r.knowledge_layer='reference'
RETURN a.name AS 起点, r.name AS 关系, b.name AS 终点,
       r.certainty_zh AS 确定性, r.applicability AS 适用边界,
       r.source_file AS 来源文件, r.page AS 物理页, r.quote AS 原文, r.source_url AS 来源网址;

// 8. 全图（491节点，可能受Browser显示上限和拥挤影响）。
MATCH (n:ShipKG)
OPTIONAL MATCH (n)-[r]->(m:ShipKG)
RETURN n, r, m;

// 9. 数据集入口已删除；试验、测点、摘要仍直接连到来源。
MATCH (n:ShipKG)-[r:DOCUMENTED_BY]->(s:ShipKG:Source)
WHERE n.kind IN ['Run','Sensor'] OR n.source_level='记录级'
RETURN n, r, s;

// 10. 类别与具体事件的分类关系（不是因果边）。
MATCH (event:ShipKG:Fault)-[r:INSTANCE_OF]->(category:ShipKG:Fault)
RETURN event, r, category;

// 11. 船舶角色、系统角色。名称相同不等于身份相同。
MATCH (n:ShipKG)
WHERE n.kind IN ['Vessel','System']
RETURN n.kind AS 类别, coalesce(n.entity_level,n.system_level) AS 角色,
       n.name AS 名称, n.id AS 稳定ID ORDER BY 类别, 角色, 名称;

// 12. 已退休的实体标签应返回0（元数据仍列旧标签不代表有节点）。
MATCH (n:ShipKG)
WHERE n:FaultType OR n:Dataset OR n:VesselType OR n:Subsystem OR n:Observation
RETURN count(n) AS 旧类别残留节点;

// 13. 5个泛化船型入口已移除；具体船记录及船型属性仍在。
MATCH (v:ShipKG:Vessel)
WHERE v.vessel_type IS NOT NULL
RETURN v.name AS 船舶记录, v.vessel_type AS 船型,
       v.props_json AS 详细属性及分类证据;

// 14. 19个设备节点；12个“系统”名称已改为装置，另1个去掉2017。
MATCH (e:ShipKG:Equipment)
RETURN e.name AS 设备名, e.previous_display_name AS 上版名称,
       e.original_name AS 原始名称, e.case_id AS 案例, e.id AS 稳定ID
ORDER BY 设备名;

// 15. 查看记录级Source—状态—建议—资料级Source，不是事故根因链。
MATCH (o:ShipKG:Source)-[r]->(n:ShipKG)
WHERE o.source_level='记录级'
  AND type(r) IN ['SHOWS_CONDITION','HAS_RECOMMENDED_ACTION','DOCUMENTED_BY']
RETURN o, r, n;

// 16. 第1条监测摘要，演示记录级来源定位与字段。
MATCH (o:ShipKG:Source)-[r:SHOWS_CONDITION|HAS_RECOMMENDED_ACTION]->(n:ShipKG)
WHERE o.source_level='记录级' AND o.record=1
RETURN o.name AS 监测记录, o.warning_hours AS 提前预警小时,
       o.reference_class AS 参考分类, r.name AS 关系, n.name AS 状态或建议,
       r.evidence_id AS 证据ID, r.locator AS 来源行定位, r.source_file AS 来源文件;

// 17. 合并核验：资料级30，记录级12，总42；Observation标签节点为0。
MATCH (s:ShipKG:Source)
RETURN s.source_level AS 来源层级, count(*) AS 数量;

// 18. 记录仍逐一归属资料级来源；保留12条来源关系与行号。
MATCH (record:ShipKG:Source)-[r:DOCUMENTED_BY]->(document:ShipKG:Source)
WHERE record.source_level='记录级' AND document.source_level='资料级'
RETURN record.name AS 记录名, record.id AS 原稳定ID, record.record AS 原行号,
       document.name AS 资料来源, r.evidence_id AS 证据ID, r.locator AS 原始定位;
