"""Auditable inventories without making CSV part of the import workflow."""
import json
from pathlib import Path
from retrieve import read_store
from schema import KIND_ZH, VERSION


def main():
    output = Path(__file__).resolve().parent / 'output'
    store = read_store()
    major = VERSION.split('.')[0]
    lines = [f'# V{VERSION}实体实例完整清单', '', f'由当前SQLite生成；关联属性和全部关系、证据见graph_inventory_v{major}.json。', '']
    for kind, zh in KIND_ZH.items():
        rows = sorted([n for n in store['nodes'].values() if n['kind']==kind], key=lambda n:n['name'])
        lines += [f'## {zh}（{kind}）：{len(rows)}个', '', '| 名称 | 稳定ID | 别名 | 属性 |', '| --- | --- | --- | --- |']
        for n in rows:
            values = [n['name'], n['id'], n['aliases'], n['props']]
            lines.append('| ' + ' | '.join(v.replace('|',' / ').replace('\n',' ') for v in values) + ' |')
        lines.append('')
    (output / f'entity_inventory_v{major}.md').write_text('\n'.join(lines), encoding='utf-8')
    (output / f'graph_inventory_v{major}.json').write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding='utf-8')
    from export_readable_csv import export_csv
    export_csv(output / 'ship_fault_kg.sqlite')
    print(f"Inventory: {len(store['nodes'])} nodes, {len(store['edges'])} edges")


if __name__ == '__main__':
    main()
