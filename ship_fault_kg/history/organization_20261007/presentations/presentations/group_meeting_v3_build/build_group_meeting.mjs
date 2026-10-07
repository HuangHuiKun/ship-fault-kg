import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation, PresentationFile, FileBlob} from '@oai/artifact-tool';
process.env.RUNTIME_NODE_MODULES='C:/Users/18270/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';

const work='D:/RAGQnASystem/RAGQnASystem-main';
const build=path.join(work,'ship_fault_kg/presentations/group_meeting_v3_build');
const out=path.join(work,'ship_fault_kg/presentations/group_meeting_v3_output');
const skill='C:/Users/18270/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const python='C:/Users/18270/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
const {resolvePresentationFont,finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const font=resolvePresentationFont({fontFamily:'Microsoft YaHei'});
const P=Presentation.create({slideSize:{width:1280,height:720}});
const navy='#102B43',teal='#057C91',muted='#526675';
const notes=[];
function txt(s,text,x,y,w,h,size=26,color=navy,bold=false){
 const sh=s.shapes.add({geometry:'textbox',name:text.slice(0,28),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=text;sh.text.style={typeface:font,fontSize:size,color,bold,autoFit:'none',verticalAlignment:'top',insets:{top:0,left:0,right:0,bottom:0}};return sh;
}
function slide(title,subtitle=''){
 const s=P.slides.add();s.background.fill='#FFFFFF';
 txt(s,title,64,42,1152,68,44,navy,true);
 if(subtitle)txt(s,subtitle,66,118,1148,52,25,muted);
 txt(s,String(P.slides.items.length).padStart(2,'0'),1174,679,48,25,17,muted);
 return s;
}
async function image(s,file,x,y,w,h,alt){s.images.add({blob:new Uint8Array(await fs.readFile(file)),contentType:file.endsWith('.png')?'image/png':'image/jpeg',alt,fit:'contain',position:{left:x,top:y,width:w,height:h}});}
function table(s,values,widths,y=192,h=400,size=25){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:64,top:y,width:1152,height:h,columnWidths:widths,values});
 t.borders.assign({fill:'#D8E2E8',width:1,style:'solid'});
 for(let r=0;r<values.length;r++){t.rows[r].height=h/values.length;for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?navy:(r%2?'#F1F7F9':'#FFFFFF');
  cell.text.style={typeface:font,fontSize:size,color:r===0?'#FFFFFF':navy,bold:r===0,verticalAlignment:'middle',autoFit:'none',insets:{left:14,right:12,top:9,bottom:8}};
 }}return t;
}
function note(s,text,src=[]){const n=text+'\n\n资料与引用：\n'+src.join('\n');s.speakerNotes.textFrame.setText(n);notes.push({number:notes.length+1,title:s===P.slides.items[0]?'船舶动力系统故障知识图谱':s.shapes.items[0].text.toString(),text,src});}

const kg=path.join(work,'ship_fault_kg');const data=path.join(work,'ship_fault_kg_data');
const localReport=path.join(kg,'README_CN.md');
const facts=JSON.parse(await fs.readFile(path.join(kg,'output/build_report.json'),'utf8'));
if(facts.node_count!==500||facts.edge_count!==1201||Object.keys(facts.node_types).length!==20||Object.keys(facts.relation_types).length!==32)throw new Error('Source counts changed; revise deck');

// 1. A decorative illustration only. All foreground title text remains editable.
{
 const s=P.slides.add();s.background.fill='#061C34';
 s.images.add({blob:new Uint8Array(await fs.readFile(path.join(build,'ship_cover.png'))),contentType:'image/png',fit:'cover',position:{left:0,top:0,width:1280,height:720},alt:'船舶动力系统概念插图，非真实设备或工程图'});
 txt(s,'船舶动力系统\n故障知识图谱',58,126,540,168,58,'#FFFFFF',true);
 txt(s,'构建进展与知识增强诊断计划',62,329,515,80,30,'#92DEEA');
 txt(s,'汇报人：黄辉坤\n2026年10月组会',64,548,420,78,25,'#FFFFFF');
 txt(s,'封面为概念示意插图',927,683,286,20,16,'#B0C6D4');
 note(s,'各位老师、师兄好。我今天汇报的是船舶动力系统故障知识图谱的构建进展，以及后续怎样利用这个图谱增强诊断报告。我负责的重点是承接前面模型给出的初步诊断结果，为它补充故障机理、检查和运维建议，以及能查到原文的来源证据。',[localReport,'封面插图：内置图像生成工具，仅为概念装饰，不作工程证据。']);
}
// 2. Directly speakable opening summary.
{
 const s=slide('阶段工作总结','已完成资料搜集、图谱构建、Neo4j建库和增强报告原型');
 const lines=[
 ['调研','在已调研范围内，未找到可直接复用的船舶故障图谱，选择自建'],
 ['资料','下载故障数据、官方调查报告、厂家通函，并参考相关论文与代码'],
 ['建库','围绕故障组织实体、因果关系和证据，导入Neo4j并完成可视化'],
 ['下一步','边修订图谱，边开展RAG实验，接入师兄模型的初步诊断结果']];
 lines.forEach(([a,b],i)=>{txt(s,a,68,208+i*100,140,42,31,teal,true);txt(s,b,224,208+i*100,970,76,29);});
 note(s,'这段时间，我先搜寻了船舶相关的知识图谱。虽然找到了相关论文和代码，但在已调研范围内，还没有找到能直接下载复用、又满足我们诊断增强需求的完整图谱，所以选择自己搭建。随后，我下载了船舶故障数据集、官方事故报告和厂家技术资料，以这些材料作为事实和溯源依据，构建了一个以故障为入口的知识图谱，并完成了Neo4j建库和可视化。接下来，我会一边根据真实资料优化图谱，一边做检索和报告增强实验，接收师兄模型输出的初步诊断结果，补充机理解释、建议及来源证据。',[localReport,path.join(data,'05_metadata/README_CN.md')]);
}
// 3. Downloaded materials versus actually incorporated graph facts.
{
 const s=slide('资料来源与各自用途','下载的资料用于筛选和核对，只有带依据的事实进入结构化图谱');
 table(s,[['资料类型','已搜集的代表性内容','在本任务中的用途'],
 ['数据集','船用柴油机实机故障数据、中文RAG语料\n方位推进器CBM、UCI推进仿真数据','设备与故障标签、测点及工况\n仿真与实船资料分开标记'],
 ['事故报告','MAIB：Wight Sky、Windcat 8\nKommandor Susan、Queen Mary 2等','提取故障现象、原因和事件链\n保留报告与物理页码'],
 ['厂家资料','MAN服务通函、STAMFORD/AvK技术说明\n本轮新增下载16份PDF，15份用于结构化事实','补拉缸、烧瓦、轴带与电网机理\n注明适用机型及不确定性'],
 ['论文与代码','船用柴油机故障图谱论文、诊断综述\nHFACS-KG、TSRF等代码参考','参考实体关系模式、因果检索与评价\n参考代码不等于已经集成实现']], [160,586,406],194,412,24);
 txt(s,'原始资料在项目资料包中保留，来源清单记录网址、许可和本地文件位置',66,636,1135,40,23,muted);
 note(s,'资料分成几类。第一类是四个公开数据集，包括实机柴油机故障试验、中文船机语料、推进器状态监测和推进仿真资料，它们提供故障标签、测点和工况。第二类是MAIB官方事故调查报告，主要提供事故原因、经过、后果和建议。第三类是制造商通函，本轮新下载16份PDF，其中15份实际支持新建结构化事实，另一份保留为参考文本。第四类是论文和代码，用来参考本体模式、抽取及检索方法。需要说明：这些资料没有全部转成图谱，仿真数据也没有冒充实船事故，开源代码主要作为参考。',[path.join(data,'05_metadata/source_manifest.csv'),path.join(data,'05_metadata/source_manifest_v3.csv'),'https://doi.org/10.3390/jmse13040693','https://github.com/yijie-sjtu/HFACS-KG','https://github.com/TS-RF/TSRF']);
}
// 4. Numbered factual procedure; the PDF is primary evidence, not decoration.
{
 const s=slide('知识图谱构建与审核','每条诊断关系保留来源，避免把资料中的“可能”写成“已经证实”');
 const stages=[['01 定模式','确定实体类型、关系类型及故障入口'],['02 核对原文','按PDF物理页阅读，拆成最小事实'],['03 整理关系','区分导致、可能促成、相关与检查建议'],['04 合并校验','用稳定ID去重，隔离历史事故和一般机理'],['05 生成主数据','输出SQLite实体、关系、证据和文本片段']];
 stages.forEach(([a,b],i)=>{txt(s,a,66,198+i*84,190,36,28,teal,true);txt(s,b,262,198+i*84,598,58,26);});
 await image(s,path.join(kg,'output/source_review_v3/MAN_SL2016_633_piston_rings_scuffing_page2.png'),902,178,300,425,'MAN拉缸服务通函PDF物理第2页');
 txt(s,'拉缸机理原文\nMAN SL2016-633，第2页',895,610,315,64,21,muted);
 note(s,'构建不是直接让大模型凭空生成一张图。首先确定船舶、设备、部件、故障、原因等实体和关系。接着按原文页码核对，把复杂段落拆成可审核的事实。例如，资料说油膜受损“可能”造成拉缸，我就保留这个可能性，不改成确定结论。然后给实体设置稳定ID，融合重复项，同时给每条关系标注它属于哪起事故或哪一个文献机理单元，避免不同案例拼出一条假的因果链。最后生成SQLite主数据，包含实体、关系、证据和文本片段四张表。当前296个定位锚点检查通过，定位通过仍不能替代专家对工程机理的审核。',[path.join(kg,'build.py'),path.join(kg,'fault_profiles.py'),path.join(kg,'output/source_anchor_audit_v3.json'),'https://www.man-es.com/docs/default-source/service-letters/sl2016-633.pdf']);
}
// 5. Coverage scope: overlapping subsystem classification, not independent incident counts.
{
 const s=slide('故障覆盖与子系统范围','5个功能子系统，12个经典故障参考入口，保留19起历史事故');
 table(s,[['功能子系统','当前包含的故障与参考知识'],
 ['燃油与进排气','拉缸、活塞环和缸套磨损、燃油喷漏火灾'],
 ['润滑与轴承','烧瓦与轴承咬死、发电机轴承机械磨损、轴承电蚀'],
 ['冷却与海水','冷却水通道堵塞与热过载、冷却回路汽蚀、冷却管路失效'],
 ['传动与推进','扭振减振器失效、轴带发电机对中损伤\n联轴器故障、轴系扭振与联轴器过载风险'],
 ['电力与控制','绕组绝缘劣化、船舶电网耦合振荡、谐波滤波失效和失电']], [280,872],194,420,27);
 txt(s,'同一故障可以涉及多个子系统。厂家机理与论文观察均保留适用范围',66,637,1140,40,23,muted);
 note(s,'图谱不是围绕某一条船堆资料，而是围绕故障建立检索入口。现在覆盖燃油进排气、润滑轴承、冷却海水、传动推进、电力控制五个功能子系统。本轮补充了拉缸、烧瓦、轴承电蚀、轴带对中异常和电网振荡等经典知识，形成12个参考入口，同时保留19起历史事故。这12个入口不是12起新增事故，105个Fault节点也不代表105类独立确认的故障。一个故障可以同时涉及热、机械和电气。例如齿轮箱热膨胀影响对中，再影响轴带发电机振动。联轴器的事故证据目前是CPP执行器小联轴器失效，不能说已经证实大型船主轴联轴器断裂机理。',[path.join(kg,'fault_profiles.py'),path.join(kg,'output/build_report.json'),localReport]);
}
// 6. Actual Neo4j graph screenshot with readable editable schema explanation.
{
 const s=slide('实体、因果关系与来源证据','拉缸示例：油膜问题、具体故障、检查和措施共享同一个知识上下文');
 await image(s,path.join(kg,'output/neo4j_v3_scuffing.jpg'),66,176,407,478,'本机Neo4j拉缸图谱真实查询截图');
 txt(s,'20类实体',517,192,680,38,29,teal,true);
 txt(s,'船舶、船型、系统、子系统、设备、部件\n故障类别、故障、原因、条件、症状、后果\n检查、措施、案例、来源\n数据集、运行、测点、观测',517,239,680,154,25);
 txt(s,'32类关系',517,405,680,38,29,teal,true);
 txt(s,'包括归属、导致、可能促成、指示、检查、应对和来源\n分类关系只说明归属，不能当成因果结论',517,451,680,78,25);
 txt(s,'关系上的溯源字段',517,551,680,38,29,teal,true);
 txt(s,'文件名、原文、PDF物理页、网址、确定性、适用范围',517,598,680,57,25);
 note(s,'可以把图谱理解成一个能沿关系查证据的知识网络。它有20类实体：既有船舶、设备和部件，也有故障、原因、症状、后果、检查和措施，还有案例、来源以及实验数据。32类关系里面，只有部分是因果关系，归属和分类关系不能当成机理结论。左边是本机Neo4j的真实拉缸查询，共返回7条诊断关系、9个实体。核心路径是表面抛光或涂抹促成油膜难以维持，油膜问题可能促成黏着拉伤，拉伤导致表面硬化需要修复。同时连接缸况检查、气缸润滑和负荷处理参考措施。每条边都保留文件、原文、页码和机型限制，后续报告可以引用这些字段。',[path.join(kg,'output/neo4j_v3_scuffing.jpg'),path.join(kg,'output/entity_inventory_v3.md'),'https://www.man-es.com/docs/default-source/service-letters/sl2016-633.pdf','https://www.man-es.com/docs/default-source/service-letters/sl2023-737.pdf']);
}
// 7. Screenshot preserves live DB evidence; native numbers remain editable.
{
 const s=slide('Neo4j建库与实际核验','SQLite直接生成MERGE/SET导入语句，无需CSV中转');
 await image(s,path.join(kg,'output/neo4j_v3_counts.jpg'),62,176,397,465,'Neo4j实时统计500节点1201关系15测点12参考入口19事故');
 const stat=[['500','活动节点'],['1201','活动关系'],['332','证据记录'],['852','检索文本片段']];
 stat.forEach(([v,l],i)=>{const x=515+(i%2)*337,y=204+Math.floor(i/2)*161;txt(s,v,x,y,290,65,58,teal,true);txt(s,l,x,y+73,288,45,26);});
 txt(s,'建库：稳定ID、唯一约束、增量导入\n显示：中文实体名和关系名，按故障或事故查看',514,536,680,84,25);
 txt(s,'活动测点保留15个，其余55个及86条关系可恢复归档。原始数据未删除',66,645,1148,36,23,muted);
 note(s,'建库时，我把SQLite里面的实体和关系直接转成Neo4j的MERGE和SET语句，通过已经登录的Browser导入shipfaultkg数据库，不需要先转CSV。节点使用稳定ID，并设置ShipKG.id唯一约束，便于后续增量更新。导入后再查询真实数据库统计，当前是500个活动节点、1201条活动关系，15个核心测点、12个故障入口和19起事故。332条证据和852个文本片段来自SQLite主数据，不是这张Neo4j截图单独统计的结果。可视化显示中文名称，按故障查看比一次显示所有边更直观。55个非核心测点及86条关系只是归档，仍能恢复，原始文件保持不变。',[path.join(kg,'output/neo4j_import_result.json'),path.join(kg,'output/build_report.json'),path.join(kg,'import_neo4j.py'),path.join(kg,'queries_v3.cypher')]);
}
// 8. Editable output excerpt from the existing local Qwen demonstration.
{
 const s=slide('知识增强报告原型','本机Qwen 3B选择证据，程序核查后生成带引用的诊断草稿');
 txt(s,'输入：主机疑似拉缸，如何补充机理解释和检查建议？',66,191,1150,53,29,navy,true);
 table(s,[['图谱提供的知识','增强报告中的表达'],
 ['同一拉缸单元的7条事实\n实体、关系及适用范围','补充油膜难以维持与拉缸的机理联系\n保留“可能”，不确认本船根因'],
 ['检查与运维措施\n对应证据编号','核查缸套表面与活塞环状态\n参考厂家负荷及气缸润滑处理程序'],
 ['MAN通函及PDF物理页码\n原文与来源网址','在解释和建议后给出引用\n说明适用MAN B&W两冲程机型']], [445,707],271,300,26);
 txt(s,'已有24道开发检索题和13项结构／回归检查。独立诊断质量评测仍待开展',66,615,1140,66,24,muted);
 note(s,'图谱建好以后，我已经跑通了一个报告增强原型。输入是“主机疑似拉缸”，检索得到这个参考单元里的7条事实。大模型选择用于解释、检查和措施的证据编号，程序再核查编号及知识上下文，最后按照约束模板输出带页码引用的草稿。所以现在证明的是检索到报告的流程可以运行，还没有证明真实诊断准确率。当前检索用了实体别名、关键词和字符TF-IDF相似度，再结合图关系补全，尚未接入神经向量语义模型或学习式重排序器。24道题是开发自测，不能把自测结果当成独立专家测试。',[path.join(kg,'output/demo_v3_scuffing.md'),path.join(kg,'output/demo_v3_scuffing.json'),path.join(kg,'retrieve.py'),path.join(kg,'generate_demo.py'),path.join(kg,'output/fault_retrieval_evaluation_v3.json')]);
}
// 9. Explicit handoff ownership and inputs. This is a proposed interface, not integrated production.
{
 const s=slide('与师兄诊断模块的衔接','拟约定输入输出接口，将初步诊断补充为有解释、有证据的报告');
 table(s,[['模块与分工','输入或处理内容','交付给下一环节'],
 ['前级诊断模块\n师兄负责','根据运行数据和特征形成初步判断','设备、症状、候选故障\n异常特征与置信信息'],
 ['知识增强模块\n我负责','实体对齐，检索原因、路径与措施\n融合排序，组织证据包，约束LLM','增强诊断报告\n引用证据和不确定性'],
 ['评价环节\n与评价模块对接','评价证据一致性、解释合理性与信息遗漏','修改建议\n补充检索或修订报告']], [250,525,377],194,357,26);
 txt(s,'输入接口需一起确定：设备构型、初步诊断文本、异常特征、候选故障及可用置信信息',66,595,1140,70,26,teal,true);
 note(s,'我这部分与师兄的分工是：前面的诊断模块先根据运行数据和模型，给出设备、症状和候选故障等初步判断。我接收这个结果，先识别和对齐实体，再到知识图谱里检索相关原因、因果路径、检查方法和运维措施，把知识融合、排序后组织成Evidence Pack，也就是带来源的证据包，再引导大模型生成增强报告。增强报告要说明为什么这样判断、有什么检查和建议、依据哪份资料，以及哪里还不确定。最后与评价模块衔接，根据反馈补检索或修改报告。目前接口是拟定方案，尚未宣称已经完成真实数据联调，需要和师兄共同确定字段和设备构型信息。',[localReport,path.join(kg,'example_diagnosis.json'),'模块分工依据用户任务描述；其他师兄的具体模型结构和姓名未获提供，故未编造。']);
}
// 10. Concrete inputs, actions and deliverables for the next research steps.
{
 const s=slide('后续工作与实验计划','图谱持续修订与RAG实验并行推进，逐步接入真实诊断结果');
 table(s,[['阶段','要什么、做什么','验收与输出'],
 ['图谱修订','真实故障报告、手册和专家意见\n增删改实体关系，补来源、机型和审核状态','版本化图谱\n变更清单与可追溯证据'],
 ['检索实验','独立问题集，标注实体、相关事实和正确路径\n比较关键词、语义、图路径及混合策略','Recall@K、Precision@K、MRR\n召回／排序策略与消融结果'],
 ['生成评价','同一批初步诊断输入\n比较无检索、文本RAG与图谱增强输出','证据一致性、解释合理性\n遗漏、幻觉与引用正确性'],
 ['模块联调','师兄的标准化初步诊断与评价反馈\n核查接口，补充检索，迭代报告','端到端增强报告\n实验配置、代码与阶段报告']], [174,578,400],193,412,25);
 txt(s,'优先补齐：真实电域测点、主轴联轴器断裂事故链、独立专家标注与设备适用性审核',66,635,1140,46,23,muted);
 note(s,'后续两条线并行。第一条线是持续优化图谱：拿到真实船舶资料后，修订实体、关系和机型适用性，记录每次变更。第二条线是开展RAG实验：先建立独立标注集，明确哪些实体、事实和路径应该检索到，再用Recall、Precision和MRR优化召回与排序。检索之外，还要比较同一批输入下，不检索、普通文本RAG和图谱增强报告的差别，重点看证据是否一致、解释是否合理、有没有遗漏或幻觉。最后接入师兄的标准化初步诊断和评价反馈，形成完整增强报告。近期最需要的是初步诊断输入样例和专家审核，真实电网测点及主轴断裂事故证据也仍需补充。',[localReport,path.join(kg,'evaluate_fault_v3.py'),'本页为后续研究计划，不代表神经语义检索、评价闭环或真实数据联调已经完成。']);
}

await fs.mkdir(out,{recursive:true});
await (await PresentationFile.exportPptx(P)).save(path.join(build,'candidate.pptx'));
for(let i=0;i<P.slides.items.length;i++){
 const blob=await P.export({slide:P.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(build,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
}
await fs.writeFile(path.join(build,'notes.json'),JSON.stringify(notes,null,2));
const final=path.join(out,'船舶故障知识图谱构建与RAG增强诊断_组会汇报_20261005.pptx');
const tableOwners=[3,5,8,9,10];
const result=await finalizePresentation({workspaceDir:work,candidatePath:path.join(build,'candidate.pptx'),finalPath:final,pythonExecutable:python,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tableOwners.flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:10,requiredNativeTableOwnerSlides:tableOwners,requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
console.log(JSON.stringify({final,slides:P.slides.items.length,result},null,2));
const verifiedPresentation=await PresentationFile.importPptx(await FileBlob.load(final));
for(let i=0;i<verifiedPresentation.slides.items.length;i++){
 const blob=await verifiedPresentation.export({slide:verifiedPresentation.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(build,`final-slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
}
