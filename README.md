# SMPC for multi-institutional scoring

Research proof of concept for calculating a synthetic institutional vulnerability score with three data owners. It is not production software and must not be used with personal data.

## Immediate editable demonstration

Python 3 is the only dependency for the plaintext reference and the web interface. On Windows PowerShell, Linux or WSL:

```sh
python web/server.py
```

Open **http://127.0.0.1:8765**. The page is deliberately simple: choose a synthetic household, edit the numeric fields directly, and press **Calcular referencia Python**.

The three simulated owners are:

| Party | Source | Private synthetic input |
|---|---|---|
| P0 | DS8 social organisation | annual equivalent income |
| P1 | DS4 electricity retailer | annual electricity expenditure and payment incident |
| P2 | DS14 gas/fuel provider | annual non-electric energy expenditure |

The Profile 1 experiment uses three binary indicators:

```text
I2 = 1 when income < 60% of the public median
I3 = 1 when total energy expenditure > 10% of income
I4 = 1 when an electricity payment incident exists

P1 active = I3
P1 score  = active × (45×I2 + 40×I3 + 15×I4)
```

The score ranges from 0 to 100. The thresholds and weights are transparent experimental choices, **not an approved SOCIAREM eligibility rule**.

## Plaintext reference versus actual MP-SPDZ

- **Python reference:** combines all invented inputs in plaintext and shows I2, I3 and I4. It validates the rule but provides no cryptographic privacy.
- **MP-SPDZ / Semi2k:** reads owner-separated temporary input files, runs three local protocol processes, and opens only `P1_ACTIVE` and `P1_SCORE`. It never silently falls back to Python.

To enable the second button, install and build MP-SPDZ in WSL/Linux, then start the server from that environment:

```sh
export MP_SPDZ_HOME=/absolute/path/to/MP-SPDZ
python3 web/server.py
```

The editable values are copied into a temporary directory as `Input-P0-0`, `Input-P1-0` and `Input-P2-0`. MP-SPDZ receives that prefix through `-IF`; the temporary files and generated program are removed after the run. The central localhost demo server still sees all values, so this is **not genuine institutional isolation**.

## Command-line demonstrations

Plaintext preview and unit tests:

```sh
python scripts/show_profile_p1.py
python -m unittest discover -s tests -v
```

Actual three-party protocol in Linux/WSL:

```sh
bash scripts/run_profile_p1.sh /absolute/path/to/MP-SPDZ 10 1800000 60
```

The runner compiles a generated `.mpc` program, launches three Semi2k parties, and checks every opened activation/score pair against the independent Python oracle. Do not claim a real protocol run passed unless this command or the `Three-party MP-SPDZ smoke test` GitHub Actions workflow actually succeeds.

## Scope and limitations

- Only invented, pre-aligned household records.
- Three protocol parties run as separate processes on one machine in the demo.
- Semi2k is used under a semi-honest experimental model.
- The score itself releases information; SMPC cannot remove leakage implied by an authorised output.
- Private record linkage/PSI, malicious security, governance, GDPR assessment, Eclipse EDC integration and deployment on isolated institutional hosts remain future work.

See [the P1 technical explanation](docs/profile_p1_demo.md), [the web walkthrough](docs/web_demo.md), and [the threat model](docs/threat-model.md).

## Earlier two-party experiment

The repository also retains the initial energy-burden example in `src/energy_burden.mpc`. It securely compares energy expenditure with a public percentage of income and opens one Boolean flag. It is kept for historical comparison; the three-party P1 score is the main demonstration.
