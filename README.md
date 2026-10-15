# SMPC for multi-institutional scoring

Experimental repository for privacy-preserving computation of indicators from vertically partitioned institutional data. Developed as a research proof of concept, not for production use.

## Interactive web demonstration (recommended for meetings)

**Python 3 is the only dependency for the interactive visual reference demo.** There is no npm, frontend build step, database or installation of a web framework.

On **Windows PowerShell** or **Linux/WSL** in this cloned repository:

```sh
python web/server.py
```

Then open **http://127.0.0.1:8765** in a browser. On Linux use `python3 web/server.py` if needed.

The dashboard animates the three synthetic institution inputs, lets you select one of seven households, inspect synthetic attributes, change public thresholds, observe the activation of P1, and switch between two *explicitly labelled* backends:

- **Run visual reference** — actual server-side Python calculation over synthetic data. This is plaintext, NOT cryptographically private, and works immediately on Windows with no extra packages.
- **Run actual 3-party MPC** — calls the **real** MP-SPDZ Semi2k protocol if you have configured the backend from Linux/WSL. No silent fallback to plaintext. Otherwise the button is disabled and explains the missing setup.

To enable local cryptographic runs in **WSL/Linux** after installing/building MP-SPDZ:

```sh
export MP_SPDZ_HOME=/absolute/path/to/MP-SPDZ
python3 web/server.py
```

Build MP-SPDZ's `semi2k-party.x` as described in [the upstream instructions](https://github.com/data61/MP-SPDZ); the [3-party GitHub Actions integration test](https://github.com/rubenl-cloud/smpc-institutional-scoring/actions/workflows/three-party-smpc.yml) has passed. In this prototype, those parties execute as **separate local processes**, not genuinely isolated institutional machines. The shared synthetic test harness has access to every input file; for real deployment each stakeholder must supply its input independently.

Detailed setup, demo walkthrough and troubleshooting: **[Web demo guide](docs/web_demo.md)**. For exact indicator and P1 rules see [P1 technical specification](docs/profile_p1_demo.md).

## NEW: 3-institution P1 profile activation (demo for 16 October)

This is the main experiment to present. It uses **three independent synthetic stakeholders**, unlike the small 2-party example below:

| MPC party | Source | Private inputs |
|---|---|---|
| P0: social organisation | DS8 audited declaration | annual household equivalent income |
| P1: electricity retailer | DS4 | annual electricity bill and non-payment incident |
| P2: gas / fuel provider | DS14 | annual non-electric energy bill |

Three-party MP-SPDZ computes: **I2 relative poverty AND I3 high energy burden**, with I4 non-payment **reinforcing** priority, and reveals only **P1 tier 0 / 1 / 2**. The exact profile rule is an experimental hypothesis, **not** a decision criterion approved by SOCIAREM. The simulated median (€18,000/year) and 10% burden threshold are illustrative.

### Show immediately (Python 3 only)

```bash
python3 scripts/show_profile_p1.py
python3 -m unittest discover -s tests -v
```

The preview prints tiers `2 0 0 1 0 2 0` for seven synthetic households, with three activated profiles. **It is the plaintext reference, not secure computation.**

### Run real three-party SMPC (Linux / WSL)

After installing and building MP-SPDZ `semi2k-party.x`:

```bash
bash scripts/run_profile_p1.sh /absolute/path/to/MP-SPDZ 10
```

This should launch three MPC parties, compile the secure program and verify the outputs against the plaintext reference. Check the [three-party GitHub Actions workflow](https://github.com/rubenl-cloud/smpc-institutional-scoring/actions/workflows/three-party-smpc.yml) for independent backend test results; **do not claim protocol execution succeeded unless that workflow or a local run actually passes**.

See **[full stakeholder mapping, P1 rules, threat-model limitations and meeting walkthrough](docs/profile_p1_demo.md)**. Row alignment is assumed; PSI, institutional governance and Eclipse EDC integration remain future work.

---

## Earlier basic 2-party energy-burden experiment

Party 0 holds annual household energy expenditure (in euro cents). Party 1 holds annual equivalent household income (in euro cents). For each aligned synthetic household, the parties securely evaluate:

`flag = (100 * expenditure_cents > threshold_percent * annual_equivalent_income_cents)`

Only the **boolean flag** is revealed. Neither institution should receive the other institution's raw input. The threshold is a configurable *experimental* parameter; it is not a SOCIAREM-approved eligibility or classification rule.

The repository uses the **MP-SPDZ** compiler (Python-like `.mpc` programs), Python 3 standard library for preparing data and testing, and **Semi2k** for initial two-party, semi-honest experiments. Household alignment is assumed in v0; PSI/private record linkage and real institutional deployment are out of scope.

## Demo to show immediately (no installation needed)\n\nFrom the repository root run:\n\n```sh\npython3 scripts/quick_demo.py --threshold 10\npython3 -m unittest discover -s tests -v\n```\n\nThis fast showcase is an **unencrypted, plaintext baseline**, **not an SMPC execution**. It prints the synthetic inputs and flags for four sample households; its purpose is to validate the rule and explain the future private-input flow. The real SMPC circuit is in `src/energy_burden.mpc` and requires MP-SPDZ installed and built, as below.\n\n## Run real two-party MPC (Linux / WSL)

1. Install MP-SPDZ following the [official installation instructions](https://mp-spdz.readthedocs.io/en/latest/readme.html). Use a documented upstream release and install its build prerequisites. MP-SPDZ is not vendored into this repository.
2. From this repository, run `bash scripts/run_demo.sh /absolute/path/to/MP-SPDZ 10`. This generates synthetic inputs for both parties, compiles the `.mpc` program, runs the Semi2k protocol locally, and checks the observed flags against the plain-text reference.
3. Run unit tests with `python3 -m unittest discover -s tests -v`; the unit tests do **not** require MP-SPDZ.

The demo copies **synthetic** input files into the MP-SPDZ working directory. For real institutions, each party must create and manage its own private input file on an isolated host. Do not use personal or sensitive records in this demo.

For reproducibility, see `docs/experiment.md` and `docs/threat-model.md`. The MP-SPDZ backend is not yet validated against a locally executed integration test in this repository.

## Scope and non-goals

- One public output bit per household; synthetic records are pre-aligned in a shared public order.
- Positive income, nonnegative expenditure, euro-cent integer units.
- Security target: semi-honest two-party MPC, **not** malicious-party robustness, output privacy, end-to-end identity alignment, GDPR compliance, or EDC integration.
- Built for algorithmic validation and future protocol benchmarking; no real-world vulnerability decisions.
