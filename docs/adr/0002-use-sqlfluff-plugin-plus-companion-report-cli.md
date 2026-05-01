# ADR 0002: Use SQLFluff plugin plus companion report CLI

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** Maintainers

## Context

`sqlfluff-complexity` needs to support two related workflows:

- strict lint enforcement in local development, pre-commit, and CI
- non-blocking complexity reporting for calibration, review, and code-scanning artifacts

SQLFluff already provides the parser, configuration model, rule execution, and standard suppression behavior that users expect in SQL linting workflows. Reporting needs a different interface because console summaries and SARIF artifacts are not a natural fit for individual SQLFluff lint results alone.

## Decision

We will implement `sqlfluff-complexity` as a native SQLFluff plugin for enforcement plus a companion `sqlfluff-complexity` command for report mode.

The stable invariant is that native rules and report mode must share the same metric collection and scoring engine. Rule wrappers may format SQLFluff `LintResult` objects, and the report CLI may format console or SARIF output, but neither should implement separate metric semantics.

## Consequences

- Developers can use normal `sqlfluff lint` behavior, including rule selection and `noqa` suppression.
- CI can choose between failing lint and generating non-blocking reports.
- The package has two public execution surfaces, so shared core logic and integration tests are required to prevent drift.
- The companion CLI adds maintenance cost, but keeps reporting behavior explicit and easier to evolve.

## Alternatives considered

- **Rules only:** Simpler package surface, but weak support for SARIF and non-blocking report workflows.
- **Standalone CLI only:** Easier to control output, but loses native SQLFluff rule discovery, suppression, and developer workflow integration.
- **Custom formatter around `sqlfluff lint`:** Reuses SQLFluff execution but couples report behavior to lint output and makes aggregate per-file reporting harder.

## Trade-offs

We accept a slightly larger package surface to preserve the native SQLFluff developer experience while supporting CI reporting. The main implementation risk is behavior drift between enforcement and reporting, mitigated by the shared metric engine invariant.

## References

- [Product design: sqlfluff-complexity](../product_design.md)
- [ADR 0001: Record architecture decisions](0001-record-architecture-decisions.md)
- [SQLFluff custom rules guide](https://docs.sqlfluff.com/en/stable/guides/setup/developing_custom_rules.html)
