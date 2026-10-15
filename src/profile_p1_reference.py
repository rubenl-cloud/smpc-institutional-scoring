"""Plaintext oracle for the synthetic three-party P1 experiment.

This module deliberately combines all inputs, so it is only a regression
reference for invented data. It is not a privacy-preserving computation.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDIAN_ANNUAL_CENTS = 1_800_000
POVERTY_PERCENT = 60
BURDEN_PERCENT = 10
WEIGHT_I2 = 45
WEIGHT_I3 = 40
WEIGHT_I4 = 15


@dataclass(frozen=True)
class ProfileResult:
    """Permitted educational result and its plaintext explanation."""

    active: int
    score: int
    i2_relative_poverty: int
    i3_high_energy_burden: int
    i4_payment_incident: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def read_csv(path: Path, names: tuple[str, ...]) -> list[dict[str, int | str]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if tuple(reader.fieldnames or ()) != names:
            raise ValueError(f"{path}: expected {names}, got {reader.fieldnames}")
        rows = []
        for raw in reader:
            values: dict[str, int | str] = {"household_id": raw["household_id"]}
            for key in names[1:]:
                values[key] = int(raw[key])
            rows.append(values)
    if not rows or len({row['household_id'] for row in rows}) != len(rows):
        raise ValueError(f"{path}: empty or duplicate household IDs")
    return rows


def evaluate_profile(
    income: int,
    electricity: int,
    non_electricity: int,
    arrears: int,
    *,
    median: int = MEDIAN_ANNUAL_CENTS,
    poverty_percent: int = POVERTY_PERCENT,
    burden_percent: int = BURDEN_PERCENT,
    weight_i2: int = WEIGHT_I2,
    weight_i3: int = WEIGHT_I3,
    weight_i4: int = WEIGHT_I4,
) -> ProfileResult:
    """Activate P1 on I3 and return an experimental weighted 0-100 score."""
    values = (income, electricity, non_electricity, arrears, median,
              poverty_percent, burden_percent, weight_i2, weight_i3, weight_i4)
    if any(type(value) is not int for value in values):
        raise TypeError("All inputs and parameters must be integers")
    if income <= 0 or electricity < 0 or non_electricity < 0 or arrears not in (0, 1):
        raise ValueError("Invalid private input")
    if median <= 0 or not 0 <= poverty_percent <= 100 or not 0 <= burden_percent <= 100:
        raise ValueError("Invalid public parameter")
    if min(weight_i2, weight_i3, weight_i4) < 0 or weight_i2 + weight_i3 + weight_i4 != 100:
        raise ValueError("Indicator weights must be non-negative and sum to 100")
    if max(income, electricity, non_electricity, median) >= 10**12:
        raise ValueError("Monetary amount out of experiment range")

    i2 = int(100 * income < poverty_percent * median)
    i3 = int(100 * (electricity + non_electricity) > burden_percent * income)
    i4 = arrears
    active = i3
    score = active * (weight_i2 * i2 + weight_i3 * i3 + weight_i4 * i4)
    return ProfileResult(active, score, i2, i3, i4)


def load_parties(directory: Path = ROOT / "data") -> list[tuple[str, int, int, int, int]]:
    social = read_csv(directory / "party0_ds8_social.csv", ("household_id", "annual_equiv_income_cents"))
    energy = read_csv(directory / "party1_ds4_electricity.csv", ("household_id", "annual_electricity_cost_cents", "payment_incident"))
    fuel = read_csv(directory / "party2_ds14_fuels.csv", ("household_id", "annual_non_electric_cost_cents"))
    ids = [[row["household_id"] for row in party] for party in (social, energy, fuel)]
    if not (ids[0] == ids[1] == ids[2]):
        raise ValueError("The synthetic household order must match across parties; PSI is outside v0")
    return [
        (str(s["household_id"]), int(s["annual_equiv_income_cents"]),
         int(e["annual_electricity_cost_cents"]), int(f["annual_non_electric_cost_cents"]),
         int(e["payment_incident"]))
        for s, e, f in zip(social, energy, fuel)
    ]


def expected_results(rows: list[tuple[str, int, int, int, int]], **kwargs) -> list[ProfileResult]:
    return [evaluate_profile(income, electricity, fuel, arrears, **kwargs)
            for _, income, electricity, fuel, arrears in rows]
