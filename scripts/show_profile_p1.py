#!/usr/bin/env python3
"""Immediate synthetic plaintext preview. THIS IS NOT A SECURE MPC RUN."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from profile_p1_reference import (load_parties, expected_tiers, MEDIAN_ANNUAL_CENTS,
                                  POVERTY_PERCENT, BURDEN_PERCENT)

rows = load_parties()
tiers = expected_tiers(rows)
print('\n=== SOCIAREM-inspired P1 | THREE INSTITUTIONAL DATA SOURCES ===')
print('DS8 Foundation: household annual equivalent income [P0]')
print('DS4 Energy retailer: annual electricity bill + arrears [P1]')
print('DS14 Fuel provider: annual non-electric expenditure [P2]')
print(f'Public benchmark: median €{MEDIAN_ANNUAL_CENTS/100:,.0f}; poverty line {POVERTY_PERCENT}%')
print(f'Burden threshold {BURDEN_PERCENT}% (EXPERIMENTAL / NOT VALIDATED)')
print('Experimental activation: below poverty line AND above burden threshold')
print('P1 tier: 0=inactive, 1=active, 2=active with electricity arrears\n')
print('RESULTS — synthetic households (plaintext oracle; NOT an SMPC execution)')
for (household, *_), tier in zip(rows, tiers):
    print(f'  {household}: P1_TIER {tier}')
print(f'\nActivated: {sum(v > 0 for v in tiers)}/{len(tiers)}; priority tier 2: {sum(v == 2 for v in tiers)}')
print('\nTo compute SAME output with private inputs, run scripts/run_profile_p1.sh on MP-SPDZ.')
