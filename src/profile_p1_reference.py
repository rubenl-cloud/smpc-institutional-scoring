"""Plaintext reference for a 3-provider synthetic P1 scoring experiment.

Only used to validate MPC results. NEVER use this aggregator on real stakeholder
files: it intentionally combines private data to provide a synthetic oracle.
"""
from __future__ import annotations
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDIAN_ANNUAL_CENTS = 1_800_000   # illustrative national benchmark: €18,000
POVERTY_PERCENT = 60            # relative poverty threshold
BURDEN_PERCENT = 10             # unvalidated demonstration threshold


def read_csv(path: Path, names: tuple[str, ...]) -> list[dict[str, int | str]]:
    with path.open(newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        if tuple(reader.fieldnames or ()) != names:
            raise ValueError(f'{path}: expected {names}, got {reader.fieldnames}')
        rows = []
        for raw in reader:
            values: dict[str, int | str] = {'household_id': raw['household_id']}
            for key in names[1:]:
                values[key] = int(raw[key])
            rows.append(values)
    if not rows or len({r['household_id'] for r in rows}) != len(rows):
        raise ValueError(f'{path}: empty or duplicate household IDs')
    return rows


def classify(income: int, electricity: int, non_electricity: int,
             arrears: int, median: int = MEDIAN_ANNUAL_CENTS,
             poverty_percent: int = POVERTY_PERCENT,
             burden_percent: int = BURDEN_PERCENT) -> int:
    """Return 0 inactive; 1 active; 2 active with payment incidents.

    Both poverty and energy burden must hold. The incident flag reinforces the
    activated profile but does not activate it independently.
    """
    if any(type(v) is not int for v in (income, electricity, non_electricity, arrears, median, poverty_percent, burden_percent)):
        raise TypeError('All inputs must be integers')
    if income <= 0 or electricity < 0 or non_electricity < 0 or arrears not in (0, 1):
        raise ValueError('Invalid private input')
    if median <= 0 or not 0 <= poverty_percent <= 100 or not 0 <= burden_percent <= 100:
        raise ValueError('Invalid public parameter')
    # Bound experimental domain to avoid fixed-width arithmetic overflow.
    if max(income, electricity, non_electricity, median) >= 10**12:
        raise ValueError('Monetary amount out of experiment range')
    i2_poverty = 100 * income < poverty_percent * median
    i3_excess_burden = 100 * (electricity + non_electricity) > burden_percent * income
    active = i2_poverty and i3_excess_burden
    return (1 + arrears) if active else 0


def load_parties(directory: Path = ROOT / 'data') -> list[tuple[str, int, int, int, int]]:
    social = read_csv(directory / 'party0_ds8_social.csv', ('household_id', 'annual_equiv_income_cents'))
    energy = read_csv(directory / 'party1_ds4_electricity.csv', ('household_id', 'annual_electricity_cost_cents', 'payment_incident'))
    fuel = read_csv(directory / 'party2_ds14_fuels.csv', ('household_id', 'annual_non_electric_cost_cents'))
    ids = [[r['household_id'] for r in lst] for lst in (social, energy, fuel)]
    if not (ids[0] == ids[1] == ids[2]):
        raise ValueError('The synthetic household order must match across parties; PSI is outside v0')
    return [(str(s['household_id']), int(s['annual_equiv_income_cents']),
             int(e['annual_electricity_cost_cents']), int(f['annual_non_electric_cost_cents']),
             int(e['payment_incident']))
            for s, e, f in zip(social, energy, fuel)]


def expected_tiers(rows: list[tuple[str, int, int, int, int]], **kwargs) -> list[int]:
    return [classify(inc, elec, fuel, arrears, **kwargs)
            for _, inc, elec, fuel, arrears in rows]
