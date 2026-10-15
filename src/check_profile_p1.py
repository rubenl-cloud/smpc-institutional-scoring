"""Check an MP-SPDZ three-party transcript against synthetic plaintext oracle."""
from __future__ import annotations
import re
import sys
from pathlib import Path


def check(log: str, expected: list[int]) -> None:
    observed = [int(v) for v in re.findall(r'^P1_TIER\s+([012])\s*$', log, re.MULTILINE)]
    if observed != expected:
        raise AssertionError(f'MP-SPDZ output {observed}; expected {expected}')


if __name__ == '__main__':
    expected = [int(x) for x in Path(sys.argv[2]).read_text().split()]
    check(Path(sys.argv[1]).read_text(errors='replace'), expected)
    print(f'PASS: actual 3-party MP-SPDZ outputs match baseline on all {len(expected)} households')
