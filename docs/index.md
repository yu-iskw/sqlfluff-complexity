# Documentation

Start with [README](../README.md) for the project overview. These pages provide focused user and contributor documentation.

## End-User Guides

- [Quick start](quickstart.md): install, configure, and run the first CPX lint.
- [Configuration](configuration.md): thresholds, aggregate weights, and path overrides.
- [Rules reference](rules.md): CPX rule codes and metrics.
- [Reporting](reporting.md): console, SARIF, and JSON report mode.
- [Baseline and regression checks](baseline.md): snapshot baselines and CI regression gates without dbt artifacts.
- [dbt usage](dbt.md): SQLFluff dbt templater compatibility and v1 boundaries.
- [Dialects](dialects.md): tested dialects and SQLFluff/dbt mapping caveats.

## Contributor Docs

- [Contributing](../CONTRIBUTING.md): setup, tests, fixture authoring, ADRs, and verifier workflow.
- [Product design](product_design.md): product background and long-form design notes.
- [Architecture decisions](adr/): accepted architectural decisions and trade-offs.

## Suggested Reading Paths

New users:

1. [Quick start](quickstart.md)
2. [Rules reference](rules.md)
3. [Configuration](configuration.md)

dbt users:

1. [Quick start](quickstart.md)
2. [dbt usage](dbt.md)
3. [Dialects](dialects.md)

CI adopters:

1. [Reporting](reporting.md)
2. [Baseline and regression checks](baseline.md)
3. [Configuration](configuration.md)
4. [Rules reference](rules.md)
