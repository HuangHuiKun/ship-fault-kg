"""V6 lexical evidence retrieval. Old 38/24 gold queries are historical only."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from ship_fault_kg.v6_assistant.retrieve import main,retrieve
if __name__=='__main__':main()
