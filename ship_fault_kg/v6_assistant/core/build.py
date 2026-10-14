"""Reproducible V5 build from frozen annotations and source-checked additions.

No LLM call, no candidate knowledge zone, no speculative transitive causal edge.
SQLite stores full evidence; Neo4j contains only the twelve business labels.
"""
import ast, collections, csv, importlib.util, json, re, shutil, sqlite3, types
from pathlib import Path
from .preprocess import Registry,KG,DATA,OUT,CORPUS,hid,norm,jsonl,write_json
from .schema import KINDS,RELATIONS,ENDPOINTS,CAUSAL,VERSION
from .curation import ARTICLES,PARAMETERS,PDF_FACTS

BASE=KG/'history/v4_3_before_v5_rebuild_20261009'
FACTORS={
 '非原厂零件超出适用保养周期','未核验大修零件真伪','装入非原厂轴承',
 '固定灭火系统释放前通风口未关闭','盘车联锁未纳入计划维护','盘车状态未标识与操作说明被涂覆',
 '盘车指示灯照明不足','回油法兰未设喷溅保护','回油管缺少有效超压释放',
 '安全阀长期未功能检查','未响应轴承磨损报警与减速请求','未完成厂商四螺钉法兰改造',
 '未核对阀位即拆进口法兰','海水管多年未检查更新','驾驶台无人导致舱底报警漏察',
 '船长不熟悉可调螺距桨备用按钮','船长未核对螺距指示','调光与推进安全按钮相邻相似',
 '备用气瓶上线时未隔离主气瓶','排气隔热与屏蔽缺失损坏','燃油接头喷溅保护缺失',
 '反复燃油漏泄未完整报告','保护测试绕过互感器绕组','关键断路器置于手动位',
 '吊舱舱底传感器位置偏低','缺少失电断路器历史记录','缺少磨粒预警装置',
 '油污抹布遗留在歧管上方','机舱水密门敞开',
}
STATE_FAULTS={
 '推进电机扭矩骤降','推进电机超速','推进电机保护跳闸','全部推进电机停机',
 '进水停机序列启动','吊舱转至90度停放','主机停止','主机无法继续运行',
 '控制空气压力不足','备用空气均压后仍不足','右舷螺距保持前进',
 '海水经泵进口管大量流入','海水进口阀被淹无法接近','燃油喷向裸露高温排气歧管',
 '滑油喷雾接触高温排气护罩','液压油喷向高温排气管','活塞顶部过热','被冷却部件热过载',
 '副机高温保护停机','驾驶台丧失右舷螺距控制','驾驶台丧失左舷螺距控制',
}
ALIASES={'拉缸':'缸套黏着拉伤','烧瓦与轴承咬死':'轴承咬死与烧瓦（工程检索统称）',
         '曲轴扭振减振器失效':'扭振减振器失效','轴承电蚀':'电机与发电机轴承电蚀',
         '船舶电网耦合振荡':'船舶电网电压频率振荡',
         'CPP倒车参数设置错误':'可调螺距桨倒车参数设置错误',
         'CPP备用控制模式误选':'误选可调螺距桨备用控制模式'}
SHORT={'F':'Fault','S':'State','X':'Factor','C':'Check','A':'Action','P':'Parameter','E':'Equipment','B':'Component'}
RELMAP={'LEADS_TO':'CAUSES','CONTRIBUTED_TO':'CONTRIBUTES_TO','MAY_CONTRIBUTE_TO':'CONTRIBUTES_TO',
        'TRIGGERS':'CAUSES','PRECEDED':'PRECEDES','INCREASES_SEVERITY_OF':'WORSENS'}
SYS={'fuel_air':'燃油与进排气系统','lubrication':'润滑与轴承系统','cooling':'冷却与海水系统',
     'transmission':'传动与推进系统','electrical':'电力与控制系统'}

def load_module(name):
    if name=='corpus_knowledge':
        tree=ast.parse((BASE/(name+'.py')).read_text(encoding='utf-8-sig'))
        class DictCalls(ast.NodeTransformer):
            def visit_Call(self,node):
                if not isinstance(node.func,ast.Name) or node.func.id!='dict' or node.args:
                    raise ValueError('Non-literal call in frozen corpus annotation')
                return ast.Dict(keys=[ast.Constant(k.arg) for k in node.keywords],
                                values=[self.visit(k.value) for k in node.keywords])
        value=next(ast.literal_eval(DictCalls().visit(n.value)) for n in tree.body if isinstance(n,ast.Assign)
                   and any(isinstance(t,ast.Name) and t.id=='ARTICLES' for t in n.targets))
        return types.SimpleNamespace(ARTICLES=value)
    spec=importlib.util.spec_from_file_location('frozen_v43_'+name,BASE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def safe_name(kind,name):
    name=ALIASES.get(name,name)
    if kind=='Equipment':
        name=re.sub(r'^(?:SD\d{4}-\d{2}|2017)\s*','',name)
        if name.endswith('系统'): name=name[:-2]+'装置'
    return name

def classify(token):
    pieces=token.split('|');kind=SHORT.get(pieces[0],pieces[0]);name=pieces[1]
    if kind=='Cause': kind='Factor' if name not in {'油道残留碎屑','油路磨粒与污染','异物经滑油进入主轴承','燃油固体颗粒造成针阀运动受阻'} else 'State'
    elif kind=='Condition': kind='Factor' if name in FACTORS else 'State'
    elif kind in {'Symptom','Consequence'}: kind='State'
    elif kind=='Fault' and name in STATE_FAULTS: kind='State'
    return kind,safe_name(kind,name),' '.join(pieces[2:])

class Builder:
    def __init__(self,registry):
        self.r=registry;self.nodes={};self.edges={};self.assertions={};self.issues=[];self.alignments=[]
        self.case_equipment={};self.legacy_name={};self.provenance=set();self.explicit_facts=0
        conn=sqlite3.connect(f'file:{(BASE/"output/ship_fault_kg.sqlite").as_posix()}?mode=ro',uri=True)
        conn.row_factory=sqlite3.Row
        self.oldnodes={row['id']:dict(row) for row in conn.execute('SELECT * FROM nodes')}
        self.oldedges=[dict(row) for row in conn.execute('SELECT * FROM edges')];conn.close()
        for node in self.oldnodes.values():
            props=json.loads(node['props'])
            self.legacy_name[(node['kind'],props.get('original_name',node['name']))]=node['name']

    def node(self,kind,name,scope='',aliases='',**props):
        if kind not in KINDS: raise ValueError('Invalid class '+kind)
        name=safe_name(kind,name)
        ident=hid('shipkg5',kind,name,scope)
        level='context_record' if scope and kind not in {'Case','Vessel','Source'} else 'concept'
        if kind in {'Case','Vessel','Source'}: level={'Case':'case','Vessel':'actual_vessel','Source':'source'}[kind]
        node=self.nodes.setdefault(ident,dict(id=ident,kind=kind,name=name,aliases=[],
            props=dict(graph_version=VERSION,kind_zh=KINDS[kind],display_name=name,
                entity_level=level,scope_id=scope,knowledge_zone='formal_experiment',**props)))
        node['props'].update(props)
        for alias in [aliases,name]:
            if alias and alias not in node['aliases']: node['aliases'].append(alias)
        return ident

    def token(self,token,scope=''):
        kind,name,aliases=classify(token)
        return self.node(kind,name,scope if kind in {'Fault','State','Factor'} else '',aliases)

    def source(self,sid):
        row=self.r.sources[sid]
        return self.node('Source',row['title'],scope=sid,source_id=sid,source_tier=row['source_tier'],
            local_paths=row['paths'],source_level='文章级' if row['category']=='corpus_article' else '资料级',
            sha256=row['sha256'],url=row['url'],license=row['license'],expert_review='not_performed')

    def edge(self,a,rel,b,passage,scope,certainty='stated',nature='source_statement',**more):
        ak=self.nodes[a]['kind'];bk=self.nodes[b]['kind']
        if rel not in RELATIONS or ak not in ENDPOINTS[rel][0] or bk not in ENDPOINTS[rel][1]:
            raise ValueError(f'Invalid endpoints {ak} {rel} {bk}')
        if rel in {'IS_A','INSTANCE_OF'} and ak!=bk: raise ValueError('Cross-kind concept alignment')
        index_natures={'case_index','case_equipment_index','asset_index','applicability_index',
                       'concept_alignment','functional_classification','provenance_index'}
        locator_key=passage['source_id'] if nature in index_natures else passage['id']
        aid=hid('assertion',a,rel,b,scope,locator_key,nature)
        if aid in self.assertions: return
        context_raw,context_text,_=self.r.pages[(passage['source_id'],str(passage['page']) if passage['page'] is not None else '')]
        start=passage['normalized_start'];end=passage['normalized_end']
        source=self.r.sources[passage['source_id']]
        reviewed='assistant_source_text_check' if nature.startswith(('source','secondary')) else 'explicit_migration_or_index_rule'
        action_status='not_applicable'
        if ak=='Action' and rel in {'ADDRESSES','ACTS_ON'}:
            if certainty=='reported_action': action_status='reported_in_source_context'
            elif certainty=='derived_action': action_status='analyst_suggested_for_review'
            elif 'recommendation' in nature or (nature=='source_guidance_statement' and certainty=='guidance'):
                action_status='recommended_reference'
            else: action_status='reported_or_recommended_unspecified'
        assertion=dict(id=aid,subject=a,relation=rel,object=b,source_id=passage['source_id'],
            passage_id=passage['id'],scope_id=scope,certainty=certainty,polarity='positive',
            statement_nature=nature,review_status='accepted_for_experiment',review_method=reviewed,
            reviewer='Codex assistant',expert_review='not_performed',source_tier=source['source_tier'],
            quote=passage['text'],context=context_text[max(0,start-280):end+280],
            applicability=more.get('applicability','仅在本声明来源及构型范围内使用'),
            action_status=more.get('action_status',action_status),
            source_version=source['sha256'],locator=passage['locator'],page=passage['page'],
            normalized_start=start,normalized_end=end,**{k:v for k,v in more.items() if k not in {'applicability','action_status'}})
        self.assertions[aid]=assertion
        eid=hid('edge',aid)
        props=dict(id=eid,assertion_id=aid,name=RELATIONS[rel],graph_version=VERSION,
            scope_id=scope,certainty=certainty,polarity='positive',statement_nature=nature,
            source_id=passage['source_id'],passage_id=passage['id'],source_tier=source['source_tier'],
            source_file=passage['locator'],source_url=source['url'],page=str(passage['page'] or ''),
            quote=passage['text'],locator=passage['locator'],source_sha256=source['sha256'],
            is_causal=rel in CAUSAL,review_method=reviewed,expert_review='not_performed',
            applicability=assertion['applicability'],action_status=assertion['action_status'])
        self.edges[eid]=dict(id=eid,source=a,relation=rel,target=b,props=props)

    def documented(self,node,passage,scope):
        key=(node,passage['source_id'])
        if key in self.provenance: return
        self.provenance.add(key)
        self.edge(node,'DOCUMENTED_BY',self.source(passage['source_id']),passage,scope,nature='provenance_index')

    def instance(self,record,passage,scope):
        node=self.nodes[record]
        if node['props']['entity_level']!='context_record':return record
        generic=self.node(node['kind'],node['name'],aliases=' '.join(node['aliases']))
        self.edge(record,'INSTANCE_OF',generic,passage,scope,nature='concept_alignment')
        self.documented(generic,passage,scope)
        return generic

    def declaration(self,token_a,rel,token_b,passage,scope,certainty,nature,applicability=''):
        if rel in {'REDUCES_EFFECTIVENESS_OF','LIMITS_DETECTION_OF'}:
            self.issues.append(dict(scope=scope,a=token_a,relation=rel,b=token_b,
                reason='旧关系不能无损映射到已确认23类关系，保留旧声明归档，不冒充因果关系'))
            return
        if rel=='PROMPTS':token_a,token_b=token_b,token_a;rel='ADDRESSES'
        rel=RELMAP.get(rel,rel)
        a=self.token(token_a,scope if scope.startswith('case:') else '')
        b=self.token(token_b,scope if scope.startswith('case:') else '')
        if rel in CAUSAL and self.nodes[b]['kind']=='Factor':
            rel='ASSOCIATED_WITH';nature='migration_association_not_causation'
        if rel=='INDICATES' and self.nodes[b]['kind']!='Fault':
            rel='ASSOCIATED_WITH';nature='migration_association_not_fault_diagnosis'
        if rel=='PRECEDES' and not scope.startswith('case:'):
            self.issues.append(dict(scope=scope,reason='不对通用概念添加时间先后'));return
        self.edge(a,rel,b,passage,scope,certainty,nature,applicability=applicability)
        self.explicit_facts+=1
        for ident in (a,b):
            self.documented(ident,passage,scope)
            if scope.startswith('case:'):
                generic=self.instance(ident,passage,scope)
                case=self.case_equipment[scope]['case']
                self.edge(case,'INVOLVES',ident,passage,scope,nature='case_index')
            if self.nodes[ident]['kind'] in {'Fault','Check','Action'}:
                equip=self.case_equipment.get(scope,{}).get('equipment')
                if equip: self.edge(ident,'APPLIES_TO',equip,passage,scope,nature='applicability_index',applicability=applicability)
        if scope.startswith('case:'):
            equip=self.case_equipment[scope]['equipment']
            for ident in (a,b):
                if self.nodes[ident]['kind']=='Fault':self.edge(ident,'OCCURS_ON',equip,passage,scope,nature='case_equipment_index')

    def legacy(self):
        cases=load_module('curated_cases').CASES+load_module('expanded_cases').EXPANDED_CASES
        # frozen SQLite retains the user's V4.3 readable asset names.
        for case_index,row in enumerate(cases,1):
            scope='case:'+row['id'];app='本报告案例，不外推为所有船舶已证实根因'
            page=self.r.locate(row['source'],row['summary_anchor'],row['summary_page'])
            cname=next((n['name'] for n in self.oldnodes.values() if n['kind']=='Case' and json.loads(n['props']).get('case_id')==row['id']),row['name'])
            cname=cname.removeprefix(row['vessel']).removeprefix('匿名').strip()
            case=self.node('Case',cname,scope=scope,case_id=scope,vessel_name=row['vessel'].removeprefix('匿名'),
                vessel_identity_status='source_case_only' if row.get('anonymous') else 'named_vessel',
                propulsion_architecture=row.get('system') or '来源未明确',applicability=app)
            equip_old=next((self.oldnodes[e['target']] for e in self.oldedges if e['relation']=='HAS_EQUIPMENT' and e['case_id']==row['id']),None)
            equip_name=equip_old['name'] if equip_old else row.get('equipment','柴油机')
            equip=self.node('Equipment',equip_name,scope,propulsion_architecture=row.get('system') or '来源未明确')
            self.case_equipment[scope]=dict(case=case,equipment=equip)
            self.nodes[case]['props']['case_code']=f'C{case_index:02d}'
            self.edge(case,'INVOLVES',equip,page,scope,nature='case_index');self.instance(equip,page,scope)
            self.documented(case,page,scope);self.documented(equip,page,scope)
            if not row.get('anonymous') and not row['vessel'].startswith('匿名'):
                vessel=self.node('Vessel',row['vessel'],vessel_type=row.get('vessel_type','来源未明确'),
                    propulsion_architecture=row.get('system') or '来源未明确')
                self.edge(vessel,'HAS_CASE',case,page,scope,nature='case_index');self.documented(vessel,page,scope)
            for e in self.oldedges:
                if e['case_id']!=row['id'] or e['relation']!='HAS_COMPONENT':continue
                old=self.oldnodes[e['target']]
                component=self.node('Component',old['name'],scope)
                self.edge(equip,'HAS_COMPONENT',component,page,scope,nature='asset_index')
                self.edge(case,'INVOLVES',component,page,scope,nature='case_index')
                self.instance(component,page,scope);self.documented(component,page,scope)
            for a,rel,b,p,anchor,certainty in row['facts']:
                passage=self.r.locate(row['source'],anchor,p)
                self.declaration(a,rel,b,passage,scope,certainty,'source_case_statement',app)
            for key in row.get('subsystems', ['electrical'] if '电力' in str(row.get('system')) else ['transmission']):
                system=self.node('System',SYS[key],system_level='functional_subsystem')
                self.edge(equip,'SERVES_SYSTEM',system,page,scope,nature='functional_classification')
                self.documented(system,page,scope)
        for profile in load_module('fault_profiles').PROFILES:
            scope='reference:'+profile['id'];app=profile['applicability']
            main=self.node('Fault',profile['name'],aliases=profile['aliases'],applicability=app)
            for a,rel,b,file,p,anchor,certainty in profile['facts']:
                passage=self.r.locate(file,anchor,p)
                self.documented(main,passage,scope)
                self.declaration(a,rel,b,passage,scope,'possible' if rel=='MAY_CONTRIBUTE_TO' else certainty,'source_guidance_statement',app)
                for token in (a,b):
                    ident=self.token(token)
                    if self.nodes[ident]['kind'] in {'Fault','Check','Action'}:
                        for key in profile['subsystems']:
                            system=self.node('System',SYS[key],system_level='functional_subsystem')
                            self.edge(ident,'APPLIES_TO',system,passage,scope,nature='functional_classification',applicability=app)
            # Profile memberships are retrieval tags in metadata, not invented IS_A links.
            self.nodes[main]['props']['reference_unit']=True
        for row in load_module('corpus_knowledge').ARTICLES:
            path=CORPUS/row['path'];scope='article:'+self.r.by_file[path.name]
            equip=self.node('Equipment','柴油机')
            self.case_equipment[scope]=dict(equipment=equip)
            for a,rel,b,quote in row['facts']:
                passage=self.r.locate(path.name,quote)
                self.declaration(a,rel,b,passage,scope,'possible' if rel=='MAY_CONTRIBUTE_TO' else 'secondary_stated','secondary_source_statement',row['scope'])

    def additions(self):
        for article in ARTICLES:
            scope='article:'+self.r.by_file[article['name']]
            equip=self.node('Equipment',article['equipment'],applicability=article['scope'])
            system=self.node('System',SYS[article['system']],system_level='functional_subsystem')
            self.case_equipment[scope]=dict(equipment=equip)
            for row in article['facts']:
                passage=self.r.locate(article['name'],row['quote'])
                self.documented(equip,passage,scope)
                self.edge(equip,'SERVES_SYSTEM',system,passage,scope,nature='functional_classification')
                self.declaration(row['a'],row['r'],row['b'],passage,scope,row['certainty'],row['nature'],article['scope'])
        for row in PDF_FACTS:
            passage=self.r.locate(row['file'],row['quote'],row['page'])
            scope='guidance:'+passage['source_id']
            equip=self.node('Equipment','交流发电机')
            self.case_equipment[scope]=dict(equipment=equip)
            self.declaration(row['a'],row['r'],row['b'],passage,scope,row['certainty'],row['nature'],row['scope'])
            self.documented(equip,passage,scope)
            system=self.node('System',SYS['electrical'],system_level='functional_subsystem')
            self.edge(equip,'SERVES_SYSTEM',system,passage,scope,nature='functional_classification')
        for state,name,unit,file,quote in PARAMETERS:
            passage=self.r.locate(file,quote);scope='article:'+passage['source_id']
            state_id=self.node('State',state);param=self.node('Parameter',name,unit=unit,definition=name)
            self.edge(state_id,'DESCRIBED_BY_PARAMETER',param,passage,scope,nature='explicit_parameter_description')
            self.documented(param,passage,scope)
        for row in self.r.parameters:
            name=row.get('full_name','')
            if row.get('category')=='time / labeling':continue
            sid=row['source_id'];raw=self.r.pages[(sid,'')][0];line=raw.splitlines()[row['line']-1]
            passage=self.r.locate('variable_dictionary.csv',line)
            translated=translate_parameter(name)
            param=self.node('Parameter',translated,aliases=name,unit=row.get('unit',''),symbol=row.get('symbol',''),
                definition=name,native_note=row.get('note',''),parameter_source='实验数据原生变量字典',
                measurement_form='raw_voltage' if row.get('unit')=='V' else 'native_value',
                not_diagnostic_threshold=True)
            equip=self.node('Equipment','试验柴油机',applicability='Marine Engine Fault Dataset试验台，不等同实船运行')
            self.edge(param,'CHARACTERIZES',equip,passage,'dataset:marine_engine',nature='native_variable_dictionary')
            self.documented(param,passage,'dataset:marine_engine');self.documented(equip,passage,'dataset:marine_engine')
        scenarios={'Air-cooler fouling':'增压空气冷却器污损','Air-filter clogging (compressor)':'压气机空气滤清器堵塞',
                   'Cooling-water pump cavitation':'冷却水泵汽蚀','Injection-valve nozzle clogging':'喷油器喷嘴堵塞',
                   'Turbine degradation':'增压器涡轮退化（柴油机试验）'}
        for row in self.r.records:
            native=row.get('scenario','')
            if not native:continue
            matches=[name for en,name in scenarios.items() if en.casefold() in native.casefold()]
            if not matches:
                self.issues.append(dict(scope='dataset',scenario=native,reason='标签需要进一步语义核对，未转图谱故障'));continue
            raw=self.r.pages[(row['source_id'],'')][0];line=raw.splitlines()[row['line']-1]
            passage=self.r.locate('dataset_index.csv',line)
            fault=self.node('Fault',matches[0],aliases=native)
            equipment=self.node('Equipment','试验柴油机',applicability='受控试验，不等同实船已发生事故')
            self.edge(fault,'APPLIES_TO',equipment,passage,'dataset:marine_engine',certainty='dataset_label',nature='native_dataset_label',
                applicability='Marine Engine Fault Dataset原始标签；不推导未在数据中证明的机理')
            self.documented(fault,passage,'dataset:marine_engine')

    def ontology_links(self):
        file='船机帮船舶动力设备日常维护要点与常见故障排除.md'
        passage=self.r.locate(file,'船舶动力系统作为船舶航行与电力供给的中枢单元')
        root=self.node('System','船舶动力系统',system_level='functional_root')
        self.documented(root,passage,'ontology:system_taxonomy')
        for name in SYS.values():
            child=self.node('System',name,system_level='functional_subsystem')
            self.edge(child,'IS_SUBSYSTEM_OF',root,passage,'ontology:system_taxonomy',nature='curator_functional_taxonomy',
                applicability='实验本体的功能分组，不作为来源报告的原始因果结论')
        groups=[('船机帮船用共轨柴油机排气阀常见故障与排除.md','共轨柴油机排气阀常见故障有','排气阀故障',
            ['排气阀无法开启','排气阀烧损','排气阀高温腐蚀','排气阀阀杆卡紧','排气阀阀杆断裂','气阀弹簧断裂','排气阀阀壳裂纹']),
          ('船机帮船舶柴油机废气涡轮增压器振动的主要原因有哪些.md','轴承长时间使用后产生磨损、变形、裂纹和烧伤时','增压器轴承损伤',
            ['增压器轴承磨损','增压器轴承变形','增压器轴承裂纹','增压器轴承烧伤']),
          ('船机帮船用齿轮箱故障分析与管理对策.md','齿轮断裂在斜齿轮和宽直齿齿轮上发生较多','齿轮断裂',
            ['齿轮突然断裂','齿轮疲劳断裂','齿轮径向劈裂'])]
        for file,quote,parent,children in groups:
            p=self.r.locate(file,quote);scope='ontology:fault_taxonomy:'+p['source_id']
            parent_id=self.node('Fault',parent);self.documented(parent_id,p,scope)
            for name in children:
                child=self.node('Fault',name)
                self.edge(child,'IS_A',parent_id,p,scope,nature='curator_concept_taxonomy',
                    applicability='依据该文故障枚举整理的概念包含关系，非事故根因关系')
        file='船机帮某型船主机遥控系统典型故障分析.md'
        for check,param,unit,quote in [
            ('用示波器测量遥控电源纹波','遥控直流电源纹波','V','测量空载电压，纹波在0.1 V以内'),
            ('测量转速传感器信号频率','转速传感器信号频率','Hz','用万用表测量转速传感器转速信号频率'),
            ('用示波器观察转速信号波形','转速信号波形','波形','通过示波表监测转速信号波形'),
            ('按电路规程监测电气比例阀驱动电流','电气比例阀驱动电流','原文电流接口单位','通过给EP阀线圈串联电流表监测各工况驱动电流信号'),
        ]:
            p=self.r.locate(file,quote);scope='article:'+p['source_id']
            c=self.node('Check',check);v=self.node('Parameter',param,unit=unit,definition=param)
            self.edge(c,'USES_PARAMETER',v,p,scope,nature='explicit_check_variable');self.documented(v,p,scope)

    def validate(self):
        errors=[]
        for edge in self.edges.values():
            a=self.nodes[edge['source']];b=self.nodes[edge['target']];rel=edge['relation']
            if a['kind'] not in ENDPOINTS[rel][0] or b['kind'] not in ENDPOINTS[rel][1]:errors.append(edge['id'])
            assertion=self.assertions[edge['props']['assertion_id']]
            if assertion['passage_id'] not in self.r.passages:errors.append(edge['id']+' missing passage')
            if rel=='PRECEDES' and not assertion['scope_id'].startswith('case:'):errors.append('temporal generic edge')
            if rel in CAUSAL:
                scopes=[n['props'].get('scope_id') for n in (a,b) if n['props']['entity_level']=='context_record']
                if len(set(scopes))>1:errors.append('cross-case causal edge')
            if rel in {'IS_A','INSTANCE_OF'}:
                if a['kind']!=b['kind'] or a['id']==b['id']:errors.append('bad alignment')
        # IS_A graph must be acyclic; source/annotation layers are not IS_A nodes.
        adjacency=collections.defaultdict(list)
        for e in self.edges.values():
            if e['relation']=='IS_A':adjacency[e['source']].append(e['target'])
        active=set();seen=set()
        def visit(n):
            if n in active: errors.append('IS_A cycle');return
            if n in seen:return
            active.add(n)
            for child in adjacency[n]:visit(child)
            active.remove(n);seen.add(n)
        for n in list(adjacency):visit(n)
        # Each business node must have a traceable source connection.
        documented={e['source'] for e in self.edges.values() if e['relation']=='DOCUMENTED_BY'}
        for n in self.nodes.values():
            if n['kind']!='Source' and n['id'] not in documented:errors.append('undocumented '+n['name'])
        if errors: raise ValueError(json.dumps(errors,ensure_ascii=False))
        concepts=collections.Counter(n['kind'] for n in self.nodes.values() if n['props']['entity_level']=='concept')
        counts=collections.Counter(n['kind'] for n in self.nodes.values())
        fault=concepts['Fault']
        ratios={kind:dict(count=concepts[kind],fault_concepts=fault,ratio=round(concepts[kind]/fault,3),
                planning_range=bounds,within_planning_range=bounds[0]<=concepts[kind]/fault<=bounds[1])
                for kind,bounds in {'State':[1.5,3],'Factor':[.5,1.5],'Check':[.8,1.5],'Action':[1,2]}.items()}
        return dict(graph_version=VERSION,nodes=len(self.nodes),edges=len(self.edges),node_types=dict(sorted(counts.items())),
            concept_counts=dict(sorted(concepts.items())),context_records=sum(n['props']['entity_level']=='context_record' for n in self.nodes.values()),
            business_nodes_excluding_sources=len(self.nodes)-counts['Source'],relations=dict(collections.Counter(e['relation'] for e in self.edges.values())),
            assertion_count=len(self.assertions),explicit_knowledge_statements=self.explicit_facts,
            causal_assertions=sum(e['relation'] in CAUSAL for e in self.edges.values()),
            corpus_new_articles=len(ARTICLES),source_registry=len(self.r.sources),passages=len(self.r.passages),
            source_reference_coverage=1.0,locator_coverage=1.0,structural_errors=errors,
            class_ratios_vs_fault_concepts=ratios,expert_reviewed_assertions=0,
            review_policy='仅为实验进行原文定位核验和声明整理；未经过船舶专业专家复核，不可直接用于实船操作',
            baseline=dict(version='4.3',nodes=491,edges=1200,source='history中的冻结SQLite、声明与名称映射；不运行旧版构建器'),
            growth=dict(nodes=round(len(self.nodes)/491,3),edges=round(len(self.edges)/1200,3)),
            excluded_legacy_statements=len(self.issues),schema_defined_business_relations=len(RELATIONS)-1,
            automatically_invented_causal_edges=0,candidate_zone=False,passage_assertion_neo4j_nodes=False)

    def export(self,report):
        # Same generic name, different incident: readable suffixes make this
        # visible without changing identity or contaminating the generic concept.
        for node in self.nodes.values():
            if node['props']['entity_level']=='context_record':
                scope=node['props']['scope_id'];case=self.case_equipment.get(scope,{}).get('case')
                if case:
                    code=self.nodes[case]['props']['case_code']
                    node['props']['display_name']=node['name']+'〔'+code+'〕'
                    node['props']['case_code']=code
        nodes=sorted(self.nodes.values(),key=lambda r:r['id']);edges=sorted(self.edges.values(),key=lambda r:r['id'])
        jsonl(OUT/'entities.jsonl',nodes);jsonl(OUT/'relationships.jsonl',edges)
        jsonl(OUT/'assertions.jsonl',sorted(self.assertions.values(),key=lambda r:r['id']))
        jsonl(OUT/'migration_exclusions.jsonl',self.issues)
        self.r.save()
        write_json(OUT/'build_report.json',report)
        snapshot=dict(database='shipfaultkg',nodes=[dict(id=n['id'],labels=[n['kind'],'ShipKG'],properties=dict(n['props'],
            id=n['id'],kind=n['kind'],name=n['name'],aliases=n['aliases'])) for n in nodes],
            edges=[dict(id=e['id'],source=e['source'],relation=e['relation'],target=e['target'],properties=e['props']) for e in edges])
        write_json(OUT/'neo4j_snapshot_v5.json',snapshot)
        db=OUT/'ship_fault_kg.sqlite'
        # Build to a staging file, then atomically replace only our own V5 output.
        stage=OUT/'ship_fault_kg.staging.sqlite';conn=sqlite3.connect(stage)
        conn.executescript('DROP TABLE IF EXISTS nodes; DROP TABLE IF EXISTS edges; DROP TABLE IF EXISTS assertions; DROP TABLE IF EXISTS sources; DROP TABLE IF EXISTS passages; DROP TABLE IF EXISTS dataset_records; DROP TABLE IF EXISTS parameter_dictionary; CREATE TABLE nodes(id TEXT PRIMARY KEY,kind TEXT,name TEXT,aliases TEXT,props TEXT); CREATE TABLE edges(id TEXT PRIMARY KEY,source TEXT,relation TEXT,target TEXT,assertion_id TEXT,props TEXT); CREATE TABLE assertions(id TEXT PRIMARY KEY,source_id TEXT,passage_id TEXT,scope_id TEXT,data TEXT); CREATE TABLE sources(id TEXT PRIMARY KEY,data TEXT); CREATE TABLE passages(id TEXT PRIMARY KEY,source_id TEXT,text TEXT,data TEXT); CREATE TABLE dataset_records(id TEXT PRIMARY KEY,data TEXT); CREATE TABLE parameter_dictionary(id TEXT PRIMARY KEY,data TEXT); CREATE INDEX node_kind ON nodes(kind); CREATE INDEX edge_source ON edges(source); CREATE INDEX edge_target ON edges(target); CREATE INDEX assertion_scope ON assertions(scope_id);')
        dump=lambda x:json.dumps(x,ensure_ascii=False)
        conn.executemany('INSERT INTO nodes VALUES (?,?,?,?,?)',[(n['id'],n['kind'],n['name'],dump(n['aliases']),dump(n['props'])) for n in nodes])
        conn.executemany('INSERT INTO edges VALUES (?,?,?,?,?,?)',[(e['id'],e['source'],e['relation'],e['target'],e['props']['assertion_id'],dump(e['props'])) for e in edges])
        conn.executemany('INSERT INTO assertions VALUES (?,?,?,?,?)',[(a['id'],a['source_id'],a['passage_id'],a['scope_id'],dump(a)) for a in self.assertions.values()])
        conn.executemany('INSERT INTO sources VALUES (?,?)',[(r['id'],dump(r)) for r in self.r.sources.values()])
        conn.executemany('INSERT INTO passages VALUES (?,?,?,?)',[(r['id'],r['source_id'],r['text'],dump(r)) for r in self.r.passages.values()])
        for table,rows in [('dataset_records',self.r.records),('parameter_dictionary',self.r.parameters)]:
            conn.executemany(f'INSERT INTO {table} VALUES (?,?)',[(r['record_id'],dump(r)) for r in rows])
        conn.commit();integrity=conn.execute('PRAGMA integrity_check').fetchone()[0];conn.close()
        if integrity!='ok':raise ValueError('SQLite integrity failed')
        stage.replace(db)
        with (OUT/'知识图谱_关系节点属性_V5.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.writer(f);writer.writerow(['起点类别','起点名称','中文关系','终点类别','终点名称','声明性质','适用范围','确定性','来源','原文页码','原文引用','关系ID','声明ID'])
            for edge in edges:
                a=self.nodes[edge['source']];b=self.nodes[edge['target']];p=edge['props']
                writer.writerow([KINDS[a['kind']],a['name'],p['name'],KINDS[b['kind']],b['name'],p['statement_nature'],p['applicability'],p['certainty'],p['source_file'],p['page'],p['quote'],edge['id'],p['assertion_id']])
        write_json(OUT/'schema.json',dict(version=VERSION,classes=KINDS,relations=RELATIONS,
            endpoints={k:[sorted(a),sorted(b)] for k,(a,b) in ENDPOINTS.items()}))
        try:
            shutil.copyfile(OUT/'知识图谱_关系节点属性_V5.csv',KG/'output/知识图谱_关系节点属性.csv')
        except PermissionError:
            print('Readable root CSV is open; the authoritative V5 CSV has still been refreshed.')

def translate_parameter(name):
    direct={'Engine Speed':'发动机转速','Compressor Filter Loss':'压气机空气滤器压差',
      'Turbine Back Pressure':'涡轮排气背压','Charge Air Press.':'增压空气压力','Water Brake Weight':'水力测功器载荷',
      'Fuel Flow':'燃油流量','Shaft Torque':'轴转矩','Shaft Power':'轴功率','Total Input Energy':'总输入能量率',
      'Total Indicated work':'总指示功','Total Effective Work':'总有效功率','Mechanical Loss':'机械损失功率',
      'Mechanical Efficiency':'机械效率','Indicated Efficiency':'指示效率','Effective Efficiency':'有效效率',
      'Other Loss':'其他损失功率','Engine room Temp.':'机舱温度','Fuel Temp.':'燃油温度',
      'LO Circulating Pump Press.':'主滑油循环泵压力原始电压信号','Fuel transfer pump Press.':'燃油输送泵压力原始电压信号',
      'Fresh Cooling Water Press.':'高温淡水泵压力原始电压信号','Sea Cooling Water Press.':'低温海水泵压力原始电压信号',
      'TCH LO pump Press.':'增压器滑油泵压力原始电压信号','Fuel Injector Cooling Oil Press.':'喷油器冷却油压力原始电压信号',
      'Engine Cooling water flow':'发动机冷却水流量','LO Cooling water flow':'滑油冷却水流量',
      'Charge Air IC Cooling water flow':'增压空气冷却器冷却水流量','TCH LO Cooling water flow':'增压器滑油冷却水流量',
      'Total Heat Loss in Heat Exchangers':'换热器总热损失功率','Exh.Gas Vol. Flow (From Engine Speed)':'由转速推算的排气标准体积流量',
      'Exh. Gas Mass Flow':'排气质量流量','Exh.Gas Total Power':'涡轮前排气能量率','TCH Power':'增压器功率','Exh.Gas Power':'涡轮后排气能量率',
      'Loss with cooling water':'发动机冷却水带走热功率','Loss with LO':'滑油带走热功率','Loss in Charge Air IC':'增压空气冷却器热损失功率','Loss with TCH LO':'增压器滑油带走热功率'}
    if name in direct:return direct[name]
    patterns=[(r'Max\. In-Cylinder Press\. No\.(\d)',r'\1缸最高缸压'),(r'Min\. In-Cylinder Press\. No\.(\d)',r'\1缸最低缸压'),
        (r'No\.(\d) Exh\.Gas Temp\.',r'\1缸排气温度'),(r'Indicated Work No\.(\d)',r'\1缸指示功'),(r'Effective Work No\.(\d)',r'\1缸有效功率')]
    for pat,replacement in patterns:
        if re.fullmatch(pat,name):return re.sub(pat,replacement,name)
    pieces={'Exh.Gas Temp. Turbine':'涡轮排气温度','Cooling Water Temp. Engine':'发动机冷却水温度',
        'LO Temp. Engine':'发动机滑油温度','LO Cooling Water Temp.':'滑油冷却水温度',
        'Charge Air IC Air Temp.':'增压空气冷却器空气温度','Charge Air IC Cooling Water Temp.':'增压空气冷却器冷却水温度',
        'LO Temp. TCH':'增压器滑油温度','Fuel Oil Temp. Flow meter':'燃油流量计处燃油温度'}
    for en,zh in sorted(pieces.items(),key=lambda p:-len(p[0])):
        if name.startswith(en):return (zh+name[len(en):]).replace(' Out','出口').replace(' In','进口').strip()
    raise ValueError('Parameter requires reviewed Chinese translation: '+name)

def main():
    registry=Registry().run();builder=Builder(registry)
    builder.legacy();builder.additions();builder.ontology_links()
    report=builder.validate();builder.export(report)
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
