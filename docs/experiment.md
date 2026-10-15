# Experiment protocol

- **Question:** Can two holders of vertically partitioned synthetic attributes compute a thresholded energy-burden condition without disclosing raw attributes?
- **Plaintext function:** `100 * annual_energy_expenditure_cents > threshold_percent * annual_equivalent_income_cents`. Integer arithmetic; strictly greater than the threshold, not greater-than-or-equal.
- **Public information:** record count and order, threshold (integer percent), and one result bit per record.
- **Private inputs:** P0 energy expenditure; P1 equivalent income. Never put actual institutional data in this demonstration.
- **Baseline:** `src/reference.py` and `tests/test_reference.py`.
- **MP-SPDZ program:** `src/energy_burden.mpc` illustrates a fixed 4-household circuit. `src/prepare_experiment.py` generates an N-household copy in the external MP-SPDZ checkout and separate local input files.
- **Runner:** `bash scripts/run_demo.sh /absolute/path/to/MP-SPDZ 10` on Linux/WSL after building MP-SPDZ with Semi2k support. It runs the protocol via the supplied `Scripts/semi2k.sh` helper, captures logs and compares flags. Semi2k is not a malicious-secure protocol.
- **Tests:** `python3 -m unittest discover -s tests -v` (no SMPC dependencies).
- **Status:** the Python-side baseline is testable independently. MP-SPDZ execution needs validation in a machine with the MP-SPDZ build dependencies; do not report performance measurements until it runs.
- **Reproducibility:** report MP-SPDZ git commit/tag, compiler flags, party count, security setting, CPU/RAM, OS, network RTT, household count, wall-clock runtime and communication (when available). Repeat multiple trials before interpreting performance.
- **Next steps:** independent party execution; PSI for entity matching; policy-controlled output; >2 input owners; arithmetic scoring/ranking; comparative protocol benchmarks; EDC orchestration.
