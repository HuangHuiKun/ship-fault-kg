"""Four full maintenance texts, preserving installation and sensor failure boundaries."""
from ship_fault_kg.v6_assistant.authoring import Batch
b=Batch();RECORDS=b.records
article=b.article;fact=b.fact;chain=b.chain;checks=b.checks;actions=b.actions

r=article('src:c73e0f9dfff562b72ce90be7','主机起动后运行参数监测参考','cooling','船舶主柴油机',
    '二手运行介绍；46℃和118℃为图片示例非通用设定，不采纳延迟启动海水泵为统一操作。')
q='主机燃油温度，主机燃油压力，包括燃油供应泵压力及燃油循环泵压力等。'
for p in ['主机燃油进机温度','主机燃油供应泵压力','主机燃油循环泵压力']:
    fact(r,'P|'+p,'CHARACTERIZES','E|船舶主柴油机',q)
checks(r,[('起动后按本机要求核对燃油温度和泵压力','E|船舶主柴油机')],q)
q='如果温度（粘度）不符合要求，对温度（粘度）进行调节'
fact(r,'A|按燃油品级和本机要求调整燃油温度黏度','ACTS_ON','E|船舶主柴油机',q,'guidance')
q='如果主机滑油进口温度太高，说明旁通量太大'
fact(r,'S|滑油冷却器旁通量过大','CONTRIBUTES_TO','S|主机滑油进口温度过高',q,'possible')
q='调节之后我们要注意滑油温度是否降低。'
checks(r,[('滑油温控调整后确认实际温度响应','S|主机滑油进口温度过高')],q)
q='要经常检查主机的扫气压力。'
checks(r,[('按巡检计划监测主机扫气压力','E|船舶主柴油机')],q)
q='通过调节进空冷器冷却海水量，来对主机的扫气温度进行调节。'
fact(r,'A|按机型批准工况调节空冷器冷却水量','ACTS_ON','E|船舶主柴油机',q,'guidance')
checks(r,[('主机起动后按要求核对扫气温度','E|船舶主柴油机')],q)

r=article('src:7d4ff7333fc58647511bf488','CAT3516C EUI结构维护与通信误报警参考','electrical','CAT3516C电控单体喷油装置',
    '二手技术文章，681轮设备介绍与正文618轮通信故障不能当同船事故；原ET日志未核验。',
    notes='不采纳柴油机高压点火等不准确措辞；电磁阀电压喷射压力不作跨机型阈值。')
q='整个系统由外置浮子油箱、燃油初级滤器，机带输送泵、进油管、燃油精细滤器、凸轮轴、机械传动机构、电控喷油器、回油减压阀、回油冷却器和回油管组成。'
for comp in ['外置浮子燃油箱','燃油初级滤器','机带燃油输送泵','燃油精细滤器','凸轮轴','电控单体喷油器','燃油回油减压阀','燃油回油冷却器']:
    fact(r,'E|CAT3516C电控单体喷油装置','HAS_COMPONENT','B|'+comp,q,group='architecture')
q='如果喷油器更换，或换装到其他缸上，或两个喷油器调换，喷油器代码必须重新编制。'
fact(r,'A|按CAT ET程序在更换换位后编制对应喷油器代码','ACTS_ON','E|CAT3516C电控单体喷油装置',q,'guidance','coding')
q='否则可能导致不同汽缸间的正时和喷油量差别。'
fact(r,'X|EUI更换换位后未更新对应校准代码','INCREASES_RISK_OF','S|各缸喷油正时油量差异',q,'possible','coding')
q='电子控制系统模块对高温、高湿度十分敏感。'
fact(r,'X|电子控制模块高温高湿环境','INCREASES_RISK_OF','F|柴油机电子控制模块异常',q,'possible','maintenance')
q='严禁在发动机高速运转时将蓄电池或24V控制电源从电路中断开'
fact(r,'A|按CAT要求避免运行中断开控制电源','ACTS_ON','E|CAT3516C电控单体喷油装置',q,'guidance','maintenance')
q='当发动机出现故障时，不能将蓄电池或24V电源从电路中断开，防止ECM中故障代码及有关资料信息被删除。'
fact(r,'X|故障记录保存前不当断开ECM控制电源','INCREASES_RISK_OF','S|ECM故障信息丢失',q,'possible','maintenance')
fact(r,'A|先按ET流程保存故障信息再进行批准隔离','ACTS_ON','E|CAT3516C电控单体喷油装置',q,'guidance','maintenance')
q='应用高阻抗数字式万用表测试'
checks(r,[('按CAT电子检修程序使用高阻抗数字表测量','E|CAT3516C电控单体喷油装置')],q,group='maintenance')
q='ECM 防止受潮，不要敲击到ECM'
fact(r,'A|维护CAT ECM防潮并避免冲击','ACTS_ON','E|CAT3516C电控单体喷油装置',q,'guidance','maintenance')
q='保持燃油清净， 按要求更换燃油滤器，注意油柜的放残'
fact(r,'A|按CAT维护计划更换燃油滤器并油柜放残','ACTS_ON','E|CAT3516C电控单体喷油装置',q,'guidance','maintenance')
q='注意电路的连接，以防止电路连接处松动或者破损。'
checks(r,[('按CAT维护计划检查电控线束接头紧固破损','E|CAT3516C电控单体喷油装置')],q,group='maintenance')
q='查询当前和历史的故障代码;显示ECM参数配置;系统故障的诊断测试;效验各传感器。'
for c in ['用CAT ET读取当前历史故障码','用CAT ET核对ECM配置','按CAT ET批准流程校验传感器']:
    checks(r,[(c,'E|CAT3516C电控单体喷油装置')],q,group='maintenance')
q='当柴油机出现故障时候，应首先判断并检查可能引起故障的机械因素。'
checks(r,[('电控报警时先结合运行表现排查机械因素','E|CAT3516C电控单体喷油装置')],q,group='maintenance')
q='5号缸断开报警,不能并网运行'
fact(r,'S|电控报告气缸断开报警','ASSOCIATED_WITH','S|发电机组不能并网',q,group='communication')
q='判断为监测线路故障，后经排查发现通信线路接头松动，紧固后正常。'
fact(r,'F|柴油机监测通信接头松动','CONTRIBUTES_TO','S|电控报告气缸断开报警',q,'probable','communication')
actions(r,[('按检修规程恢复监测通信接头紧固并复测','F|柴油机监测通信接头松动')],q,group='communication')
q='各缸喷油器电磁线圈电压正常，1、2、5、9号喷油器均可正常喷油，控制线路正常'
checks(r,[('气缸断开报警时用ET核验喷油器电磁线圈与实际喷油','S|电控报告气缸断开报警')],q,group='communication')

r=article('src:8f82814aafda97989d35b890','康明斯航标海巡应用维护问题参考','lubrication','康明斯海巡船柴油机',
    '二手应用总结；仅定性维护原则，机型保修磨合小时温度力矩不能通用化。',
    notes='正文618与681不涉本来源；旧燃油倒入新滤器文字自相矛盾，采用随后明确污染风险；绝不把滑油倒进增压器进气管作为建议。')
q='如果增压器在柴油机启动后立即开始高速运转，机油压力不会及时增加给增压器供油'
fact(r,'X|起动后供油未建立立即高速运行','CONTRIBUTES_TO','S|增压器轴承供油不足',q,'conditional',group='startup')
q='转子由于惯性仍在高速旋转，转子轴和轴承是半干的。 摩擦惯性运动状态导致轴承和密封圈过早磨损。'
chain(r,['S|熄火后增压器惯性旋转缺润滑','F|增压器轴承密封圈早期磨损'],q,'conditional','shutdown')
q='熄火后，冷却水不再循环，被加热部件的热量不能被冷却水带走，温度还会继续升高，造成局部过热'
chain(r,['S|停机后余热未被冷却回路带走','S|增压器停机后局部热浸过热'],q,'conditional','shutdown')
q='长时间怠速运转由于柴油机机油压力低，润滑不完全，导致运动副磨损加剧。'
chain(r,['X|不适宜长时间低怠速工况','S|怠速机油压力低润滑不足','F|柴油机运动副磨损加剧'],q,'conditional','idle')
q='柴油机燃烧温度过低，燃烧不完全，可能引起积炭堵塞喷油器喷孔、活塞环或使气门卡住。'
for f in ['F|喷油器喷孔积炭堵塞','F|活塞环积炭卡滞','F|气门积炭卡住']:
    fact(r,'S|低温不完全燃烧积炭','INCREASES_RISK_OF',f,q,'possible','idle')
q='未燃烧的柴油将会冲刷气缸壁上的油膜，稀释机油'
chain(r,['S|低冷却液温度下未燃柴油冲刷缸壁油膜','S|柴油混入机油稀释'],q,'conditional','idle')
q='注入新燃油滤清器的清洁腔后，会增加喷油泵和喷油器的磨损。'
fact(r,'X|旧燃油滤器残油倒入新滤器清洁腔','INCREASES_RISK_OF','F|喷油泵喷油器磨损加剧',q,'possible','filter')
q='不要漏装燃滤螺纹座密封圈。'
fact(r,'A|更换燃油滤芯核对螺纹座密封圈正确装配','ACTS_ON','E|康明斯海巡船柴油机',q,'guidance','filter')
q='起动后不拧紧会漏油'
fact(r,'X|油水分离器放水阀放残后未关紧','CAUSES','F|燃油油水分离器放残阀漏油',q,'conditional','filter')
q='应使用厂家确认、指定的“三滤”并且确保无受潮、无灰尘、无磕碰。 船上备用滤器最好集中密封保存。'
fact(r,'A|选用厂家确认滤器并密封防潮防尘储存','ACTS_ON','E|康明斯海巡船柴油机',q,'guidance','filter')
q='对于 C、D级的保养，则必须由经康明斯船用柴油机培训机构培训合格的专业人员来完成'
fact(r,'A|按机型维护级别由合格人员执行深度检修','ACTS_ON','E|康明斯海巡船柴油机',q,'guidance','maintenance')
q='应仔细阅读使用说明书，严格按说明书使用和操作，尤其是保证做好新车的磨合。'
fact(r,'A|依具体使用手册执行新机磨合与运行管理','ACTS_ON','E|康明斯海巡船柴油机',q,'guidance','maintenance')

r=article('src:ea2ee0b11eccfdbd0a5186cf','双主机机外滑油串油清洗工艺参考','lubrication','主机机外滑油管路装置',
    '二手特定在建船工艺；ISO等级与NAS等效说法未经标准核验，阀号温度频次只属于原船方案。')
q='系统中若存在污物杂质，会加快机件磨损，增大功率损耗，增加故障概率'
fact(r,'S|主机滑油回路残留颗粒杂质','CONTRIBUTES_TO','F|主机润滑机件加速磨损',q)
q='焊渣、粉尘、铁锈等杂质，难免进入管内造成污染。'
fact(r,'X|滑油管路施工作业转运储存防护不足','CONTRIBUTES_TO','S|主机滑油回路残留颗粒杂质',q,'possible')
q='清除管内焊渣、密封管路端口、清洁舱柜污垢等'
for a in ['按建造验收要求清除滑油管内焊渣','施工储存时密封保护滑油管路端口','按验收要求清洁滑油循环舱']:
    actions(r,[(a,'S|主机滑油回路残留颗粒杂质')],q)
q='分别连接构成左、右主机的串油回路'
fact(r,'A|按批准串油工艺区分机外机内独立清洗范围','ACTS_ON','E|主机机外滑油管路装置',q,'guidance')
q='被旁通的设备、阀件、附件接口用盲板或其他措施保护以避免串油中进入灰尘、杂物。'
actions(r,[('串油时保护旁通设备接口防止二次污染','S|主机滑油回路残留颗粒杂质')],q)
q='避免振荡器的振动频率与管系的固有频率相近，否则焊缝处会产生过大应力而损坏管路。'
chain(r,['X|串油振荡激励频率接近管系固有频率','S|串油管系焊缝振动应力过大','F|串油管路焊缝损坏'],q,'possible')
actions(r,[('批准串油工艺避开管系共振激励频率','X|串油振荡激励频率接近管系固有频率')],q)
q='查看临时滤器内的滤网1次，直到无可见的固体杂质颗粒。'
checks(r,[('按串油验收流程检查临时滤网固体颗粒','S|主机滑油回路残留颗粒杂质')],q)
q='再提取油样检测颗粒物污染度'
checks(r,[('串油后取油样检测颗粒物污染度','S|主机滑油回路残留颗粒杂质')],q)
q='经主机服务工程师、船东、船检确认后，串油清洗程序结束。'
fact(r,'A|按主机批准清洁等级和验收程序确认串油完成','ACTS_ON','E|主机机外滑油管路装置',q,'guidance')
q='移走旁通管，拆掉临时滤器，恢复接通管系'
fact(r,'A|串油验收后按恢复清单撤除临时件复位管系','ACTS_ON','E|主机机外滑油管路装置',q,'guidance')
