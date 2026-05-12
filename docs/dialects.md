# Dialects

`sqlfluff-complexity` relies on SQLFluff's parser and dialect labels. Configure the SQLFluff dialect that matches your SQL, and the CPX rules collect metrics from the parsed segment tree.

## Officially Tested Dialects (P0)

The official fixture-backed subset for accuracy/reliability is:

- `bigquery`
- `snowflake`
- `sparksql` (Databricks/Spark SQL workloads)
- `postgres`

These dialects have dedicated fixture-matrix assertions and regression coverage for CPX metrics.

## Best-Effort Dialects

Other SQLFluff dialects may work but are best-effort unless explicit fixture coverage is added.
Current repository fixtures also include `ansi`, `athena`, and `redshift` for compatibility checks, but they are not part of the official P0 support contract.

## Fixture Coverage Model

Support confidence is determined by fixture coverage and deterministic metric assertions, not by adapter naming alone.

For each official dialect, fixtures are expected to cover:

- pass/boundary/fail threshold behavior for representative metrics
- dialect-specific syntax cases
- negative/noise-resistant false-positive scenarios

Fixtures validate parser and metric behavior only. They do not execute SQL against warehouses.

## SQLFluff Dialects Versus dbt Adapters

dbt adapter names are useful coverage prompts, but they are not the parser contract. SQLFluff dialect labels are the parser contract.

Examples:

| dbt adapter     | SQLFluff dialect |
| --------------- | ---------------- |
| `dbt-athena`    | `athena`         |
| `dbt-bigquery`  | `bigquery`       |
| `dbt-postgres`  | `postgres`       |
| `dbt-redshift`  | `redshift`       |
| `dbt-snowflake` | `snowflake`      |
| `dbt-spark`     | `sparksql`       |

Use the SQLFluff dialect label in `.sqlfluff`:

```ini
[sqlfluff]
dialect = bigquery
rules = CPX_C102,CPX_C201
```

## SparkSQL And Databricks

Apache Spark SQL fixtures use SQLFluff's `sparksql` dialect label. Databricks-specific syntax should use SQLFluff's `databricks` dialect when you intentionally test Databricks behavior.

Do not use `spark` as a SQLFluff dialect label.

## Athena, Trino, And Presto

Athena, Trino, and Presto syntax overlap, but they are not interchangeable. The current fixture matrix uses SQLFluff's `athena` dialect for Athena coverage.

If your project depends on Trino-specific syntax, configure and test SQLFluff's `trino` dialect separately.

## Adding Dialect Fixtures

Contributor-facing fixture instructions live in [CONTRIBUTING.md](../CONTRIBUTING.md). At a high level:

1. Add focused SQL under `src/sqlfluff_complexity/tests/fixtures/sql/<dialect>/`.
2. Add matching expected metrics JSON under `src/sqlfluff_complexity/tests/fixtures/expected/<dialect>/`.
3. Keep fixtures small and grounded in official dialect references.
4. Validate that SQLFluff parses the fixture without `unparsable` segments.

See [ADR 0005](adr/0005-validate-sql-dialect-support-with-fixture-matrix.md) for the fixture matrix decision.

See the [docs index](index.md) for the rest of the user documentation.
