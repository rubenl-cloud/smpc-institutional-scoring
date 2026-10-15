"""Prepare synthetic 3-party input files and parameterized MP-SPDZ source.

The test driver reads synthetic datasets together only for a plaintext oracle.
In institutional deployment each party must deliver its own input privately;
no one actor may access all original datasets as in this toy environment.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from profile_p1_reference import load_parties, expected_tiers


def prepare(output_root: Path, data_dir: Path, *, median: int = 1_800_000,
            poverty: int = 60, burden: int = 10) -> tuple[int, Path]:
    if median <= 0 or median >= 10**12 or not 0 <= poverty <= 100 or not 0 <= burden <= 100:
        raise ValueError('Invalid public benchmark or percentage')
    rows = load_parties(data_dir)
    tiers = expected_tiers(rows, median=median, poverty_percent=poverty, burden_percent=burden)
    destination = output_root / 'Programs' / 'Source' / 'profile_p1.mpc'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        f'N = {len(rows)}\nMEDIAN_ANNUAL_CENTS = {median}\nPOVERTY_PERCENT = {poverty}\nBURDEN_PERCENT = {burden}\n'
        'for i in range(N):\n'
        '    income = sint.get_input_from(0)\n'
        '    electricity = sint.get_input_from(1)\n'
        '    arrears = sint.get_input_from(1)\n'
        '    non_electricity = sint.get_input_from(2)\n'
        '    low_income = 100 * income < POVERTY_PERCENT * MEDIAN_ANNUAL_CENTS\n'
        '    high_burden = 100 * (electricity + non_electricity) > BURDEN_PERCENT * income\n'
        '    activated = low_income * high_burden\n'
        '    tier = activated * (1 + arrears)\n'
        "    print_ln('P1_TIER %s', tier.reveal())\n", encoding='utf-8')
    pd = output_root / 'Player-Data'
    pd.mkdir(parents=True, exist_ok=True)
    # Explicit owner-separated files; layout follows each party's call order.
    (pd / 'Input-P0-0').write_text(''.join(f'{inc}\n' for _, inc, _, _, _ in rows), encoding='ascii')
    (pd / 'Input-P1-0').write_text(''.join(f'{elec}\n{arrears}\n' for _, _, elec, _, arrears in rows), encoding='ascii')
    (pd / 'Input-P2-0').write_text(''.join(f'{fuel}\n' for _, _, _, fuel, _ in rows), encoding='ascii')
    expected = output_root / 'expected_profile_p1.txt'
    expected.write_text(''.join(f'{t}\n' for t in tiers), encoding='ascii')
    return len(rows), expected


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('mp_spdz', type=Path)
    p.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parents[1] / 'data')
    p.add_argument('--median', type=int, default=1_800_000, help='Annual equivalent income median in euro cents')
    p.add_argument('--poverty', type=int, default=60, help='Percentage of national median')
    p.add_argument('--burden', type=int, default=10, help='Experimental energy burden percent')
    a = p.parse_args()
    n, expected = prepare(a.mp_spdz.resolve(), a.data_dir.resolve(), median=a.median,
                          poverty=a.poverty, burden=a.burden)
    print(f'Prepared {n} aligned synthetic households and 3 separate party files')
    print(f'Expected output: {expected}')
