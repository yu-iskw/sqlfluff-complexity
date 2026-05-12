# Metric Semantics (Source of Truth)

This page defines canonical counting behavior for CPX metrics. Implementation, fixtures, and user docs should stay aligned with this document.

Scope and parser model:

- Metrics are computed from SQLFluff parse trees (no dbt artifacts).
- File-level report metrics are computed on the parse root.
- Some lint rules evaluate narrower scopes (for example CPX_C107 evaluates each `WITH` clause).
- Officially tested dialect subset: `bigquery`, `snowflake`, `sparksql` (Databricks/Spark SQL), `postgres`. Other dialects are best-effort.

## `ctes`

- Counts: `common_table_expression` nodes in a statement tree.
- Does not count: base tables/views, subqueries without `WITH`.
- Scope: file/root in report; statement tree for lint.
- Caveat: nested `WITH` contributes to file-level totals.
- Positive: `with a as (...), b as (...) select ...` → 2.
- Negative: `select * from (select 1) t` → 0.

## `joins`

- Counts: `join_clause` segments.
- Does not count: comma joins represented without `join_clause`.
- Scope: parse tree of evaluated statement/root.
- Caveat: dialect join syntax variants are normalized by SQLFluff.
- Positive: `from a join b ... join c ...` → 2.
- Negative: `from a, b` → 0 for this metric.

## `subquery_depth`

- Counts: maximum nesting depth of subquery `select_statement` structures.
- Does not count: sibling subqueries at same depth as additional depth.
- Scope: parse tree root/subtree.
- Caveat: depends on SQLFluff nesting shape.
- Positive: `select * from (select * from (select 1)) t` → depth 2.
- Negative: `select * from (select 1) a join (select 2) b` → depth 1.

## `case_expressions`

- Counts: number of `case_expression` segments.
- Does not count: `if()`/dialect conditional functions unless parsed as CASE.
- Scope: parse tree root/subtree.
- Caveat: dialect-specific conditional syntax may map differently.
- Positive: `select case when ... end, case when ... end` → 2.
- Negative: `select coalesce(a,b)` → 0.

## `boolean_operators`

- Counts: logical predicate operators (`AND`/`OR`) parsed as boolean operators.
- Does not count: string literals/identifiers containing `AND`/`OR`.
- Scope: parse tree root/subtree.
- Caveat: parser-driven; avoids raw keyword regex false positives.
- Positive: `where a=1 and (b=2 or c=3)` → 2.
- Negative: `select 'AND' as token` → 0.

## `window_functions`

- Counts: functions with an `OVER (...)` window clause.
- Does not count: non-window aggregate/scalar functions.
- Scope: parse tree root/subtree.
- Caveat: dialect window syntax support follows SQLFluff grammar.
- Positive: `row_number() over (partition by k)` → 1.
- Negative: `count(*)` (no `OVER`) → 0.

## `cte_dependency_depth`

- Counts: longest dependency path among CTE aliases in a `WITH` graph.
- Does not count: schema-qualified relations as CTE aliases.
- Scope: report = max over all `WITH` blocks in file; CPX_C107 lint = per `WITH`.
- Caveat: nested `WITH` scopes are evaluated independently to reduce false positives.
- Positive: `with a as (...), b as (select * from a), c as (select * from b)` → depth 3.
- Negative: `with a as (...) select * from public.a` does not add dependency edge.

## `expression_depth` (used by CPX_C108 as nested CASE depth)

- Counts: maximum nesting depth of `case_expression` nodes.
- Does not count: generic expression nesting unrelated to CASE.
- Scope: file/root metric.
- Caveat: name is `expression_depth` in metric payload; configured via `max_nested_case_depth`.
- Positive: `case when ... then case when ... end end` → depth 2.
- Negative: two separate non-nested CASE expressions → depth 1.

## `set_operation_count`

- Counts: `set_operator` segments (`UNION`, `UNION ALL`, `INTERSECT`, `EXCEPT`).
- Does not count: duplicated hits from parenthesized traversal.
- Scope: file/root metric (CPX_C109 parity with report behavior).
- Caveat: parser identifies operator tokens across dialects.
- Positive: `select 1 union all select 2 except select 3` → 2.
- Negative: single `select` without set operator → 0.

## `derived_tables`

- Counts: inline table subqueries in `FROM`/`JOIN` (`from (select ...) alias`).
- Does not count: scalar subqueries in expressions/functions; CTE definition bodies for CPX_C110 counting.
- Scope: file/root metric.
- Caveat: excludes CTE bodies to avoid double-penalizing with `ctes`.
- Positive: `select * from (select 1) t` → 1.
- Negative: `with c as (select * from (select 1) t) select * from c` → 0 when counting derived tables inside CTE bodies.

## Aggregate complexity score (`CPX_C201`)

- Behavior: weighted sum of all structural metrics (`ctes`, `joins`, `subquery_depth`, `case_expressions`, `boolean_operators`, `window_functions`, `cte_dependency_depth`, `set_operation_count`, `expression_depth`, `derived_tables`).
- Uses `complexity_weights` merged with defaults.
- Scope: file/root metric score.
- Relationship: combines weak signals where no single metric exceeds threshold.
- Severity policy is applied on the resolved score using rule-level `severity` and `severity_bands`.
