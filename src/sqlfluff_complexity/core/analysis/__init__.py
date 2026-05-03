"""Contributor-level complexity analysis and aggregate-score explainability."""

from sqlfluff_complexity.core.analysis.contributors import (
    RAW_SNIPPET_WORK_CAP,
    ComplexityAnalysis,
    MetricContributor,
    compact_segment_raw,
    format_contributor_examples,
    format_contributor_summary,
    segment_position,
    top_contributors,
    weighted_contributor_samples,
)
from sqlfluff_complexity.core.analysis.explainability import (
    explain_score_contributors,
    ranked_weighted_contributions,
    refactoring_hint_for_contributors,
)

__all__ = [
    "RAW_SNIPPET_WORK_CAP",
    "ComplexityAnalysis",
    "MetricContributor",
    "compact_segment_raw",
    "explain_score_contributors",
    "format_contributor_examples",
    "format_contributor_summary",
    "ranked_weighted_contributions",
    "refactoring_hint_for_contributors",
    "segment_position",
    "top_contributors",
    "weighted_contributor_samples",
]
