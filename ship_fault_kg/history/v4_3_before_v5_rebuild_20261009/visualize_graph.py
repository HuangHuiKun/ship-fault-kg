"""Build a self-contained, labelled case viewer and Neo4j Browser GRASS."""
import json
from pathlib import Path
from retrieve import read_store
from schema import VERSION, KIND_ZH, RELATION_ZH, CERTAINTY_ZH, DIAGNOSTIC_RELS, CAUSAL_RELS

OUTPUT = Path(__file__).resolve().parent / 'output'
COLORS = {'FaultType':'#ef4444','Fault':'#f87171','Cause':'#fbbf24','Condition':'#fde68a','Consequence':'#fb923c',
          'Check':'#60a5fa','Action':'#34d399','Symptom':'#a78bfa','Case':'#93c5fd',
          'Subsystem':'#2dd4bf','Component':'#d8b4fe','Equipment':'#c4b5fd','Source':'#94a3b8'}

# Captured from this Browser's "Reset styles to default" on 2026-10-05.
# Preserve its native palette; do NOT use the offline viewer palette in Neo4j.
BROWSER_BASE_COLORS = {'VesselType':'#a3a5f2','Vessel':'#ffb2d7','System':'#e7b04f',
    'Symptom':'#be9dc8','Subsystem':'#bea788','Source':'#c1d1ff','ShipKG':'#ffd95a',
    'Sensor':'#ffd8ff','Run':'#ffa5f6','Observation':'#00b3db','FaultType':'#ffd7ff',
    'Fault':'#e5dfff','Equipment':'#59a9e7','Dataset':'#ff8d69','Consequence':'#86ccd1',
    'Condition':'#ffc736','Component':'#abae8a','Check':'#ffbc00','Cause':'#b1de38',
    'Case':'#7ad7d1','Action':'#b4dbff'}

TEMPLATE = r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>船舶动力故障图谱 V2</title>
<style>*{box-sizing:border-box}body{margin:0;background:#edf2f7;color:#17304b;font:15px "Microsoft YaHei",sans-serif}header{background:#12344d;color:white;padding:22px 30px}h1{margin:0 0 10px;font-size:25px}.stats{color:#bfdded}main{padding:20px}select,button{padding:9px;border:1px solid #c4d1dc;border-radius:5px;background:white;margin-right:8px;font-size:14px}#canvas{margin:15px 0;background:white;border:1px solid #dce5ee;border-radius:8px;overflow:auto;max-height:72vh}#info{background:white;border-radius:8px;padding:16px;line-height:1.7;border-left:5px solid #168ab0;white-space:pre-wrap}#legend span{display:inline-block;padding:4px 10px;border-radius:5px;margin:7px 7px 0 0;font-size:13px}svg text{font-family:"Microsoft YaHei",sans-serif;font-size:12px}g.node,path.edge,text.edge{cursor:pointer}g.node:hover rect{stroke:#0369a1;stroke-width:3}.hint{color:#63758a;font-size:13px;margin:10px 0}.edge-label{paint-order:stroke;stroke:white;stroke-width:5px;stroke-linejoin:round;fill:#263b52}</style>
<header><h1>船舶动力系统故障知识图谱 · V2</h1><div class="stats" id="stats"></div></header>
<main><select id="case" aria-label="选择事故案例"></select><select id="mode" aria-label="选择关系类型"><option value="diagnostic">诊断关系（含检查与措施）</option><option value="causal">仅因果类关系</option><option value="all">案例全部关系（含组织与来源）</option></select><button id="fit">适应宽度</button><button id="real">原始大小</button><div id="legend"></div><p class="hint">每个节点均显示实体名，每条边显示中文关系；点击节点或边查看属性、来源与确定性。因果方向为箭头方向。仅显示同一事故内的关系，不把不同事故拼成因果链。长图可横向滚动。</p><div id="canvas"><svg id="svg" xmlns="http://www.w3.org/2000/svg"></svg></div><div id="info">请选择案例，点击关系查看证据。</div></main>
<script>const DATA=__DATA__;const COLORS=__COLORS__;const DIAG=__DIAG__;const CAUSAL=__CAUSAL__;const KINDS=__KINDS__;const N=DATA.nodes;const E=Object.values(DATA.edges);const cases=Object.values(N).filter(n=>n.kind==='Case').sort((a,b)=>a.name.localeCompare(b.name,'zh'));const sel=document.getElementById('case'),mode=document.getElementById('mode'),svg=document.getElementById('svg'),info=document.getElementById('info');
document.getElementById('stats').textContent=`${cases.length} 起事故 · ${Object.keys(N).length} 个节点 · ${E.length} 条关系 · ${Object.keys(DATA.evidence).length} 条证据 · 5 个子系统`;
for(const n of cases){let o=document.createElement('option');o.value=n.props.case_id;o.textContent=n.name;sel.append(o)}sel.value='queen_mary2_hf_2010';
for(const [k,c] of Object.entries(COLORS)){const s=document.createElement('span');s.style.background=c;s.textContent=KINDS[k]||k;document.getElementById('legend').append(s)}
const ns='http://www.w3.org/2000/svg';function el(tag,attrs={},text=''){let e=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text)e.textContent=text;return e}
function detailsEdge(e){const v=DATA.evidence[e.evidence_id];info.textContent=`${N[e.source].name} —${e.caption}→ ${N[e.target].name}\n关系类型：${e.relation}；确定性：${e.certainty_zh}\n案例：${e.case_id}\n证据ID：${e.evidence_id}\n来源：${v.source_file}，PDF物理页 ${v.page||'不适用'}，定位 ${v.locator}\n原文摘录：${v.quote}\n网址：${v.source_url}`}
function render(){let edges=E.filter(e=>e.case_id===sel.value&&(mode.value==='all'||(mode.value==='causal'?CAUSAL:DIAG).includes(e.relation)));let ids=[...new Set(edges.flatMap(e=>[e.source,e.target]))];let indegree=Object.fromEntries(ids.map(id=>[id,0])),level=Object.fromEntries(ids.map(id=>[id,0]));for(const e of edges)indegree[e.target]++;let q=ids.filter(id=>!indegree[id]);for(let i=0;i<q.length;i++){let a=q[i];for(const e of edges.filter(e=>e.source===a)){level[e.target]=Math.max(level[e.target],level[a]+1);if(--indegree[e.target]===0)q.push(e.target)}}
let max=Math.max(0,...Object.values(level));for(const id of ids){if(['Check','Action'].includes(N[id].kind)){level[id]=0}}let cols={};for(const id of ids){(cols[level[id]]??=[]).push(id)}let pos={};for(const [l,list]of Object.entries(cols)){list.sort((a,b)=>N[a].kind.localeCompare(N[b].kind)||N[a].name.localeCompare(N[b].name,'zh'));list.forEach((id,i)=>pos[id]={x:45+Number(l)*255,y:70+i*118})}let width=(max+1)*255+60,height=Math.max(430,...Object.values(pos).map(p=>p.y+95));svg.replaceChildren();svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.setAttribute('width',width);svg.setAttribute('height',height);svg.dataset.width=width;svg.dataset.height=height;
let defs=el('defs'),marker=el('marker',{id:'arrow',viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:6,markerHeight:6,orient:'auto-start-reverse'});marker.append(el('path',{d:'M0,0 L10,5 L0,10 z',fill:'#7b8d9e'}));defs.append(marker);svg.append(defs);svg.append(el('text',{x:30,y:27,fill:'#52677d'},`${edges.length} 条关系，${ids.length} 个实体 · ${cases.find(n=>n.props.case_id===sel.value).name}`));
edges.forEach((e,i)=>{let a=pos[e.source],b=pos[e.target],forward=b.x>a.x;let x1=a.x+180,y1=a.y+33,x2=b.x,y2=b.y+33;if(!forward){x1=a.x+90;y1=a.y+66;x2=b.x+90;y2=b.y;}
let d=forward?`M${x1},${y1} C${x1+45},${y1} ${x2-45},${y2} ${x2-8},${y2}`:`M${x1},${y1} C${x1+70},${y1+30} ${x2+70},${y2-30} ${x2},${y2-8}`;let path=el('path',{d,fill:'none',stroke:'#8da0af','stroke-width':1.5,'marker-end':'url(#arrow)',class:'edge'});path.addEventListener('click',()=>detailsEdge(e));let title=el('title',{},e.caption+' · '+e.certainty_zh);path.append(title);svg.append(path);let t=el('text',{x:forward?(x1+x2)/2:x1+72,y:(y1+y2)/2-6+(i%3-1)*9,'text-anchor':'middle',class:'edge edge-label'},e.caption);t.addEventListener('click',()=>detailsEdge(e));svg.append(t)});
for(const id of ids){let n=N[id],p=pos[id],g=el('g',{class:'node'});g.append(el('rect',{x:p.x,y:p.y,width:180,height:66,rx:9,fill:COLORS[n.kind]||'#cbd5e1',stroke:'#e2e8f0'}));let txt=n.props.display_name||n.name;let chunks=txt.match(/.{1,13}/gu)||[''];chunks.forEach((s,i)=>g.append(el('text',{x:p.x+90,y:p.y+20+i*17,'text-anchor':'middle'},s)));g.append(el('title',{},n.name+' · '+KINDS[n.kind]));g.addEventListener('click',()=>{info.textContent=`实体：${n.name}\n类型：${KINDS[n.kind]} (${n.kind})\nID：${n.id}\n别名：${n.aliases}\n属性：${JSON.stringify(n.props,null,2)}`});svg.append(g)}info.textContent='点击关系可查看原文依据。此图为静态数据库快照；Neo4j 实时查询以数据库页面为准。';}
sel.onchange=mode.onchange=render;document.getElementById('fit').onclick=()=>{svg.setAttribute('width',document.getElementById('canvas').clientWidth-10);svg.setAttribute('height',(document.getElementById('canvas').clientWidth-10)*Number(svg.dataset.height)/Number(svg.dataset.width))};document.getElementById('real').onclick=()=>{svg.setAttribute('width',svg.dataset.width);svg.setAttribute('height',svg.dataset.height)};render();</script></html>'''


def main():
    data = read_store()
    for n in data['nodes'].values():
        n['props'] = json.loads(n['props'])
    for e in data['edges'].values():
        e['props'] = json.loads(e['props'])
        e['caption'] = e['props'].get('name', RELATION_ZH[e['relation']])
        if e['certainty'] in ('possible', 'probable') and not e['caption'].startswith(('可能','很可能')):
            e['caption'] = CERTAINTY_ZH[e['certainty']] + e['caption']
        e['certainty_zh'] = CERTAINTY_ZH[e['certainty']]
    data.pop('passages')
    page = TEMPLATE.replace('__DATA__', json.dumps(data, ensure_ascii=False).replace('</', '<\\/'))
    page = page.replace('船舶动力故障图谱 V2','船舶动力故障图谱 V'+VERSION).replace('船舶动力系统故障知识图谱 · V2','船舶动力系统故障知识图谱 · V'+VERSION+'（故障为入口）')
    page = page.replace("filter(n=>n.kind==='Case')", "filter(n=>n.kind==='Case'||n.props.knowledge_id)")
    page = page.replace("o.value=n.props.case_id;o.textContent=n.name", "o.value=n.props.case_id||n.props.knowledge_id;o.textContent=(n.props.knowledge_layer==='corpus_secondary'?'语料（待核验）｜':n.props.knowledge_id?'机理｜':'事故｜')+n.name")
    page = page.replace("sel.value='queen_mary2_hf_2010'", "sel.value='knowledge:liner_scuffing'")
    page = page.replace("cases.find(n=>n.props.case_id===sel.value)", "cases.find(n=>(n.props.case_id||n.props.knowledge_id)===sel.value)")
    page = page.replace("${cases.length} 起事故", "${cases.filter(n=>n.kind==='Case').length} 起历史事故 · ${cases.filter(n=>n.props.knowledge_id&&n.props.knowledge_layer!=='corpus_secondary').length} 个故障参考单元 · ${cases.filter(n=>n.props.knowledge_layer==='corpus_secondary').length} 个待核验语料单元")
    page = page.replace('仅显示同一事故内的关系，不把不同事故拼成因果链。', '仅显示同一事故/机理单元的关系，不跨单元拼接因果链；机理不等于本船已证实根因。')
    page = page.replace('案例：${e.case_id}', '知识上下文：${e.case_id}\\n知识层：${e.case_id.startsWith(\'corpus:\')?\'二次语料，待专业人员复核\':e.props.knowledge_layer||\'历史事故/实验资料\'}\\n适用范围：${e.props.applicability||\'历史案例，仅作参照；本船根因仍需确认\'}')
    page = page.replace("info.textContent='点击关系可查看原文依据。此图为静态数据库快照；Neo4j 实时查询以数据库页面为准。';", "info.textContent=(cases.find(n=>(n.props.case_id||n.props.knowledge_id)===sel.value).props.applicability||'历史案例，不能直接推定本船根因')+'\\n点击关系可查看原文依据。此图为静态快照，实时状态以Neo4j为准。';")
    palette = {k:COLORS.get(k,BROWSER_BASE_COLORS[k]) for k in KIND_ZH}
    for key, value in [('__COLORS__', palette), ('__DIAG__', sorted(DIAGNOSTIC_RELS)), ('__CAUSAL__', sorted(CAUSAL_RELS)), ('__KINDS__', KIND_ZH)]:
        page = page.replace(key, json.dumps(value, ensure_ascii=False))
    # A three-column snake layout is useful for reading a short causal chain
    # in a narrow panel, without shrinking the labels of the entire graph.
    page = page.replace('<button id="fit">', '<select id="layout" aria-label="选择布局"><option value="layered">层级布局</option><option value="compact">紧凑阅读布局</option></select><button id="fit">')
    page = page.replace("let width=(max+1)*255+60,height=", "if(document.getElementById('layout').value==='compact'){ids.sort((a,b)=>level[a]-level[b]||N[a].name.localeCompare(N[b].name,'zh'));ids.forEach((id,i)=>{let r=Math.floor(i/3),c=r%2?2-i%3:i%3;pos[id]={x:25+c*235,y:70+r*145}});max=2;}let width=(max+1)*255+60,height=")
    page = page.replace('sel.onchange=mode.onchange=render;', "sel.onchange=mode.onchange=document.getElementById('layout').onchange=render;")
    page = page.replace('let d=forward?', "const backwards=b.x<a.x&&b.y===a.y;const vertical=b.x===a.x&&b.y>a.y;if(backwards){x1=a.x;y1=a.y+33;x2=b.x+180;y2=b.y+33;}let d=forward?")
    page = page.replace("let path=el('path'", "if(backwards)d=`M${x1},${y1} C${x1-20},${y1} ${x2+20},${y2} ${x2+8},${y2}`;if(vertical)d=`M${x1},${y1} C${x1},${y1+30} ${x2},${y2-30} ${x2},${y2-8}`;let path=el('path'")
    page = page.replace('x:forward?(x1+x2)/2:x1+72', 'x:forward||backwards?(x1+x2)/2:x1+25')
    (OUTPUT / 'graph_viewer.html').write_text(page, encoding='utf-8')
    # Browser preview applies the later matching rule at higher priority.
    # Keep the common ShipKG fallback FIRST, before every concrete entity kind.
    grass = 'node.ShipKG { color: #ffd95a; diameter: 25px; size: 25px; caption: "{display_name}"; }\n'
    styles = {'node.ShipKG': {'color': '#ffd95a', 'diameter': '25px', 'size': '25px', 'caption': '{display_name}'}}
    for kind in KIND_ZH:
        # Unified Fault category uses the existing Fault style. No extra labels
        # or palette are introduced merely to distinguish reference roles.
        size = '25px'
        color = BROWSER_BASE_COLORS[kind]
        grass += f'node.{kind} {{ color: {color}; diameter: {size}; size: {size}; caption: "{{display_name}}"; }}\n'
        styles['node.' + kind] = {'color': color, 'diameter': size, 'size': size, 'caption': '{display_name}'}
    for relation in RELATION_ZH:
        grass += f'relationship.{relation} {{ color: #74889A; shaft-width: 2px; width: 2px; caption: "{{name}}"; }}\n'
        styles['relationship.' + relation] = {'color': '#74889A', 'shaft-width': '2px', 'width': '2px', 'caption': '{name}'}
    (OUTPUT / 'shipkg_v4.grass').write_text(grass, encoding='utf-8')
    (OUTPUT / 'shipkg_v4_json.grass').write_text(json.dumps(styles, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Created graph_viewer.html and shipkg_v4.grass')


if __name__ == '__main__':
    main()
