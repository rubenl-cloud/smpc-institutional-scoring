"""Generate a public-size circuit and two separate synthetic-party input files.

WARNING: This convenient local demo reads a common synthetic fixture. In an
institutional deployment data should NEVER be assembled by a coordinator;
each party supplies its own file from an isolated runtime.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from reference import load_fixture, flags


def prepare(fixture: Path, mp_spdz: Path, threshold: int):
    if not 0 <= threshold <= 100:
        raise ValueError("Threshold must be 0..100 (integer percent)")
    rows = load_fixture(fixture)
    for _, cost, income in rows:
        if cost < 0 or income <= 0:
            raise ValueError("Energy must be nonnegative and income positive")
        # Keep inputs and intermediate 100*energy well within signed 64-bit range.
        if max(cost, income) >= 10**12:
            raise ValueError("Synthetic monetary amounts are out of supported range")

    source = mp_spdz / "Programs" / "Source" / "energy_burden.mpc"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "# Generated from this repository's public-size experiment parameters.\n"
        f"N = {len(rows)}\nTHRESHOLD_PERCENT = {threshold}\n"
        "for i in range(N):\n"
        "    energy_cents = sint.get_input_from(0)\n"
        "    income_cents = sint.get_input_from(1)\n"
        "    result = 100 * energy_cents > THRESHOLD_PERCENT * income_cents\n"
        "    print_ln('RESULT %s', result.reveal())\n", encoding="utf-8"
    )

    player_dir = mp_spdz / "Player-Data"
    player_dir.mkdir(parents=True, exist_ok=True)
    (player_dir / "Input-P0-0").write_text(
        "\n".join(str(e) for _, e, _ in rows) + "\n", encoding="ascii")
    (player_dir / "Input-P1-0").write_text(
        "\n".join(str(y) for _, _, y in rows) + "\n", encoding="ascii")
    expected = mp_spdz / "expected_energy_burden.txt"
    expected.write_text(
        "\n".join(map(str, flags(rows, threshold))) + "\n", encoding="ascii"
    )
    return len(rows), expected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mp_spdz", type=Path, help="MP-SPDZ root")
    parser.add_argument("--fixture", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "synthetic.csv")
    parser.add_argument("--threshold", type=int, default=10)
    args = parser.parse_args()
    count, path = prepare(args.fixture.resolve(), args.mp_spdz.resolve(), args.threshold)
    print(f"Prepared {count} synthetic households. Expected output: {path}")


if __name__ == "__main__":
    main()
