"""Compute Precision / Recall / F1 from validation results."""
import json, pandas as pd
from pathlib import Path

RESULTS = Path("results")

records = []
with open(RESULTS / "validation_results.jsonl", encoding="utf-8") as f:
    for line in f:
        try:
            records.append(json.loads(line))
        except:
            pass

rows = []
for r in records:
    if "error" in r:
        continue
    evals = r.get("evaluations", [])
    if not evals or not isinstance(evals[0], dict):
        continue
    n = len(evals)
    if n == 0:
        continue
    correct  = sum(1   for e in evals if e["judgment"] == "Correct")
    partial  = sum(0.5 for e in evals if e["judgment"] == "Partial")
    wrong    = sum(1   for e in evals if e["judgment"] == "Wrong")

    precision = (correct + partial) / n
    estimated_total = r.get("estimated_total", n)
    recall = (correct + partial) / estimated_total if estimated_total > 0 else 0

    rows.append({
        "source_file":   r["source_file"],
        "accident_type": r["accident_type"],
        "n_extracted":   n,
        "correct":       correct,
        "partial":       int(partial * 2),
        "wrong":         wrong,
        "precision":     round(precision, 3),
        "est_total":     estimated_total,
        "recall":        round(recall, 3),
    })

df = pd.DataFrame(rows)
df.to_csv(RESULTS / "validation_per_report.csv", index=False)

# Overall metrics
total_extracted = df["n_extracted"].sum()
total_correct   = df["correct"].sum() + df["partial"].sum() * 0.5
total_est       = df["est_total"].sum()

overall_precision = total_correct / total_extracted
overall_recall    = total_correct / total_est
overall_f1        = 2 * overall_precision * overall_recall / (overall_precision + overall_recall)

print("=" * 50)
print(f"Reports evaluated : {len(df)}")
print(f"Factors extracted : {int(total_extracted)}")
print(f"Precision         : {overall_precision:.3f}  ({overall_precision*100:.1f}%)")
print(f"Recall            : {overall_recall:.3f}  ({overall_recall*100:.1f}%)")
print(f"F1                : {overall_f1:.3f}  ({overall_f1*100:.1f}%)")
print("=" * 50)

print("\nBy accident type:")
by_type = df.groupby("accident_type").agg(
    reports=("source_file","count"),
    precision=("precision","mean"),
    recall=("recall","mean"),
).round(3)
print(by_type.to_string())

summary = {
    "n_reports": len(df),
    "n_factors": int(total_extracted),
    "precision": round(overall_precision, 3),
    "recall":    round(overall_recall, 3),
    "f1":        round(overall_f1, 3),
    "by_type":   by_type.to_dict()
}
with open(RESULTS / "validation_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("\nSaved: results/validation_summary.json")
