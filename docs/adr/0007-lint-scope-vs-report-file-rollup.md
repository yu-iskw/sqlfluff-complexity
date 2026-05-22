# ADR 0007: Lint evaluation scope vs report file rollup

- **Status:** Accepted
- **Date:** 2026-05-22
- **Deciders:** Maintainers

## Context

ADR 0002 requires a shared metric engine for SQLFluff lint and the `sqlfluff-complexity report` CLI. Metrics are collected from parse trees via `analyze_segment_tree`, but **where** that tree is rooted and **how** thresholds are applied differs between the two surfaces.

Developers often assume `sqlfluff lint` and `sqlfluff-complexity report` will flag the same violations for the same file and config. Without an explicit contract, subtle scope differences look like bugs.

## Decision

We treat **lint** and **report** as complementary products with different evaluation scopes:

| Surface | Scope | Threshold application |
| ------- | ----- | --------------------- |
| **`sqlfluff lint` (CPX rules)** | SQLFluff crawler targets: per `with_compound_statement` (C101, C107), per outer `select_statement` (C102–C106, C201), or file root (C108–C110) | Violations anchored to the crawl segment (or file root for C108–C110) |
| **`sqlfluff-complexity report`** | Whole file parse tree | At most one finding per metric rule per file, using **file-level** aggregates from `ComplexityMetrics` |

Shared invariants (unchanged from ADR 0002):

- Same `analyze_segment_tree` / `ComplexityMetrics` definitions for a given tree root.
- Same numeric thresholds from `ComplexityPolicy` and SQLFluff config.
- Same violation message builders where the evaluation unit matches (file-level rules C108–C110; message text parity tested).

Explicit non-parity (documented, tested where it matters):

- **Segment-scoped rules (C101–C107, C102–C201):** Lint may emit **multiple** violations per file (e.g. one per WITH clause for C107); report emits **zero or one** finding per metric per file from file-level totals (for C107, `metrics.cte_dependency_depth` is the max across WITH blocks).
- **C107 messages:** Lint uses `cte_dependency_depth_for_with_clause`; report uses the shared metric-threshold template against file-level `cte_dependency_depth`.

We will **not** change report to mirror every crawler hit in v1 without a dedicated design pass; report remains optimized for CI dashboards and per-file rollups.

## Consequences

- CLI and docs must state that report is a **file rollup**, not a replay of lint crawl results.
- Parity tests cover **file-level** rules (C108–C110) and segment rules where a single-statement file makes counts identical (e.g. C102 on a one-statement SQL file).
- Contract tests document **intentional** lint vs report count differences for C107 (multi-WITH).
- Future work may add optional “lint-equivalent report” mode; out of scope until requested.

## Alternatives considered

- **Report mirrors all crawler scopes:** Strongest parity, higher complexity and noisier SARIF/HTML for multi-statement files.
- **Lint uses file-level only:** Simpler parity, worse ergonomics (one violation per file, weak anchors).
- **Document-only with no tests:** Rejected; contracts need CI enforcement.

## References

- ADR 0002: SQLFluff plugin plus companion report CLI
- `src/sqlfluff_complexity/core/config/rule_registry.py` — canonical rule metadata
- `tests/reporting/test_report_lint_threshold_parity.py` — parity and scope contracts
