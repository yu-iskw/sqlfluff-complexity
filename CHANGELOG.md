# Changelog

All notable changes to this project are documented in this file.

## Unreleased

### Breaking changes

- **`complexity_weights` is JSON-only.** The comma-separated `key:value` form is removed. Set `complexity_weights` to a JSON object string (for example `{"joins":2,"derived_tables":0}`) or `{}` for defaults. Migrate existing `ctes:2,joins:2,...` values to the equivalent JSON object.

## 0.4.1

### Patch notes

- Patch release (version bump only).

## 0.4.0

### Breaking

- **SQLFluff 4 required.** The package now depends on `sqlfluff>=4.0.0,<5.0.0`. SQLFluff 3.x is not supported. If you are still on SQLFluff 3, pin an earlier `sqlfluff-complexity` release (for example `sqlfluff-complexity<0.4`) until you upgrade SQLFluff.
- For dbt projects, use **`sqlfluff-templater-dbt` 4.x** alongside SQLFluff 4 (for example `sqlfluff-templater-dbt>=4.0.0,<5.0.0`).

### Notes

- Integration tests for the dbt mini fixture were updated for metric values produced against SQLFluff 4 parse trees (`cte_dependency_depth`, nested `case_expression` depth).
