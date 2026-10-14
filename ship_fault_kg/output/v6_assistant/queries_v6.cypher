// 1. 实体分类统计（只统计本项目）
MATCH (n:ShipKG) RETURN n.kind AS entity_type, count(*) AS nodes ORDER BY nodes DESC;

// 2. 完整系统层次（28节点，含根系统）
MATCH p=(s:ShipKG:System)-[:IS_SUBSYSTEM_OF*1..3]->(parent:ShipKG:System)
RETURN p;

// 3. 故障概念总览（限制显示量，不建议一次画5591节点）
MATCH (f:ShipKG:Fault) WHERE f.entity_level='concept'
RETURN f LIMIT 100;

// 4. 保持架局部：故障、状态、因素和来源（不是全都为因果关系）
MATCH (f:ShipKG:Fault)-[r]-(n:ShipKG)
WHERE f.name CONTAINS '保持架'
RETURN f,r,n LIMIT 100;

// 5. 证据表，保留来源和适用范围，不只看图上线条
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE type(r) IN ['CAUSES','CONTRIBUTES_TO','INCREASES_RISK_OF','WORSENS']
  AND (a.name CONTAINS '保持架' OR b.name CONTAINS '保持架')
RETURN a.name AS subject, r.name AS relation, b.name AS object,
 r.quote AS quote,r.source_id AS source_id,r.locator AS locator,
 r.scope_id AS scope,r.certainty AS certainty,r.certainty_group AS certainty_group LIMIT 30;

// 6. 同范围因果路径；不跨scope拼接“已证实”原因
MATCH p=(a:ShipKG)-[:CAUSES|CONTRIBUTES_TO|INCREASES_RISK_OF|WORSENS*1..3]->(f:ShipKG:Fault)
WHERE f.name CONTAINS '超速'
  AND all(r IN relationships(p) WHERE r.scope_id=relationships(p)[0].scope_id)
RETURN p LIMIT 30;

// 7. 查看来源节点。正式来源链接可能为空，必须同时检查locator与原文
MATCH (n:ShipKG)-[r:DOCUMENTED_BY]->(s:ShipKG:Source)
WHERE n.name CONTAINS '超速'
RETURN n,r,s LIMIT 80;

//全局图
MATCH (n:ShipKG)
OPTIONAL MATCH (n)-[r]->(m:ShipKG)
RETURN n, r, m;
