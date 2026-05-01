# sqlfluff-complexity

SQLFluff plugin for SQL and dbt model complexity rules.

`sqlfluff-complexity` is currently under active implementation. The first slice focuses on
shared SQL complexity metrics, native SQLFluff rules, and a companion report command so teams can
use the same scoring semantics for strict linting and non-blocking CI reports.

Detailed rule behavior, report-mode design, and future dbt manifest work are still tracked in
[docs/product_design.md](docs/product_design.md) while implementation is underway.

## Project Status

- Native SQLFluff plugin and companion CLI are being built together.
- v1 measures SQLFluff-parsed SQL; dbt manifest and DAG-level metrics are deferred.
- Architecture decisions are recorded in [docs/adr/](docs/adr/).

## Tooling

- **Package Management**: [uv](https://github.com/astral-sh/uv)
- **Build System**: [Hatchling](https://hatch.pypa.io/latest/)
- **Linting & Formatting**: [Trunk](https://trunk.io/) (Ruff, Pyright, Pylint, Bandit; Ruff is also the formatter)
- **Testing**: [pytest](https://docs.pytest.org/) orchestrated by [Nox](https://nox.thea.codes/)
- **CI/CD**: GitHub Actions

## Test fixtures

Parser-driven metrics drift when SQLFluff dialect parsers change, so the project keeps curated SQL
under `src/sqlfluff_complexity/tests/fixtures/sql/<dialect>/` with optional golden metrics JSON under
`src/sqlfluff_complexity/tests/fixtures/expected/<dialect>/`.

- Fixture directory names are SQLFluff dialect names, not dbt adapter package names. For example,
  Spark SQL fixtures belong under `sparksql`, while Databricks-specific syntax belongs under
  `databricks`.
- dbt adapter names are useful coverage prompts, but they do not always map one-to-one to SQLFluff
  dialects. Treat `dbt-athena` / `dbt-trino` coverage carefully because Athena, Trino, and Presto
  syntax can overlap without being interchangeable.
- Dialect fixture themes should come from official references for each SQLFluff dialect: core SQL
  constructs for ANSI/Postgres-like parsers, warehouse-specific constructs for BigQuery/Snowflake,
  Spark-family syntax for SparkSQL/Databricks, and Trino-family syntax for Athena/Trino/Presto-like
  coverage. Keep fixtures small and focused on parser-sensitive complexity behavior.
- **Default PR tests** run the regular pytest suite, including ANSI fixtures, through Nox with
  `-m "not dialect_extra and not dbt_templater"` so optional suites stay out of pull-request
  feedback.
- **Optional dialect-only tests** use the `dialect_extra` marker and the explicit Nox session:
  `uv run nox -s dialect_extra`. You can still pass pytest selectors, for example
  `uv run nox -s dialect_extra -- -k snowflake`.
- **Optional dbt templater tests** use the `dbt_templater` marker and the explicit Nox session:
  `uv run nox -s dbt_templater`. This boundary is for SQLFluff dbt-templater compatibility only;
  v1 complexity metrics still come from SQLFluff-parsed SQL, not dbt manifests or DAG-level dbt
  metadata.
- **Scheduled / manual CI** runs dialect buckets through the same marker via
  [`.github/workflows/test-dialect-fixtures.yml`](.github/workflows/test-dialect-fixtures.yml).
  The workflow bounds pytest-xdist worker count so the optional suite can grow without consuming an
  unbounded runner.

## Security & Quality

This project keeps strict security and maintainability guardrails:

- **[GitHub CodeQL](https://codeql.github.com/)**: Deep analysis using the `security-and-quality` suite to track code health and catch vulnerabilities.
- **Complexity Guardrails**: Cyclomatic complexity is capped at **10** per function (enforced via Ruff `C901`).
- **Trunk Linters**: [Bandit](https://github.com/PyCQA/bandit) (security), [Semgrep](https://semgrep.dev/) (patterns), [Trivy](https://github.com/aquasecurity/trivy) (IaC/Secret scanning), and [OSV-Scanner](https://github.com/google/osv-scanner) (dependencies).

## Development

Conventions, build commands, and AI-agent instructions: see [AGENTS.md](AGENTS.md). Claude Code–specific config lives in `CLAUDE.md` (it imports [AGENTS.md](AGENTS.md)) and in [`.claude/`](.claude/).

```bash
make setup      # Install dependencies and set up environment
make lint       # Run all linters via Trunk
make format     # Auto-format code via Trunk
make test       # Run default Nox pytest sessions for Python 3.10, 3.11, and 3.12
make test-dialect-extra # Run optional dialect fixture tests
make test-dbt-templater # Run optional dbt templater compatibility tests
```

Useful direct Nox commands:

```bash
uv run nox -s tests            # Default multi-Python suite
uv run nox -s tests-3.12       # One default Python session
uv run nox -s dialect_extra    # Optional dialect fixtures
uv run nox -s dbt_templater    # Optional dbt templater compatibility
```
