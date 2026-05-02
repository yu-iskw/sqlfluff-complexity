# Baseline and regression checks

Large repositories can snapshot complexity metrics in a **baseline** file and run **check** in CI to detect regressions against that snapshot. Analysis uses the same SQLFluff parse tree and metric engine as `report`; **no dbt artifacts** are read.

## Baseline JSON (`schema_version` `1.0`)

Stable fields:

| Field            | Meaning                                                    |
| ---------------- | ---------------------------------------------------------- |
| `schema_version` | Must be `1.0`.                                             |
| `tool`           | Must be `sqlfluff-complexity`.                             |
| `entries`        | Map of normalized relative paths (POSIX) to per-file data. |

Each entry includes:

| Field     | Meaning                                                                                                                                                   |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `score`   | Aggregate weighted complexity score (integer), or omitted when analysis failed.                                                                           |
| `metrics` | Counter map (`ctes`, `joins`, `subqueries`, `subquery_depth`, `case_expressions`, `boolean_operators`, `window_functions`), or omitted when not computed. |
| `errors`  | List of read/parse error strings (may be empty).                                                                                                          |

Paths are normalized relative to the working directory when possible; absolute paths appear only when the file lies outside the current working directory.

## Commands

### Create a baseline

```bash
sqlfluff-complexity baseline create models/ \
  --dialect snowflake \
  --config .sqlfluff \
  --output .sqlfluff-complexity-baseline.json
```

Optional discovery flags match `report`: `--include`, `--exclude`, `--files-from`, `--changed-from`, `--jobs`.

Default output path: `.sqlfluff-complexity-baseline.json`.

### Check against a baseline

```bash
sqlfluff-complexity check models/ \
  --dialect snowflake \
  --config .sqlfluff \
  --baseline .sqlfluff-complexity-baseline.json \
  --fail-on regression
```

Required:

- `--baseline PATH`
- `--fail-on regression|threshold|none`

Optional: `--format console|json`, `--output PATH`, `--fail-on-error`, path discovery flags.

#### `--fail-on` modes

| Mode         | Behavior                                                                                                                                                                                                                                   |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `regression` | Fail when score or any metric **increases** vs baseline for an existing file; fail when a **new** file has policy findings (warnings). Ignores baseline entries for deleted files. Parse/read errors do not fail unless `--fail-on-error`. |
| `threshold`  | Fail when current analysis has **any** policy findings (same notion as lint thresholds). Does not compare to baseline scores.                                                                                                              |
| `none`       | Never fail for complexity findings; use `--fail-on-error` to fail on parse/read errors only.                                                                                                                                               |

### Check JSON (`schema_version` `1.0`)

Top-level keys: `schema_version`, `tool`, `summary` (`files_checked`, `regressions`, `threshold_violations`, `errors`), `results` (array of per-file outcomes).

Each result includes `path`, `status`, and optional `baseline_score`, `current_score`, `changed_metrics`.

## Exit codes

| Code | Meaning                                                                    |
| ---- | -------------------------------------------------------------------------- |
| 0    | Success                                                                    |
| 1    | Check failed (per `--fail-on`) or `--fail-on-error` with parse/read errors |
| 2    | Invalid CLI usage, baseline file, or path resolution (e.g. git failure)    |

See [reporting](reporting.md) for directory discovery, `--include` / `--exclude`, and parallel `--jobs`.
