#!/usr/bin/env bash
# Exit 0 if CACHE_FILE exists and mtime age is strictly less than TTL; else exit 1.
# Environment: CPX_REPORT_CACHE_TTL_SECONDS (default 300, digits only).
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

cache_file=${1:?usage: is-cache-fresh.sh CACHE_FILE}

if [[ ! -f "$cache_file" ]]; then
  exit 1
fi

ttl_raw=${CPX_REPORT_CACHE_TTL_SECONDS:-300}
if [[ ! "$ttl_raw" =~ ^[0-9]+$ ]]; then
  ttl_raw=300
fi

now=$(date +%s)
mt=$(cpx_mtime_epoch "$cache_file")
age=$((now - mt))

if ((age < 0)); then
  exit 1
fi
if ((age < ttl_raw)); then
  exit 0
fi
exit 1
