#!/usr/bin/env bash
# Strict build, or explicit hash re-record after an intentional source change.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo 'Usage: OM5_STOCK=/path/to/stock.BIN tools/dev/build.sh NEW_OUTPUT_DIR [--record]' >&2
  exit 2
fi
: "${OM5_STOCK:?Set OM5_STOCK to the official E148 1.1 file}"
if [[ ${2:-} == --record ]]; then
  python3 "$root/tools/oly_patch_record.py" "$root/firmware/om5ii" --stock "$OM5_STOCK" --work "$1"
elif [[ $# == 1 ]]; then
  python3 "$root/tools/oly_patch.py" "$root/firmware/om5ii" --stock "$OM5_STOCK" --out "$1" --decoded
else
  echo 'Only --record is accepted as the second argument' >&2
  exit 2
fi
