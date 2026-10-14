"""Version-explicit entry point; also works when cwd is ship_fault_kg."""
import importlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
COMMANDS={'build':'build','verify':'verify','retrieve':'retrieve','neo4j':'neo4j','report':'release'}
if len(sys.argv)<2 or sys.argv[1] not in COMMANDS:
    raise SystemExit('Usage: python manage_v5.py {build|verify|retrieve|neo4j|report} [arguments]')
command=sys.argv.pop(1)
importlib.import_module('ship_fault_kg.v5.'+COMMANDS[command]).main()
