"""Shared finding model for lint messages, JSON, and SARIF."""

from __future__ import annotations

from dataclasses import dataclass

from sqlfluff_complexity.core.analysis import MetricContributor
from sqlfluff_complexity.core.metrics import ComplexityMetrics


@dataclass(frozen=True)
class SourceLocation:
    """Stable location for a finding (1-based line/column)."""

    path: str | None
    line: int
    column: int


@dataclass(frozen=True)
class ComplexityFinding:
    """One complexity violation with metrics and optional contributors."""

    rule_id: str
    metric: str
    message: str
    remediation: str
    location: SourceLocation
    metrics: ComplexityMetrics
    score: int | None
    threshold: int | None
    contributors: tuple[MetricContributor, ...]
    level: str  # "note", "warning", or "error"
    aggregate_score: int | None = None
