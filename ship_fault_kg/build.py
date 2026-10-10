"""Default local builder now points to V5; never mutates Neo4j."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from ship_fault_kg.v5.build import main
if __name__=='__main__':main()
