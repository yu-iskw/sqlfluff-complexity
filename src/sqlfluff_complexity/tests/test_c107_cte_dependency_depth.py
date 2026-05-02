"""Tests for CPX_C107 (CTE dependency depth) and structural metric extraction."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

from sqlfluff.core import Linter

from sqlfluff_complexity.core.segment_tree import collect_metrics
from sqlfluff_complexity.core.structural_metrics import cte_dependency_depth_for_with_clause
from sqlfluff_complexity.tests.sqlfluff_helpers import lint_sql, rule_violations

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlfluff.core.parser.segments.base import BaseSegment


def _iter_with_compound_statements(root: BaseSegment) -> Iterator[BaseSegment]:
    """Preorder DFS over ``with_compound_statement`` segments (consistent tree walk order)."""
    stack = [root]
    while stack:
        seg = stack.pop()
        if getattr(seg, "type", "") == "with_compound_statement":
            yield seg
        children = tuple(getattr(seg, "segments", ()) or ())
        stack.extend(reversed(children))


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


def test_metrics_chained_ctes_with_column_list_in_first_cte() -> None:
    """CTE body must be the query after AS, not the (col1, col2) list bracket."""
    sql = """
    WITH
      x (c1, c2) AS (
        SELECT 1 AS c1, 2 AS c2
      ),
      y AS (
        SELECT * FROM x
      )
    SELECT * FROM y
    """
    m = collect_metrics(_parse(sql))
    assert m.ctes == 2
    assert m.cte_dependency_depth == 2


def test_metrics_schema_qualified_table_not_counted_as_cte_ref() -> None:
    """Dotted table refs must not match CTEs by last segment (false edges)."""
    sql = """
    WITH
      orders AS (SELECT 1 AS id)
    SELECT * FROM catalog.orders
    """
    m = collect_metrics(_parse(sql))
    assert m.cte_dependency_depth == 1
    assert m.ctes == 1


def test_c107_outer_with_not_penalized_for_nested_with_depth() -> None:
    """Outer WITH depth must ignore deeper chains inside a nested WITH body."""
    sql = """
    WITH outer_wrap AS (
      WITH
        a AS (SELECT 1 AS id),
        b AS (SELECT * FROM a),
        c AS (SELECT * FROM b),
        d AS (SELECT * FROM c)
      SELECT * FROM d
    )
    SELECT * FROM outer_wrap
    """
    tree = _parse(sql)
    with_roots = list(_iter_with_compound_statements(tree))
    assert len(with_roots) == 2
    outer_with, inner_with = with_roots
    assert cte_dependency_depth_for_with_clause(outer_with) == 1
    assert cte_dependency_depth_for_with_clause(inner_with) == 4


def test_c107_lint_outer_passes_inner_flags_nested_chain() -> None:
    """Outer WITH should not violate from inner depth; inner WITH still enforces its own chain."""
    sql = dedent("""
        WITH outer_wrap AS (
          WITH
            a AS (SELECT 1 AS id),
            b AS (SELECT * FROM a),
            c AS (SELECT * FROM b),
            d AS (SELECT * FROM c)
          SELECT * FROM d
        )
        SELECT * FROM outer_wrap
        """).strip()
    linted = lint_sql(
        sql,
        dedent("""
            [sqlfluff]
            dialect = ansi
            rules = CPX_C107

            [sqlfluff:rules:CPX_C107]
            max_cte_dependency_depth = 3
            """).strip(),
    )
    violations = sorted(
        rule_violations(linted, "CPX_C107"),
        key=lambda v: (v.line_no, getattr(v, "line_pos", 0) or 0),
    )
    assert len(violations) == 1
    inner_last_cte_line = 6
    assert violations[0].line_no == inner_last_cte_line
    assert "CTE dependency depth is 4" in violations[0].desc()


def test_c107_nested_with_inner_and_outer_can_both_violate_with_max_zero() -> None:
    """Each WITH is evaluated separately; shallow outer + deep inner can yield two violations."""
    sql = dedent("""
        WITH outer_wrap AS (
          WITH
            a AS (SELECT 1 AS id),
            b AS (SELECT * FROM a),
            c AS (SELECT * FROM b),
            d AS (SELECT * FROM c)
          SELECT * FROM d
        )
        SELECT * FROM outer_wrap
        """).strip()
    linted = lint_sql(
        sql,
        dedent("""
            [sqlfluff]
            dialect = ansi
            rules = CPX_C107

            [sqlfluff:rules:CPX_C107]
            max_cte_dependency_depth = 0
            """).strip(),
    )
    violations = sorted(
        rule_violations(linted, "CPX_C107"),
        key=lambda v: (v.line_no, getattr(v, "line_pos", 0) or 0),
    )
    assert len(violations) == 2
    assert violations[0].line_no == 1
    assert "CTE dependency depth is 1" in violations[0].desc()
    assert violations[1].line_no == 6
    assert "CTE dependency depth is 4" in violations[1].desc()


def test_metrics_postgres_public_schema_table_not_false_edge_to_cte() -> None:
    """Postgres `schema.table` must not create a spurious edge to a same-named CTE."""
    sql = dedent("""
        WITH orders AS (SELECT 1 AS id)
        SELECT id FROM public.orders
        """).strip()
    m = collect_metrics(Linter(dialect="postgres").parse_string(sql).tree)
    assert m.ctes == 1
    assert m.cte_dependency_depth == 1


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
