"""Small, transparent development evaluation of graph retrieval.

These labels were written from the same source set and are a smoke test, not
an independent expert assessment or generalisation benchmark.
"""

from __future__ import annotations

import json
import argparse
from pathlib import Path

from retrieve import Retriever
from eval_cases_v2 import QUERIES, PARAPHRASES
from expanded_cases import EXPANDED_CASES


HERE = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--strategy', choices=['hybrid','lexical'], default='hybrid')
    args = parser.parse_args()
    retriever = Retriever()
    naming = json.loads((HERE / 'naming_v4.json').read_text(encoding='utf-8'))['nodes']
    approved_names = {r['oldName']: r['name'] for r in naming.values() if not r['delete']}
    questions = json.loads((HERE / "eval_queries.json").read_text(encoding="utf-8"))
    # The original V1 coverage gold predates the supported V3/V4 reference
    # profiles. Reference evidence still does not establish this vessel's cause.
    for item in questions:
        if item['id'] == 'Q12':
            item['coverage'] = 'reference_knowledge'
            item['gold_update_reason'] = '已有参考机理；仍不代表本船联轴器断裂根因已确认。'
    cases = {c['id']: c for c in EXPANDED_CASES}
    for i, (case_id, query) in enumerate(QUERIES):
        gold = [[f[0].split('|')[1], f[1], f[2].split('|')[1]] for f in cases[case_id]['facts'][:3]]
        questions.append({'id': f'V2-{i+1:02d}', 'query': query, 'case_id': case_id, 'gold': gold})
        questions.append({'id': f'P-{i+1:02d}', 'query': PARAPHRASES[i], 'case_id': case_id, 'gold': gold})
    questions += [{'id':'NEG1','query':'航天器太阳能电池的辐射衰减原因是什么？','coverage':'no_evidence'},
                  {'id':'NEG2','query':'心脏冠状动脉狭窄如何治疗？','coverage':'no_evidence'}]
    details = []
    case_rr = []
    fact_recall_5 = []
    fact_recall_10 = []
    fact_precision_5 = []
    dataset_hits = []
    coverage_hits = []
    for item in questions:
        result = retriever.search(item["query"], top_facts=10, strategy=args.strategy)
        row = {"id": item["id"], "query": item["query"],
               "top_case": result["cases"][0]["case_id"] if result["cases"] else None,
               "coverage": result["coverage"]}
        if "case_id" in item:
            ranks = [x["case_id"] for x in result["cases"]]
            rr = 1 / (ranks.index(item["case_id"]) + 1) if item["case_id"] in ranks else 0
            case_rr.append(rr)
            ranked = [(f["case_id"], f["subject"], f["relation"], f["object"])
                      for f in result["facts"]]
            gold = {(item["case_id"], approved_names.get(f[0], f[0]), f[1],
                     approved_names.get(f[2], f[2])) for f in item["gold"]}
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
        'strategy': args.strategy,
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
    target = HERE / "output" / ("retrieval_evaluation_v4.json" if args.strategy == 'hybrid' else 'retrieval_evaluation_v4_lexical.json')
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    (HERE / 'output' / 'eval_queries_v4.json').write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
