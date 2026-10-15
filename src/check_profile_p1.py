"""Check a three-party MP-SPDZ transcript against the plaintext oracle."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def parse_results(log: str) -> list[tuple[int, int]]:
    return [(int(active), int(score)) for active, score in re.findall(
        r"^P1_ACTIVE\s+([01])\s+P1_SCORE\s+(\d+)\s*$", log, re.MULTILINE)]


def check(log: str, expected: list[tuple[int, int]]) -> None:
    observed = parse_results(log)
    if observed != expected:
        raise AssertionError(f"MP-SPDZ output {observed}; expected {expected}")


if __name__ == "__main__":
    expected_rows = [tuple(map(int, line.split())) for line in Path(sys.argv[2]).read_text().splitlines()]
    check(Path(sys.argv[1]).read_text(errors="replace"), expected_rows)
    print(f"PASS: actual three-party outputs match the reference for {len(expected_rows)} household(s)")
