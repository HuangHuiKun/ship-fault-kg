"""
Automated cross-model validation:
  Qwen extracted HFACS factors → Claude Sonnet evaluates correctness
  against original PDF text.
"""
import os, json, time
import pandas as pd
import pdfplumber
from openai import OpenAI
from pathlib import Path

PDF_DIR = Path("pdf")
RESULTS = Path("results")

# ── Load sample ───────────────────────────────────────────────────────────────
ann  = pd.read_excel(RESULTS / "validation_annotation_sheet.xlsx", sheet_name="Annotations")
summ = pd.read_excel(RESULTS / "validation_annotation_sheet.xlsx", sheet_name="Sample_Overview")

# Unique reports in sample
report_ids = summ["source_file"].unique().tolist()
print(f"Reports to validate: {len(report_ids)}")

# qwen-plus as independent validator (extraction was done with qwen-max)
client = OpenAI(
    api_key=os.environ.get('DASHSCOPE_API_KEY'),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
EVAL_MODEL = "qwen-plus"

EVAL_PROMPT = """\
You are an independent maritime safety expert evaluating the quality of HFACS (Human Factors Analysis and Classification System) factor extraction from accident investigation reports.

## Original Accident Report Text (excerpts):
{report_text}

## Accident Type: {accident_type}

## Extracted HFACS Factors to Evaluate:
{factors_list}

For each factor, judge its correctness based on the report text:
- **Correct**: Factor accurately reflects a causal finding stated or clearly implied in the report
- **Partial**: Factor is roughly right but too vague, imprecise, or merges two separate issues
- **Wrong**: Factor is hallucinated, irrelevant, or contradicts the report

Also estimate how many significant causal factors the report contains in total (for recall calculation).

Respond in JSON only:
{{
  "evaluations": [
    {{"factor": "<exact factor text>", "judgment": "Correct|Partial|Wrong", "reason": "<1 sentence>"}},
    ...
  ],
  "estimated_total_factors_in_report": <integer>,
  "missed_factors": ["<factor 1>", "<factor 2>"]
}}
"""

def extract_pdf_text(pdf_path: Path, max_chars: int = 8000) -> str:
    """Extract text from PDF, truncate to fit context."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = []
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages.append(t)
            text = "\n".join(pages)
            # Take first + last portions to capture intro and conclusions
            if len(text) > max_chars:
                half = max_chars // 2
                text = text[:half] + "\n\n[... middle section omitted ...]\n\n" + text[-half:]
            return text
    except Exception as e:
        return f"[PDF extraction error: {e}]"

results = []
already_done = set()
out_path = RESULTS / "validation_results.jsonl"

# Resume support
if out_path.exists():
    with open(out_path) as f:
        for line in f:
            try:
                r = json.loads(line)
                already_done.add(r["source_file"])
            except:
                pass
    print(f"Resuming — {len(already_done)} already done")

with open(out_path, "a", encoding="utf-8") as out_f:
    for i, sf in enumerate(report_ids):
        if sf in already_done:
            print(f"[{i+1}/{len(report_ids)}] SKIP {sf}")
            continue

        # Get factors for this report
        factors = ann[ann["report_id"] == sf.replace(".pdf","")]["hfacs_factor"].tolist()
        accident_type = summ[summ["source_file"] == sf]["accident_type"].iloc[0]

        if not factors:
            print(f"[{i+1}/{len(report_ids)}] No factors for {sf}, skipping")
            continue

        # Extract PDF text
        pdf_path = PDF_DIR / sf
        report_text = extract_pdf_text(pdf_path)

        # Build factors list
        factors_numbered = "\n".join(f"{j+1}. {f}" for j, f in enumerate(factors))

        prompt = EVAL_PROMPT.format(
            report_text=report_text,
            accident_type=accident_type,
            factors_list=factors_numbered,
        )

        print(f"[{i+1}/{len(report_ids)}] Evaluating {sf} ({len(factors)} factors)...", end=" ", flush=True)

        try:
            msg = client.chat.completions.create(
                model=EVAL_MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            raw = msg.choices[0].message.content.strip()
            # Strip markdown code block if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed = json.loads(raw)
            record = {
                "source_file": sf,
                "accident_type": accident_type,
                "n_factors": len(factors),
                "evaluations": parsed.get("evaluations", []),
                "estimated_total": parsed.get("estimated_total_factors_in_report", len(factors)),
                "missed_factors": parsed.get("missed_factors", []),
            }
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            out_f.flush()

            # Quick summary
            judgments = [e["judgment"] for e in parsed.get("evaluations", [])]
            c = judgments.count("Correct")
            p = judgments.count("Partial")
            w = judgments.count("Wrong")
            print(f"C={c} P={p} W={w}")

        except Exception as e:
            print(f"ERROR: {e}")
            record = {"source_file": sf, "error": str(e)}
            out_f.write(json.dumps(record) + "\n")

        time.sleep(0.5)  # rate limit

print("\nValidation complete. Run compute_metrics.py to get Precision/Recall/F1.")
