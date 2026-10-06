# HFACS-KG

Source code and prompts for the paper:

> **Knowledge Graph Construction and Causal Analysis for Maritime Safety: An HFACS-Guided Zero-Shot LLM Approach**
> Yijie Xi and Jingbo Yin. *Ocean Engineering*, 2026 (under review).

This repository accompanies the manuscript and reproduces the extraction
pipeline, the 29-category HFACS semantic grouping, and all analyses reported
in Sections 4 and 5 (including the sensitivity analyses of Section 5.5).

## What is in this repository

```
prompts/      Stage-1 and Stage-2 LLM prompts + JSON output schemas
keywords/     The 29 semantic-grouping keyword patterns (machine-readable JSON)
analysis/     R001-R007 analysis scripts + validation + GraphRAG demo
LICENSE       MIT
```

The repository contains **only the code, prompts, and keyword tables**. The
underlying IMO GISIS accident investigation PDFs are not redistributed; re-use
is subject to the IMO Casualty Investigation Code. Researchers wishing to
reproduce the knowledge graph end-to-end may obtain the source reports
directly from <https://gisis.imo.org>.

## Repository layout

### prompts/

- `stage1.md` — the Stage-1 extraction prompt (free-text plus controlled
  vocabulary of 22 accident types).
- `stage1_schema.json` — the JSON output schema for Stage 1 (accident
  metadata, vessels, event sequence, causal factors, environmental
  conditions).
- `stage2.md` — the Stage-2 HFACS-mapping prompt (four-level HFACS taxonomy
  description + assignment instructions).
- `stage2_schema.json` — the JSON output schema for Stage 2 (per-factor
  `hfacs_levels` array + rationale).

### keywords/categories.json

The 29 keyword-pattern categories used in Section 3.5 and reproduced in
Appendix C of the manuscript. Each entry has a `category` name and a
case-insensitive Python regular expression `pattern`. First-match-wins
ordering; the catch-all `Other / Unclassified` captures the remaining 18.9%
of extracted factors.

### analysis/

| Script | Purpose | Manuscript reference |
|--------|---------|----------------------|
| `R000_sanity.py`              | Basic sanity statistics on the KG export. | — |
| `R001_accident_distribution.py` | Accident-type histogram (Figure 1). | §3.4 |
| `R002_hfacs_frequency.py`     | Raw HFACS factor frequency. | §5.1 |
| `R002b_hfacs_regex_grouping.py` | Canonical 29-category semantic grouping. | §3.5, Appendix C |
| `R003_kg_statistics.py`       | KG node/edge counts and sparsity. | §4 |
| `R004_type_factor_association.py` | Type x category heatmap (Figure 4). | §5.2 |
| `R005_event_chain_analysis.py` | Event chain length distribution (Figure 5). | §5.3 |
| `R006_causal_paths.py`        | Two-hop causal paths (Figures 6-7). | §5.4 |
| `R007_sensitivity_analyses.py` | SA1, SA2, SA3 (Figure 9). | §5.5 |
| `auto_validate.py`            | LLM-assisted validation helper. | §4 |
| `compute_metrics.py`          | Precision / recall / F1 computation. | §4.4 |
| `gen_validation_sample.py`    | Stratified 47-report validation sample. | §4.4, §4.5 |
| `graphrag_demo.py`            | GraphRAG demonstration queries Q1-Q3. | §6 (GraphRAG) |
| `redraw_all_figures.py`       | Regenerate paper figures. | — |
| `redraw_diagrams.py`          | Regenerate pipeline / architecture diagrams. | — |

## Reproducing the analyses

### 1. Prerequisites

```bash
python -m pip install pandas numpy scipy matplotlib openai pdfplumber
```

Python 3.10+ is recommended; 3.13 / 3.14 have been tested.

### 2. Obtain the KG export

The analysis scripts read CSV files exported from the Neo4j-hosted KG. The
expected layout (relative to the working directory) is:

```
kg_export/
  nodes_accident.csv
  nodes_hfacs_factor.csv
  nodes_event.csv
  nodes_vessel.csv
  nodes_location.csv
  nodes_environment.csv
  rel_led_to.csv
  rel_originated_from.csv
  rel_involved_in.csv
  rel_happened_at.csv
  rel_affected_by.csv
```

The KG itself is built by running the extraction pipeline against the GISIS
PDFs (see step 3); the KG export is not committed to this repository.

### 3. Run the extraction pipeline

The Stage-1 and Stage-2 prompts in `prompts/` are submitted to a large
language model via the OpenAI-compatible chat-completions API. The published
pipeline used Qwen-Max via Alibaba DashScope; any model that supports JSON
output (e.g., Qwen-Max, GPT-4o, Claude 3.5 Sonnet) can be used.

Set the API credentials via environment variables (the scripts have been
scrubbed of hardcoded keys):

```bash
export DASHSCOPE_API_KEY=...        # or your provider's equivalent
```

The high-level extraction loop is:

```python
from openai import OpenAI
import os, json, pathlib

client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
stage1_prompt = pathlib.Path("prompts/stage1.md").read_text(encoding="utf-8")
stage2_prompt = pathlib.Path("prompts/stage2.md").read_text(encoding="utf-8")
# ... iterate over GISIS PDFs, extract text with pdfplumber,
# submit stage1_prompt + PDF text, parse JSON, then submit
# stage2_prompt + causal_factors list, parse JSON, write to Neo4j.
```

### 4. Reproduce the analyses

With the KG export present:

```bash
python analysis/R001_accident_distribution.py
python analysis/R002b_hfacs_regex_grouping.py
python analysis/R003_kg_statistics.py
python analysis/R004_type_factor_association.py
python analysis/R005_event_chain_analysis.py
python analysis/R006_causal_paths.py
python analysis/R007_sensitivity_analyses.py   # SA1, SA2, SA3 (§5.5)
```

Each script writes its outputs (CSV summaries, JSON, PNG figures) into a
local `results/` directory.

## Citation

If you use this code or the keyword-pattern table in your own work, please
cite:

```bibtex
@article{XiYin2026HFACSKG,
  author  = {Xi, Yijie and Yin, Jingbo},
  title   = {Knowledge Graph Construction and Causal Analysis for Maritime
             Safety: An {HFACS}-Guided Zero-Shot {LLM} Approach},
  journal = {Ocean Engineering},
  year    = {2026},
  note    = {Under review}
}
```

## License

Code in this repository is released under the [MIT License](LICENSE).
The IMO GISIS source PDFs and any derived KG content are subject to the
terms of the IMO Casualty Investigation Code and are not redistributed here.

## Contact

Yijie Xi (<qw1412@sjtu.edu.cn>) — corresponding author for code
Jingbo Yin (<jingboyin@sjtu.edu.cn>) — corresponding author for the manuscript
School of Ocean and Civil Engineering, Shanghai Jiao Tong University.
