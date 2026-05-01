# Dialects

`sqlfluff-complexity` relies on SQLFluff's parser and dialect labels. Configure the SQLFluff dialect that matches your SQL, and the CPX rules collect metrics from the parsed segment tree.

## Tested Dialect Fixtures

The repository keeps parser-focused fixtures for these SQLFluff dialect labels:

| SQLFluff dialect | Typical users                        |
| ---------------- | ------------------------------------ |
| `ansi`           | portable SQL baseline                |
| `athena`         | AWS Athena projects                  |
| `bigquery`       | BigQuery GoogleSQL projects          |
| `postgres`       | PostgreSQL and dbt-postgres projects |
| `redshift`       | Amazon Redshift projects             |
| `snowflake`      | Snowflake projects                   |
| `sparksql`       | Apache Spark SQL projects            |

These fixtures validate parser and metric behavior. They do not execute SQL against warehouses.

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
