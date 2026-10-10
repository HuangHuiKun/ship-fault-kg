// 连接到shipfaultkg后逐段执行；表格数量不受Browser图形显示上限影响。
// 1. 真实总数
MATCH (n:ShipKG) RETURN count(n) AS 节点;
MATCH (:ShipKG)-[r]->(:ShipKG) RETURN count(r) AS 关系;
// 2. 类别统计与层级
MATCH (n:ShipKG) RETURN n.kind_zh AS 类别, n.entity_level AS 层级, count(n) AS 数量 ORDER BY 类别,层级;
// 3. 五个子系统及动力系统根节点
MATCH p=(s:System:ShipKG)-[:IS_SUBSYSTEM_OF]->(root:System:ShipKG) RETURN p;
// 4. 不带出处节点的总体展示；通常需在Browser设置提高Initial Node Display。
// 不建议默认铺满；必要时逐系统或逐故障查看。
MATCH p=(a:ShipKG)-[r]->(b:ShipKG)
WHERE type(r)<>'DOCUMENTED_BY' RETURN p;
// 5. 拉缸局部：只画显式的因果边，不把索引边当因果
MATCH (f:Fault:ShipKG {name:'缸套黏着拉伤',entity_level:'concept'})
MATCH p=(a:ShipKG)-[:CAUSES|CONTRIBUTES_TO|INCREASES_RISK_OF|WORSENS*1..3]->(f)
WHERE all(r IN relationships(p) WHERE r.scope_id=relationships(p)[0].scope_id)
RETURN p LIMIT 40;
// 6. 拉缸直接症状、检查、措施及各自来源
MATCH (f:Fault:ShipKG {name:'缸套黏着拉伤',entity_level:'concept'})
MATCH (f)-[r:HAS_MANIFESTATION|INDICATES|CHECKS|ADDRESSES]-(n:ShipKG)
MATCH (n)-[d:DOCUMENTED_BY]->(s:Source:ShipKG)
WHERE s.source_id=r.source_id
RETURN f,r,n,d,s LIMIT 35;
// 7. 逐跳证据表：可看原文、页码、确定性与范围
MATCH p=(a:ShipKG)-[:CAUSES|CONTRIBUTES_TO|INCREASES_RISK_OF|WORSENS*1..3]->
 (f:Fault:ShipKG {name:'缸套黏着拉伤',entity_level:'concept'})
WHERE all(x IN relationships(p) WHERE x.scope_id=relationships(p)[0].scope_id)
UNWIND relationships(p) AS r
RETURN DISTINCT startNode(r).display_name AS 起点,r.name AS 关系,endNode(r).display_name AS 终点,
 r.scope_id AS 范围,r.certainty AS 确定性,r.source_file AS 原文件,r.page AS 文件页码,
 r.quote AS 原文,r.applicability AS 适用范围,r.assertion_id AS 声明ID LIMIT 80;
// 8. 案例与通用概念严格分开
MATCH (c:Case:ShipKG {case_code:'C01'})-[r:INVOLVES]->(n:ShipKG)
OPTIONAL MATCH (n)-[i:INSTANCE_OF]->(g:ShipKG)
RETURN c,r,n,i,g LIMIT 70;
// 9. 来源性质；来源注册总量不能由此查询推算
MATCH (s:Source:ShipKG) RETURN s.source_tier AS 性质,count(s) AS 数量;
// 10. 不应存在Passage、Assertion、Run、Sensor旧节点
MATCH (n:ShipKG) WHERE n:Passage OR n:Assertion OR n:Run OR n:Sensor RETURN count(n) AS 应为零;
// 11. 样式和数据库约束不是同一件事
SHOW CONSTRAINTS;
