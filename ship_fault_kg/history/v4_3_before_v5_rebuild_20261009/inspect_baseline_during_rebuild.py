import sqlite3, json
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'output' / 'ship_fault_kg.sqlite'
c = sqlite3.connect(f'file:{path.as_posix()}?mode=ro', uri=True)
c.row_factory = sqlite3.Row
for row in c.execute("SELECT name,sql FROM sqlite_master WHERE type='table'"):
    print(row['name'], row['sql'])
for table in ('nodes','edges','evidence','passages'):
    print(table, json.dumps([dict(r) for r in c.execute(f'SELECT * FROM {table} LIMIT 2')], ensure_ascii=False))
for kind in ('System','Vessel','Sensor','Source','Cause'):
    print(kind, json.dumps([dict(r) for r in c.execute('SELECT * FROM nodes WHERE kind=?',(kind,))], ensure_ascii=False))
