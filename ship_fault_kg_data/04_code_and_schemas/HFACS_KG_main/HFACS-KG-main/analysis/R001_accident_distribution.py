"""R001 — Accident type distribution"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json
from pathlib import Path

DATA = Path("kg_export")
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

df = pd.read_csv(DATA / "nodes_accident.csv")
dist = df["accident_type"].value_counts().reset_index()
dist.columns = ["accident_type", "count"]
dist["percentage"] = (dist["count"] / len(df) * 100).round(1)
dist.to_csv(RESULTS / "R001_accident_distribution.csv", index=False)

# Plot
fig, ax = plt.subplots(figsize=(10, 6))
colors = plt.cm.Set3.colors
bars = ax.bar(dist["accident_type"], dist["count"], color=colors[:len(dist)])
ax.set_xlabel("Accident Type", fontsize=12)
ax.set_ylabel("Count", fontsize=12)
ax.set_title("Maritime Accident Type Distribution (n=1,165)", fontsize=14)
plt.xticks(rotation=45, ha="right", fontsize=9)
for bar, pct in zip(bars, dist["percentage"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
            f"{pct:.1f}%", ha="center", va="bottom", fontsize=7)
plt.tight_layout()
plt.savefig(RESULTS / "R001_accident_distribution.png", dpi=300, bbox_inches="tight")
plt.close()

summary = {"top3": dist.head(3)[["accident_type","count","percentage"]].to_dict("records"),
           "total": len(df), "n_types": len(dist)}
with open(RESULTS / "R001_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print(f"[R001] DONE: Top type={dist.iloc[0]['accident_type']} ({dist.iloc[0]['count']}, {dist.iloc[0]['percentage']}%), {len(dist)} types total")
print(dist.to_string(index=False))
