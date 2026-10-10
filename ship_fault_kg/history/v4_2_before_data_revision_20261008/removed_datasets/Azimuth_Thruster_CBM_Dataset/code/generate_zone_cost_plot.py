#!/usr/bin/env python3
"""Create a simple diagnostic-zone economic summary plot from the anonymised processed table.
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "figures" / "generated_zone_cost_avoidance_from_table4.png"

def parse_money(x):
    return float(str(x).replace(",", ""))

def main():
    df = pd.read_csv(DATA / "table4_diagnostic_zones_economics.csv")
    df["Cost avoidance numeric"] = df["Cost avoidance (USD)"].map(parse_money)
    plt.figure(figsize=(7, 4))
    plt.bar(df["Zone"], df["Cost avoidance numeric"])
    plt.xlabel("Diagnostic zone")
    plt.ylabel("Cost avoidance (USD)")
    plt.title("Scenario-based cost avoidance by diagnostic zone")
    plt.tight_layout()
    plt.savefig(OUT, dpi=300)
    print(f"Saved {OUT}")

if __name__ == "__main__":
    main()
