"""Non-mutating release/rollback-plan checks. Not a scientific retrieval eval."""
import csv,hashlib,json,sqlite3,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from .preprocess import KG,OUT,write_json
from . import neo4j

def main():
    checks={}
    new=json.loads((OUT/'neo4j_snapshot_v5.json').read_text(encoding='utf-8'))
    previous=json.loads((OUT/'last_deployed_snapshot.json').read_text(encoding='utf-8'))
    checks['cached_rebuild_matches_deployed_snapshot']=neo4j.signature(new)==neo4j.signature(previous)
    old=json.loads((neo4j.BACKUP/'neo4j_live_before_v5.json').read_text(encoding='utf-8'))
    checks['real_old_database_preserved']=len(old['nodes'])==491 and len(old['edges'])==1200
    backup_db=neo4j.BACKUP/'output/ship_fault_kg.sqlite'
    checks['original_sqlite_sha256_unchanged']=hashlib.sha256(backup_db.read_bytes()).hexdigest().upper()=='E027967835BAF395ADF011E91BC3137634F52E257C43994EE57CCCEDB41C6496'
    # Validate the complete old-version labels/types as a restore plan, without
    # executing it or temporarily replacing the current database.
    neo4j.KINDS=dict(neo4j.KINDS,Run='试验',Sensor='测点',Cause='原因',Condition='工况',Symptom='症状',Consequence='后果')
    query,params=neo4j.deployment_query(new,old)
    checks['restore_plan_valid_without_database_write']='DETACH' not in query and len(params['old_nodes'])==len(new['nodes'])
    table=list(csv.reader((OUT/'知识图谱_关系节点属性_V5.csv').open(encoding='utf-8-sig',newline='')))
    checks['readable_csv_complete']=len(table)-1==len(new['edges']) and len(table[0])==13
    checks['root_csv_matches_v5']=(OUT/'知识图谱_关系节点属性_V5.csv').read_bytes()==(KG/'output/知识图谱_关系节点属性.csv').read_bytes()
    labels={label for n in new['nodes'] for label in n['labels']}
    checks['no_passage_assertion_run_sensor_nodes']=not labels&{'Passage','Assertion','Run','Sensor'}
    manifest=json.loads((neo4j.BACKUP/'backup_manifest.json').read_text(encoding='utf-8'))
    # Byte fingerprints cover recovery material. Python caches and Office/WPS
    # locks are machine-specific artifacts, intentionally excluded from Git.
    archive_records=[r for r in manifest['files']
        if '__pycache__' not in Path(r['path']).parts
        and Path(r['path']).suffix!='.pyc'
        and not Path(r['path']).name.startswith('~$')]
    checks['archive_files_sha256_match']=all(
        (neo4j.BACKUP/r['path']).is_file()
        and hashlib.sha256((neo4j.BACKUP/r['path']).read_bytes()).hexdigest()==r['sha256']
        for r in archive_records)
    book=OUT/'outputs/kg_v5_20261009/知识图谱清单_V5.xlsx'
    if book.exists():
        with zipfile.ZipFile(book) as archive:
            checks['xlsx_zip_integrity']=archive.testzip() is None
            xml=ET.fromstring(archive.read('xl/workbook.xml'))
            checks['xlsx_has_four_review_sheets']=len(xml.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet'))==4
            checks['xlsx_cached_formulas_have_no_errors']=all(b't="e"' not in archive.read(p) for p in archive.namelist() if p.startswith('xl/worksheets/sheet') and p.endswith('.xml'))
    result=dict(passed=all(checks.values()),checks=checks,
        archive_files_checked=len(archive_records),
        excluded_machine_artifacts=[r['path'] for r in manifest['files'] if r not in archive_records],
        note='恢复SQL只作结构校验，未实际回滚当前数据库；重建一致性以当前已部署快照为比较基准。')
    write_json(OUT/'pipeline_test_report.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
    if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()
