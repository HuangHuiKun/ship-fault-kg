// 在 Neo4j Browser 中逐段运行，数据库选择 shipfaultkg。
// 1. 全图规模；不能用 count(*) 的笛卡尔积来统计节点和边。
MATCH (n:ShipKG)
WITH count(n) AS nodes
MATCH (:ShipKG)-[r]->(:ShipKG)
WHERE r.id STARTS WITH 'edge:'
RETURN nodes, count(r) AS relationships;

// 2. 节点类型分布
MATCH (n:ShipKG)
RETURN n.kind_zh AS 实体类型, n.kind AS 英文类型, count(n) AS 数量
ORDER BY 数量 DESC;

// 3. 五个子系统与所涉及的事故；同一事故可以涉及多个子系统
MATCH (c:ShipKG:Case)-[:IN_SUBSYSTEM]->(s:ShipKG:Subsystem)
RETURN s.name AS 子系统, count(DISTINCT c) AS 涉及事故数量, collect(c.name) AS 案例;

// 4. 船型统计；九条匿名船是独立案例记录，不是九个已识别船名
MATCH (v:ShipKG:Vessel)-[:OF_VESSEL_TYPE]->(t:ShipKG:VesselType)
RETURN t.name AS 船型, count(DISTINCT v) AS 船舶记录数;

// 5. 单一事故的诊断关系；避免把全部组织关系一起展示成毛线团
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE r.case_id='pride_can_cpp_2014'
  AND type(r) IN ['LEADS_TO','CHECKS','ADDRESSES','WORSENS','LIMITS_DETECTION_OF','INCREASES_RISK_OF']
RETURN a,r,b;

// 6. Stena Europe燃油泄漏火灾链
MATCH (a:ShipKG)-[r:LEADS_TO]->(b:ShipKG)
WHERE r.case_id='stena_europe_fuel_2023'
RETURN a,r,b;

// 7. Queen Mary 2：同一案例内、限定长度的因果路径；保留可能性
MATCH p=(a:ShipKG)-[:LEADS_TO|CONTRIBUTED_TO|MAY_CONTRIBUTE_TO*2..5]->(b:ShipKG)
WHERE all(r IN relationships(p) WHERE r.case_id='queen_mary2_hf_2010')
RETURN p LIMIT 6;

// 8. 证据追溯：按物理PDF页定位，不等同报告印刷页码
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE r.case_id='queen_mary2_hf_2010' AND r.is_causal=true
RETURN a.name AS 起点, r.name AS 关系, b.name AS 终点,
       r.certainty_zh AS 确定性, r.source_file AS 来源,
       r.page AS PDF页码, r.quote AS 原文摘录, r.source_url AS 网址;

// 9. 标签和来源完整性；结果应是0、0
MATCH (n:ShipKG)
WITH count(CASE WHEN n.display_name IS NULL OR n.display_name='' THEN 1 END) AS 无名称节点
MATCH (:ShipKG)-[r]->(:ShipKG)
WHERE r.id STARTS WITH 'edge:'
RETURN 无名称节点,
 count(CASE WHEN r.name IS NULL OR r.evidence_id IS NULL OR r.source_file IS NULL THEN 1 END) AS 无名称或证据关系;

// 10. 验证唯一约束已存在
SHOW CONSTRAINTS;
