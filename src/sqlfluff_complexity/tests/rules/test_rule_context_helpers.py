"""Tests for helpers in ``sqlfluff_complexity.rules.base`` (file root, nested selects)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from sqlfluff.core import FluffConfig, Linter
from sqlfluff.core.rules.context import RuleContext

from sqlfluff_complexity.core.scan.segment_tree import is_nested_select_statement
from sqlfluff_complexity.rules.base import file_segment_from_context

if TYPE_CHECKING:
    from sqlfluff.core.parser.segments.base import BaseSegment


def _all_segments_of_type(root: BaseSegment, segment_type: str) -> list[BaseSegment]:
    found: list[BaseSegment] = []
    stack: list[BaseSegment] = [root]
    while stack:
        seg = stack.pop()
        if getattr(seg, "type", "") == segment_type:
            found.append(seg)
        stack.extend(reversed(getattr(seg, "segments", ()) or ()))
    return found


def _ancestor_stack_to(root: BaseSegment, target: BaseSegment) -> tuple[BaseSegment, ...]:
    """Ancestors from parse root down to and including the direct parent of ``target``."""

    def dfs(node: BaseSegment, acc: list[BaseSegment]) -> bool:
        for child in getattr(node, "segments", ()) or ():
            if child is target:
                stack.clear()
                stack.extend([*acc, node])
                return True
            if dfs(child, [*acc, node]):
                return True
        return False

    stack: list[BaseSegment] = []
    if not dfs(root, []):
        message = "target segment not found under root"
        raise AssertionError(message)
    return tuple(stack)


def test_file_segment_from_context_finds_file_in_parent_stack_for_inner_select() -> None:
    """``parent_stack`` from root to parent of inner ``select_statement`` includes ``file``."""
    cfg = FluffConfig.from_kwargs(dialect="ansi")
    linter = Linter(config=cfg)
    root = linter.parse_string("select * from (select 1 as x) s").tree
    assert getattr(root, "type", "") == "file"
    selects = _all_segments_of_type(root, "select_statement")
    inner = selects[-1]
    parent_stack = _ancestor_stack_to(root, inner)
    assert parent_stack
    assert getattr(parent_stack[0], "type", "") == "file"
    ctx = RuleContext(
        dialect=linter.dialect,
        fix=False,
        templated_file=None,
        path=Path("m.sql"),
        config=cfg,
        segment=inner,
        parent_stack=parent_stack,
    )
    assert file_segment_from_context(ctx) is root


def test_file_segment_from_context_finds_file_in_parent_stack() -> None:
    """Lint contexts may carry ``file`` on ``parent_stack``."""
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
    root = Linter(dialect="ansi").parse_string("select * from (select 1 as x) s").tree
    selects = _all_segments_of_type(root, "select_statement")
    assert len(selects) >= 2
    inner_sel = selects[-1]
    assert is_nested_select_statement(inner_sel) is True
