# Dialects

`sqlfluff-complexity` relies on SQLFluff's parser and dialect labels. Configure the SQLFluff dialect that matches your SQL, and the CPX rules collect metrics from the parsed segment tree.

## Official Support Matrix

The following dialects have **P0 fixture coverage**: every CPX metric is tested with passing and failing cases, plus dialect-specific false-positive guards for syntax patterns that must not trigger incorrect violations.

| SQLFluff dialect | Platform                              | Support level | False-positive guards |
| ---------------- | ------------------------------------- | ------------- | --------------------- |
| `bigquery`       | Google BigQuery (GoogleSQL)           | **P0 tested** | UNNEST, CROSS JOIN UNNEST, schema-qualified names |
| `snowflake`      | Snowflake                             | **P0 tested** | LATERAL FLATTEN |
| `sparksql`       | Apache Spark SQL / Databricks         | **P0 tested** | LATERAL VIEW EXPLODE |
| `postgres`       | PostgreSQL / dbt-postgres             | **P0 tested** | Scalar subquery in SELECT list |

**P0 tested** means: CPX rules and report mode produce correct metric counts for these dialects. Dialect-specific syntax patterns (table functions, lateral views, schema-qualified references) are verified not to trigger false violations. See [false-positive regression tests](../src/sqlfluff_complexity/tests/false_positive/test_false_positives.py) for the full test list.

## Best-Effort Dialects

These dialects are parsed by SQLFluff and accepted by CPX rules, but do not have comprehensive false-positive fixture coverage in this release:

| SQLFluff dialect | Typical users                        |
| ---------------- | ------------------------------------ |
| `ansi`           | portable SQL baseline                |
| `athena`         | AWS Athena projects                  |
| `redshift`       | Amazon Redshift projects             |

**Best-effort** means: CPX metric collection uses the same parse-tree traversal as P0 dialects, but dialect-specific syntax variants have not been exhaustively guarded. If you encounter a false positive on a best-effort dialect, open an issue with a minimal SQL reproduction.

## Dialect-Specific Caveats

### BigQuery

- **`UNNEST([...])` in FROM:** `UNNEST` as a table-valued function in `FROM` does not contain a nested `SELECT` statement. It is not counted as a derived table (C110) and does not add to `subquery_depth` (C103).
- **`CROSS JOIN UNNEST(array_col)`:** This is a `join_clause` in SQLFluff's grammar and counts as one join (C102). It does not count as a derived table (C110).
- **Schema-qualified names:** Names like `project.dataset.table` are never mistaken for CTE references. CTE dependency depth (C107) ignores any name containing a dot.

### Snowflake

- **`LATERAL FLATTEN(input => col)`:** Snowflake's array-flattening table function in `FROM` is not a `join_clause` and not a subquery. It contributes 0 to C102 and 0 to C110.

### Databricks / SparkSQL

- **`LATERAL VIEW EXPLODE(array_col)`:** Spark's generator syntax is not a `join_clause` and not a FROM subquery. It contributes 0 to C102 and 0 to C110.
- Use SQLFluff's `sparksql` dialect label for Spark SQL and Databricks SQL. The `databricks` dialect is available in SQLFluff for Databricks-specific syntax; use it when you intentionally test Databricks-only behavior.

### Postgres

- **Scalar correlated subqueries:** A `(SELECT max(...) FROM ... WHERE ...)` in the `SELECT` column list is not in `FROM` position. It contributes to `subquery_depth` (C103) but not to `derived_tables` (C110).

## Tested Dialect Fixtures

The repository keeps parser-focused fixtures for these SQLFluff dialect labels:

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
