"""CPX_C201 show_contributors matches report output."""

from __future__ import annotations

from sqlfluff_complexity.tests.fixture_loader import read_sql_fixture
from sqlfluff_complexity.tests.sqlfluff_helpers import lint_sql, rule_violations


def test_c201_respects_show_contributors_false() -> None:
    """When show_contributors is false, omit Top contributors and Examples."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c201_aggregate_sample"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C201

        [sqlfluff:rules:CPX_C201]
        max_complexity_score = 4
        show_contributors = false
        complexity_weights = ctes:2,joins:2,subquery_depth:4,case_expressions:2,boolean_operators:1,window_functions:2
        """,
    )

    violations = rule_violations(linted, "CPX_C201")
    assert len(violations) == 1
    desc = violations[0].desc()
    assert "aggregate complexity score" in desc
    assert "Metrics:" in desc
    assert "Top contributors:" not in desc
    assert "Examples:" not in desc


def test_c201_respects_max_contributors_zero_with_show_true() -> None:
    """When max_contributors is 0, omit contributor detail like other CPX rules."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c201_aggregate_sample"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C201

        [sqlfluff:rules:CPX_C201]
        max_complexity_score = 4
        show_contributors = true
        max_contributors = 0
        complexity_weights = ctes:2,joins:2,subquery_depth:4,case_expressions:2,boolean_operators:1,window_functions:2
        """,
    )

    violations = rule_violations(linted, "CPX_C201")
    assert len(violations) == 1
    desc = violations[0].desc()
    assert "aggregate complexity score" in desc
    assert "Metrics:" in desc
    assert "Top contributors:" not in desc
    assert "Examples:" not in desc
