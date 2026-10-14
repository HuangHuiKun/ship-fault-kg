"""Rebuild in an isolated temporary directory to check the archive migration."""
import contextlib
import hashlib
import io
import json
import shutil
import tempfile
from pathlib import Path
from . import pipeline
from .core.neo4j import signature

def main():
    archive = pipeline.KG / 'history/organization_v6_20261013'
    current = pipeline.OUT
    expected = json.loads((current/'neo4j_snapshot.json').read_text(encoding='utf-8'))
    with tempfile.TemporaryDirectory(prefix='rebuild_check_', dir=archive) as scratch:
        temporary = Path(scratch).resolve()
        if not temporary.is_relative_to(archive.resolve()):
            raise RuntimeError('Unexpected temporary location')
        try:
            # Curated representative batches reference this immutable reading index.
            shutil.copy2(current/'source_complete_reading_queue.jsonl', temporary/'source_complete_reading_queue.jsonl')
            pipeline.OUT = temporary
            with contextlib.redirect_stdout(io.StringIO()):
                pipeline.assemble()
            rebuilt = json.loads((temporary/'neo4j_snapshot.json').read_text(encoding='utf-8'))
            report = json.loads((temporary/'build_report.json').read_text(encoding='utf-8'))
            exact = signature(expected) == signature(rebuilt)
            if not exact or report['sqlite_integrity'] != 'ok':
                raise RuntimeError('Migrated build differs from published graph')
        finally:
            pipeline.OUT = current
    manifest = dict(archive='history/organization_v6_20261013', files=[])
    for path in sorted(archive.rglob('*')):
        if path.is_file() and path.name != 'organization_manifest.json' and '__pycache__' not in path.parts:
            manifest['files'].append(dict(path=path.relative_to(archive).as_posix(),
                bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    pipeline.save(archive/'organization_manifest.json', manifest)
    result = dict(nodes=report['nodes'], edges=report['edges'],
        isolated_rebuild_matches_published_snapshot=exact,
        sqlite_integrity=report['sqlite_integrity'], snapshot_sha256=signature(rebuilt),
        archived_files=len(manifest['files']), neo4j_changed=False,
        removed_from_active_output=['v5','v6_expansion'],
        note='V5 baseline remains an archived read-only build dependency; expansion has zero valid statements.')
    pipeline.save(archive/'organization_verification.json', result)
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    main()
