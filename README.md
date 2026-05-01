# sqlfluff-complexity

SQLFluff rules and reports for finding SQL and dbt models that are too complex to review safely.

`sqlfluff-complexity` adds CPX rules to SQLFluff for CTE count, join count, nested
subquery depth, `CASE` expressions, boolean predicates, window functions, and an
aggregate weighted complexity score. The same metric engine also powers a companion
`sqlfluff-complexity report` command for non-blocking console and SARIF reports.

## Who It Is For

- Analytics engineers who want dbt models to stay small enough to review.
- Data platform teams that already run SQLFluff in local development or CI.
- Teams that want gradual complexity reporting before turning on strict lint failures.

## Quick Start

Install the package, enable CPX rules in `.sqlfluff`, then run SQLFluff:

```ini
[sqlfluff]
dialect = postgres
rules = CPX_C101,CPX_C102,CPX_C103,CPX_C104,CPX_C105,CPX_C106,CPX_C201
```

```bash
sqlfluff lint models/
```

For a complete walkthrough, see [docs/quickstart.md](docs/quickstart.md).

## Documentation

- [Quick start](docs/quickstart.md): install, configure, and run the first lint.
- [Configuration](docs/configuration.md): thresholds, aggregate weights, and path overrides.
- [Rules reference](docs/rules.md): CPX rule codes and what each metric counts.
- [Reporting](docs/reporting.md): console and SARIF report mode.
- [dbt usage](docs/dbt.md): SQLFluff dbt templater compatibility and v1 boundaries.
- [Dialects](docs/dialects.md): tested dialects and dbt adapter mapping caveats.
- [Docs index](docs/index.md): all user, contributor, and design documents.

## Project Status

- Native SQLFluff plugin rules and the companion report CLI are available in the package.
- v1 measures SQLFluff-parsed SQL; direct dbt `manifest.json` and DAG-level metrics are deferred.
- Architecture decisions are recorded in [docs/adr/](docs/adr/).

## Development

Contributor setup, Nox sessions, fixture authoring, ADR workflow, and verifier guidance live in
[CONTRIBUTING.md](CONTRIBUTING.md). Agent-specific project instructions live in
[AGENTS.md](AGENTS.md).
