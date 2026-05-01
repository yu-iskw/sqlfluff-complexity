"""Optional dialect fixture tests for warehouse-specific SQLFluff parsers."""

from __future__ import annotations

from typing import Any

import pytest
from sqlfluff.core import FluffConfig, Linter

from sqlfluff_complexity.core.segment_tree import collect_metrics
from sqlfluff_complexity.tests.fixture_loader import (
    dbt_adapter_to_sqlfluff_dialect,
    dialect_extra_fixtures,
    expected_metrics_path,
    load_expected_metrics,
    read_sql_fixture,
    sql_fixture_path,
)

_EXPECTED_ADAPTER_MAPPING = {
    "dbt-postgres": "postgres",
    "dbt-redshift": "redshift",
    "dbt-snowflake": "snowflake",
    "dbt-bigquery": "bigquery",
    "dbt-athena-community": "athena",
    "dbt-spark": "sparksql",
}


def _case_id(case: Any) -> str:
    return case.fixture_id


def _parse_tree(sql: str, *, dialect: str) -> Any:
    parsed = Linter(dialect=dialect).parse_string(sql)
    assert parsed.tree is not None
    assert not list(parsed.tree.recursive_crawl("unparsable"))
    return parsed.tree


def _lint_with_complexity_rule(sql: str, *, dialect: str) -> Any:
    config = FluffConfig.from_string(
        f"""
        [sqlfluff]
        dialect = {dialect}
        rules = CPX_C201

        [sqlfluff:rules:CPX_C201]
        max_complexity_score = 100
        """
    )
    return Linter(config=config).lint_string(sql)


@pytest.mark.dialect_extra
def test_dbt_adapter_mapping_uses_sqlfluff_dialect_labels() -> None:
    """dbt adapter package names should map to explicit SQLFluff parser labels."""
    assert {
        adapter: dbt_adapter_to_sqlfluff_dialect(adapter) for adapter in _EXPECTED_ADAPTER_MAPPING
    } == _EXPECTED_ADAPTER_MAPPING
    assert dbt_adapter_to_sqlfluff_dialect("dbt-spark") == "sparksql"


@pytest.mark.dialect_extra
def test_dialect_extra_manifest_uses_readable_fixture_ids() -> None:
    """Manifest IDs should make dialect fixture failures easy to identify."""
    assert [case.fixture_id for case in dialect_extra_fixtures()] == [
        f"{case.dbt_adapter}->{case.sqlfluff_dialect}:{case.stem}"
        for case in dialect_extra_fixtures()
    ]


@pytest.mark.dialect_extra
@pytest.mark.parametrize("case", dialect_extra_fixtures(), ids=_case_id)
def test_dialect_extra_manifest_files_exist(case: Any) -> None:
    """Every declared dialect fixture should have SQL and expected metrics files."""
    assert sql_fixture_path(case.sqlfluff_dialect, case.stem).is_file()
    assert expected_metrics_path(case.sqlfluff_dialect, case.stem).is_file()


@pytest.mark.dialect_extra
@pytest.mark.parametrize("case", dialect_extra_fixtures(), ids=_case_id)
def test_dialect_extra_fixture_metrics_match_expected_json(case: Any) -> None:
    """Dialect fixtures should parse cleanly and produce stable metrics."""
    sql = read_sql_fixture(case.sqlfluff_dialect, case.stem)
    expected = load_expected_metrics(case.sqlfluff_dialect, case.stem)

    assert collect_metrics(_parse_tree(sql, dialect=case.sqlfluff_dialect)) == expected


@pytest.mark.dialect_extra
@pytest.mark.parametrize("case", dialect_extra_fixtures(), ids=_case_id)
def test_dialect_extra_fixtures_lint_with_complexity_rule(case: Any) -> None:
    """Dialect fixtures should run through SQLFluff linting with the plugin rule loaded."""
    sql = read_sql_fixture(case.sqlfluff_dialect, case.stem)
    linted = _lint_with_complexity_rule(sql, dialect=case.sqlfluff_dialect)

    assert linted.violations == []
