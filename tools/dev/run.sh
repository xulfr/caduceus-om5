#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
if [[ $# -lt 3 ]]; then
  echo "Usage: OM_EMU_DIR=/path/to/om-emu tools/dev/run.sh BUILD OUT 'keys' [options]" >&2
  exit 2
fi
: "${OM_EMU_DIR:?Set OM_EMU_DIR to the OM-Emu checkout}"
build=$1; out=$2; keys=$3; shift 3
card_args=()
if [[ -n ${CARD:-} ]]; then card_args=("--card=$CARD"); fi
PRE=${PRE:-$root/tools/dev/mount.mjs} OM_EMU_MODEL=E148 node "$root/tools/dev/sess.mjs" "$OM_EMU_DIR" "$build/decoded/0100.bin" "$build/decoded/0101.bin" "$out" "$keys" --ready --peekP "${card_args[@]}" "$@"
