#!/usr/bin/env bash
# Print absolute path to the JSON cache file for the current cache key.
# Environment: CPX_REPORT_DIALECT (default ansi), CPX_REPORT_CONFIG (optional),
# CPX_REPORT_RECURSIVE (optional, non-empty => recursive scan in key),
# CPX_REPORT_CACHE_DIR (optional). Positional args: same path list as report.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

dialect=${CPX_REPORT_DIALECT:-ansi}
cfg=${CPX_REPORT_CONFIG:-}
rec=${CPX_REPORT_RECURSIVE:-}

abs=()
for p in "$@"; do
  abs+=("$(cpx_abspath "$p")")
done

mapfile -t sorted < <(printf '%s\n' "${abs[@]}" | LC_ALL=C sort -u)
cwd=$(pwd -P)

digest=$(
  {
    printf '%s\n' "$cwd" "$dialect" "$cfg" "$rec"
    ((${#sorted[@]} > 0)) && printf '%s\n' "${sorted[@]}"
  } | cpx_sha256_key20
)

base=$(cpx_default_cache_base)
mkdir -p -- "$base"
# Trim trailing slash from base for predictable join
base=${base%/}
printf '%s/sqlfluff-complexity-report-%s.json\n' "$base" "$digest"
