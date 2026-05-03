"""Tests for nested-segment helpers used by CPX rules."""

from __future__ import annotations

from sqlfluff.core import Linter

from sqlfluff_complexity.core.scan.segment_tree import (
    is_nested_select_statement,
    is_nested_set_expression,
)


def _all_segments_of_type(sql: str, segment_type: str) -> list:
    root = Linter(dialect="ansi").parse_string(sql).tree
    found: list = []
    stack = [root]
    while stack:
        seg = stack.pop()
        if getattr(seg, "type", "") == segment_type:
            found.append(seg)
        stack.extend(reversed(getattr(seg, "segments", ()) or ()))
    return found


def test_is_nested_set_expression_true_for_inner_union() -> None:
    """Parenthesized union yields one inner set_expression under an outer set_expression."""
    expressions = _all_segments_of_type(
        "(select 1 union all select 2) union all select 3",
        "set_expression",
    )
    assert len(expressions) == 2
    nested = [s for s in expressions if is_nested_set_expression(s)]
    assert len(nested) == 1
    assert is_nested_set_expression(nested[0]) is True


def test_is_nested_set_expression_false_for_only_outer_union() -> None:
    """A single flat union has one set_expression with no set_expression ancestor."""
    expressions = _all_segments_of_type(
        "select 1 union all select 2 union all select 3",
        "set_expression",
    )
    assert len(expressions) == 1
    assert is_nested_set_expression(expressions[0]) is False


def test_is_nested_select_statement_inner_derived_table() -> None:
    """Inner select in FROM is nested under outer select_statement."""
    selects = _all_segments_of_type("select * from (select 1 as x) s", "select_statement")
    assert len(selects) >= 2
    inner_sel = selects[-1]
    assert is_nested_select_statement(inner_sel) is True
