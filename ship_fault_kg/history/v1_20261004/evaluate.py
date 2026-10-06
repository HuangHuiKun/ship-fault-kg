"""Small, transparent development evaluation of graph retrieval.

These labels were written from the same source set and are a smoke test, not
an independent expert assessment or generalisation benchmark.
"""

from __future__ import annotations

import json
from pathlib import Path

from retrieve import Retriever


HERE = Path(__file__).resolve().parent


def main() -> None:
    retriever = Retriever()
    questions = json.loads((HERE / "eval_queries.json").read_text(encoding="utf-8"))
    details = []
    case_rr = []
    fact_recall_5 = []
    fact_recall_10 = []
    fact_precision_5 = []
    dataset_hits = []
    coverage_hits = []
    for item in questions:
        result = retriever.search(item["query"], top_facts=10)
        row = {"id": item["id"], "query": item["query"],
               "top_case": result["cases"][0]["case_id"] if result["cases"] else None,
               "coverage": result["coverage"]}
        if "case_id" in item:
            ranks = [x["case_id"] for x in result["cases"]]
            rr = 1 / (ranks.index(item["case_id"]) + 1) if item["case_id"] in ranks else 0
            case_rr.append(rr)
            ranked = [(f["case_id"], f["subject"], f["relation"], f["object"])
                      for f in result["facts"]]
            gold = {(item["case_id"], *f) for f in item["gold"]}
            n5 = len(gold.intersection(ranked[:5]))
            n10 = len(gold.intersection(ranked[:10]))
            fact_recall_5.append(n5 / len(gold))
            fact_recall_10.append(n10 / len(gold))
            fact_precision_5.append(n5 / 5)
            row.update({"case_rr": rr, "gold_count": len(gold), "fact_hits_5": n5,
                        "fact_hits_10": n10, "recall_at_5": n5 / len(gold),
                        "recall_at_10": n10 / len(gold), "precision_at_5": n5 / 5})
        if "dataset_run" in item:
            hit = any(m["run_file"] == item["dataset_run"] and
                      m["data_rows"] == item["expected_rows"] for m in result["dataset_matches"])
            dataset_hits.append(hit)
            row["dataset_hit"] = hit
        if "coverage" in item:
            hit = result["coverage"] == item["coverage"]
            coverage_hits.append(hit)
            row["coverage_hit"] = hit
        details.append(row)

    summary = {
        "question_count": len(questions), "case_question_count": len(case_rr),
        "case_mrr_at_3": round(sum(case_rr) / len(case_rr), 4),
        "case_recall_at_1": round(sum(x == 1 for x in case_rr) / len(case_rr), 4),
        "fact_recall_at_5": round(sum(fact_recall_5) / len(fact_recall_5), 4),
        "fact_recall_at_10": round(sum(fact_recall_10) / len(fact_recall_10), 4),
        "fact_precision_at_5": round(sum(fact_precision_5) / len(fact_precision_5), 4),
        "dataset_lookup_accuracy": round(sum(dataset_hits) / len(dataset_hits), 4),
        "coverage_warning_accuracy": round(sum(coverage_hits) / len(coverage_hits), 4),
        "limitation": "Developer-authored queries from the same source set; not a held-out expert benchmark.",
    }
    output = {"summary": summary, "details": details}
    target = HERE / "output" / "retrieval_evaluation.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
