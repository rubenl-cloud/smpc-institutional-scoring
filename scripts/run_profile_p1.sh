#!/usr/bin/env bash
# bash scripts/run_profile_p1.sh /path/to/MP-SPDZ [burden_pct] [median_cents] [poverty_pct]
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MPC="$(cd "${1:?Supply the MP-SPDZ installation path}" && pwd)"
BURDEN="${2:-10}"
MEDIAN="${3:-1800000}"
POVERTY="${4:-60}"
if [[ ! -x "$MPC/semi2k-party.x" ]]; then
  echo "Missing MP-SPDZ semi2k-party.x: build with make -j2 semi2k-party.x" >&2
  exit 2
fi
python3 "$REPO/src/prepare_profile_p1.py" "$MPC" --burden "$BURDEN" --median "$MEDIAN" --poverty "$POVERTY"
(
  cd "$MPC"
  ./compile.py -R 64 profile_p1
  PLAYERS=3 bash Scripts/semi2k.sh profile_p1
) | tee "$REPO/profile_p1_execution.log"
python3 "$REPO/src/check_profile_p1.py" "$REPO/profile_p1_execution.log" "$MPC/expected_profile_p1.txt"
