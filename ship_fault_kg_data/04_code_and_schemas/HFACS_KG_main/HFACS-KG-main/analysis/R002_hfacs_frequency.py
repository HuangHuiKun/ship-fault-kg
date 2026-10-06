"""R002 — HFACS factor frequency analysis"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json
from pathlib import Path

DATA = Path("kg_export")
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

hfacs = pd.read_csv(DATA / "nodes_hfacs_factor.csv")
accidents = pd.read_csv(DATA / "nodes_accident.csv")
n_accidents = len(accidents)

# Count factor frequency by name
freq = hfacs["name"].value_counts().reset_index()
freq.columns = ["factor_name", "count"]
freq["pct_of_accidents"] = (freq["count"] / n_accidents * 100).round(1)
freq.to_csv(RESULTS / "R002_hfacs_top50.csv", index=False)

# Top 30 horizontal bar chart
top30 = freq.head(30)
fig, ax = plt.subplots(figsize=(12, 10))
bars = ax.barh(range(len(top30)), top30["count"], color="steelblue", alpha=0.8)
ax.set_yticks(range(len(top30)))
# Truncate long names
labels = [name[:65] + "..." if len(name) > 65 else name for name in top30["factor_name"]]
ax.set_yticklabels(labels, fontsize=8)
ax.invert_yaxis()
ax.set_xlabel("Frequency (number of accident reports)", fontsize=11)
ax.set_title("Top 30 Most Frequent HFACS Factors in Maritime Accidents", fontsize=13)
for bar, count in zip(bars, top30["count"]):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            str(count), va="center", fontsize=8)
plt.tight_layout()
plt.savefig(RESULTS / "R002_hfacs_top50.png", dpi=300, bbox_inches="tight")
plt.close()

summary = {
    "total_unique_factors": len(freq),
    "total_factor_instances": int(hfacs.shape[0]),
    "avg_factors_per_accident": round(hfacs.shape[0] / n_accidents, 1),
    "top10": freq.head(10)[["factor_name","count","pct_of_accidents"]].to_dict("records")
}
with open(RESULTS / "R002_summary.json", "w") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print(f"[R002] DONE: {len(freq)} unique factors, avg {summary['avg_factors_per_accident']} per accident")
print(f"Top 5 factors:")
for i, row in freq.head(5).iterrows():
    print(f"  {i+1}. {row['factor_name'][:70]} ({row['count']}, {row['pct_of_accidents']}%)")
