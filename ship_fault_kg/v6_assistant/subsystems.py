"""Conservative, explicitly derived functional sub-system index.

These are ontology groupings for retrieval, not source-authored fault claims.
Only an equipment name with an unambiguous literal cue receives a leaf link.
"""
import re

RULES = {
    '燃油与进排气系统': (
        (r'喷油|燃油|高压油泵|共轨|供油单元|单体泵|ICU|压力控制阀PCV', '燃油供给与喷射子系统'),
        (r'增压|空冷|扫气|进气滤清', '增压与进气子系统'),
        (r'排气|气阀|气门|配气|阀桥|废气锅炉', '排气与配气子系统'),
        (r'活塞|缸套|气缸压缩', '气缸燃烧与活塞组件子系统'),
        (r'起动|启动|空气分配|盘车', '起动空气与盘车辅助子系统'),
        (r'VIT|ME.?V阀|燃油凸轮|喷油定时', '喷油定时与液压执行子系统')),
    '润滑与轴承系统': (
        (r'气缸.*(?:润滑|注油)|汽缸.*注油|注油器|气缸油', '气缸润滑子系统'),
        (r'滑油分油|离心.*滑油|滤清|滑油过滤|伺服油滤', '滑油净化与过滤子系统'),
        (r'曲轴箱|污油回收', '曲轴箱与油气管理子系统'),
        (r'轴承|轴瓦', '轴承支承子系统'),
        (r'循环润滑|滑油泵|机油泵|油底壳|油柜|油箱|油道|油通道|机外滑油|压力润滑|润滑装置|滑油装置', '润滑供油子系统')),
    '冷却与海水系统': (
        (r'海水.*冷却|海水空冷|海水.*泵', '海水冷却与供水子系统'),
        (r'淡水|缸套冷却|冷却水|高温水|低温水|暖缸|恒温阀|膨胀水箱', '淡水冷却与暖缸子系统'),
        (r'滑油冷却器|机油冷却器|燃油冷却器', '滑油与燃油冷却子系统'),
        (r'舱底|排水|压载', '舱底排水与辅助水路子系统')),
    '传动与推进系统': (
        (r'齿轮箱|减速箱|减速齿轮', '传动齿轮箱子系统'),
        (r'轴系|联轴器|联轴节|联轴|刚性联接|尾轴', '轴系与联轴子系统'),
        (r'曲轴|连杆|运动机构|正时齿轮|凸轮轴传动', '曲柄连杆与机内传动子系统'),
        (r'螺旋桨|推进|舵桨|离合|可调螺距', '螺旋桨与推进执行子系统')),
    '电力与控制系统': (
        (r'发电机|励磁', '发电与励磁子系统'),
        (r'电网|配电|断路器|汇流排|主开关|出线开关|谐波滤波', '配电与电网子系统'),
        (r'控制|调速|传感|监测|安保|电控|PLC|ADU|Pt100|仪表|检测|遥控|保护|反馈', '监测控制与保护子系统')),
}

def classify_equipment(name):
    """Curator functional index, not a physical cause inferred from keywords.

    Multi-role equipment can have several memberships. A plain engine model
    without a functional cue receives no invented detailed classification.
    """
    return [(parent,leaf) for parent,rules in RULES.items() for pattern,leaf in rules
            if re.search(pattern,name,re.I)]

def add_grounded_leaf_links(builder, registry):
    original = list(builder.edges.values())
    matched = []; seen=set(); hierarchy=set()
    for edge in original:
        if edge['relation'] != 'SERVES_SYSTEM':
            continue
        equipment = builder.nodes[edge['source']]
        # Original broad memberships are source/case context, not necessarily
        # mutually-exclusive engineering ownership. Preserve them transparently.
        edge['props']['classification_role']='source_context'
        builder.assertions[edge['props']['assertion_id']]['classification_role']='source_context'
        for parent,leaf_name in classify_equipment(equipment['name']):
            key=(edge['source'],parent,leaf_name,edge['props']['source_id'])
            if key in seen:continue
            seen.add(key)
            pid=edge['props']['passage_id']
            passage=registry.passages.get(pid)
            if passage is None:
                raise ValueError('Missing evidence for existing system link: '+pid)
            leaf=builder.node('System', leaf_name, system_level='functional_subsystem_detail',
                              ontology_origin='curator_functional_taxonomy',
                              classification_basis='设备名称显式功能线索；非原文因果声明')
            parent_id=builder.node('System',parent,system_level='functional_subsystem')
            scope='ontology:functional_detail:'+leaf_name
            builder.documented(leaf, passage, scope)
            if (leaf,parent_id) not in hierarchy:
                builder.edge(leaf,'IS_SUBSYSTEM_OF',parent_id,passage,scope,
                             nature='curator_functional_taxonomy',
                             classification_role='ontology_hierarchy',
                             applicability='实验检索本体分组；不是资料原文中的故障因果声明')
                hierarchy.add((leaf,parent_id))
            builder.edge(edge['source'],'SERVES_SYSTEM',leaf,passage,
                         edge['props']['scope_id'],nature='functional_classification',
                         classification_role='curator_functional_membership',
                         applicability='依据设备名称字面线索归入细分系统，需后续复核')
            matched.append((equipment['name'],parent,leaf_name))
    return matched
