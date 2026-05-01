# Configuration

`sqlfluff-complexity` uses normal SQLFluff rule configuration. Add CPX rules to your `.sqlfluff` file, then tune thresholds for your project.

## Enable Rules

```ini
[sqlfluff]
dialect = snowflake
rules = CPX_C101,CPX_C102,CPX_C103,CPX_C104,CPX_C105,CPX_C106,CPX_C201
```

You can also enable only the rules you are ready to enforce:

```ini
[sqlfluff]
dialect = snowflake
rules = CPX_C102,CPX_C103,CPX_C201
```

## Default Thresholds

The plugin default config sets these limits:

| Rule       | Config key              | Default |
| ---------- | ----------------------- | ------: |
| `CPX_C101` | `max_ctes`              |       8 |
| `CPX_C102` | `max_joins`             |       8 |
| `CPX_C103` | `max_subquery_depth`    |       3 |
| `CPX_C104` | `max_case_expressions`  |      10 |
| `CPX_C105` | `max_boolean_operators` |      20 |
| `CPX_C106` | `max_window_functions`  |      10 |
| `CPX_C201` | `max_complexity_score`  |      60 |

Example override:

```ini
[sqlfluff:rules:CPX_C102]
max_joins = 6

[sqlfluff:rules:CPX_C103]
max_subquery_depth = 2
```

## Aggregate Score

`CPX_C201` computes a weighted aggregate score from the same metrics used by the individual rules.

Default weights:

```ini
[sqlfluff:rules:CPX_C201]
max_complexity_score = 60
complexity_weights = ctes:2,joins:2,subquery_depth:4,case_expressions:2,boolean_operators:1,window_functions:2
mode = enforce
```

The aggregate score uses maximum nested subquery depth, not raw subquery count.

## Path Overrides

Use `path_overrides` when different model areas need different budgets. Patterns use normalized path strings and glob-style matching.

```ini
[sqlfluff:rules:CPX_C201]
max_complexity_score = 60
path_overrides =
    models/staging/*.sql:max_joins=12,max_complexity_score=80
    models/marts/*.sql:max_joins=6,max_complexity_score=50
    models/experimental/*.sql:mode=report
```

Supported override keys:

- `max_ctes`
- `max_joins`
- `max_subquery_depth`
- `max_case_expressions`
- `max_boolean_operators`
- `max_window_functions`
- `max_complexity_score`
- `mode`

`mode` can be `enforce` or `report`. A matching `mode=report` override suppresses SQLFluff rule enforcement for the affected CPX rule path while keeping the policy useful for report mode.

## Config Check

Before running lint or report in CI, validate CPX-related settings (aggregate weights, `path_overrides`, and `mode`) with:

```bash
sqlfluff-complexity config-check --dialect postgres --config .sqlfluff
```

The command loads the same SQLFluff config as report mode, runs the existing parsers, and exits non-zero on invalid values.

## Enforcement Versus Reporting

Native CPX rules run through `sqlfluff lint` and can fail lint. The companion [report command](reporting.md) uses the same metric and threshold semantics, but emits console or SARIF output for non-blocking analysis.

Recommended rollout:

1. Run reports to understand existing complexity.
2. Tune path overrides for known high-complexity areas.
3. Enforce individual high-signal rules.
4. Add aggregate score enforcement once the score budget is calibrated.

See the [docs index](index.md) for the rest of the user documentation.
