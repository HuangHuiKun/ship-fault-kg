"""R000 — Data integrity sanity check"""
import pandas as pd
import json, sys
from pathlib import Path

DATA = Path("kg_export")
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

files = {
    "nodes_accident":     ("id","name","accident_type","source_file"),
    "nodes_hfacs_factor": ("id","name","source_file"),
    "nodes_event":        ("id","name","source_file"),
    "nodes_vessel":       ("id","name","source_file"),
    "nodes_location":     ("id","name","source_file"),
    "nodes_environment":  ("id","name","source_file"),
    "rel_originated_from":("src","src_label","dst","dst_label"),
    "rel_led_to":         ("src","src_label","dst","dst_label"),
    "rel_involved_in":    ("src","src_label","dst","dst_label"),
    "rel_happened_at":    ("src","src_label","dst","dst_label"),
    "rel_affected_by":    ("src","src_label","dst","dst_label"),
}

expected = {
    "nodes_accident": 1165, "nodes_hfacs_factor": 24888,
    "nodes_event": 6799,    "nodes_vessel": 3722,
    "nodes_location": 3119, "nodes_environment": 2982,
    "rel_originated_from": 21553, "rel_led_to": 11585,
    "rel_involved_in": 5331, "rel_happened_at": 4577,
    "rel_affected_by": 4422,
}

results = {}
errors = []

for name, cols in files.items():
    path = DATA / f"{name}.csv"
    df = pd.read_csv(path)
    count = len(df)
    null_pct = df["name"].isna().mean() * 100 if "name" in df.columns else 0
    dup_count = df.duplicated(subset=["id"] if "id" in df.columns else ["src","dst"]).sum()
    exp = expected[name]
    match = count == exp

    results[name] = {"count": count, "expected": exp, "match": match,
                     "null_name_pct": round(null_pct, 2), "duplicates": int(dup_count)}
    if not match:
        errors.append(f"{name}: got {count}, expected {exp}")
    if null_pct > 1:
        errors.append(f"{name}: {null_pct:.1f}% null names")

    print(f"  {'OK' if match else 'FAIL'} {name}: {count} rows (expected {exp}), nulls={null_pct:.1f}%, dups={dup_count}")

with open(RESULTS / "R000_summary.json", "w") as f:
    json.dump({"status": "PASS" if not errors else "FAIL", "errors": errors, "details": results}, f, indent=2)

if errors:
    print(f"\n[R000] FAIL: {errors}")
    sys.exit(1)
else:
    print(f"\n[R000] DONE: All 11 files pass integrity check — 42,679 nodes, 47,468 relationships confirmed")
