"""R006 — Causal path analysis: HFACS factor → EventNode → Accident"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json
from pathlib import Path
from collections import defaultdict, Counter

DATA = Path("kg_export")
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

accidents = pd.read_csv(DATA / "nodes_accident.csv")
hfacs     = pd.read_csv(RESULTS / "R002b_hfacs_with_categories.csv")
events    = pd.read_csv(DATA / "nodes_event.csv")
led_to    = pd.read_csv(DATA / "rel_led_to.csv")

# Index maps
factor_cat  = dict(zip(hfacs["id"], hfacs["category"]))
acc_type    = dict(zip(accidents["id"], accidents["accident_type"]))
# source_file → accident_type (for 2-hop path analysis)
src_to_type = dict(zip(accidents["source_file"], accidents["accident_type"]))

# ── Pattern 1: Which HFACS categories most often initiate (LED_TO EventNode) ──
hfacs_to_event = led_to[(led_to["src_label"] == "HFACS_Factor") &
                         (led_to["dst_label"] == "EventNode")]
initiator_cats = hfacs_to_event["src"].map(factor_cat).value_counts()
initiator_cats = initiator_cats[initiator_cats.index != "Other / Unclassified"]

# ── Pattern 2: Which HFACS categories most directly cause accidents ────────────
hfacs_to_acc = led_to[(led_to["src_label"] == "HFACS_Factor") &
                       (led_to["dst_label"] == "Accident")]
direct_cats = hfacs_to_acc["src"].map(factor_cat).value_counts()
direct_cats = direct_cats[direct_cats.index != "Other / Unclassified"]

# via source_file join (most complete)
hfacs_with_type = hfacs[["id","category","source_file"]].copy()
hfacs_with_type["acc_type"] = hfacs_with_type["source_file"].map(src_to_type)
orig_cats = (hfacs_with_type[hfacs_with_type["category"] != "Other / Unclassified"]
             ["category"].value_counts())

# ── Pattern 3: 2-hop paths HFACS_cat → (via EventNode) → Accident type ────────
# Step A: HFACS → EventNode
hf_ev = hfacs_to_event[["src","dst"]].rename(columns={"src":"hf","dst":"ev"})
hf_ev["hf_cat"] = hf_ev["hf"].map(factor_cat)

# Step B: EventNode → Accident
ev_acc = led_to[(led_to["src_label"] == "EventNode") &
                 (led_to["dst_label"] == "Accident")][["src","dst"]]
ev_acc.columns = ["ev","acc"]
ev_acc["acc_type"] = ev_acc["acc"].map(acc_type)

paths_2hop = hf_ev.merge(ev_acc, on="ev", how="inner")

# Fallback: use source_file-based path if LED_TO paths are sparse
if len(paths_2hop) < 100:
    # Use category × acc_type via source_file
    paths_2hop = hfacs_with_type.dropna(subset=["acc_type"])[["category","acc_type"]]
    paths_2hop.columns = ["hf_cat","acc_type"]
    path_counts = (paths_2hop.groupby(["hf_cat","acc_type"]).size()
                   .reset_index(name="count")
                   .sort_values("count", ascending=False))
else:
    path_counts = (paths_2hop.groupby(["hf_cat","acc_type"]).size()
                   .reset_index(name="count")
                   .sort_values("count", ascending=False))

path_counts = path_counts[path_counts["hf_cat"] != "Other / Unclassified"]
path_counts.to_csv(RESULTS / "R006_causal_patterns.csv", index=False)

# ── Figure 1: Initiators vs direct causes comparison ─────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

top_init = initiator_cats.head(10)
axes[0].barh(top_init.index[::-1], top_init.values[::-1], color="steelblue", alpha=0.85)
axes[0].set_title("HFACS Categories: Initiating Event Chains\n(HFACS_Factor → EventNode)", fontsize=10)
axes[0].set_xlabel("Number of edges", fontsize=9)
for i, (idx, val) in enumerate(zip(top_init.index[::-1], top_init.values[::-1])):
    axes[0].text(val + 5, i, str(val), va="center", fontsize=8)

top_dir = orig_cats.head(10)
axes[1].barh(top_dir.index[::-1], top_dir.values[::-1], color="coral", alpha=0.85)
axes[1].set_title("HFACS Categories: Directly Originating Accidents\n(HFACS_Factor → Accident via ORIGINATED_FROM)", fontsize=10)
axes[1].set_xlabel("Number of edges", fontsize=9)
for i, (idx, val) in enumerate(zip(top_dir.index[::-1], top_dir.values[::-1])):
    axes[1].text(val + 5, i, str(val), va="center", fontsize=8)

plt.suptitle("Causal Role of HFACS Categories in Maritime Accidents", fontsize=12)
plt.tight_layout()
plt.savefig(RESULTS / "R006_causal_roles.png", dpi=300, bbox_inches="tight")
plt.close()

# ── Figure 2: Top 2-hop causal paths ─────────────────────────────────────────
top_paths = path_counts.head(20)
labels = [f"{r['hf_cat'][:30]}  →  {r['acc_type']}"
          for _, r in top_paths.iterrows()]
fig, ax = plt.subplots(figsize=(13, 7))
bars = ax.barh(labels[::-1], top_paths["count"].values[::-1], color="mediumseagreen", alpha=0.85)
ax.set_xlabel("Path frequency (number of HFACS→Event→Accident chains)", fontsize=10)
ax.set_title("Top 20 Two-Hop Causal Paths\n(HFACS Category → EventNode → Accident Type)", fontsize=11)
for bar, val in zip(bars, top_paths["count"].values[::-1]):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            str(val), va="center", fontsize=8)
plt.tight_layout()
plt.savefig(RESULTS / "R006_top_causal_paths.png", dpi=300, bbox_inches="tight")
plt.close()

summary = {
    "total_2hop_paths": len(paths_2hop),
    "unique_path_types": len(path_counts),
    "top_initiator_category": str(initiator_cats.index[0]),
    "top_direct_cause_category": str(orig_cats.index[0]),
    "top10_paths": top_paths.head(10).to_dict("records")
}
with open(RESULTS / "R006_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print(f"[R006] DONE: {summary['total_2hop_paths']} two-hop causal paths found "
      f"({summary['unique_path_types']} unique pattern types)")
print(f"  Top initiator category: {summary['top_initiator_category']}")
print(f"  Top direct cause category: {summary['top_direct_cause_category']}")
print("\nTop 10 causal paths (HFACS category → Accident type):")
for r in summary["top10_paths"]:
    print(f"  {r['hf_cat']:<35} -> {r['acc_type']:<20} ({r['count']})")
