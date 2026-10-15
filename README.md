# SMPC for multi-institutional scoring

Experimental repository for privacy-preserving computation of indicators from vertically partitioned institutional data. Developed as a research proof of concept, not for production use.

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
