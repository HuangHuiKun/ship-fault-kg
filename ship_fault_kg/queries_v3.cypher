// 数据库选 shipfaultkg。逐段运行；返回节点/关系才能看到Graph。
// 1. 故障入口总览：类别 -> 子系统（分类，不是因果）。
MATCH (f:ShipKG:FaultType)-[r:IN_SUBSYSTEM]->(s:ShipKG:Subsystem)
RETURN f,r,s;

// 2. 拉缸文献机理、检查与措施；不会跨历史事故拼链。
MATCH (k:ShipKG:FaultType {name:'拉缸'})
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE r.case_id=k.knowledge_id
 AND type(r) IN ['CONTRIBUTED_TO','MAY_CONTRIBUTE_TO','LEADS_TO','CHECKS','ADDRESSES','INDICATES']
RETURN a,r,b;

// 3. 将拉缸改为其它类别名即可查看其全部知识与来源。
MATCH (k:ShipKG:FaultType {name:'烧瓦与轴承咬死'})
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE r.case_id=k.knowledge_id
RETURN k,a,r,b;

// 4. 所有具体故障与相邻原因/后果/检查；排除正常参照状态。
MATCH (f:ShipKG:Fault)-[r]-(n:ShipKG)
WHERE coalesce(f.semantic_class,'') <> 'normal_reference'
 AND type(r) IN ['CAUSES','LEADS_TO','CONTRIBUTED_TO','MAY_CONTRIBUTE_TO','CHECKS','ADDRESSES','INDICATES']
RETURN f,r,n;

// 5. 热-机-电耦合相关参考关系及可追溯的原文位置。
MATCH (a:ShipKG)-[r]->(b:ShipKG)
WHERE r.knowledge_layer='reference' AND r.coupling_domains CONTAINS '电'
RETURN a.name AS 起点,r.name AS 关系,b.name AS 终点,
 r.certainty_zh AS 确定性,r.applicability AS 适用范围,
 r.source_file AS 来源,r.page AS PDF物理页,r.quote AS 原文片段,r.source_url AS 网址;

// 6. 故障类别 -> 具体故障；分类不等于已证明根因相同。
MATCH (f:ShipKG:Fault)-[r:INSTANCE_OF]->(t:ShipKG:FaultType)
RETURN f,r,t;

// 7. 15个活动测点及单位；原始电压通道不能当作已标定压力。
MATCH (s:ShipKG:Sensor)
RETURN s.display_name AS 测点,s.name AS 原字段,s.unit AS 单位,s.note AS 原始数据说明
ORDER BY 原字段;

// 8. 实时活动图谱核验。归档标签不计入活动图谱。
MATCH (n:ShipKG)
WITH count(n) AS nodes,count(CASE WHEN n:Sensor THEN 1 END) AS sensors,
 count(CASE WHEN n:FaultType THEN 1 END) AS fault_types,
 count(CASE WHEN n:Case THEN 1 END) AS historical_cases
MATCH (:ShipKG)-[r]->(:ShipKG)
RETURN nodes,count(r) AS relationships,sensors,fault_types,historical_cases;

// 9. 名称完整性；匿名前缀已去掉，身份未公开标记仍保留。
MATCH (n:ShipKG)
WHERE n.kind IN ['Vessel','VesselType','Case'] AND n.name STARTS WITH '匿名'
RETURN count(n) AS remaining_anonymous_prefix; // 应为0

// 10. 原始船舶身份边界，不能把案例编号当真实船名。
MATCH (v:ShipKG:Vessel) WHERE v.anonymous=true
RETURN v.name,v.vessel_identity_status,v.original_name;
