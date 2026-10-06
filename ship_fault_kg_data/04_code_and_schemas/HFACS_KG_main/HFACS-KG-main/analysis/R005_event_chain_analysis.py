"""R005 — Event chain length distribution and analysis"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import json
from pathlib import Path
from collections import defaultdict

DATA = Path("kg_export")
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

accidents = pd.read_csv(DATA / "nodes_accident.csv")
events    = pd.read_csv(DATA / "nodes_event.csv")
led_to    = pd.read_csv(DATA / "rel_led_to.csv")
orig      = pd.read_csv(DATA / "rel_originated_from.csv")

# EventNode -> EventNode edges (time-ordered chain)
ev_ev = led_to[(led_to["src_label"] == "EventNode") &
               (led_to["dst_label"] == "EventNode")][["src","dst"]]

# EventNode -> Accident edges (chain terminates at accident)
ev_acc = led_to[(led_to["src_label"] == "EventNode") &
                (led_to["dst_label"] == "Accident")][["src","dst"]]

# Build successor map
successors = defaultdict(list)
for _, row in ev_ev.iterrows():
    successors[row["dst"]].append(row["src"])   # dst is earlier in chain

# Find chain roots (EventNodes that are not destinations of any ev→ev edge)
all_ev_ids = set(events["id"])
ev_ev_dsts = set(ev_ev["dst"])
ev_ev_srcs = set(ev_ev["src"])

# Root = appears as src but not as dst in EventNode->EventNode
# i.e., the LAST event in the chain (leads to accident)
# Actually let's trace chains from accident backwards

# Map accident → connected EventNodes via LED_TO
acc_to_events = defaultdict(set)
for _, row in ev_acc.iterrows():
    acc_to_events[row["dst"]].add(row["src"])

# Also via ORIGINATED_FROM (EventNode → Accident)
orig_ev_acc = orig[(orig["src_label"] == "EventNode") &
                   (orig["dst_label"] == "Accident")][["src","dst"]]
for _, row in orig_ev_acc.iterrows():
    acc_to_events[row["dst"]].add(row["src"])

# For each accident, count how many EventNodes are associated
acc_type = accidents[["id","accident_type"]].set_index("id")

chain_stats = []
for acc_id, ev_set in acc_to_events.items():
    n_events = len(ev_set)
    if acc_id in acc_type.index:
        atype = acc_type.loc[acc_id, "accident_type"]
    else:
        atype = "Unknown"
    chain_stats.append({"accident_id": acc_id, "accident_type": atype,
                        "chain_length": n_events})

# Also count accidents with NO event chain
acc_with_chains = set(acc_to_events.keys())
for _, row in accidents.iterrows():
    if row["id"] not in acc_with_chains:
        chain_stats.append({"accident_id": row["id"],
                            "accident_type": row["accident_type"],
                            "chain_length": 0})

chain_df = pd.DataFrame(chain_stats)
chain_df.to_csv(RESULTS / "R005_chain_stats.csv", index=False)

# ── Figure 1: chain length distribution ───────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Histogram (exclude 0s for clarity in left plot)
nonzero = chain_df[chain_df["chain_length"] > 0]["chain_length"]
clip = 20  # truncate display at 20 for readability
clipped = nonzero.clip(upper=clip)
axes[0].hist(clipped, bins=range(1, clip+2), color="steelblue", alpha=0.8, edgecolor="white")
axes[0].set_xlabel("Event Chain Length (# EventNodes per accident)", fontsize=11)
axes[0].set_ylabel("Number of Accidents", fontsize=11)
axes[0].set_title(f"Event Chain Length Distribution\n(accidents with ≥1 event node; chains >{clip} grouped into last bin)",
                  fontsize=10)
axes[0].axvline(nonzero.mean(), color="red", linestyle="--", label=f"Mean={nonzero.mean():.1f}")
axes[0].axvline(nonzero.median(), color="orange", linestyle="--", label=f"Median={nonzero.median():.0f}")
n_long = int((nonzero > clip).sum())
axes[0].text(clip * 0.65, axes[0].get_ylim()[1] * 0.85 if axes[0].get_ylim()[1] > 0 else 10,
             f"{n_long} accidents\nhave chain>{clip}", fontsize=8, color="gray", ha="center")
axes[0].legend(fontsize=9)

# Mean chain length by accident type (top 10)
top10 = accidents["accident_type"].value_counts().head(10).index.tolist()
type_stats = (chain_df[chain_df["accident_type"].isin(top10)]
              .groupby("accident_type")["chain_length"]
              .agg(["mean","median","count"])
              .sort_values("mean", ascending=True))
axes[1].barh(type_stats.index, type_stats["mean"], color="coral", alpha=0.85)
for i, (idx, row) in enumerate(type_stats.iterrows()):
    axes[1].text(row["mean"] + 0.05, i, f'{row["mean"]:.1f}', va="center", fontsize=8)
axes[1].set_xlabel("Mean Event Chain Length", fontsize=11)
axes[1].set_title("Mean Event Chain Length by Accident Type\n(top 10 types)", fontsize=11)

plt.suptitle("Maritime Accident Event Chain Analysis", fontsize=13, y=1.01)
plt.tight_layout()
plt.savefig(RESULTS / "R005_chain_length_dist.png", dpi=300, bbox_inches="tight")
plt.close()

# Summary stats
summary = {
    "accidents_with_chains": int((chain_df["chain_length"] > 0).sum()),
    "accidents_no_chains": int((chain_df["chain_length"] == 0).sum()),
    "total_ev_ev_edges": len(ev_ev),
    "mean_chain_length": round(float(nonzero.mean()), 2),
    "median_chain_length": float(nonzero.median()),
    "max_chain_length": int(nonzero.max()),
    "by_type": type_stats[["mean","count"]].round(2).to_dict()
}
with open(RESULTS / "R005_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print(f"[R005] DONE: {summary['accidents_with_chains']} accidents have event chains, "
      f"mean length={summary['mean_chain_length']}, max={summary['max_chain_length']}")
print(f"  EventNode->EventNode edges: {summary['total_ev_ev_edges']}")
print("\nMean chain length by type:")
for atype, row in type_stats.sort_values("mean", ascending=False).iterrows():
    print(f"  {atype:<25} mean={row['mean']:.1f}  n={int(row['count'])}")
