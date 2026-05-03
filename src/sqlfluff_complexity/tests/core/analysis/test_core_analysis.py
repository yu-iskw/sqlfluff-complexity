"""Tests for segment-tree contributor analysis."""

from __future__ import annotations

from typing import Any
from unittest import mock

from sqlfluff.core import Linter

from sqlfluff_complexity.core.analysis import (
    RAW_SNIPPET_WORK_CAP,
    MetricContributor,
    compact_segment_raw,
    format_contributor_examples,
    segment_position,
)
from sqlfluff_complexity.core.scan.segment_tree import analyze_segment_tree, collect_metrics


def _parse_tree(sql: str, *, dialect: str = "ansi") -> Any:
    parsed = Linter(dialect=dialect).parse_string(sql)
    assert parsed.tree is not None
    return parsed.tree


def test_collect_metrics_matches_analyze_metrics() -> None:
    """collect_metrics should stay aligned with analyze_segment_tree."""
    sql = "select 1 from t join u on t.id = u.id where a = 1 and b = 2"
    root = _parse_tree(sql)
    analysis = analyze_segment_tree(root)
    assert collect_metrics(root) == analysis.metrics


def test_analyze_segment_tree_records_join_and_boolean_contributors() -> None:
    """Contributors should attach to counted segment types."""
    sql = "select 1 from t join u on t.id = u.id where a = 1 and b = 2"
    analysis = analyze_segment_tree(_parse_tree(sql))
    metrics = analysis.metrics
    assert metrics.joins == 1
    assert metrics.boolean_operators == 1
    kinds = {c.metric for c in analysis.contributors}
    assert "joins" in kinds
    assert "boolean_operators" in kinds


def test_compact_segment_raw_truncates_before_regex_on_huge_raw() -> None:
    """Avoid scanning megabyte literals when building contributor snippets."""
    huge = "x" * 5000
    fake_seg = mock.Mock()
    fake_seg.raw = huge
    out = compact_segment_raw(fake_seg)
    assert len(out) <= RAW_SNIPPET_WORK_CAP


def test_compact_segment_raw_collapses_whitespace() -> None:
    """Raw snippets should be single-line and bounded."""
    root = _parse_tree("select\n  1\n")
    seg = next(root.recursive_crawl("numeric_literal"))
    raw = compact_segment_raw(seg)
    assert "\n" not in raw
    assert raw == "1"


def test_format_contributor_examples_respects_weights() -> None:
    """Examples should prefer higher-weight metrics when possible."""
    contributors = (
        MetricContributor(
            metric="boolean_operators",
            raw="AND",
            line=2,
            column=1,
            segment_type="binary_operator",
            reason="test",
        ),
        MetricContributor(
            metric="joins",
            raw="JOIN u",
            line=1,
            column=10,
            segment_type="join_clause",
            reason="test",
        ),
    )
    weights = {"joins": 5, "boolean_operators": 1}
    text = format_contributor_examples(contributors, weights, max_items=2)
    assert text.startswith("Examples:")
    assert "joins" in text
    assert "boolean_operators" in text


def test_segment_position_best_effort() -> None:
    """Position helper should not raise for parsed segments."""
    root = _parse_tree("select 1")
    seg = next(root.recursive_crawl("numeric_literal"))
    line, col = segment_position(seg)
    assert isinstance(line, (int, type(None)))
    assert isinstance(col, (int, type(None)))


def test_segment_position_reads_join_clause_sqlfluff_marker() -> None:
    """join_clause segments expose line_no/line_pos on PositionMarker."""
    root = _parse_tree(
        "select * from base\njoin u on base.id = u.id",
        dialect="ansi",
    )
    seg = next(root.recursive_crawl("join_clause"))
    line, col = segment_position(seg)
    assert line == 2
    assert col == 1
