"""Compatibility entry for guarded V5 deployment, with hidden password entry."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from ship_fault_kg.v5.neo4j import main
if __name__=='__main__':
    if len(sys.argv)==1:sys.argv.append('apply')
    main()
