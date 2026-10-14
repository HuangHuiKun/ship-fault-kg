"""Generate factual release documentation and inventory from the built artifacts."""
import collections, hashlib, json, shutil
from pathlib import Path
from .preprocess import KG,OUT,write_json
from .schema import KINDS,RELATIONS
from .neo4j import BACKUP,signature

ROLES={
 'Vessel':'8条可以从资料识别船名的真实船舶；未具名的事故不捏造船名。船型、动力架构作为属性。',
 'System':'1个动力系统根节点、5个功能子系统；动力架构不再混作系统类别。',
 'Equipment':'设备的通用概念及案例内实例；名称不以船名开头，不以“系统”作为设备泛称。',
 'Component':'零部件通用概念与案例内实例，通过包含关系和检查、维护关系连接。',
 'Fault':'通用故障概念与案例内故障记录统一标签，用entity_level与INSTANCE_OF区分。',
 'State':'物理状态、运行异常、症状及后果；不把所有状态都强行归为故障根因。',
 'Factor':'材料、设计、制造、安装、维护、管理等因素；风险因素不等于已证实根因。',
 'Parameter':'参数和派生特征，含原生单位；原始电压不能未经标定转成工程压力。',
 'Check':'检查方法；关注查什么、使用什么参数，不能与维修动作混为一类。',
 'Action':'维护、处置、预防措施；作为参考主题，不作为自动下发的操作指令。',
 'Case':'19个原有正式事故案例；不把中文文章或试验工况冒充新增真实事故。',
 'Source':'46份实际参与建图的资料或文章。全量注册资料不等于图中来源节点。',
}

def rows(name):
    return [json.loads(line) for line in (OUT/name).read_text(encoding='utf-8').splitlines() if line.strip()]

def main():
    report=json.loads((OUT/'build_report.json').read_text(encoding='utf-8'))
    verify=json.loads((OUT/'verification_report.json').read_text(encoding='utf-8'))
    nodes=rows('entities.jsonl');edges=rows('relationships.jsonl');sources={s['id']:s for s in rows('sources.jsonl')}
    used={e['props']['source_id'] for e in edges}
    srcs=sorted([sources[sid] for sid in used],key=lambda s:(s['source_tier'],s['title']))
    classes='\n'.join(f"| {KINDS[k]}（{k}） | {report['node_types'][k]} | {report['concept_counts'].get(k,'—')} | {ROLES[k]} |" for k in KINDS)
    relations='\n'.join(f"| {r} | {zh} | {report['relations'].get(r,0)} |" for r,zh in RELATIONS.items())
    ratio='\n'.join(f"| {KINDS[k]} | {v['count']} | {v['ratio']} | {v['planning_range'][0]}～{v['planning_range'][1]} | {'符合' if v['within_planning_range'] else '不符合'} |" for k,v in report['class_ratios_vs_fault_concepts'].items())
    source_lines='\n'.join(f"| {i} | {s['title'].replace('|','/')} | {s['source_tier']} | {'；'.join(s['paths'])} | {s['url'] or '清单未提供直达链接'} |" for i,s in enumerate(srcs,1))
    livefile=OUT/'neo4j_verify_result.json'
    live=json.loads(livefile.read_text(encoding='utf-8')) if livefile.exists() else {}
    importfile=OUT/'neo4j_import_result.json'
    imported=json.loads(importfile.read_text(encoding='utf-8')) if importfile.exists() else {}
    status='已实际同步并核验一致' if live.get('exact_property_match') and imported.get('exact_property_match') else '请查阅数据库导入及核验回执；不能仅凭本地构建声称建库成功'
    smoke_total=len(verify['smoke_tests'])
    text=f'''# V5 船舶故障实验知识图谱：构建、结果与回滚说明

构建日期：2026-10-09。数据库：本机 `shipfaultkg`。建库状态：**{status}**。

## 1. 本次交付是什么

这是一套可替换的实验知识图谱与可复现构建程序，为“上游初步诊断文本 → 检索故障机理、检查和运维知识 → 有证据的诊断报告增强”提供基础。不是训练完成的大模型，也不是经过船级社认证的实船诊断系统。

本次不修改原始资料包，不训练模型，不提交或推送Git。仅有一个正式实验知识区；不生成未审核候选知识区。声明状态为 `accepted_for_experiment`，审核方式明确为助手原文核对或迁移规则，**不冒称人工专家审核**。

## 2. 相较旧版究竟增加了什么

| 项目 | 旧 V4.3 | 新 V5 |
| --- | ---: | ---: |
| 节点 | 491 | {report['nodes']} |
| 关系（含索引与溯源） | 1200 | {report['edges']} |
| 实体类别 | 15 | 12 |
| 实际关系类型 | 28 | 24：23种业务关系＋溯源关系 |
| 原有正式案例 | 19 | 19 |
| 实际使用来源节点 | 33 | {report['node_types']['Source']} |
| 四类因果关系声明 | 149 | {report['causal_assertions']} |
| 中文文章建图试点 | 4篇 | 原4篇＋新增14篇，共18篇 |
| 可定位文本片段 | 4406 | {report['passages']} |

节点约为原来的 {report['growth']['nodes']} 倍、关系约为 {report['growth']['edges']} 倍。增长主要来自状态、影响因素、检查、维护、部件及明确关系，不是虚构更多船舶或把每个文本片段放进Neo4j凑数。

**统计口径：**{report['edges']}条关系中，1381条为`DOCUMENTED_BY`溯源边，1962条为其他关系；其中有{report['explicit_knowledge_statements']}条显式知识声明、{report['causal_assertions']}条因果类声明。唯一节点三元组为{verify['unique_business_triples']}条，同作用域三元组为{verify['unique_scoped_triples']}条。不同证据可以支持同一三元组；不能把关系总数称为不同故障机理的总数。

## 3. 各类实体与比例

| 类别 | 全部节点 | 通用概念 | 作用与边界 |
| --- | ---: | ---: | --- |
{classes}

配比以 **168个通用Fault概念**为分母，而不是把48条事故内故障记录也加进分母。197个情境记录通过 `INSTANCE_OF` 对齐通用概念。同名事件在不同案例中保持不同ID，显示名称附带 `〔C01〕` 等案例码。

| 配套类别 | 通用概念数 | 相对Fault比例 | 确认的规划范围 | 当前检查 |
| --- | ---: | ---: | --- | --- |
{ratio}

比例只是覆盖规划，不是科学有效性的证明。今后必须以原文支持为前提扩充，不能通过复制节点或拆碎句子填数量。

五个功能子系统：燃油与进排气、润滑与轴承、冷却与海水、传动与推进、电力与控制；再加一个“船舶动力系统”上级根节点。热—机—电跨域机理目前仍不均衡，尤其电网耦合振荡的多环节实证和轴带机组工况需要继续补充。

## 4. 可复现构建过程：每一步做什么、为什么

### 步骤一：先冻结旧版，确保能退回

`history/v4_3_before_v5_rebuild_20261009/` 保存原根目录文件、旧output、资料清单及旧SQLite；`neo4j_live_before_v5.json` 保存建库前真实数据库的491个节点、1200条关系、属性、标签及约束信息。备份发生在数据库更新之前，不是事后用旧脚本猜测重建。资料包原件没有改动，因此未重复复制体积较大的原始数据集。

### 步骤二：建立来源注册表

`v5/preprocess.py`读取报告、论文、中文Markdown全文和保留试验数据的索引/变量字典。按文件字节SHA256建立来源版本和稳定ID，记录原路径、题名、网址、授权、来源性质。相同文件内容合并为同一来源。

产物：`sources.jsonl`、`preprocess_cache.json`。目前注册1308份文本/元数据来源，含1275篇中文语料；只有46份实际支持了当前图谱边并成为Neo4j Source节点。**全部读入不等于全部接受为知识。**

### 步骤三：无损预处理与定位

PDF按物理页抽取；中文文章读完整正文，规范化空白后以1200字符非重叠分块，另为选中声明保存精确引用片段。记录物理页码、原始/规范化字符位置、行号及文件指纹。PDF页码指文件的实际第几页，不保证等于报告页脚编号。

产物：`preprocessed_pages.jsonl`、`passages.jsonl`、`preprocessing_report.json`。全文缓存只在原始文件与资料清单指纹都没变时复用。AGN076第9页未抽出文字，不从该页构造知识；无文字页需另行人工判断空白或OCR需求。关键厂家页面已渲染核对，见`qa/`。

试验数据保留16条原生文件索引和74条变量字典行；排除时间/标签字段后有70个数值变量参与Parameter建模。**本次没有读取全部时序波形来自动发现因果关系**，也没有把试验运行做成Neo4j Run节点。

### 步骤四：整理可核对的知识声明

冻结的19起事故、12个参考故障单元及原4篇中文试点声明作为旧版知识输入，读取来源锚点并重新校验。新声明集中在 `v5/curation.py`，补充14篇中文文章及STAMFORD等厂家资料的检查、维护和机理。**沿用的是冻结的旧知识声明与名称映射，不运行旧版构建器；并非完全摆脱旧资料输入依赖。**

声明至少包含：主语类别与名称、关系、宾语类别与名称、出处、原文引用、页码/位置、作用域、确定性、声明性质、适用边界。例：

```python
fact(r, 'S|缸套润滑油膜减薄或破坏', 'CAUSES',
     'S|缸套与活塞环干摩擦', '原文中已定位的整段机理描述')
```

这里`S`表示State。构建器先定位引用，找不到则报错；再产生两个稳定实体ID、一条声明Assertion及一条关系。更长链按原文明确步骤保存相邻关系，**不会额外推断“最早因素必然导致最后故障”**。因果、风险、提示、相关、时间先后分开，不把同时发生视为因果。

不是自动“抽完1275篇就全部入库”。目前正式使用18篇，其他全文只供后续受控扩充；未选内容不是已审核知识，也没有作为候选知识节点发布。

### 步骤五：概念规范化、情境隔离与结构建模

`v5/schema.py`规定12种类别、23种业务关系、中文关系名和端点约束。旧Cause/Condition/Symptom/Consequence按含义整理为State或Factor；故障实例与通用Fault用INSTANCE_OF连接。设备、部件按案例分开，未知船舶仅留案例属性，动力架构留属性。15条无法无损映射的旧声明写入`migration_exclusions.jsonl`，不强行包装为新因果边。

`scope_id`区分`case:`事故、`article:`文章、`reference:`参考单元、`guidance:`厂家指导及`dataset:`变量定义。来源不同、构型不同的链不得直接拼成“已证实根因”。`IS_A`必须同类别、无环；运维措施与检查方法分开。旧材料中执行/建议状态不清的Action保留`reported_or_recommended_unspecified`，不能说它已在当前船舶执行。

### 步骤六：SQLite主数据、JSONL与快照

`v5/build.py`生成SQLite七张表：nodes、edges、assertions、sources、passages、dataset_records、parameter_dictionary；先写暂存数据库，通过完整性检查后替换本版主数据。SQLite是轻量的本地结构化数据文件，不是Neo4j的备份引擎。

`entities.jsonl`和`relationships.jsonl`供检查与交换；`assertions.jsonl`保存每条边的完整证据；`neo4j_snapshot_v5.json`保存拟导入的节点标签、所有属性和边。**Passage与Assertion只保留在本地，不作为Neo4j节点。**易读CSV由同一批数据自动生成，是查看清单，不是建库必经步骤。

### 步骤七：独立校验再建库

`v5/verify.py`检查SQLite、类别与端点、引用与来源、原文件指纹、中文边名、作用域及比例，并跑12个故障短词和1个完整诊断文本开发样例。当前结果：`passed={verify['passed']}`，{verify['raw_sources_verified']}份使用来源的原始文件指纹通过核对，{verify['smoke_passed']}/{smoke_total}样例找到目标故障。排名细节以verification_report.json为准。**这是开发冒烟测试，不能报告为独立Recall@K、Precision@K、MRR实验。**自动验证可确认定位、结构和一致性，不能自动证明所有声明语义正确。

`v5/neo4j.py`通过本机HTTP Query API直接导入：检查实时快照未被其他操作改变 → 一次事务替换ShipKG范围 → 完整属性指纹比较。非本项目相邻节点会使非DETACH删除失败并回滚，不默默删除其他数据。不关闭认证，不保存密码，不必SQLite→CSV→Neo4j绕行。

本次实际更新现有`shipfaultkg`，不是声称新建了另一数据库。连接HTTP7474、Bolt7687未修改。以后更新保存每次部署前快照，并以最后一次部署快照检查并发修改；未通过当前快照独立校验则拒绝导入。

## 5. 当前关系字典（可读边名）

| 关系编码 | 中文名称 | 当前数量 |
| --- | --- | ---: |
{relations}

`CAUSES`是来源所述导致；`CONTRIBUTES_TO`是促成；`INCREASES_RISK_OF`是风险增加；`WORSENS`是加剧。四者不是同等强度。`certainty`进一步保留possible/probable等限定。DOCUMENTED_BY是出处索引，ASSERTION仍在本地。

措施状态：`recommended_reference`为来源建议；`reported_in_source_context`为来源情境内报告的动作，不代表当前待诊断船舶已执行；`analyst_suggested_for_review`为整理者衍生建议，须审核；`reported_or_recommended_unspecified`为旧材料无法确定执行/建议状态；索引边等不表达执行情况，标`not_applicable`。这些状态也写入检索证据包，不混称“全部已执行”或“全部厂家建议”。

节点常用属性：id、kind、name、aliases、display_name、entity_level、scope_id、graph_version、knowledge_zone。部分类别另含船型/架构、单位/测量形式、案例码、出处URL/指纹/授权等。

关系常用属性：id、name、assertion_id、scope_id、certainty、statement_nature、source_id、source_file、source_url、source_sha256、passage_id、page、quote、applicability、action_status、review_method、expert_review。完整属性名单见`entity_inventory_v5.md`。SQLite主键、脚本模式约束与Neo4j唯一性约束是不同层次；真实数据库约束以`neo4j_verify_result.json`为准，不能将脚本检查冒称数据库强制约束。

## 6. 查询与检索怎样用

见同目录`queries_v5.cypher`。分层浏览建议先看5个子系统，再按故障看局部因果与溯源；1356个节点一次铺满并不利于阅读。上下文节点显示案例码，边属性name保存中文名。可选`shipkg_v5.grass`沿用旧类型颜色映射，为新增类型继承接近的旧类别色；不自动修改Browser当前自定义样式。需要时手动导入，并将ShipKG的标签优先级放到业务标签之后。

本地检索示例：

```powershell
cd D:\\RAGQnASystem\\RAGQnASystem-main
python ship_fault_kg/manage_v5.py retrieve "主机可能拉缸，排气温度升高，冷却水出口温度偏高"
```

流程为Fault概念别名匹配＋字/二元组词法相似度 → Top-K故障 → INSTANCE_OF关联事件 → 每个scope内最多3步关系扩展 → 带出处、引用、确定性、适用范围的证据JSON。`retrieval_example.json`是真实运行结果。

当前不是语义向量/混合重排成熟检索，不调用LLM。仅作用于设备的通用维护节点未必进入故障直接扩展结果；后续应在有构型约束的前提下补充设备/部件检查、维护的检索路径，再与师兄输出联调。不能把此轮构建说成完整RAG质量评估完成。

## 7. 构建、更新、回滚命令

以下在项目根目录、安装pypdf的Python环境中运行；本机本次实际使用Python 3.12.14和pypdf 6.10.0。核心依赖锁定在`v5/requirements.txt`，缺失时执行`python -m pip install -r ship_fault_kg/v5/requirements.txt`。检查环境可先执行`python -c "import pypdf, sqlite3"`。可选PDF页渲染核对使用pypdfium2 5.13.0；Excel清单是本次附带快照，不是核心Python构建的依赖。

```powershell
python ship_fault_kg/manage_v5.py build
python ship_fault_kg/manage_v5.py verify
python ship_fault_kg/manage_v5.py neo4j apply
python ship_fault_kg/manage_v5.py neo4j verify
python ship_fault_kg/manage_v5.py report
```

Neo4j相关命令在终端隐藏输入密码，先启动Desktop实例。`apply`只认备份/上次部署对应的实时图谱，遇手工改库不覆盖，应先核对差异。

恢复旧数据库（会替换当前ShipKG图谱，并先备份当前实时内容）：

```powershell
python ship_fault_kg/manage_v5.py neo4j restore
```

恢复默认指向`history/v4_3_before_v5_rebuild_20261009/neo4j_live_before_v5.json`。该命令恢复节点与关系及属性，不删除新建约束或自动还原Browser本地样式；本次未修改原Neo4j约束/浏览器样式。要恢复旧本地工作流，可直接使用history中冻结的SQLite做只读检索；若恢复旧构建脚本，应先另备份当前代码，再将备份原根目录文件恢复到原位置、将备份output恢复到原output位置。**不要在history里运行依赖相对位置的旧构建器。**完整备份文件指纹见`backup_manifest.json`。

## 8. 方法依据与差异

参考[Stanford Ontology Development 101](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf)的用途驱动、概念/属性/实例分离和迭代检查思路；参考[W3C PROV概览](https://www.w3.org/TR/prov-overview/)的出处、活动与版本追踪思路。本项目借鉴原则，**未实现完整OWL推理或宣称PROV标准合规**。

与全自动LLM抽取相比，声明驱动的优点是可解释、可复核、来源定位明确；缺点是扩充较慢、人工设计依赖强，专家未复核时仍可能有漏项和概念不一致。与纯文本RAG相比，图谱能显式区分风险/因果/症状并控制路径范围；缺点是结构化覆盖有限，未入图的内容可能检索不到。与成熟工业本体相比，目前语义约束和实船验证尚不足，不应越权作为生产诊断知识库。

## 9. 仍待完善

1. 专家复核为0；原文存在不代表归纳的每个因果方向都已由专家认可，特别是二次维修文章。
2. 18/1275中文文章完成正式整理；其他文章只能用于后续有出处、有审核记录的扩充。
3. 概念粒度与同义词仍有差异；通用概念和事件记录分开可能显示同名，但ID和案例码不同，并非可无条件合并的重复。
4. 因果“链”应每一跳检查scope、certainty与来源。共享概念不意味着跨资料整条链已被证实。
5. Action有部分建议/已执行状态未能细分；维持unspecified而不作虚假执行陈述。侵入式维修、阈值及运行策略必须服从厂家和专家。
6. 旧38/24题与旧ID不能直接使用；需重新编制独立查询、相关实体/边/路径金标准，按来源隔离开发和测试再计算检索指标。
7. 正式LLM增强、事实忠实性/引用正确率/运维适用性评价和反馈闭环尚待下一阶段；本次只交付基础图谱和检索探针。

## 10. 实际使用来源清单

题名来自现有资料清单或文章文件名；有些清单题名是资料概括名称，不冒称都已核对为出版物封面全名。引用到报告原页和本地文件，可进一步补全作者、年份、正式题名、DOI与授权。

| 序号 | 资料题名 | 来源性质 | 原始文件路径（相对资料包） | 原始/分发网址 |
| --- | --- | --- | --- | --- |
{source_lines}

第三方原件保留其原有著作权与许可。本实验文档不构成再分发许可或安全操作保证；见项目DISCLAIMER.md。
'''
    (OUT/'新版知识图谱构建与建库报告_V5.md').write_text(text,encoding='utf-8')
    prop_counts=collections.defaultdict(collections.Counter)
    for n in nodes:
        prop_counts[n['kind']].update(set(n['props'])|{'id','kind','name','aliases'})
    inventory='# V5 实体、关系和属性清单\n\n所有行来自本次实际构建，不是设计目标。详细节点见entities.jsonl，逐边见CSV。\n\n| 类别 | 全部节点 | 通用概念 | 作用 |\n| --- | ---: | ---: | --- |\n'+classes+'\n\n## 节点实际属性\n\n'
    for k,c in prop_counts.items():
        inventory+='### '+KINDS[k]+'\n\n'+', '.join(f'`{p}`（{v}节点）' for p,v in sorted(c.items()))+'\n\n'
    inventory+='## 关系实际属性\n\n'+', '.join('`'+p+'`' for p in sorted({p for e in edges for p in e['props']}))+'\n\n## 关系编码\n\n| 编码 | 中文名 | 数量 |\n| --- | --- | ---: |\n'+relations+'\n'
    (OUT/'entity_inventory_v5.md').write_text(inventory,encoding='utf-8')
    # Version marker is navigation metadata, never another graph source of truth.
    write_json(KG/'output/CURRENT_VERSION.json',dict(version='5.0',sqlite='v5/ship_fault_kg.sqlite',entrypoint='../manage_v5.py',
        report='v5/新版知识图谱构建与建库报告_V5.md',legacy_backup='history/v4_3_before_v5_rebuild_20261009'))
    shutil.copyfile(OUT/'知识图谱_关系节点属性_V5.csv',KG/'output/知识图谱_关系节点属性.csv')
    colors={'Vessel':'#ffb2d7','System':'#e7b04f','Case':'#7ad7d1','Equipment':'#59a9e7',
        'Component':'#abae8a','Fault':'#e5dfff','State':'#ffc736','Factor':'#b1de38',
        'Check':'#ffbc00','Action':'#b4dbff','Parameter':'#ffd8ff','Source':'#c1d1ff','ShipKG':'#ffd95a'}
    style='\n'.join('node.'+k+' { color: '+c+'; diameter: 25px; caption: "{display_name}"; }' for k,c in colors.items())
    style+='\nrelationship { color: #74889A; shaft-width: 2px; caption: "{name}"; }\n'
    (OUT/'shipkg_v5.grass').write_text(style,encoding='utf-8')
    # Inventory of the actual archive, excluding this generated inventory itself.
    items=[]
    for f in sorted(BACKUP.rglob('*')):
        if f.is_file() and f.name!='backup_manifest.json':
            items.append(dict(path=f.relative_to(BACKUP).as_posix(),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
    old=json.loads((BACKUP/'neo4j_live_before_v5.json').read_text(encoding='utf-8'))
    write_json(BACKUP/'backup_manifest.json',dict(files=items,neo4j_live_canonical_signature=signature(old),
        old_nodes=len(old['nodes']),old_edges=len(old['edges']),raw_data_policy='原始资料未改动；保存元数据与旧构建产物，未重复复制原始大数据集'))
    print(json.dumps(dict(report=str(OUT/'新版知识图谱构建与建库报告_V5.md'),inventory=str(OUT/'entity_inventory_v5.md'),archive_files=len(items)),ensure_ascii=False))

if __name__=='__main__':main()
