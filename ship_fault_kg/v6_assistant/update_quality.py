"""Refresh V6 descriptive quality statistics without changing KG data."""
import collections
import hashlib
import json
import re
from pathlib import Path
from .pipeline import KG, OUT, rows, save

BUSINESS = {'CAUSES','CONTRIBUTES_TO','INCREASES_RISK_OF','WORSENS','HAS_MANIFESTATION',
            'INDICATES','ASSOCIATED_WITH','PRECEDES','CHECKS','ADDRESSES','ACTS_ON'}
CAUSAL = {'CAUSES','CONTRIBUTES_TO','INCREASES_RISK_OF','WORSENS'}
ARCHIVE = KG/'history/output_refresh_v6_20261013'
QUALITY = KG/'output/船舶故障知识图谱_质量评价标准与实施方案_V6_20261013.md'

def table(headers, records):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join('---' for _ in headers)+' |']+
        ['| '+' | '.join(str(x) for x in record)+' |' for record in records])

def compute():
    nodes = rows(OUT/'entities.jsonl'); edges = rows(OUT/'relationships.jsonl')
    sources = {s['id']:s for s in rows(OUT/'sources.jsonl')}
    nmap = {n['id']:n for n in nodes}
    non_sources = {n['id'] for n in nodes if n['kind']!='Source'}
    business_edges = [e for e in edges if e['relation'] in BUSINESS]
    views = {}
    for name, ids, links in [('G0 全图',set(nmap),edges),
            ('G1 去来源',non_sources,[e for e in edges if e['source'] in non_sources and e['target'] in non_sources]),
            ('G2 业务，固定非来源节点集',non_sources,business_edges),
            ('G2-active，仅业务边端点',{v for e in business_edges for v in (e['source'],e['target'])},business_edges)]:
        pairs={(e['source'],e['target']) for e in links if e['source']!=e['target']}
        adjacent={key:set() for key in ids}
        for a,b in pairs:adjacent[a].add(b);adjacent[b].add(a)
        isolated=sum(not neighbours for neighbours in adjacent.values())
        unseen=set(ids);largest=0
        while unseen:
            seed=unseen.pop();frontier=[seed];size=1
            while frontier:
                for nxt in adjacent[frontier.pop()]:
                    if nxt in unseen:unseen.remove(nxt);frontier.append(nxt);size+=1
            largest=max(largest,size)
        views[name]=dict(nodes=len(ids),records=len(links),unique_pairs=len(pairs),
            density=len(pairs)/(len(ids)*(len(ids)-1)) if len(ids)>1 else 0,
            isolated=isolated,largest_weak_component=largest)
    scoped=collections.defaultdict(lambda:collections.defaultdict(set))
    for e in edges:
        if e['relation'] in CAUSAL:
            scoped[e['props']['scope_id']][e['source']].add(e['target'])
    path_counts=collections.Counter()
    def walk(adj, chain):
        if len(chain)>1:path_counts[len(chain)-1]+=1
        if len(chain)==7:return
        for target in adj.get(chain[-1],()):
            if target not in chain:walk(adj,chain+[target])
    for adj in scoped.values():
        for start in adj:walk(adj,[start])
    concepts={n['id'] for n in nodes if n['kind']=='Fault' and n['props']['entity_level']=='concept'}
    concept_of={e['source']:e['target'] for e in edges if e['relation']=='INSTANCE_OF'}
    hits={name:set() for name in ['cause','manifestation','check','action']}
    for e in edges:
        a=concept_of.get(e['source'],e['source']); b=concept_of.get(e['target'],e['target'])
        if e['relation'] in CAUSAL and b in concepts:hits['cause'].add(b)
        if e['relation']=='HAS_MANIFESTATION' and a in concepts:hits['manifestation'].add(a)
        if e['relation']=='CHECKS' and b in concepts:hits['check'].add(b)
        if e['relation']=='ADDRESSES' and b in concepts:hits['action'].add(b)
    used={n['props']['source_id'] for n in nodes if n['kind']=='Source'}
    categories=collections.Counter(sources[s]['category'] for s in used)
    unique=collections.Counter((e['source'],e['relation'],e['target'],e['props']['scope_id'],
        e['props']['source_id'],e['props']['passage_id'],e['props']['quote']) for e in edges)
    data=dict(version='6.0',views=views,path_counts=dict(sorted(path_counts.items())),
        fault_concepts=len(concepts),fault_direct_coverage={k:len(v) for k,v in hits.items()},
        self_loops=sum(e['source']==e['target'] for e in edges),
        exact_duplicate_extra_records=sum(v-1 for v in unique.values()),
        source_categories=dict(categories),sqlite_sha256=hashlib.sha256((OUT/'ship_fault_kg.sqlite').read_bytes()).hexdigest(),
        g2_relation_codes=sorted(BUSINESS),path_policy='same scope, directed, unique ordered node sequences, no repeated nodes, maximum 6 hops')
    save(OUT/'quality_statistics_v6.json',data)
    return data

def refresh_document(data):
    text=(ARCHIVE/'船舶故障知识图谱_质量评价标准与实施方案_V5_20261012.md').read_text(encoding='utf-8')
    report=json.loads((OUT/'build_report.json').read_text(encoding='utf-8'))
    check=json.loads((OUT/'verification_report.json').read_text(encoding='utf-8'))
    schema=json.loads((OUT/'schema.json').read_text(encoding='utf-8'))
    text=text.replace('本项目 V5.0 知识图谱。编写与结构统计日期：2026-10-12。','本项目 V6.0 知识图谱。更新与结构统计日期：2026-10-13。')
    text=text.replace('当前 V5 检索器在 `v5/retrieve.py` 中','当前 V6 检索器在 `v6_assistant/retrieve.py` 中（复用 core/retrieve.py 底层算法）')
    text=text.replace('核对 V5 ID','核对 V6 ID').replace('当前 V5 独立测试集','当前 V6 独立测试集').replace('V5对应的独立问题','V6对应的独立问题')
    scope=f'''本次读取 `output/v6_assistant/ship_fault_kg.sqlite`，统计由实际 V6 节点、关系与声明计算。当前数据库为 shipfaultkg，图谱结构与上次导入结果的全属性指纹一致。本文更新不改变图谱或 Neo4j。

- **5,591 个节点、14,334 条关系，12 类实体、24 类关系。**
- Fault 节点1,021个：765个概念、256个情境记录；全类情境记录共811个。
- 直接知识声明3,274条（原726＋新增2,548）；本节 G2 特定业务视图为{data['views']['G2 业务，固定非来源节点集']['records']}条关系，二者单位和关系集合不同。
- 因果类记录1,635条：导致884、促成516、增加风险225、加剧10。
- Source节点299个，注册来源1,308个。原固定片段6,358个，当前片段表7,845条，实际引用精确片段2,085个。
- 本轮助手阅读262个来源，其中253个形成声明、9个未纳入；仍有1,000个未完成本轮阅读。不能以“已登记”替代“已审阅”。
- System为28个：1个根系统、5个大系统、22个细分系统。层次与功能归属是整理者的检索索引，不代表新的因果事实。
- 字段并集为{len(schema['entity_property_fields'])}种实体props字段（另有4个基础字段）和{len(schema['relation_property_fields'])}种关系属性，不是每条记录都填满。
- 专家审核数0，正式抽取准确率、检索指标和增强收益尚未测得。

SQLite文件SHA256：`{data['sqlite_sha256']}`。
图快照的全属性指纹：`{check['snapshot_sha256']}`。
文件指纹与图内容指纹口径不同，均只用于版本核对，不证明知识正确。'''
    text=re.sub(r'(?<=### 2\.1 当前版本的评价对象\n).*?(?=\n### 2\.2)', '\n\n'+scope+'\n',text,flags=re.S)
    text=text.replace('第一轮可对 726 条业务关系抽约 150 条','第一轮可对 3,274 条直接知识声明分层抽约 200～300 条')
    text=text.replace('352 条因果声明','1,635 条因果类记录')
    csv='''`output/知识图谱_关系节点属性.csv` 按当前 V6 的每条关系一行生成，共14,334条数据记录。
保留原13列，追加图谱版本、起终点ID、来源ID、片段ID、范围ID及起点/终点/关系属性JSON。名称列便于阅读，ID和属性列用于复查，JSON可按需展开。
该表不参与建库，不改写金标准，也不是独立人工审核结果。声明ID可以连接当前SQLite；上下文仍须从片段、规范文本与原件回查。'''
    text=re.sub(r'(?<=### 4\.1 现有 CSV 能提供什么，还缺什么\n).*?(?=\n建议另做审核表)', '\n\n'+csv+'\n',text,flags=re.S)
    viewrows=[]
    for name,v in data['views'].items():
        n=v['nodes'];viewrows.append([name,n,f"{v['records']:,}／{v['unique_pairs']:,}",f"{v['density']:.6f}",
            f"{v['isolated']}/{n}＝{v['isolated']/n:.2%}",f"{v['largest_weak_component']}/{n}＝{v['largest_weak_component']/n:.2%}"])
    structural='''以下为本次 V6 全量只读统计，合并平行边、去自环后计算有向密度，弱连通忽略方向。数值不是知识抽取正确率。

'''+table(['视图','节点','关系记录／唯一有向节点对','密度','孤立节点比例','最大弱连通子图占比'],viewrows)+f'''

G2-active 孤立率由选点方式决定，不能用于声称质量优秀。全图的大连通分量可能由 Source 与系统等组织节点连接起来，不能证明每个故障有充分检查与措施。
当前自环{data['self_loops']}条，按端点、关系、scope、来源、片段与引用联合判定的额外完全重复记录{data['exact_duplicate_extra_records']}条；这不排除近义词重复、错误合并或语义错误。
50项已实现的结构/定位/检索探针检查通过，其中10项是开发检索冒烟测试。它们不替代专家审核、原文支持率和正式Recall@K/MRR。
V6校验报告中3,393条 mechanism_and_maintenance_edges 使用另一关系集合，包含参数联系；与本节G2不可混用。
'''
    text=re.sub(r'(?<=### 5\.1 结构结果\n).*?(?=\n### 5\.2)', '\n\n'+structural,text,flags=re.S)
    paths='''限定四类因果关系、同一scope、方向一致、不重复节点，合并同范围相同有向节点对，最多搜索6跳。统计的是节点序列，不是证据组合数，也不是专家认可的路径数。

'''+table(['跳数','V6候选路径数'],[(i,data['path_counts'].get(i,0)) for i in range(1,7)])+'''

1跳与1,635条因果记录可能不同，原因是同范围相同节点对被合并。长链数量不代表可信推理能力，默认检索的三轮邻接扩展也不等于三跳有向因果推理。
既有拉缸、冷却润滑等机理链仍需逐边回查出处、条件和关系强度；混合“导致/促成/增加风险”的链不能全部表述为必然因果。
'''
    text=re.sub(r'(?<=### 5\.2 多跳候选结果\n).*?(?=\n### 5\.3)', '\n\n'+paths,text,flags=re.S)
    n=data['fault_concepts'];cov=data['fault_direct_coverage']
    coverage='''对765个故障概念汇集自身与INSTANCE_OF情境记录上的直接关系：

'''+table(['项目','有相应直接关系的故障概念','比例'],[(label,f'{cov[key]}/{n}',f'{cov[key]/n:.2%}') for key,label in
          [('cause','至少一个入向因果联系'),('manifestation','至少一个出向表现为'),('check','至少一个入向检查'),('action','至少一个入向应对')]])+'''

这是直接联系筛查，既不是原文Recall，也不是目标故障覆盖率。检查或措施可能连在State/Factor上，需要区分间接可达、原文漏抽和资料缺失。
State/Factor/Check/Action的概念数与故障概念比例为1.665/0.502/0.774/0.825。检查与措施仍低于部分规划下限，需补充真实证据，不能为达到比例而制造知识。
V6额外要求审核 classification_role（来源上下文/整理者分类）、source_review_extent（全文/节选/旧证据）、certainty_group和action_status（实施记录/参考建议）。
'''
    text=re.sub(r'(?<=### 5\.3 故障知识缺口的初步筛查\n).*?(?=\n### 5\.4)', '\n\n'+coverage,text,flags=re.S)
    text=text.replace('output/v5/build_report.json','output/v6_assistant/build_report.json').replace('ship_fault_kg/v5/schema.py','ship_fault_kg/v6_assistant/schema.py').replace('ship_fault_kg/v5/retrieve.py','ship_fault_kg/v6_assistant/retrieve.py').replace('[V5 构建报告]','[V6 构建报告]')
    text=text.replace('当前版本实测基线：已经知道什么，还不知道什么','V6 当前版本实测基线：已经知道什么，还不知道什么')
    QUALITY.write_text(text,encoding='utf-8')
    print(json.dumps(dict(quality_document=str(QUALITY),statistics=str(OUT/'quality_statistics_v6.json'),views=data['views'],path_counts=data['path_counts'],coverage=data['fault_direct_coverage'],sources=data['source_categories']),ensure_ascii=False))

def main():
    refresh_document(compute())

if __name__=='__main__':main()
