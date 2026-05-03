"""Invariant tests for metrics fixture loader and golden-metrics parametrization."""

from __future__ import annotations

from sqlfluff_complexity.tests.core.scan import test_fixture_metrics as golden_metrics
from sqlfluff_complexity.tests.fixture_loader import (
    METRICS_BOOTSTRAP_STEMS,
    _dialect_names_with_metric_sql,
    iter_metrics_bootstrap_targets,
)


def test_golden_metrics_parametrize_hook_matches_function_name() -> None:
    """``pytest_generate_tests`` must stay aligned with the golden test's ``__name__``."""
    assert (
        golden_metrics.test_fixture_metrics_match_expected_json.__name__
        == golden_metrics.METRICS_GOLDEN_TEST_NAME
    )


def test_iter_metrics_bootstrap_targets_cardinality() -> None:
    """Bootstrap emits one row per dialect in discovery times each bootstrap stem."""
    targets = iter_metrics_bootstrap_targets()
    assert targets, (
        "expected iter_metrics_bootstrap_targets to be non-empty "
        "(fixtures/sql dialect dirs with metrics_*.sql)"
    )
    dialects = {d for d, _ in targets}
    # Same dialect universe as loader discovery (Cartesian product contract).
    assert dialects == set(_dialect_names_with_metric_sql())
    assert len(targets) == len(METRICS_BOOTSTRAP_STEMS) * len(dialects)
    assert all(stem in METRICS_BOOTSTRAP_STEMS for _, stem in targets)
