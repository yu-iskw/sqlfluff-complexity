#!/usr/bin/env bash
# Print absolute path to the JSON cache file for the current cache key.
# Environment: CPX_REPORT_DIALECT (default ansi), CPX_REPORT_CONFIG (optional),
# CPX_REPORT_RECURSIVE (optional, non-empty => recursive scan in key),
# CPX_REPORT_CACHE_DIR (optional). Positional args: same path list as report.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

cpx_cache_json_path "$@"
