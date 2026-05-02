# Rules Reference

`sqlfluff-complexity` rule codes use the `CPX_` prefix. The individual rules flag one metric at a time, and `CPX_C201` flags an aggregate weighted score.

## Metric Summary

| Rule       | Metric                              | Default | Config key                   |
| ---------- | ----------------------------------- | ------: | ---------------------------- |
| `CPX_C101` | Common table expressions            | 8       | `max_ctes`                   |
| `CPX_C102` | Join clauses                        | 8       | `max_joins`                  |
| `CPX_C103` | Nested subquery depth               | 3       | `max_subquery_depth`         |
| `CPX_C104` | `CASE` expressions                  | 10      | `max_case_expressions`       |
| `CPX_C105` | Boolean `AND` / `OR` operators      | 20      | `max_boolean_operators`      |
| `CPX_C106` | Window functions                    | 10      | `max_window_functions`       |
| `CPX_C107` | Longest CTE dependency chain        | 5       | `max_cte_dependency_depth`   |
| `CPX_C201` | Aggregate weighted complexity score | 60      | `max_complexity_score`       |

## CPX_C101: Too Many CTEs

Flags a statement when the CTE count exceeds `max_ctes`.

This is useful when a single SQL model becomes a long chain of transformation layers. Consider splitting layers into separate models or named upstream transformations.

```ini
[sqlfluff:rules:CPX_C101]
max_ctes = 8
```

## CPX_C102: Too Many Joins

Flags a statement when the join count exceeds `max_joins`.

Many joins increase review, correctness, and optimization risk. Consider moving joins upstream or breaking relational fan-in into intermediate models.

```ini
[sqlfluff:rules:CPX_C102]
max_joins = 8
```

Example pattern:

```sql
select *
from orders
join customers on orders.customer_id = customers.id
join regions on customers.region_id = regions.id
```

## CPX_C103: Nested Subquery Depth Too High

Flags a statement when nested subquery depth exceeds `max_subquery_depth`.

Deep nesting makes SQL harder to reason about and often hides transformation stages that deserve names.

```ini
[sqlfluff:rules:CPX_C103]
max_subquery_depth = 3
```

## CPX_C104: Too Many CASE Expressions

Flags a statement when `CASE` expression count exceeds `max_case_expressions`.

Dense `CASE` logic often means business rules are embedded directly in a model. Consider extracting mapping tables or upstream classification models.

```ini
[sqlfluff:rules:CPX_C104]
max_case_expressions = 10
```

## CPX_C105: Boolean Predicate Complexity Too High

Flags a statement when boolean `AND` / `OR` operator count exceeds `max_boolean_operators`.

Large predicates are difficult to validate and easy to break during review. Consider naming complex filters in CTEs or moving them into smaller models.

```ini
[sqlfluff:rules:CPX_C105]
max_boolean_operators = 20
```

Example pattern:

```sql
where
    status = 'paid'
    and country = 'JP'
    or account_type = 'enterprise'
```

## CPX_C106: Too Many Window Functions

Flags a statement when window function count exceeds `max_window_functions`.

Many window functions can indicate dense analytic logic. Consider extracting repeated analytic calculations into intermediate models.

```ini
[sqlfluff:rules:CPX_C106]
max_window_functions = 10
```

## CPX_C107: CTE Dependency Depth Too High

Flags a `WITH` clause when the longest chain of CTE references (within that statement’s parse tree)
exceeds `max_cte_dependency_depth`.

Raw CTE count (`CPX_C101`) and dependency depth measure different things: many independent CTEs can be
easier to follow than a long chain where each CTE builds on the previous one.

Only references visible as simple `table_reference` names to other CTEs in the same `WITH` are
considered. `ref()`, sources, macros, and dotted relation names are not resolved—unknown references
are ignored rather than guessed.

```ini
[sqlfluff:rules:CPX_C107]
max_cte_dependency_depth = 5
```

## CPX_C201: Aggregate Complexity Score Too High

Flags a statement when the weighted aggregate complexity score exceeds `max_complexity_score`.

`CPX_C201` is useful when no single metric is extreme but the combination of joins, nested queries, predicates, windows, and expressions makes a model hard to review.

Violation messages include the computed score, the configured `max_complexity_score`, a metric breakdown, the top weighted contributors, and a short refactoring hint.

```ini
[sqlfluff:rules:CPX_C201]
max_complexity_score = 60
complexity_weights = ctes:2,joins:2,subquery_depth:4,case_expressions:2,boolean_operators:1,window_functions:2,cte_dependency_depth:0,set_operation_count:0,expression_depth:0
mode = enforce
```

The aggregate score is:

```text
ctes * ctes_weight
+ joins * joins_weight
+ subquery_depth * subquery_depth_weight
+ case_expressions * case_expressions_weight
+ boolean_operators * boolean_operators_weight
+ window_functions * window_functions_weight
+ cte_dependency_depth * cte_dependency_depth_weight
+ set_operation_count * set_operation_count_weight
+ expression_depth * expression_depth_weight
```

See [configuration](configuration.md) for path overrides and report-mode rollout patterns.

See the [docs index](index.md) for the rest of the user documentation.
