---
name: analyze-cpx-report
description: Run or reuse a cached sqlfluff-complexity JSON report (default 5-minute TTL), then interpret entries, findings, scores, and errors for large dbt or SQL projects without re-parsing on every agent turn.
---

# Analyze CPX report (cached JSON)

Use this skill when an agent (or user) needs **insights from `sqlfluff-complexity report`** on a **large** tree of SQL files (for example dbt `models/`) and repeated full runs are too slow.

## Prerequisites

- `sqlfluff-complexity` on `PATH` (or invoke via `uv run sqlfluff-complexity` from a project that lists the package as a dependency).
- A shell with `python3` available (used for a portable cache key and file-age check).

## Parameters (conceptual)

- **Paths**: same positional paths you would pass to `sqlfluff-complexity report` (files and/or directories). Use `-r` / `--recursive` when passing directories that contain nested `.sql` files.
- **Dialect / config**: match the project’s SQLFluff settings (`--dialect`, optional `--config`).
- **TTL**: default **300 seconds** (5 minutes). Override with environment variable `CPX_REPORT_CACHE_TTL_SECONDS` (integer seconds).
- **Cache directory**: default platform temp (`$TMPDIR` on Unix, `%TEMP%` on Windows). Override with `CPX_REPORT_CACHE_DIR` (must exist or be creatable).

## Workflow

1. **Choose cache inputs** so the cache file name changes when the scan meaningfully changes: working directory, `--dialect`, `--config` path, `--recursive` flag, and the list of path arguments (normalized to absolute paths in sorted order for stability).

2. **Resolve cache path** using the helper below (copy into the shell session or wrap in a project script). The cache file is a single JSON document per unique input tuple.

3. **Refresh policy**

   - If the cache file **exists** and its age is **strictly less than** the TTL, **do not** re-run the report; load and analyze that JSON.
   - Otherwise run:

     ```bash
     sqlfluff-complexity report --format json --output "$CPX_CACHE_FILE" \
       --dialect "<dialect>" ${CONFIG_FLAG:+"--config" "$CONFIG_PATH"} \
       ${RECURSIVE_FLAG} -- <paths...>
     ```

     Use `--recursive` when analyzing directory trees (required by the CLI when the argument is a directory).

4. **Analyze the JSON** (no need to shell out again while the cache is fresh):

   - Top-level keys (schema version **1.1**): `tool`, `version`, `schema_version`, `entries`, `findings`.
   - **`entries`**: one object per SQL file with `path`, `score`, `metrics` (may be `null` on parse failure), `errors` (strings), `findings` (short objects: `level`, `message`, `rule_id`), and `findings_detail` (full finding shape including `remediation`, `contributors`, thresholds, and per-rule metrics).
   - **`findings`**: flattened list of all findings in the same canonical shape as each `findings_detail` item—convenient for sorting and filtering across files.
   - Produce **actionable** summaries: counts by `rule_id`, worst files by `score` or `aggregate_score`, parse or templating `errors`, and remediation themes from `remediation` / `message`.

5. **Stale cache**: if the user changed SQL, CPX config, or SQLFluff config since the cache was written, a fresh TTL may still serve **wrong** conclusions. When the user says they just edited models or thresholds, **bypass** the cache (delete the cache file or set `CPX_REPORT_CACHE_TTL_SECONDS=0` for one run).

## Portable cache helper (bash + python3)

```bash
# Inputs — set before calling
: "${CPX_REPORT_DIALECT:=ansi}"
# CPX_REPORT_CONFIG=/abs/path/.sqlfluff   # optional
# CPX_REPORT_RECURSIVE=1                 # set when using directories with -r
# CPX_REPORT_CACHE_TTL_SECONDS=600       # optional override (seconds)
# CPX_REPORT_CACHE_DIR — optional; defaults to tempfile.gettempdir() via python

export CPX_CACHE_FILE
CPX_CACHE_FILE="$(python3 -c '
import hashlib, os, sys, tempfile
dialect = os.environ.get("CPX_REPORT_DIALECT", "ansi")
cfg = os.environ.get("CPX_REPORT_CONFIG", "")
rec = os.environ.get("CPX_REPORT_RECURSIVE", "")
paths = sorted({os.path.abspath(p) for p in sys.argv[1:]})
key = "|".join([os.getcwd(), dialect, cfg, rec] + paths)
digest = hashlib.sha256(key.encode()).hexdigest()[:20]
base = os.environ.get("CPX_REPORT_CACHE_DIR") or tempfile.gettempdir()
os.makedirs(base, exist_ok=True)
print(os.path.join(base, f"sqlfluff-complexity-report-{digest}.json"))
' -- "$@")"

if python3 -c '
import os, sys, time
ttl = int(os.environ.get("CPX_REPORT_CACHE_TTL_SECONDS", "300"))
p = os.environ["CPX_CACHE_FILE"]
try:
    age = time.time() - os.path.getmtime(p)
except OSError:
    sys.exit(1)
sys.exit(0 if age < ttl else 1)
'; then
  echo "Using cached report: $CPX_CACHE_FILE"
else
  echo "Generating report to $CPX_CACHE_FILE"
  # Example — adjust flags and paths:
  # sqlfluff-complexity report --format json --output "$CPX_CACHE_FILE" \
  #   --dialect "$CPX_REPORT_DIALECT" ${CPX_REPORT_CONFIG:+--config "$CPX_REPORT_CONFIG"} \
  #   ${CPX_REPORT_RECURSIVE:+-r} -- models
fi
```

Agents should **read** `$CPX_CACHE_FILE` as JSON after this block (either parse in Python or stream into the model context).

## Guardrails

- Do not treat a cached report as authoritative after **SQL or config** changes unless TTL is zero or the cache file was removed.
- **Directory arguments** without `--recursive` cause the CLI to exit with code 2; always mirror the same invocation the user would run manually.
- For **consumer** dbt projects, keep `templater` and dbt-related SQLFluff settings in **root** config (see the `configure-cpx` skill): nested-directory `templater` overrides are not allowed by SQLFluff.

## Related

- [configure-cpx](../configure-cpx/SKILL.md) — adopt thresholds and presets before deep report analysis.
- Upstream repository: [sqlfluff-complexity](https://github.com/yu-iskw/sqlfluff-complexity/).
