"""Generate an exact, auditable V2->V3 diff and scoped Neo4j sensor cleanup."""
import json
from pathlib import Path
from retrieve import read_store, Retriever, make_prompt
from import_neo4j import literal
from fault_profiles import IMPORTANT_SENSORS

HERE=Path(__file__).resolve().parent
OUT=HERE/'output'
OLD=HERE/'history'/'v2_before_fault_focus_20261005'/'output'/'ship_fault_kg.sqlite'

def main():
    old,new=read_store(OLD),read_store()
    removed=set(old['nodes'])-set(new['nodes'])
    if len(removed)!=55 or any(old['nodes'][x]['kind']!='Sensor' for x in removed):
        raise ValueError('Unexpected deletion scope; refuse cleanup preparation')
    edges_removed=set(old['edges'])-set(new['edges'])
    if any(old['edges'][x]['source'] not in removed and old['edges'][x]['target'] not in removed for x in edges_removed):
        raise ValueError('Unexpected non-sensor relationship removal')
    sensors=sorted([n for n in new['nodes'].values() if n['kind']=='Sensor'],key=lambda n:n['name'])
    if {n['name'] for n in sensors}!=set(IMPORTANT_SENSORS):
        raise ValueError('Sensor selection mismatch')
    changes={'before':{'nodes':len(old['nodes']),'edges':len(old['edges']),'sensors':70},
             'after':{'nodes':len(new['nodes']),'edges':len(new['edges']),'sensors':len(sensors)},
             'added_nodes':len(set(new['nodes'])-set(old['nodes'])),
             'added_edges':len(set(new['edges'])-set(old['edges'])),
             'removed_nodes':[{'id':x,'name':old['nodes'][x]['name'],'kind':'Sensor'} for x in sorted(removed)],
             'removed_edges':sorted(edges_removed),
             'renamed_nodes':[{'id':x,'before':old['nodes'][x]['name'],'after':new['nodes'][x]['name']}
                              for x in old['nodes'].keys() & new['nodes'].keys() if old['nodes'][x]['name']!=new['nodes'][x]['name']],
             'backup':str(OLD.parent.parent),'raw_datasets_deleted':False}
    (OUT/'revision_changes_v3.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
    ids=literal(sorted(removed))
    # Historical migration helpers; retired after the user-requested scoped purge.
    (OUT/'neo4j_sensor_cleanup_v3.cypher').write_text('// Disabled: user selected recoverable archival. Use neo4j_sensor_archive_v3.cypher; no nodes or relationships are deleted.\n',encoding='utf-8')
    preview=f'MATCH (n:ShipKG:Sensor) WHERE n.id IN {ids} RETURN count(n) AS sensors_to_remove, collect(n.name) AS names;'
    (OUT/'neo4j_sensor_preview_v3.cypher').write_text(preview,encoding='utf-8')
    restore=f'MATCH (n:ArchivedShipKG:ArchivedSensor) WHERE n.id IN {ids} SET n:ShipKG:Sensor REMOVE n:ArchivedShipKG:ArchivedSensor REMOVE n.archived_reason RETURN count(n) AS restored;'
    archive=f'MATCH (n:ShipKG:Sensor) WHERE n.id IN {ids} SET n:ArchivedShipKG:ArchivedSensor, n.archived_reason="V3 core-sensor selection" REMOVE n:ShipKG:Sensor RETURN count(n) AS archived_sensors;'
    (OUT/'neo4j_sensor_archive_v3.cypher').write_text(archive,encoding='utf-8')
    (OUT/'neo4j_sensor_unarchive_v3.cypher').write_text(restore,encoding='utf-8')
    import html
    guide='<!doctype html><meta charset="utf-8"><h1>V3测点可恢复归档</h1><p>仅移出活动 ShipKG 图谱；保留节点属性、原始关系及原始数据文件。不执行永久删除。</p>'
    for title,text in [('预览55个目标',preview),('可恢复归档55个测点',archive),('归档恢复',restore)]:
        guide+=f'<h2>{title}</h2><button onclick="navigator.clipboard.writeText(this.nextElementSibling.textContent)">复制</button><pre>{html.escape(text)}</pre>'
    (OUT/'sensor_cleanup_guide_v3.html').write_text(guide,encoding='utf-8')
    if (OUT/'maintenance_20261005'/'purge_receipt.json').exists():
        notice='// Retired: the 55 archived sensors and 86 edges were deleted after external backup.\n// See ../README_CN.md and maintenance_20261005/deleted_sensors_backup.json.\n// Label-only unarchive cannot recreate deleted nodes. Explicit recovery: python ship_fault_kg/purge_archived_sensors.py --restore\n'
        for name in ['neo4j_sensor_cleanup_v3.cypher','neo4j_sensor_preview_v3.cypher',
                     'neo4j_sensor_archive_v3.cypher','neo4j_sensor_unarchive_v3.cypher']:
            (OUT/name).write_text(notice,encoding='utf-8')
        guide='<!doctype html><meta charset="utf-8"><h1>55个测点维护已完成</h1><p>55个非核心传感器及86条关联关系已从Neo4j删除，当前保留15个传感器。原始数据不变，完整恢复备份存于 maintenance_20261005/deleted_sensors_backup.json。旧的标签归档/恢复语句已停用，不能重建已删除节点。</p><p><a href="../README_CN.md">统一项目说明：查看当前建库、样式和恢复方法</a></p>'
        (OUT/'sensor_cleanup_guide_v3.html').write_text(guide,encoding='utf-8')
    retriever=Retriever()
    examples=[]
    for query in ['主机疑似拉缸，如何补充机理解释和检查建议？','烧瓦与轴承咬死可能是什么原因？',
                  '轴带发电机对中异常与振动损伤如何解释？','电机与发电机轴承电蚀如何溯源？',
                  '船舶电网耦合振荡如何补充来源和检查？']:
        result=retriever.search(query,top_facts=12)
        examples.append({'retrieval':result,'llm_prompt':make_prompt(result)})
    (OUT/'retrieval_examples_v3.json').write_text(json.dumps(examples,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in changes.items() if k not in {'removed_nodes','removed_edges','renamed_nodes'}},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
