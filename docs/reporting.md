# Reporting

The native CPX rules are for enforcement through `sqlfluff lint`. The companion `sqlfluff-complexity report` command is for non-blocking analysis and CI artifacts.

Report mode uses the same SQLFluff parser, metric collector, scoring weights, thresholds, and path overrides as the native rules. **No dbt artifacts** (`manifest.json`, `run_results.json`, `catalog.json`, or DAG metadata) are read; analysis is SQLFluff parse-tree only.

## Console Report

Analyze one or more SQL files:

```bash
sqlfluff-complexity report --dialect postgres models/orders.sql
```

The console output includes one row per file:

```text
sqlfluff-complexity report
path score ctes joins subquery_depth case_expressions boolean_operators window_functions cte_dependency_depth set_operation_count expression_depth
models/orders.sql 14 1 2 0 1 3 1 2 0 1
```

When findings exist, each rule line may append a short bracketed contributor summary (`line` / `col` / segment type) so reviewers can jump to the SQLFluff segments that drove the metric.

Use `--config` to apply your SQLFluff configuration:

```bash
sqlfluff-complexity report \
  --dialect snowflake \
  --config .sqlfluff \
  models/staging/orders.sql
```

Optional per-rule settings (in `.sqlfluff`) tune verbosity without changing thresholds:

- `show_contributors` (default `true`): include compact contributor locations in lint messages and reports.
- `max_contributors` (default `3`): cap how many contributor lines are shown per violation.

### Interpreting `cte_dependency_depth` in reports

The **`cte_dependency_depth`** column (and JSON `metrics.cte_dependency_depth`) is the **maximum**
dependency-chain depth **across every `WITH` block** in that file’s parse tree. **`CPX_C107`** compares
thresholds per **`WITH` clause** when linting—so one large report number does not imply every outer
`WITH` failed lint if only a nested `WITH` carried the chain. Use findings or `sqlfluff lint` output
when reconciling report rows with rule failures.

## JSON Report

For automation and lightweight CI artifacts, use `--format json`. The top-level payload includes `schema_version` `1.1`, `version` (package version), `tool`, per-file `entries`, and a flat `findings` array built from the same **ComplexityFinding** model as lint and SARIF.

Each finding includes `rule_id`, `level`, `message`, `remediation`, `path`, `line`, `column`, `metric`, `threshold`, `score` (metric actual for threshold rules; aggregate score for CPX_C201), `aggregate_score` (file-level weighted score when applicable), full `metrics` counters, and `contributors` (metric, line, column, segment_type, reason, truncated `raw`).

Parse failures use `score: null`, `metrics: null` on the entry, and a `CPX_PARSE_ERROR` finding.

```bash
sqlfluff-complexity report \
  --dialect postgres \
  --config .sqlfluff \
  --format json \
  --output complexity.json \
  models/
```

Example (excerpt):

```json
{
  "schema_version": "1.1",
  "version": "0.1.0",
  "tool": "sqlfluff-complexity",
  "findings": [
    {
      "rule_id": "CPX_C102",
      "level": "warning",
      "message": "CPX_C102: join count 4 exceeds max_joins=2. Consider reducing join fan-in...",
      "remediation": "Consider reducing join fan-in, moving enrichment upstream...",
      "path": "models/orders.sql",
      "line": 3,
      "column": 1,
      "metric": "joins",
      "threshold": 2,
      "score": 4,
      "aggregate_score": 42,
      "metrics": {
        "ctes": 0,
        "joins": 4,
        "subqueries": 0,
        "subquery_depth": 0,
        "case_expressions": 0,
        "boolean_operators": 0,
        "window_functions": 0,
        "cte_dependency_depth": 0,
        "set_operation_count": 0,
        "expression_depth": 0
      },
      "contributors": [
        {
          "metric": "joins",
          "line": 5,
          "column": 1,
          "segment_type": "join_clause",
          "reason": "join clause",
          "raw": "JOIN ..."
        }
      ]
    }
  ],
  "entries": []
}
```

## SARIF Report

Generate SARIF for code-scanning workflows:

```bash
sqlfluff-complexity report \
  --dialect postgres \
  --config .sqlfluff \
  --format sarif \
  --output complexity.sarif \
  models/
```

SARIF `2.1.0` includes `runs[0].tool.driver.name` `sqlfluff-complexity`, **rules** metadata for `CPX_C101`–`CPX_C107`, `CPX_C201`, and `CPX_PARSE_ERROR` (with remediation in `help` / `fullDescription`), and **results** with `ruleId`, `level`, `message.text`, `locations[].physicalLocation` (`artifactLocation.uri` plus `region.startLine` / `startColumn`). When metrics exist, each result includes `properties.score` (aggregate complexity score), `properties.metrics`, and `properties.remediation`. Parse-error results omit `properties` so automation can distinguish read/parse failures.

The SARIF output does not embed full SQL source text in messages.

## Parse And Read Errors

By default, report mode records parse/read errors in the report output and exits successfully. Use `--fail-on-error` when automation should fail if any input cannot be read or parsed.

```bash
sqlfluff-complexity report \
  --dialect postgres \
  --fail-on-error \
  models/
```

## When To Use Report Mode

Use report mode when:

- you want baseline metrics before enabling enforcement
- CI should publish findings without failing immediately
- you want SARIF artifacts for code-scanning review

Use native SQLFluff rules when:

- the threshold is ready to enforce
- developers should receive inline lint feedback
- `noqa` and normal SQLFluff rule selection should apply

## Rollout Pattern

1. Run report mode against the whole project.
2. Tune thresholds and path overrides in `.sqlfluff`.
3. Start enforcing one or two high-signal rules.
4. Add `CPX_C201` after the aggregate score budget feels stable.

See [configuration](configuration.md) for threshold and path override examples.

See the [docs index](index.md) for the rest of the user documentation.
