# ADR 0003: Derive complexity metrics from SQLFluff segment trees

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** Maintainers

## Context

The plugin must count SQL complexity signals such as CTEs, joins, nested subquery depth, `CASE` expressions, boolean operators, and window functions across multiple SQL dialects. Raw SQL text varies by dialect, formatter output, and templating behavior, while SQLFluff already parses SQL into a structured segment tree.

Metric accuracy does not need to be perfect across every dialect in v1, but the implementation should be maintainable and should avoid known-fragile string matching where SQLFluff provides structured parse information.

## Decision

We will collect complexity metrics from SQLFluff parsed segments rather than from raw SQL text or regular expressions.

The stable invariant is that metric semantics come from SQLFluff's parsed segment tree. SQLFluff-version-sensitive traversal details should remain localized so native rules and report mode can share the same interpretation of a parsed SQL statement.

Tests will use parsed fixture SQL to validate expected metrics and to document known dialect limitations.

## Consequences

- Metric collection aligns with SQLFluff's parsing model and should behave better across supported dialects.
- Segment names and parser behavior can change across SQLFluff releases, so the project must pin a supported major range and keep fixture coverage around traversal assumptions.
- Some edge cases, especially nested subquery depth and boolean operator context, require careful fixture calibration.
- The report CLI must use the same parsed-segment path as native rules to preserve consistent semantics.

## Alternatives considered

- **Raw regular expressions:** Fast to implement, but fragile for nested SQL, comments, templating, and dialect-specific syntax.
- **Token-only counting:** More structured than raw regex, but still insufficient for nested subquery depth and expression context.
- **Warehouse query plans or semantic analysis:** Potentially richer, but outside v1 scope and incompatible with lightweight local linting.

## Trade-offs

We accept coupling to SQLFluff parser internals in exchange for better maintainability than custom SQL parsing. The coupling must remain localized so future SQLFluff changes are easier to test and repair.

## References

- [Product design: segment traversal](../product_design.md#14-segment-traversal-design)
- [ADR 0002: Use SQLFluff plugin plus companion report CLI](0002-use-sqlfluff-plugin-plus-companion-report-cli.md)
- [ADR 0005: Validate SQL dialect support with fixture matrix](0005-validate-sql-dialect-support-with-fixture-matrix.md)
- [SQLFluff custom rules guide](https://docs.sqlfluff.com/en/stable/guides/setup/developing_custom_rules.html)
