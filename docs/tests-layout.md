# Test directory layout

Tests live under `src/sqlfluff_complexity/tests/` next to the package (see [AGENTS.md](../AGENTS.md)). The layout is **hybrid**: package-internal unit tests mirror `sqlfluff_complexity.core`, while cross-cutting suites sit in named sibling folders.

## Layout

| Area         | Path                 | Purpose                                                                                |
| ------------ | -------------------- | -------------------------------------------------------------------------------------- |
| Core package | `tests/core/`        | Mirrors `sqlfluff_complexity.core` — analysis, config, messages, model, scan.          |
| Reporting    | `tests/reporting/`   | Console report CLI, SARIF, golden JSON, per-rule contributor reporting.                |
| Integration  | `tests/integration/` | SQLFluff plugin discovery and CLI, dbt templater, package CLI smoke, version metadata. |
| Rules        | `tests/rules/`       | Rule-focused behavior and SQLFluff lint integration against CPX rules.                 |

## Shared assets at the tests root

- **`fixture_loader.py`**, **`sqlfluff_helpers.py`** — shared helpers imported as `sqlfluff_complexity.tests.*`.
- **`fixtures/`** — SQL snippets, expected metrics JSON, and the minimal dbt project used by templater tests.

Place new files in the folder that matches the primary concern: core internals under `core/`, reporting artifacts under `reporting/`, end-to-end or tooling glue under `integration/`, rule semantics and lint outcomes under `rules/`.
