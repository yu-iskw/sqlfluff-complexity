#!/usr/bin/env bash
# Exit 0 if CACHE_FILE exists and mtime age is strictly less than TTL; else exit 1.
# Environment: CPX_REPORT_CACHE_TTL_SECONDS (default 300).
set -euo pipefail
cache_file=${1:?usage: is-cache-fresh.sh CACHE_FILE}
exec python3 -c '
import os
import sys
import time

ttl = int(os.environ.get("CPX_REPORT_CACHE_TTL_SECONDS", "300"))
path = sys.argv[1]
try:
    age = time.time() - os.path.getmtime(path)
except OSError:
    sys.exit(1)
sys.exit(0 if age < ttl else 1)
' "$cache_file"
