import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

// Offline naming proposal only. Never writes the original SQLite, graph inventory,
// build source, or Neo4j. IDs and evidence distinguish identically named instances.
const base = path.resolve('ship_fault_kg');
const out = path.join(base, 'review_v4_20261006');
const outputDir = path.join(out, 'outputs', '01a0a94e-c4a7-7221-b6ee-d80584f68a70');
await fs.mkdir(outputDir, { recursive: true });
const input = path.join(base, 'output', 'graph_inventory_v3.json');
const sqlite = path.join(base, 'output', 'ship_fault_kg.sqlite');
const hash = async p => crypto.createHash('sha256').update(await fs.readFile(p)).digest('hex');
const hashes = { inventory: await hash(input), sqlite: await hash(sqlite) };
const raw = JSON.parse(await fs.readFile(input, 'utf8'));
const nodes = Object.values(raw.nodes);
const edges = Object.values(raw.edges);
assert.equal(nodes.length, 500);
assert.equal(edges.length, 1201);
const props = n => typeof n.props === 'string' ? JSON.parse(n.props) : (n.props || {});
const oldZh = {Vessel:'船舶',VesselType:'船型',System:'动力架构',Subsystem:'子系统',Case:'事故案例',Equipment:'设备',Component:'部件',Fault:'故障/事件',Cause:'原因',Condition:'工况/条件',Symptom:'症状',Consequence:'后果',Check:'检查方法',Action:'运维措施',Dataset:'数据集',Run:'试验工况',Sensor:'测点',Observation:'监测记录',Source:'来源',FaultType:'经典故障类别'};
const newZh = {...oldZh, System:'系统',Condition:'工况与状态',Fault:'故障与事件',Observation:'监测摘要',Run:'试验运行',Source:'资料来源',FaultType:'典型故障类别'};
delete newZh.VesselType; delete newZh.Subsystem; delete newZh.Dataset;
const translations = {
 'Injection-valve nozzle clogging':'喷油器喷嘴堵塞',
 'Air-filter clogging (compressor)':'压气机空气滤清器堵塞',
 'Unconfirmed bearing-related warning':'轴承相关预警（未确认）',
 'Fuel dilution':'润滑油燃油稀释',
 'Normal wear trend':'正常磨损趋势（监测参考）',
 'Ring-adhesion':'活塞环黏着',
 'Turbine degradation':'增压器涡轮退化（柴油机试验）',
 'Structural looseness':'结构松动',
 'Piston-ablation':'活塞烧蚀',
 'Mass imbalance':'质量不平衡',
 'Coupling resonance':'联轴器共振',
 'Gear mesh anomaly':'齿轮啮合异常',
 'Liner-wear':'缸套磨损',
 'Additive depletion':'润滑油添加剂耗损',
 'Air-cooler fouling':'增压空气冷却器污损',
 'Unconfirmed bearing-related spectral anomaly':'轴承相关频谱异常（未确认）',
 'High-harmonic impact train':'高次谐波冲击序列',
 'Babbitt wear (Pb)':'巴氏合金磨损（铅指标）',
 'Cooling-water pump cavitation':'冷却水泵汽蚀',
 'Normal operation':'正常运行（状态监测参考）',
 'Ring-wear':'活塞环磨损',
 'Head-crack':'气缸盖裂纹',
 'Normal':'正常状态（燃烧室仿真参考）',
 'Oil-confirmed mixed follow-up; 250 h vibration / 250 h oil':'油液确认后的联合跟踪：振动、油液各每250小时',
 'Vibration-only CBM; 125 h vibration interval':'仅振动状态监测：每125小时检测',
 'Oil-led CBM; 500 h vibration / 125 h oil':'油液主导状态监测：振动每500小时、油液每125小时',
 'Standard monitoring; 500 h vibration / 500 h oil':'常规状态监测：振动、油液各每500小时',
 'Vibration-led CBM; 125 h vibration / 500 h oil':'振动主导状态监测：振动每125小时、油液每500小时',
 '负载 reference operating range':'参考运行负载范围',
 '负载 load program (~40-85%)':'程序变负载（约40%～85%）',
 '负载 40%, 60%, 85% (stepped)':'阶梯负载（40%、60%、85%）',
};
const shipNames = nodes.filter(n => n.kind === 'Vessel' && !props(n).anonymous).map(n => n.name).sort((a,b)=>b.length-a.length);
const genericPrefixes = ['专用货船','滚装客船','拖网渔船','化学品船','双体客船','货船'];
const stripPrefix = name => {
 let result = name;
 for (const prefix of [...shipNames, ...genericPrefixes]) {
   if (result.startsWith(prefix)) { result = result.slice(prefix.length).trim(); break; }
 }
 return result.replace(/^SD\d{4}-\d{2}\s*/, '').trim();
};
const runName = name => {
 if(name === 'Reference_Data.csv') return '参考运行（正常基线）';
 let title = name.startsWith('AF_Clogging/') ? '空气滤清器堵塞试验' :
   name.startsWith('AC_Fouling/') ? '增压空气冷却器污损试验' :
   name.startsWith('Turbine_Degradation/') ? '增压器涡轮退化试验' :
   name.startsWith('Pump_Cavitation/') ? '冷却水泵汽蚀试验' : '喷油器喷嘴堵塞试验';
 if(name.includes('LoadProgram')) return `${title}（双喷孔堵塞、程序变负载）`;
 if(name.includes('40_60_85')) return `${title}（单喷孔堵塞、40%／60%／85%阶梯负载）`;
 const match = name.match(/_(\d+)_Load/);
 return `${title}（${match ? match[1] + '%负载' : '负载待确认'}）`;
};
const obsNames = {
 1:'CAT C7轴系减速器监测摘要（案例A）',2:'CAT 3516C监测摘要（MPEB 1V）',
 3:'CAT 3516C监测摘要（MPEB 3V）',4:'CAT 3516C联轴器监测摘要（EB 1）',
 5:'CAT 3516C减振器监测摘要（EB 2）',6:'CAT 3516C方位推进单元监测摘要（EB 2）',
 7:'CAT 3516C中间轴承监测摘要（EB 4）',8:'CAT C7轴系减速器监测摘要（案例B）',
 9:'CAT 3508B/C主机轴承监测参考',10:'CAT C7主机与轴系监测摘要（案例A、EB）',
 11:'CAT C7主机与轴系监测摘要（案例A、BB）',12:'CAT 3508B/C推进器监测参考'
};
const datasetSources = new Map();
for(const e of edges) if(raw.nodes[e.source].kind === 'Dataset' && e.relation === 'DOCUMENTED_BY') datasetSources.set(e.source,e.target);
assert.equal(datasetSources.size,4);
const proposal = nodes.map(n => {
 const p=props(n); let kind=n.kind, name=n.name, reason='名称与原意一致，建议保留。', operation='保留';
 if(kind==='VesselType') {kind='Vessel'; reason='统一为船舶类型，entity_level=船型；不是某一条真实船的重复节点。';operation='合并类别，保留节点';}
 if(n.kind==='Vessel') reason='统一为船舶类型，entity_level=实船/未公开船名记录；保留案例编号和身份说明。';
 if(kind==='Subsystem') {kind='System';name=name.replace(/子系统$/,'系统');reason='统一为系统类型，system_level=功能系统；保留与动力架构层的区别。';operation='合并类别并改名';}
 if(n.kind==='System') reason='统一为系统类型，system_level=动力架构；不凭类别合并新增架构包含关系。';
 if(['Case','Equipment','Component'].includes(kind)) {
   name=stripPrefix(name);
   if(n.name!==name) {operation='改名';reason='去掉船名、船型或案例编号前缀；原名及船舶/案例范围保留为别名与属性，不合并同名设备。';}
 }
 if(kind==='Sensor') {name=p.display_name;operation='中文改名';reason=`使用原有测点字典的中文名称，保留原列名和单位 ${p.unit}。`;}
 if(translations[n.name]) {name=translations[n.name];operation='中文改名';reason='中文名称便于阅读；原英文、数据来源、标签性质及不确定性保留。';}
 if(kind==='Fault' && p.semantic_class==='normal_reference') {kind='Condition';operation='建议改类并改名';reason='正常基线/正常磨损趋势不是故障，建议移入工况与状态；此项可在审阅时否决。';}
 if(kind==='Run') {name=runName(name);operation='建议中文改名';reason='一个节点表示一个运行文件，不等于一种独立故障；原文件路径保留。';}
 if(kind==='Observation') {name=obsNames[p.record];operation='建议中文改名';reason='12条匿名现场摘要而非12起事故；EB、BB、MPEB代码保留，未核实前不扩译。';}
 if(kind==='Dataset') {operation='删除节点，迁移溯源';reason='删除数据集实体，将51条内容关联改为内容节点到已有来源节点的溯源关系；原资料文件不删除。';}
 if(name.startsWith('CPP')) name=name.replace(/^CPP/, '可调螺距桨');
 if(name.includes('CPP') && ['Action','Check','Condition','Component','Equipment','Case'].includes(kind)) name=name.replaceAll('CPP','可调螺距桨');
 if(kind==='Action') name=name.replaceAll('OEM','原厂');
 if(name!==n.name && operation==='保留') {operation='建议改名';reason='展开常用缩写以便阅读，原名称保留为别名。';}
 const level=n.kind==='VesselType'?'船型':n.kind==='Vessel'?'实船/未公开船名记录':n.kind==='Subsystem'?'功能系统':n.kind==='System'?'动力架构':'';
 return {id:n.id,oldKind:n.kind,kind,name,oldName:n.name,operation,reason,level,props:p,aliases:n.aliases,delete:kind==='Dataset', mergeTarget:''};
});
const byId=Object.fromEntries(proposal.map(n=>[n.id,n]));
const relationNames = {ADDRESSES:'应对',AFFECTS_COMPONENT:'影响部件',ASSOCIATED_WITH:'相关联',AT_LOAD:'运行负载为',BELONGS_TO_SUBSYSTEM:'归属系统',CHECKS:'检查',CONTRIBUTED_TO:'促成',DOCUMENTED_BY:'来源于',HAS_CASE:'发生案例',HAS_CHANNEL:'测点来源于',HAS_COMPONENT:'包含部件',HAS_EQUIPMENT:'涉及设备',HAS_RECOMMENDED_ACTION:'建议采取',HAS_RUN:'试验来源于',IN_SUBSYSTEM:'涉及系统',IN_SYSTEM:'采用系统架构',INCREASES_RISK_OF:'增加风险',INCREASES_SEVERITY_OF:'加剧严重度',INDICATES:'提示',INSTANCE_OF:'归入故障类别',INVOLVES:'涉及',LEADS_TO:'导致',LIMITS_DETECTION_OF:'妨碍发现',MAY_CONTRIBUTE_TO:'可能促成',OF_VESSEL_TYPE:'船型为',PRECEDED:'先于发生',PROMPTS:'应触发处置',REDUCES_EFFECTIVENESS_OF:'削弱措施效果',SHOWS_CONDITION:'呈现状态',TESTS_FAULT:'试验故障为',TRIGGERS:'触发',WORSENS:'加重后果'};
const targetCaptions={Fault:'涉及故障与事件',Cause:'涉及原因',Condition:'涉及工况与状态',Consequence:'涉及后果',Check:'涉及检查方法',Action:'涉及运维措施',Symptom:'涉及症状'};
const edgeProposal=edges.map(e=>{
 let source=e.source,target=e.target,code=e.relation,label=relationNames[code],operation='保留关系',reason='保留原方向、证据及确定性。',deleted=false;
 if(datasetSources.has(source)) {
   if(code==='DOCUMENTED_BY') {deleted=true;operation='删除冗余入口关系';reason='数据集节点删除，此入口关系不生成来源自环；证据记录仍保留。';}
   else {target=datasetSources.get(source);source=e.target;code='DOCUMENTED_BY';label='来源于';operation='转接来源并反向';reason='内容节点直接来源于已有Source节点；旧边ID/原端点/数据集说明保留为迁移记录，不制造因果。';}
 } else if(code==='BELONGS_TO_SUBSYSTEM') {code='BELONGS_TO_SYSTEM';reason='子系统已合并为系统，关系代码相应改为BELONGS_TO_SYSTEM。';operation='改关系类型与名称';}
 else if(code==='IN_SUBSYSTEM') {code='IN_SYSTEM';operation='统一关系类型';reason='采用统一系统类别；中文边名仍区分涉及系统与采用系统架构。';}
 if(e.relation==='INVOLVES') {label=targetCaptions[byId[target].kind]||'涉及';reason='按终点类别细化中文边名；保留INVOLVES代码和非因果性质。';operation='细化中文名称';}
 if(e.relation==='LEADS_TO' && ['possible','probable'].includes(e.certainty)) {label=e.certainty==='possible'?'可能导致':'很可能导致';reason='保留原证据强度，避免把不确定推断写成已确认因果。';operation='细化不确定性名称';}
 const ev=raw.evidence[e.evidence_id];
 assert.ok(ev,`Missing evidence: ${e.evidence_id}`);
 return {...e,source,target,code,label,operation,reason,deleted,oldSource:e.source,oldTarget:e.target,oldRelation:e.relation,evidence:ev};
});
const retained=proposal.filter(n=>!n.delete), keptEdges=edgeProposal.filter(e=>!e.deleted);
assert.equal(retained.length,496); assert.equal(keptEdges.length,1197);
assert.equal(edgeProposal.filter(e=>e.operation==='转接来源并反向').length,51);
assert.ok(keptEdges.every(e=>!byId[e.source].delete && !byId[e.target].delete));
const counts=arr=>arr.reduce((d,n)=>{d[n.kind]=(d[n.kind]||0)+1;return d;},{});
const oldCounts=counts(nodes),newCounts=counts(retained);
const duplicateNames=[];
for(const kind of ['Vessel','System','Equipment','Component','Case']) {
 const groups=new Map();for(const n of retained.filter(n=>n.kind===kind)) {const key=n.name;groups.set(key,[...(groups.get(key)||[]),n]);}
 for(const [name, group] of groups) if(group.length>1) duplicateNames.push({kind,name,ids:group.map(n=>n.id),decision:'只列同名候选，不按名称自动合并；需要身份或案例证据。'});
}
const relCounts=edges.reduce((d,e)=>{d[e.relation]=(d[e.relation]||0)+1;return d;},{});
const newRelCounts=keptEdges.reduce((d,e)=>{d[e.code]=(d[e.code]||0)+1;return d;},{});
const sourceNote='来源：现有V3 SQLite及graph_inventory_v3.json；按稳定ID核对，详细关系出处列于关系审阅表。';
const wb=Workbook.create();
const schema=wb.worksheets.add('类型与关系');
const ent=wb.worksheets.add('实体审阅');
const rel=wb.worksheets.add('关系审阅');
const setup=(s,title,note)=>{
 s.showGridLines=false;s.getRange('A1').values=[[title]];s.getRange('A1').format.font={name:'Arial',size:16,bold:true,color:'#243746'};
 s.getRange('A2').values=[[note]];s.getRange('A2').format.font={name:'Arial',size:10,color:'#586774'};
};
const table=(s,start,headers,rows,name,widths)=>{
 const end=start+rows.length;const last=col(headers.length);
 s.getRange(`A${start}:${last}${end}`).values=[headers,...rows];
 s.getRange(`A${start}:${last}${end}`).format.font={name:'Arial',size:10,color:'#243746'};
 s.getRange(`A${start}:${last}${end}`).format.verticalAlignment='center';
 s.getRange(`A${start}:${last}${end}`).format.wrapText=true;
 s.getRange(`A${start}:${last}${start}`).format={fill:'#334E68',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center',wrapText:true,rowHeight:32};
 s.getRange(`A${start+1}:${last}${end}`).format.rowHeight=68;
 widths.forEach((w,i)=>s.getRange(`${col(i+1)}${start}:${col(i+1)}${end}`).format.columnWidth=w);
 const t=s.tables.add(`A${start}:${last}${end}`,true,name);t.showFilterButton=true;
 return end;
};
function col(n){let s='';while(n){n--;s=String.fromCharCode(65+n%26)+s;n=Math.floor(n/26);}return s;}
const inputStyle=(s,range)=>{s.getRange(range).format.fill='#FFF4D6';s.getRange(range).format.font={name:'Arial',size:10,color:'#1D4ED8'};};
setup(schema,'船舶图谱命名与结构审阅','待确认草案。500个现有节点、1201条现有关系逐项保留审阅记录；尚未重建、尚未导入Neo4j。');
const typeNotes={Vessel:'统一类别，保留17条实船/身份未公开记录。',VesselType:'统一为船舶，保留10个船型概念；不是同一条船的重复项。',System:'统一为系统，保留3个动力架构节点。',Subsystem:'统一为系统，保留5个功能系统节点。',Dataset:'仅删4个图谱节点；51条内容关联转接已有Source，4条入口边删除。',Fault:'23个全英文名称译为中文；另建议把3个正常参考节点转为Condition。',Observation:'12条现场匿名摘要；建议改名监测摘要，不当作事故。',Run:'16个运行文件：15组故障试验、1组正常参考；建议改名试验运行。',FaultType:'12个概念层检索入口；不是12起事故，也不是已训练分类器。'};
table(schema,4,['原类别','现有数量','建议类别','建议代码','我的类别名称','处理缘由'],Object.keys(oldZh).map(k=>[oldZh[k],oldCounts[k],k==='Dataset'?'删除':newZh[k==='VesselType'?'Vessel':k==='Subsystem'?'System':k],k==='Dataset'?'删除':k==='VesselType'?'Vessel':k==='Subsystem'?'System':k,'',typeNotes[k]||'保留类别；具体节点名称见实体审阅。']),'EntityTypeReview',[20,12,22,24,24,78]);
inputStyle(schema,'E5:E24');
schema.getRange('A26').values=[['关系类型映射（中文显示名可修改，代码供程序检索）']];schema.getRange('A26').format.font={name:'Arial',size:14,bold:true};
table(schema,28,['原关系代码','现有数量','建议显示名称','建议代码／迁移','我的显示名称','语义说明'],Object.keys(relCounts).sort().map(k=>{
 let code=k==='BELONGS_TO_SUBSYSTEM'?'BELONGS_TO_SYSTEM':k==='IN_SUBSYSTEM'?'IN_SYSTEM':k;
 let note='保留方向和证据强度，不将相关或时间先后改成因果。';
 if(['HAS_CHANNEL','HAS_RUN'].includes(k)) {code='DOCUMENTED_BY（反向）';note='数据集删除后，测点/试验直接来源于已有资料来源。';}
 if(k==='HAS_CASE')note='船舶到Case保留；Dataset到Observation的12条改为Observation来源于Source。';
 if(k==='SHOWS_CONDITION')note='Observation的12条保留；Dataset的8条改为状态/故障来源于Source。';
 if(k==='DOCUMENTED_BY')note='删除4条Dataset入口边，承接51条内容溯源边，不生成Source自环。';
 if(k==='INVOLVES')note='不新增因果。按终点细化显示为涉及故障、原因、症状、工况、检查、措施或后果。';
 return[k,relCounts[k],relationNames[k],code,'',note];
}),'RelationTypeReview',[32,12,26,38,24,78]);
inputStyle(schema,'E29:E60');
schema.getRange('A62').values=[['草案预计496个节点、1197条关系、17类实体、29类关系；须经您确认后才执行。']];
schema.getRange('A63').values=[[sourceNote]];
schema.getRange('A62:F63').format.rowHeight=24;
schema.freezePanes.freezeRows(4);
setup(ent,'全部实体命名审阅','黄色列可填写。我的名称/我的类别覆盖建议；处理意见、合并目标ID和理由需审核。填写表格不会修改Neo4j。');
const sorted=proposal.sort((a,b)=>a.kind.localeCompare(b.kind)||a.name.localeCompare(b.name,'zh-CN'));
const entityRows=sorted.map((n,i)=>[i+1,n.delete?'删除':newZh[n.kind],n.oldName,n.name,'','待审核',n.reason,'',n.id,oldZh[n.oldKind],n.operation,n.mergeTarget,'','',JSON.stringify(n.props),'',n.aliases]);
table(ent,4,['序号','建议类别','原名称','建议名称','我的名称','处理意见','处理理由','我的类别','实体ID','原类别','建议操作','合并目标ID','名称预览','类别预览','原属性（完整值）','来源索引','原别名'],entityRows,'EntityReview',[8,18,40,40,40,16,72,22,44,18,24,44,40,22,80,80,60]);
inputStyle(ent,'E5:F504');inputStyle(ent,'H5:H504');inputStyle(ent,'L5:L504');
ent.getRange('F5:F504').dataValidation={rule:{type:'list',values:['待审核','接受建议','按我的名称','保留原样','删除','合并','另行说明']}};
ent.getRange('M5:M504').formulas=sorted.map((_,i)=>[`=IF(F${i+5}="保留原样",C${i+5},IF(E${i+5}="",D${i+5},E${i+5}))`]);
ent.getRange('N5:N504').formulas=sorted.map((_,i)=>[`=IF(F${i+5}="保留原样",J${i+5},IF(H${i+5}="",B${i+5},H${i+5}))`]);
for(let i=0;i<sorted.length;i++) {
 const related=edges.filter(e=>e.source===sorted[i].id||e.target===sorted[i].id);
 const ev=[...new Set(related.map(e=>e.evidence_id))];
 ent.getRange(`P${i+5}`).values=[[ev.join('; ')]];
}
ent.getRange('I5:Q504').format.wrapText=false;
ent.getRange('A5:A504').setNumberFormat('#,##0');
ent.freezePanes.freezeRows(4);ent.freezePanes.freezeColumns(2);
setup(rel,'全部关系命名审阅','黄色列可改中文关系名/处理意见。边ID、原端点、证据强度及出处保留；名称预览采用建议实体名，不自动随实体表改名。');
const relSorted=edgeProposal.sort((a,b)=>Number(b.deleted)-Number(a.deleted)||a.code.localeCompare(b.code)||byId[a.source].name.localeCompare(byId[b.source].name,'zh-CN'));
const relRows=relSorted.map((e,i)=>[i+1,byId[e.source].name,e.label,byId[e.target].name,'','待审核',e.operation,e.reason,e.id,e.oldRelation,raw.nodes[e.oldSource].name,raw.nodes[e.oldTarget].name,e.code,e.evidence_id,e.certainty,e.case_id,e.evidence.source_file,e.evidence.page,e.evidence.locator,e.evidence.source_url,'',e.source,e.target,e.oldSource,e.oldTarget,e.evidence.quote,props(e).name]);
table(rel,4,['序号','建议起点实体','建议关系名','建议终点实体','我的关系名','处理意见','建议操作','处理理由','关系ID','原关系代码','原起点名称','原终点名称','建议关系代码','证据ID','证据强度','案例/知识范围','来源文件','来源页码','来源位置','来源URL','关系名预览','建议起点ID','建议终点ID','原起点ID','原终点ID','原证据摘录（完整值）','原中文关系名'],relRows,'EdgeReview',[8,44,24,44,24,16,24,80,32,30,44,44,32,28,24,40,68,14,75,100,24,44,44,44,44,100,24]);
inputStyle(rel,'E5:F1205');
rel.getRange('F5:F1205').dataValidation={rule:{type:'list',values:['待审核','接受建议','按我的名称','保留原样','删除','另行说明']}};
rel.getRange('U5:U1205').formulas=relSorted.map((_,i)=>[`=IF(F${i+5}="保留原样",AA${i+5},IF(E${i+5}="",C${i+5},E${i+5}))`]);
rel.getRange('I5:Z1205').format.wrapText=false;
rel.getRange('A5:A1205').setNumberFormat('#,##0');
rel.freezePanes.freezeRows(4);rel.freezePanes.freezeColumns(2);
// Test the actual manual override formulas and restore all temporary edits.
ent.getRange('E5').values=[['审阅测试名']];assert.equal(ent.getRange('M5').values[0][0],'审阅测试名');ent.getRange('E5').values=[['']];
assert.equal(ent.getRange('M5').values[0][0],ent.getRange('D5').values[0][0]);
ent.getRange('F5').values=[['保留原样']];assert.equal(ent.getRange('M5').values[0][0],ent.getRange('C5').values[0][0]);ent.getRange('F5').values=[['待审核']];
rel.getRange('E9').values=[['审阅测试关系']];assert.equal(rel.getRange('U9').values[0][0],'审阅测试关系');rel.getRange('E9').values=[['']];
assert.equal(rel.getRange('U9').values[0][0],rel.getRange('C9').values[0][0]);
rel.getRange('F9').values=[['保留原样']];assert.equal(rel.getRange('U9').values[0][0],rel.getRange('AA9').values[0][0]);rel.getRange('F9').values=[['待审核']];
wb.recalculate();
console.log((await wb.inspect({kind:'region',sheetId:'实体审阅',range:'A4:F8',maxChars:2000,tableMaxCols:6})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},summary:'formula error scan'})).ndjson);
for(const [sheetName,range,file] of [['类型与关系','A1:F11','schema_preview.png'],['实体审阅','A1:F10','entity_preview.png'],['关系审阅','A1:F10','edge_preview.png']]) {
 const blob=await wb.render({sheetName,range,scale:1,format:'png'});
 await fs.writeFile(path.join(out,file),new Uint8Array(await blob.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(outputDir,'船舶知识图谱实体关系审阅稿.xlsx'));
assert.equal(await hash(input),hashes.inventory);assert.equal(await hash(sqlite),hashes.sqlite);
const summary={sourceHashes:hashes,oldNodeCount:nodes.length,oldEdgeCount:edges.length,oldCounts,newCounts,proposedNodeCount:retained.length,proposedEdgeCount:keptEdges.length,oldRelationCounts:relCounts,newRelationCounts:newRelCounts,duplicateNames,changedNameCount:proposal.filter(n=>n.oldName!==n.name).length,englishFaultCount:nodes.filter(n=>n.kind==='Fault'&&!/[\u4e00-\u9fff]/.test(n.name)).length,englishActionCount:nodes.filter(n=>n.kind==='Action'&&!/[\u4e00-\u9fff]/.test(n.name)).length,datasetRewiredEdges:51,datasetRemovedEdges:4,confirmed:false};
await fs.writeFile(path.join(out,'proposal_preview.json'),JSON.stringify({summary,nodes:proposal,edges:edgeProposal},null,2));
console.log(JSON.stringify(summary,null,2));
