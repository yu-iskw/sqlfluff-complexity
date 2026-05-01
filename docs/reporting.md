# Reporting

The native CPX rules are for enforcement through `sqlfluff lint`. The companion `sqlfluff-complexity report` command is for non-blocking analysis and CI artifacts.

Report mode uses the same SQLFluff parser, metric collector, scoring weights, thresholds, and path overrides as the native rules.

## Console Report

Analyze one or more SQL files:

```bash
sqlfluff-complexity report --dialect postgres models/orders.sql
```

The console output includes one row per file:

```text
sqlfluff-complexity report
path score ctes joins subquery_depth case_expressions boolean_operators window_functions
models/orders.sql 14 1 2 0 1 3 1
```

Use `--config` to apply your SQLFluff configuration:

```bash
sqlfluff-complexity report \
  --dialect snowflake \
  --config .sqlfluff \
  models/staging/orders.sql
```

## JSON Report

For automation and lightweight CI artifacts, use `--format json`. The payload uses `schema_version` `1.0`, lists one object per input path under `entries`, and includes per-file `score`, `metrics`, `findings`, and `errors`. Parse failures use `score: null` and `metrics: null`.

```bash
sqlfluff-complexity report \
  --dialect postgres \
  --config .sqlfluff \
  --format json \
  --output complexity.json \
  models/
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

The SARIF output includes CPX rule IDs such as `CPX_C102` and `CPX_C201`, but does not embed full SQL text. When metrics are available for a file, each finding may include a `properties` object with `score` and a `metrics` map (file-level values, including for threshold findings).

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
- you are calibrating aggregate score thresholds

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
