#!/usr/bin/env bash
# Exit 0 if CACHE_FILE exists and mtime age is strictly less than TTL; else exit 1.
# Environment: CPX_REPORT_CACHE_TTL_SECONDS (default 300, digits only).
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

cpx_is_cache_fresh "${1:?usage: is-cache-fresh.sh CACHE_FILE}"
