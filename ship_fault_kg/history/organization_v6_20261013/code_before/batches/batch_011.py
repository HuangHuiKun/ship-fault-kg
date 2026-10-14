"""Two full governor maintenance articles; no universal setpoints or live-work steps."""
RECORDS=[]
def article(sid,title,notes):
    r=dict(source_id=sid,title=title,system='fuel_air',equipment='红江YT111液压调速器',
        scope='二手调速器维护资料；厂家及主机厂匹配要求优先，不能跨机型照搬。',
        case=False,review='full_text',notes=notes,facts=[]);RECORDS.append(r);return r
def fact(r,a,rel,b,q,certainty='secondary_stated'):
    r['facts'].append((a,rel,b,q,certainty))
def chain(r,tokens,q,certainty='secondary_stated'):
    for a,b in zip(tokens,tokens[1:]):fact(r,a,'CAUSES',b,q,certainty)
def checks(r,items,q):
    for a,b in items:fact(r,'C|'+a,'CHECKS',b,q,'guidance')
def actions(r,items,q):
    for a,b in items:fact(r,'A|'+a,'ADDRESSES',b,q,'guidance')

r=article('src:fa7752137fc5080c59fad694','调速器专用油与换油维护参考',
    '不同主机厂油品牌号可能不同；三个月周期和80℃等不是通用限值，不采纳盘车冲洗及溶剂自行清洗程序。')
q='加入调速器油时，盛器用具必须清洁，并用细滤网过滤。'
actions(r,[('按厂家清洁度要求使用洁净盛器加注调速器油','S|调速器工作油污染'),('按厂家滤清要求过滤调速器加注油','S|调速器工作油污染')],q)
q='调速器内的油面应始终保持游标刻度线范围内。'
checks(r,[('巡检调速器工作油油标液位','S|调速器工作油液位异常')],q)
q='必须保持油的高度清洁，经常使用调速器应每三个月换一次油。'
actions(r,[('按机型及油样状态执行调速器换油保养','S|调速器工作油污染')],q)
q='要求调速器油洁净不易产生泡沫、不沉淀、不腐蚀调速器零件、耐热性好、粘度变化小'
checks(r,[('核验调速器油抗泡及沉淀情况','S|调速器油泡沫沉淀异常'),('核验调速器油黏度与耐热适用性','S|调速器工作油黏度不合适')],q)
q='主机厂根据实际情况，也对油品牌号做出了相应调整。'
fact(r,'A|按主机厂匹配要求确认调速器油品牌号','ACTS_ON','E|红江YT111液压调速器',q,'guidance')
q='应做好调速器拉杆、燃油泵齿条之间连接机构的标记'
actions(r,[('换油拆卸前标记调速器拉杆齿条连接','X|调速器拉杆齿条装复错位')],q)
q='搬动或放置调速器时，不得倒置，不能撞击调速器输入轴，也不得将输入轴做支撑！'
fact(r,'A|按厂家要求保持调速器搬运存放方向','ACTS_ON','E|红江YT111液压调速器',q,'guidance')
q='换油后需按照“调速器使用维修说明书”中的补偿调整方法重新调整。'
actions(r,[('换油后由专业人员按厂家规程复核补偿调整','X|调速器补偿调整不当')],q)

r=article('src:a78476fec209d5d3970d1ec5','YT111调速器补偿与调节机制参考',
    '旋钮开度、δ2、速降范围不外推；所有调节限专业人员按获批试验方案，不提供运行中拆盖调整步骤。')
q='111系列表式调速器中具有实现转速遥控的摩擦离合器'
fact(r,'E|红江YT111液压调速器','HAS_COMPONENT','B|调速器遥控摩擦离合器',q)
q='摩擦离合器打滑，即伺服电机的传动操纵不了柴油机的转速时'
fact(r,'F|调速器遥控摩擦离合器打滑','HAS_MANIFESTATION','S|伺服电机无法操纵柴油机转速',q)
q='若螺母的自锁作用失效，应于换新。'
actions(r,[('按厂家规程更换调速器自锁失效螺母','F|调速器摩擦离合器调整螺母自锁失效')],q)
q='可以自动分配和平衡驱动同一组的机组之间的负荷'
fact(r,'P|柴油机稳态调速率','CHARACTERIZES','E|红江YT111液压调速器',q)
q='新装、检修保养后的调速器使用时，必须进行补偿调整。'
actions(r,[('新装检修后按厂家试验方案核验调速器补偿','X|调速器补偿调整不当')],q)
q='补偿调整不当会引起柴油机运行不稳定——游车、起动粗暴、负荷突变时产生大幅度转速变化、恢复时间长等不正常现象、甚至飞车！'
for s in ['柴油机游车','柴油机起动粗暴','负荷突变后转速大幅变化','柴油机转速恢复时间过长']:
    fact(r,'X|调速器补偿调整不当','CONTRIBUTES_TO','S|'+s,q,'possible')
fact(r,'X|调速器补偿调整不当','INCREASES_RISK_OF','F|柴油机飞车',q,'possible')
q='利用节流针阀、补偿指针排除调速器内部的空气。'
actions(r,[('由专业人员按厂家方案排除调速器内部空气','S|调速器内部积气')],q)
q='反馈行程过大，控制滑阀则会过早地提前复位而产生供油量调节不足的现象'
chain(r,['X|调速器补偿反馈行程过大','S|调速器控制滑阀过早复位','S|调速器供油量调节不足'],q)
q='反馈行程过小，产生供油量调节过度的现象。'
fact(r,'X|调速器补偿反馈行程过小','CONTRIBUTES_TO','S|调速器供油量调节过度',q)
q='针阀 开得过大，就会失去节流作用，反馈动作无法到达小反馈活塞，使反馈作用过分减弱，造成供油量调节过度'
chain(r,['X|调速器补偿针阀开度过大','S|调速器补偿节流作用不足','S|调速器反馈作用过弱','S|调速器供油量调节过度'],q)
q='针阀开得过小甚至关闭，反馈作用过分增强，造成供油量调节不足，转速恢复时间长。'
chain(r,['X|调速器补偿针阀开度过小','S|调速器反馈作用过强','S|调速器供油量调节不足','S|柴油机转速恢复时间过长'],q)
q='调速器的稳定性调节，应在调节反馈指针位置的同时调节补偿针阀的开度。'
actions(r,[('专业人员按机型方案联合复核反馈及补偿针阀','X|调速器补偿调整不当')],q)
