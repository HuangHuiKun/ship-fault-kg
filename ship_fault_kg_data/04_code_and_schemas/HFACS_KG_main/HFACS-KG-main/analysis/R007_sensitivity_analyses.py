"""R007 — Sensitivity Analyses for Rebuttal (R2-C5)

Three sensitivity analyses on existing KG exports (no new LLM calls):
  SA1: alternative semantic grouping schemes (collapse / split / drop-catchall)
  SA2: bootstrap 95% CIs on type x category heatmap percentages
  SA3: Monte Carlo precision perturbation (drop 35% factors per report)
       and report rank stability of top-K categories.

Outputs go to results/R007_*.{csv,json,png}.
"""
import re
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import spearmanr

DATA = Path("kg_export")
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)
SEED = 20260530
rng = np.random.default_rng(SEED)

# ── Categories (canonical) ───────────────────────────────────────────────
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
    ("Other / Unclassified", r".+"),
]
OTHER = "Other / Unclassified"

def classify(name: str) -> str:
    n = name.lower()
    for label, pattern in CATEGORIES:
        if re.search(pattern, n, re.IGNORECASE):
            return label
    return OTHER

# ── Load data ────────────────────────────────────────────────────────────
hfacs = pd.read_csv(DATA / "nodes_hfacs_factor.csv")
accidents = pd.read_csv(DATA / "nodes_accident.csv")
orig = pd.read_csv(DATA / "rel_originated_from.csv")
hfacs["category"] = hfacs["name"].apply(classify)
print(f"Loaded {len(hfacs)} factors, {len(accidents)} accidents")

baseline = hfacs["category"].value_counts()
baseline_no_other = baseline.drop(OTHER)
print(f"  Classified pct: {(1 - baseline[OTHER]/baseline.sum())*100:.1f}%")
print(f"  Top-5 categories: {list(baseline_no_other.head(5).index)}")

# ============================================================================
# SA1 — Alternative grouping robustness
# ============================================================================
print("\n=== SA1: Alternative grouping schemes ===")
sa1 = {}

# (a) Drop catch-all and compare ranking of named categories
counts_no_other = baseline.drop(OTHER)
sa1["a_top5_categories_unchanged"] = list(counts_no_other.head(5).index)
sa1["a_classified_pct_baseline"] = round(counts_no_other.sum() / baseline.sum() * 100, 2)
print(f"  (a) Drop 'Other'  Top-5: {sa1['a_top5_categories_unchanged'][:3]}...")

# (b) Merge top-3 categories into one macro; rank-correlate residual categories
top3 = baseline_no_other.head(3).index.tolist()
sa1["b_merged_top3"] = top3
merged_series = hfacs["category"].replace({c: "Macro_Top3" for c in top3})
counts_b = merged_series.value_counts()
non_top3_base = baseline_no_other.drop(top3)
non_top3_alt = counts_b.drop(["Macro_Top3", OTHER], errors="ignore").loc[non_top3_base.index]
rho_b, p_b = spearmanr(non_top3_base.rank(ascending=False),
                       non_top3_alt.rank(ascending=False))
sa1["b_residual_spearman_rho"] = float(rho_b)
sa1["b_residual_spearman_p"] = float(p_b)
print(f"  (b) Merge top-3 -> residual ranking Spearman rho={rho_b:.3f}, p={p_b:.2e}")

# (c) Split Procedures & SMS into 'Procedures' and 'SMS'
def reclassify_split(name):
    n = name.lower()
    if re.search(r"\bSMS\b|safety management system|ISM", name, re.IGNORECASE):
        return "SMS_only"
    if re.search(r"procedure|protocol|checklist|standing order|permit.*work",
                 n, re.IGNORECASE):
        return "Procedures_only"
    return classify(name)
hfacs["cat_split"] = hfacs["name"].apply(reclassify_split)
counts_c = hfacs["cat_split"].value_counts()
sa1["c_procedures_only_count"] = int(counts_c.get("Procedures_only", 0))
sa1["c_SMS_only_count"] = int(counts_c.get("SMS_only", 0))
# Compare residual ranking
residual_cats = baseline_no_other.drop("Procedures & SMS").index
common_c = residual_cats.intersection(counts_c.index)
rho_c, p_c = spearmanr(baseline_no_other.loc[common_c].rank(ascending=False),
                       counts_c.loc[common_c].rank(ascending=False))
sa1["c_residual_spearman_rho"] = float(rho_c)
sa1["c_residual_spearman_p"] = float(p_c)
print(f"  (c) Split Procedures vs SMS -> residual rho={rho_c:.3f}, p={p_c:.2e}")
print(f"      Procedures only: {sa1['c_procedures_only_count']}, "
      f"SMS only: {sa1['c_SMS_only_count']}")

# (d) Drop smallest 5 categories (consolidate into Other)
smallest5 = baseline_no_other.tail(5).index.tolist()
sa1["d_smallest5_dropped"] = smallest5
merged_d = hfacs["category"].replace({c: OTHER for c in smallest5})
counts_d = merged_d.value_counts().drop(OTHER)
common_d = baseline_no_other.drop(smallest5).index.intersection(counts_d.index)
rho_d, p_d = spearmanr(baseline_no_other.loc[common_d].rank(ascending=False),
                       counts_d.loc[common_d].rank(ascending=False))
sa1["d_residual_spearman_rho"] = float(rho_d)
sa1["d_residual_spearman_p"] = float(p_d)
print(f"  (d) Drop smallest 5 -> residual rho={rho_d:.3f}, p={p_d:.2e}")

with open(RESULTS / "R007_SA1_alt_grouping.json", "w") as f:
    json.dump(sa1, f, indent=2)
print(f"  -> saved R007_SA1_alt_grouping.json")

# ============================================================================
# SA2 — Bootstrap 95% CIs on the type x category heatmap
# Method: at each iteration, resample reports with replacement within each
# accident type, then recompute the (% of reports of that type with at least
# one factor in category c) statistic. Report 95% percentile CIs.
# ============================================================================
print("\n=== SA2: Bootstrap 95% CIs on type x category heatmap ===")

# Build the report x category indicator matrix.  Approach: each HFACS factor
# carries a source_file pointer (the originating PDF report); join factors to
# accidents via that pointer (a single accident may map to multiple Accident
# nodes when an incident records several distinct events, but the underlying
# report is unique).
src_to_type = (accidents.drop_duplicates("source_file")
               .set_index("source_file")["accident_type"])
hfacs_typed = hfacs.copy()
hfacs_typed["accident_type"] = hfacs_typed["source_file"].map(src_to_type)
hfacs_typed = hfacs_typed.dropna(subset=["accident_type"])
print(f"  Joined factors: {len(hfacs_typed)} / {len(hfacs)} "
      f"({len(hfacs_typed)/len(hfacs)*100:.1f}%)")
# Aggregate to source_file (report) x category indicator
report_cat = (hfacs_typed.groupby(["source_file", "category"])
              .size().unstack(fill_value=0) > 0).astype(int)
# Drop the catch-all column
if OTHER in report_cat.columns:
    report_cat = report_cat.drop(columns=[OTHER])
report_cat["accident_type"] = src_to_type.reindex(report_cat.index)
report_cat = report_cat.dropna(subset=["accident_type"])
print(f"  Indicator matrix: {report_cat.shape[0]} reports x {report_cat.shape[1]-1} categories")

# Top-10 accident types and top-10 categories by mean prevalence
top_types = accidents["accident_type"].value_counts().head(10).index.tolist()
cat_columns = [c for c in report_cat.columns if c != "accident_type"]
type_mean = (report_cat.groupby("accident_type")[cat_columns].mean() * 100)
overall_cat = type_mean.mean(axis=0).sort_values(ascending=False)
top_cats = overall_cat.head(10).index.tolist()

heatmap_base = type_mean.loc[top_types, top_cats].values

B = 1000
heatmap_boot = np.zeros((B, len(top_types), len(top_cats)))
reports_by_type = {t: report_cat[report_cat["accident_type"] == t].index.to_numpy()
                   for t in top_types}
for b in range(B):
    for ti, t in enumerate(top_types):
        idx = rng.choice(reports_by_type[t], size=len(reports_by_type[t]), replace=True)
        sub = report_cat.loc[idx, top_cats]
        heatmap_boot[b, ti, :] = sub.mean(axis=0).values * 100

ci_low = np.percentile(heatmap_boot, 2.5, axis=0)
ci_high = np.percentile(heatmap_boot, 97.5, axis=0)
ci_width = ci_high - ci_low
sa2_summary = {
    "median_ci_halfwidth_pct": float(np.median(ci_width) / 2),
    "mean_ci_halfwidth_pct": float(np.mean(ci_width) / 2),
    "p90_ci_halfwidth_pct": float(np.percentile(ci_width, 90) / 2),
    "n_cells": int(heatmap_base.size),
    "n_bootstrap": B,
    "seed": SEED,
    "top_types": top_types,
    "top_cats": top_cats,
}
print(f"  Median CI half-width:  {sa2_summary['median_ci_halfwidth_pct']:.2f} pp")
print(f"  Mean   CI half-width:  {sa2_summary['mean_ci_halfwidth_pct']:.2f} pp")
print(f"  P90    CI half-width:  {sa2_summary['p90_ci_halfwidth_pct']:.2f} pp")

# Persist full heatmap with CIs
rows = []
for ti, t in enumerate(top_types):
    for ci_i, c in enumerate(top_cats):
        rows.append({
            "accident_type": t, "category": c,
            "pct_base": round(float(heatmap_base[ti, ci_i]), 2),
            "pct_ci_low": round(float(ci_low[ti, ci_i]), 2),
            "pct_ci_high": round(float(ci_high[ti, ci_i]), 2),
        })
pd.DataFrame(rows).to_csv(RESULTS / "R007_SA2_heatmap_ci.csv", index=False)
with open(RESULTS / "R007_SA2_summary.json", "w") as f:
    json.dump(sa2_summary, f, indent=2)
print(f"  -> saved R007_SA2_heatmap_ci.csv, R007_SA2_summary.json")

# ============================================================================
# SA3 — Monte Carlo precision perturbation
# Drop 35% of factors per report at random (P=65%), 1000 trials.
# Report Spearman rho between baseline ranking and perturbed ranking,
# and the Jaccard overlap of the top-5 categories.
# ============================================================================
print("\n=== SA3: Monte Carlo precision perturbation (drop 35% factors/report) ===")
B3 = 1000
DROP = 0.35

baseline_rank = baseline_no_other.rank(ascending=False)
top5_base = set(baseline_no_other.head(5).index)
grouped_factor_idx = {k: v.index.to_numpy() for k, v in hfacs.groupby("source_file")}

rhos, top5_overlaps = [], []
for b in range(B3):
    keep_parts = []
    for src, idx_arr in grouped_factor_idx.items():
        n_keep = max(1, int(round(len(idx_arr) * (1 - DROP))))
        keep_parts.append(rng.choice(idx_arr, size=n_keep, replace=False))
    keep_idx = np.concatenate(keep_parts)
    sub = hfacs.loc[keep_idx]
    counts_b = sub["category"].value_counts().drop(OTHER, errors="ignore")
    common = baseline_rank.index.intersection(counts_b.index)
    rank_b = counts_b.loc[common].rank(ascending=False)
    rho_b, _ = spearmanr(baseline_rank.loc[common], rank_b)
    rhos.append(float(rho_b))
    top5_b = set(counts_b.head(5).index)
    top5_overlaps.append(
        len(top5_base & top5_b) / len(top5_base | top5_b))
sa3_summary = {
    "spearman_rho_mean": float(np.mean(rhos)),
    "spearman_rho_median": float(np.median(rhos)),
    "spearman_rho_p2_5": float(np.percentile(rhos, 2.5)),
    "spearman_rho_p97_5": float(np.percentile(rhos, 97.5)),
    "top5_jaccard_mean": float(np.mean(top5_overlaps)),
    "top5_jaccard_p2_5": float(np.percentile(top5_overlaps, 2.5)),
    "top5_baseline": list(top5_base),
    "n_trials": B3,
    "drop_rate": DROP,
    "seed": SEED,
}
print(f"  Spearman rho (baseline vs perturbed): mean={sa3_summary['spearman_rho_mean']:.3f}"
      f" 95% CI [{sa3_summary['spearman_rho_p2_5']:.3f}, "
      f"{sa3_summary['spearman_rho_p97_5']:.3f}]")
print(f"  Top-5 Jaccard overlap:  mean={sa3_summary['top5_jaccard_mean']:.3f}"
      f"  2.5th pct={sa3_summary['top5_jaccard_p2_5']:.3f}")

with open(RESULTS / "R007_SA3_perturbation.json", "w") as f:
    json.dump(sa3_summary, f, indent=2)
print(f"  -> saved R007_SA3_perturbation.json")

# ============================================================================
# Plot a simple summary figure
# ============================================================================
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
axes[0].hist(ci_width.flatten() / 2, bins=30, color="steelblue", edgecolor="white")
axes[0].axvline(np.median(ci_width) / 2, color="red", linestyle="--",
                label=f"Median = {np.median(ci_width)/2:.2f}pp")
axes[0].set_xlabel("95% CI half-width (percentage points)")
axes[0].set_ylabel("Number of (type, category) cells")
axes[0].set_title("SA2: Bootstrap CI half-widths\n(top-10 types x top-10 categories)")
axes[0].legend()

axes[1].hist(rhos, bins=30, color="darkorange", edgecolor="white")
axes[1].axvline(np.mean(rhos), color="red", linestyle="--",
                label=f"Mean = {np.mean(rhos):.3f}")
axes[1].set_xlabel("Spearman rho vs baseline ranking")
axes[1].set_ylabel("Number of trials")
axes[1].set_title(f"SA3: Rank stability under {int(DROP*100)}% factor removal\n"
                  f"({B3} Monte Carlo trials)")
axes[1].legend()
plt.tight_layout()
fig.savefig(RESULTS / "R007_sensitivity_summary.png", dpi=200)
print(f"  -> saved R007_sensitivity_summary.png")

print("\nAll sensitivity analyses complete.")
