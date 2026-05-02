"""SQLFluff segment-tree metric collection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlfluff_complexity.core.analysis import (
    ComplexityAnalysis,
    MetricContributor,
    compact_segment_raw,
    segment_position,
)
from sqlfluff_complexity.core.metrics import ComplexityMetrics
from sqlfluff_complexity.core.structural_metrics import compute_structural_metrics

if TYPE_CHECKING:
    from sqlfluff.core.parser.segments.base import BaseSegment

BOOLEAN_OPERATOR_RAW = {"AND", "OR"}


def analyze_segment_tree(root: BaseSegment) -> ComplexityAnalysis:
    """Collect metrics and per-segment contributors from a SQLFluff segment tree."""
    counter = _MetricCounter(root)
    counter.walk(root, active_selects=0, nested_depth=0)
    return ComplexityAnalysis(
        metrics=counter.to_metrics(),
        contributors=tuple(counter.contributors),
    )


def collect_metrics(root: BaseSegment) -> ComplexityMetrics:
    """Collect complexity metrics from a SQLFluff segment tree."""
    return analyze_segment_tree(root).metrics


def is_nested_select_statement(segment: BaseSegment) -> bool:
    """Return True when this select_statement sits under another select_statement.

    Used to avoid duplicate rule hits on nested selects. When parent metadata
    is unavailable, returns False so rules keep prior behavior.
    """
    if getattr(segment, "type", "") != "select_statement":
        return False

    current: BaseSegment | None = segment
    for _ in range(256):
        parent = _parent_segment(current)
        if parent is None:
            break
        if getattr(parent, "type", "") == "select_statement":
            return True
        current = parent
    return False


def _parent_segment(segment: BaseSegment | None) -> BaseSegment | None:
    if segment is None:
        return None
    parent = segment.get_parent()
    if isinstance(parent, tuple):
        return parent[0]
    return parent


class _MetricCounter:
    """Stateful collector for one SQLFluff segment tree walk."""

    def __init__(self, root: BaseSegment) -> None:
        self.ctes = 0
        self.joins = 0
        self.subqueries = 0
        self.subquery_depth = 0
        self.case_expressions = 0
        self.boolean_operators = 0
        self.window_functions = 0
        cte_dep, set_ops, expr_dep = compute_structural_metrics(root)
        self.cte_dependency_depth = cte_dep
        self.set_operation_count = set_ops
        self.expression_depth = expr_dep
        self.contributors: list[MetricContributor] = []

    def _add_contributor(
        self,
        metric: str,
        segment: BaseSegment,
        *,
        reason: str,
    ) -> None:
        line, column = segment_position(segment)
        self.contributors.append(
            MetricContributor(
                metric=metric,
                raw=compact_segment_raw(segment),
                line=line,
                column=column,
                segment_type=str(getattr(segment, "type", "")),
                reason=reason,
            ),
        )

    def walk(self, segment: BaseSegment, active_selects: int, nested_depth: int) -> None:
        """Walk a segment and its children."""
        segment_type = getattr(segment, "type", "")

        if segment_type == "common_table_expression":
            self.ctes += 1
            self._add_contributor("ctes", segment, reason="common table expression")
            self._walk_children(segment, active_selects=0, nested_depth=0)
            return

        next_active_selects, next_nested_depth = self._select_depths(
            segment,
            segment_type,
            active_selects,
            nested_depth,
        )
        self._count_segment(segment, segment_type)

        self._walk_children(
            segment,
            active_selects=next_active_selects,
            nested_depth=next_nested_depth,
        )

    def _walk_children(self, segment: BaseSegment, active_selects: int, nested_depth: int) -> None:
        for child in getattr(segment, "segments", ()) or ():
            self.walk(child, active_selects=active_selects, nested_depth=nested_depth)

    def _select_depths(
        self,
        segment: BaseSegment,
        segment_type: str,
        active_selects: int,
        nested_depth: int,
    ) -> tuple[int, int]:
        if segment_type != "select_statement":
            return active_selects, nested_depth

        if active_selects == 0:
            return 1, 0

        nested_depth += 1
        self.subqueries += 1
        self.subquery_depth = max(self.subquery_depth, nested_depth)
        self._add_contributor(
            "subquery_depth",
            segment,
            reason="nested select statement",
        )
        return active_selects + 1, nested_depth

    def _count_segment(self, segment: BaseSegment, segment_type: str) -> None:
        if segment_type == "join_clause":
            self.joins += 1
            self._add_contributor("joins", segment, reason="join clause")
        elif segment_type == "case_expression":
            self.case_expressions += 1
            self._add_contributor("case_expressions", segment, reason="case expression")
        elif segment_type == "over_clause":
            self.window_functions += 1
            self._add_contributor("window_functions", segment, reason="window over clause")
        elif self._is_boolean_operator(segment):
            self.boolean_operators += 1
            self._add_contributor(
                "boolean_operators",
                segment,
                reason="boolean and/or operator",
            )

    def _is_boolean_operator(self, segment: BaseSegment) -> bool:
        return (
            getattr(segment, "type", "") == "binary_operator"
            and getattr(segment, "raw_upper", "") in BOOLEAN_OPERATOR_RAW
        )

    def to_metrics(self) -> ComplexityMetrics:
        """Convert collected counters to the public metric model."""
        return ComplexityMetrics(
            ctes=self.ctes,
            joins=self.joins,
            subqueries=self.subqueries,
            subquery_depth=self.subquery_depth,
            case_expressions=self.case_expressions,
            boolean_operators=self.boolean_operators,
            window_functions=self.window_functions,
            cte_dependency_depth=self.cte_dependency_depth,
            set_operation_count=self.set_operation_count,
            expression_depth=self.expression_depth,
        )
