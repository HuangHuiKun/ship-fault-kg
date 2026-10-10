"""Current graph as one Chinese relation-node-property table, stdlib only.

Run directly to refresh, or let build.py refresh it after each successful build.
This is a read-only export of SQLite, not a Neo4j importer or CSV edit-back tool.
"""
from __future__ import annotations

import argparse
import csv
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from schema import KIND_ZH, RELATION_ZH, CERTAINTY_ZH, CAUSAL_RELS

HERE = Path(__file__).resolve().parent
FILENAME = "知识图谱_关系节点属性.csv"
HEADERS = ["起点节点", "起点类型", "起点主要属性", "关系名称", "终点节点", "终点类型",
           "终点主要属性", "关系性质", "证据性质", "所属案例或知识单元", "来源文件",
           "来源位置", "来源链接", "起点ID", "关系代码", "终点ID", "关系ID", "证据ID", "图谱版本"]
# Display business properties; omit migration/audit internals available in JSON.
PROPERTY_ZH = {
    "source_tier": "来源可靠性层级", "expert_review": "专家核验状态", "warning": "使用限制",
    "entity_level": "实体层级", "vessel_type": "船型", "vessel_types": "船型列表",
    "vessel_identity_status": "船舶身份说明", "anonymous": "船舶身份未公开",
    "system_level": "系统层级", "equipment_scope": "设备范围",
    "fault_level": "故障层级", "knowledge_layer": "知识层级",
    "coupling_domains": "耦合领域", "applicability": "适用范围",
    "semantic_class": "语义类别", "data_origin": "数据性质",
    "source_level": "来源层级", "source_record_type": "记录类型",
    "record": "原表记录行", "reference_class": "原始记录分类",
    "warning_hours": "预警时间（小时）", "warning_months": "预警时间（月）",
    "unit": "单位", "original_column_name": "原始测点字段",
    "selection_reason": "测点保留理由", "note": "说明",
    "anomaly_state": "异常状态", "data_rows": "数据行数", "columns": "数据列数",
    "schema_type": "数据结构", "original_file_name": "原始数据文件",
}
VALUE_ZH = {
    "secondary": "二次语料", "pending": "待核验", "corpus_secondary": "二次中文语料知识",
    "controlled_experiment": "受控试验", "experiment": "试验",
    "simulated": "仿真", "field_report": "实船调查报告",
    "monitoring_summary": "监测汇总", "cbm_summary": "状态监测汇总",
    "reference_knowledge": "参考知识", "normal_reference": "正常参照状态",
    "observed": "观测状态", "derived": "依据资料整理",
    "thermodynamic_simulation": "热力仿真", "simulation": "仿真",
    "anonymised_field_summary": "未公开船名的实船监测汇总",
    "failure_or_event": "故障或事件", "unconfirmed_warning": "未证实的警告状态",
    "degradation": "性能退化", "protective_event": "保护动作事件",
    "reference_category": "参考故障类别", "reference": "参考",
    "scenario": "试验工况", "thermal": "热", "mechanical": "机", "electrical": "电",
    "binary (0=pre-anomaly, 1=anomaly)": "二值标注（0=异常前，1=异常）",
    "all-anomaly (no baseline segment)": "全部为异常（无正常基线段）",
    "none (baseline)": "正常基线（无异常）",
}


def display(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (list, tuple)):
        return "、".join(display(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    text = str(value)
    return VALUE_ZH.get(text, text)


def safe_cell(value):
    """Prevent Excel formula evaluation, preserving underlying graph values."""
    text = display(value).replace("\r\n", "\n").replace("\r", "\n")
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def summary(node):
    props = node["properties"]
    pieces = []
    for key, label in PROPERTY_ZH.items():
        value = props.get(key)
        if value is None or value == "" or value == [] or value == {}:
            continue
        # Avoid showing the same vessel classification twice.
        if key == "vessel_types" and value == [props.get("vessel_type")]:
            continue
        if key == "semantic_class" and value == "failure_or_event" and props.get("fault_level"):
            continue
        pieces.append(f"{label}：{display(value)}")
    return "；".join(pieces)


def make_rows(db):
    db = Path(db).resolve()
    with closing(sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        # One read transaction: all tables describe the same snapshot.
        conn.execute("BEGIN")
        nodes = {row["id"]: dict(row) for row in conn.execute("SELECT * FROM nodes ORDER BY id")}
        edges = [dict(row) for row in conn.execute("SELECT * FROM edges ORDER BY id")]
        evidence = {row["id"]: dict(row) for row in conn.execute("SELECT * FROM evidence")}
    for node in nodes.values():
        node["properties"] = json.loads(node["props"])
    contexts = {}
    for node in nodes.values():
        props = node["properties"]
        if node["kind"] == "Case" and props.get("case_id"):
            contexts[props["case_id"]] = "事故案例：" + node["name"]
        if props.get("knowledge_id"):
            contexts["knowledge:" + props["knowledge_id"]] = "参考机理：" + node["name"]
    rows, seen, versions = [], set(), set()
    order = {kind: index for index, kind in enumerate([
        "Fault", "Cause", "Condition", "Symptom", "Consequence", "Check", "Action",
        "Equipment", "Component", "System", "Case", "Vessel", "Run", "Sensor", "Source"])}
    edges.sort(key=lambda edge: (order.get(nodes[edge["source"]]["kind"], 999),
                                nodes[edge["source"]]["name"], edge["relation"],
                                nodes[edge["target"]]["name"], edge["id"]))
    for edge in edges:
        start, end = nodes[edge["source"]], nodes[edge["target"]]
        proof = evidence[edge["evidence_id"]]
        props = json.loads(edge["props"])
        versions.update(str(node["properties"].get("graph_version", "")) for node in (start, end))
        positions = []
        if proof.get("page") not in (None, ""):
            positions.append(f"物理第{proof['page']}页")
        if proof.get("locator"):
            positions.append(str(proof["locator"]))
        context_id = edge.get("case_id", "")
        causal = props.get("is_causal", edge["relation"] in CAUSAL_RELS)
        rows.append([start["name"], KIND_ZH.get(start["kind"], start["kind"]), summary(start),
                     props.get("name") or RELATION_ZH.get(edge["relation"], edge["relation"]),
                     end["name"], KIND_ZH.get(end["kind"], end["kind"]), summary(end),
                     "因果类" if causal else "非因果（归属、分类、检查或建议等）",
                     CERTAINTY_ZH.get(edge["certainty"], edge["certainty"]),
                     contexts.get(context_id, context_id), proof.get("source_file", ""),
                     "；".join(positions), proof.get("source_url", ""), start["id"],
                     edge["relation"], end["id"], edge["id"], edge["evidence_id"],
                     props.get("graph_version", start["properties"].get("graph_version", ""))])
        seen.update((start["id"], end["id"]))
    # Retain future nodes with no edge rather than silently omitting them.
    for ident in sorted(set(nodes) - seen):
        node = nodes[ident]
        rows.append([node["name"], KIND_ZH.get(node["kind"], node["kind"]), summary(node),
                     "暂无关联关系", "", "", "", "无关系", "", "", "", "", "",
                     node["id"], "", "", "", "", node["properties"].get("graph_version", "")])
        versions.add(str(node["properties"].get("graph_version", "")))
    if len(versions - {""}) > 1:
        raise ValueError(f"Mixed graph versions: {sorted(versions)}")
    return [[safe_cell(value) for value in row] for row in rows], {
        "node_count": len(nodes), "relationship_count": len(edges),
        "isolated_node_count": len(nodes) - len(seen), "rows": len(rows),
        "graph_version": next(iter(versions - {""}), "unknown")}


def atomic_replace(source, target):
    """Narrow failure-injection seam; tests must not mock the global os module."""
    os.replace(source, target)


def export_csv(db=None, output=None):
    db = Path(db or HERE / "output" / "ship_fault_kg.sqlite")
    output = Path(output or db.parent / FILENAME)
    rows, result = make_rows(db)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Keep last valid CSV intact if Excel holds it open or export is interrupted.
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tmp", prefix="shipkg_csv_",
                                         dir=output.parent, encoding="utf-8-sig", newline="",
                                         delete=False) as handle:
            temp_name = handle.name
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(HEADERS)
            writer.writerows(rows)
        atomic_replace(temp_name, output)
    finally:
        if temp_name and Path(temp_name).exists():
            Path(temp_name).unlink()  # Exact temporary file owned by this export.
    return dict(result, output=str(output), encoding="UTF-8 with BOM")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=HERE / "output" / "ship_fault_kg.sqlite")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--matrix-json", type=Path, help="Optional authoring/verification matrix; no CSV written")
    args = parser.parse_args()
    if args.matrix_json:
        rows, info = make_rows(args.db)
        args.matrix_json.write_text(json.dumps({"headers": HEADERS, "rows": rows, "summary": info},
                                              ensure_ascii=False), encoding="utf-8")
        print(json.dumps(info, ensure_ascii=False))
    else:
        print(json.dumps(export_csv(args.db, args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
