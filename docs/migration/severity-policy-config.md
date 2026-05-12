# Migration: severity policy configuration (breaking change)

## What changed

CPX rules now support explicit severity policy:

- `severity` (default rule severity): `info`, `warning`, `error`
- `severity_bands` (JSON array): threshold-based overrides

## Old vs new configuration

Old threshold-only style:

```ini
[sqlfluff:rules:CPX_C102]
max_joins = 8
```

New severity-aware style:

```ini
[sqlfluff:rules:CPX_C102]
max_joins = 8
severity = warning
severity_bands = [{"min": 9, "severity": "warning"}, {"min": 13, "severity": "error"}]
```

Aggregate score:

```ini
[sqlfluff:rules:CPX_C201]
max_complexity_score = 60
severity = warning
severity_bands = [{"min": 61, "severity": "warning"}, {"min": 90, "severity": "error"}]
complexity_weights = {"joins":2,"subquery_depth":4}
```

`complexity_weights` above is intentionally partial; omitted keys continue using packaged defaults.

## Severity resolution

1. Start with rule `severity`.
2. For each matching band where `value >= min`, apply that band.
3. Highest matching `min` wins.

## Report output changes

- JSON findings include `severity`.
- SARIF maps severity deterministically:
  - `info` -> `note`
  - `warning` -> `warning`
  - `error` -> `error`
- HTML and console outputs show severity for each finding.

## SQLFluff native lint limitation

SQLFluff rule violations are still failures when emitted. The nuanced severity model is fully represented in `sqlfluff-complexity report` outputs; lint messages include severity text but do not provide non-failing warning mode per violation.

## Config validation errors

`sqlfluff-complexity config-check` now fails fast for invalid severity settings, including:

- unknown severity strings
- malformed `severity_bands` JSON
- non-list band payloads
- missing `min` / `severity`
- negative or non-numeric `min`
- duplicate band thresholds

## Recommended rollout

1. Keep thresholds unchanged and set `severity = warning`.
2. Add `severity_bands` for escalation only at high values.
3. Roll out report artifacts (JSON/SARIF/HTML) in CI first.
4. Tighten thresholds and/or escalate to `error` after baseline stabilization.
