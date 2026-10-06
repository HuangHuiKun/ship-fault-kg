"""Apply the approved V4 naming/ontology rules without changing stable IDs.

Raw source annotations intentionally retain their historic namespace; this
final build stage prevents renaming from conflating different ship instances.
"""
import json
from collections import Counter
from pathlib import Path
from schema import VERSION, KIND_ZH, RELATION_ZH, CAUSAL_RELS


def apply_redesign(builder):
    rules = json.loads(Path(__file__).with_name('naming_v4.json').read_text(encoding='utf-8'))['nodes']
    missing = set(builder.nodes) - set(rules)
    if missing:
        raise ValueError('New/unreviewed entities need naming rules: ' + ', '.join(sorted(missing)))
    datasets = {i: n for i, n in builder.nodes.items() if n['kind'] == 'Dataset'}
    source_map = {e['source']: e['target'] for e in builder.edges.values()
                  if e['source'] in datasets and e['relation'] == 'DOCUMENTED_BY'}
    if set(source_map) != set(datasets):
        raise ValueError('Dataset provenance is incomplete')
    moved = removed = 0
    for ident, n in list(builder.nodes.items()):
        r = rules[ident]
        p = n['props']
        old_kind, old_name = n['kind'], n['name']
        p.update(legacy_kind=old_kind, graph_version=VERSION)
        if old_name != r['name']:
            p.setdefault('original_name', old_name)
            p['previous_name'] = old_name
            n['aliases'] = ' '.join(dict.fromkeys([n['aliases'], old_name, r['oldName']])).strip()
        n.update(kind=r['kind'], name=r['name'])
        if r['delete']:
            continue
        p.update(display_name=n['name'], kind_zh=KIND_ZH[n['kind']])
        if old_kind in {'Vessel', 'VesselType'}:
            p['entity_level'] = '船型' if old_kind == 'VesselType' else '实船记录'
        if old_kind in {'System', 'Subsystem'}:
            p['system_level'] = '功能系统' if old_kind == 'Subsystem' else '动力架构'
        if old_kind in {'Fault', 'FaultType'} and n['kind'] == 'Fault':
            p['fault_level'] = '故障类别' if old_kind == 'FaultType' else '具体故障或事件'
            if old_kind == 'FaultType':
                p.update(semantic_class='reference_category', knowledge_layer='reference')
        if old_kind == 'Run':
            p['original_file_name'] = old_name
        if old_kind == 'Sensor':
            p['original_column_name'] = old_name
        if old_kind == 'Source':
            p['original_title'] = old_name
        if old_kind in {'Equipment', 'Component'}:
            scopes = sorted({e['case_id'] for e in builder.edges.values()
                             if ident in (e['source'], e['target']) and e['case_id']})
            p['case_ids'] = scopes
            if len(scopes) == 1:
                p['case_id'] = scopes[0]
    for ident, e in list(builder.edges.items()):
        p, original = e['props'], dict(e)
        label = p.get('name', RELATION_ZH[e['relation']])
        if e['source'] in datasets:
            ds = datasets[e['source']]
            if e['relation'] == 'DOCUMENTED_BY':
                del builder.edges[ident]
                removed += 1
                continue
            child = e['target']
            e.update(source=child, target=source_map[ds['id']], relation='DOCUMENTED_BY')
            p.update(original_dataset_id=ds['id'], original_dataset_name=ds['name'],
                     original_dataset_props=json.dumps(ds['props'], ensure_ascii=False),
                     legacy_relation=original['relation'], legacy_source=original['source'],
                     legacy_target=original['target'], data_origin=ds['props'].get('data_origin', ''))
            builder.nodes[child]['props'].setdefault('data_origin', ds['props'].get('data_origin', ''))
            builder.nodes[child]['props'].setdefault('source_id', e['target'])
            label = '来源于'
            moved += 1
        elif e['relation'] == 'BELONGS_TO_SUBSYSTEM':
            e['relation'], label = 'BELONGS_TO_SYSTEM', '归属系统'
        elif e['relation'] == 'IN_SUBSYSTEM':
            e['relation'], label = 'IN_SYSTEM', '涉及系统'
        elif e['relation'] == 'IN_SYSTEM':
            label = '采用系统架构'
        elif e['relation'] == 'INVOLVES':
            k = builder.nodes[e['target']]['kind']
            labels = {'Fault':'涉及故障', 'Cause':'涉及原因', 'Condition':'涉及工况与状态',
                      'Consequence':'涉及后果', 'Check':'涉及检查方法',
                      'Action':'涉及运维措施', 'Symptom':'涉及症状'}
            label = labels.get(k, '涉及')
        else:
            label = RELATION_ZH[e['relation']]
        if e['certainty'] in {'possible', 'probable'} and not label.startswith(('可能', '很可能')):
            label = ('可能' if e['certainty'] == 'possible' else '很可能') + label
        if e['relation'] != original['relation']:
            p.setdefault('legacy_relation', original['relation'])
        p.update(name=label, graph_version=VERSION, is_causal=e['relation'] in CAUSAL_RELS)
    for ident in datasets:
        del builder.nodes[ident]
    refinement = apply_refinement(builder)
    builder.redesign_report = {'version':VERSION,'dataset_nodes_removed':len(datasets),
                              'provenance_edges_rewired':moved,'entry_edges_removed':removed,
                              'refinement':refinement,
                              'fault_levels':dict(Counter(n['props']['fault_level'] for n in builder.nodes.values() if n['kind']=='Fault'))}
    if any(n['kind'] not in KIND_ZH for n in builder.nodes.values()):
        raise ValueError('Retired entity type still present')


def apply_refinement(builder):
    """Keep classification provenance as properties, never conflate vessels."""
    rules = json.loads(Path(__file__).with_name('refinement_v4_1.json').read_text(encoding='utf-8'))
    removed = rules['remove_vessel_types']
    for ident, name in removed.items():
        node = builder.nodes[ident]
        if node['kind'] != 'Vessel' or node['name'] != name or node['props'].get('entity_level') != '船型':
            raise ValueError('Vessel removal outside reviewed scope: ' + ident)
    dropped = []
    for ident, edge in list(builder.edges.items()):
        if edge['source'] not in removed and edge['target'] not in removed:
            continue
        if edge['relation'] != 'OF_VESSEL_TYPE' or edge['target'] not in removed:
            raise ValueError('Unexpected relation on removed vessel-type node: ' + ident)
        name = removed[edge['target']]
        vessel = builder.nodes[edge['source']]
        types = vessel['props'].setdefault('vessel_types', [])
        if name not in types:
            types.append(name)
        if len(types) == 1:
            vessel['props']['vessel_type'] = types[0]
        vessel['aliases'] = ' '.join(dict.fromkeys([vessel['aliases'], name])).strip()
        provenance = {'former_edge_id':ident, 'former_type_node_id':edge['target'],
                      'vessel_type':name, 'evidence_id':edge['evidence_id'],
                      'case_id':edge['case_id'], 'certainty':edge['certainty']}
        vessel['props'].setdefault('vessel_type_provenance', []).append(provenance)
        for node in builder.nodes.values():
            if node['kind']=='Case' and node['props'].get('case_id')==edge['case_id']:
                node['props']['vessel_type'] = name
                node['props'].setdefault('vessel_type_provenance', []).append(provenance)
        dropped.append(ident)
        del builder.edges[ident]
    for ident in removed:
        del builder.nodes[ident]
    for ident, (old_name, new_name) in rules['equipment_names'].items():
        node = builder.nodes[ident]
        if node['kind']!='Equipment' or node['name']!=old_name:
            raise ValueError('Equipment rename outside reviewed scope: ' + ident)
        node['aliases'] = ' '.join(dict.fromkeys([node['aliases'], old_name])).strip()
        node['name'] = new_name
        node['props'].update(display_name=new_name, previous_display_name=old_name,
                             name_revision='4.1', naming_basis='保留原资料范围，使用设备或装置名；不虚构新物理部件')
        if old_name.endswith('系统'):
            node['props']['equipment_scope']='设备装置集合（非功能系统分类）'
    return {'vessel_type_nodes_removed':len(removed), 'classification_edges_to_properties':len(dropped),
            'removed_vessel_names':list(removed.values()), 'removed_edge_ids':dropped,
            'equipment_names_updated':len(rules['equipment_names']), 'observations_merged':False}
