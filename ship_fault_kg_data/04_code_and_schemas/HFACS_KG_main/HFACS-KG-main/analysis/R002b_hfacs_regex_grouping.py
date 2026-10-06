"""R002b — HFACS factor semantic grouping via keyword regex"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import re, json
from pathlib import Path
from collections import Counter

DATA = Path("kg_export")
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

# ── Category definitions (ordered: first match wins) ──────────────────────────
CATEGORIES = [
    ("Situational Awareness",
     r"situational awareness|lookout|watchkeeping|watch.keep|vigilance|"
     r"monitor.alarm|fail.*notice|fail.*detect|awareness|attention|"
     r"maintain.*watch|proper watch|bridge watch"),

    ("Navigation & Passage Planning",
     r"navigat|passage plan|chart|ECDIS|radar|GPS|AIS|course|speed|"
     r"grounding|collision avoidance|lookout|pilotage|pilot.*error|"
     r"passage.*plan|route plan|chart correction"),

    ("Training & Competency",
     r"training|competenc|qualification|certif|familiaris|familiariz|"
     r"skill|experience|knowledge|inexperienc|inadequate.*train|"
     r"lack.*train|insufficient.*train|lack.*competenc|lack.*skill"),

    ("Communication",
     r"communicat|VHF|language|phraseolog|hand signal|MAYDAY|"
     r"cross.check|verification|briefing|information.*shar|"
     r"failure.*communicat|lack.*communicat|ambiguous"),

    ("Fatigue & Workload",
     r"fatig|inattention|fatigue|rest period|work.*hour|overwork|"
     r"sleep|rest|workload|pressure.*expedit|stress|mental state"),

    ("Bridge & Crew Resource Management",
     r"BRM|bridge resource|crew resource|resource management|"
     r"team.*work|teamwork|bridge team|cross.check|CRM|"
     r"supervision.*bridge|bridge.*supervis"),

    ("Procedures & SMS",
     r"procedure|SMS|protocol|work permit|risk assessment|ISM|"
     r"checklist|standing order|permit.*work|safety management system|"
     r"lack.*procedure|absent.*procedure|no.*procedure|deficient.*SMS|"
     r"inadequate.*SMS|fail.*follow.*procedure|non.compliance"),

    ("Supervision & Oversight",
     r"supervis|oversight|monitoring|lack.*supervis|inadequate.*supervis|"
     r"failure.*supervis|insufficient.*supervis|management.*oversight|"
     r"organizational.*oversight"),

    ("Maintenance & Equipment",
     r"maintenanc|defect|repair|alarm.*disabl|equipment.*fail|"
     r"malfunction|out.*service|broken|worn|deteriorat|"
     r"failure.*maintain|fail.*repair|known.*defect"),

    ("Emergency Response",
     r"emergency.*response|rescue|abandon|evacuat|lifeboat|"
     r"emergency.*coordinat|delayed.*response|fail.*activat.*alarm|"
     r"MAYDAY.*delay|emergency.*communicat|emergency.*drill"),

    ("Manning & Crewing",
     r"manning|crew.*compos|under.staff|overmanning|minimum.*safe.*manning|"
     r"crew.*certif|crew.*qualif|staffing|short.*hand"),

    ("Enclosed Space & Atmosphere",
     r"enclosed space|atmosphere|oxygen|toxic|gas|EEBD|"
     r"tank.*entry|confined space|inert|asphyxia"),

    ("Fire & Explosion Safety",
     r"fire|explosion|flammable|ignition|extinguish|hotwork|"
     r"hot.work|fire.*detect|fire.*suppres|combustible"),

    ("Cargo & Lifting Operations",
     r"cargo|crane|lift|load|rigging|mooring|securing|"
     r"stow|ballast|stability.*cargo|cargo.*shift"),

    ("PPE & Personal Safety",
     r"PPE|lifejacket|harness|life.jacket|protective.*equipment|"
     r"fall.*arrest|fall.*prevent|safety.*equipment"),

    ("Organizational & Regulatory",
     r"organizat|regulat|compli|enforce|authority|flag.*state|"
     r"port.*state|ISM.*code|SOLAS|MLC|convention|policy|"
     r"corporate|company.*policy|management.*system"),

    ("Safety Culture & Pressure",
     r"safety.*cultur|pressure|commercial.*pressure|cost.*driven|"
     r"production.*pressure|normaliz.*devian|risk.*accept|"
     r"overrid.*safety|priorit.*commercial"),

    ("Voyage & Weather Planning",
     r"voyage plan|passage.*plan|weather.*risk|weather.*assess|"
     r"departure.*plan|risk.*departure|Antarctic|high.risk.*area|"
     r"pre.departure|gale warning|meteorolog|weather.*condition|"
     r"failure.*assess.*weather|failure.*plan|deficient.*voyage|"
     r"inadequate.*voyage|absence.*notice.*mariner|Notice.*Mariner"),

    ("Human Error & Decision Making",
     r"misidentif|misjudg|misinterpret|misappl|miscalcul|"
     r"assumption.based|complacen|distract|inattentive|"
     r"wrong.*valve|wrong.*helm|incorrect.*assessment|"
     r"error.*judgment|failure.*anticipate|failure.*appreciate|"
     r"failure.*recognize|delayed.*recogn|delayed.*evasive|"
     r"impatien|undue.*rush|routine.*work.*complacen|"
     r"over.confiden|poor.*judgment|poor.*decision"),

    ("Vessel Design & Stability",
     r"design|stability|watertight|subdivision|structural|"
     r"ergonomic|lack.*guard|no.*propeller.*guard|"
     r"inadequate.*stability|stability.*standard|"
     r"topside.*weight|excessive.*weight|freeboard|"
     r"lack.*watertight|absence.*watertight|code.*practice"),

    ("Medical & Physical Condition",
     r"alcohol|drug|intoxicat|impair|disease|illness|medical|"
     r"health|fatigue.*medical|dizziness|ischaemic|diabetes|"
     r"blister|injury.*physical|physical.*condition"),

    ("Specific Operational Failures",
     r"failure to verify|failure to use|failure to deploy|"
     r"failure to stop|failure to notify|failure to monitor|"
     r"failure to update|failure to perform|failure to sound|"
     r"failure to cool|failure to integrate|failure to resolve|"
     r"failure to identify|failure to activate|failure to assess|"
     r"wrong valve|incorrect valve|valve.*opened|"
     r"failure.*helm|failure.*anchor|failure.*signal"),

    ("Lessons Learned & Documentation",
     r"record.keeping|logbook|documentation|lessons.*learned|"
     r"fleet.wide|disseminat|feedback|incident.*report|"
     r"near.miss.*report|VDR|voyage.*data.*recorder|"
     r"lack.*VDR|absence.*VDR|poor.*record"),

    ("Resource Allocation & Planning",
     r"resource.*allocat|inadequate.*resource|insufficient.*resource|"
     r"poor.*utiliz|underuse|under.utiliz|"
     r"cross.departmental|fleet.*resource|"
     r"inadequate.*company|company.*PMS|PMS"),

    ("Violation & Non-compliance",
     r"violat|unauthoris|unauthorized|non.complian|breach|"
     r"disregard|ignor.*rule|ignor.*protocol|bypass|"
     r"working alone|single.handed.*without|unapproved|"
     r"improper.*use|misuse"),

    ("Risk Perception & Normalization of Deviation",
     r"normali.*deviation|normali.*hazard|risk.*perception|"
     r"over.reliance|overconfiden|over.confident|tolerance.*risk|"
     r"historical.*tolerance|years.*routine|complacen.*routine|"
     r"lack.*risk.*percept|tendency.*normali|acceptable.*risk"),

    ("Inter-vessel & Team Coordination",
     r"coordinat|lack.*coordinat|no.*coordinat|pre.transfer|"
     r"between.*vessel|between.*team|uncoordinat|"
     r"opening.*meeting|stevedore.*meet|no.*briefing|"
     r"absence.*meeting|failure.*call.*master|failure.*notify.*master|"
     r"failure.*seek.*clarif|failure.*inform"),

    ("Physical Hazard & Immediate Cause",
     r"struck.*wave|tripping|caught.*rope|caught.*line|"
     r"entangled|slipped|fell|fall.*overboard|"
     r"working.*height|work.*alone.*height|"
     r"guardrail|open.*hatch|unsecured|stove.*lit|"
     r"no.*anchor|anchor.*fitted|wired.open|cap.*off"),

    ("Contingency & Emergency Planning",
     r"contingency|emergency.*plan|DPA|designated.*person|"
     r"CO2.*not.*activat|CO2.*activat.*uncertain|"
     r"EPIRB|emergency.*generator|abandon.*ship.*drill|"
     r"muster.*drill|lack.*emergency.*plan"),

    ("Other / Unclassified", r".+"),   # catch-all
]

def classify(name: str) -> str:
    n = name.lower()
    for label, pattern in CATEGORIES:
        if re.search(pattern, n, re.IGNORECASE):
            return label
    return "Other / Unclassified"

# ── Load and classify ──────────────────────────────────────────────────────────
hfacs = pd.read_csv(DATA / "nodes_hfacs_factor.csv")
accidents = pd.read_csv(DATA / "nodes_accident.csv")
n_accidents = len(accidents)

hfacs["category"] = hfacs["name"].apply(classify)

# Category frequency
cat_freq = hfacs["category"].value_counts().reset_index()
cat_freq.columns = ["category", "count"]
cat_freq["pct_accidents"] = (cat_freq["count"] / n_accidents * 100).round(1)
cat_freq["pct_factors"] = (cat_freq["count"] / len(hfacs) * 100).round(1)

print("=== HFACS Category Distribution ===")
print(cat_freq.to_string(index=False))
print(f"\nTotal factors: {len(hfacs)}, Classified (non-Other): "
      f"{len(hfacs[hfacs['category'] != 'Other / Unclassified'])} "
      f"({len(hfacs[hfacs['category'] != 'Other / Unclassified'])/len(hfacs)*100:.1f}%)")

# Save CSV
cat_freq.to_csv(RESULTS / "R002b_hfacs_categories.csv", index=False)

# ── Figure 1: category bar chart ───────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 8))
colors = plt.cm.tab20.colors
classified = cat_freq[cat_freq["category"] != "Other / Unclassified"].copy()
other_row  = cat_freq[cat_freq["category"] == "Other / Unclassified"].copy()
plot_data = pd.concat([classified, other_row], ignore_index=True)
bar_colors = list(colors[:len(classified)]) + ["#cccccc"]
bars = ax.barh(plot_data["category"], plot_data["count"],
               color=bar_colors, alpha=0.85)
ax.invert_yaxis()
ax.set_xlabel("Number of HFACS Factor Instances", fontsize=11)
ax.set_title("Distribution of HFACS Factors by Category\n(Maritime Accident Knowledge Graph, n=1,165 accidents)",
             fontsize=12)
for bar, (_, row) in zip(bars, plot_data.iterrows()):
    ax.text(bar.get_width() + 20, bar.get_y() + bar.get_height()/2,
            f"{row['count']} ({row['pct_accidents']:.0f}%)", va="center", fontsize=8)
plt.tight_layout()
plt.savefig(RESULTS / "R002b_hfacs_categories.png", dpi=300, bbox_inches="tight")
plt.close()

# ── Figure 2: per accident-type breakdown (top 8 types) ───────────────────────
orig = pd.read_csv(DATA / "rel_originated_from.csv")
# accident nodes → accident_type
acc_type = accidents[["id","accident_type"]].rename(columns={"id":"dst"})
orig_typed = orig.merge(acc_type, on="dst", how="left")
# factor nodes → category
factor_cat = hfacs[["id","category"]].rename(columns={"id":"src"})
orig_typed = orig_typed.merge(factor_cat, on="src", how="left")

top8_types = accidents["accident_type"].value_counts().head(8).index.tolist()
matrix = (
    orig_typed[orig_typed["accident_type"].isin(top8_types)]
    .groupby(["accident_type","category"])
    .size()
    .unstack(fill_value=0)
)
# Normalise rows to percentage
matrix_pct = matrix.div(matrix.sum(axis=1), axis=0) * 100
# Keep top 10 categories by total
top_cats = cat_freq[cat_freq["category"] != "Other / Unclassified"]["category"].head(10).tolist()
matrix_pct = matrix_pct[[c for c in top_cats if c in matrix_pct.columns]]

fig, ax = plt.subplots(figsize=(14, 6))
im = ax.imshow(matrix_pct.values, aspect="auto", cmap="YlOrRd")
ax.set_xticks(range(len(matrix_pct.columns)))
ax.set_xticklabels(matrix_pct.columns, rotation=35, ha="right", fontsize=8)
ax.set_yticks(range(len(matrix_pct.index)))
ax.set_yticklabels(matrix_pct.index, fontsize=9)
plt.colorbar(im, ax=ax, label="% of HFACS factors for accident type")
ax.set_title("HFACS Category Patterns by Accident Type (%)", fontsize=12)
for i in range(len(matrix_pct.index)):
    for j in range(len(matrix_pct.columns)):
        val = matrix_pct.values[i, j]
        if val > 0:
            ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                    fontsize=7, color="black" if val < 30 else "white")
plt.tight_layout()
plt.savefig(RESULTS / "R002b_hfacs_type_heatmap.png", dpi=300, bbox_inches="tight")
plt.close()

# Save full hfacs with categories
hfacs.to_csv(RESULTS / "R002b_hfacs_with_categories.csv", index=False)

summary = {
    "total_factors": len(hfacs),
    "classified_pct": round(len(hfacs[hfacs["category"] != "Other / Unclassified"]) / len(hfacs) * 100, 1),
    "top5_categories": cat_freq.head(5)[["category","count","pct_accidents"]].to_dict("records")
}
with open(RESULTS / "R002b_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print(f"\n[R002b] DONE: {summary['classified_pct']}% factors classified into named categories")
print(f"Top 3: {', '.join(r['category'] for r in summary['top5_categories'][:3])}")
