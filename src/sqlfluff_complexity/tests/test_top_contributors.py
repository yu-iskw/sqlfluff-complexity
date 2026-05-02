"""Unit tests for contributor selection helpers."""

from __future__ import annotations

from sqlfluff_complexity.core.analysis import MetricContributor, top_contributors


def _c(metric: str, line: int, segment_type: str = "x") -> MetricContributor:
    return MetricContributor(
        metric=metric,
        raw="",
        line=line,
        column=1,
        segment_type=segment_type,
        reason="test",
    )


def test_top_contributors_filters_by_metric_preserves_order() -> None:
    """Filtering by metric keeps declaration order."""
    contribs = (_c("joins", 1), _c("ctes", 2), _c("joins", 3))
    got = top_contributors(contribs, metric="joins", limit=10)
    assert got == (_c("joins", 1), _c("joins", 3))


def test_top_contributors_limits() -> None:
    """Limit trims after filtering."""
    contribs = tuple(_c("joins", i) for i in range(10))
    got = top_contributors(contribs, metric="joins", limit=2)
    assert len(got) == 2


def test_top_contributors_none_metric_all_metrics_order() -> None:
    """metric=None returns contributors in source order up to limit."""
    contribs = (_c("a", 1), _c("b", 2), _c("c", 3))
    got = top_contributors(contribs, metric=None, limit=2)
    assert got == (_c("a", 1), _c("b", 2))


def test_top_contributors_empty() -> None:
    """Empty input yields empty tuple."""
    assert top_contributors((), metric="joins", limit=3) == ()


def test_top_contributors_zero_limit() -> None:
    """Zero limit yields empty."""
    assert top_contributors((_c("joins", 1),), metric="joins", limit=0) == ()
