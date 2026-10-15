#!/usr/bin/env bash
# bash scripts/run_profile_p1.sh /path/to/MP-SPDZ [burden_pct] [median_cents] [poverty_pct] [data_dir]
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MPC="$(cd "${1:?Supply the MP-SPDZ installation path}" && pwd)"
BURDEN="${2:-10}"
MEDIAN="${3:-1800000}"
POVERTY="${4:-60}"
DATA_DIR="${5:-$REPO/data}"

if [[ ! -x "$MPC/semi2k-party.x" ]]; then
  echo "Missing MP-SPDZ semi2k-party.x: build with make -j2 semi2k-party.x" >&2
  exit 2
fi

RUN_DIR="$(mktemp -d "${TMPDIR:-/tmp}/profile-p1.XXXXXXXX")"
PROGRAM="profile_p1_demo_$$"
SOURCE_TARGET="$MPC/Programs/Source/$PROGRAM.mpc"
cleanup() {
  rm -rf -- "$RUN_DIR"
  rm -f -- "$SOURCE_TARGET" "$MPC/Programs/Schedules/$PROGRAM.sch"
  rm -f -- "$MPC/Programs/Bytecode/$PROGRAM-0.bc"
}
trap cleanup EXIT

python3 "$REPO/src/prepare_profile_p1.py" "$RUN_DIR" \
  --data-dir "$DATA_DIR" --burden "$BURDEN" --median "$MEDIAN" \
  --poverty "$POVERTY" --program-name "$PROGRAM"
cp -- "$RUN_DIR/$PROGRAM.mpc" "$SOURCE_TARGET"

(
  cd "$MPC"
  ./compile.py -R 64 "$PROGRAM"
  PLAYERS=3 bash Scripts/semi2k.sh "$PROGRAM" -IF "$RUN_DIR/inputs/Input"
) | tee "$RUN_DIR/execution.log"

python3 "$REPO/src/check_profile_p1.py" \
  "$RUN_DIR/execution.log" "$RUN_DIR/expected_profile_p1.txt"
