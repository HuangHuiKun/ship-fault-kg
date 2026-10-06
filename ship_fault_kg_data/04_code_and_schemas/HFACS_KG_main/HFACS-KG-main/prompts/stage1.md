# Stage-1 Extraction Prompt

This file documents the Stage-1 zero-shot extraction prompt used by the
HFACS-KG pipeline, as described in Section 3.2 of the manuscript and
reproduced verbatim in Appendix A. The pipeline submits each accident
investigation report (PDF text, extracted via pdfplumber) to a large language
model (Qwen-Max via DashScope) using this prompt.

## System role

You are an expert maritime accident investigator. You will be given the full
text of a single accident investigation report. Your task is to extract
structured information strictly grounded in the report text. Do not infer
information that is not stated or clearly implied.

## User instructions

Extract the following fields and return a single JSON object that conforms to
the schema in `stage1_schema.json`:

- `accident_metadata`: an object with `name`, `type` (selected from the
  controlled vocabulary listed below), `date`, and `location`.
- `vessels_involved`: an array of objects, each with `name`, `imo_number`,
  and `flag_state` where available.
- `event_sequence`: an ordered array of strings describing discrete physical
  or procedural occurrences in the chronological order asserted by the
  report. Use verbatim or minimally paraphrased clauses.
- `causal_factors`: an array of free-text descriptions of contributing
  human, organisational, and environmental factors identified by
  investigators.
- `environmental_conditions`: an object with `weather`, `visibility`,
  `sea_state`, and `time_of_day`.

## Controlled vocabulary (accident_type)

Collision; Contact; Grounding; Sinking; Capsizing; Fire; Explosion; Flooding;
Machinery Failure; Steering Failure; Loss of Containment / Pollution;
Enclosed Space Accident; Fall from Height; Man Overboard; Personal Injury;
Fatality; Stranding; Hull Failure; Cargo Shift; Collision with Submerged
Object; Other.

## Hard constraints

- Extract only information stated or clearly implied within the report.
- Do not infer causes beyond documented evidence.
- Preserve ambiguous or contradictory timelines exactly as stated.
- Return a single JSON object only; emit no other text.
