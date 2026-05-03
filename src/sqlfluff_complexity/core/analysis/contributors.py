"""Contributor-level complexity analysis for SQLFluff segment trees."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from sqlfluff.core.parser.segments.base import BaseSegment

    from sqlfluff_complexity.core.model.metrics import ComplexityMetrics


_RAW_MAX_LEN = 120
RAW_SNIPPET_WORK_CAP = _RAW_MAX_LEN + 80


@dataclass(frozen=True)
class MetricContributor:
    """One concrete segment that contributed to a complexity metric."""

    metric: str
    raw: str
    line: int | None
    column: int | None
    segment_type: str
    reason: str


@dataclass(frozen=True)
class ComplexityAnalysis:
    """Metrics plus per-segment contributors for explainability."""

    metrics: ComplexityMetrics
    contributors: tuple[MetricContributor, ...]


def compact_segment_raw(segment: BaseSegment | None) -> str:
    """Return a compact, truncation-safe raw snippet for reporting."""
    if segment is None:
        return ""
    raw = getattr(segment, "raw", "") or ""
    raw = raw.strip()
    # Cap work before whitespace normalization (very large segment.raw is rare).
    work_cap = RAW_SNIPPET_WORK_CAP
    if len(raw) > work_cap:
        raw = raw[:work_cap]
    raw = re.sub(r"\s+", " ", raw)
    if len(raw) > _RAW_MAX_LEN:
        end = _RAW_MAX_LEN - 3
        return f"{raw[:end]}..."
    return raw


def _int_attr(marker: object, *names: str) -> int | None:
    """First usable integer attribute on ``marker``."""
    for name in names:
        raw = getattr(marker, name, None)
        if raw is None:
            continue
        try:
            return int(raw)
        except (TypeError, ValueError):
            continue
    return None


def segment_position(segment: BaseSegment | None) -> tuple[int | None, int | None]:
    """Best-effort line/column from SQLFluff position markers."""
    if segment is None:
        return None, None
    marker = getattr(segment, "pos_marker", None)
    if marker is None:
        return None, None
    line_int = _int_attr(marker, "line_no", "working_line_no", "lineno")
    col_int = _int_attr(marker, "line_pos", "working_line_pos", "pos")
    return line_int, col_int


def _pick_contributor_examples(
    contributors: Sequence[MetricContributor],
    weights: Mapping[str, int],
    max_items: int,
) -> list[MetricContributor]:
    indexed = _contributors_sorted_by_weight(contributors, weights)
    chosen = _unique_metrics_from_sorted(indexed, max_items)
    return _backfill_contributors(chosen, contributors, max_items)


def _contributors_sorted_by_weight(
    contributors: Sequence[MetricContributor],
    weights: Mapping[str, int],
) -> list[tuple[int, MetricContributor]]:
    indexed = list(enumerate(contributors))
    indexed.sort(
        key=lambda pair: (
            -int(weights.get(pair[1].metric, 0)),
            pair[1].metric,
            pair[0],
        ),
    )
    return indexed


def _unique_metrics_from_sorted(
    indexed: list[tuple[int, MetricContributor]],
    max_items: int,
) -> list[MetricContributor]:
    chosen: list[MetricContributor] = []
    seen_metrics: set[str] = set()
    for _, contributor in indexed:
        if len(chosen) >= max_items:
            break
        if contributor.metric in seen_metrics:
            continue
        chosen.append(contributor)
        seen_metrics.add(contributor.metric)
    return chosen


def _backfill_contributors(
    chosen: list[MetricContributor],
    contributors: Sequence[MetricContributor],
    max_items: int,
) -> list[MetricContributor]:
    if len(chosen) >= max_items:
        return chosen[:max_items]
    for contributor in contributors:
        if len(chosen) >= max_items:
            break
        if contributor not in chosen:
            chosen.append(contributor)
    return chosen[:max_items]


def top_contributors(
    contributors: Iterable[MetricContributor],
    *,
    metric: str | None,
    limit: int,
) -> tuple[MetricContributor, ...]:
    """Select up to ``limit`` contributors deterministically.

    When ``metric`` is set, prefer contributors for that metric (source order).
    When ``metric`` is None, return contributors across all metrics in source order.
    """
    if limit < 1:
        return ()

    items = tuple(contributors)
    if metric is None:
        return items[:limit] if items else ()

    filtered = tuple(c for c in items if c.metric == metric)
    return filtered[:limit]


def format_contributor_summary(
    contributors: Sequence[MetricContributor],
    *,
    limit: int,
) -> str:
    """Compact one-line summary: ``line N col M segment_type; ...``."""
    if limit < 1 or not contributors:
        return ""

    parts: list[str] = []
    for contributor in contributors[:limit]:
        line = contributor.line if contributor.line is not None else "?"
        col = contributor.column if contributor.column is not None else "?"
        parts.append(f"line {line} col {col} {contributor.segment_type}")

    return "; ".join(parts)


def weighted_contributor_samples(
    contributors: Sequence[MetricContributor],
    weights: Mapping[str, int],
    *,
    max_items: int,
) -> tuple[MetricContributor, ...]:
    """Pick up to ``max_items`` contributors for score-weighted explainability."""
    if max_items < 1 or not contributors:
        return ()
    chosen = _pick_contributor_examples(contributors, weights, max_items)
    return tuple(chosen)


def format_contributor_examples(
    contributors: Sequence[MetricContributor],
    weights: Mapping[str, int],
    *,
    max_items: int = 3,
) -> str:
    """Build a short ``Examples: ...`` clause from contributor records."""
    if max_items < 1 or not contributors:
        return ""

    chosen = list(weighted_contributor_samples(contributors, weights, max_items=max_items))
    parts: list[str] = []
    for contributor in chosen:
        line = contributor.line
        loc = f" at line {line}" if line is not None else ""
        parts.append(f"{contributor.metric}{loc}: {contributor.raw}")

    if not parts:
        return ""
    return "Examples: " + ", ".join(parts)
