// V4.3当前查询；先在Browser选择shipfaultkg。逐段复制执行。
// 全图中文显示：node caption=display_name; relationship caption=name。
// GraSS为output/shipkg_v4.grass。数量用Table，节点/关系用Graph。

// 1. 当前数据统计：491 / 1200 / 111 / 15。
CALL () { MATCH (n:ShipKG) RETURN count(n) AS nodes }
CALL () { MATCH (:ShipKG)-[r]->(:ShipKG) RETURN count(r) AS relationships }
CALL () { MATCH (f:ShipKG:Fault) RETURN count(f) AS faults }
CALL () { MATCH (s:ShipKG:Sensor) RETURN count(s) AS sensors }
RETURN nodes, relationships, faults, sensors;

// 2. 实体类别分布：15类；已移出Azimuth监测摘要，中文文章统一用Source。
MATCH (n:ShipKG)
RETURN n.kind_zh AS 实体类型, n.kind AS 类型代码, count(*) AS 数量
ORDER BY 数量 DESC;

// 3. 关系类别分布：28种。中文name允许按语境和确定性细化。
MATCH (:ShipKG)-[r]->(:ShipKG)
RETURN type(r) AS 关系代码, collect(DISTINCT r.name) AS 中文名称, count(*) AS 数量
ORDER BY 数量 DESC;

// 4. 故障类别12；原保留故障事件90；二次语料故障状态9。不是111种确诊故障。
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

// 9. 试验、测点、中文文章直接连到来源；当前没有记录级Source。
MATCH (n:ShipKG)-[r:DOCUMENTED_BY]->(s:ShipKG:Source)
WHERE n.kind IN ['Run','Sensor'] OR n.source_level='文章级'
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

// 15. 中文润滑油/烧瓦语料链，待专家核验；不要跨文章拼接。
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE r.case_id='corpus:a4dd6412481f'
  AND type(r) IN ['CAUSES','LEADS_TO','INCREASES_RISK_OF','MAY_CONTRIBUTE_TO','CHECKS','ADDRESSES']
RETURN a, r, b;

// 16. 二次语料诊断事实的原文溯源：文章路径与归一化字符区间，不伪造PDF页码。
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE r.certainty='corpus_statement'
  AND type(r) IN ['CAUSES','LEADS_TO','INCREASES_RISK_OF','MAY_CONTRIBUTE_TO','CHECKS','ADDRESSES']
RETURN a.name AS 起点, r.name AS 关系, b.name AS 终点,
       r.certainty_zh AS 证据性质, r.expert_review AS 审核状态,
       r.locator AS 原文定位, r.quote AS 原文, r.source_url AS 资料包来源;

// 17. 当前来源层级：资料级29、文章级4，总33；记录级0。
MATCH (s:ShipKG:Source)
RETURN s.source_level AS 来源层级, count(*) AS 数量;

// 18. 文章级Source归属资料包Source；每条诊断关系另有自己的原文证据。
MATCH (article:ShipKG:Source)-[r:DOCUMENTED_BY]->(document:ShipKG:Source)
WHERE article.source_level='文章级' AND document.source_level='资料级'
RETURN DISTINCT article.name AS 文章名, article.id AS 稳定ID,
       article.locator AS 本地文章, article.expert_review AS 审核状态,
       document.name AS 资料包, document.url AS 资料包网址;
