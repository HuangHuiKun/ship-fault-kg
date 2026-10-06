"""Portable GraphML with explicit node and edge captions; standard library."""
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from retrieve import read_store
from schema import RELATION_ZH


def main():
    store = read_store()
    namespace = 'http://graphml.graphdrawing.org/xmlns'
    ET.register_namespace('', namespace)
    def tag(name):
        return '{' + namespace + '}' + name
    root = ET.Element(tag('graphml'))
    keys = {'name', 'kind', 'aliases', 'display_name', 'relation', 'case_id', 'certainty',
            'source_file', 'page', 'source_url', 'evidence_id', 'quote', 'props_json'}
    for key in sorted(keys):
        ET.SubElement(root, tag('key'), {'id': key, 'for': 'all', 'attr.name': key, 'attr.type': 'string'})
    graph = ET.SubElement(root, tag('graph'), {'id': 'ShipFaultKG_V2', 'edgedefault': 'directed'})
    for n in store['nodes'].values():
        element = ET.SubElement(graph, tag('node'), {'id': n['id']})
        values = {k: n[k] for k in ('name', 'kind', 'aliases')}
        values.update(display_name=json.loads(n['props'])['display_name'], props_json=n['props'])
        for k, v in values.items():
            ET.SubElement(element, tag('data'), {'key': k}).text = str(v)
    for e in store['edges'].values():
        element = ET.SubElement(graph, tag('edge'), {'id': e['id'], 'source': e['source'], 'target': e['target']})
        ev = store['evidence'][e['evidence_id']]
        values = {k: e[k] for k in ('relation', 'case_id', 'certainty', 'evidence_id')}
        values.update({k: ev[k] for k in ('source_file', 'page', 'source_url', 'quote')})
        values.update(name=RELATION_ZH[e['relation']], props_json=e['props'])
        for k, v in values.items():
            ET.SubElement(element, tag('data'), {'key': k}).text = str(v)
    target = Path(__file__).resolve().parent / 'output' / 'ship_fault_kg.graphml'
    ET.ElementTree(root).write(target, encoding='utf-8', xml_declaration=True)
    print(f'{len(store["nodes"])} nodes, {len(store["edges"])} edges -> {target}')


if __name__ == '__main__':
    main()
