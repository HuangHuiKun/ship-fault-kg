// V6 readable export. Author/inspect with the bundled Artifact Tool, save CSV.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';
const runtime=process.env.SHIPKG_RUNTIME_NODE_MODULES ?? 'C:/Users/18270/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const req=createRequire(path.join(runtime,'package.json'));
const {Workbook}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')).href);
const kg=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(kg,'output/v6_assistant');
const read=async name=>(await fs.readFile(path.join(out,name),'utf8')).trim().split(/\r?\n/).map(JSON.parse);
const nodes=new Map((await read('entities.jsonl')).map(n=>[n.id,n]));
const edges=await read('relationships.jsonl');
const claims=new Map((await read('assertions.jsonl')).map(a=>[a.id,a]));
const report=JSON.parse(await fs.readFile(path.join(out,'build_report.json'),'utf8'));
const schema=JSON.parse(await fs.readFile(path.join(out,'schema.json'),'utf8'));
const headers=['起点类别','起点名称','中文关系','终点类别','终点名称','声明性质','适用范围','确定性','来源','原文页码','原文引用','关系ID','声明ID',
 '图谱版本','起点ID','终点ID','来源ID','片段ID','范围ID','起点属性JSON','终点属性JSON','关系属性JSON'];
const matrix=[headers,...edges.map(e=>{
 const a=nodes.get(e.source),b=nodes.get(e.target),c=claims.get(e.props.assertion_id);
 if(!a||!b||!c)throw Error('Unresolved export reference');
 return [schema.classes[a.kind],a.name,e.props.name,schema.classes[b.kind],b.name,
 c.statement_nature,c.applicability,c.certainty,c.locator,c.page??'',c.quote,e.id,c.id,
 report.graph_version,a.id,b.id,c.source_id,c.passage_id,c.scope_id,JSON.stringify(a.props),JSON.stringify(b.props),JSON.stringify(e.props)];
})];
const workbook=Workbook.create();const sheet=workbook.worksheets.add('关系清单');
sheet.getRangeByIndexes(0,0,matrix.length,headers.length).values=matrix;
// These styles are used only for private preview. CSV remains a plain data file.
sheet.getRange('A1:F9').format.font={name:'Microsoft YaHei',size:11};
sheet.getRange('A1:F1').format.font={name:'Microsoft YaHei',size:11,bold:true};
sheet.getRange('A1:F9').format.columnWidth=24;
sheet.getRange('A1:F9').format.rowHeight=42;
sheet.getRange('A1:F9').format.wrapText=true;
workbook.recalculate();
const check=await workbook.inspect({kind:'table',range:'关系清单!A1:F4',include:'values,formulas',tableMaxRows:4,tableMaxCols:6,maxChars:1800});
console.log(check.ndjson);
const values=sheet.getRangeByIndexes(0,0,matrix.length,headers.length).values;
if(values.length!==report.edges+1||new Set(values.slice(1).map(r=>r[11])).size!==report.edges)throw Error('CSV row/ID count mismatch');
if(values.some((r,i)=>r.some((x,j)=>String(x??'')!==String(matrix[i][j]??''))))throw Error('Artifact cell value mismatch');
const csvCell=v=>{const s=String(v??'');return /[",\r\n]/.test(s)?'"'+s.replaceAll('"','""')+'"':s;};
const csv='\uFEFF'+values.map(r=>r.map(csvCell).join(',')).join('\r\n')+'\r\n';
const final=path.join(kg,'output/知识图谱_关系节点属性.csv');
await fs.writeFile(final,csv,'utf8');
const privateDir=path.join(kg,'history/output_refresh_v6_20261013/validation');
await fs.mkdir(privateDir,{recursive:true});
const preview=await workbook.render({sheetName:'关系清单',range:'A1:F9',scale:1});
await fs.writeFile(path.join(privateDir,'csv-after.png'),new Uint8Array(await preview.arrayBuffer()));
await fs.writeFile(path.join(privateDir,'csv_verification.json'),JSON.stringify({version:report.graph_version,rows:edges.length,columns:headers.length,node_count:nodes.size,all_values_match:true,encoding:'UTF-8 BOM',output:final},null,2));
console.log(JSON.stringify({csv:final,rows:edges.length,columns:headers.length}));
