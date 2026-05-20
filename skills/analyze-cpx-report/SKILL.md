---
name: analyze-cpx-report
description: Runs or reuses a cached sqlfluff-complexity JSON report via bundled shell scripts (default 5-minute TTL), then interprets entries, findings, scores, and errors for large dbt or SQL projects. Use when analyzing complexity reports, CPX JSON output, cached sqlfluff-complexity runs, or repeated report analysis on large trees.
disable-model-invocation: true
---

# Analyze CPX report (cached JSON)

Use this skill when an agent (or user) needs **insights from `sqlfluff-complexity report`** on a **large** tree of SQL files (for example dbt `models/`) and repeated full runs are too slow.

## Prerequisites

- `sqlfluff-complexity` on `PATH`, unless `CPX_REPORT_PREFIX` supplies a prefix (for example `uv run`).
- **Bash** (scripts use bash-only features such as `mapfile`).
- For cache file names: **one of** `sha256sum`, `openssl dgst -sha256`, or `shasum -a 256` on `PATH`.
- For freshness checks: **`stat`** with GNU (`stat -c %Y`) or BSD (`stat -f %m`) semantics.

## Utility scripts (preferred)

From the directory that contains this `SKILL.md`, scripts live under `scripts/`. **Execute** them (do not paste duplicated logic into chat). There is **no Python** in this skill: helpers live in [`scripts/lib.sh`](scripts/lib.sh) (sourced by the other scripts; do not run it as a standalone program).

| Script | Role |
| ------ | ---- |
| [`scripts/ensure-json-report.sh`](scripts/ensure-json-report.sh) | Resolve cache path, reuse JSON if within TTL, else run `sqlfluff-complexity report --format json`. **Stdout:** single line, absolute path to the JSON file. **Stderr:** status messages. |
| [`scripts/cache-path.sh`](scripts/cache-path.sh) | Print cache path only (same key as ensure; does **not** create directories). Requires the same environment variables as `ensure-json-report.sh` for dialect/config/recursive. Args: report path list. |
| [`scripts/is-cache-fresh.sh`](scripts/is-cache-fresh.sh) | Exit `0` if the given cache file exists and is **strictly younger** than `CPX_REPORT_CACHE_TTL_SECONDS` (default 300); otherwise exit `1`. |

### Example

```bash
SKILL_ROOT=/path/to/analyze-cpx-report   # directory containing SKILL.md
export CPX_REPORT_CACHE_TTL_SECONDS=300
CPX_CACHE_FILE="$("$SKILL_ROOT/scripts/ensure-json-report.sh" -d snowflake -r -- models)"
# Read JSON at "$CPX_CACHE_FILE" for analysis
```

Force regeneration once: `--force` or `CPX_REPORT_FORCE=1`.

## Parameters

- **Paths**: same as `sqlfluff-complexity report` (use `-r` for directories with nested `.sql` files).
- **TTL**: `CPX_REPORT_CACHE_TTL_SECONDS` (default **300**).
- **Cache directory**: `CPX_REPORT_CACHE_DIR` (optional; default is the OS temp directory).

## JSON analysis (after you have a path)

- Top-level keys (`schema_version` **1.1**): `tool`, `version`, `schema_version`, `entries`, `findings`.
- **`entries`**: per-file `path`, `score`, `metrics`, `errors`, short `findings`, and `findings_detail` (full remediation and contributors).
- **`findings`**: flattened list for cross-file sorting and rule counts.

Summarize by `rule_id`, worst files by `score` / `aggregate_score`, and any parse or templating `errors`.

## Guardrails

- TTL **does not** detect edits to SQL or config; after meaningful changes, use `--force` or delete the cache file.
- Directories without `-r` / `--recursive` make the CLI exit **2**.
- Keep dbt `templater` settings in **root** SQLFluff config (see [configure-cpx](../configure-cpx/SKILL.md)).

## Related

- [configure-cpx](../configure-cpx/SKILL.md) — adopt thresholds and presets before deep report analysis.
- Upstream: [sqlfluff-complexity](https://github.com/yu-iskw/sqlfluff-complexity/).
