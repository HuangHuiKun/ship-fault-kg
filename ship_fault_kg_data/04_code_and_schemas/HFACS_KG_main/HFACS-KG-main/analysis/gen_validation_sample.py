"""Generate stratified validation sample + annotation spreadsheet"""
import pandas as pd
import random, json
from pathlib import Path

random.seed(2026)
DATA    = Path("kg_export")
RESULTS = Path("results")

acc  = pd.read_csv(DATA / "nodes_accident.csv")
hf   = pd.read_csv(RESULTS / "R002b_hfacs_with_categories.csv")
ev   = pd.read_csv(DATA / "nodes_event.csv")
led  = pd.read_csv(DATA / "rel_led_to.csv")

# ── Stratified sample: ~50 reports, proportional to top-10 types ─────────────
TARGET = 50
top_types = acc["accident_type"].value_counts().head(10)
total_top  = top_types.sum()

sampled_ids = []
for atype, count in top_types.items():
    n = max(2, round(TARGET * count / total_top))
    pool = acc[acc["accident_type"] == atype]["source_file"].tolist()
    sampled_ids += random.sample(pool, min(n, len(pool)))

# De-duplicate and trim to ~50
sampled_ids = list(dict.fromkeys(sampled_ids))[:TARGET]
print(f"Sampled {len(sampled_ids)} reports")

# ── Build annotation rows ─────────────────────────────────────────────────────
rows = []
for sf in sampled_ids:
    acc_row  = acc[acc["source_file"] == sf].iloc[0]
    factors  = hf[hf["source_file"] == sf][["name","category"]].reset_index(drop=True)
    events   = ev[ev["source_file"] == sf]["name"].tolist()

    for i, (_, frow) in enumerate(factors.iterrows()):
        rows.append({
            "report_id":       sf.replace(".pdf",""),
            "accident_type":   acc_row["accident_type"],
            "accident_name":   acc_row["name"],
            "factor_index":    i + 1,
            "total_factors":   len(factors),
            "hfacs_factor":    frow["name"],
            "auto_category":   frow["category"],
            # ── annotation columns (human fills these) ──
            "correctness":     "",   # Correct / Partial / Wrong
            "correct_category":"",  # fill if auto_category is wrong
            "notes":           "",
        })

df = pd.DataFrame(rows)
out_path = RESULTS / "validation_annotation_sheet.xlsx"

# Add summary sheet
with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Annotations", index=False)

    # Summary: one row per report
    summary = (acc[acc["source_file"].isin(sampled_ids)]
               [["source_file","accident_type","name"]]
               .copy())
    summary["n_factors"] = summary["source_file"].map(
        hf.groupby("source_file").size())
    ev_counts = ev.groupby("source_file").size()
    summary["n_events_extracted"] = summary["source_file"].map(ev_counts).fillna(0).astype(int)
    summary = summary.drop(columns=["n_events_extracted"], errors="ignore")  # will re-add below
    ev_counts = ev.groupby("source_file").size()
    summary["n_events_extracted"] = summary["source_file"].map(ev_counts).fillna(0).astype(int)
    summary.columns = ["source_file","accident_type","accident_name",
                        "n_factors_extracted","n_events_extracted"]
    summary.to_excel(writer, sheet_name="Sample_Overview", index=False)

    # Guidelines sheet
    guide = pd.DataFrame({
        "Annotation Guide": [
            "=== HOW TO ANNOTATE ===",
            "",
            "For each HFACS factor row, fill in the 'correctness' column:",
            "",
            "  Correct  : The factor accurately reflects a finding stated or implied in the report.",
            "             The wording may differ but the meaning is correct.",
            "",
            "  Partial  : The factor is partially right — either too vague, too specific,",
            "             or mixes two separate issues into one.",
            "",
            "  Wrong    : The factor is hallucinated, irrelevant, or contradicts the report.",
            "",
            "=== RECALL ESTIMATION ===",
            "After reviewing all extracted factors for a report, add a row at the bottom",
            "of that report's section with factor_index='MISSED' and write any important",
            "causal factors the LLM missed in the 'notes' column.",
            "",
            "=== CATEGORY CHECK ===",
            "If the auto_category is clearly wrong, fill in 'correct_category'.",
            "Otherwise leave blank.",
            "",
            "=== TIPS ===",
            "- Focus on whether the SUBSTANCE is correct, not exact wording.",
            "- 'Partial' is acceptable — count it as 0.5 in final scoring.",
            "- Aim for ~5-10 min per report. Don't over-analyse.",
        ]
    })
    guide.to_excel(writer, sheet_name="Guidelines", index=False)

print(f"Saved: {out_path}")
print(f"Total rows to annotate: {len(df)}")
print(f"\nSample breakdown:")
print(df.drop_duplicates("report_id")["accident_type"].value_counts().to_string())
