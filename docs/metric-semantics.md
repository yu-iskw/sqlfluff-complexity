# Metric Semantics

This page defines precise counting rules for each CPX metric. It covers what is counted, what is explicitly excluded, the scope of measurement, dialect-specific caveats, and the relationship between adjacent metrics.

## CPX_C101: CTEs (`ctes`)

**What is counted:** Every `common_table_expression` segment in the outermost `WITH` clause of the current parse scope.

**What is NOT counted:**
- CTE definitions inside a nested `WITH` block that appears inside a CTE body (those belong to their own `with_compound_statement`)
- CTE aliases referenced in `FROM` or `JOIN` (references, not definitions)
- Subqueries in `FROM` position (those are derived tables — see C110)

**Scope:** One `WITH` clause at a time. When `CPX_C107` runs lint, it evaluates the enclosing `with_compound_statement`; report mode collects from all `WITH` blocks in the file and returns the total CTE count.

**Dialect caveats:** All supported dialects use `WITH` syntax. Recursive CTEs (`WITH RECURSIVE`) count the same way as non-recursive CTEs.

**Adjacent metrics:** `CPX_C107` measures how deeply CTEs depend on each other, not how many there are. A file with 8 independent CTEs scores 1 on `cte_dependency_depth` but 8 on `ctes`.

---

## CPX_C102: Joins (`joins`)

**What is counted:** Every explicit `join_clause` segment in the parse tree (INNER JOIN, LEFT JOIN, RIGHT JOIN, CROSS JOIN, FULL OUTER JOIN, and their variants).

**What is NOT counted:**
- Implicit comma joins (`FROM a, b`) — these are parsed as `from_clause_element` segments, not `join_clause`
- `LATERAL VIEW` in SparkSQL — this is its own syntactic form, not a JOIN keyword
- BigQuery `CROSS JOIN UNNEST(array_col)` — counted as a JOIN because it uses the `join_clause` segment (see below)
- Snowflake `LATERAL FLATTEN(input => col)` — not counted; it is a table function, not a `join_clause`

**Dialect caveats:**
- **BigQuery:** `CROSS JOIN UNNEST(array_col)` is a `join_clause` and counts as a join. However, `UNNEST([...])` in `FROM` without JOIN is not a `join_clause` and does not count.
- **Snowflake:** `LATERAL FLATTEN` in `FROM` is a table function, not a `join_clause`. It does not count as a join.
- **SparkSQL:** `LATERAL VIEW EXPLODE(array_col)` is a Spark-specific generator syntax. It is not a `join_clause` and does not count.

**Adjacent metrics:** `CPX_C110` counts inline subqueries in `FROM` position. A `JOIN (SELECT ...) AS alias` contributes one join to C102 and one derived table to C110.

---

## CPX_C103: Nested Subquery Depth (`subquery_depth`)

**What is counted:** The maximum nesting depth of `select_statement` segments relative to the outermost `select_statement`. A subquery directly inside a `FROM` or `WHERE` clause adds 1 to the depth. A subquery inside that subquery adds 2, etc.

**What is NOT counted:**
- Raw subquery count (that is `subqueries`)
- The outermost `select_statement` itself (depth 0)
- CTE bodies (they are separate named statements, not nested depths)

**Scope:** Maximum depth across all subquery positions: `WHERE`, `FROM`, `SELECT` column list, `JOIN ON`, `HAVING`.

**Adjacent metrics:** `CPX_C110` counts `FROM`-position subqueries but not their depth. A three-level deeply nested FROM subquery contributes depth=3 to C103 but only 1 to C110 (the outermost FROM occurrence). `CPX_C104`/`CPX_C108` measure `CASE` expressions independently.

---

## CPX_C104: CASE Expressions (`case_expressions`)

**What is counted:** Every `case_expression` segment in the parse tree, regardless of position or nesting. A `CASE` nested inside another `CASE` adds 2 to the count (both the outer and inner expressions).

**What is NOT counted:**
- `COALESCE`, `IIF`, `DECODE`, `NULLIF` — these are function expressions, not `case_expression` segments in SQLFluff's grammar

**Scope:** Whole file parse tree.

**Adjacent metrics:** `CPX_C108` measures the maximum nesting depth of `CASE` within `CASE`, not the total count. A file with 10 non-nested `CASE` expressions scores 1 on C108 (depth=1) but 10 on C104. A file with one triply-nested `CASE` scores 3 on C108 but only 3 on C104.

---

## CPX_C105: Boolean Operators (`boolean_operators`)

**What is counted:** Every `boolean_binary_operator` (or equivalent) segment in the parse tree corresponding to `AND` or `OR` logical connectives.

**What is NOT counted:**
- `CASE WHEN ... THEN ...` — keyword `WHEN` is not a boolean operator
- Equality predicates (`a = b`) — these are comparison operators, not boolean operators
- `NOT` (unary negation) — not counted
- String literals that happen to contain the text "AND" or "OR"

**Scope:** Whole file parse tree. Counts logical predicate connectives only.

**Dialect caveats:**
- All supported dialects represent `AND` / `OR` as binary boolean operators in SQLFluff's grammar. The count is dialect-independent.
- BigQuery, Snowflake, SparkSQL, and Postgres CASE expressions are parsed as `case_expression` segments, not boolean chains, so `CASE WHEN a THEN b WHEN c THEN d END` contributes 0 to boolean_operators.

**Adjacent metrics:** `CPX_C104` counts `CASE` expressions. A complex `WHERE` clause using `CASE` expressions rather than `AND`/`OR` will inflate C104, not C105.

---

## CPX_C106: Window Functions (`window_functions`)

**What is counted:** Every `OVER` clause in the parse tree. Each `function_name OVER (...)` contributes 1 to the count.

**What is NOT counted:**
- References to previously named window frames (`WINDOW` clause definitions) without an `OVER` — not currently counted
- Aggregate functions without `OVER` (e.g., `SUM(x)` in a GROUP BY context)

**Scope:** Whole file parse tree.

**Dialect caveats:** All supported dialects use `OVER (...)` syntax for window functions, so the metric is dialect-independent.

**Adjacent metrics:** Not directly related to C104 or C105. A dense analytic model may have high C106 and low C104/C105.

---

## CPX_C107: CTE Dependency Depth (`cte_dependency_depth`)

**What is counted:** The maximum length of a CTE reference chain within a single `WITH` clause. If CTE `c` references CTE `b` which references CTE `a`, the chain depth is 3.

**Algorithm:** A directed graph of CTE-to-CTE references is built from the `WITH` clause. The metric is the length of the longest path in that graph (analogous to critical path in a DAG).

**What is NOT counted:**
- References to external tables (non-CTE names)
- Schema-qualified names (e.g., `warehouse.orders`) — qualified names cannot refer to CTEs, which use bare identifiers
- `ref()`, `source()`, Jinja macros, or other templated expressions — resolved only after templating; unresolved references are ignored
- Nested `WITH` blocks inside a CTE body — those are separate `with_compound_statement` scopes

**Scope (lint):** One `with_compound_statement` at a time. `CPX_C107` evaluates the enclosing `WITH` clause independently.

**Scope (report):** The `cte_dependency_depth` metric in report output is the maximum chain depth across all `WITH` blocks in the file. A nested inner `WITH` with a deeper chain can drive the file-level metric higher than the outermost `WITH` alone.

**Dialect caveats:**
- **BigQuery:** Schema-qualified names (`project.dataset.table`) are skipped correctly and do not inflate the dependency graph.
- All supported dialects use the same CTE syntax (`WITH name AS (...)`).

**Adjacent metrics:** `CPX_C101` counts CTE definitions (how many). `CPX_C107` measures dependency depth (how deeply they chain). A file with 8 independent CTEs (depth=1) and one that chains 4 deep are both interesting for different reasons.

---

## CPX_C108: Nested CASE Depth (`expression_depth`)

**What is counted:** The maximum nesting depth of `case_expression` segments in the parse tree. A `CASE` directly at the top level has depth 1. A `CASE` inside a `CASE` has depth 2.

**What is NOT counted:**
- The total number of `CASE` expressions (that is `CPX_C104`)
- General expression tree depth (parentheses, function calls)

**Scope:** Whole file parse tree. The metric is the deepest level of `case_expression` nesting found anywhere in the file.

**Adjacent metrics:** `CPX_C104` and `CPX_C108` both involve CASE expressions. C104 counts the total; C108 measures the nesting depth. They are independent. A flat model with 12 CASE expressions at depth=1 has high C104 and low C108. A model with one quadruply-nested CASE has high C108 and moderate C104 (4).

---

## CPX_C109: Set Operations (`set_operation_count`)

**What is counted:** Every `set_operator` segment in the parse tree. Each `UNION`, `UNION ALL`, `INTERSECT`, `INTERSECT ALL`, `EXCEPT`, or `EXCEPT ALL` keyword between query blocks adds 1.

**What is NOT counted:**
- Parenthesized groupings that do not add new operators (a parenthesized UNION query has the same count as the non-parenthesized version)
- Duplicate violations from nested set operation structures — the metric is file-level and does not double-count

**Scope:** Whole file parse tree. Evaluated once per file via the parse root, so nested parenthesized unions and per-arm `select_statement` fragments cannot produce duplicate violations.

**Adjacent metrics:** `CPX_C101` through `CPX_C108` are orthogonal to set operation count. A file with a large UNION ALL fan-out may have low C101–C108 but high C109.

---

## CPX_C110: Derived Tables (`derived_tables`)

**What is counted:** Subqueries that appear directly in `FROM` position — specifically `from_expression_element` segments that contain an inline `select_statement`. This includes:
- `FROM (SELECT ...) AS alias`
- `JOIN (SELECT ...) AS alias`

**What is NOT counted:**
- CTE bodies (`WITH name AS (SELECT ...)`) — named subqueries, not inline FROM subqueries
- Scalar subqueries in the `SELECT` column list or `WHERE` clause (those contribute to `subquery_depth` / C103)
- Table functions: BigQuery `UNNEST([...])`, Snowflake `LATERAL FLATTEN`, SparkSQL `LATERAL VIEW EXPLODE` — these are table-valued functions, not inline `select_statement` segments
- `FROM (SELECT ...)` inside a CTE body — excluded to avoid double-penalizing alongside `CPX_C101`

**Scope:** Whole file parse tree, excluding CTE bodies.

**Dialect caveats:**
- **BigQuery:** `FROM UNNEST(array_col)` and `CROSS JOIN UNNEST(array_col)` are table-valued functions. They do not contain a nested `select_statement` and are not counted as derived tables.
- **Snowflake:** `LATERAL FLATTEN(input => col)` is a table function in `FROM`. Not counted as a derived table.
- **SparkSQL:** `LATERAL VIEW EXPLODE(array_col)` is a Spark-specific generator. Not counted as a derived table.
- **Postgres:** Scalar correlated subqueries in the `SELECT` list are not in `FROM` position and are not counted as derived tables.

**Adjacent metrics:** `CPX_C101` counts CTE definitions. A query that uses CTEs exclusively has C101 > 0 and C110 = 0. `CPX_C103` measures depth of nested subqueries; a two-level nested FROM subquery contributes 1 to C110 (the outer) and depth=2 to C103.

---

## CPX_C201: Aggregate Complexity Score

**What is counted:** A weighted sum of all individual CPX metrics:

```
score = (ctes × w_ctes)
      + (joins × w_joins)
      + (subquery_depth × w_subquery_depth)
      + (case_expressions × w_case_expressions)
      + (boolean_operators × w_boolean_operators)
      + (window_functions × w_window_functions)
      + (cte_dependency_depth × w_cte_dependency_depth)
      + (set_operation_count × w_set_operation_count)
      + (expression_depth × w_expression_depth)
      + (derived_tables × w_derived_tables)
```

Note that `subquery_depth` (maximum nesting depth) is used in the aggregate score, not raw subquery count.

**Default weights:** See [configuration: aggregate score](configuration.md#aggregate-score).

**Scope:** File-level. All `WITH` blocks, all joins, all CASE expressions, and all derived tables in the file contribute.

**Relationship to individual rules:** C201 can flag a file even if no individual metric triggers its threshold rule. It is complementary, not redundant — it catches files where many metrics are elevated but each is individually below threshold.

See [rules: CPX_C201](rules.md#cpx_c201-aggregate-complexity-score-too-high) for violation message format and weight configuration.

---

See the [docs index](index.md) for the rest of the user documentation.
