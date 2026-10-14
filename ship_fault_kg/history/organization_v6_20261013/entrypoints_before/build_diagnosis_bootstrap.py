"""Build transparent synthetic upstream reports and V5-linked development labels.

Standard library only. Reads KG SQLite in read-only mode; never changes the KG.
All numbers, vessel IDs, model outputs and confidence scores are synthetic.
"""
import argparse
import collections
import datetime as dt
import hashlib
import json
import math
import sqlite3
from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]
DB = ROOT / 'ship_fault_kg/output/v5/ship_fault_kg.sqlite'
OUT = ROOT / 'ship_fault_kg/diagnosis_bootstrap/v1'
CAUSAL = {'CAUSES', 'CONTRIBUTES_TO', 'INCREASES_RISK_OF', 'WORSENS'}
DIAGNOSTIC = CAUSAL | {'HAS_MANIFESTATION', 'INDICATES', 'ASSOCIATED_WITH',
                       'CHECKS', 'ADDRESSES', 'PRECEDES'}
SYSTEMS = ['燃油与进排气系统', '润滑与轴承系统', '冷却与海水系统',
           '传动与推进系统', '电力与控制系统']
NOTICE = '合成开发样本；非实船记录。数值、基线和模型分数为人工设定，未经模型训练、概率校准或专家审核。'


def scenario(system, target, scope, equipment, observation, quantities):
    return dict(system=SYSTEMS[system], target=target, scope=scope,
                equipment=equipment, observation=observation, quantities=quantities)


# quantity tuple: name, unit, synthetic baseline, synthetic current, origin role.
# Numeric magnitudes are illustrative fixtures, not manufacturer limits.
SCENARIOS = [
    scenario(0, '缸套黏着拉伤', 'article:src:cef7c2668aad667902214eb9', '低速柴油主机气缸单元',
             '同负荷下单缸排气温度和冷却水出口温度升高，伴随声音沉闷。',
             [('单缸排气温度','°C',360,425,'observed'),('冷却水出口温度','°C',78,89,'observed'),('气缸摩擦强度相对估计值','1',1,1.35,'predicted')]),
    scenario(0, '压气机喘振', 'article:src:99db95aca2e29734039f5ddb', '废气涡轮增压器',
             '增压器径向、轴向振动增大，增压压力出现周期波动。',
             [('径向振动速度RMS','mm/s',2.1,6.3,'observed'),('轴向振动速度RMS','mm/s',1.6,4.7,'observed'),('增压压力波动峰峰值','MPa',0.01,0.045,'observed')]),
    scenario(0, '喷油器针阀过热卡死', 'article:src:430ee12a295bd84f23acbc26', '柴油机喷油单元',
             '某缸排气温度降低，模型估计该缸燃烧贡献下降。',
             [('单缸排气温度','°C',350,245,'observed'),('单缸转矩贡献相对估计值','1',1,0.58,'predicted')]),
    scenario(0, '共轨冲洗单向阀止回失效', 'article:src:1b6d84a474f7c6ab85c7806f', '高压共轨燃油喷射装置',
             '低压供油支路压力异常上升，同时共轨保压衰减加快。',
             [('低压供油支路压力','MPa',0.6,1.05,'observed'),('共轨压力相对衰减率','%/min',2,11,'predicted')]),
    scenario(0, '高压油泵节流阀小开度卡滞', 'article:src:1b6d84a474f7c6ab85c7806f', '高压共轨燃油喷射装置',
             '供油需求增加时共轨压力跟踪不足，模型估计高压泵进油量偏低。',
             [('共轨压力跟踪相对误差','%',2,15,'observed'),('高压泵进油量相对估计值','1',1,0.68,'predicted')]),
    scenario(0, '排气阀无法开启', 'article:src:e3211dc804eb4d5f9607758a', '共轨柴油机排气阀驱动单元',
             '阀门有开启指令但升程反馈接近零，共轨滑油压力下降。',
             [('排气阀相对升程','1',1,0.04,'observed'),('共轨滑油相对压力','1',1,0.52,'observed')]),
    scenario(0, '压气机空气滤清器堵塞', 'article:src:7d933cc0b95b8764a8dc264e', '柴油发电机进气滤清单元',
             '滤器前后压差增加，模型估计进气流阻增大。',
             [('进气滤器压差','kPa',1.5,4.8,'observed'),('进气流阻相对估计值','1',1,1.75,'predicted')]),
    scenario(0, '喷油器弹簧断裂', 'article:src:1b6d84a474f7c6ab85c7806f', '高压共轨燃油喷射装置',
             '单缸排气温度偏高，喷油控制表现与其他缸不一致。',
             [('单缸排气温度','°C',355,418,'observed'),('缸间排温差','°C',12,65,'observed')]),
    scenario(1, '主轴承咬死', 'reference:knowledge:bearing_seizure', '柴油机主轴承单元',
             '油雾报警重复出现，轴承磨损监测变化明显，轴承温度上升。',
             [('主轴承温度','°C',62,92,'observed'),('油雾相对浓度','1',1,2.7,'observed'),('磨损速率相对估计值','1',1,2.4,'predicted')]),
    scenario(1, '滑油滤清器与油道堵塞', 'article:src:50563ebed2cb0b0eb6149cd6', '柴油机滑油供给单元',
             '滤器压差上升，滤后供油压力下降，流量估计值降低。',
             [('滑油滤器压差','MPa',0.03,0.13,'observed'),('滤后滑油压力','MPa',0.42,0.25,'observed'),('滑油流量相对估计值','1',1,0.62,'predicted')]),
    scenario(1, '轴瓦烧伤', 'article:src:50563ebed2cb0b0eb6149cd6', '柴油机连杆轴瓦单元',
             '轴瓦温度升高，供给滑油压力下降，摩擦功耗估计增加。',
             [('轴瓦温度','°C',64,96,'observed'),('供给滑油压力','MPa',0.4,0.23,'observed'),('摩擦功耗相对估计值','1',1,1.6,'predicted')]),
    scenario(1, '增压器轴承磨损', 'article:src:99db95aca2e29734039f5ddb', '废气涡轮增压器轴承',
             '增压器振动和噪声增大，同负荷下转速下降。',
             [('轴承座振动速度RMS','mm/s',2,5.8,'observed'),('增压器相对转速','1',1,0.83,'observed')]),
    scenario(1, '主轴瓦磨损失效', 'article:src:e4c1386b8596127cda940fd2', '柴油机主轴瓦单元',
             '主轴承温度上升，中间层预测润滑油膜厚度及承载能力下降。',
             [('主轴承温度','°C',61,83,'observed'),('油膜厚度相对估计值','1',1,0.55,'predicted'),('油膜承载能力相对估计值','1',1,0.63,'predicted')]),
    scenario(1, '发电机滚动轴承磨损失效', 'reference:knowledge:generator_bearing_wear', '船用发电机滚动轴承',
             '发电机轴承座轴向振动增加，轴承温度呈上升趋势。',
             [('轴向振动速度RMS','mm/s',1.8,5.4,'observed'),('轴承温度','°C',58,77,'observed')]),
    scenario(1, '电机与发电机轴承电蚀', 'reference:knowledge:bearing_electrical_erosion', '船用电机滚动轴承',
             '轴电压与轴电流相对基线增加，同时出现轴承振动异常。',
             [('轴电压RMS','V',0.3,1.6,'observed'),('轴电流RMS','A',0.02,0.15,'observed'),('轴承座振动速度RMS','mm/s',1.9,4.3,'observed')]),
    scenario(1, '活塞环与缸套磨损', 'reference:knowledge:liner_scuffing', '柴油机活塞环与缸套单元',
             '扫气泄放油铁含量增加，中间层估计气缸密封能力下降。',
             [('扫气泄放油铁含量','mg/kg',35,110,'observed'),('气缸密封能力相对估计值','1',1,0.8,'predicted')]),
    scenario(2, '冷却水通道结垢堵塞', 'reference:knowledge:coolant_blockage', '柴油机冷却水通道',
             '冷却支路流量减少，出口温度上升，换热能力估计下降。',
             [('冷却支路流量','m³/h',24,16,'observed'),('冷却水出口温度','°C',78,90,'observed'),('换热能力相对估计值','1',1,0.72,'predicted')]),
    scenario(2, '冷却水管路汽蚀', 'reference:knowledge:cooling_cavitation', '扫气空气冷却器水侧回路',
             '水侧流量降低，压力波动与异常噪声增加，扫气空气温度升高。',
             [('冷却器水侧相对流量','1',1,0.61,'observed'),('水侧压力波动峰峰值','MPa',0.01,0.04,'observed'),('扫气空气温度','°C',42,55,'observed')]),
    scenario(2, '活塞冷却喷嘴板堵塞', 'article:src:70ef59ac24eff8655c9758d8', '柴油机活塞顶部冷却单元',
             '活塞冷却支路流量偏低，模型预测活塞顶部热负荷升高。',
             [('活塞冷却支路相对流量','1',1,0.58,'observed'),('活塞顶部相对热负荷','1',1,1.32,'predicted')]),
    scenario(2, '空压机高压冷却器渗漏', 'article:src:618f2620d0be984a505012a1', '空压机与副机共享淡水冷却回路',
             '空压机投入后共享冷却淡水回路出现气泡，副机冷却压力波动。',
             [('冷却压力波动峰峰值','MPa',0.015,0.065,'observed'),('回路气相占比相对估计值','1',0.01,0.08,'predicted')]),
    scenario(2, '冷却水泵吸空', 'article:src:618f2620d0be984a505012a1', '副机共享冷却淡水回路',
             '淡水泵出口压力间歇下降，流量反馈接近中断，回路有气泡。',
             [('淡水泵出口压力','MPa',0.3,0.12,'observed'),('冷却水相对流量','1',1,0.25,'observed')]),
    scenario(2, '海水泵轴封失效', 'article:src:9608278885fb76338e8f64c4', '柴油机海水冷却泵轴封',
             '海水泵轴封处泄漏量增加，泵轴轴向位移估计值增大。',
             [('轴封相对泄漏量','1',1,4.5,'observed'),('泵轴轴向相对位移','1',1,1.8,'predicted')]),
    scenario(2, '滑油冷却芯体腐蚀破损', 'article:src:9608278885fb76338e8f64c4', '海水冷却式滑油冷却器',
             '滑油含水率上升，冷却器两侧介质压差持续存在。',
             [('滑油含水率','%',0.05,0.35,'observed'),('冷却器海水侧相对滑油侧压差','MPa',0.08,0.08,'observed')]),
    scenario(2, '冷却水温度过高', 'article:src:3f7682b4ff9819c4b36ae512', '柴油机冷却与润滑耦合单元',
             '冷却水与滑油温度同时升高，中间层预测滑油黏度下降。',
             [('冷却水温度','°C',78,91,'observed'),('滑油温度','°C',47,61,'observed'),('滑油相对黏度','1',1,0.74,'predicted')]),
    scenario(3, '离合器打滑', 'article:src:32d7d1ad6f909e0386ecbd5b', '船用减速齿轮箱离合器',
             '离合器接合指令下输入输出转速比偏离，齿轮箱滑油温度持续升高。',
             [('离合器相对滑差','%',1,9,'observed'),('齿轮箱滑油温度','°C',52,76,'observed')]),
    scenario(3, '齿轮疲劳裂纹', 'article:src:32d7d1ad6f909e0386ecbd5b', '船用减速齿轮箱齿轮副',
             '啮合频率边带增加，转矩波动增大；未进行拆检或裂纹探伤。',
             [('齿轮啮合边带相对幅值','1',1,2.2,'observed'),('轴系转矩波动相对幅值','1',1,1.6,'observed')]),
    scenario(3, '齿轮箱内部磨损', 'article:src:32d7d1ad6f909e0386ecbd5b', '船用减速齿轮箱',
             '滑油金属磨屑指标上升，齿轮箱振动增加；尚无内部拆检结论。',
             [('滑油铁含量','mg/kg',18,76,'observed'),('齿轮箱振动速度RMS','mm/s',2.3,4.9,'observed')]),
    scenario(3, '轴带发电机与齿轮箱对中失准', 'reference:knowledge:shaft_generator_alignment', '轴带发电机与齿轮箱联接单元',
             '热态轴向振动增大，热态轴线相对偏移估计值上升。',
             [('热态轴向振动速度RMS','mm/s',2,5.6,'observed'),('热态轴线偏移相对估计值','1',1,2.1,'predicted')]),
    scenario(3, '轴系扭转共振风险', 'reference:knowledge:shaft_torsional', '柴油机推进轴系与联轴器',
             '特定转速带内扭转振动幅值增加，模型估计转矩脉动与轴系响应接近共振。',
             [('扭转振动相对幅值','1',1,2.8,'observed'),('转矩脉动相对幅值','1',1,1.9,'predicted')]),
    scenario(3, 'CPP执行器运动传递失效', 'reference:knowledge:coupling_failure', '可调螺距螺旋桨执行器',
             '驾驶台螺距指令变化后，执行器反馈与实际螺距反馈不同步。',
             [('螺距指令反馈偏差','%',2,28,'observed'),('执行器反馈变化相对幅值','1',1,1,'observed'),('实际螺距变化相对幅值','1',1,0.12,'observed')]),
    scenario(3, '扭振减振器失效', 'reference:knowledge:damper_failure', '柴油机扭振减振器',
             '减振器附近出现异响，机组振动趋势改变，减振能力估计下降。',
             [('机组振动速度RMS','mm/s',2.2,5.1,'observed'),('减振能力相对估计值','1',1,0.57,'predicted')]),
    scenario(3, '主机离合器脱开', 'case:sd2013_02_control_air', '控制空气供给与主机离合装置',
             '控制空气压力下降，随后离合器接合反馈丢失、推进响应减弱。',
             [('控制空气压力','MPa',0.7,0.32,'observed'),('离合器接合反馈','1',1,0,'observed'),('推进转矩相对估计值','1',1,0.15,'predicted')]),
    scenario(4, '发电机绕组绝缘电阻降低', 'reference:knowledge:winding_insulation', '船用发电机绕组绝缘单元',
             '停电隔离后的仿真绝缘检测值低于同温度历史基线，极化指数下降。',
             [('同温度绝缘电阻','MΩ',40,12,'observed'),('极化指数','1',2.2,1.3,'observed')]),
    scenario(4, '船舶电网电压频率振荡', 'reference:knowledge:electrical_oscillation', '含变流器的船舶电网',
             '母线电压和频率出现低频周期波动，发电端转矩估计同时波动。',
             [('母线电压波动峰峰值','%',1,6,'observed'),('频率波动峰峰值','Hz',0.08,0.5,'observed'),('发电端转矩相对波动','1',1,2.0,'predicted')]),
    scenario(4, '测速板整形比较器输出故障', 'article:src:fc3cd905fda8e914de25fe6a', '主机遥控测速信号单元',
             '原始转速信号稳定，整形输出间歇丢失，显示转速跳变。',
             [('原始转速波动峰峰值','r/min',3,3,'observed'),('整形输出丢失率','%',0,14,'observed')]),
    scenario(4, '遥控电源绝缘不良', 'article:src:fc3cd905fda8e914de25fe6a', '主机遥控电源模块',
             '隔离检测得到的电源模块绝缘值下降，遥控装置发生间歇异常。',
             [('电源模块绝缘电阻','MΩ',30,6,'observed'),('遥控信号间歇丢失率','%',0,8,'observed')]),
    scenario(4, '柴油发电机扩展箱故障', 'article:src:56dd07314f198900598d29a2', '柴油发电机主开关扩展箱',
             '并网合闸请求发出后安全联锁回路反馈未闭合，主开关未合闸。',
             [('安全联锁闭合反馈','1',1,0,'observed'),('主开关合闸反馈','1',1,0,'observed')]),
    scenario(4, '安全停车中间继电器故障', 'article:src:56dd07314f198900598d29a2', '柴油发电机安全停车继电器回路',
             '继电器输入条件满足，但触点反馈与指令不一致，主开关合闸受阻。',
             [('继电器触点指令反馈一致率','%',100,58,'observed'),('主开关合闸反馈','1',1,0,'observed')]),
    scenario(4, '发电机内部短路', 'article:src:7d933cc0b95b8764a8dc264e', '柴油发电机定转子单元',
             '三相电流不平衡增大，电流短时上升，同时机内振动增大。',
             [('三相电流不平衡度','%',2,14,'observed'),('电流相对幅值','1',1,1.7,'observed'),('机内相对振动','1',1,2.1,'observed')]),
    scenario(4, '转速传感器感应端损伤', 'article:src:fc3cd905fda8e914de25fe6a', '主机遥控转速传感器',
             '独立转速通道稳定，该传感器脉冲幅值下降并发生漏脉冲。',
             [('测速脉冲相对幅值','1',1,0.48,'observed'),('漏脉冲率','%',0,9,'observed')]),
]


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def jsonl(path, rows):
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')


def load_graph():
    conn = sqlite3.connect('file:' + DB.as_posix() + '?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    nodes = {r['id']: dict(r, props=json.loads(r['props']), aliases=json.loads(r['aliases']))
             for r in conn.execute('SELECT * FROM nodes')}
    edges = [dict(r, props=json.loads(r['props'])) for r in conn.execute('SELECT * FROM edges')]
    claims = {r['id']: json.loads(r['data']) for r in conn.execute('SELECT * FROM assertions')}
    sources = {r['id']: json.loads(r['data']) for r in conn.execute('SELECT * FROM sources')}
    passages = {r['id']: json.loads(r['data']) for r in conn.execute('SELECT * FROM passages')}
    conn.close()
    return nodes, edges, claims, sources, passages


def resolve_target(name, nodes):
    found = [n for n in nodes.values() if n['name'] == name and n['props']['entity_level'] == 'concept']
    if len(found) != 1:
        raise ValueError('Target must resolve to exactly one concept: ' + name)
    return found[0]


def local_evidence(s, nodes, edges, claims, sources):
    target = resolve_target(s['target'], nodes)
    seed = {target['id']} | {e['source'] for e in edges
                            if e['relation'] == 'INSTANCE_OF' and e['target'] == target['id']}
    pool = [e for e in edges if e['props']['scope_id'] == s['scope'] and e['relation'] in DIAGNOSTIC]
    direct = [e for e in pool if e['source'] in seed or e['target'] in seed]
    if not direct:
        raise ValueError('No scoped diagnostic evidence: ' + s['target'])
    # At most one causal neighbor beyond the seed; checks/actions attached to
    # those physical states are suggestions for review, not exhaustive gold.
    touched = seed | {x for e in direct if e['relation'] in CAUSAL
                      for x in (e['source'], e['target'])}
    chosen = [e for e in pool if e in direct or
              (e['relation'] in CAUSAL | {'CHECKS','ADDRESSES'} and
               (e['source'] in touched or e['target'] in touched))]
    bundles = []
    for e in sorted(chosen, key=lambda e: e['id']):
        c = claims[e['assertion_id']]
        src = sources[c['source_id']]
        bundles.append(dict(assertion_id=c['id'], edge_id=e['id'],
            subject_id=e['source'], subject=nodes[e['source']]['name'],
            relation=e['relation'], relation_name=e['props']['name'],
            object_id=e['target'], object=nodes[e['target']]['name'],
            scope_id=c['scope_id'], source_id=c['source_id'], passage_id=c['passage_id'],
            quote=c['quote'], page=c['page'], locator=c['locator'],
            normalized_start=c['normalized_start'], normalized_end=c['normalized_end'],
            certainty=c['certainty'], applicability=c['applicability'],
            action_status=c['action_status'], expert_review=c['expert_review'],
            source_title=src['title'], source_url=src['url'], source_sha256=src['sha256']))
    paths = []
    grouped = collections.defaultdict(list)
    for b in bundles:
        if b['relation'] in CAUSAL:
            grouped[b['source_id']].append(b)
    for source_id, facts in grouped.items():
        adjacency = collections.defaultdict(list)
        for b in facts:
            adjacency[b['subject_id']].append(b)
        def visit(current, ids, chain):
            if len(chain) >= 2 and seed.intersection(ids):
                paths.append(dict(node_ids=ids, assertion_ids=[x['assertion_id'] for x in chain],
                    scope_id=s['scope'], source_id=source_id,
                    review_status='candidate_path_not_expert_validated'))
            if len(chain) == 3:
                return
            for b in adjacency[current]:
                if b['object_id'] not in ids:
                    visit(b['object_id'], ids + [b['object_id']], chain + [b])
        for start in sorted(adjacency):
            visit(start, [start], [])
    return target, bundles, paths


def quantities(s, number, normal=False, missing=False):
    result = []
    for i, (name, unit, base, value, role) in enumerate(s['quantities'], 1):
        # Both variants in a pair receive identical numerical values.
        if normal:
            value = base
        elif unit not in ('1','%') and value != base:
            precision = {'°C':1, 'mm/s':2, 'MPa':3, 'kPa':2, 'r/min':1,
                         'MΩ':2, 'mg/kg':1, 'V':3, 'A':4, 'Hz':3}.get(unit,2)
            value = round(value * (1 + ((number % 5) - 2) * 0.004), precision)
        if missing:
            value = None
        delta = None if value is None else round(value - base, 4)
        trend = 'unknown' if value is None else ('stable' if value == base else ('up' if value > base else 'down'))
        result.append(dict(quantity_id='P%02d' % i, name=name, value=value, unit=unit,
            channel_role=role, acquisition='synthetic_sensor_fixture' if role == 'observed' else 'synthetic_intermediate_prediction',
            baseline_value=None if missing else base, baseline_basis='synthetic_same_condition_reference_not_oem_limit',
            delta_from_baseline=delta, trend=trend, validity='missing' if missing else 'synthetic_available',
            engineering_threshold=None, threshold_source=None,
            uncertainty=dict(standard_deviation=None, reason='未构造预测分布，不虚构标准差或置信区间')))
    return result


def make_report(s, scene_index, variant, report_index, target):
    normal = variant == 'negated_normal'
    missing = variant == 'missing_fields'
    physical = quantities(s, scene_index, normal, missing)
    if variant == 'explicit_fault':
        text = '初步诊断：疑似%s。%s尚未经现场检查确认。' % (s['target'], s['observation'])
        candidates = [dict(name=s['target'], category='fault_hypothesis' if target['kind']=='Fault' else 'abnormal_state',
                           status='suspected', model_score=round(0.7 + scene_index % 6 * 0.03, 2))]
        observation = s['observation']
        score_target = '候选故障或异常状态的模型输出分数'
    elif variant == 'symptom_only':
        observation = s['observation']
        text = '初步诊断：%s目前仅识别到异常表现，未输出具体故障名称。' % observation
        candidates = []
        score_target = '异常状态识别的模型输出分数，非根因置信度'
    elif normal:
        observation = '同工况监测值与仿真基线一致，本窗口未观察到上述异常。'
        text = '初步诊断：本窗口未发现%s，监测值与仿真基线一致。否定结论仅覆盖当前窗口，不能排除全部潜在故障。' % s['target']
        candidates = [dict(name=s['target'], category='excluded_hypothesis', status='not_observed_in_window', model_score=None)]
        score_target = '当前窗口正常状态的模型输出分数'
    elif missing:
        observation = '仅收到异常标志；关键物理量缺失，设备具体型号与工况未提供。'
        text = '初步诊断：%s现有信息不足以命名具体故障，请先补齐数据。' % observation
        candidates = []
        score_target = '未提供'
    elif variant == 'competing_hypotheses':
        observation = s['observation']
        text = '初步诊断：%s现有表现可由多种原因引起，上游未给出唯一故障结论。' % observation
        candidates = []
        score_target = '异常状态识别分数；未提供各根因概率'
    else:
        observation = s['observation']
        text = '初步诊断：疑似%s。%s当前设备型号未提供，未给出适用厂家阈值。' % (s['target'], observation)
        candidates = [dict(name=s['target'], category='fault_hypothesis' if target['kind']=='Fault' else 'abnormal_state', status='suspected', model_score=0.73)]
        score_target = '候选故障或异常状态的模型输出分数'
    if missing:
        score = None
    elif candidates and variant != 'negated_normal':
        score = candidates[0]['model_score']
    else:
        score = 0.84 if normal else 0.61
    confidence = dict(value=score, target=score_target, method='synthetic_fixture_assigned' if score is not None else 'not_available',
        calibrated=False, probability_interpretation=False, method_version=None,
        stochastic_constraint_result=None, prediction_distribution=None,
        explanation='人工设定的接口测试分数；不代表师兄的随机性约束方法，不能解释为实际正确概率。')
    goal = {
        'explicit_fault':'检索候选故障的参考机理、相关症状、建议检查与参考措施，保留出处和适用范围。',
        'symptom_only':'从设备和症状召回可能相关机理，给出需补充的检查证据，不确诊唯一根因。',
        'negated_normal':'保留否定信息；如返回知识，仅作为条件性参考，不将未观察到的故障转成肯定诊断。',
        'missing_fields':'指出缺少物理量、型号和工况；允许条件性参考，不编造数值、故障或置信度。',
        'competing_hypotheses':'提供鉴别检查和备选解释；不得把非特异性症状归为唯一根因。',
        'unsupported_threshold':'请给出该设备的精确报警阈值、维修扭矩和可运行时长；若缺少本机厂家资料，应明确无法确定。',
    }[variant]
    model_name = 'SIM-DL-interface-fixture-v1'
    report_id = 'DR-%03d' % report_index
    clock = dt.datetime(2026,10,12,8,0,tzinfo=dt.timezone(dt.timedelta(hours=8))) + dt.timedelta(minutes=5*scene_index)
    trend_words = {'up':'上升','down':'下降','stable':'保持基线','unknown':'缺失'}
    changes = '；'.join(p['quantity_id']+' '+p['name']+trend_words[p['trend']] for p in physical)
    interpretation = ('关键物理量缺失，目前只能保留异常标志，不能形成数值证据链。' if missing else
        changes+'。'+('这些量与本窗口正常描述一致。' if normal else
        ('将上述变化作为候选判断的输入依据，仍需检索与现场检查区分其他解释。' if candidates else
         '将上述变化组织为异常线索，尚不能确定具体故障。')))
    chains = [dict(chain_id='U01', observation_id='O01', quantity_ids=[p['quantity_id'] for p in physical],
        inference_type='upstream_hypothesis_not_kg_causal_chain',
        interpretation=interpretation,
        verified_root_cause=False)]
    trace = '初步溯源仅追溯到输入观测和中间层预测；具体根因、检查依据及措施出处留待知识检索补充。'
    return dict(schema_version='upstream_diagnosis_report/1.0', report_id=report_id,
        generated_at=clock.isoformat(), data_status='synthetic_bootstrap', disclaimer=NOTICE,
        equipment=dict(vessel_id='SIM-VESSEL-%02d' % (SYSTEMS.index(s['system'])+1),
                       system=s['system'], equipment_name=s['equipment'], equipment_model=None,
                       equipment_id='SIM-EQ-%02d' % scene_index, architecture_status='not_verified_against_real_vessel'),
        operating_context=dict(load_pct=None if missing else (0 if '绝缘' in s['target'] else 45+scene_index%6*5),
            operating_mode='unknown' if missing else ('隔离检测仿真' if '绝缘' in s['target'] else '稳定负荷仿真窗口'),
            observation_window_seconds=300, sampling_interval_seconds=None,
            context_origin='synthetic_fixture', ambient_temperature_c=None),
        upstream_model=dict(model_id=model_name, model_version='1.0', trained_model=False,
            raw_signal_reference=None, intermediate_prediction_reference=None),
        diagnosis=dict(summary=text, candidates=candidates, confirmed_root_cause=None,
            diagnostic_status='insufficient_information' if missing else ('no_abnormality_observed' if normal else 'preliminary'),
            confidence=confidence),
        physical_quantities=physical,
        observations=[dict(observation_id='O01', description=observation,
            polarity='negative' if normal else ('unknown' if missing else 'positive'),
            quantity_ids=[p['quantity_id'] for p in physical])],
        initial_evidence_chain=chains, initial_trace_text=trace,
        missing_information=['设备型号与适用手册','真实原始信号及采样信息','预测分布与置信度计算方法','现场检查结论'] +
                            (['关键物理量','负荷与运行模式'] if missing else []),
        retrieval_request=dict(goal=goal, preserve_upstream_confidence=True,
            manufacturer_threshold_required=variant=='unsupported_threshold'))


def retrieval_input(report):
    e = report['equipment']; ctx = report['operating_context']
    lines = ['数据性质：人工合成开发输入，非实船记录；数值和分数均为接口测试设定。',
             '设备：%s；子系统：%s。' % (e['equipment_name'],e['system']),
             '型号：未提供；运行模式：%s；负荷：%s。' % (ctx['operating_mode'], '未提供' if ctx['load_pct'] is None else str(ctx['load_pct'])+'%'),
             report['diagnosis']['summary']]
    for p in report['physical_quantities']:
        lines.append('物理量%s：%s %s；同工况仿真基线：%s；来源：%s。' %
                     (p['name'],p['value'] if p['value'] is not None else '缺失',p['unit'],
                      p['baseline_value'] if p['baseline_value'] is not None else '缺失',
                      '中间层预测' if p['channel_role']=='predicted' else '仿真观测'))
    c = report['diagnosis']['confidence']
    lines += ['模型分数：%s；%s；未经校准。' % (c['value'] if c['value'] is not None else '未提供',c['target']),
              report['initial_trace_text'], '检索任务：'+report['retrieval_request']['goal']]
    return '\n'.join(lines)


def render_report(r):
    ctx=r['operating_context']; c=r['diagnosis']['confidence']
    rows = ['# 船舶动力系统初始诊断报告｜'+r['report_id'],'', '**数据性质：** '+NOTICE,'',
        '## 1. 基本信息与工况','',
        '- 仿真船舶编号：'+r['equipment']['vessel_id'],
        '- 子系统：'+r['equipment']['system'], '- 设备：'+r['equipment']['equipment_name'],
        '- 型号：未提供；报告时间：'+r['generated_at'],
        '- 运行模式：%s；负荷：%s；观测窗口：300秒。' % (ctx['operating_mode'],str(ctx['load_pct'])+'%' if ctx['load_pct'] is not None else '未提供'),'',
        '## 2. 诊断结果','',r['diagnosis']['summary'],'',
        '## 3. 依据物理量','',
        '| 编号 | 物理量 | 当前值 | 单位 | 同工况仿真基线 | 类型 |','| --- | --- | ---: | --- | ---: | --- |']
    for p in r['physical_quantities']:
        rows.append('| %s | %s | %s | %s | %s | %s |' % (p['quantity_id'],p['name'],p['value'] if p['value'] is not None else '缺失',
            p['unit'],p['baseline_value'] if p['baseline_value'] is not None else '缺失',
            '中间层预测' if p['channel_role']=='predicted' else '仿真观测'))
    rows += ['', '基线用于同工况比较，不是厂家报警或维修阈值；本表不是完整时序数据。', '',
        '## 4. 诊断置信度','',
        '- 分数：%s；评价对象：%s。' % (c['value'] if c['value'] is not None else '未提供',c['target']),
        '- '+c['explanation'],'', '## 5. 初步诊断溯源与证据链','',
        'O01：'+r['observations'][0]['description'], '',
        'U01：'+r['initial_evidence_chain'][0]['interpretation'],'',r['initial_trace_text'],'',
        '## 6. 不确定性与待补充信息','']
    rows += ['- '+x for x in r['missing_information']]
    rows += ['', '## 7. 后续知识检索任务','',r['retrieval_request']['goal'],'']
    return '\n'.join(rows)


TEMPLATE = '''# 船舶动力系统初始诊断报告模板 v1.0

用途：承接深度学习诊断结果及中间层物理量，作为知识检索输入。适用于师兄的初始报告；知识增强报告在其后追加，不覆盖初始判断。

## 1. 基本信息与工况

- 报告编号：{{report_id}}
- 数据性质：{{真实/仿真/人工合成}}；原始信号索引：{{raw_signal_reference}}
- 船舶/设备编号：{{vessel_id}} / {{equipment_id}}
- 子系统、设备、具体型号：{{system}} / {{equipment_name}} / {{equipment_model或未提供}}
- 时间、负荷、运行模式、观测窗口和采样信息：{{operating_context}}
- 上游模型及版本：{{model_id}} / {{model_version}}

## 2. 诊断结果

{{diagnosis.summary}}

候选故障/异常状态及状态：{{diagnosis.candidates}}。分别保留“疑似”“已排除”“正常窗口”“信息不足”；没有故障名称时不补编。未经核验，confirmed_root_cause为null。

## 3. 依据物理量

| 编号 | 名称 | 数值 | 单位 | 观测/中间层预测 | 比较基线及出处 | 不确定性/缺失 |
| --- | --- | --- | --- | --- | --- | --- |
| P01 | {{name}} | {{value或null}} | {{unit}} | {{channel_role}} | {{baseline_value及basis}} | {{uncertainty}} |

区分测量值、预测物理量、派生特征。保留原生单位，不把未标定信号转换为工程量；基线不能直接当报警阈值。缺失值使用null，不用0代替。

## 4. 诊断置信度

- 分数/概率及评价对象：{{value}} / {{target}}
- 方法、版本、校准状态及随机性约束结果：{{method}} / {{method_version}} / {{calibrated}} / {{stochastic_constraint_result}}
- 预测分布与区间：{{prediction_distribution或null}}
- 解释：{{explanation}}

方法未提供时标“未经校准的模型分数”或“未提供”。检索相似度不能替换诊断置信度，不能用规则任意抬高上游分数。

## 5. 初步诊断溯源与证据链

O01：{{observations}} → P01/P02：{{physical_quantities}} → U01：{{初步判断及假设}}。

{{initial_trace_text}}

此处只解释初步结果来自哪些观测及预测，关联不能直接升级为因果。具体根因与知识出处留待后续检索；不提前写入参考答案、图谱ID、引用原文或完整因果链。

## 6. 不确定性与待补充信息

{{missing_information}}。说明尚无现场检查、型号/工况缺失、物理量预测不确定性，以及存在的备选解释。

## 7. 后续知识检索任务

{{retrieval_request.goal}}

输入到检索器：设备/型号/工况 + 初步诊断 + 关键物理量 + 否定和不确定性 + 检索目标。参考标注单独读取，禁止拼入检索输入。

## 8. 后续知识增强报告追加区（本批初始报告不预填）

1. 保留原始诊断及置信度。
2. 追加参考机理、候选因果路径与适用条件。
3. 追加鉴别检查、参考措施及出处。
4. 标明哪些内容是上游观测，哪些是图谱/原文知识，哪些是假设。
5. 明确证据缺口与冲突；没有型号及适用手册时不生成精确维修参数。

本批样本全部为人工合成开发数据。该模板尚未对照船级社专业术语文件或师兄实际接口确认，不宣称属于船级社规范模板。
'''


def schema():
    nullable_number = {'type':['number','null']}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema',
        'title':'上游初始诊断报告 v1.0', 'type':'object', 'additionalProperties':False,
        'required':['schema_version','report_id','generated_at','data_status','disclaimer','equipment','operating_context',
                    'upstream_model','diagnosis','physical_quantities','observations','initial_evidence_chain',
                    'initial_trace_text','missing_information','retrieval_request'],
        'properties':{
            'schema_version':{'const':'upstream_diagnosis_report/1.0'},
            'report_id':{'type':'string','minLength':1},'generated_at':{'type':'string','format':'date-time'},
            'data_status':{'enum':['synthetic_bootstrap','simulation','real']},'disclaimer':{'type':'string'},
            'equipment':{'type':'object','required':['vessel_id','system','equipment_name','equipment_model','equipment_id','architecture_status'],
                'properties':{k:{'type':['string','null']} for k in ['vessel_id','system','equipment_name','equipment_model','equipment_id','architecture_status']}},
            'operating_context':{'type':'object','required':['load_pct','operating_mode','observation_window_seconds','context_origin'],
                'properties':{'load_pct':{'type':['number','null'],'minimum':0,'maximum':100},'operating_mode':{'type':'string'},
                    'observation_window_seconds':{'type':'integer','minimum':1},'sampling_interval_seconds':nullable_number,
                    'context_origin':{'type':'string'},'ambient_temperature_c':nullable_number}},
            'upstream_model':{'type':'object','required':['model_id','model_version','trained_model','raw_signal_reference','intermediate_prediction_reference'],
                'properties':{'model_id':{'type':'string'},'model_version':{'type':'string'},'trained_model':{'type':'boolean'},
                    'raw_signal_reference':{'type':['string','null']},'intermediate_prediction_reference':{'type':['string','null']}}},
            'diagnosis':{'type':'object','required':['summary','candidates','confirmed_root_cause','diagnostic_status','confidence'],
                'properties':{'summary':{'type':'string','minLength':1},'confirmed_root_cause':{'type':['string','null']},
                    'diagnostic_status':{'enum':['preliminary','no_abnormality_observed','insufficient_information','confirmed']},
                    'candidates':{'type':'array','items':{'type':'object','required':['name','category','status','model_score'],
                        'properties':{'name':{'type':'string'},'category':{'enum':['fault_hypothesis','abnormal_state','excluded_hypothesis']},
                            'status':{'type':'string'},'model_score':{'type':['number','null'],'minimum':0,'maximum':1}}}},
                    'confidence':{'type':'object','required':['value','target','method','calibrated','probability_interpretation','explanation'],
                        'properties':{'value':{'type':['number','null'],'minimum':0,'maximum':1},'target':{'type':'string'},
                            'method':{'type':'string'},'calibrated':{'type':'boolean'},'probability_interpretation':{'type':'boolean'},
                            'method_version':{'type':['string','null']},'stochastic_constraint_result':{},
                            'prediction_distribution':{},'explanation':{'type':'string'}}}}},
            'physical_quantities':{'type':'array','minItems':1,'items':{'type':'object',
                'required':['quantity_id','name','value','unit','channel_role','acquisition','baseline_value','baseline_basis',
                            'delta_from_baseline','trend','validity','engineering_threshold','threshold_source','uncertainty'],
                'properties':{'quantity_id':{'type':'string'},'name':{'type':'string'},'value':nullable_number,'unit':{'type':'string'},
                    'channel_role':{'enum':['observed','predicted','derived']},'acquisition':{'type':'string'},
                    'baseline_value':nullable_number,'baseline_basis':{'type':'string'},'delta_from_baseline':nullable_number,
                    'trend':{'enum':['up','down','stable','unknown']},'validity':{'type':'string'},
                    'engineering_threshold':nullable_number,'threshold_source':{'type':['string','null']},'uncertainty':{'type':'object'}}}},
            'observations':{'type':'array','minItems':1,'items':{'type':'object','required':['observation_id','description','polarity','quantity_ids'],
                'properties':{'observation_id':{'type':'string'},'description':{'type':'string'},'polarity':{'enum':['positive','negative','unknown']},
                    'quantity_ids':{'type':'array','items':{'type':'string'}}}}},
            'initial_evidence_chain':{'type':'array','items':{'type':'object','required':['chain_id','observation_id','quantity_ids','inference_type','interpretation','verified_root_cause'],
                'properties':{'chain_id':{'type':'string'},'observation_id':{'type':'string'},'quantity_ids':{'type':'array','items':{'type':'string'}},
                    'inference_type':{'type':'string'},'interpretation':{'type':'string'},'verified_root_cause':{'type':'boolean'}}}},
            'initial_trace_text':{'type':'string'},'missing_information':{'type':'array','items':{'type':'string'}},
            'retrieval_request':{'type':'object','required':['goal','preserve_upstream_confidence','manufacturer_threshold_required'],
                'properties':{'goal':{'type':'string'},'preserve_upstream_confidence':{'type':'boolean'},'manufacturer_threshold_required':{'type':'boolean'}}}}}


def validate_schema_keywords(value, spec, path='$'):
    """Validate the exact keywords used by our schema, without dependencies.

    This is NOT a general Draft 2020-12 implementation. Reject unsupported
    keywords rather than silently pretending to validate a future schema.
    """
    supported={'$schema','title','type','additionalProperties','required','properties','const',
               'minLength','format','minimum','maximum','enum','items','minItems'}
    unknown=set(spec)-supported
    if unknown: raise ValueError('Unsupported schema keywords: '+str(unknown))
    errors=[]
    types=spec.get('type',[])
    if isinstance(types,str): types=[types]
    predicates={'null':lambda v:v is None,'string':lambda v:isinstance(v,str),
        'boolean':lambda v:isinstance(v,bool),'number':lambda v:type(v) in (int,float) and math.isfinite(v),
        'integer':lambda v:type(v) is int,'object':lambda v:isinstance(v,dict),'array':lambda v:isinstance(v,list)}
    if types and not any(predicates[t](value) for t in types):
        return [path+': invalid type']
    if 'const' in spec and value!=spec['const']:errors.append(path+': wrong constant')
    if 'enum' in spec and value not in spec['enum']:errors.append(path+': outside enum')
    if type(value) in (int,float):
        if 'minimum' in spec and value<spec['minimum']:errors.append(path+': below minimum')
        if 'maximum' in spec and value>spec['maximum']:errors.append(path+': above maximum')
    if isinstance(value,str):
        if len(value)<spec.get('minLength',0):errors.append(path+': too short')
        if spec.get('format')=='date-time':
            try:
                stamp=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
                if stamp.tzinfo is None:errors.append(path+': timezone required')
            except ValueError:errors.append(path+': invalid date-time')
    if isinstance(value,dict):
        for required in spec.get('required',[]):
            if required not in value:errors.append(path+': missing '+required)
        props=spec.get('properties',{})
        if spec.get('additionalProperties') is False and set(value)-set(props):
            errors.append(path+': unexpected properties')
        for key,item in value.items():
            if key in props:errors+=validate_schema_keywords(item,props[key],path+'.'+key)
    if isinstance(value,list):
        if len(value)<spec.get('minItems',0):errors.append(path+': too few items')
        for index,item in enumerate(value):
            errors+=validate_schema_keywords(item,spec.get('items',{}),path+'[%d]'%index)
    return errors


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    nodes, edges, claims, sources, passages = load_graph()
    before = hashlib.sha256(DB.read_bytes()).hexdigest()
    reports=[]; inputs=[]; labels=[]; catalog=[]
    for idx, s in enumerate(SCENARIOS, 1):
        target,bundle,paths=local_evidence(s,nodes,edges,claims,sources)
        local_index=(idx-1)%8
        split='bootstrap_dev' if local_index < 5 else 'bootstrap_check'
        catalog.append(dict(scenario_id='SC-%02d'%idx,split=split,system=s['system'],
            target_id=target['id'],target_name=s['target'],target_kind=target['kind'],
            scope_id=s['scope'],equipment=s['equipment'],synthetic_observation=s['observation'],
            observation_authorship='assistant_authored_hypothetical_not_source_measurement',
            supporting_assertion_ids=[b['assertion_id'] for b in bundle]))
        for variant in ['explicit_fault','symptom_only']:
            r=make_report(s,idx,variant,len(reports)+1,target)
            reports.append(r)
            inputs.append(dict(report_id=r['report_id'],diagnosis_text=retrieval_input(r)))
            labels.append(dict(report_id=r['report_id'],scenario_group_id='SC-%02d'%idx,
                split=split,system=s['system'],sample_type=variant,
                label_status='silver_development_reference_pending_expert_review',
                intended_target_concept_id=target['id'],intended_target_name=s['target'],intended_target_kind=target['kind'],
                target_interpretation='合成场景预设的检索目标，不是从症状确诊的根因；非唯一相关答案。',
                relevance_completeness='partial_not_exhaustive',
                permitted_scope_ids=[s['scope']],reference_assertion_ids=[b['assertion_id'] for b in bundle],
                reference_passage_ids=sorted({b['passage_id'] for b in bundle}),
                reference_source_ids=sorted({b['source_id'] for b in bundle}),
                candidate_paths=paths,reference_evidence=bundle,
                expected_behavior=['return_conditional_reference','preserve_confidence','preserve_scope_and_certainty','cite_evidence',
                    'do_not_confirm_root_cause_from_simulation'],
                forbidden_behavior=['invent_measurements','invent_oem_limits','upgrade_risk_to_confirmed_cause','cross_scope_causal_concatenation']))
    # Separate challenge fixtures: no fabricated graph relevance set.
    types=['negated_normal','missing_fields','competing_hypotheses','unsupported_threshold']
    behaviors={
        'negated_normal':['preserve_negation','do_not_assert_excluded_fault','conditional_reference_is_allowed'],
        'missing_fields':['request_missing_quantities_model_and_context','do_not_invent_confidence','conditional_reference_is_allowed'],
        'competing_hypotheses':['avoid_unique_root_cause','request_discriminating_checks','conditional_reference_is_allowed'],
        'unsupported_threshold':['abstain_from_exact_threshold_torque_and_runtime','request_model_specific_manual','conditional_reference_is_allowed'],
    }
    for system_index in range(5):
        for j,variant in enumerate(types):
            s=SCENARIOS[system_index*8+j]
            target=resolve_target(s['target'],nodes)
            r=make_report(s,41+system_index*4+j,variant,len(reports)+1,target)
            reports.append(r);inputs.append(dict(report_id=r['report_id'],diagnosis_text=retrieval_input(r)))
            labels.append(dict(report_id=r['report_id'],scenario_group_id='EDGE-%d-%d'%(system_index+1,j+1),
                split='bootstrap_dev' if j<2 else 'bootstrap_check', system=s['system'],sample_type=variant,
                label_status='behavioral_fixture_pending_human_review',intended_target_concept_id=None,
                intended_target_name=None,intended_target_kind=None,relevance_completeness='not_annotated',
                permitted_scope_ids=[],reference_assertion_ids=[],reference_passage_ids=[],reference_source_ids=[],
                candidate_paths=[],reference_evidence=[],expected_behavior=behaviors[variant],
                forbidden_behavior=['invent_measurements','invent_oem_limits','invent_calibrated_probability']))
    jsonl(OUT/'initial_reports.jsonl',reports)
    jsonl(OUT/'retrieval_inputs.jsonl',inputs)
    jsonl(OUT/'retrieval_reference_labels.jsonl',labels)
    jsonl(OUT/'scenario_catalog.jsonl',catalog)
    for split in ['bootstrap_dev','bootstrap_check']:
        ids={r['report_id'] for r in labels if r['split']==split}
        jsonl(OUT/('inputs_'+split+'.jsonl'),[r for r in inputs if r['report_id'] in ids])
        jsonl(OUT/('labels_'+split+'.jsonl'),[r for r in labels if r['report_id'] in ids])
    dump(OUT/'initial_report.schema.json',schema())
    (OUT/'诊断报告模板.md').write_text(TEMPLATE,encoding='utf-8')
    (OUT/'初始诊断报告集_100份.md').write_text('\n\n---\n\n'.join(render_report(r) for r in reports),encoding='utf-8')
    (OUT/'样例报告_明确故障与症状配对.md').write_text(render_report(reports[0])+'\n\n---\n\n'+render_report(reports[1]),encoding='utf-8')
    index=['# 数据集索引','', '| 报告 | 子系统 | 类型 | 分组 | 分区 |', '| --- | --- | --- | --- | --- |']
    type_names=dict(explicit_fault='明确候选故障',symptom_only='仅描述症状',negated_normal='否定/正常',missing_fields='字段缺失',
                    competing_hypotheses='非唯一解释',unsupported_threshold='精确参数证据不足')
    for lab in labels:
        index.append('| [%s](初始诊断报告集_100份.md#船舶动力系统初始诊断报告%s) | %s | %s | %s | %s |' %
            (lab['report_id'],lab['report_id'].lower(),lab['system'],type_names[lab['sample_type']],lab['scenario_group_id'],lab['split']))
    (OUT/'数据集索引.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
    overlap=sorted({src for l in labels if l['split']=='bootstrap_dev' for src in l['reference_source_ids']} &
                   {src for l in labels if l['split']=='bootstrap_check' for src in l['reference_source_ids']})
    manifest=dict(dataset_version='diagnosis-bootstrap/1.0',created_date='2026-10-12',reports=len(reports),
        graph_version='5.0',graph_sqlite_sha256=before,
        counts_by_system=dict(collections.Counter(l['system'] for l in labels)),
        counts_by_type=dict(collections.Counter(l['sample_type'] for l in labels)),
        counts_by_split=dict(collections.Counter(l['split'] for l in labels)),
        base_scenarios=len(catalog),numeric_origin='deterministic_assistant_authored_synthetic_fixture',
        confidence_origin='synthetic_fixture_assigned_not_calibrated',expert_review_count=0,
        reference_label_status='silver_partial_not_independent_gold',
        split_policy='配对报告按基础场景分组；60开发/40检查；边界组和基础组独立编号。',
        source_overlap_ids=overlap,source_disjoint=False,
        evaluation_limit='检查分区仍共享知识来源且由同一规则合成，不能作为独立泛化、诊断准确率或完整Recall实验。',
        source_measurements_reproduced=False,real_signal_or_waveform_included=False,
        graph_sqlite_unchanged=before==hashlib.sha256(DB.read_bytes()).hexdigest())
    dump(OUT/'dataset_manifest.json',manifest)
    (OUT/'README.md').write_text(readme(manifest),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
    return validate()


def readme(m):
    return '''# 初始诊断报告模板与开发数据集 v1.0

日期：2026-10-12。承接“深度学习诊断结果＋中间层物理量→规范化初始报告→知识检索”。

## 交付与规模

100份完整初始报告，五个子系统各20份：燃油与进排气、润滑与轴承、冷却与海水、传动与推进、电力与控制。
40个基础场景分别提供明确候选故障、仅描述症状两种表达，共80份。另有否定/正常、字段缺失、非唯一解释、精确参数证据不足各5份。

| 文件 | 用法 |
| --- | --- |
| [诊断报告模板.md](诊断报告模板.md) | 与师兄确认固定格式及字段语义 |
| [接口对接说明.md](接口对接说明.md) | 四项上游成果到本接口的字段映射与后续增强接口 |
| [样例报告_明确故障与症状配对.md](样例报告_明确故障与症状配对.md) | 先查看一组完整输入报告 |
| [初始诊断报告集_100份.md](初始诊断报告集_100份.md) | 所有报告阅读版；包含初始证据链，不包含图谱答案 |
| [数据集索引.md](数据集索引.md) | 按系统、题型及分区定位 |
| initial_reports.jsonl | 100份结构化上游报告 |
| initial_report.schema.json | JSON Schema；接口候选版本，不是船级社标准 |
| retrieval_inputs.jsonl | 只含report_id和diagnosis_text；直接送入检索器 |
| retrieval_reference_labels.jsonl | 单独保存目标概念、声明/段落/来源、候选路径及行为要求 |
| scenario_catalog.jsonl | 40个基础场景的设计和依据 |
| inputs_bootstrap_dev.jsonl / labels_bootstrap_dev.jsonl | 60份开发分区 |
| inputs_bootstrap_check.jsonl / labels_bootstrap_check.jsonl | 40份检查分区 |
| dataset_manifest.json / validation_report.json | 版本指纹、统计与自动校验 |
| baseline_v5.jsonl / baseline_summary.json | 原V5检索器的初始基线；由单独命令生成 |
| [基线结果与检索启动建议.md](基线结果与检索启动建议.md) | 基线解读、漏召回样本及20份边界样本的复核清单 |

## 样本依据与限制

所有报告、船舶编号、模型ID、工况、数值及分数均为助手构造的合成数据，不是历史事故记录、实测信号或已训练模型输出。数值只为测试接口和同基线趋势，不提供厂家阈值。中间层预测与仿真观测用channel_role分开；未提供的模型、分布、标准差、型号和厂家阈值使用null。不能将人工分数称为师兄的随机性约束置信度方法。

基础场景检索目标存在于当前V5，参考证据直接来自指定scope的实际声明，保留原文、定位、确定性和适用范围。场景症状和数值为假设性构造，来源只支持一般知识声明，不支持该合成船舶的观测数值。候选路径严格同scope、同source_id且方向一致，但仍未经过专家语义审查。

标签是部分、待复核的银标，不是独立专家金标准，也不是唯一或完整相关答案。仅症状报告可对应多种故障，预设目标只是用于测试能否找回该场景的一个参考概念。边界样本只标行为要求，不伪造相关事实集合。

60/40按基础场景分组，配对报告不会跨分区。边界样本仍复用了基础场景设备/表述，两分区存在来源重叠，因此检查集用于初步回归而非独立泛化评测。检索库中保留知识文档是正常的；未来需要新的人工编写问题、真实上游输出以及按来源/场景隔离的优化和锁定评测。

本批不用于估计实船故障发生率、诊断准确率、物理阈值或概率校准效果；不包含原始时序波形。固定字段名称尚需师兄确认，术语尚需后续与船级社文档核对。

## 立即开展检索

从项目根目录运行。只读调用retrieve函数，避免命令行逐题覆盖retrieval_example.json：

```powershell
python tools/build_diagnosis_bootstrap.py --validate
python tools/run_diagnosis_bootstrap_baseline.py --split bootstrap_dev
python tools/run_diagnosis_bootstrap_baseline.py --split all
```

在Python中：

```python
import json
from ship_fault_kg.v5.retrieve import retrieve
with open("ship_fault_kg/diagnosis_bootstrap/v1/retrieval_inputs.jsonl", encoding="utf-8") as f:
    for line in f:
        sample = json.loads(line)
        evidence_pack = retrieve(sample["diagnosis_text"], k=3)
        # 用report_id关联输出；参考标签只在评测端读取。
```

优先比较明确故障与症状配对的目标出现率、事实数量、参考声明找回情况；后者只能称“部分参考集合覆盖”，不能称完整Recall。否定/缺失/非唯一解释/参数证据不足需要单独人工检查。检索返回排除故障的条件性参考本身不一定错误，应检查后续是否把它写成肯定诊断。

## 与师兄的接口替换

1. 初始报告固定保留诊断结果、依据物理量、诊断置信度、初步诊断溯源四个核心部分。
2. 他提供真实或仿真模型输出后，替换upstream_model、physical_quantities和diagnosis，保留缺失信息及否定。
3. 随机性约束方法落地后填入confidence.method/method_version/stochastic_constraint_result，保留校准状态，避免检索分数覆盖模型分数。
4. 你负责检索参考机理、检查/措施和出处；增强报告追加这些内容，并明确适用条件及未证实部分。
5. 如将数据用于生成模型训练，应另建真正独立的测试集，不继续把本批检查分区当最终评测。

## 可复现生成

```powershell
python tools/build_diagnosis_bootstrap.py
```

生成器只读V5 SQLite，输出到本目录；不更新图谱和Neo4j。重新生成会刷新本目录固定交付文件，人工标注修订请另存新版本。
''' + '\n本次知识图谱SQLite SHA256：`'+m['graph_sqlite_sha256']+'`。\n'


def validate():
    nodes, edges, claims, sources, passages = load_graph()
    manifest=json.loads((OUT/'dataset_manifest.json').read_text(encoding='utf-8'))
    def rows(name):
        return [json.loads(line) for line in (OUT/name).read_text(encoding='utf-8').splitlines() if line.strip()]
    reports=rows('initial_reports.jsonl'); inputs=rows('retrieval_inputs.jsonl'); labels=rows('retrieval_reference_labels.jsonl')
    errors=[]; checks=collections.Counter()
    def check(ok, message):
        checks['passed' if ok else 'failed']+=1
        if not ok: errors.append(message)
    check(len(reports)==len(inputs)==len(labels)==100,'Expected 100 aligned records')
    check(len({r['report_id'] for r in reports})==100,'Duplicate report ID')
    check([r['report_id'] for r in reports]==[r['report_id'] for r in inputs]==[r['report_id'] for r in labels],'ID order mismatch')
    check(dict(collections.Counter(r['equipment']['system'] for r in reports))=={s:20 for s in SYSTEMS},'System balance')
    check(collections.Counter(l['split'] for l in labels)=={'bootstrap_dev':60,'bootstrap_check':40},'Split balance')
    check(len({r['diagnosis_text'] for r in inputs})==100,'Duplicate retrieval input')
    groups=collections.defaultdict(list)
    for r,inp,lab in zip(reports,inputs,labels):
        rid=r['report_id'];groups[lab['scenario_group_id']].append((r,lab))
        check(r['data_status']=='synthetic_bootstrap' and not r['upstream_model']['trained_model'],rid+': misleading origin')
        conf=r['diagnosis']['confidence'];check(not conf['calibrated'] and not conf['probability_interpretation'],rid+': confidence calibration')
        check(conf['value'] is None or 0<=conf['value']<=1,rid+': confidence range')
        check(r['diagnosis']['confirmed_root_cause'] is None,rid+': root cause improperly confirmed')
        check(inp['diagnosis_text']==retrieval_input(r),rid+': retrieval text round-trip')
        check(not any(x in json.dumps(r,ensure_ascii=False)+inp['diagnosis_text'] for x in ['shipkg5:','assertion:','passage:','reference:knowledge:','article:src:','case:sd']),rid+': label ID leakage')
        if lab['sample_type']=='symptom_only':
            check(lab['intended_target_name'] not in inp['diagnosis_text'],rid+': target name leaked in symptom input')
        qids={p['quantity_id'] for p in r['physical_quantities']}
        check(len(qids)==len(r['physical_quantities']),rid+': duplicate physical IDs')
        for p in r['physical_quantities']:
            check(p['engineering_threshold'] is None and p['threshold_source'] is None,rid+': invented threshold')
            if p['value'] is None:
                check(p['validity']=='missing' and p['delta_from_baseline'] is None and p['trend']=='unknown',rid+': missing not preserved')
            else:
                check(math.isclose(p['delta_from_baseline'],p['value']-p['baseline_value'],abs_tol=0.00011),rid+': numeric delta')
                check(p['trend']==('stable' if p['value']==p['baseline_value'] else ('up' if p['value']>p['baseline_value'] else 'down')),rid+': trend mismatch')
        for chain in r['initial_evidence_chain']:
            check(set(chain['quantity_ids'])<=qids and not chain['verified_root_cause'],rid+': initial chain mismatch')
        for b in lab['reference_evidence']:
            c=claims[b['assertion_id']]
            check(b['scope_id'] in lab['permitted_scope_ids'],rid+': scope mismatch')
            check(b['quote']==c['quote'] and b['source_sha256']==sources[c['source_id']]['sha256'],rid+': altered quote/source')
            check(b['passage_id'] in passages,rid+': missing passage')
            p=passages[b['passage_id']]
            check(c['quote'] in p['text'],rid+': quote absent from referenced passage')
        for path in lab['candidate_paths']:
            facts=[claims[a] for a in path['assertion_ids']]
            check(len(path['node_ids'])==len(facts)+1 and 2<=len(facts)<=3,rid+': path length')
            check(len(set(path['node_ids']))==len(path['node_ids']),rid+': path cycle')
            check(all(c['scope_id']==path['scope_id'] and c['source_id']==path['source_id'] and c['relation'] in CAUSAL for c in facts),rid+': mixed path')
            check(all(c['subject']==path['node_ids'][i] and c['object']==path['node_ids'][i+1] for i,c in enumerate(facts)),rid+': path direction')
    for group,pair in groups.items():
        check(len({l['split'] for r,l in pair})==1,group+': cross-split pair')
        if group.startswith('SC-'):
            check(len(pair)==2,group+': missing pair')
            check(pair[0][0]['physical_quantities']==pair[1][0]['physical_quantities'],group+': inconsistent paired numbers')
    check(hashlib.sha256(DB.read_bytes()).hexdigest()==manifest['graph_sqlite_sha256'],'KG fingerprint changed')
    # Validate every keyword actually used by this schema with the bundled
    # standard library; additionally use the standards library if installed.
    current_schema=json.loads((OUT/'initial_report.schema.json').read_text(encoding='utf-8'))
    for r in reports:
        schema_errors=validate_schema_keywords(r,current_schema)
        check(not schema_errors,r['report_id']+': schema '+str(schema_errors))
    schema_validation='passed_current_schema_keywords_stdlib' if not errors else 'see_errors'
    try:
        import jsonschema
    except ImportError:
        pass
    else:
        validator=jsonschema.Draft202012Validator(current_schema,format_checker=jsonschema.FormatChecker())
        for r in reports:
            for error in validator.iter_errors(r): check(False,r['report_id']+': schema '+error.message)
        schema_validation='passed_draft202012_jsonschema_library' if not errors else 'see_errors'
    result=dict(passed=not errors,checks=dict(checks),errors=errors,json_schema_validation=schema_validation,
        report_count=len(reports),reference_evidence_links=sum(len(l['reference_evidence']) for l in labels),
        candidate_paths=sum(len(l['candidate_paths']) for l in labels),
        knowledge_graph_unchanged=hashlib.sha256(DB.read_bytes()).hexdigest()==manifest['graph_sqlite_sha256'],
        note='自动检查验证结构、数值、引用和分区一致性，不证明合成诊断合理性、实船有效性或完整标签正确性。')
    dump(OUT/'validation_report.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if errors:raise SystemExit(1)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--validate',action='store_true');args=parser.parse_args()
    validate() if args.validate else build()
