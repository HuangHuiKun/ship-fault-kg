VERSION = '5.0'
KINDS = dict(Vessel='船舶', System='系统', Equipment='设备', Component='部件',
             Fault='故障', State='状态', Factor='影响因素', Parameter='参数',
             Check='检查方法', Action='运维措施', Case='事故案例', Source='来源')
RELATIONS = {
    'IS_SUBSYSTEM_OF':'属于上级系统', 'SERVES_SYSTEM':'服务于系统',
    'HAS_COMPONENT':'包含部件', 'INSTANCE_OF':'是概念的实例',
    'APPLIES_TO':'适用于', 'CAUSES':'导致', 'CONTRIBUTES_TO':'促成',
    'INCREASES_RISK_OF':'增加风险', 'WORSENS':'加剧',
    'HAS_MANIFESTATION':'表现为', 'INDICATES':'提示', 'ASSOCIATED_WITH':'相关联',
    'PRECEDES':'先于发生', 'CHECKS':'检查', 'ADDRESSES':'应对', 'ACTS_ON':'作用于',
    'INVOLVES':'涉及', 'OCCURS_ON':'发生于', 'HAS_CASE':'发生案例',
    'DESCRIBED_BY_PARAMETER':'以参数描述', 'CHARACTERIZES':'表征',
    'USES_PARAMETER':'使用参数', 'IS_A':'属于概念类别', 'DOCUMENTED_BY':'记载于',
}
CAUSAL = {'CAUSES','CONTRIBUTES_TO','INCREASES_RISK_OF','WORSENS'}
ENDPOINTS = {
    'IS_SUBSYSTEM_OF':({'System'},{'System'}),
    'SERVES_SYSTEM':({'Equipment','Component'},{'System'}),
    'HAS_COMPONENT':({'Equipment','Component'},{'Component'}),
    'APPLIES_TO':({'Fault','Check','Action'},{'System','Equipment','Component'}),
    **{r:({'Fault','State','Factor'},{'Fault','State'}) for r in CAUSAL},
    'HAS_MANIFESTATION':({'Fault'},{'State'}), 'INDICATES':({'State'},{'Fault'}),
    'ASSOCIATED_WITH':({'Fault','State','Factor'},{'Fault','State','Factor'}),
    'PRECEDES':({'Fault','State'},{'Fault','State'}),
    'CHECKS':({'Check'},{'Fault','State','Factor','Equipment','Component'}),
    'ADDRESSES':({'Action'},{'Fault','State','Factor'}),
    'ACTS_ON':({'Action'},{'Equipment','Component'}),
    'INVOLVES':({'Case'},set(KINDS)-{'Source','Case'}),
    'OCCURS_ON':({'Fault'},{'Equipment','Component'}),
    'HAS_CASE':({'Vessel'},{'Case'}),
    'DESCRIBED_BY_PARAMETER':({'State'},{'Parameter'}),
    'CHARACTERIZES':({'Parameter'},{'System','Equipment','Component'}),
    'USES_PARAMETER':({'Check'},{'Parameter'}),
    'DOCUMENTED_BY':(set(KINDS),{'Source'}),
    'INSTANCE_OF':(set(KINDS)-{'Source','Case','Vessel'},set(KINDS)-{'Source','Case','Vessel'}),
    'IS_A':(set(KINDS)-{'Source','Case','Vessel'},set(KINDS)-{'Source','Case','Vessel'}),
}
