#!/usr/bin/env python3
"""Immediate plaintext preview. This is not an SMPC execution."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from profile_p1_reference import (BURDEN_PERCENT, MEDIAN_ANNUAL_CENTS,
                                  POVERTY_PERCENT, expected_results, load_parties)

rows = load_parties()
results = expected_results(rows)
print("\n=== P1 VULNERABILITY PROFILE | PLAINTEXT REFERENCE ===")
print("P0 social organisation: annual equivalent income")
print("P1 electricity retailer: annual bill and payment incident")
print("P2 gas/fuel provider: annual non-electric energy expenditure")
print(f"Activation: I3 energy burden > {BURDEN_PERCENT}%")
print("Score: 45×I2 + 40×I3 + 15×I4 (zero when profile is inactive)")
print(f"I2 threshold: income < {POVERTY_PERCENT}% of synthetic median €{MEDIAN_ANNUAL_CENTS / 100:,.0f}")
print("Weights and thresholds are experimental, not SOCIAREM-approved.\n")
print("RESULTS — invented households; plaintext oracle; NOT SMPC")
for (household, *_), result in zip(rows, results):
    print(f"  {household}: active={result.active} score={result.score:3d}/100 "
          f"[I2={result.i2_relative_poverty}, I3={result.i3_high_energy_burden}, "
          f"I4={result.i4_payment_incident}]")
print(f"\nActivated: {sum(result.active for result in results)}/{len(results)}")
print("For actual cryptographic execution, use scripts/run_profile_p1.sh in WSL/Linux.")
