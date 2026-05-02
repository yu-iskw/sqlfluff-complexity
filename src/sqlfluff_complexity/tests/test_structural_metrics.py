"""Unit tests for structural metric extraction (shared with ``_MetricCounter``)."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

from sqlfluff.core import Linter

from sqlfluff_complexity.core.segment_tree import collect_metrics
from sqlfluff_complexity.core.structural_metrics import (
    StructuralScanResult,
    compute_structural_metrics,
    count_set_operations,
    max_case_expression_nesting_depth,
    max_cte_dependency_depth,
    merge_structural_scan,
)

if TYPE_CHECKING:
    from sqlfluff.core.parser.segments.base import BaseSegment

_CASE_NESTED_SQL = dedent(
    """
    SELECT
      CASE
        WHEN true THEN
          CASE WHEN 1 = 1 THEN 1 ELSE 0 END
        ELSE 0
      END AS x
    """
).strip()


def _parse_tree(sql: str) -> BaseSegment:
    parsed = Linter(dialect="ansi").parse_string(sql)
    assert parsed.tree is not None
    return parsed.tree


def test_merge_structural_scan_matches_full_scan_on_tree() -> None:
    """Stacked updates from ``merge_structural_scan`` must match one ``compute_structural_metrics`` pass."""
    root = _parse_tree(
        dedent(
            """
            WITH
              a AS (SELECT 1),
              b AS (SELECT * FROM a)
            SELECT * FROM b
            UNION ALL
            SELECT * FROM a
            """
        ).strip()
    )
    acc = StructuralScanResult(0, 0, 0)
    stack: list[tuple[BaseSegment, int]] = [(root, 0)]
    while stack:
        seg, case_depth = stack.pop()
        st = getattr(seg, "type", "")
        acc = merge_structural_scan(acc, seg, case_depth)
        child_case_depth = case_depth + 1 if st == "case_expression" else case_depth
        children = getattr(seg, "segments", ()) or ()
        stack.extend((ch, child_case_depth) for ch in reversed(children))
    full = compute_structural_metrics(root)
    assert acc == full


def test_public_helpers_match_compute_structural_metrics() -> None:
    """Compatibility wrappers must delegate to the same scan as ``compute_structural_metrics``."""
    root = _parse_tree(_CASE_NESTED_SQL)
    full = compute_structural_metrics(root)
    assert max_cte_dependency_depth(root) == full.cte_dependency_depth
    assert count_set_operations(root) == full.set_operation_count
    assert max_case_expression_nesting_depth(root) == full.expression_depth


def test_collect_metrics_structural_fields_match_compute() -> None:
    """Single merged walk in ``collect_metrics`` must match standalone structural scan."""
    root = _parse_tree(_CASE_NESTED_SQL)
    m = collect_metrics(root)
    scan = compute_structural_metrics(root)
    assert m.cte_dependency_depth == scan.cte_dependency_depth
    assert m.set_operation_count == scan.set_operation_count
    assert m.expression_depth == scan.expression_depth


def test_nested_case_expression_depth() -> None:
    """Inner CASE inside outer CASE should yield expression_depth >= 2."""
    m = collect_metrics(_parse_tree(_CASE_NESTED_SQL))
    assert m.expression_depth >= 2
