"""R004 — HFACS category patterns by accident type (heatmap)"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import json
from pathlib import Path

DATA = Path("kg_export")
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

accidents  = pd.read_csv(DATA / "nodes_accident.csv")
hfacs      = pd.read_csv(RESULTS / "R002b_hfacs_with_categories.csv")

# Join via source_file (each factor belongs to the accident from the same PDF)
acc_src = accidents[["source_file","accident_type"]]
linked = (hfacs[["source_file","category"]]
          .merge(acc_src, on="source_file", how="inner")
          .dropna(subset=["category","accident_type"]))

# Top 10 accident types by count
top10_types = accidents["accident_type"].value_counts().head(10).index.tolist()

# Top 12 categories (exclude Other)
cat_order = (hfacs[hfacs["category"] != "Other / Unclassified"]
             ["category"].value_counts().head(12).index.tolist())

matrix = (linked[linked["accident_type"].isin(top10_types)]
          .groupby(["accident_type","category"]).size()
          .unstack(fill_value=0))
matrix = matrix[[c for c in cat_order if c in matrix.columns]]

# Normalise by row (% within accident type)
matrix_pct = matrix.div(matrix.sum(axis=1), axis=0) * 100

matrix_pct.to_csv(RESULTS / "R004_type_factor_matrix.csv")

# ── Heatmap ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(15, 7))
im = ax.imshow(matrix_pct.values, aspect="auto", cmap="YlOrRd", vmin=0, vmax=matrix_pct.values.max())

# Short column labels
short_labels = {
    "Procedures & SMS": "Procedures\n& SMS",
    "Navigation & Passage Planning": "Navigation\n& Planning",
    "Training & Competency": "Training &\nCompetency",
    "Situational Awareness": "Situational\nAwareness",
    "Supervision & Oversight": "Supervision\n& Oversight",
    "Fatigue & Workload": "Fatigue &\nWorkload",
    "Communication": "Communication",
    "Maintenance & Equipment": "Maintenance\n& Equipment",
    "Cargo & Lifting Operations": "Cargo &\nLifting",
    "Organizational & Regulatory": "Organizational\n& Regulatory",
    "Vessel Design & Stability": "Vessel Design\n& Stability",
    "Safety Culture & Pressure": "Safety Culture\n& Pressure",
}
col_labels = [short_labels.get(c, c) for c in matrix_pct.columns]

ax.set_xticks(range(len(matrix_pct.columns)))
ax.set_xticklabels(col_labels, fontsize=8)
ax.set_yticks(range(len(matrix_pct.index)))
ax.set_yticklabels(matrix_pct.index, fontsize=9)

plt.colorbar(im, ax=ax, label="% of HFACS factors (row-normalised)")
ax.set_title("HFACS Category Distribution by Accident Type\n(row-normalised %, top 10 accident types × top 12 HFACS categories)",
             fontsize=12, pad=12)

for i in range(len(matrix_pct.index)):
    for j in range(len(matrix_pct.columns)):
        val = matrix_pct.values[i, j]
        if val >= 1.0:
            ax.text(j, i, f"{val:.0f}%", ha="center", va="center",
                    fontsize=7.5, color="black" if val < matrix_pct.values.max()*0.6 else "white",
                    fontweight="bold" if val >= 20 else "normal")

plt.tight_layout()
plt.savefig(RESULTS / "R004_type_factor_heatmap.png", dpi=300, bbox_inches="tight")
plt.close()

# ── Top factor per accident type (raw counts) ─────────────────────────────────
top_factor_per_type = {}
for atype in top10_types:
    subset = linked[linked["accident_type"] == atype]
    top = subset["category"].value_counts().head(3)
    top_factor_per_type[atype] = top.to_dict()

with open(RESULTS / "R004_summary.json", "w", encoding="utf-8") as f:
    json.dump({"top_factor_per_type": top_factor_per_type,
               "matrix_shape": list(matrix_pct.shape)}, f, indent=2, ensure_ascii=False)

print("[R004] DONE: Accident-type × HFACS category heatmap generated")
print(f"  Matrix: {matrix_pct.shape[0]} accident types × {matrix_pct.shape[1]} categories")
print("\nTop HFACS category per accident type:")
for atype, cats in top_factor_per_type.items():
    top1 = list(cats.keys())[0]
    print(f"  {atype:<25} -> {top1}")
