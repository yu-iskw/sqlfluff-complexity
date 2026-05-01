# Contributing

Thanks for helping improve `sqlfluff-complexity`. This guide is for contributors and maintainers. End-user usage docs start in [README.md](README.md).

## Development Setup

Install the development environment:

```bash
make setup
```

This project uses:

- `uv` for dependency management
- Hatchling for packaging
- pytest orchestrated by Nox for tests
- Trunk for linting and formatting

## Common Commands

```bash
make lint                 # Trunk lint suite
make format               # Trunk formatting
make test                 # Default Nox test sessions
make test-dialect-extra   # Optional dialect fixture suite
make test-dbt-templater   # Optional dbt templater suite
make build                # Package build
make scan-vulnerabilities # Trivy, OSV-Scanner, and Grype
make codeql               # Local CodeQL analysis
```

Useful direct Nox commands:

```bash
uv run nox -s tests
uv run nox -s tests-3.12
uv run nox -s dialect_extra
uv run nox -s dbt_templater
```

## Test Suites

The default suite excludes optional markers so pull-request feedback stays fast.

- `dialect_extra`: optional parser/fixture matrix for non-ANSI dialects
- `dbt_templater`: optional SQLFluff dbt templater compatibility tests

Run optional suites when changing fixture loading, dialect-specific SQL, SQLFluff integration, dbt templater behavior, or CI workflows.

## Adding Dialect Fixtures

Dialect fixtures are development tests, not shipped package data.

1. Add SQL under `src/sqlfluff_complexity/tests/fixtures/sql/<sqlfluff_dialect>/`.
2. Add expected metrics JSON under `src/sqlfluff_complexity/tests/fixtures/expected/<sqlfluff_dialect>/`.
3. Keep fixture directory names as SQLFluff dialect labels, not dbt adapter names.
4. Keep fixtures small and focused on one parser-sensitive theme.
5. Ground new dialect syntax in official references where possible.
6. Run `make test-dialect-extra`.

Spark fixtures use `sparksql`. Databricks-specific syntax should be added separately under `databricks` only when intentional.

## Adding dbt Templater Coverage

dbt templater tests live behind the `dbt_templater` marker and optional `dbt` dependency group. They prove SQLFluff can render dbt models before CPX metrics/rules run.

Keep the v1 boundary clear:

- OK: SQLFluff dbt templater rendering, parsing, metrics, and linting
- Not OK for v1: direct `manifest.json` parsing or DAG-level complexity metrics

Run:

```bash
make test-dbt-templater
```

## Documentation Changes

Use this split:

- `README.md`: end-user portal
- `docs/*.md`: focused end-user guides and references
- `CONTRIBUTING.md`: developer workflows
- `docs/product_design.md`: product/design background
- `docs/adr/`: architectural decisions and trade-offs

Avoid duplicating volatile implementation details across many docs. Prefer linking to the focused reference page.

## ADRs

Use ADRs for decisions with architectural impact, cross-cutting consequences, strategic direction, or non-obvious trade-offs.

Examples that warrant ADRs:

- package architecture and public surfaces
- metric source-of-truth decisions
- dbt manifest scope decisions
- multi-version test orchestration choices

Routine docs edits, bug fixes, and local refactors usually do not need ADRs.

## Verification Before Handoff

For broad changes, run the repo verifier or equivalent checks before handoff:

```bash
make build
make lint
make test
make scan-vulnerabilities
make codeql
```

If the change touches optional suites, also run:

```bash
make test-dialect-extra
make test-dbt-templater
```

Coding-agent instructions and project conventions live in [AGENTS.md](AGENTS.md).
