# Marine Engine Fault Dataset

Measurement data from a controlled experimental campaign on a **Matsui Iron Works MU323DGSC** marine diesel engine. The release contains a baseline reference-performance dataset, five fault/anomaly scenario classes recorded at fixed loads, and supporting documentation for interpretation and reuse.

> **Status:** prepared for open release on Zenodo as the data record accompanying a *Scientific Data* Data Descriptor (manuscript under review; preprint on arXiv). The dataset DOI below is reserved; the record will be opened on acceptance.

## Authors

- Ahmad BahooToroody — Aalto University (Dept. of Energy and Mechanical Engineering); Kotka Maritime Research Centre — ORCID 0000-0002-7126-4244
- Oleksiy Bondarenko — National Maritime Research Institute, Tokyo — ORCID 0000-0002-1811-2372
- Mohammad Mahdi Abaei — Aalto University (Dept. of Energy and Mechanical Engineering); Kotka Maritime Research Centre — ORCID 0000-0003-1480-2007
- Yoichi Niki — National Maritime Research Institute, Tokyo — ORCID 0000-0001-6294-542X
- Enrico Zio — Politecnico di Milano (Energy Dept.); MINES Paris-PSL University (CRC, Sophia Antipolis) — ORCID 0000-0002-7108-637X

## Citation

If you use this dataset, please cite both the dataset and the Data Descriptor:

> BahooToroody, A., Bondarenko, O., Abaei, M. M., Niki, Y., & Zio, E. (2026). *Marine Engine Fault Dataset* (Version 1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.19857425

> BahooToroody, A., Bondarenko, O., Abaei, M. M., Niki, Y., & Zio, E. (2026). *Marine Engine Fault Dataset: Open-Access Data under Controlled Reference and Fault Scenario Conditions*. Scientific Data (submitted). Preprint: arXiv:2607.19444 (https://doi.org/10.48550/arXiv.2607.19444).

See `CITATION.cff` for machine-readable citation metadata.

## License

This dataset is released under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license. You may share and adapt the data for any purpose, including commercially, provided you give appropriate credit. Full terms: https://creativecommons.org/licenses/by/4.0/ (see `LICENSE`).

---

## Repository contents

```
Marine_Engine_Fault_Data/
├── README.md                     this file
├── LICENSE                       CC BY 4.0
├── CITATION.cff                  machine-readable citation
├── dataset_index.csv             file-level index
├── variable_dictionary.csv       variable-level dictionary
├── Reference_Data.csv            baseline reference-performance file (70-column schema)
├── AF_Clogging/                  compressor air-filter clogging  (40/60/75/85 % load)
├── AC_Fouling/                   air-cooler fouling               (40/60/75/85 % load)
├── Injector_Nozzle/              injection-valve nozzle clogging  (one-hole; two-hole load program)
├── Pump_Cavitation/              cooling-water pump cavitation    (60/85 % load)
├── Turbine_Degradation/          turbine degradation              (40/60/85 % load)
└── provenance/normalize.py       script used to normalise the raw exports into this release
```

`dataset_index.csv` is the authoritative per-file overview (schema type, scenario, load, row/column counts, anomaly-state type). All tabular files in this release are UTF-8 CSV, the canonical, non-proprietary form (they open directly in Excel, pandas, R, etc.).

## File format and schema

**Encoding & line endings.** All CSV files are **UTF-8 (no BOM)** with **LF** line endings.

**Three-row header.** Every CSV — reference *and* scenario — uses the same three-row header convention:

1. row 1 — full variable names (use these as column keys)
2. row 2 — shorthand symbols (note: some symbols are reused, e.g. `Pmax`, `Pmin`, `We`, `Wi` for cylinders No.1–3)
3. row 3 — units

Data begin on row 4.

**Scenario files** share a single **73-column schema** with identical column order across all files. The first three columns are:

- `Time_abs` — absolute time from midnight (s)
- `Time_rel` — elapsed time from start of test (s)
- `Anomaly State` — `0` = pre-anomaly segment, `1` = anomalous segment

> The two **Injector_Nozzle** files are dedicated restricted-nozzle test programs and contain **anomalous operation only** (`Anomaly State = 1` throughout, no baseline segment).

**Reference file.** `Reference_Data.csv` is the baseline. It uses the same three-row header convention but a **different 70-column set**: it has **no** `Anomaly State`, and it uses `Time` (`T`, s) instead of `Time_abs`/`Time_rel`. Handle it separately from the scenario files during preprocessing.

**Two channels are present everywhere but not always recorded.** For schema uniformity, `Compressor Filter Loss` (`dPf`, Pa) and `Turbine Back Pressure` (`dPex`, Pa) are present as columns in **all** scenario files, but were **not recorded** in five runs and are therefore **empty (NaN)** in:
`AC_Fouling_85_Load.csv`, `Clogged_Injector_Nozzle1_40_60_85_Load.csv`, `Clogged_Injector_Nozzle2_LoadProgram.csv`, `CW_Pump_Cavitation_60_Load.csv`, `CW_Pump_Cavitation_85_Load.csv`.
An empty cell in these two columns means "not measured in this run", not "zero". Per-file presence is recorded in `variable_dictionary.csv` and `dataset_index.csv`.

**Units.** A mix of SI and engineering units is used as logged by the test bench (e.g. `kgf/cm2`, `kgf`, `m3/h`, `°C`). Several pressure-related channels are stored as **raw voltage signals (V)**, not calibrated pressures: `Pl_lo`, `Pl_fuel`, `Pl_water1`, `Pl_water2`, `Pl_loturb`, `Pl_valve`. Treat these as raw sensor outputs.

## How to load (Python)

```python
import pandas as pd

# Scenario file — use the full-name row as columns, drop shorthand + units rows
df = pd.read_csv(
    "AF_Clogging/AF_Clogging_60_Load.csv",
    header=0, skiprows=[1, 2], encoding="utf-8",
)
pre   = df[df["Anomaly State"] == 0]
fault = df[df["Anomaly State"] == 1]

# Reference file — same header convention, different (70-column) schema
ref = pd.read_csv("Reference_Data.csv", header=0, skiprows=[1, 2], encoding="utf-8")
```

## Scenario descriptions

**AF_Clogging — compressor air-filter clogging.** Introduced by gradually covering the filter surface, producing a progressive increase in pressure loss across the air filter. Fixed-load tests at 40 %, 60 %, 75 %, 85 %.

**AC_Fouling — air-cooler fouling.** Introduced by altering the charge-air cooling condition, raising charge-air temperature and degrading cooling effectiveness. Fixed-load tests at 40 %, 60 %, 75 %, 85 %. At low load and elevated temperature, some instability in temperature control may appear because the cooling-water control action operated near its deadband; this is part of the implemented abnormal response, not a data fault.

**Injector_Nozzle — injection-valve nozzle clogging.** Two severities: a **one-hole** plugged nozzle operated at three loads (`Clogged_Injector_Nozzle1_40_60_85_Load.csv`), and a more severe **two-hole** plugged nozzle operated under a load program (`Clogged_Injector_Nozzle2_LoadProgram.csv`). Both files are anomalous operation only.

**Pump_Cavitation — cooling-water pump cavitation.** A cavitation-like anomaly imitated by introducing pressurized air into the pump suction, causing pressure drop and instability. Tests at 60 %, 85 %.

**Turbine_Degradation — turbine degradation.** Induced by increasing exhaust-side back pressure downstream of the turbine, altering turbine and turbocharger operating conditions. Fixed-load tests at 40 %, 60 %, 85 %.

## Usage notes

- Compare scenario records with the reference file using **matched load conditions** where possible.
- Keep both the full-name and shorthand rows during preprocessing, since shorthand symbols are reused across channels.
- Treat empty `dPf`/`dPex` cells as missing, not zero.

## Provenance / version

**Version 1.0.** This release was normalized for consistency from the raw bench exports: all files re-encoded to UTF-8; a single 73-column schema and column order enforced across scenario files; label casing and column-name typos corrected (including `Anomaly State` and `Loss with cooling water`); degree-Celsius units unified to `°C`; the index recomputed from the released files; and the variable dictionary updated with accurate per-file presence and data types. Measurement values themselves were not altered. The exact transformation is reproduced by `provenance/normalize.py`.
