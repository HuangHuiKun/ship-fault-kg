"""Version-explicit V6 commands; passwords are requested interactively."""
import importlib
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
COMMANDS = {'build': 'pipeline', 'verify': 'verify', 'retrieve': 'retrieve',
            'neo4j': 'neo4j', 'report': 'release'}
if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
    raise SystemExit('Usage: python manage_v6.py {build|verify|retrieve|neo4j|report} [arguments]')
command = sys.argv.pop(1)
if command == 'build':
    sys.argv.insert(1, 'build')
importlib.import_module('ship_fault_kg.v6_assistant.' + COMMANDS[command]).main()
