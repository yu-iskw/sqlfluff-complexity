# dbt Usage

`sqlfluff-complexity` works with dbt projects through SQLFluff templating. In v1, the plugin measures SQL that SQLFluff can parse; it does not read dbt artifacts directly.

## Supported In v1

- SQLFluff `templater = dbt`
- SQLFluff-parsed dbt model SQL
- native CPX lint rules
- `sqlfluff-complexity report` against SQL files rendered/parsing through SQLFluff

## Not Supported In v1

- direct parsing of `target/manifest.json`
- DAG fan-in or fan-out metrics
- model lineage scoring
- guarantees about complexity that exists only after macro expansion outside SQLFluff's parsed output

See [ADR 0004](adr/0004-defer-dbt-manifest-metrics-for-v1.md) for the decision rationale.

## Install dbt Templater Dependencies

SQLFluff's dbt templater is packaged separately from SQLFluff. Install the templater and the adapter for your warehouse in the same environment where you run SQLFluff.

Example for Postgres:

```bash
pip install sqlfluff-complexity sqlfluff-templater-dbt dbt-postgres
```

Example for DuckDB-based local testing:

```bash
pip install sqlfluff-complexity sqlfluff-templater-dbt dbt-duckdb
```

## Configure SQLFluff

Minimal `.sqlfluff` example:

```ini
[sqlfluff]
dialect = postgres
templater = dbt
rules = CPX_C101,CPX_C102,CPX_C103,CPX_C104,CPX_C105,CPX_C106,CPX_C201

[sqlfluff:templater:dbt]
project_dir = .
profiles_dir = ~/.dbt
profile = my_project
target = dev
dbt_skip_compilation_error = False
```

`dbt_skip_compilation_error = False` is useful when you want CI to expose dbt compilation issues instead of silently ignoring them.

## Run

Run SQLFluff normally:

```bash
sqlfluff lint models/
```

For non-blocking analysis:

```bash
sqlfluff-complexity report --dialect postgres --config .sqlfluff models/
```

## Jinja Builtins Alternative

SQLFluff also supports the Jinja templater with dbt builtins enabled. This can be faster for editor or pre-commit feedback, but it is not the same as the real dbt templater.

```ini
[sqlfluff]
templater = jinja

[sqlfluff:templater:jinja]
apply_dbt_builtins = True
```

Use the dbt templater when dbt macro rendering accuracy matters more than speed.

## Practical Caveats

- The dbt templater can be slower than the default Jinja templater.
- Some dbt macros may need database access at compile time.
- Use a test database or embedded adapter such as DuckDB for compatibility checks when possible.
- Keep complexity thresholds calibrated to source-review needs; v1 is not a replacement for dbt project graph analysis.

See the [docs index](index.md) for the rest of the user documentation.
