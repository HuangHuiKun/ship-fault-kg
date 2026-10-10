"""One-time recoverable relocation; never delete files or recurse history."""
import hashlib,json,shutil
from .preprocess import KG,write_json
from .neo4j import BACKUP

def main():
    target=BACKUP/'retired_active_entries'
    if (target/'move_manifest.json').exists():
        raise SystemExit('One-time archival already completed; current V5 entries will not be moved.')
    target.mkdir(parents=True,exist_ok=True)
    manifest=[]
    preserve={'manage_v5.py','README_CN.md','FILE_LAYOUT.md'}
    candidates=[f for f in KG.iterdir() if f.is_file() and f.name not in preserve]
    # Documentation is replaced separately with apply_patch, after preservation.
    for folder in (KG/'output',):
        candidates.extend(f for f in folder.iterdir() if f.is_file() and f.name not in {'CURRENT_VERSION.json','知识图谱_关系节点属性.csv'})
    for f in candidates:
        if f.name.startswith('~$'):continue # Office's live lock files are not ours.
        source=f.resolve();dest=(target/f.relative_to(KG)).resolve()
        if not source.is_relative_to(KG.resolve()) or not dest.is_relative_to(BACKUP.resolve()):
            raise ValueError('Unsafe relocation')
        if dest.exists():raise ValueError('Existing archive target: '+str(dest))
        digest=hashlib.sha256(f.read_bytes()).hexdigest()
        dest.parent.mkdir(parents=True,exist_ok=True)
        try:shutil.move(str(source),str(dest))
        except PermissionError:
            manifest.append(dict(original=str(source),moved=False,reason='Open file; original retained',sha256=digest));continue
        if hashlib.sha256(dest.read_bytes()).hexdigest()!=digest:raise ValueError('Archive verification failed')
        manifest.append(dict(original=str(source),archive=str(dest),moved=True,sha256=digest))
    write_json(target/'move_manifest.json',manifest)
    print(json.dumps(dict(moved=sum(m['moved'] for m in manifest),retained=sum(not m['moved'] for m in manifest),archive=str(target))))

if __name__=='__main__':main()
