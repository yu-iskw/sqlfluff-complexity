# Documentation

Start with [README](../README.md) for the project overview. These pages provide focused user and contributor documentation.

## End-User Guides

- [Quick start](quickstart.md): install, configure, and run the first CPX lint.
- [Configuration](configuration.md): thresholds, aggregate weights, path overrides, and severity.
- [Rules reference](rules.md): CPX rule codes, metrics, and default severity.
- [Reporting](reporting.md): console, JSON, SARIF, and HTML report mode with severity output.
- [Metric semantics](metric-semantics.md): precise counting rules for all 11 CPX metrics, dialect caveats, and false-positive guidance.
- [Dialects](dialects.md): official support matrix, best-effort dialects, and dialect-specific caveats.
- [SQLFluff lint behavior](sqlfluff-lint-behavior.md): how severity interacts with lint vs report mode.
- [Migration guide](migration.md): breaking changes in this release and how to update configs.
- [Adoption](adoption.md): calibration playbook, CI recipes, before/after examples.
- [dbt usage](dbt.md): SQLFluff dbt templater compatibility and v1 boundaries.

## Contributor Docs

- [Test layout](tests-layout.md): how `tests/core/`, `reporting/`, `integration/`, and `rules/` are organized.
- [Contributing](../CONTRIBUTING.md): setup, tests, fixture authoring, ADRs, and verifier workflow.
- [Internal import migration](migration-internal.md): mapping old `core` module paths after layout changes (forks and tooling).
- [Product design](product_design.md): product background and long-form design notes.
- [Architecture decisions](adr/): accepted architectural decisions and trade-offs.

## Suggested Reading Paths

New users:

1. [Quick start](quickstart.md)
2. [Rules reference](rules.md)
3. [Configuration](configuration.md)

Upgrading from a prior release:

1. [Migration guide](migration.md)
2. [Configuration: severity](configuration.md#severity)
3. [SQLFluff lint behavior](sqlfluff-lint-behavior.md)

dbt users:

1. [Quick start](quickstart.md)
2. [dbt usage](dbt.md)
3. [Dialects](dialects.md)

CI adopters:

1. [Reporting](reporting.md)
2. [Configuration](configuration.md)
3. [Rules reference](rules.md)
