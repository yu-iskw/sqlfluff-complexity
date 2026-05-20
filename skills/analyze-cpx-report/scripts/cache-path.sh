#!/usr/bin/env bash
# Print absolute path to the JSON cache file for the current cache key.
# Environment: CPX_REPORT_DIALECT (default ansi), CPX_REPORT_CONFIG (optional),
# CPX_REPORT_RECURSIVE (optional, non-empty => recursive scan in key),
# CPX_REPORT_CACHE_DIR (optional). Positional args: same path list as report.
set -euo pipefail
exec python3 -c '
import hashlib
import os
import sys
import tempfile

dialect = os.environ.get("CPX_REPORT_DIALECT", "ansi")
cfg = os.environ.get("CPX_REPORT_CONFIG", "")
rec = os.environ.get("CPX_REPORT_RECURSIVE", "")
paths = sorted({os.path.abspath(p) for p in sys.argv[1:]})
key = "|".join([os.getcwd(), dialect, cfg, rec] + paths)
digest = hashlib.sha256(key.encode()).hexdigest()[:20]
base = os.environ.get("CPX_REPORT_CACHE_DIR") or tempfile.gettempdir()
os.makedirs(base, exist_ok=True)
print(os.path.join(base, f"sqlfluff-complexity-report-{digest}.json"))
' -- "$@"
