"""Contributor-level complexity analysis for SQLFluff segment trees."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from sqlfluff.core.parser.segments.base import BaseSegment


_RAW_MAX_LEN = 120


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

    metrics: "ComplexityMetrics"
    contributors: tuple[MetricContributor, ...]


def compact_segment_raw(segment: BaseSegment | None) -> str:
    """Return a compact, truncation-safe raw snippet for reporting."""
    if segment is None:
        return ""
    raw = getattr(segment, "raw", "") or ""
    raw = raw.strip()
    raw = re.sub(r"\s+", " ", raw)
    if len(raw) > _RAW_MAX_LEN:
        end = _RAW_MAX_LEN - 3
        return f"{raw[:end]}..."
    return raw


def segment_position(segment: BaseSegment | None) -> tuple[int | None, int | None]:
    """Best-effort line/column from SQLFluff position markers."""
    if segment is None:
        return None, None
    marker = getattr(segment, "pos_marker", None)
    if marker is None:
        return None, None
    line_no = getattr(marker, "lineno", None)
    col = getattr(marker, "pos", None)
    try:
        line_int = int(line_no) if line_no is not None else None
    except (TypeError, ValueError):
        line_int = None
    try:
        col_int = int(col) if col is not None else None
    except (TypeError, ValueError):
        col_int = None
    return line_int, col_int


def format_contributor_examples(
    contributors: Sequence[MetricContributor],
    weights: Mapping[str, int],
    *,
    max_items: int = 3,
) -> str:
    """Build a short ``Examples: ...`` clause from contributor records."""
    if max_items < 1 or not contributors:
        return ""

    indexed = list(enumerate(contributors))
    indexed.sort(
        key=lambda pair: (
            -int(weights.get(pair[1].metric, 0)),
            pair[1].metric,
            pair[0],
        ),
    )

    chosen: list[MetricContributor] = []
    seen_metrics: set[str] = set()
    for _, contributor in indexed:
        if len(chosen) >= max_items:
            break
        if contributor.metric in seen_metrics:
            continue
        chosen.append(contributor)
        seen_metrics.add(contributor.metric)

    if len(chosen) < max_items:
        for contributor in contributors:
            if len(chosen) >= max_items:
                break
            if contributor not in chosen:
                chosen.append(contributor)

    parts: list[str] = []
    for contributor in chosen[:max_items]:
        line = contributor.line
        loc = f" at line {line}" if line is not None else ""
        parts.append(f"{contributor.metric}{loc}: {contributor.raw}")

    if not parts:
        return ""
    return f"Examples: {', '.join(parts)}"


if TYPE_CHECKING:
    from sqlfluff_complexity.core.metrics import ComplexityMetrics
