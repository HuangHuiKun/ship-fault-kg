"""V4 Chinese captions, unified entity roles and source-stage taxonomy."""

VERSION = "4.1"
KIND_ZH = {
    "Vessel": "船舶", "System": "系统", "Case": "事故案例", "Equipment": "设备",
    "Component": "部件", "Fault": "故障", "Cause": "原因",
    "Condition": "工况与状态", "Symptom": "症状", "Consequence": "后果",
    "Check": "检查方法", "Action": "运维措施", "Run": "试验运行",
    "Sensor": "测点", "Observation": "监测摘要", "Source": "资料来源",
}
# Legacy source declarations remain intact to preserve IDs and evidence. Only
# the final V4 graph uses KIND_ZH; redesign.py performs the reviewed migration.
LEGACY_KIND_ZH = dict(KIND_ZH, VesselType="船型", Subsystem="子系统",
                      Dataset="数据集", FaultType="经典故障类别")
RELATION_ZH = {
    "DOCUMENTED_BY": "来源于", "HAS_CASE": "发生案例", "INVOLVES": "涉及",
    "IN_SYSTEM": "涉及系统", "IN_SUBSYSTEM": "涉及子系统",
    "BELONGS_TO_SYSTEM": "归属系统",
    "BELONGS_TO_SUBSYSTEM": "归属子系统", "OF_VESSEL_TYPE": "船型为",
    "TESTS_FAULT": "试验故障为", "HAS_EQUIPMENT": "涉及设备",
    "HAS_COMPONENT": "包含部件", "AFFECTS_COMPONENT": "影响部件",
    "HAS_RUN": "包含试验", "AT_LOAD": "运行负载为", "HAS_CHANNEL": "包含测点",
    "HAS_STATUS": "具有状态", "SHOWS_CONDITION": "呈现状态",
    "HAS_RECOMMENDED_ACTION": "建议采取", "CAUSES": "导致",
    "CONTRIBUTED_TO": "促成", "LEADS_TO": "导致", "INCREASES_RISK_OF": "增加风险",
    "PRECEDED": "先于发生", "PROMPTS": "应触发处置", "REDUCES_EFFECTIVENESS_OF": "削弱措施效果",
    "ASSOCIATED_WITH": "相关联", "LIMITS_DETECTION_OF": "妨碍发现",
    "ADDRESSES": "应对", "CHECKS": "检查", "INDICATES": "提示",
    "MAY_CONTRIBUTE_TO": "可能促成", "INCREASES_SEVERITY_OF": "加剧严重度",
    "TRIGGERS": "触发", "WORSENS": "加重后果", "MONITORS": "监测",
    "INSTANCE_OF": "归入故障类别",
}
DIAGNOSTIC_RELS = {
    "CAUSES", "CONTRIBUTED_TO", "LEADS_TO", "INCREASES_RISK_OF", "PRECEDED",
    "PROMPTS", "REDUCES_EFFECTIVENESS_OF", "ASSOCIATED_WITH", "LIMITS_DETECTION_OF",
    "ADDRESSES", "CHECKS", "INDICATES", "MAY_CONTRIBUTE_TO", "INCREASES_SEVERITY_OF",
    "TRIGGERS", "WORSENS",
}
CAUSAL_RELS = {
    "CAUSES", "CONTRIBUTED_TO", "LEADS_TO", "INCREASES_RISK_OF", "TRIGGERS",
    "WORSENS", "MAY_CONTRIBUTE_TO", "INCREASES_SEVERITY_OF",
}
SUBSYSTEMS = {
    "fuel_air": "燃油与进排气子系统",
    "lubrication": "润滑与轴承子系统",
    "cooling": "冷却与海水子系统",
    "transmission": "传动与推进子系统",
    "electrical": "电力与控制子系统",
}
CERTAINTY_ZH = {
    "reported": "报告明确记载", "probable": "很可能", "possible": "可能",
    "reported_action": "报告行动/建议", "derived_action": "依据报告整理的检查建议",
    "dataset_label": "数据集标签", "simulated": "仿真状态",
    "curated_classification": "研究者分类（非因果结论）",
    "guidance": "厂家一般机理/指导（须核对机型）",
    "research_observation": "论文实测观察（非本船已证实根因）",
}
