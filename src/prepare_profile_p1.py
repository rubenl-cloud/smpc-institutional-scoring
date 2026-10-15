"""Create a generated MPC program and owner-separated temporary inputs."""
from __future__ import annotations

import argparse
from pathlib import Path
from profile_p1_reference import load_parties, expected_results


def prepare(output_root: Path, data_dir: Path, *, median: int = 1_800_000,
            poverty: int = 60, burden: int = 10,
            program_name: str = "profile_p1_generated") -> tuple[int, Path, Path]:
    if median <= 0 or median >= 10**12 or not 0 <= poverty <= 100 or not 0 <= burden <= 100:
        raise ValueError("Invalid public benchmark or percentage")
    if not program_name.replace("_", "").isalnum():
        raise ValueError("Invalid generated program name")

    rows = load_parties(data_dir)
    results = expected_results(rows, median=median, poverty_percent=poverty,
                               burden_percent=burden)
    output_root.mkdir(parents=True, exist_ok=True)
    source = output_root / f"{program_name}.mpc"
    source.write_text(
        f"N = {len(rows)}\n"
        f"MEDIAN_ANNUAL_CENTS = {median}\n"
        f"POVERTY_PERCENT = {poverty}\n"
        f"BURDEN_PERCENT = {burden}\n"
        "WEIGHT_I2 = 45\nWEIGHT_I3 = 40\nWEIGHT_I4 = 15\n"
        "for i in range(N):\n"
        "    income = sint.get_input_from(0)\n"
        "    electricity = sint.get_input_from(1)\n"
        "    arrears = sint.get_input_from(1)\n"
        "    non_electricity = sint.get_input_from(2)\n"
        "    i2 = 100 * income < POVERTY_PERCENT * MEDIAN_ANNUAL_CENTS\n"
        "    i3 = 100 * (electricity + non_electricity) > BURDEN_PERCENT * income\n"
        "    i4 = arrears\n"
        "    active = i3\n"
        "    score = active * (WEIGHT_I2 * i2 + WEIGHT_I3 * i3 + WEIGHT_I4 * i4)\n"
        "    print_ln('P1_ACTIVE %s P1_SCORE %s', active.reveal(), score.reveal())\n",
        encoding="utf-8",
    )

    inputs = output_root / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    (inputs / "Input-P0-0").write_text("".join(f"{income}\n" for _, income, _, _, _ in rows), encoding="ascii")
    (inputs / "Input-P1-0").write_text("".join(f"{electricity}\n{arrears}\n" for _, _, electricity, _, arrears in rows), encoding="ascii")
    (inputs / "Input-P2-0").write_text("".join(f"{fuel}\n" for _, _, _, fuel, _ in rows), encoding="ascii")
    expected = output_root / "expected_profile_p1.txt"
    expected.write_text("".join(f"{result.active} {result.score}\n" for result in results), encoding="ascii")
    return len(rows), expected, source


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    parser.add_argument("--median", type=int, default=1_800_000)
    parser.add_argument("--poverty", type=int, default=60)
    parser.add_argument("--burden", type=int, default=10)
    parser.add_argument("--program-name", default="profile_p1_generated")
    args = parser.parse_args()
    count, expected_path, source_path = prepare(
        args.output_root.resolve(), args.data_dir.resolve(), median=args.median,
        poverty=args.poverty, burden=args.burden, program_name=args.program_name,
    )
    print(f"Prepared {count} aligned synthetic households in temporary owner-separated files")
    print(f"Generated source: {source_path}")
    print(f"Expected output: {expected_path}")
