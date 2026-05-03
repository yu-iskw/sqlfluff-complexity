# Configuration

`sqlfluff-complexity` uses normal SQLFluff rule configuration. Add CPX rules to your `.sqlfluff` file, then tune thresholds for your project.

## Enable Rules

```ini
[sqlfluff]
dialect = snowflake
rules = CPX_C101,CPX_C102,CPX_C103,CPX_C104,CPX_C105,CPX_C106,CPX_C107,CPX_C108,CPX_C109,CPX_C110,CPX_C201
```

You can also enable only the rules you are ready to enforce:

```ini
[sqlfluff]
dialect = snowflake
rules = CPX_C102,CPX_C103,CPX_C201
```

## Default Thresholds

The plugin default config sets these limits:

| Rule       | Config key                 | Default |
| ---------- | -------------------------- | ------: |
| `CPX_C101` | `max_ctes`                 |       8 |
| `CPX_C102` | `max_joins`                |       8 |
| `CPX_C103` | `max_subquery_depth`       |       3 |
| `CPX_C104` | `max_case_expressions`     |      10 |
| `CPX_C105` | `max_boolean_operators`    |      20 |
| `CPX_C106` | `max_window_functions`     |      10 |
| `CPX_C107` | `max_cte_dependency_depth` |       5 |
| `CPX_C108` | `max_nested_case_depth`    |      10 |
| `CPX_C109` | `max_set_operations`       |      12 |
| `CPX_C110` | `max_derived_tables`       |       4 |
| `CPX_C201` | `max_complexity_score`     |      60 |

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
complexity_weights = ctes:2,joins:2,subquery_depth:4,case_expressions:2,boolean_operators:1,window_functions:2,cte_dependency_depth:0,set_operation_count:0,expression_depth:0,derived_tables:0
mode = enforce
```

The aggregate score uses maximum nested subquery depth, not raw subquery count.

The **`cte_dependency_depth`** component in `complexity_weights` applies to the **file-level**
metric (maximum chain depth across all `WITH` blocks in the parsed tree), not to each `WITH` in
isolation—see [Reporting: interpreting `cte_dependency_depth`](reporting.md#interpreting-cte_dependency_depth-in-reports) and [CPX_C107](rules.md#cpx_c107-cte-dependency-depth-too-high).

### SQLFluff nested configuration by path

If you want different strictness in different parts of the repository, SQLFluff already supports **stacking configuration by path**: it merges settings from config files along the directory chain toward each file being linted, with values from files **closer to that file** overriding earlier ones. See [SQLFluff: Setting configuration — Nesting](https://docs.sqlfluff.com/en/stable/configuration/setting_configuration.html#nesting).

CPX options use the same `[sqlfluff:rules:CPX_*]` sections as other rules, so nested `.sqlfluff` files (or other [supported config filenames](https://docs.sqlfluff.com/en/stable/configuration/setting_configuration.html#configuration-files) in those directories) should follow upstream merge rules.

**Templater caveat:** SQLFluff does **not** allow setting `templater` in config files under subdirectories of the working directory (same nesting documentation). For example, do not rely on `models/staging/.sqlfluff` alone to switch `templater = dbt`; keep templater (and related dbt templater sections) in root or higher-level config.

This repository **has not exhaustively verified** nested-file workflows across every CPX rule and every `sqlfluff` / `sqlfluff-complexity` entry point. If you see unexpected behavior, prefer a **single root config** plus **`path_overrides`** below, or open an issue with a minimal reproduction.

Compared to **`path_overrides`** (next): nesting spreads policy across multiple files using standard SQLFluff; `path_overrides` keeps one file and applies glob lines under `[sqlfluff:rules:CPX_C201]` for CPX-specific thresholds and `mode`.

Use `path_overrides` when different model areas need different budgets. Patterns use normalized path strings and glob-style matching.

Paths are matched with `fnmatch` against the **path string SQLFluff uses for the file** (typically the path passed to lint or report, often relative to the project root). Absolute paths under `/tmp/...` will not match `models/**/*.sql` unless your globs account for them.

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
- `max_cte_dependency_depth`
- `max_nested_case_depth`
- `max_set_operations`
- `max_derived_tables`
- `max_complexity_score`
- `mode`

`mode` can be `enforce` or `report`. A matching `mode=report` override suppresses SQLFluff rule enforcement for the affected CPX rule path while keeping the policy useful for report mode.

## Config Check

Before running lint or report in CI, validate CPX-related settings (aggregate weights, `path_overrides`, and `mode`) with:

```bash
sqlfluff-complexity config-check --dialect postgres --config .sqlfluff
```

The command loads the same SQLFluff config as report mode, runs the existing parsers, and exits non-zero on invalid values.

## Presets

For a copyable starting point, generate plain SQLFluff config from a preset:

```bash
sqlfluff-complexity config preset recommended --dialect postgres
```

Available presets:

| Preset        | Use case                                     |
| ------------- | -------------------------------------------- |
| `report_only` | Baseline complexity without enforcing C201   |
| `lenient`     | Low-noise rollout for teams new to CPX rules |
| `recommended` | Conservative defaults for most teams         |
| `strict`      | Mature projects that want tighter thresholds |

Presets are emitted to stdout only. They do not create hidden runtime behavior; after copying the generated config, tune the normal SQLFluff rule sections and path overrides as needed.

## Enforcement Versus Reporting

Native CPX rules run through `sqlfluff lint` and can fail lint. The companion [report command](reporting.md) uses the same metric and threshold semantics, but emits console or SARIF output for non-blocking analysis.

Recommended rollout:

1. Run reports to understand existing complexity.
2. Tune path overrides for known high-complexity areas.
3. Enforce individual high-signal rules.
4. Add aggregate score enforcement once the score budget is calibrated.

See the [docs index](index.md) for the rest of the user documentation.
