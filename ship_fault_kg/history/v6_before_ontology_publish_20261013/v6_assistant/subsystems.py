"""Conservative, explicitly derived functional sub-system index.

These are ontology groupings for retrieval, not source-authored fault claims.
Only an equipment name with an unambiguous literal cue receives a leaf link.
"""
import re

RULES = {
    '燃油与进排气系统': (
        (r'喷油|燃油|油泵|共轨', '燃油供给与喷射子系统'),
        (r'增压|进气|空冷|扫气', '增压与进气子系统'),
        (r'排气|气阀', '排气与配气子系统')),
    '润滑与轴承系统': (
        (r'滑油|润滑|注油', '润滑供油子系统'),
        (r'轴承|轴瓦', '轴承支承子系统')),
    '冷却与海水系统': (
        (r'海水|舱底', '海水与舱底子系统'),
        (r'淡水|缸套水|冷却水', '淡水冷却子系统')),
    '传动与推进系统': (
        (r'齿轮箱|减速箱', '传动齿轮箱子系统'),
        (r'轴系|联轴器|联轴节|轴带', '轴系与联轴子系统'),
        (r'螺旋桨|推进器|舵桨', '螺旋桨与推进执行子系统')),
    '电力与控制系统': (
        (r'发电机|励磁', '发电与励磁子系统'),
        (r'电网|配电|断路器|汇流排', '配电与电网子系统'),
        (r'控制|调速|传感|监测|安保', '监测控制与保护子系统')),
}

def add_grounded_leaf_links(builder, registry):
    original = list(builder.edges.values())
    matched = []
    for edge in original:
        if edge['relation'] != 'SERVES_SYSTEM':
            continue
        equipment = builder.nodes[edge['source']]
        parent = builder.nodes[edge['target']]['name']
        for pattern, leaf_name in RULES.get(parent, ()):
            if not re.search(pattern, equipment['name'], re.I):
                continue
            pid=edge['props']['passage_id']
            passage=registry.passages.get(pid)
            if passage is None:
                raise ValueError('Missing evidence for existing system link: '+pid)
            leaf=builder.node('System', leaf_name, system_level='functional_subsystem_detail',
                              ontology_origin='curator_literal_equipment_name_rule')
            scope='ontology:functional_detail:'+leaf_name
            builder.documented(leaf, passage, scope)
            if not any(e['source']==leaf and e['target']==edge['target'] and
                       e['relation']=='IS_SUBSYSTEM_OF' for e in builder.edges.values()):
                builder.edge(leaf,'IS_SUBSYSTEM_OF',edge['target'],passage,scope,
                             nature='curator_functional_taxonomy',
                             applicability='实验检索本体分组；不是资料原文中的故障因果声明')
            builder.edge(edge['source'],'SERVES_SYSTEM',leaf,passage,
                         edge['props']['scope_id'],nature='functional_classification',
                         applicability='依据设备名称字面线索归入细分系统，需后续复核')
            matched.append((equipment['name'],parent,leaf_name))
            break
    return matched
