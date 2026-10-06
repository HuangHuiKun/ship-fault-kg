"""R003 — KG structural statistics"""
import pandas as pd
import json
from pathlib import Path

DATA = Path("kg_export")
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

nodes = {
    "Accident":      pd.read_csv(DATA / "nodes_accident.csv"),
    "HFACS_Factor":  pd.read_csv(DATA / "nodes_hfacs_factor.csv"),
    "EventNode":     pd.read_csv(DATA / "nodes_event.csv"),
    "Vessel":        pd.read_csv(DATA / "nodes_vessel.csv"),
    "Location":      pd.read_csv(DATA / "nodes_location.csv"),
    "Environment":   pd.read_csv(DATA / "nodes_environment.csv"),
}
rels = {
    "ORIGINATED_FROM": pd.read_csv(DATA / "rel_originated_from.csv"),
    "LED_TO":          pd.read_csv(DATA / "rel_led_to.csv"),
    "INVOLVED_IN":     pd.read_csv(DATA / "rel_involved_in.csv"),
    "HAPPENED_AT":     pd.read_csv(DATA / "rel_happened_at.csv"),
    "AFFECTED_BY":     pd.read_csv(DATA / "rel_affected_by.csv"),
}

n_accidents = len(nodes["Accident"])

stats = {
    "nodes": {k: len(v) for k, v in nodes.items()},
    "total_nodes": sum(len(v) for v in nodes.values()),
    "relationships": {k: len(v) for k, v in rels.items()},
    "total_relationships": sum(len(v) for v in rels.values()),
    "derived": {
        "avg_hfacs_per_accident": round(len(nodes["HFACS_Factor"]) / n_accidents, 1),
        "avg_events_per_accident": round(len(nodes["EventNode"]) / n_accidents, 1),
        "avg_vessels_per_accident": round(len(nodes["Vessel"]) / n_accidents, 1),
        "avg_orig_from_per_accident": round(len(rels["ORIGINATED_FROM"]) / n_accidents, 1),
        "event_chain_rels": int(rels["LED_TO"][rels["LED_TO"]["src_label"]=="EventNode"][rels["LED_TO"]["dst_label"]=="EventNode"].shape[0]),
    }
}

# Save CSV summary
rows = []
for k, v in stats["nodes"].items():
    rows.append({"category": "node", "type": k, "count": v})
for k, v in stats["relationships"].items():
    rows.append({"category": "relationship", "type": k, "count": v})
pd.DataFrame(rows).to_csv(RESULTS / "R003_kg_stats.csv", index=False)

with open(RESULTS / "R003_summary.json", "w") as f:
    json.dump(stats, f, indent=2)

print(f"[R003] DONE: {stats['total_nodes']} nodes, {stats['total_relationships']} relationships")
print(f"  Avg HFACS factors per accident: {stats['derived']['avg_hfacs_per_accident']}")
print(f"  Avg event chain nodes per accident: {stats['derived']['avg_events_per_accident']}")
print(f"  EventNode->EventNode chains: {stats['derived']['event_chain_rels']}")
for k, v in stats["nodes"].items():
    print(f"  {k}: {v}")
for k, v in stats["relationships"].items():
    print(f"  {k}: {v}")
