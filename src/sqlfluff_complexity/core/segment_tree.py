"""SQLFluff segment-tree metric collection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlfluff_complexity.core.metrics import ComplexityMetrics

if TYPE_CHECKING:
    from sqlfluff.core.parser.segments.base import BaseSegment

BOOLEAN_OPERATOR_RAW = {"AND", "OR"}


def collect_metrics(root: BaseSegment) -> ComplexityMetrics:
    """Collect complexity metrics from a SQLFluff segment tree."""
    counter = _MetricCounter()
    counter.walk(root, active_selects=0, nested_depth=0)
    return counter.to_metrics()


class _MetricCounter:
    """Stateful collector for one SQLFluff segment tree walk."""

    def __init__(self) -> None:
        self.ctes = 0
        self.joins = 0
        self.subqueries = 0
        self.subquery_depth = 0
        self.case_expressions = 0
        self.boolean_operators = 0
        self.window_functions = 0

    def walk(self, segment: BaseSegment, active_selects: int, nested_depth: int) -> None:
        """Walk a segment and its children."""
        segment_type = getattr(segment, "type", "")

        if segment_type == "common_table_expression":
            self.ctes += 1
            self._walk_children(segment, active_selects=0, nested_depth=0)
            return

        next_active_selects, next_nested_depth = self._select_depths(
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
        return active_selects + 1, nested_depth

    def _count_segment(self, segment: BaseSegment, segment_type: str) -> None:
        if segment_type == "join_clause":
            self.joins += 1
        elif segment_type == "case_expression":
            self.case_expressions += 1
        elif segment_type == "over_clause":
            self.window_functions += 1
        elif self._is_boolean_operator(segment):
            self.boolean_operators += 1

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
        )
