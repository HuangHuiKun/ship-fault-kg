// Optional review workbook. CSV/SQLite are the automatic build outputs.
import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const input=path.resolve(process.argv[2]);
const output=path.join(input,'outputs','kg_v5_20261009');
await fs.mkdir(output,{recursive:true});
const read=async f=>JSON.parse(await fs.readFile(path.join(input,f),'utf8'));
const rows=async f=>(await fs.readFile(path.join(input,f),'utf8')).split(/\r?\n/).filter(Boolean).map(JSON.parse);
const report=await read('build_report.json'),schema=await read('schema.json');
const nodes=await rows('entities.jsonl'),edges=await rows('relationships.jsonl'),registry=await rows('sources.jsonl');
const byId=new Map(nodes.map(n=>[n.id,n]));
const sources=new Map(registry.map(s=>[s.id,s]));
const provenance=new Map();
for(const e of edges.filter(e=>e.relation==='DOCUMENTED_BY')){
  const list=provenance.get(e.source)||[];list.push(sources.get(e.props.source_id));provenance.set(e.source,list);
}
const wb=Workbook.create();
const summary=wb.worksheets.add('规模与比例');
const entity=wb.worksheets.add('实体清单');
const relation=wb.worksheets.add('关系与证据');
const sourceSheet=wb.worksheets.add('来源登记');

function grid(sheet,data,widths,tableName){
  sheet.showGridLines=false;sheet.freezePanes.freezeRows(1);
  const all=sheet.getRangeByIndexes(0,0,data.length,data[0].length);
  all.values=data;all.format.font.name='Microsoft YaHei';all.format.font.size=10;
  all.format.rowHeightPx=25;all.format.verticalAlignment='center';
  const header=sheet.getRangeByIndexes(0,0,1,data[0].length);
  header.format.fill='#183B56';header.format.font.color='#FFFFFF';header.format.font.bold=true;
  header.format.rowHeightPx=32;
  widths.forEach((w,i)=>sheet.getRangeByIndexes(0,i,data.length,1).format.columnWidthPx=w);
  const table=sheet.tables.add(`A1:${String.fromCharCode(64+data[0].length)}${data.length}`,true,tableName);
  table.showFilterButton=true;
}
const entityData=[['类别','名称','层级','案例码','节点ID','别名','作用域','主要附加属性','原始文件','出处URL']];
for(const n of nodes){
  const p=n.props,src=provenance.get(n.id)||[];
  const extra=Object.fromEntries(Object.entries(p).filter(([k])=>!['graph_version','kind_zh','display_name','entity_level','scope_id','knowledge_zone','case_code'].includes(k)));
  entityData.push([schema.classes[n.kind],n.name,p.entity_level,p.case_code||'',n.id,n.aliases.join('；'),p.scope_id||'',JSON.stringify(extra),src.flatMap(s=>s.paths).join('；'),[...new Set(src.map(s=>s.url).filter(Boolean))].join('；')]);
}
grid(entity,entityData,[105,330,145,80,260,330,290,500,500,360],'EntitiesV5');
const relationData=[['起点类别','起点名称','中文关系','终点类别','终点名称','声明性质','作用域','确定性','原文件','物理页码','原文引用','适用边界','出处URL','措施状态','关系ID']];
for(const e of edges){
  const a=byId.get(e.source),b=byId.get(e.target),p=e.props;
  relationData.push([schema.classes[a.kind],a.props.display_name,p.name,schema.classes[b.kind],b.props.display_name,p.statement_nature,p.scope_id,p.certainty,p.source_file,p.page||'',p.quote,p.applicability,p.source_url,p.action_status,e.id]);
}
grid(relation,relationData,[100,320,135,100,320,240,300,135,460,100,700,580,380,260,280],'RelationsV5');
const used=[...new Set(edges.map(e=>e.props.source_id))].map(id=>sources.get(id)).sort((a,b)=>a.title.localeCompare(b.title,'zh'));
const sourceData=[['题名','来源性质','原始路径','原始/分发网址','文件SHA256','授权信息','专家审核']];
for(const s of used)sourceData.push([s.title,s.source_tier,s.paths.join('；'),s.url,s.sha256,s.license,'尚未进行']);
grid(sourceSheet,sourceData,[430,190,600,410,500,550,130],'SourcesV5');

summary.showGridLines=false;summary.freezePanes.freezeRows(5);
summary.getRange('A1:F25').format.font.name='Microsoft YaHei';
summary.getRange('A1:F25').format.font.size=11;summary.getRange('A1:F25').format.rowHeightPx=31;
summary.getRange('A1:F1').merge();summary.getRange('A1').values=[['船舶故障实验知识图谱 · V5 清单']];
summary.getRange('A1:F1').format.fill='#183B56';summary.getRange('A1:F1').format.font.color='#FFFFFF';
summary.getRange('A1:F1').format.font.size=19;summary.getRange('A1:F1').format.font.bold=true;summary.getRange('A1:F1').format.rowHeightPx=48;
summary.getRange('A2:F2').merge();summary.getRange('A2').values=[['2026-10-09快照；不经专家复核，不作为实船操作指令。']];
for(const [header,value,label,formula] of [
 ['A3:B3','A4:B4','总节点',`=COUNTA('实体清单'!$E$2:$E$${nodes.length+1})`],
 ['C3:D3','C4:D4','总关系',`=COUNTA('关系与证据'!$O$2:$O$${edges.length+1})`],
 ['E3:F3','E4:F4','实际来源',`=COUNTA('来源登记'!$E$2:$E$${used.length+1})`]]){
 summary.getRange(header).merge();summary.getRange(header.split(':')[0]).values=[[label]];
 summary.getRange(value).merge();summary.getRange(value.split(':')[0]).formulas=[[formula]];
 summary.getRange(value).setNumberFormat('#,##0');summary.getRange(value).format.font.size=17;
 summary.getRange(header).format.horizontalAlignment='center';summary.getRange(value).format.horizontalAlignment='center';
}
summary.getRange('A5:F5').values=[['实体类别','全部节点','通用概念','相对故障比例','规划范围','比例检查']];
summary.getRange('A5:F5').format.fill='#DCEAF4';summary.getRange('A5:F5').format.font.bold=true;
const kinds=Object.keys(schema.classes),faultRow=kinds.indexOf('Fault')+6;
for(let i=0;i<kinds.length;i++){
 const k=kinds[i],r=i+6,zh=schema.classes[k];
 summary.getRange(`A${r}`).values=[[zh]];
 summary.getRange(`B${r}`).formulas=[[`=COUNTIF('实体清单'!$A$2:$A$${nodes.length+1},A${r})`]];
 summary.getRange(`C${r}`).formulas=[[`=COUNTIFS('实体清单'!$A$2:$A$${nodes.length+1},A${r},'实体清单'!$C$2:$C$${nodes.length+1},"concept")`]];
 if(report.class_ratios_vs_fault_concepts[k]){
  const [lo,hi]=report.class_ratios_vs_fault_concepts[k].planning_range;
  summary.getRange(`D${r}`).formulas=[[`=C${r}/$C$${faultRow}`]];
  summary.getRange(`D${r}`).setNumberFormat('0.000');
  summary.getRange(`E${r}`).values=[[`${lo}～${hi}`]];
  summary.getRange(`F${r}`).formulas=[[`=IF(AND(D${r}>=${lo},D${r}<=${hi}),"符合","检查")`]];
 }
}
summary.getRange('A19:F19').merge();summary.getRange('A19').values=[[`关系含 ${report.relations.DOCUMENTED_BY} 条溯源边；因果类声明 ${report.causal_assertions} 条。`]];
summary.getRange('A20:F20').merge();summary.getRange('A20').values=[['通用概念不含事件实例；同名事件可因不同事故保持不同ID。']];
summary.getRange('A21:F21').merge();summary.getRange('A21').values=[['18篇语料用于正式建图；1,275篇全部已索引，不代表全部已审核。']];
summary.getRange('A23:F23').merge();summary.getRange('A23').values=[['Excel为本次清单快照；CSV随Python构建自动刷新。修改知识请改声明，不改Excel。']];
summary.getRange('A24:F24').merge();summary.getRange('A24').values=[['详细原文、scope、确定性和边界在“关系与证据”表，可筛选到每条声明。']];
summary.getRange('A19:F24').format.font.size=10;summary.getRange('A19:F24').format.font.color='#4A6070';
[175,115,115,155,145,115].forEach((w,i)=>summary.getRangeByIndexes(0,i,25,1).format.columnWidthPx=w);
await wb.recalculate();
console.log((await wb.inspect({kind:'region',sheetId:summary.name,range:'A3:F17',maxChars:3200,tableMaxRows:17,tableMaxCols:6})).ndjson);
const png=await wb.render({sheetName:summary.name,autoCrop:'all',scale:1,format:'png'});
await fs.writeFile(path.join(output,'summary_preview.png'),new Uint8Array(await png.arrayBuffer()));
const file=await SpreadsheetFile.exportXlsx(wb);
const filePath=path.join(output,'知识图谱清单_V5.xlsx');await file.save(filePath);
console.log(JSON.stringify({file:filePath,entityRows:nodes.length,relationRows:edges.length,sourceRows:used.length}));
