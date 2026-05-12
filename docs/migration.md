# Migration Guide

This page covers breaking changes in the P0 accuracy-and-policy release and how to migrate existing configurations and integrations.

## What Changed

### 1. Severity model added to report output

All `ComplexityFinding` objects now have a `level` field typed as `SeverityLevel` (a `str` subclass). In prior releases, `level` was a plain `"warning"` string in all findings.

**Impact on JSON output:** The `"level"` field in JSON reports is still a plain string (`"warning"`, `"error"`, or `"info"`). No structural change is needed for consumers that already read `finding["level"]`. The field now carries configurable severity.

**Impact on SARIF output:** The SARIF `level` field now maps `SeverityLevel.info` to `"note"` (SARIF 2.1.0 does not support `"info"` as a valid level value). If your SARIF-consuming tool previously saw `"warning"` for all results and now receives `"note"`, this reflects that the finding was configured as `severity = info`.

**Impact on console output:** Each finding line now has a `[warning]`, `[error]`, or `[info]` prefix. If you parse console output, update your parsers to account for this prefix.

### 2. New config keys: `severity` and `severity_bands`

Each CPX rule section now accepts two optional keys:

```ini
[sqlfluff:rules:CPX_C102]
max_joins = 6
severity = warning
severity_bands = [{"threshold": 10, "severity": "error"}]
```

These keys affect report output only (see [SQLFluff lint behavior](sqlfluff-lint-behavior.md)). They are not required; the default is `severity = warning` with no bands. If you do not add these keys, behavior is identical to the previous release.

### 3. `ConfigValidationError` replaces bare `ValueError` for severity config errors

If you configure `severity = critical` (an invalid value), the error raised is now `ConfigValidationError` instead of a generic `ValueError`. `ConfigValidationError` is a `ValueError` subclass, so existing `except ValueError` catch sites continue to work. The error message includes the config key, the invalid value, and the expected values.

### 4. Config validation now covers severity keys

`sqlfluff-complexity config-check` now validates `severity` and `severity_bands` values in addition to the existing `complexity_weights`, `path_overrides`, and `mode` validation. Invalid values exit non-zero with a structured error message.

## How to Migrate

### Step 1: Update SARIF consumers (if applicable)

If you consume SARIF output and check `result["level"]`, note that findings previously at `"warning"` will still be `"warning"` unless you explicitly configure `severity = info`. If you configure any rule with `severity = info`, those SARIF results will have `"level": "note"` (not `"info"`).

No action needed if all rules use the default `severity = warning`.

### Step 2: Update console output parsers (if applicable)

The console report now prefixes each finding line with `[warning]`, `[error]`, or `[info]`. Update any shell parsing logic that depends on the exact line format.

Before:
```
  CPX_C102: join count 9 exceeds max_joins=8.
```

After:
```
  [warning] CPX_C102: join count 9 exceeds max_joins=8.
```

### Step 3: Optionally configure severity

To escalate certain rules to `error` for CI failure gating (once that integration is added), add to your `.sqlfluff`:

```ini
[sqlfluff:rules:CPX_C102]
severity = error
```

Or use severity bands to escalate at higher thresholds:

```ini
[sqlfluff:rules:CPX_C102]
max_joins = 6
severity = warning
severity_bands = [{"threshold": 12, "severity": "error"}]
```

This has no effect on `sqlfluff lint` behavior. It affects only report mode output formatting.

### Step 4: Run config-check

After updating your config, validate with:

```bash
sqlfluff-complexity config-check --dialect postgres --config .sqlfluff
```

Any invalid `severity` values are reported immediately with the offending key and expected values.

## What Did Not Change

- Metric counting semantics for all CPX rules (C101–C110, C201) are unchanged.
- Threshold keys (`max_joins`, `max_ctes`, etc.) are unchanged.
- `path_overrides`, `complexity_weights`, and `mode` are unchanged.
- `sqlfluff lint` pass/fail behavior is controlled by threshold keys, not `severity`. Severity is a report-mode-only concept.
- No dbt artifact support was added. `manifest.json`, `run_results.json`, `catalog.json`, and DAG metadata are not read.

## Troubleshooting

**`ConfigValidationError: Invalid value 'critical' for CPX_C102.severity`**

The `severity` key accepts only `"info"`, `"warning"`, or `"error"`. Check spelling and case (all lowercase).

**`ConfigValidationError` on `severity_bands`**

The `severity_bands` value must be a JSON array string. Valid format:

```ini
severity_bands = [{"threshold": 10, "severity": "error"}]
```

Each object requires both `threshold` (non-negative integer) and `severity` (`"info"`, `"warning"`, or `"error"`). The value must be valid JSON (double-quoted keys, no trailing commas).

**SARIF `"level": "note"` instead of `"warning"`**

This means a rule is configured with `severity = info`. Check your `.sqlfluff` for `severity = info` entries.

See the [docs index](index.md) for the rest of the user documentation.
