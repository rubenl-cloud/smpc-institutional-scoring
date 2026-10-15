#!/usr/bin/env bash
# Run with: bash scripts/run_demo.sh /absolute/path/to/MP-SPDZ [threshold_percent]
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MPC_ROOT="${1:?Pass the path to an installed MP-SPDZ checkout}"
THRESHOLD="${2:-10}"
MPC_ROOT="$(cd "$MPC_ROOT" && pwd)"
test -x "$MPC_ROOT/semi2k-party.x" || {
  echo "Missing semi2k-party.x: build MP-SPDZ for semi2k first." >&2; exit 2;
}
python3 "$REPO_ROOT/src/prepare_experiment.py" "$MPC_ROOT" --threshold "$THRESHOLD"
(
  cd "$MPC_ROOT"
  ./compile.py -R 64 energy_burden
  # MP-SPDZ's provided script starts multiple local player processes.
  bash Scripts/semi2k.sh energy_burden > "$REPO_ROOT/mp-spdz-run.log" 2>&1
)
python3 "$REPO_ROOT/src/check_output.py" "$REPO_ROOT/mp-spdz-run.log" "$MPC_ROOT/expected_energy_burden.txt"
echo "Run log: $REPO_ROOT/mp-spdz-run.log"
