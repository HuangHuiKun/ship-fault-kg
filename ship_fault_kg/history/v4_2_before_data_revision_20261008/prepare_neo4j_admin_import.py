"""Prepare validated CSV files for a fresh Neo4j Desktop database.

The output is for ``neo4j-admin database import full shipfaultkg``.  It never
connects to or changes an existing Neo4j database.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import re
import sqlite3


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "output" / "ship_fault_kg.sqlite"
DEST = ROOT / "output" / "neo4j_admin_import"


def clean(value: object) -> str:
    """Keep CSV records on one physical line for the offline importer."""
    if value is None:
        return ""
    return str(value).replace("\r", " ").replace("\n", " ")


def main() -> None:
    with sqlite3.connect(SOURCE) as conn:
        conn.row_factory = sqlite3.Row
        nodes = [dict(row) for row in conn.execute("SELECT * FROM nodes ORDER BY id")]
        edges = [dict(row) for row in conn.execute("SELECT * FROM edges ORDER BY id")]
        evidence = {
            row["id"]: dict(row)
            for row in conn.execute("SELECT * FROM evidence")
        }

    node_ids = {row["id"] for row in nodes}
    if len(node_ids) != len(nodes):
        raise ValueError("Duplicate node IDs")
    if len({row["id"] for row in edges}) != len(edges):
        raise ValueError("Duplicate relationship IDs")
    for row in edges:
        if row["source"] not in node_ids or row["target"] not in node_ids:
            raise ValueError(f"Relationship {row['id']} has a missing endpoint")
        if row["evidence_id"] not in evidence:
            raise ValueError(f"Relationship {row['id']} has missing evidence")
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", row["relation"]):
            raise ValueError(f"Invalid relationship type: {row['relation']}")

    DEST.mkdir(parents=True, exist_ok=True)
    with (DEST / "nodes_admin.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([
            "id:ID(ShipKG)", "kind", "name", "aliases", "props_json",
            "case_id", "data_origin", "data_rows", ":LABEL",
        ])
        for row in nodes:
            kind = row["kind"]
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", kind):
                raise ValueError(f"Invalid node kind: {kind}")
            props = json.loads(row["props"])
            writer.writerow([
                row["id"], kind, clean(row["name"]),
                clean(row["aliases"]), clean(row["props"]),
                clean(props.get("case_id")), clean(props.get("data_origin")),
                clean(props.get("data_rows")), f"ShipKG;{kind}",
            ])

    with (DEST / "relationships_admin.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([
            ":START_ID(ShipKG)", ":END_ID(ShipKG)", "id", ":TYPE",
            "case_id", "certainty", "evidence_id", "source_file",
            "source_url", "page", "locator", "quote", "props_json",
        ])
        for row in edges:
            ev = evidence[row["evidence_id"]]
            writer.writerow([
                row["source"], row["target"], row["id"], row["relation"],
                clean(row["case_id"]), clean(row["certainty"]), row["evidence_id"],
                clean(ev["source_file"]), clean(ev["source_url"]),
                clean(ev["page"]), clean(ev["locator"]), clean(ev["quote"]),
                clean(row["props"]),
            ])

    print(json.dumps({
        "nodes": len(nodes), "relationships": len(edges), "evidence_records": len(evidence),
        "nodes_file": str(DEST / "nodes_admin.csv"),
        "relationships_file": str(DEST / "relationships_admin.csv"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
