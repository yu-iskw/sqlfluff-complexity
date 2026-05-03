"""Optional SQLFluff dbt templater integration tests."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from sqlfluff.core import FluffConfig, Linter

from sqlfluff_complexity.core.model.metrics import ComplexityMetrics
from sqlfluff_complexity.core.scan.segment_tree import collect_metrics

_DBT_PROJECT = Path(__file__).parent.parent / "fixtures" / "dbt_mini_project"
_DBT_MODEL = _DBT_PROJECT / "models" / "fct_order_complexity.sql"
_OPTIONAL_DBT_MODULES = (
    ("sqlfluff_templater_dbt", "sqlfluff-templater-dbt"),
    ("dbt.adapters.duckdb", "dbt-duckdb"),
)


def _require_dbt_templater_deps() -> None:
    """Skip clearly when the optional dbt templater dependency group is not installed."""
    missing_packages = []
    for module_name, package_name in _OPTIONAL_DBT_MODULES:
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        missing_package_list = ", ".join(missing_packages)
        pytest.skip(
            "Install optional dbt templater dependencies with "
            f"`uv sync --group dbt` to run these tests. Missing: {missing_package_list}.",
        )


def _make_dbt_linter() -> Linter:
    """Return a SQLFluff linter configured for the fixture dbt project."""
    _require_dbt_templater_deps()
    config = FluffConfig.from_path(str(_DBT_PROJECT))
    return Linter(config=config)


@pytest.mark.dbt_templater
def test_dbt_templater_parses_model_with_ref() -> None:
    """The dbt templater should render refs before SQLFluff parses complexity metrics."""
    dbt_linter = _make_dbt_linter()
    parsed_models = list(dbt_linter.parse_path(str(_DBT_MODEL)))

    assert len(parsed_models) == 1
    parsed_model = parsed_models[0]
    assert parsed_model.tree is not None
    assert not list(parsed_model.tree.recursive_crawl("unparsable"))
    assert collect_metrics(parsed_model.tree) == ComplexityMetrics(
        ctes=2,
        joins=0,
        subqueries=0,
        subquery_depth=0,
        case_expressions=1,
        boolean_operators=1,
        window_functions=0,
    )


@pytest.mark.dbt_templater
def test_dbt_templater_lints_model_with_complexity_rule() -> None:
    """The dbt-templated model should lint through the plugin rule without violations."""
    dbt_linter = _make_dbt_linter()
    linted = dbt_linter.lint_path(str(_DBT_MODEL))

    assert linted.get_violations() == []
