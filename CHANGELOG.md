# Changelog

All notable changes to this project are documented in this file.

## Unreleased

## 0.6.0

### Breaking changes

- **`complexity_weights` is JSON-only.** The comma-separated `key:value` form is removed. Set `complexity_weights` to a JSON object string (for example `{"joins":2,"derived_tables":0}`) or `{}` for defaults. Migrate existing `ctes:2,joins:2,...` values to the equivalent JSON object.

### Changed

- Centralized CPX rule metadata (thresholds, presets, report limits, SARIF rule IDs) in a shared registry used by lint rules, report, and SARIF output.
- Shared violation message builders for C201 aggregate score and C107 CTE dependency depth; report and policy loading aligned with the registry.
- Metric lint rules C102–C106 use a common outer-select evaluation path with a nested-select guard.
- CLI `report` help references ADR 0007 (lint crawl scope vs report file rollup).

### Added

- ADR 0007: lint evaluation scope vs report file rollup.
- Contract tests for lint vs report threshold parity, including documented C107 scope differences.

## 0.5.4

### Changed

- HTML report: shorter file paths relative to scan roots (report path arguments, then longest common prefix); **Full paths** toggle in Filters.
- HTML report: column header help on Path, Score, Findings, and Errors (hover or keyboard focus).
- HTML report: Files table default page size 50.
- HTML report: **Details** overflow fix for narrow embeds (~500px previews).
- HTML report: removed Top directories panel and Filtered files by directory chart (immediate-parent rollups did not match typical dbt model folder layouts).

## 0.5.2

### Added

- CLI `--version` flag prints the installed package version.

### HTML report

- **Details** is available when aggregate score is positive (not only when findings exist); scored files with no threshold violations show a score-context summary in the expanded panel.

## 0.4.1

### Patch notes

- Patch release (version bump only).

## 0.4.0

### Breaking

- **SQLFluff 4 required.** The package now depends on `sqlfluff>=4.0.0,<5.0.0`. SQLFluff 3.x is not supported. If you are still on SQLFluff 3, pin an earlier `sqlfluff-complexity` release (for example `sqlfluff-complexity<0.4`) until you upgrade SQLFluff.
- For dbt projects, use **`sqlfluff-templater-dbt` 4.x** alongside SQLFluff 4 (for example `sqlfluff-templater-dbt>=4.0.0,<5.0.0`).

### Notes

- Integration tests for the dbt mini fixture were updated for metric values produced against SQLFluff 4 parse trees (`cte_dependency_depth`, nested `case_expression` depth).
