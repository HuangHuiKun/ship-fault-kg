"""Auditable inventories without making CSV part of the import workflow."""
import json
from pathlib import Path
from retrieve import read_store
from schema import KIND_ZH, VERSION


def main():
    output = Path(__file__).resolve().parent / 'output'
    store = read_store()
    (output / 'graph_inventory_v2.json').write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = [f'# V{VERSION}实体实例完整清单', '', '由当前SQLite生成；关联属性和全部关系、证据见graph_inventory_v3.json。', '']
    for kind, zh in KIND_ZH.items():
        rows = sorted([n for n in store['nodes'].values() if n['kind']==kind], key=lambda n:n['name'])
        lines += [f'## {zh}（{kind}）：{len(rows)}个', '', '| 名称 | 稳定ID | 别名 | 属性 |', '| --- | --- | --- | --- |']
        for n in rows:
            values = [n['name'], n['id'], n['aliases'], n['props']]
            lines.append('| ' + ' | '.join(v.replace('|',' / ').replace('\n',' ') for v in values) + ' |')
        lines.append('')
    (output / 'entity_inventory_v2.md').write_text('\n'.join(lines), encoding='utf-8')
    (output / 'entity_inventory_v3.md').write_text('\n'.join(lines), encoding='utf-8')
    (output / 'graph_inventory_v3.json').write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Inventory: {len(store['nodes'])} nodes, {len(store['edges'])} edges")


if __name__ == '__main__':
    main()
