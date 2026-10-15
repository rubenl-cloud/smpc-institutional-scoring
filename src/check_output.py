"""Validate public MPC output against the plaintext oracle."""
import re
import sys
from pathlib import Path

def check(output: str, expected: list[int]) -> None:
    actual = [int(x) for x in re.findall(r"^RESULT\s+([01])\s*$", output, re.MULTILINE)]
    if actual != expected:
        raise AssertionError(f"MPC outputs {actual!r}; expected {expected!r}")

if __name__ == "__main__":
    log = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    expected = [int(x) for x in Path(sys.argv[2]).read_text().split()]
    check(log, expected)
    print(f"PASS: {len(expected)} SMPC classifications matched the plaintext reference")
