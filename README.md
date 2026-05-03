# sqlfluff-complexity

SQLFluff rules and reports for finding SQL and dbt models that are too complex to review safely.

`sqlfluff-complexity` adds CPX rules to SQLFluff for CTE count, join count, nested
subquery depth, `CASE` expressions, nested `CASE` depth, boolean predicates, window functions,
CTE dependency depth, set operations (`UNION` / `INTERSECT` / `EXCEPT`), and an aggregate weighted
complexity score. The same metric engine also powers a companion
`sqlfluff-complexity report` command for non-blocking console, JSON, and SARIF reports.

## Who It Is For

- Analytics engineers who want dbt models to stay small enough to review.
- Data platform teams that already run SQLFluff in local development or CI.
- Teams that want gradual complexity reporting before turning on strict lint failures.

## Quick Start

Install the custom SQLFluff plugin in the same Python environment where you run SQLFluff:

```bash
pip install sqlfluff-complexity
```

If your project uses `uv`:

```bash
uv add --dev sqlfluff-complexity
```

Then enable CPX rules in `.sqlfluff` and run SQLFluff:

```ini
[sqlfluff]
dialect = postgres
rules = CPX_C101,CPX_C102,CPX_C103,CPX_C104,CPX_C105,CPX_C106,CPX_C107,CPX_C108,CPX_C109,CPX_C201
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
- [Adoption](docs/adoption.md): calibration, CI/SARIF examples, before/after SQL vignette.
- [dbt usage](docs/dbt.md): SQLFluff dbt templater compatibility and v1 boundaries.
- [Dialects](docs/dialects.md): tested dialects and dbt adapter mapping caveats.
- [Docs index](docs/index.md): all user, contributor, and design documents.
- [Internal import migration](docs/migration-internal.md): if you import `sqlfluff_complexity.core` submodules directly, update paths after subpackage refactors.

## Large dbt projects

This plugin does **not** read dbt artifacts (`manifest.json`, `run_results.json`, `catalog.json`) or graph metadata. Complexity is measured from the SQLFluff parse tree only—which aligns well with [SQLFluff’s dbt templater](docs/dbt.md) so `ref()`, `source()`, and macros compile before linting.

Practical adoption patterns:

- Use the dbt templater when you need compiled SQL fidelity; keep `sqlfluff-complexity` focused on structural signals from parsed SQL.
- Tune thresholds per rule and use [`path_overrides`](docs/configuration.md) on `CPX_C201` where staging vs marts need different budgets.
- Prefer `sqlfluff lint` on changed models in CI and [`sqlfluff-complexity report`](docs/reporting.md) for broader visibility without failing builds.
- For **CTE dependency depth**, see [docs/rules.md](docs/rules.md) (CPX_C107) and [docs/reporting.md](docs/reporting.md) (report vs per-`WITH` lint).

See also [dbt usage](docs/dbt.md) and [configuration](docs/configuration.md).

## Project Status

- Native SQLFluff plugin rules and the companion report CLI are available in the package.
- v1 measures SQLFluff-parsed SQL; direct dbt `manifest.json` and DAG-level metrics are deferred.
- Architecture decisions are recorded in [docs/adr/](docs/adr/).

## Development

Contributor setup, Nox sessions, fixture authoring, ADR workflow, and verifier guidance live in
[CONTRIBUTING.md](CONTRIBUTING.md). Agent-specific project instructions live in
[AGENTS.md](AGENTS.md).
