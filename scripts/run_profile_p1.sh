#!/usr/bin/env bash
# bash scripts/run_profile_p1.sh /path/to/MP-SPDZ [public burden threshold percent]
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MPC="$(cd "${1:?Supply the MP-SPDZ installation path}" && pwd)"
BURDEN="${2:-10}"
if [[ ! -x "$MPC/semi2k-party.x" ]]; then
  echo "MP-SPDZ semi2k-party.x missing. Build it first: cd MP-SPDZ && make -j2 semi2k-party.x" >&2
  exit 2
fi
python3 "$REPO/src/prepare_profile_p1.py" "$MPC" --burden "$BURDEN"
(
  cd "$MPC"
  ./compile.py -R 64 profile_p1
  PLAYERS=3 bash Scripts/semi2k.sh profile_p1
) | tee "$REPO/profile_p1_execution.log"
python3 "$REPO/src/check_profile_p1.py" "$REPO/profile_p1_execution.log" "$MPC/expected_profile_p1.txt"
