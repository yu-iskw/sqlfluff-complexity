"""Helpers for loading SQL and expected metrics from test fixtures."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from sqlfluff_complexity.core.model.metrics import ComplexityMetrics

_FIXTURES_ROOT = Path(__file__).parent / "fixtures"
_SQL_ROOT = _FIXTURES_ROOT / "sql"
_EXPECTED_ROOT = _FIXTURES_ROOT / "expected"
_DIALECT_EXTRA_STEMS = {
    "athena": (
        "metrics_dialect_baseline",
        "metrics_derived_subquery",
        "metrics_unnest_join",
    ),
    "bigquery": (
        "metrics_dialect_baseline",
        "metrics_array_struct_unnest",
    ),
    "postgres": (
        "metrics_dialect_baseline",
        "metrics_lateral_join",
    ),
    "redshift": (
        "metrics_dialect_baseline",
        "metrics_derived_subquery",
        "metrics_qualify_window",
    ),
    "snowflake": (
        "metrics_dialect_baseline",
        "metrics_flatten_lateral",
        "metrics_qualify_window",
    ),
    "sparksql": (
        "metrics_dialect_baseline",
        "metrics_lateral_view_explode",
    ),
}


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
    for dbt_adapter, sqlfluff_dialect in _DBT_ADAPTER_TO_SQLFLUFF_DIALECT.items()
    for stem in _DIALECT_EXTRA_STEMS[sqlfluff_dialect]
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
