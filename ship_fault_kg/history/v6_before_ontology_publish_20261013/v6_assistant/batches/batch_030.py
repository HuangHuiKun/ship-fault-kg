"""Representative source excerpts, and one fully read excluded utility article.

Quotes below were actually read by the current assistant; they are explicitly
logged as excerpts, never as full-document reading.
"""
from ship_fault_kg.v6_assistant.authoring import Batch
b=Batch();RECORDS=b.records
def source(sid,title,system,equipment,scope,case=False,notes=''):
 return b.excerpt(sid,title,system,equipment,scope,[],case,notes)
def quote(r,text):
 r['reviewed_excerpts'].append({'text':text});return text

r=source('src:06f2fc322a91e43c15797559','主控安保板TVS过压击穿分析片段',
 'electrical','主机主控与安保电路板','二手电路调查分析；失效链为作者可能原因，不能仅凭TVS烧毁确定供电源故障。',True)
q=quote(r,'当电源正极对机壳出现高压时，正极对机壳的TVS首先被击穿，随后正负极之间的TVS被击穿。')
b.fact(r,'S|主机控制电源正极对机壳过压','INCREASES_RISK_OF','F|控制板对地TVS击穿',q,'possible')
q=quote(r,'因此TVS首先被烧毁短路，电源正极串联的保险熔断')
b.chain(r,['F|控制板对地TVS击穿','S|控制板TVS烧毁短路','F|控制电源正极保险熔断'],q,'case_interpretation')
q=quote(r,'单极对地电压成方波的主要原因为充放电板的绝缘监测仪工作产生的脉冲电压。')
b.fact(r,'S|绝缘监测仪输出脉冲电压','CAUSES','S|控制电源单极对地方波电压',q,'source_interpretation')
q=quote(r,'用示波器测量充放电板输出单相对地电压，其峰值电压为38.6 V，超出TVS击穿电压。')
b.checks(r,[('合格电气人员按原厂规程测量控制电源对地峰值电压','S|主机控制电源正极对机壳过压')],q)

r=source('src:d32f21cc5248dd8edabd2790','柴油机滑油氧化监测与环槽磨损片段',
 'lubrication','发电柴油机润滑与活塞密封装置','二手油液监测案例；窜气属初步怀疑，后续环槽磨损为实际检查记录。',True)
q=quote(r,'怀疑燃烧室可能因密封不良导致了燃气下窜，高温燃气加速了润滑油的降解变质，燃烧副产物通过窜气方式也污染了滑油。')
b.fact(r,'S|燃烧室密封不良','CONTRIBUTES_TO','S|高温燃气窜入曲轴箱',q,'suspected')
b.fact(r,'S|高温燃气窜入曲轴箱','CONTRIBUTES_TO','S|滑油氧化变质加速',q,'suspected')
q=quote(r,'氧化和硝化引起了滑油添加剂消耗、烃类衰变、产生高低温沉积物（漆膜、积碳和油泥），造成酸值和黏度增加。')
for state in ['滑油添加剂消耗','滑油沉积物生成','滑油酸值和黏度增加']:
 b.fact(r,'S|滑油氧化硝化增强','CONTRIBUTES_TO','S|'+state,q)
q=quote(r,'建议船方立即停用该发电柴油机，并对缸套、活塞、活塞环等密封情况进行检查，待故障修复后更换滑油，持续做好油液跟踪监测。')
b.checks(r,[('油液氧化异常后检查活塞缸套活塞环密封','S|燃烧室密封不良')],q)
b.actions(r,[('修复根因后按油品规程更换滑油并跟踪化验','S|滑油氧化变质加速')],q)
q=quote(r,'未发现明显异常损伤，但发现活塞环槽存在不同程度的磨损问题。')
b.checks(r,[('油液异常检查时测量活塞环槽磨损及侧隙','F|活塞环槽磨损')],q)

r=source('src:dc0bc8106b60aec4c8153f79','MAN双燃料机曲轴箱保护排查片段',
 'electrical','MAN双燃料机油雾与飞溅油监测装置','二手保护管理文章；高油雾报警须同时排查真实机损和监测失效。',
 notes='不把文章中的固定10min开箱等待时间作为所有机型的通用安全时限。')
q=quote(r,'当主机冷却水泄漏到润滑油中的情况发生时,主机启动后的滑油高温使水份蒸发产生的水蒸气造成油雾浓度的增加而引起关停。')
b.chain(r,['F|主机冷却水漏入滑油','S|滑油中水分受热蒸发','S|油雾探测浓度升高','S|主机油雾保护关停'],q,'conditional')
q=quote(r,'恶劣环境不适宜电子元器件的使用,极易造成元件老化,产生浓度数值不准,误动作造成跳机的次数增加')
b.chain(r,['X|油雾探测器长期处于高温高振动环境','F|油雾探测器电子元件老化','S|油雾浓度测值失准','S|油雾保护误停机'],q,'possible')
q=quote(r,'取样检测滑油含水情况,避免滑油含水雾化蒸汽造成机组误报警。')
b.checks(r,[('油雾报警后按规程取样检测滑油水分','F|主机冷却水漏入滑油')],q)
q=quote(r,'测量所有主轴瓦,连杆瓦的温度,排查轴瓦情况。')
b.checks(r,[('油雾报警安全停机后核查主轴瓦与连杆瓦温度','E|MAN双燃料机油雾与飞溅油监测装置')],q)
q=quote(r,'在问题原因没有排除前,避免再次启机,以免产生比较严重的后果。')
b.actions(r,[('油雾高温报警原因查清前保持停机并遵循原厂检查程序','S|油雾探测浓度升高')],q)

r=source('src:e22eaf586aae51f0c1f9d5ed','7RT-flex68D缸套低温腐蚀检查片段',
 'lubrication','7RT-flex68D主机气缸润滑装置','二手特定机型案例；使用燃油含硫量和油品碱值均限于原船记录。',True)
q=quote(r,'主机运行在低低负荷转速下，造成了缸套低温腐蚀的发生。')
b.fact(r,'X|主机长期低负荷低转速运行','INCREASES_RISK_OF','F|缸套低温腐蚀',q)
q=quote(r,'残油碱值过低，缸套容易发送低温腐蚀，含铁量会大幅上升，缸套发生磨损。')
b.fact(r,'S|气缸残油碱值过低','INCREASES_RISK_OF','F|缸套低温腐蚀',q)
b.fact(r,'F|缸套低温腐蚀','HAS_MANIFESTATION','S|气缸残油含铁量增加',q)
q=quote(r,'残油碱值过大不仅造成气缸油浪费，还会在活塞头及活塞顶部形成结垢(灰白色沉积物，多钙盐类物质)，造成磨损。')
b.chain(r,['S|气缸残油碱值过大','S|活塞头钙盐类沉积物增加','F|活塞缸套异常磨损'],q,'possible')
q=quote(r,'对主机扫气箱例行定期检查，发现主机每个缸缸套下方出现黑色斑块')
b.fact(r,'F|缸套低温腐蚀','HAS_MANIFESTATION','S|缸套下方出现黑色斑块',q,'case_observed')
b.checks(r,[('按扫气箱安全检查规程核查缸套下部腐蚀斑块','F|缸套低温腐蚀')],q)

r=source('src:e6d4ab2130973b4af5272f2b','轴带发电机转速控制信号故障片段',
 'electrical','主机遥控与轴带发电机低速保护装置','二手信号排查案例；限定B4输出通道和低速保护回路，不泛化为所有轴发跳闸原因。',True)
q=quote(r,'测量发现，这块数字量输出电路板 CH47、CH48 这两个通道损坏，无正确数字量输出去控制相应继电器。')
b.fact(r,'F|主机遥控数字量输出通道损坏','CAUSES','S|轴带发电机控制继电器缺少正确输入信号',q)
b.checks(r,[('按接线图核验遥控板至低速保护继电器的输出信号','F|主机遥控数字量输出通道损坏')],q)
q=quote(r,'短接后失去了轴带发电机的低转速报警和保护作用。')
b.fact(r,'X|临时短接轴带发电机转速保护输入','CAUSES','S|轴带发电机低转速报警保护失效',q)

b.exclude('src:e2496f97e762319dc923d6ff','船舶轮机管路水锤文章',
 '全文主要涉及生活供水辅助管路而非动力故障案例；部分压力波传播解释有明显疑点，本轮不据此新增动力故障声明。',
 '全文已阅读；保留资料索引，后续若获得可靠动力冷却管路资料再补充水锤机理。')
