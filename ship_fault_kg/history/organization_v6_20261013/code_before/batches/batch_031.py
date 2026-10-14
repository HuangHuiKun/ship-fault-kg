"""Six representative excerpts across cooling, injection and shaft mechanics."""
from ship_fault_kg.v6_assistant.authoring import Batch
b=Batch();RECORDS=b.records
def source(sid,title,system,equipment,scope,case=False,notes=''):
 return b.excerpt(sid,title,system,equipment,scope,[],case,notes)
def quote(r,text):
 r['reviewed_excerpts'].append({'text':text});return text

r=source('src:105d77c5c31bb589726e2aee','空冷器换热管碎片堵塞与冲刷腐蚀片段',
 'cooling','主机海水空冷器','二手散货船换热管调查；文中临界流速由材质和原构型决定，不作为通用阈值。',True)
q=quote(r,'卡在换热管内的碎片导致换热管流通面积减少。')
b.fact(r,'F|空冷器换热管碎片堵塞','CAUSES','S|空冷器换热管有效流通面积减少',q)
q=quote(r,'铜管内径断面面积的40%被堵住的话，流速就会超过3.1米/秒，从而保护膜被破坏。')
b.chain(r,['S|空冷器换热管有效流通面积减少','S|换热管局部流速超过材料适用范围','S|换热铜管保护膜破坏'],q,'conditional')
q=quote(r,'本次腐蚀显然是由碎片封堵产生的过流速引起的。')
b.fact(r,'S|换热管局部流速超过材料适用范围','CAUSES','F|空冷器换热管冲刷腐蚀',q,'source_interpretation')
q=quote(r,'为排查碎片来源，仔细检查了从海底门到空冷器的整个管路系统。')
b.checks(r,[('空冷器堵塞后检查海底门至空冷器的异物来源','F|空冷器换热管碎片堵塞')],q)

r=source('src:13a4e8899bf055383eb3bbbd','副机冷却水偏低与恒温阀冲蚀片段',
 'cooling','副机高温水恒温阀','二手恒温阀案例；不据文中车削尺寸形成通用修复标准。',True)
q=quote(r,'高温水恒温阀阀面、阀座的腐蚀穿孔是导致副机高温冷却水出口温度偏低的根本原因。')
b.fact(r,'F|高温水恒温阀阀面阀座腐蚀穿孔','CAUSES','S|副机高温水出口温度偏低',q)
q=quote(r,'析出的气泡瞬间破灭，水以高速冲击阀面和阀座，造成此处的金属被冲蚀剥离。')
b.fact(r,'S|恒温阀节流后气泡破灭冲击','CONTRIBUTES_TO','F|高温水恒温阀金属冲蚀剥离',q,'source_interpretation')
q=quote(r,'使阀座和阀面处出现麻点、凹坑，甚至穿孔，引起冷却水的泄露，影响了阀的正常功能。')
b.fact(r,'F|高温水恒温阀阀面阀座腐蚀穿孔','CAUSES','F|高温水恒温阀内漏',q)
q=quote(r,'在确认冷却水泵和中央冷却器工作正常的情况下，就要检查高温水恒温阀了。')
b.checks(r,[('排除泵和中央冷却器异常后检查高温水恒温阀','S|副机高温水出口温度偏低')],q)

r=source('src:28175fb88c47f90a3968951a','电控主机PCV内漏与滑油污染片段',
 'fuel_air','电控主机燃油共轨压力控制阀PCV','二手PCV拆检案例；ICU与油泵密封失效属于排查分支，不代表均为该船事故原因。',True)
q=quote(r,'发现 PCV 的针阀密封面有缺口（如图 5），调压活塞密封圈老化（如图 6）等情况。')
b.checks(r,[('按原厂安全拆检流程检查PCV针阀密封面及活塞密封圈','E|电控主机燃油共轨压力控制阀PCV')],q)
q=quote(r,'如果密封圈 O 形圈（方框内）有缺陷密封不严时，燃油回油管又保持有一定的压力，此时燃油可能会通过该密封面进入到活塞底部的滑油泄放腔室，污染系统滑油。')
b.fact(r,'F|PCV密封圈失效','INCREASES_RISK_OF','S|燃油经PCV进入系统滑油',q,'conditional')
q=quote(r,'主机系统滑油闪点降偏低一般是因燃油泄漏进入到系统滑油中造成的')
b.fact(r,'S|燃油进入系统滑油','CONTRIBUTES_TO','S|主机滑油闪点降低',q)
q=quote(r,'当检漏口 1 堵塞时，如果阀芯（方框内）密封不良，有内漏时，高压燃油会通过阀芯进入到伺服油侧，导致伺服油被燃油污染。')
b.fact(r,'X|ICU检漏口堵塞且阀芯密封内漏','INCREASES_RISK_OF','S|ICU伺服滑油受燃油污染',q,'conditional')
q=quote(r,'如果高压油泵内漏严重，且高压油泵顶升机构密封不良，会导致漏泄的燃油通过顶升机构的密封面进入高压油泵下部的凸轮箱污染滑油。')
b.fact(r,'X|高压油泵严重内漏且顶升机构密封不良','INCREASES_RISK_OF','S|燃油经油泵进入凸轮箱滑油',q,'conditional')
q=quote(r,'换新 PCV 后，主机启动困难的故障得以解决。')
b.fact(r,'A|按PCV原厂维修规定更换故障阀并验证启动保压','ACTS_ON',
       'E|电控主机燃油共轨压力控制阀PCV',q,'guidance')

r=source('src:f2b8d7ec8fab20173dfd667e','RT-flex ICU喷射停滞补偿异常片段',
 'fuel_air','RT-flex ICU喷射控制单元','二手喷射曲线分析；选中片段不足以证明低硫燃油是根因，因此不增加低硫油直接致故障关系。',True)
q=quote(r,'ICU 内部磨损或卡滞导致“喷射停滞时间偏差”自动补偿过大而引起喷射始点提前，爆压降低。')
for f in ['ICU内部磨损','ICU内部卡滞']:
 b.fact(r,'F|'+f,'CONTRIBUTES_TO','S|喷射停滞时间偏差补偿过大',q,'possible')
b.fact(r,'S|喷射停滞时间偏差补偿过大','CAUSES','S|喷射始点异常提前',q,'source_interpretation')
b.fact(r,'S|喷射停滞时间偏差补偿过大','CONTRIBUTES_TO','S|气缸最高燃烧压力降低',q,'source_interpretation')
q=quote(r,'截取 Flex View 软件中燃油喷射曲线( 见图 1) ，可以看出该缸的喷射始点相比其他缸明显提前')
b.checks(r,[('用Flex View对比故障缸及其他缸的喷射曲线','E|RT-flex ICU喷射控制单元')],q)

r=source('src:e43f8ad67dcc31e809d883ec','碰撞反向扭矩导致曲轴红套滑移片段',
 'transmission','B&W6K45GF半组合曲轴','二手科考船碰撞案例；外力反扭矩引发红套滑移，不代表所有红套滑移都源于碰撞。',True)
q=quote(r,'货船球鼻艏顶到该船右螺旋桨，该船右轴系受到突加的巨大的反向扭矩导致右主机被强制逼停，从而导致右主机曲轴红套滑移。')
b.chain(r,['X|外船碰撞螺旋桨','S|轴系突受巨大反向扭矩','S|主机被强制逼停','F|曲轴红套滑移'],q,'case_identified')
q=quote(r,'曲轴生产厂家制造曲轴时在每个主轴颈和曲柄臂的红套结合面冲有圆形凹洞作为记号，方便用户检查红套是否滑移')
b.checks(r,[('按制造商规程核对红套结合面定位标记','F|曲轴红套滑移')],q)

r=source('src:1350267f104d0c7086f018ec','曲轴循环载荷与疲劳裂纹机理片段',
 'transmission','柴油机曲轴','二手机理分析；只采用循环应力与疲劳裂纹的明确描述。',
 notes='不采纳仅凭裂纹方向判定磨削后放行的维修建议。')
q=quote(r,'曲柄臂与轴颈过渡圆角处产生很大的应力。 当此应力超过曲轴的疲劳极限时，即会导致弯曲疲劳裂纹的出现。')
b.fact(r,'S|曲轴过渡圆角循环应力超过疲劳限','INCREASES_RISK_OF','F|曲轴弯曲疲劳裂纹',q,'conditional')
