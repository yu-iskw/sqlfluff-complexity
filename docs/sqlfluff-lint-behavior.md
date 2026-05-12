# SQLFluff Lint Behavior

This page explains how `severity` and `severity_bands` config keys interact with `sqlfluff lint`, and clarifies the boundary between lint enforcement and report mode.

## Summary

| Feature | `sqlfluff lint` | `sqlfluff-complexity report` |
| ------- | --------------- | ---------------------------- |
| Metric counting | Yes | Yes |
| Threshold enforcement (`max_joins`, etc.) | Yes — violation = lint failure | Yes — violation = finding in output |
| `severity` / `severity_bands` config keys | **Ignored** | Used to set `finding.level` |
| `noqa` inline suppression | Yes | No |
| Output format | SQLFluff lint format | Console, JSON, SARIF, HTML |
| Exit code on violation | Non-zero | Zero (unless `--fail-on-error`) |

## How severity interacts with `sqlfluff lint`

The `severity` and `severity_bands` keys in `[sqlfluff:rules:CPX_*]` sections are **report-mode-only** configuration. They control the `level` field on `ComplexityFinding` objects produced by the report command.

**`sqlfluff lint` does not read `severity` or `severity_bands`.** These keys are present in `config_keywords` so SQLFluff does not reject them as unknown config, but the lint rules do not use them to change pass/fail behavior. A rule configured with `severity = info` still fails lint when the metric exceeds `max_*`.

**Lint pass/fail is controlled exclusively by threshold keys** (`max_joins`, `max_ctes`, etc.) and `mode`.

## How `mode = report` works

Setting `mode = report` in a rule section (or via `path_overrides`) suppresses lint violation output for that rule:

```ini
[sqlfluff:rules:CPX_C201]
mode = report
```

This is different from `severity = info`. With `mode = report`, the rule produces no lint violations. With `severity = info`, the rule still produces lint violations when the threshold is exceeded — but report-mode findings will show `[info]` in the output.

To make a metric non-blocking in lint, use `mode = report`. To categorize a metric as informational in report output, use `severity = info`.

## `noqa` suppression

CPX rules respect SQLFluff's `-- noqa` inline suppression:

```sql
select *
from a
join b on a.id = b.id  -- noqa: CPX_C102
join c on a.id = c.id
```

This works for `sqlfluff lint` only. Report mode does not apply `noqa` suppression — all metrics are collected from the parse tree regardless of inline comments.

## Severity in report output

When report mode is used, each `ComplexityFinding` carries a `level` derived from:

1. The base `severity` for the rule (default: `warning`)
2. Any matching `severity_bands` entry for the actual metric value

The highest matching band wins. If the metric value is below all band thresholds, the base `severity` applies.

Example:

```ini
[sqlfluff:rules:CPX_C102]
max_joins = 4
severity = warning
severity_bands = [{"threshold": 10, "severity": "error"}]
```

- join count = 6 → base `severity` applies → `level = "warning"`
- join count = 12 → band threshold 10 is exceeded → `level = "error"`

This level appears in JSON `"level"` field, SARIF `"level"` field (`"info"` maps to `"note"`), and as a `[warning]`/`[error]`/`[info]` prefix in console output.

## Exit codes

`sqlfluff lint` exits non-zero when any rule violation is found (unless `mode = report` suppresses it).

`sqlfluff-complexity report` exits zero by default, even when findings exist. Use `--fail-on-error` to exit non-zero when any finding is present or any file fails to parse:

```bash
sqlfluff-complexity report --dialect postgres --fail-on-error models/
```

See the [docs index](index.md) for the rest of the user documentation.
