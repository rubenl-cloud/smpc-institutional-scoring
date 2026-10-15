# SMPC for multi-institutional scoring

Experimental repository for privacy-preserving computation of indicators from vertically partitioned institutional data. Developed as a research proof of concept, not for production use.

## First experiment: household energy burden

Party 0 holds annual household energy expenditure (in euro cents). Party 1 holds annual equivalent household income (in euro cents). For each aligned synthetic household, the parties securely evaluate:

`flag = (100 * expenditure_cents > threshold_percent * annual_equivalent_income_cents)`

Only the **boolean flag** is revealed. Neither institution should receive the other institution's raw input. The threshold is a configurable *experimental* parameter; it is not a SOCIAREM-approved eligibility or classification rule.

The repository uses the **MP-SPDZ** compiler (Python-like `.mpc` programs), Python 3 standard library for preparing data and testing, and **Semi2k** for initial two-party, semi-honest experiments. Household alignment is assumed in v0; PSI/private record linkage and real institutional deployment are out of scope.

## Quick start (Linux / WSL)

1. Install MP-SPDZ following the [official installation instructions](https://mp-spdz.readthedocs.io/en/latest/readme.html). Prefer release `v0.4.3`; install its build prerequisites. MP-SPDZ is not vendored into this repository.
2. From this repository, run `bash scripts/run_demo.sh /absolute/path/to/MP-SPDZ 10`. This generates synthetic inputs for both parties, compiles the `.mpc` program, runs the Semi2k protocol locally, and checks the observed flags against the plain-text reference.
3. Run unit tests with `python3 -m unittest discover -s tests -v`; the unit tests do **not** require MP-SPDZ.

The demo copies **synthetic** input files into the MP-SPDZ working directory. For real institutions, each party must create and manage its own private input file on an isolated host. Do not use personal or sensitive records in this demo.

For reproducibility, see `docs/experiment.md` and `docs/threat-model.md`. The MP-SPDZ backend is not yet validated against a locally executed integration test in this repository.

## Scope and non-goals

- One public output bit per household; synthetic records are pre-aligned in a shared public order.
- Positive income, nonnegative expenditure, euro-cent integer units.
- Security target: semi-honest two-party MPC, **not** malicious-party robustness, output privacy, end-to-end identity alignment, GDPR compliance, or EDC integration.
- Built for algorithmic validation and future protocol benchmarking; no real-world vulnerability decisions.
