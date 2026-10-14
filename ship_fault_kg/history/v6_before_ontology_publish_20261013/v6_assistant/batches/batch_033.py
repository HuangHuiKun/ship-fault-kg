"""Representative evidence for six cross-system diagnostic cases.

Explicit assistant-authored claims; no local model or template causal inference.
Only the literal evidence selected below is declared reviewed for this batch.
"""
from ship_fault_kg.v6_assistant.authoring import Batch
b=Batch();RECORDS=b.records

def source(sid,title,system,equipment,scope,case=False):
 return b.excerpt(sid,title,system,equipment,scope,[],case)
def quote(r,text):
 r['reviewed_excerpts'].append({'text':text});return text

r=source('src:06f41b4fbd64754c70c3db7b','并联发电机负荷转移与UG-8调速器油质片段',
 'electrical','UG-8液压调速器','齿条卡涩为理论排查分支，原案例检查未发现异常；油质脏污为实际发现。',False)
q=quote(r,'如果调节杆卡紧, 动作迟缓, 反应慢, 不灵敏, 则会造成加减油量不及时, 导致负载分配不均。')
b.chain(r,['F|发电柴油机燃油调节杆卡涩','S|发电柴油机加减油量不及时','S|并联发电机有功负荷分配不均'],q,'possible',group='rack_hypothesis')
q=quote(r,'长期不换油必然造成滑油脏污变质, 滑油性能下降, 调节失灵。')
b.chain(r,['X|液压调速器滑油长期未更换','S|液压调速器滑油脏污变质','F|液压调速器调节失灵'],q,'secondary_stated',group='governor_oil')
q=quote(r,'因此必须更换滑油。')
b.actions(r,[('按调速器维护规程更换脏污滑油','S|液压调速器滑油脏污变质')],q,group='governor_oil')

r=source('src:0cf21f74963bc9a1a013539c','主机海水离心泵吸空与排气改造案例片段',
 'cooling','主机海水冷却离心泵','全回转拖轮案例；一般滤网故障与本船排气问题分组，气体来源为作者分析，排气改造需设计审批，不能直接套用管径。',False)
q=quote(r,'对于入口处的滤网或过滤器堵塞，这个原因是经常可以引起离心泵的吸空的，我们在实际工作中也经常碰到。')
b.fact(r,'F|海水泵入口滤网堵塞','CONTRIBUTES_TO','F|海水离心泵吸空',q,'possible',group='filter_branch')
q=quote(r,'只要及时地清洗了滤网或过滤器后，就可以解决离心泵的吸空。')
b.actions(r,[('清洁确认堵塞的海水泵入口滤网','F|海水泵入口滤网堵塞')],q,group='filter_branch')
q=quote(r,'因为空气量大，此透气管不能完全排出空气，致使离心泵还是吸到了空气，使离心泵工况恶化，导致吸空。')
b.chain(r,['S|海底阀箱气体未充分排出','S|海水离心泵吸入气体','F|海水离心泵吸空'],q,'source_interpretation',group='vent_case')
q=quote(r,'停离心泵电源后，打开泵壳上的放水卡口，无水流出，只有大量的水汽出来。')
b.checks(r,[('停泵隔离后按规程检查泵壳气体与充水情况','F|海水离心泵吸空')],q,group='vent_case')
q=quote(r,'海水压力检测的压力继电器工作并不可靠，会出现不检测信号或者继电器不动作。')
b.fact(r,'F|海水压力继电器检测失效','CAUSES','S|海水冷却失压未被可靠检出',q,'case_observed',group='alarm')
q=quote(r,'最终选择海底门滤器的盖板上加一根 φ60 的透气管，因为海底门滤器的盖板在系统中的相对高度比较合适，适宜空气排出，而且位置也正好')
b.actions(r,[('经设计审核改善海底滤器排气通路','S|海底阀箱气体未充分排出')],q,group='vent_case')

r=source('src:20bc61fab78910fda5b1d7e6','MG-800调速器ADU故障与复电浪涌推测片段',
 'electrical','MG-800调速器ADU执行器驱动单元','ADU替换验证了故障位置；浪涌为事后推断，没有记录到浪涌测量，不作为证实事故起因。',True)
q=quote(r,'给出 UP 或DOWN 的调节信号，驱动器无输出，伺服马达不动作。')
b.fact(r,'F|电子调速器ADU执行器驱动失效','HAS_MANIFESTATION','S|调速驱动器有指令但无输出',q,'case_observed')
b.fact(r,'F|电子调速器ADU执行器驱动失效','HAS_MANIFESTATION','S|调速伺服马达不动作',q,'case_observed')
q=quote(r,'主机不发火，（集控室油门指示刻度为 0）， 起动失败， 主机调速器故障报警')
b.fact(r,'F|电子调速器ADU执行器驱动失效','HAS_MANIFESTATION','S|遥控启动油门为零且主机不发火',q,'case_observed')
q=quote(r,'机旁操纵（电子调速器不参与），油门手柄活络无卡阻，正、倒车的启动、发火、运转均正常。')
b.checks(r,[('在安全条件下对比遥控和机旁启动表现定位调速器故障','F|电子调速器ADU执行器驱动失效')],q)
q=quote(r,'才意识到全船跳电后回复供电时产生的涌浪电压冲击是故障原因。')
b.fact(r,'S|恢复供电时电压浪涌','CONTRIBUTES_TO','F|电子调速器ADU执行器驱动失效',q,'source_hypothesis_unmeasured')
q=quote(r,'供应商派专业人员到船更换、调试，调速系统恢复正常，证实判断正确。')
b.actions(r,[('由专业人员更换调试失效ADU单元','F|电子调速器ADU执行器驱动失效')],q)
q=quote(r,'电子元器件配备的高压保护装置，定期检查、测试，保持有效。')
b.checks(r,[('定期检查测试控制电子设备电源保护装置','E|MG-800调速器ADU执行器驱动单元')],q)

r=source('src:d32b84c2c16c4622bd8c94cf','备用副机回窜燃气影响并联供电及启动阀卡涩片段',
 'fuel_air','BW6T23LH副机喷油与启动装置','两次不同故障分组保存；不把已排除的争油或管路摩擦假设列为实际事故原因。',False)
q=quote(r,'针阀偶件密封面有机械杂质，喷嘴针阀卡死在开启位置。')
b.fact(r,'X|喷油器针阀密封面机械杂质','CONTRIBUTES_TO','F|喷油器针阀卡在开启位置',q,'case_identified',group='fuel_backflow')
q=quote(r,'出油止回阀弹簧断裂，出油阀失去了止回作用，缸内气体冲入燃油管系。')
b.chain(r,['F|高压油泵出油止回阀弹簧断裂','S|高压油泵出油阀止回功能丧失','S|气缸气体反冲进入燃油管系'],q,'case_identified',group='fuel_backflow')
q=quote(r,'3# 缸内的压缩空气经油头和高压油泵反冲到燃油管，再进入到三台副机燃油总管。')
b.fact(r,'S|气缸气体反冲进入燃油管系','CAUSES','S|多台副机共用燃油总管混入气体',q,'case_identified',group='fuel_backflow')
q=quote(r,'空气先进入到 No.2 副机燃油系统，导致 No.2 副机停车。')
b.fact(r,'S|多台副机共用燃油总管混入气体','CAUSES','F|供电副机因燃油进气停车',q,'case_identified',group='fuel_backflow')
q=quote(r,'更换 3# 缸油头和高压油泵出油止回阀弹簧，试启动，运转副机负荷不再波动，故障消除。')
b.actions(r,[('更换卡涩喷油器并复核泵压性能','F|喷油器针阀卡在开启位置'),('更换断裂出油止回阀弹簧并复验','F|高压油泵出油止回阀弹簧断裂')],q,group='fuel_backflow')
q=quote(r,'小油箱排空、清洁，加油口增设滤网，换用洁净的轻柴油。')
b.fact(r,'A|清洁喷油器试验装置油箱并过滤试验燃油','ACTS_ON','E|喷油器泵压试验装置',q,'guidance',group='fuel_backflow')
q=quote(r,'启动阀能开启却关闭不到位即卡在开启位置， 任何时候启动空气总会进入 1# 缸，增加活塞上行的阻力，致使副机启动时转速忽快忽慢，旋转乏力。')
b.chain(r,['F|副机启动阀卡在开启位置','S|启动空气持续进入气缸','S|活塞上行阻力增加','S|副机启动转速忽快忽慢且旋转乏力'],q,'case_identified',group='starting_valve')
q=quote(r,'更换 No.3 副机 1# 缸缸头启动阀，启动成功。')
b.actions(r,[('更换失效启动阀并验证启闭功能','F|副机启动阀卡在开启位置')],q,group='starting_valve')

r=source('src:de81b1f7081da8603055e0c4','VIT电气转换故障至主机后燃因果链片段',
 'fuel_air','主机VIT电气转换器','MAN6S80MC-C特定案例，压力电流关系以该机出厂数据为准；不推广固定压力临时改装。',True)
q=quote(r,'VIT的 I /P 转换器出现故障，不能将主机控制系统输出的电流信号转变成相应压力的至 VIT 执行机构的压缩空气信号。')
b.fact(r,'F|VIT电气转换器失效','CAUSES','S|VIT执行机构控制气压不足',q,'case_identified')
q=quote(r,'VIT 的执行机构未起到应有的作用，导致主机后燃严重，扫气温度、排烟温度都相应升高。')
b.chain(r,['S|VIT执行机构控制气压不足','S|可变喷油定时执行不到位','F|主机后燃严重'],q,'case_interpretation')
b.fact(r,'F|主机后燃严重','HAS_MANIFESTATION','S|扫气温度和排烟温度同时升高',q,'case_observed')
q=quote(r,'用专用表检测输出电流信号为 8.0mA 左右，说明只能是 VIT的 I /P 转换器出现故障')
b.checks(r,[('对照出厂对应关系测量VIT输入电流与输出气压','F|VIT电气转换器失效')],q)
q=quote(r,'公司安排专业工程师上船更换 I /P 转换器，同时进行相应的调整检测，整个 I /P 转换器故障彻底消除。')
b.actions(r,[('由专业工程师更换VIT转换器并标定验证','F|VIT电气转换器失效')],q)
q=quote(r,'在分析展开示功图时，能准确找到排烟温度及扫气温度同时都升高的故障是主机后燃造成的')
b.checks(r,[('对比相同工况示功图识别主机后燃','F|主机后燃严重')],q)

r=source('src:e0aa55241673ea41df499e67','SRP2500A接排失败与供油连杆匹配片段',
 'transmission','SRP2500A舵桨气胎离合器与调速机构','机型特定案例；接排转速窗口不作为全部船型通用阈值。',True)
q=quote(r,'右主机因为调速器供油连杆部分匹配问题导致调速过程无法正常执行，接排失败。')
b.chain(r,['F|主机调速器供油连杆匹配不当','S|主机调速过程无法正常执行','F|舵桨离合器接排失败'],q,'case_identified')
q=quote(r,'主机转速过低时，在接排瞬间主机输出转矩小于接排启动的最小转矩，会导致接排失败甚至主机被“憋停”')
b.chain(r,['S|主机接排转速过低','S|接排输出转矩不足','F|舵桨离合器接排失败'],q,'conditional')
b.fact(r,'S|接排输出转矩不足','CONTRIBUTES_TO','F|主机接排时憋停',q,'possible')
q=quote(r,'主机转速过高时，在接排时会加速摩擦片和轴系的损耗。')
b.fact(r,'X|离合器接排转速超过设计适用范围','INCREASES_RISK_OF','F|离合器摩擦片与轴系异常磨损',q,'possible')
q=quote(r,'如果对应主控转速信号的气压正常，则故障为柴油机调速器方向; 如果此时输出的气压异常，则可由电空转换阀逆推，通过测量进一步判断故障点。')
b.checks(r,[('核对电空转换阀输入电流与输出气压分段定位接排故障','F|舵桨离合器接排失败')],q)
q=quote(r,'调整调速器油门连杆伸缩长度和匹配角度，使控制手柄最大位置时主机转速达到额定值750r/min，故障排除。')
b.actions(r,[('按机型规程重新匹配调速器供油连杆并标定','F|主机调速器供油连杆匹配不当')],q)
q=quote(r,'控制手柄主控指令轻易不可改动，一经改动需将后续信号重新进行系统标定。')
b.fact(r,'A|控制指令变更后重新标定下游信号链','ACTS_ON','E|SRP2500A舵桨气胎离合器与调速机构',q,'guidance')
