"""Idempotently import the built graph into an existing Neo4j database.

Only MERGE and SET are used. Other nodes and relations are not deleted or
changed. Every imported node carries the :ShipKG label.

Run in a Python environment containing py2neo:
    python ship_fault_kg/import_neo4j.py
"""

from __future__ import annotations

from collections import defaultdict
import getpass
import json
import os
from pathlib import Path
import re
import sqlite3
import sys

from py2neo import Graph


DB = Path(__file__).resolve().parent / "output" / "ship_fault_kg.sqlite"


def batches(rows: list[dict], size: int = 100):
    for start in range(0, len(rows), size):
        yield rows[start:start + size]


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        nodes = [dict(row) for row in conn.execute("SELECT * FROM nodes")]
        edges = [dict(row) for row in conn.execute("SELECT * FROM edges")]
        evidence = {row["id"]: dict(row) for row in conn.execute("SELECT * FROM evidence")}
    finally:
        conn.close()

    password = os.getenv("NEO4J_PASSWORD")
    if not password:
        if not sys.stdin.isatty():
            raise RuntimeError("Neo4j 当前密码未提供；请在交互终端运行此脚本，或先设置 NEO4J_PASSWORD。")
        password = getpass.getpass("当前 Neo4j 管理员密码（输入不显示）：")
    neo4j_url = os.getenv("NEO4J_URL", "http://localhost:7475")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_dbname = os.getenv("NEO4J_DBNAME", "shipfaultkg")
    graph = Graph(neo4j_url,
                  auth=(neo4j_user, password),
                  name=neo4j_dbname)
    graph.run("CREATE CONSTRAINT shipkg_id IF NOT EXISTS FOR (n:ShipKG) REQUIRE n.id IS UNIQUE")

    by_kind = defaultdict(list)
    for node in nodes:
        props = json.loads(node["props"])
        by_kind[node["kind"]].append({**node,
            "case_id": props.get("case_id", ""),
            "data_origin": props.get("data_origin", ""),
            "data_rows": props.get("data_rows", "")})
    for kind, group in by_kind.items():
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", kind):
            raise ValueError(f"Unexpected node kind: {kind}")
        cypher = (f"UNWIND $rows AS row MERGE (n:ShipKG:{kind} {{id:row.id}}) "
                  "SET n.kind=row.kind, n.name=row.name, n.aliases=row.aliases, "
                  "n.props_json=row.props, n.case_id=row.case_id, "
                  "n.data_origin=row.data_origin, n.data_rows=row.data_rows")
        for batch in batches(group):
            graph.run(cypher, rows=batch).consume()

    by_relation = defaultdict(list)
    for edge in edges:
        ev = evidence[edge["evidence_id"]]
        by_relation[edge["relation"]].append({**edge,
            "source_file": ev["source_file"], "source_url": ev["source_url"],
            "page": str(ev["page"]), "locator": ev["locator"], "quote": ev["quote"]})
    for relation, group in by_relation.items():
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", relation):
            raise ValueError(f"Unexpected relation: {relation}")
        cypher = ("UNWIND $rows AS row "
                  "MATCH (a:ShipKG {id:row.source}), (b:ShipKG {id:row.target}) "
                  f"MERGE (a)-[r:{relation} {{id:row.id}}]->(b) "
                  "SET r.case_id=row.case_id, r.certainty=row.certainty, "
                  "r.evidence_id=row.evidence_id, r.source_file=row.source_file, "
                  "r.source_url=row.source_url, r.page=row.page, "
                  "r.locator=row.locator, r.quote=row.quote, r.props_json=row.props")
        for batch in batches(group):
            graph.run(cypher, rows=batch).consume()

    node_count = graph.run("MATCH (n:ShipKG) RETURN count(n) AS n").evaluate()
    edge_count = graph.run("MATCH (:ShipKG)-[r]->(:ShipKG) WHERE r.id STARTS WITH 'edge:' RETURN count(r) AS n").evaluate()
    result = {"imported_nodes_in_file": len(nodes), "imported_edges_in_file": len(edges),
              "shipkg_nodes_in_neo4j": node_count, "shipkg_edges_in_neo4j": edge_count,
              "database": neo4j_dbname}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if node_count < len(nodes) or edge_count < len(edges):
        raise RuntimeError("Neo4j import count is smaller than the source graph")


if __name__ == "__main__":
    main()
