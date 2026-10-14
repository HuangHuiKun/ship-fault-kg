"""Default V6 local builder; does not mutate Neo4j."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from ship_fault_kg.v6_assistant.pipeline import main
if __name__=='__main__':
    sys.argv.insert(1,'build')
    main()
