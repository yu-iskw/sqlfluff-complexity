"""Tests for rule context helpers."""

from __future__ import annotations

from pathlib import Path

from sqlfluff.core import FluffConfig, Linter
from sqlfluff.core.rules.context import RuleContext

from sqlfluff_complexity.core.scan.segment_tree import (
    is_nested_select_statement,
)
from sqlfluff_complexity.rules.base import file_segment_from_context


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


def test_file_segment_from_context_finds_file_in_parent_stack() -> None:
    """Lint contexts carry ``file`` on ``parent_stack`` when ``get_parent()`` is unset."""
    cfg = FluffConfig.from_kwargs(dialect="ansi")
    linter = Linter(config=cfg)
    root = linter.parse_string("select 1").tree
    assert getattr(root, "type", "") == "file"
    inner = root.segments[0]
    ctx = RuleContext(
        dialect=linter.dialect,
        fix=False,
        templated_file=None,
        path=Path("m.sql"),
        config=cfg,
        segment=inner,
        parent_stack=(root,),
    )
    assert file_segment_from_context(ctx) is root


def test_is_nested_select_statement_inner_derived_table() -> None:
    """Inner select in FROM is nested under outer select_statement."""
    selects = _all_segments_of_type("select * from (select 1 as x) s", "select_statement")
    assert len(selects) >= 2
    inner_sel = selects[-1]
    assert is_nested_select_statement(inner_sel) is True
