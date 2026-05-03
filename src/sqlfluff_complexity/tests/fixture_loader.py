"""Load SQL/metrics test fixtures, discover ``metrics_*.sql`` goldens, dbt manifest.

SQL file header (Hybrid E): ``source_url``, ``source_section``, ``license_note``,
``verbatim`` (``yes`` only with a strong ``license_note``; cloud docs default to
derived SQL + URL). Dialects are **subdirectories of** ``fixtures/sql/`` that contain
at least one ``metrics_*.sql``. ``discover_metrics_fixture_cases()`` pairs each such
SQL file with ``fixtures/expected/<dialect>/<stem>.metrics.json``.
``dialect_extra_fixtures()`` reuses the same stems for dbt adapter mappings.

Bootstrap
---------
``dev/bootstrap_exp_fixtures.py`` must use ``METRICS_BOOTSTRAP_STEMS`` and
``iter_metrics_bootstrap_targets()`` so dialect dirs match discovery and expansion
stems are defined once here. ``METRICS_BOOTSTRAP_STEMS`` / ``iter_metrics_bootstrap_targets()``
cover a **subset** of pairs that ``discover_metrics_fixture_cases()`` may return (discovery
includes every ``metrics_*.sql`` with a golden JSON, not only bootstrap stems).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from sqlfluff_complexity.core.model.metrics import ComplexityMetrics

_FIXTURES_ROOT = Path(__file__).parent / "fixtures"
_SQL_ROOT = _FIXTURES_ROOT / "sql"
_EXPECTED_ROOT = _FIXTURES_ROOT / "expected"
_METRICS_FIXTURE_GLOB = "metrics_*.sql"

# Subset of metrics fixture stems (not all metrics_*.sql); see module Bootstrap section.
METRICS_BOOTSTRAP_STEMS: tuple[str, ...] = (
    "metrics_exp_cpx_ddl",
    "metrics_exp_cpx_mutate",
    "metrics_exp_cpx_select",
    "metrics_exp_cpx_signature",
    "metrics_wave1_cte_join_window",
    "metrics_wave1_derived_union",
    "metrics_wave1_exists_boolean",
    "metrics_wave1_insert_archive",
)


def _dialect_names_with_metric_sql() -> tuple[str, ...]:
    """Return sorted dialect folder names that contain at least one ``metrics_*.sql``."""
    if not _SQL_ROOT.is_dir():
        return ()
    return tuple(
        child.name
        for child in sorted(_SQL_ROOT.iterdir())
        if child.is_dir() and any(child.glob(_METRICS_FIXTURE_GLOB))
    )


def _sorted_metric_sql_stems(dialect: str) -> tuple[str, ...]:
    """Return sorted stems (filename without ``.sql``) for ``metrics_*.sql`` fixtures."""
    dialect_dir = _SQL_ROOT / dialect
    if not dialect_dir.is_dir():
        return ()
    return tuple(sorted(p.stem for p in dialect_dir.glob(_METRICS_FIXTURE_GLOB)))


def iter_metrics_bootstrap_targets() -> tuple[tuple[str, str], ...]:
    """Return ``(dialect, stem)`` pairs for the bootstrap script (no golden JSON required).

    Dialects match ``_dialect_names_with_metric_sql()``; stems are ``METRICS_BOOTSTRAP_STEMS``.
    This Cartesian product is a **subset** of ``discover_metrics_fixture_cases()`` (which
    includes every ``metrics_*.sql`` with golden JSON, not only bootstrap stems).
    """
    return tuple(
        (dialect, stem)
        for dialect in _dialect_names_with_metric_sql()
        for stem in METRICS_BOOTSTRAP_STEMS
    )


@dataclass(frozen=True)
class DialectFixture:
    """Test-only mapping from a dbt adapter package to a SQLFluff dialect fixture."""

    dbt_adapter: str
    sqlfluff_dialect: str
    stem: str

    @property
    def fixture_id(self) -> str:
        """Return a pytest-friendly ID for this dialect fixture."""
        return f"{self.dbt_adapter}->{self.sqlfluff_dialect}:{self.stem}"


_DBT_ADAPTER_TO_SQLFLUFF_DIALECT = {
    "dbt-postgres": "postgres",
    "dbt-redshift": "redshift",
    "dbt-snowflake": "snowflake",
    "dbt-bigquery": "bigquery",
    "dbt-athena-community": "athena",
    "dbt-spark": "sparksql",
}
_DIALECT_EXTRA_FIXTURES = tuple(
    DialectFixture(
        dbt_adapter=dbt_adapter,
        sqlfluff_dialect=sqlfluff_dialect,
        stem=stem,
    )
    for dbt_adapter, sqlfluff_dialect in sorted(_DBT_ADAPTER_TO_SQLFLUFF_DIALECT.items())
    for stem in _sorted_metric_sql_stems(sqlfluff_dialect)
)


def sql_fixture_path(dialect: str, stem: str) -> Path:
    """Return the SQL fixture path for a dialect and stem."""
    return _SQL_ROOT / dialect / f"{stem}.sql"


def expected_metrics_path(dialect: str, stem: str) -> Path:
    """Return the expected metrics fixture path for a dialect and stem."""
    return _EXPECTED_ROOT / dialect / f"{stem}.metrics.json"


def read_sql_fixture(dialect: str, stem: str) -> str:
    """Return UTF-8 SQL text for a dialect-specific fixture."""
    return sql_fixture_path(dialect, stem).read_text(encoding="utf-8")


def discover_metrics_fixture_cases() -> tuple[tuple[str, str], ...]:
    """Return ``(dialect, stem)`` pairs for every ``metrics_*.sql`` with expected JSON.

    Each pair must have ``fixtures/sql/<dialect>/<stem>.sql`` and
    ``fixtures/expected/<dialect>/<stem>.metrics.json``. Raises ``FileNotFoundError``
    with a clear message when the expected sidecar is missing.
    """
    cases: list[tuple[str, str]] = []
    for dialect in _dialect_names_with_metric_sql():
        for stem in _sorted_metric_sql_stems(dialect):
            expected_path = expected_metrics_path(dialect, stem)
            if not expected_path.is_file():
                msg = (
                    f"Metrics fixture {dialect}/{stem} is missing expected JSON at "
                    f"{expected_path}. Add {expected_path.name} or remove the SQL file."
                )
                raise FileNotFoundError(msg)
            cases.append((dialect, stem))
    return tuple(cases)


def load_expected_metrics(dialect: str, stem: str) -> ComplexityMetrics:
    """Load expected metrics from JSON next to the SQL fixture stem."""
    data: dict[str, Any] = json.loads(
        expected_metrics_path(dialect, stem).read_text(encoding="utf-8")
    )
    merged: dict[str, Any] = {}
    for field_info in fields(ComplexityMetrics):
        name = field_info.name
        if name in data:
            merged[name] = data[name]
        else:
            merged[name] = getattr(ComplexityMetrics(), name)
    return ComplexityMetrics(**merged)


def dbt_adapter_to_sqlfluff_dialect(dbt_adapter: str) -> str:
    """Return the SQLFluff dialect label for a dbt adapter package name."""
    return _DBT_ADAPTER_TO_SQLFLUFF_DIALECT[dbt_adapter]


def dialect_extra_fixtures() -> tuple[DialectFixture, ...]:
    """Return the optional dialect fixture manifest."""
    return _DIALECT_EXTRA_FIXTURES
