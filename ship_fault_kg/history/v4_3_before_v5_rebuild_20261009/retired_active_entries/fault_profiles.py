"""V3 fault-centred reference units; each fact has an exact physical-PDF-page anchor.

Reference units are NOT invented accidents. Classification links are curated,
not causal assertions. Narrow applicability and uncertainty survive retrieval.
"""
SCUFF = 'MAN_SL2016_633_piston_rings_scuffing.pdf'
RINGS = 'MAN_SL2019_685_ring_coating_wear.pdf'
LUBE = 'MAN_SL2023_737_cylinder_lubrication.pdf'
BEARING = 'MAN_SL2013_569_bearing_wear_monitoring.pdf'
DAMPER = 'MAN_SL2017_654_torsional_damper.pdf'
WATER = 'MAN_SL2016_623_cooling_water.pdf'
EFF = 'MAN_main_engine_auxiliary_efficiency.pdf'
SHAFT = 'STAMFORD_AGN039_marine_shaft_generators.pdf'
CURRENT = 'STAMFORD_AGN033_bearing_currents.pdf'
INSULATION = 'STAMFORD_AGN040_winding_insulation.pdf'
TVA = 'STAMFORD_AGN235_torsional_analysis.pdf'
COUPLE = 'STAMFORD_AGN232_coupling_arrangements.pdf'
PROTECTION = 'STAMFORD_AGN035_fault_protection.pdf'
AVKBEAR = 'STAMFORD_AGN076_alternator_bearings.pdf'
OSC = 'Frontiers_2021_marine_converter_oscillations.pdf'
HEBRIDES = 'MAIB_2017_20_Hebrides_CPP_coupling.pdf'

def f(a, rel, b, source, page, anchor, certainty='guidance'):
    return a, rel, b, source, page, anchor, certainty

def p(key, name, main, subs, domains, scope, facts, aliases='', instances=()):
    return dict(id='knowledge:'+key, name=name, main_fault=main, subsystems=subs,
                domains=domains, applicability=scope, facts=facts, aliases=aliases,
                instances=list(instances))

PROFILES = [
    p('liner_scuffing', '拉缸', '缸套黏着拉伤', ['fuel_air','lubrication'], '热-机',
      'MAN B&W两冲程柴油机缸套/活塞环；2016通函用于机理，润滑油选择须查2023通函及本机手册。不能把活塞咬死一概等同于已证实拉缸。', [
        f('Condition|缸套表面抛光或涂抹|liner polishing smearing', 'CONTRIBUTED_TO', 'Condition|缸套油膜难以维持|compromised oil film', SCUFF,2,'making it difficult to keep a proper oil film'),
        f('Condition|缸套油膜难以维持', 'MAY_CONTRIBUTE_TO', 'Fault|缸套黏着拉伤|拉缸 liner scuffing', SCUFF,2,'high friction and seizures that will not recover (liner scuffing)'),
        f('Fault|缸套黏着拉伤', 'LEADS_TO', 'Condition|缸套表面硬化需修复|hardened liner surface', SCUFF,2,'surface of the liner is hardened'),
        f('Check|检查缸套表面与活塞环状态', 'CHECKS', 'Fault|缸套黏着拉伤', SCUFF,3,'Conditioning the liner surface','derived_action'),
        f('Action|按厂家程序及时降负荷并核查气缸润滑', 'ADDRESSES', 'Fault|缸套黏着拉伤', SCUFF,2,'increased lubrication and reduced load'),
        f('Action|按机型与燃料选择气缸油并检查缸况', 'ADDRESSES', 'Condition|缸套油膜难以维持', LUBE,1,'maintaining an adequate oil film'),
        f('Symptom|扫气泄放油铁含量升高', 'INDICATES', 'Fault|活塞环与缸套磨损', RINGS,2,'high iron content'),
      ], '拉缸 scuffing 缸套拉伤 黏着磨损'),
    p('bearing_seizure', '烧瓦与轴承咬死', '主轴承咬死', ['lubrication'], '热-机',
      '主机滑动轴承；烧瓦是检索用的工程统称，不能把全部轴瓦疲劳、瓦片转位或轴承失效直接标成已证实烧瓦。', [
        f('Cause|异物经滑油进入主轴承', 'LEADS_TO', 'Fault|主轴承咬死|烧瓦 抱轴 bearing seizure', BEARING,2,'sudden ingress of foreign matter'),
        f('Condition|未响应轴承磨损报警与减速请求', 'WORSENS', 'Fault|主轴承咬死', BEARING,2,'crew did not react to the alarm'),
        f('Fault|主轴承咬死', 'LEADS_TO', 'Consequence|曲轴与机座需大修', BEARING,2,'comprehensive repair of the crankshaft and bearing'),
        f('Check|核验轴承磨损监测快速磨损功能', 'CHECKS', 'Fault|主轴承咬死', BEARING,4,'Ability to detect rapidly developing bearing damage'),
        f('Action|响应轴承磨损报警并按安全程序降负荷', 'ADDRESSES', 'Condition|未响应轴承磨损报警与减速请求', BEARING,2,'automatic slow-down/load reduction'),
        f('Symptom|油雾探测器反复报警', 'ASSOCIATED_WITH', 'Fault|主轴承咬死', BEARING,2,'OMD system'),
      ], '烧瓦 抱轴 轴瓦过热 轴承咬死 bearing seizure'),
    p('coolant_blockage', '冷却水通道堵塞与热过载', '冷却水通道结垢堵塞', ['cooling','fuel_air'], '热-机',
      'MAN四冲程柴油机闭式淡水冷却；水质要求与添加剂须按具体机型手册确认。', [
        f('Cause|冷却水水质或处理不当', 'LEADS_TO', 'Fault|冷却水通道结垢堵塞', WATER,2,'deposits of limescale and/or rust'),
        f('Fault|冷却水通道结垢堵塞', 'LEADS_TO', 'Condition|换热能力降低', WATER,2,'reduce the heat transfer'),
        f('Condition|换热能力降低', 'MAY_CONTRIBUTE_TO', 'Fault|被冷却部件热过载', WATER,2,'may result in thermal overload'),
        f('Fault|被冷却部件热过载', 'MAY_CONTRIBUTE_TO', 'Fault|排气阀座开裂泄漏', WATER,2,'cracks and leakages'),
        f('Check|检测冷却水硬度和抑制剂浓度', 'CHECKS', 'Cause|冷却水水质或处理不当', WATER,3,'quality of the freshwater must be checked'),
        f('Action|按本机手册处理冷却水并定期送检', 'ADDRESSES', 'Cause|冷却水水质或处理不当', WATER,3,'send a coolant sample to an'),
      ], '冷却水堵塞 结垢 冷却不足 热过载'),
    p('cooling_cavitation', '冷却回路汽蚀', '冷却水管路汽蚀', ['cooling','fuel_air'], '热-机',
      '扫气空气冷却器水侧；该证据描述低流量局部沸腾及管路汽蚀，不等同于已证明所有冷却泵汽蚀由此引起。', [
        f('Condition|扫气空气冷却器水流量过低', 'MAY_CONTRIBUTE_TO', 'Condition|冷却器水侧局部沸腾', EFF,11,'A flow which is too low may cause local boiling'),
        f('Condition|冷却器水侧局部沸腾', 'MAY_CONTRIBUTE_TO', 'Fault|冷却水管路汽蚀', EFF,11,'may lead to cavitation in the cooling water pipes'),
        f('Condition|扫气空气冷却器水流量过低', 'LEADS_TO', 'Symptom|扫气空气温度升高', EFF,11,'Increased scavenge air temperature'),
        f('Symptom|扫气空气温度升高', 'CONTRIBUTED_TO', 'Fault|气缸磨损增加', EFF,11,'increase cylinder wear'),
        f('Check|检查扫气冷却器流量及水侧状态', 'CHECKS', 'Condition|扫气空气冷却器水流量过低', EFF,11,'maintains a constant cooling water flow','derived_action'),
        f('Action|维持厂家要求的扫气冷却器水流量', 'ADDRESSES', 'Condition|扫气空气冷却器水流量过低', EFF,11,'maintains a constant cooling water flow'),
      ], '汽蚀 空化 冷却水汽蚀 cavitation'),
    p('damper_failure', '扭振减振器失效', '曲轴扭振减振器失效', ['lubrication','transmission'], '热-机',
      'MAN L16/24、L21/31、L27/38等通函列明机型；不得推广其维护周期到其它机型。', [
        f('Condition|减振器滑油供给不足或含水污染', 'MAY_CONTRIBUTE_TO', 'Fault|曲轴扭振减振器失效', DAMPER,1,'will reduce the service life'),
        f('Condition|发动机超速或缸内液击', 'MAY_CONTRIBUTE_TO', 'Fault|曲轴扭振减振器失效', DAMPER,1,'over-speed'),
        f('Symptom|减振器异响或机组振动变化', 'INDICATES', 'Fault|曲轴扭振减振器失效', DAMPER,1,'abnormal noise'),
        f('Check|检查减振器异响与振动趋势', 'CHECKS', 'Fault|曲轴扭振减振器失效', DAMPER,1,'behavior of the complete GenSet','derived_action'),
        f('Action|确认减振器故障后按厂家程序更换', 'ADDRESSES', 'Fault|曲轴扭振减振器失效', DAMPER,1,'complete torsional vibration damper must be replaced'),
      ], '减振器失效 扭振减振器 torsional vibration damper'),
    p('shaft_generator_alignment', '轴带发电机对中异常与振动损伤', '轴带发电机振动损伤', ['transmission','electrical'], '热-机-电',
      '通过齿轮箱及联轴器驱动的轴带发电机；不能推广到所有同轴无附加轴承的构型。', [
        f('Condition|齿轮箱热膨胀改变轴线位置', 'ASSOCIATED_WITH', 'Condition|轴带发电机与齿轮箱对中失准', SHAFT,2,'thermal expansion of the hot gearbox'),
        f('Condition|风浪下船体变形', 'LEADS_TO', 'Condition|轴带发电机与齿轮箱对中失准', SHAFT,2,'ship’s hull flexes'),
        f('Condition|轴带发电机与齿轮箱对中失准', 'MAY_CONTRIBUTE_TO', 'Fault|轴带发电机振动损伤', SHAFT,2,'excessive vibration is likely to damage'),
        f('Check|核查热态对中和风浪工况下振动', 'CHECKS', 'Condition|轴带发电机与齿轮箱对中失准', SHAFT,2,'alignment is not accurate','derived_action'),
        f('Action|按构型复核联轴器补偿与减振能力', 'ADDRESSES', 'Condition|轴带发电机与齿轮箱对中失准', SHAFT,2,'absorb misalignment'),
      ], '轴带 对中不良 轴带电机振动 shaft generator alignment'),
    p('generator_bearing_wear', '发电机轴承机械磨损', '发电机滚动轴承磨损失效', ['lubrication','electrical','transmission'], '热-机-电',
      '有滚动轴承的发电机或轴带发电机构型；滚动轴承与主机滑动轴瓦的失效机理不得混用。', [
        f('Condition|轴承润滑脂不足或对中不良', 'MAY_CONTRIBUTE_TO', 'Fault|发电机滚动轴承磨损失效', AVKBEAR,4,'lack of grease or misalignment damage'),
        f('Condition|轴向振动引起轴承座微动', 'MAY_CONTRIBUTE_TO', 'Fault|发电机滚动轴承磨损失效', AVKBEAR,4,'axial vibration, causing a fretting action'),
        f('Check|按轴承型式核查润滑及对中', 'CHECKS', 'Fault|发电机滚动轴承磨损失效', AVKBEAR,4,'lack of grease or misalignment damage','derived_action'),
        f('Action|按机型维护计划补脂并复核联轴器重量', 'ADDRESSES', 'Condition|轴承润滑脂不足或对中不良', SHAFT,2,'bearing regreasing instructions'),
      ], '轴带电机磨损 发电机轴承磨损 滚动轴承 bearing wear'),
    p('bearing_electrical_erosion', '电机与发电机轴承电蚀', '轴承电蚀', ['electrical','lubrication'], '电-机',
      '具有闭合轴电流路径的旋转电机；轴承绝缘和接地刷方案按厂家/机型确定，不能假定全部STAMFORD机型都需要绝缘轴承。', [
        f('Condition|电机磁场不对称产生轴电压', 'MAY_CONTRIBUTE_TO', 'Condition|轴电流通过滚动轴承', CURRENT,1,'voltage (electrical pressure) generated'),
        f('Condition|轴电流通过滚动轴承', 'LEADS_TO', 'Fault|轴承电蚀', CURRENT,1,'electrical erosion of the bearing materials'),
        f('Check|核查轴电压电流与轴承接地绝缘方案', 'CHECKS', 'Fault|轴承电蚀', CURRENT,3,'shaft voltage measurement','derived_action'),
        f('Action|按适用机型维护接地刷与绝缘轴承', 'ADDRESSES', 'Condition|轴电流通过滚动轴承', CURRENT,3,'rotor earthing brush and insulated bearings'),
      ], '电蚀 轴承电流 轴电流 shaft bearing currents'),
    p('winding_insulation', '发电机绕组绝缘劣化', '发电机绕组绝缘电阻降低', ['electrical','cooling'], '热-电',
      'STAMFORD/AvK发电机；检测与干燥作业须停电隔离，由合格人员依本机手册执行，本文不提供通用阈值或操作命令。', [
        f('Condition|绕组表面潮湿或污染', 'LEADS_TO', 'Fault|发电机绕组绝缘电阻降低', INSULATION,6,'Surface moisture'),
        f('Condition|故障电流切除超出热损伤时间范围', 'LEADS_TO', 'Fault|发电机绝缘热劣化', PROTECTION,2,'thermal degradation'),
        f('Check|隔离后由合格人员检测绝缘电阻与极化指数', 'CHECKS', 'Fault|发电机绕组绝缘电阻降低', INSULATION,6,'Polarization Index'),
        f('Action|按本机手册处理潮湿污染并验证绝缘', 'ADDRESSES', 'Condition|绕组表面潮湿或污染', INSULATION,6,'drying out procedures'),
      ], '绝缘下降 绕组绝缘 绝缘电阻 insulation resistance'),
    p('coupling_failure', '联轴器故障', 'CPP执行器联轴器松脱', ['transmission','electrical'], '机-电',
      '实际证据是Hebrides的CPP执行器小型爪式联轴器，不是主推进轴联轴器断裂；主轴断裂根因不可由此推断。', [
        f('Cause|联轴器紧定螺钉缺少锁固措施', 'LEADS_TO', 'Fault|CPP执行器联轴器松脱', HEBRIDES,35,'absence of thread locking fluid','reported'),
        f('Fault|CPP执行器联轴器松脱', 'LEADS_TO', 'Fault|CPP执行器运动传递失效', HEBRIDES,30,'coupling remained stationary','reported'),
        f('Fault|CPP执行器运动传递失效', 'LEADS_TO', 'Fault|驾驶台丧失左舷螺距控制', HEBRIDES,30,'control of the ferry’s port CPP was lost','reported'),
        f('Check|按OEM要求检查执行器联轴器紧固完整性', 'CHECKS', 'Fault|CPP执行器联轴器松脱', HEBRIDES,36,'inspection and integrity of the jaw coupling','reported_action'),
        f('Action|按OEM服务程序维护CPP执行器', 'ADDRESSES', 'Cause|联轴器紧定螺钉缺少锁固措施', HEBRIDES,36,'service procedure for the linear servomotor','reported_action'),
      ], '联轴器故障 联轴器松脱 coupling failure'),
    p('shaft_torsional', '轴系扭振与联轴器过载风险', '轴系扭转共振风险', ['transmission','electrical','fuel_air'], '热-机-电',
      '内燃机-发电机传动链一般机理；证据支持扭振导致失效风险及电气故障转矩冲击，但未建立某大型船主轴联轴器断裂的已证实事故链。', [
        f('Condition|气缸燃烧压力产生脉动转矩', 'MAY_CONTRIBUTE_TO', 'Fault|轴系扭转共振风险', TVA,1,'pulses can excite very significant resonant responses'),
        f('Fault|轴系扭转共振风险', 'INCREASES_RISK_OF', 'Fault|轴系或联轴器疲劳磨损损伤', TVA,2,'prevent fatigue or wear damage'),
        f('Fault|发电机短路或非同期并机', 'LEADS_TO', 'Condition|联轴器瞬态转矩冲击', PROTECTION,5,'transient peak torque demand'),
        f('Check|结合缸压与惯量刚度进行扭振分析并试验验证', 'CHECKS', 'Fault|轴系扭转共振风险', TVA,7,'require validation by test'),
        f('Action|复核联轴器正常与失火工况转矩和热负荷裕量', 'ADDRESSES', 'Fault|轴系扭转共振风险', TVA,7,'engine normal and misfire scenarios'),
      ], '扭振 共振 联轴器断裂风险 torsional resonance'),
    p('electrical_oscillation', '船舶电网耦合振荡', '船舶电网电压频率振荡', ['electrical','transmission'], '机-电',
      '2021论文三类船舶的实测电网信号，含轴带发电化学品船；不是所有振荡都超限。DP船风浪影响主要作用于基波与频率，不能一概说风浪显著放大所有谐波。', [
        f('Condition|原动机转矩脉动与负载波动', 'MAY_CONTRIBUTE_TO', 'Fault|船舶电网电压频率振荡', OSC,2,'pulsating torque'),
        f('Condition|轴带变流器控制与发电端变频条件', 'ASSOCIATED_WITH', 'Fault|船舶电网电压频率振荡', OSC,6,'associated with power converter control','research_observation'),
        f('Condition|DP船风浪纵摇横摇', 'CONTRIBUTED_TO', 'Fault|船舶电网电压频率振荡', OSC,6,'depth of voltage and frequency modulations increase','research_observation'),
        f('Fault|船舶电网电压频率振荡', 'MAY_CONTRIBUTE_TO', 'Consequence|电机轴振动与绝缘热应力增加', OSC,1,'add thermal stress to insulation'),
        f('Check|分析瞬时频率基波及谐波的调制特征', 'CHECKS', 'Fault|船舶电网电压频率振荡', OSC,1,'zoom-','derived_action'),
        f('Check|联合核查调速器AVR与变流器控制变量', 'CHECKS', 'Fault|船舶电网电压频率振荡', OSC,13,'governors, and AVRs settings','derived_action'),
        f('Check|用电压相轨迹辅助识别振荡且保留局限', 'CHECKS', 'Fault|船舶电网电压频率振荡', OSC,12,'phase portraits can be used','derived_action'),
      ], '电网耦合振荡 轴带发电振荡 电压振荡 频率振荡 marine microgrid oscillation'),
]

# Exactly 15 original dataset channels, not fabricated electrical measurements.
IMPORTANT_SENSORS = {
    'Engine Speed':'发动机转速', 'Max. In-Cylinder Press. No.1':'1缸最高缸压',
    'Charge Air Press.':'增压空气压力', 'Fuel Flow':'燃油流量',
    'No.1 Exh.Gas Temp.':'1缸排气温度',
    'Cooling Water Temp. Engine In':'主机冷却水进口温度',
    'Cooling Water Temp. Engine Out I':'主机冷却水出口温度Ⅰ',
    'LO Temp. Engine In':'主机滑油进口温度',
    'LO Temp. Engine Out':'主机滑油出口温度',
    'LO Circulating Pump Press.':'滑油循环泵压力原始电压信号',
    'Fresh Cooling Water Press.':'淡水冷却压力原始电压信号',
    'Engine Cooling water flow':'主机冷却水流量',
    'Charge Air IC Air Temp. Out':'增压空气冷却器出口空气温度',
    'Shaft Torque':'轴转矩', 'Shaft Power':'轴功率',
}
