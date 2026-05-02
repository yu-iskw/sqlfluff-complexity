"""Tests for CPX_C107 (CTE dependency depth) and structural metric extraction."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlfluff.core import Linter

from sqlfluff_complexity.core.segment_tree import collect_metrics
from sqlfluff_complexity.tests.sqlfluff_helpers import lint_sql, rule_violations

if TYPE_CHECKING:
    from sqlfluff.core.parser.segments.base import BaseSegment


def _parse(sql: str, *, dialect: str = "ansi") -> BaseSegment:
    parsed = Linter(dialect=dialect).parse_string(sql)
    assert parsed.tree is not None
    return parsed.tree


def test_metrics_independent_ctes_low_chain_depth() -> None:
    """Independent CTEs should have shallow dependency depth vs count."""
    sql = """
    WITH
      a AS (SELECT 1 AS id),
      b AS (SELECT 2 AS id),
      c AS (SELECT 3 AS id)
    SELECT * FROM a
    """
    m = collect_metrics(_parse(sql))
    assert m.ctes == 3
    assert m.cte_dependency_depth == 1


def test_metrics_chained_ctes_depth_matches_chain() -> None:
    """Chained CTE references should yield depth equal to longest chain."""
    sql = """
    WITH
      a AS (SELECT 1 AS id),
      b AS (SELECT * FROM a),
      c AS (SELECT * FROM b),
      d AS (SELECT * FROM c),
      e AS (SELECT * FROM d)
    SELECT * FROM e
    """
    m = collect_metrics(_parse(sql))
    assert m.ctes == 5
    assert m.cte_dependency_depth == 5


def test_metrics_branching_cte_graph_longest_path() -> None:
    """Fork from one base should not inflate depth to total CTE count."""
    sql = """
    WITH
      base AS (SELECT 1 AS id),
      left_branch AS (SELECT * FROM base),
      right_branch AS (SELECT * FROM base),
      final AS (
        SELECT * FROM left_branch
        UNION ALL
        SELECT * FROM right_branch
      )
    SELECT * FROM final
    """
    m = collect_metrics(_parse(sql))
    assert m.ctes == 4
    assert m.cte_dependency_depth == 3
    assert m.set_operation_count >= 1


def test_c107_passes_under_default_threshold() -> None:
    """Independent CTEs should not violate CPX_C107 with default max depth."""
    sql = """
    WITH a AS (SELECT 1), b AS (SELECT 2), c AS (SELECT 3)
    SELECT * FROM a
    """
    linted = lint_sql(
        sql,
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C107
        """,
    )
    assert rule_violations(linted, "CPX_C107") == []


def test_c107_fails_when_chain_exceeds_threshold() -> None:
    """Long CTE chains should fail when max_cte_dependency_depth is tight."""
    sql = """
    WITH
      a AS (SELECT 1 AS id),
      b AS (SELECT * FROM a),
      c AS (SELECT * FROM b),
      d AS (SELECT * FROM c),
      e AS (SELECT * FROM d)
    SELECT * FROM e
    """
    linted = lint_sql(
        sql,
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C107

        [sqlfluff:rules:CPX_C107]
        max_cte_dependency_depth = 4
        """,
    )
    violations = rule_violations(linted, "CPX_C107")
    assert len(violations) == 1
    desc = violations[0].desc()
    assert "CTE dependency depth is 5" in desc
    assert "max_cte_dependency_depth=4" in desc


def test_c107_nested_select_outer_only() -> None:
    """Nested select inside CTE body should not duplicate rule hits."""
    sql = """
    WITH outer_cte AS (
      SELECT * FROM (SELECT 1 AS x) AS sq
    )
    SELECT * FROM outer_cte
    """
    linted = lint_sql(
        sql,
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C107

        [sqlfluff:rules:CPX_C107]
        max_cte_dependency_depth = 0
        """,
    )
    assert len(rule_violations(linted, "CPX_C107")) <= 1
