"""Plaintext oracle for the energy burden SMPC experiment.

Integer cents and strictly greater-than avoid floating point and
threshold-boundary ambiguity. Synthetic data only.
"""
from __future__ import annotations

import csv
from pathlib import Path


def classify(energy_cents: int, income_cents: int, threshold_percent: int = 10) -> int:
    if not isinstance(energy_cents, int) or not isinstance(income_cents, int):
        raise TypeError("Inputs must be integer euro cents")
    if not isinstance(threshold_percent, int) or not 0 <= threshold_percent <= 100:
        raise ValueError("Threshold must be an integer percent between 0 and 100")
    if energy_cents < 0 or income_cents <= 0:
        raise ValueError("Energy cost must be >=0 and income must be >0")
    return int(100 * energy_cents > threshold_percent * income_cents)


def load_fixture(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        expected = ["household_id", "energy_cents", "income_cents"]
        if reader.fieldnames != expected:
            raise ValueError(f"Expected CSV header: {expected!r}")
        rows = [(r["household_id"], int(r["energy_cents"]), int(r["income_cents"]))
                for r in reader]
    if not rows or len({r[0] for r in rows}) != len(rows):
        raise ValueError("Expected non-empty fixture with unique household IDs")
    return rows


def flags(rows, threshold_percent: int):
    return [classify(e, y, threshold_percent) for _, e, y in rows]
