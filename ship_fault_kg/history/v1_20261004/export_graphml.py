"""Export the local graph to portable GraphML for Gephi or other graph tools."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3

import networkx as nx


HERE = Path(__file__).resolve().parent


def main() -> None:
    db = sqlite3.connect(HERE / "output" / "ship_fault_kg.sqlite")
    db.row_factory = sqlite3.Row
    try:
        graph = nx.MultiDiGraph()
        for row in db.execute("SELECT * FROM nodes"):
            data = dict(row)
            props = json.loads(data.pop("props"))
            graph.add_node(data.pop("id"), **data,
                           data_origin=str(props.get("data_origin", "")),
                           case_id=str(props.get("case_id", "")))
        evidence = {row["id"]: dict(row) for row in db.execute("SELECT * FROM evidence")}
        for row in db.execute("SELECT * FROM edges"):
            data = dict(row)
            ev = evidence[data["evidence_id"]]
            graph.add_edge(data["source"], data["target"], key=data["id"],
                           relation=data["relation"], case_id=data["case_id"],
                           certainty=data["certainty"], source_file=ev["source_file"],
                           page=str(ev["page"]), source_url=ev["source_url"])
    finally:
        db.close()
    target = HERE / "output" / "ship_fault_kg.graphml"
    nx.write_graphml(graph, target)
    print(f"{target} nodes={graph.number_of_nodes()} edges={graph.number_of_edges()}")


if __name__ == "__main__":
    main()
