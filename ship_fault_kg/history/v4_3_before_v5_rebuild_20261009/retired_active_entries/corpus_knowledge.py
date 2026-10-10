"""Full corpus indexing and quote-checked, secondary-source KG pilot.

Candidate sentences are NOT graph assertions. No LLM is allowed to invent
causal links. Reviewed below means a human-style source-text check, not expert
engineering validation. Dataset train/val/test folders are provenance only.
"""
import hashlib
import re
from schema import VERSION, KIND_ZH, RELATION_ZH, CAUSAL_RELS

SOURCE = 'marine_diesel_RAG_corpus_All_data.zip'
POLICY = '二次语料；仅已核对原文，待专业人员复核；不得替代厂家手册或实船检验'

# Each assertion carries an exact quotation. Interpretive links use MAY_*.
ARTICLES = [
    dict(path='val/船机帮MANKSZ型柴油机活塞冷却系统故障分析.md',
         scope='MAN K9SZ52/105B/BL活塞水冷机型，不能推广到油冷活塞', system='cooling',
         facts=[
             ('Fault|活塞冷却喷嘴板堵塞','CAUSES','Condition|活塞顶部冷却水量不足', '当活塞顶部冷却的喷嘴板严重堵塞时，活塞顶部钻孔冷却空间无水进行冷却，或冷却水量不足，活塞顶部容易过热'),
             ('Condition|活塞顶部冷却水量不足','INCREASES_RISK_OF','Fault|活塞顶部过热', '当活塞顶部冷却的喷嘴板严重堵塞时，活塞顶部钻孔冷却空间无水进行冷却，或冷却水量不足，活塞顶部容易过热'),
             ('Condition|进水套管内冷却水流通受阻','CAUSES','Symptom|活塞冷却水进口温度高于出口', '活塞冷却水进口套管中的水量失去流通性，在进水套管中不断被其往复运动压缩升温'),
             ('Check|检查活塞顶部冷却喷孔通畅性','CHECKS','Fault|活塞冷却喷嘴板堵塞', '只有6个孔是通畅的，其余全被脏物封死'),
         ]),
    dict(path='test/船机帮一起副机冷却水失压停车故障的处理和原因分析.md',
         scope='文中共享中央淡水冷却回路；须核对本船空压机冷却器与副机回路连接', system='cooling',
         facts=[
             ('Fault|空压机高压冷却器渗漏','MAY_CONTRIBUTE_TO','Condition|压力空气进入共享冷却淡水回路', '发现 No.3 主空压机高压冷却器渗漏'),
             ('Condition|压力空气进入共享冷却淡水回路','MAY_CONTRIBUTE_TO','Condition|冷却淡水回路形成气囊', '若压力空气进入冷却淡水系统, 系统中空气量大于透气管路泄放空气的能力, 系统中就可能形成气囊,导致水泵吸空, 冷却水中断'),
             ('Condition|冷却淡水回路形成气囊','MAY_CONTRIBUTE_TO','Fault|冷却水泵吸空', '系统中就可能形成气囊,导致水泵吸空, 冷却水中断'),
             ('Fault|冷却水泵吸空','LEADS_TO','Condition|副机冷却水供给中断', '系统中就可能形成气囊,导致水泵吸空, 冷却水中断'),
             ('Condition|副机冷却水供给中断','MAY_CONTRIBUTE_TO','Fault|副机高温保护停机', 'No.1 副机高温冷却淡水低压报警, 温度很快上升, 部分负荷卸载后仍达到停车保护极限温度而自动停车'),
             ('Check|按机型规程隔离并检漏空压机冷却器','CHECKS','Fault|空压机高压冷却器渗漏', '隔离 No.3 主空压机, 检查其高、低压冷却器并泵压试验'),
             ('Action|由合格人员修复检验确认的空压机冷却器渗漏','ADDRESSES','Fault|空压机高压冷却器渗漏', '修复 No.3 主空压机高压冷却器后单独使用该机'),
         ]),
    dict(path='train/油品课堂第六讲某船使用假冒润滑油导致主机烧瓦事故案例.md',
         scope='二次转载文章，船舶/原始报告身份未核实；不计入正式事故案例', system='lubrication',
         facts=[
             ('Cause|润滑油质量不符合要求','MAY_CONTRIBUTE_TO','Condition|滑油系统油泥沉积', '这批假油，不但油膜强度不足，而且容易变质形成漆膜和油泥等沉积物，堵塞机油滤清器和油道，影响正常供油，导致烧瓦'),
             ('Condition|滑油系统油泥沉积','CAUSES','Fault|滑油滤清器与油道堵塞', '这批假油，不但油膜强度不足，而且容易变质形成漆膜和油泥等沉积物，堵塞机油滤清器和油道，影响正常供油，导致烧瓦'),
             ('Fault|滑油滤清器与油道堵塞','LEADS_TO','Condition|轴承滑油供给不足', '堵塞机油滤清器和油道，影响正常供油，导致烧瓦'),
             ('Condition|轴承滑油供给不足','INCREASES_RISK_OF','Fault|轴瓦烧伤', '烧瓦的主要原因是机油供应不足且品质不佳，轴瓦产生干摩擦引起高温，使瓦面上的合金熔化'),
             ('Check|检查滑油滤清器与油道沉积','CHECKS','Fault|滑油滤清器与油道堵塞', '拆检发现机油滤清器淤塞严重，油底壳及油道拐弯等处沉积有大量油泥'),
             ('Action|核验润滑油质量并按厂家规格选油','ADDRESSES','Cause|润滑油质量不符合要求', '要高度重视机油的优劣，正确选用润滑油'),
         ]),
    dict(path='test/船机帮5S60ME船用柴油机喷油器故障分析与对策.md',
         scope='MAN B&W 5S60ME-C7；不可套用具体装配尺寸、压力或紧固参数到其他机型', system='fuel_air',
         facts=[
             ('Fault|喷油器壳体密封锥面裂纹','CAUSES','Condition|高温燃气进入低压回油', '气缸内的高压高温燃气穿过喷油器壳体裂纹进入低压燃油中,随回油进入集油筒中导致集油筒中空气多而油位低引发报警'),
             ('Condition|高温燃气进入低压回油','LEADS_TO','Symptom|燃油集油筒低液位报警', '气缸内的高压高温燃气穿过喷油器壳体裂纹进入低压燃油中,随回油进入集油筒中导致集油筒中空气多而油位低引发报警'),
             ('Condition|高温燃气进入低压回油','MAY_CONTRIBUTE_TO','Fault|喷油器针阀过热卡死', '高温燃气引起针阀过热，最终卡死在针阀体内,使主机该缸喷油量减少,排温降低,继而主机降速'),
             ('Fault|喷油器针阀过热卡死','LEADS_TO','Symptom|单缸排气温度降低', '高温燃气引起针阀过热，最终卡死在针阀体内,使主机该缸喷油量减少,排温降低,继而主机降速'),
             ('Action|保持燃油净化设备正常运行并核验油质','ADDRESSES','Cause|燃油固体颗粒造成针阀运动受阻', '维持燃油净化设备正常运行，保证油质清洁,防止燃油中的固体颗粒造成止回阀和针阀运动阻力增大甚至卡死'),
         ]),
]


def normalize(text):
    return ' '.join(text.split())


def build_corpus_knowledge(builder, root):
    parent = builder.source(SOURCE)
    builder.nodes[parent]['props'].update(source_level='资料级', kind_zh=KIND_ZH['Source'], graph_version=VERSION, source_tier='secondary', expert_review='pending', warning=POLICY)
    ids = []
    for article in ARTICLES:
        path = root / article['path']
        raw = path.read_text(encoding='utf-8-sig')
        text = normalize(raw)
        scope = 'corpus:' + hashlib.sha1(article['path'].encode()).hexdigest()[:12]
        source = builder.node('Source', path.stem, path.stem,
            source_level='文章级', local_item=str(path.relative_to(root.parents[2])).replace('\\', '/'),
            locator=article['path'], knowledge_id=scope, knowledge_layer='corpus_secondary',
            source_tier='secondary', expert_review='pending', applicability=article['scope'],
            warning=POLICY, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            url=builder.source_by_file[SOURCE]['source_url'])
        local_nodes = {}
        for a, relation, b, quote in article['facts']:
            anchor = normalize(quote)
            position = text.find(anchor)
            if position < 0:
                raise ValueError(f'Corpus quote absent: {article["path"]}: {quote}')
            evidence = builder.evidence_row(SOURCE, f'{article["path"]}:normalized_chars={position}:{position+len(anchor)}', anchor, 'corpus_secondary')
            for token in (a, b):
                if token not in local_nodes:
                    kind, name = token.split('|', 1)
                    # Scoped IDs prevent a second-hand claim contaminating a verified case.
                    ident = 'shipkg:' + kind.lower() + ':' + hashlib.sha1((scope+'|'+token).encode()).hexdigest()[:12]
                    builder.nodes[ident] = dict(id=ident, kind=kind, name=name, aliases=name,
                        props=dict(kind_zh=KIND_ZH[kind], display_name=name, graph_version=VERSION,
                                   knowledge_layer='corpus_secondary', source_tier='secondary',
                                   expert_review='pending', applicability=article['scope'], corpus_scope=scope,
                                   **({'fault_level':'事件/状态'} if kind=='Fault' else {})))
                    local_nodes[token] = ident
                    builder.edge(source, 'INVOLVES', ident, evidence, scope, 'corpus_statement', name=RELATION_ZH['INVOLVES'])
            builder.edge(local_nodes[a], relation, local_nodes[b], evidence, scope, 'corpus_statement',
                name=('语料记载·' + RELATION_ZH[relation]), source_tier='secondary', expert_review='pending',
                applicability=article['scope'], warning=POLICY)
            builder.edge(source, 'DOCUMENTED_BY', parent, evidence, scope, 'corpus_statement', name=RELATION_ZH['DOCUMENTED_BY'])
        system = next(n['id'] for n in builder.nodes.values() if n['kind']=='System' and article['system'] in n['aliases'].split())
        builder.edge(source, 'IN_SYSTEM', system, evidence, scope, 'curated_classification', name=RELATION_ZH['IN_SYSTEM'])
        ids.append(scope)
    for edge in builder.edges.values():
        edge['props'].update(graph_version=VERSION, is_causal=edge['relation'] in CAUSAL_RELS)
    for node in builder.nodes.values():
        node['props'].update(graph_version=VERSION, kind_zh=KIND_ZH[node['kind']], display_name=node['name'])
    return dict(quote_checked_articles=len(ARTICLES), expert_verified_articles=0,
                asserted_facts=sum(len(a['facts']) for a in ARTICLES), knowledge_ids=ids,
                policy=POLICY, candidate_sentences_are_graph_assertions=False)


def index_corpus(builder, root):
    inventory, candidates = [], []
    seen = {}
    for path in sorted(root.rglob('*.md')):
        raw = path.read_text(encoding='utf-8-sig')
        text = normalize(raw)
        rel = path.relative_to(root).as_posix()
        fingerprint = hashlib.sha256(text.encode()).hexdigest()
        duplicate = seen.get(fingerprint, '')
        seen.setdefault(fingerprint, rel)
        passage_ids = []
        # Full normalized text is covered; overlap avoids cutting context at boundaries.
        start = 0
        while start < len(text):
            end = min(start + 1400, len(text))
            ident = 'passage:' + hashlib.sha1((rel+'|'+str(start)).encode()).hexdigest()[:16]
            builder.passages[ident] = dict(id=ident, source_file=SOURCE,
                source_url=builder.source_by_file[SOURCE]['source_url'], page='',
                kind='corpus_article', title=path.stem, text=text[start:end],
                locator=f'{rel}:normalized_chars={start}:{end}')
            passage_ids.append(ident)
            if end == len(text):
                break
            start = end - 150
        inventory.append(dict(path=rel, title=path.stem, original_split=rel.split('/')[0],
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(), normalized_sha256=fingerprint,
            chars=len(text), duplicate_of=duplicate, passages=passage_ids,
            graph_article=any(a['path']==rel for a in ARTICLES), source_tier='secondary',
            warning='原train/val/test是资料包分组，不是本项目独立评测分组；不得当作专家标注'))
        for match in re.finditer(r'[^\n。！？]{15,1000}[。！？]?', raw):
            sentence = match.group().strip()
            causal = bool(re.search(r'导致|引起|造成|由于|因此|促使|原因|致使', sentence))
            action = bool(re.search(r'检查|检修|更换|清洗|维护|建议|应当|应及时|防止', sentence))
            if causal or action:
                candidates.append(dict(id='candidate:'+hashlib.sha1((rel+'|'+str(match.start())).encode()).hexdigest()[:16],
                    article=rel, raw_char_start=match.start(), raw_char_end=match.end(), sentence=sentence,
                    candidate_types=(['causal'] if causal else [])+(['maintenance'] if action else []),
                    status='pending_review', graph_assertion=False,
                    note='关键词筛选候选句；须核对主客体、否定、条件、机型和原始来源，不能直接写成因果边'))
    if not inventory:
        raise ValueError('Corpus is empty')
    return inventory, candidates
