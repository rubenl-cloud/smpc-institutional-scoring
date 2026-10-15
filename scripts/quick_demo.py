#!/usr/bin/env python3
"""Fast, dependency-free research demo.

This is a PLAINTEXT reference, NOT a secure MPC implementation.
See MP-SPDZ instructions to execute the same comparison cryptographically.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic household energy-burden baseline (NOT MPC)")
    parser.add_argument("--threshold", type=int, default=10, help="Example percentage (integer 0..100)")
    parser.add_argument("--csv", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "synthetic.csv")
    args = parser.parse_args()
    if not 0 <= args.threshold <= 100:
        parser.error("--threshold must be an integer between 0 and 100")
    with args.csv.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        parser.error("No households in CSV")

    print("=" * 73)
    print("HOUSEHOLD ENERGY-BURDEN DEMO  |  PLAINTEXT REFERENCE (NOT SMPC)")
    print("=" * 73)
    print("Synthetic institutions: P0=energy expenditure; P1=equivalent income")
    print(f"Public condition: 100 * expenditure > {args.threshold} * annual income")
    print("Inputs shown here for verification; in SMPC only result bits are revealed.")
    print("-" * 73)
    print(f"{'Household':<13}{'P0 energy (€)':>17}{'P1 income (€)':>19}{'Burden':>12}{'Flag':>12}")
    print("-" * 73)
    counts = 0
    for row in rows:
        energy = int(row["energy_cents"])
        income = int(row["income_cents"])
        if income <= 0 or energy < 0:
            raise ValueError("Expected strictly positive income and nonnegative energy expenditure")
        burden = 100 * energy / income
        flag = 100 * energy > args.threshold * income
        counts += flag
        print(f"{row['household_id']:<13}{energy / 100:>17,.2f}{income / 100:>19,.2f}{burden:>11.2f}%{str(int(flag)):>12}")
    print("-" * 73)
    print(f"Flagged {counts} / {len(rows)} households. Boundary equality is NOT flagged.")
    print("For actual private-input computation: run scripts/run_demo.sh with MP-SPDZ.")
    print("=" * 73)


if __name__ == "__main__":
    main()
