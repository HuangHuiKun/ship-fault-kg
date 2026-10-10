"""Reviewed V4.2 -> V4.3 delta sync, not an arbitrary-database importer."""
import sys
from pathlib import Path
from sync_neo4j_v4 import main

if __name__=='__main__':
    if '--baseline-backup' not in sys.argv:
        sys.argv.extend(['--baseline-backup',str(Path(__file__).resolve().parent/'history/v4_2_before_data_revision_20261008')])
    sys.argv.append('--data-revision')
    main()
