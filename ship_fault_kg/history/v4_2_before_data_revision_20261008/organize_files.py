"""Conservative, repeatable historical-file archival; never touches Neo4j.

Default: preview. --apply: move exact reviewed paths, verify SHA256 and write
an audit manifest. --scan: regenerate a content-based duplicate report only.
Historical snapshots and all duplicate contents are retained, not deleted.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "history" / "organization_20261007"
MOVES = {}


def register(category, paths):
    for path in paths:
        MOVES[path] = f"history/organization_20261007/{category}/{path}"


register("legacy_tools", ["queries_v2.cypher", "queries_v3.cypher",
                         "verify_v2.py", "verify_v3.py", "revision_v3.py"])
register("v2_artifacts", [f"output/{name}" for name in [
    "demo_v2_cpp.json", "demo_v2_cpp.md", "entity_inventory_v2.md",
    "eval_queries_v2.json", "graph_inventory_v2.json", "neo4j_v2_counts.jpg",
    "neo4j_v2_graph.jpg", "shipkg_v2_json.grass", "shipkg_v2.grass",
    "viewer_v2_evidence.jpg", "viewer_verification_v2.json"]])
register("v3_artifacts", [f"output/{name}" for name in [
    "demo_v3_scuffing.json", "demo_v3_scuffing.md", "entity_inventory_v3.md",
    "entity_inventory_v3 copy.md", "fault_retrieval_evaluation_v3.json",
    "graph_inventory_v3.json", "neo4j_v3_archive.jpg", "neo4j_v3_counts.jpg",
    "neo4j_v3_scuffing.jpg", "retrieval_evaluation.json",
    "retrieval_evaluation_lexical.json", "retrieval_examples_v3.json",
    "shipkg_v3.grass", "viewer_v3_scuffing.jpg", "ollama_shipkg.stderr.log", "ollama_shipkg.stdout.log"]])
register("sensor_maintenance", [f"output/{name}" for name in [
    "maintenance_20261005", "revision_changes_v3.json", "sensor_cleanup_guide_v3.html",
    "neo4j_sensor_archive_v3.cypher", "neo4j_sensor_cleanup_v3.cypher",
    "neo4j_sensor_preview_v3.cypher", "neo4j_sensor_unarchive_v3.cypher"]])
register("connection_maintenance", ["output/neo4j_connection_repair_20261005"])
register("source_review", ["output/source_review_v3"])
register("v1_artifacts", ["output/v1_legacy"])
register("presentations", ["presentations"])
# The approved-name proposal predates V4.0, and is not a runtime dependency.
register("design_review", ["review_v4_20261006"])


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def safe(relative):
    path = (HERE / relative).resolve()
    if not path.is_relative_to(HERE) or path == HERE:
        raise ValueError(f"Unsafe archival path: {relative}")
    return path


def inventory():
    generated = {ARCHIVE / name for name in [
        "move_manifest.json", "duplicates.json", "DUPLICATES.md"]}
    result = {}
    for root, dirs, names in os.walk(HERE, followlinks=False):
        # Windows directory junctions can otherwise traverse bundled runtimes.
        # Dependencies behind a junction are NOT project-owned archival files.
        dirs[:] = sorted(name for name in dirs if name not in {"__pycache__", "node_modules"}
                         and not (getattr(os.lstat(Path(root) / name), "st_file_attributes", 0)
                                  & stat.FILE_ATTRIBUTE_REPARSE_POINT))
        for name in sorted(names):
            path = Path(root) / name
            if path not in generated and not path.is_symlink():
                result[path.relative_to(HERE).as_posix()] = {
                    "bytes": path.stat().st_size, "sha256": digest(path)}
    return result


def duplicates(files):
    by_hash = defaultdict(list)
    for name, info in files.items():
        by_hash[info["sha256"]].append(name)
    groups = [{"sha256": sha, "bytes": files[names[0]]["bytes"], "paths": names}
              for sha, names in sorted(by_hash.items()) if len(names) > 1]
    report = {
        "algorithm": "SHA256 plus byte length", "files_checked": len(files),
        "duplicate_groups": len(groups),
        "additional_copies": sum(len(group["paths"]) - 1 for group in groups),
        "theoretical_redundant_bytes": sum(group["bytes"] * (len(group["paths"]) - 1) for group in groups),
        "deletion_performed": False,
        "policy": "Keep independent version snapshots and every archival copy. Equal names are not equal content.",
        "groups": groups,
    }
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    (ARCHIVE / "duplicates.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# 文件重复检查（2026-10-07）", "",
             f"检查 {len(files)} 个文件，发现 {len(groups)} 组内容完全相同的文件，额外副本 {report['additional_copies']} 份。",
             "", "按字节长度与 SHA256 判定；不按文件名判断。缓存目录和本次自动生成的清单不参与统计。",
             "未删除任何重复文件：历史快照中的副本保留，以便独立恢复。理论冗余字节数不是可安全删除容量。",
             "特别注意：`entity_inventory_v3 copy.md` 与 `entity_inventory_v3.md` 内容不同，不能当作重复文件删除。",
             "", "## 完全重复组", ""]
    for index, group in enumerate(groups, 1):
        lines.extend([f"### {index}. {len(group['paths'])} 份，{group['bytes']} 字节", "",
                      f"SHA256：`{group['sha256']}`", ""])
        for name in group["paths"]:
            lines.append(f"- `{name}`")
        lines.append("")
    (ARCHIVE / "DUPLICATES.md").write_text("\n".join(lines), encoding="utf-8")
    return {key: value for key, value in report.items() if key != "groups"}


def apply():
    manifest_path = ARCHIVE / "move_manifest.json"
    previous = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    if previous and previous["status"] == "verified":
        print(json.dumps({"moves": 0, "note": "Already organized; no archive overwritten."}))
        return
    if previous:
        # Resume a interrupted audit, never repeat or overwrite completed moves.
        before = {row["from"]: {"bytes": row["bytes"], "sha256": row["sha256"]}
                  for row in previous["files"] if "node_modules" not in Path(row["from"]).parts}
    else:
        before = inventory()
    planned = []
    translations = {}
    for old, new in MOVES.items():
        source, target = safe(old), safe(new)
        for name in before:
            if name == old or name.startswith(old + "/"):
                translations[name] = new + name[len(old):]
        if source.exists():
            if target.exists():
                raise FileExistsError(f"Refuse overwrite: {new}")
            planned.append((source, target))
    if not planned and not previous:
        print(json.dumps({"moves": 0, "note": "Already organized; no archive overwritten."}))
        return
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    entries = [{"from": name, "to": translations.get(name, name), **info}
               for name, info in before.items()]
    manifest = {"date": "2026-10-07", "status": "planned",
                "files_moved": len(translations), "files_preserved": len(before),
                "deleted_files": 0, "neo4j_changed": False, "files": entries}
    manifest["excluded_external_dependencies"] = "node_modules junction targets; external bundled runtime was not moved or changed"
    if previous:
        # The audit tool itself was corrected to exclude junction contents.
        tool = next(row for row in entries if row["from"] == "organize_files.py")
        tool["sha256_before_audit_tool_fix"] = tool["sha256"]
        tool.update(bytes=(HERE / "organize_files.py").stat().st_size,
                    sha256=digest(HERE / "organize_files.py"))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    for source, target in planned:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
    for row in entries:
        target = safe(row["to"])
        if not target.is_file() or target.stat().st_size != row["bytes"] or digest(target) != row["sha256"]:
            raise RuntimeError(f"Content verification failed: {row['to']}")
    manifest["status"] = "verified"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in manifest.items() if key != "files"}, ensure_ascii=False))
    print(json.dumps(duplicates(inventory()), ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--scan", action="store_true")
    args = parser.parse_args()
    if args.apply:
        apply()
    elif args.scan:
        print(json.dumps(duplicates(inventory()), ensure_ascii=False))
    else:
        print(json.dumps([{ "from": old, "to": new} for old, new in MOVES.items()
                          if safe(old).exists()], ensure_ascii=False, indent=2))
