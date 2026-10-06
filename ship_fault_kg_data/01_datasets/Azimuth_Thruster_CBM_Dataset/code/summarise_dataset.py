#!/usr/bin/env python3
"""Summarise anonymised IM-CBM supporting data.
Run from the repository root:
    python code/summarise_dataset.py
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def main():
    table3 = pd.read_csv(DATA / "table3_lti_by_fault_type_anonymised.csv")
    table4 = pd.read_csv(DATA / "table4_diagnostic_zones_economics.csv")
    numeric_lti = pd.to_numeric(table3["LTI / warning (mo)"], errors="coerce")
    mechanical_lti = numeric_lti.dropna()
    print("Mechanical-fault LTI summary")
    print("n =", len(mechanical_lti))
    print("mean months =", round(mechanical_lti.mean(), 3))
    print("std months =", round(mechanical_lti.std(ddof=1), 3))
    print("\nDiagnostic-zone economics")
    print(table4[["Zone", "Zone name", "Cost-avoidance ratio"]].to_string(index=False))

if __name__ == "__main__":
    main()
