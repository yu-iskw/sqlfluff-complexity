"""Unit tests for aggregate score explainability helpers."""

from __future__ import annotations

from sqlfluff_complexity.core.explainability import (
    explain_score_contributors,
    ranked_weighted_contributions,
    refactoring_hint_for_contributors,
)
from sqlfluff_complexity.core.metrics import ComplexityMetrics


def test_ranked_contributions_ignores_zero_metric_values() -> None:
    """Metrics with zero raw count should not appear."""
    metrics = ComplexityMetrics(
        ctes=0,
        joins=10,
        subquery_depth=0,
        case_expressions=0,
        boolean_operators=0,
        window_functions=0,
    )
    weights = {
        "ctes": 2,
        "joins": 2,
        "subquery_depth": 4,
        "case_expressions": 2,
        "boolean_operators": 1,
        "window_functions": 2,
    }
    assert ranked_weighted_contributions(metrics, weights) == [("joins", 20)]


def test_ranked_contributions_ignores_zero_weights() -> None:
    """Metrics with zero weight should not appear even when raw value is non-zero."""
    metrics = ComplexityMetrics(
        ctes=4,
        joins=10,
        subquery_depth=2,
        case_expressions=3,
        boolean_operators=5,
        window_functions=1,
    )
    weights = {
        "ctes": 2,
        "joins": 2,
        "subquery_depth": 4,
        "case_expressions": 2,
        "boolean_operators": 0,
        "window_functions": 2,
    }
    ranked = ranked_weighted_contributions(metrics, weights)
    assert [name for name, _ in ranked] == [
        "joins",
        "ctes",
        "subquery_depth",
        "case_expressions",
        "window_functions",
    ]
    assert "boolean_operators" not in dict(ranked)


def test_ranked_contributions_sorts_by_descending_contribution_then_name() -> None:
    """Contributions should sort high to low; ties break by metric key ascending."""
    metrics = ComplexityMetrics(
        ctes=4,
        joins=10,
        subquery_depth=2,
        case_expressions=3,
        boolean_operators=5,
        window_functions=1,
    )
    weights = {
        "ctes": 2,
        "joins": 2,
        "subquery_depth": 4,
        "case_expressions": 2,
        "boolean_operators": 1,
        "window_functions": 2,
    }
    assert ranked_weighted_contributions(metrics, weights) == [
        ("joins", 20),
        ("ctes", 8),
        ("subquery_depth", 8),
        ("case_expressions", 6),
        ("boolean_operators", 5),
        ("window_functions", 2),
    ]


def test_ranked_contributions_tie_breaks_alphabetically() -> None:
    """Equal weighted contributions should order by metric name."""
    metrics = ComplexityMetrics(
        ctes=1,
        joins=1,
        subquery_depth=0,
        case_expressions=0,
        boolean_operators=0,
        window_functions=0,
    )
    weights = {
        "ctes": 5,
        "joins": 5,
        "subquery_depth": 1,
        "case_expressions": 1,
        "boolean_operators": 1,
        "window_functions": 1,
    }
    assert ranked_weighted_contributions(metrics, weights) == [
        ("ctes", 5),
        ("joins", 5),
    ]


def test_explain_score_contributors_respects_max_items() -> None:
    """Formatted contributors should cap at max_items."""
    metrics = ComplexityMetrics(
        ctes=4,
        joins=10,
        subquery_depth=2,
        case_expressions=3,
        boolean_operators=5,
        window_functions=1,
    )
    weights = {
        "ctes": 2,
        "joins": 2,
        "subquery_depth": 4,
        "case_expressions": 2,
        "boolean_operators": 1,
        "window_functions": 2,
    }
    assert (
        explain_score_contributors(metrics, weights, max_items=3)
        == "joins=20, ctes=8, subquery_depth=8"
    )
    assert explain_score_contributors(metrics, weights, max_items=1) == "joins=20"
    assert explain_score_contributors(metrics, weights, max_items=0) == ""


def test_refactoring_hint_single_contributor() -> None:
    """One contributor should produce a single focused phrase."""
    hint = refactoring_hint_for_contributors(["joins"])
    assert hint.startswith("Consider ")
    assert "splitting high-fan-in joins" in hint
    assert hint.endswith(" into smaller intermediate models.")


def test_refactoring_hint_two_contributors() -> None:
    """Two contributors should join with 'or'."""
    hint = refactoring_hint_for_contributors(["joins", "ctes"])
    assert " or " in hint
    assert "splitting high-fan-in joins" in hint
    assert "breaking long CTE chains" in hint


def test_refactoring_hint_many_contributors() -> None:
    """Three or more contributors should use comma-separated list before final 'or'."""
    hint = refactoring_hint_for_contributors(["joins", "ctes", "boolean_operators"])
    assert "splitting high-fan-in joins" in hint
    assert "breaking long CTE chains" in hint
    assert "simplifying dense predicates" in hint
    assert ", or " in hint


def test_refactoring_hint_empty_falls_back() -> None:
    """No known contributors should still yield a short actionable hint."""
    assert "Consider " in refactoring_hint_for_contributors([])
    assert "intermediate models" in refactoring_hint_for_contributors([])
