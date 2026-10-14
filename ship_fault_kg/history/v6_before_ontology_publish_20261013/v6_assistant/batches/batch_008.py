"""Four full mechanical texts; equipment hierarchy and model-specific parameters."""
RECORDS=[]
def article(sid,title,system,equipment,scope,case=False,notes=''):
    r=dict(source_id=sid,title=title,system=system,equipment=equipment,scope=scope,
           case=case,review='full_text',notes=notes,facts=[]);RECORDS.append(r);return r
def fact(r,a,rel,b,q,certainty='secondary_stated'):
    r['facts'].append((a,rel,b,q,certainty))
def chain(r,tokens,q,certainty='secondary_stated'):
    for a,b in zip(tokens,tokens[1:]):fact(r,a,'CAUSES',b,q,certainty)
def checks(r,items,q):
    for a,b in items:fact(r,'C|'+a,'CHECKS',b,q,'guidance')
def actions(r,items,q):
    for a,b in items:fact(r,'A|'+a,'ADDRESSES',b,q,'guidance')

r=article('src:ac708c99a88ae09fc8531f94','潍柴170Z及200齿轮结构与装配参考','transmission','潍柴170Z柴油机',
    '二手文章引用机型说明书；170Z、200和WHM6160结构不可混用；厂家最终版本优先。')
q='1.曲轴齿轮 2.发电机惰轮 3.发电机驱动齿轮 4.凸轮轴齿轮 5.大惰轮 6.小惰轮 7.油泵惰轮 8.喷油泵驱动齿轮 9.机油泵驱动齿轮'
for name in ['曲轴齿轮','发电机惰轮','发电机驱动齿轮','凸轮轴齿轮','大惰轮','小惰轮','油泵惰轮','喷油泵驱动齿轮','机油泵驱动齿轮']:
    fact(r,'E|潍柴170Z柴油机','HAS_COMPONENT','B|'+name,q)
q='A.正时齿轮 B.双联齿轮 C.中间齿轮一 D.曲轴齿轮 E.淡水泵传动齿轮 F.油泵传动齿轮 G.机油泵传动齿轮 H.中间齿轮二 I.海水泵传动齿轮'
for name in ['正时齿轮','双联齿轮','中间齿轮一','曲轴齿轮','淡水泵传动齿轮','油泵传动齿轮','机油泵传动齿轮','中间齿轮二','海水泵传动齿轮']:
    fact(r,'E|潍柴200整体喷油泵柴油机','HAS_COMPONENT','B|'+name,q)
q='安装时互相啮合的齿轮应按记号对准，才能保证正确的配气正时。'
actions(r,[('按机型齿轮正时标记对准装配','X|配气齿轮正时装配错位')],q)
q='重新拆装时，应按所标记号对准，保证啮合侧隙在允许数值范围内，且检查冷态气门间隙、配气相位值'
checks(r,[('检修核对齿轮啮合侧隙','S|齿轮啮合侧隙异常'),('检修核对冷态气门间隙','S|冷态气门间隙异常'),('检修核对配气相位','X|配气齿轮正时装配错位')],q)
fact(r,'C|检修核对齿轮啮合侧隙','USES_PARAMETER','P|传动齿轮啮合侧隙',q)
fact(r,'C|检修核对冷态气门间隙','USES_PARAMETER','P|冷态气门间隙',q)
fact(r,'C|检修核对配气相位','USES_PARAMETER','P|配气相位',q)
q='各传动齿轮的啮合侧隙在0.19-0.31mm范围内，磨损极限在0.40mm。'
fact(r,'P|传动齿轮啮合侧隙','CHARACTERIZES','E|潍柴170Z柴油机',q)
r['parameter_properties']=[dict(token='P|传动齿轮啮合侧隙',unit='mm',quantity='长度',quote=q)]
q='所有的正时都以曲轴旋转角度做为基准'
fact(r,'P|曲轴旋转角度','CHARACTERIZES','B|曲轴齿轮',q)

r=article('src:d6b6fd944cd7cd5ce87dfbaf','8DK28凸轮轴轴承烧伤机制参考','lubrication','8DK28柴油机',
    '文章描述多台机同类故障；按通用机型机制组织，不合并多个事故记录。',
    notes='修复等同新机以及推广其他机型的绝对结论未采纳；刷镀冷焊和改造均需厂家与船级批准。')
q='凸轮轴腔有烟雾冒出，并伴随着一股刺鼻的焦糊味，并有压力降低'
fact(r,'F|凸轮轴轴承烧伤','HAS_MANIFESTATION','S|凸轮轴腔烟雾焦糊味',q)
fact(r,'F|凸轮轴轴承烧伤','HAS_MANIFESTATION','S|滑油压力下降',q)
q='铝、钒等杂质颗粒进入凸轮轴与轴瓦的间隙中，在外力作用下，最终导致轴瓦拉伤、抱死和轴承壳体严重磨损。'
for f in ['凸轮轴轴瓦拉伤','凸轮轴轴瓦抱死','凸轮轴轴承壳体严重磨损']:
    fact(r,'S|凸轮轴轴瓦间隙进入金属杂质','CONTRIBUTES_TO','F|'+f,q)
q='滑油压力明显不足，使凸轮轴润滑不良，造成凸轮轴与轴瓦的干摩擦，最后导致轴瓦和凸轮轴拉伤、烧伤。'
chain(r,['S|凸轮轴轴承滑油压力不足','S|凸轮轴润滑不良','S|凸轮轴轴瓦干摩擦','F|凸轮轴轴承烧伤'],q)
fact(r,'S|凸轮轴轴瓦干摩擦','CAUSES','F|凸轮轴表面拉伤',q)
q='该处滑油压力仅为0.32 MPa(规定0.5—0.6 MPa)'
fact(r,'S|凸轮轴轴承滑油压力不足','DESCRIBED_BY_PARAMETER','P|凸轮轴轴承滑油压力',q)
r['parameter_properties']=[dict(token='P|凸轮轴轴承滑油压力',unit='MPa',quantity='压力',quote=q)]
q='轴承壳体内孔或者轴瓦外径往往会出现超差，造成凸轮轴轴承壳体与轴瓦形成间隙配合。'
chain(r,['X|凸轮轴轴瓦外径轴承孔尺寸超差','S|凸轮轴轴瓦壳体间隙配合'],q)
q='轴瓦与凸轮轴就一起旋转，使轴瓦润滑油孔与轴承壳体的润滑油孔不对中，造成滑油无法到达轴瓦表面，使轴瓦与凸轮轴之间无法形成油膜'
chain(r,['S|凸轮轴轴瓦随轴转动','S|凸轮轴轴瓦壳体油孔不对中','S|滑油无法到达凸轮轴轴瓦表面','S|凸轮轴轴瓦油膜无法形成'],q)
fact(r,'S|凸轮轴轴瓦油膜无法形成','CONTRIBUTES_TO','S|凸轮轴轴瓦干摩擦',q)
q='督促船东根据柴油机说明书采购合格的润滑油。'
actions(r,[('按8DK28说明书选用合格润滑油','S|滑油质量不合格')],q)
q='加装专门的滑油管直接到达凸轮轴轴承，以解决滑油压力不足问题。'
actions(r,[('按批准设计改善凸轮轴轴承专用供油','S|凸轮轴轴承滑油压力不足')],q)
q='加装限位螺钉，避免了凸轮轴轴瓦的轴向窜动和圆周运动'
actions(r,[('按批准方案改善凸轮轴轴瓦定位','S|凸轮轴轴瓦随轴转动')],q)
q='更换所有凸轮轴轴瓦。'
actions(r,[('按验收标准更换受损凸轮轴轴瓦','F|凸轮轴轴承烧伤')],q)
q='根据测量结果对凸轮轴进行刷镀'
fact(r,'A|按批准修复方案处理凸轮轴表面','ADDRESSES','F|凸轮轴表面拉伤',q,'reported_action')
q='使其内孔尺寸、各档凸轮轴轴承孔同轴度都达到合格产品要求'
checks(r,[('修复后复核凸轮轴轴承孔尺寸同轴度','E|8DK28柴油机')],q)

r=article('src:b07f6011c66bf9695d7b8644','倒顺离合减速齿轮箱滑油高温案例','transmission','倒顺离合减速齿轮箱',
    '二手维修案例；箱体轴承孔缩口错位为检查发现，油压及齿面接触异常为排除假设。',True,
    '开头摩擦系数解释不严谨未提取；工作温度压力只作原例记录，不作为所有齿轮箱阈值。')
q='它由圆柱斜齿轮和倒顺车多片式离合器构成'
fact(r,'E|倒顺离合减速齿轮箱','HAS_COMPONENT','B|圆柱斜齿轮',q)
fact(r,'E|倒顺离合减速齿轮箱','HAS_COMPONENT','B|倒顺车多片式离合器',q)
q='输出轴采用滑动轴承，倒顺离合器齿轮轴采用滚动轴承'
fact(r,'E|倒顺离合减速齿轮箱','HAS_COMPONENT','B|齿轮箱输出轴滑动轴承',q)
fact(r,'B|倒顺车多片式离合器','HAS_COMPONENT','B|离合器齿轮轴滚动轴承',q)
q='齿轮箱体变形，造成轴承孔变形，中心线不同心，进一步造成各轴承运转时不在同一中心上。'
chain(r,['F|减速齿轮箱箱体变形','S|齿轮箱轴承孔变形','S|齿轮箱轴承中心线不同心'],q,'possible')
q='发现轴承孔的中分面处有缩口现象'
fact(r,'F|减速齿轮箱箱体变形','HAS_MANIFESTATION','S|齿轮箱轴承孔中分面缩口',q)
q='工作油压太低造成离合器摩擦片打滑产生发热现象。'
chain(r,['S|离合器工作油压过低','F|离合器摩擦片打滑','S|离合器摩擦片发热'],q,'possible')
q='齿轮付啮合不良，也会产生挤压和摩擦发热'
fact(r,'F|齿轮副啮合不良','CONTRIBUTES_TO','S|齿轮箱齿面摩擦发热',q,'possible')
q='冷却器堵塞造成冷却性能下降，也会造成滑油温度升高。'
chain(r,['F|齿轮箱滑油冷却器堵塞','S|齿轮箱滑油冷却性能下降','S|齿轮箱滑油温度过高'],q,'possible')
q='分别对各摩擦片进行平台检测，检测结果是摩擦片的平面翘起变形小于0.10mm'
checks(r,[('按机型限值检测离合器摩擦片翘曲','S|离合器摩擦片平面翘曲')],q)
q='采取拉钢丝方法检查各轴承孔同轴度和轴线平行度'
checks(r,[('按批准工艺检查齿轮箱轴承孔同轴平行度','S|齿轮箱轴承中心线不同心')],q)
q='测量齿轮箱体各滚动轴承和滑动轴承孔尺寸'
checks(r,[('检修测量齿轮箱轴承孔尺寸','S|齿轮箱轴承孔变形')],q)
q='对中箱体和上盖各滚动轴承孔进行压色检查，根据着色情况修研，扩大滚动轴承外圈与孔接触面积'
checks(r,[('按工艺压色检查轴承外圈箱体接触','S|齿轮箱轴承孔中分面缩口')],q)
actions(r,[('按批准工艺修研齿轮箱轴承孔接触面','S|齿轮箱轴承孔中分面缩口')],q)
q='消除外应力后，在原始螺栓孔上，重新绞配定位螺栓。'
actions(r,[('消除外应力后按批准工艺恢复箱体定位','F|减速齿轮箱箱体变形')],q)
q='滑油压力：0.4MPa ； 离合器工作油压：2.4MPa； 齿轮箱滑油温度：48℃。'
for p in ['齿轮箱滑油压力','离合器工作油压','齿轮箱滑油温度']:
    fact(r,'P|'+p,'CHARACTERIZES','E|倒顺离合减速齿轮箱',q)
r['parameter_properties']=[dict(token='P|齿轮箱滑油压力',unit='MPa',quantity='压力',quote=q),
    dict(token='P|离合器工作油压',unit='MPa',quantity='压力',quote=q),
    dict(token='P|齿轮箱滑油温度',unit='℃',quantity='温度',quote=q)]

r=article('src:9643b7a09d7c43d3643d0e88','齿轮箱应急操纵构型与检查参考','transmission','柴油机直推推进机组',
    '二手应急文章，未说明确切厂家机型；只保留构型、操纵协调、油压确认等原则。',
    notes='机械应急合排、改变油位和60%功率等具体程序未提取为操作建议；应急动作须使用实船获批规程。')
q='柴油机-齿轮箱-联轴器-螺旋桨模块配置'
for c in ['推进柴油机','推进齿轮箱','推进联轴器','推进螺旋桨']:
    fact(r,'E|柴油机直推推进机组','HAS_COMPONENT','B|'+c,q)
q='机舱值班员在机旁应答将辅车钟从“遥控”位置转到“机旁”位置接受控制权'
fact(r,'A|按实船规程与驾驶台确认机旁操纵控制权','ACTS_ON','E|柴油机直推推进机组',q,'guidance')
q='启动齿轮箱电动滑油备用泵，待检查润滑油油压和工作油压是否正常。'
checks(r,[('应急操纵前按规程核对齿轮箱滑油工作油压','E|柴油机直推推进机组')],q)
for p in ['齿轮箱滑油压力','离合器工作油压']:
    fact(r,'C|应急操纵前按规程核对齿轮箱滑油工作油压','USES_PARAMETER','P|'+p,q)
q='在水流冲击下）螺旋桨带转齿轮箱轴，故应确保润滑。'
fact(r,'X|拖航时螺旋桨带转齿轮箱','ASSOCIATED_WITH','S|齿轮箱轴被动旋转',q)
actions(r,[('按厂家拖航规程保障被动旋转齿轮箱润滑','S|齿轮箱轴被动旋转')],q)
