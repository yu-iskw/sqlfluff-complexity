"""SQLFluff segment-tree metric collection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlfluff_complexity.core.analysis import (
    ComplexityAnalysis,
    MetricContributor,
    compact_segment_raw,
    segment_position,
)
from sqlfluff_complexity.core.model.metrics import ComplexityMetrics
from sqlfluff_complexity.core.model.structural_metrics import (
    StructuralScanResult,
    _cte_alias,
    _normalize_identifier,
    merge_structural_scan,
)

if TYPE_CHECKING:
    from sqlfluff.core.parser.segments.base import BaseSegment

BOOLEAN_OPERATOR_RAW = {"AND", "OR"}

# Aggregate ``function`` segments whose ``function_name`` matches (no ``over_clause`` child).
_AGGREGATE_FUNCTION_NAMES = frozenset(
    {
        "APPROX_COUNT_DISTINCT",
        "ARRAY_AGG",
        "AVG",
        "COUNT",
        "COUNTIF",
        "GROUP_CONCAT",
        "LISTAGG",
        "MAX",
        "MIN",
        "STDDEV",
        "STDDEV_POP",
        "STDDEV_SAMP",
        "STRING_AGG",
        "SUM",
        "VAR_POP",
        "VAR_SAMP",
        "VARIANCE",
    },
)

# Direct children of ``groupby_clause`` that count as grouping keys (skip punctuation/keywords).
_GROUPING_ELEMENT_TYPES = frozenset(
    {
        "boolean_literal",
        "bracketed",
        "case_expression",
        "column_reference",
        "expression",
        "function",
        "literal",
        "null_literal",
        "numeric_literal",
        "parameter",
        "quoted_identifier",
        "wildcard_expression",
    },
)

_HAVING_OR_QUALIFY_WEIGHT = 3


def _gather_all_cte_aliases(root: BaseSegment) -> frozenset[str]:
    """Collect every CTE alias in the tree (used to skip bare ``FROM cte`` source counts)."""
    names: set[str] = set()
    stack: list[BaseSegment] = [root]
    while stack:
        seg = stack.pop()
        if getattr(seg, "type", "") == "common_table_expression":
            alias = _cte_alias(seg)
            if alias:
                names.add(alias)
        stack.extend(getattr(seg, "segments", ()) or ())
    return frozenset(names)


def _relation_key_from_table_reference(table_ref: BaseSegment) -> str:
    """Normalized relation key (``schema.table`` or single name) for distinct source counting."""
    parts: list[str] = []
    for child in getattr(table_ref, "segments", ()) or ():
        if getattr(child, "type", "") == "identifier":
            name = _normalize_identifier(getattr(child, "raw", "") or "")
            if name:
                parts.append(name)
    if parts:
        return ".".join(parts)
    raw = (getattr(table_ref, "raw", "") or "").strip()
    return _normalize_identifier(raw)


def _function_name_upper(function_segment: BaseSegment) -> str:
    for child in getattr(function_segment, "segments", ()) or ():
        if getattr(child, "type", "") == "function_name":
            return (getattr(child, "raw_upper", "") or "").strip()
    return ""


def _has_descendant_type(segment: BaseSegment, segment_type: str) -> bool:
    """Depth-first search for ``segment_type`` under ``segment`` (separate pass from ``walk``).

    Used only for derived-table detection; typical SQL keeps this cheap. If profiling shows
    hotspots, fold detection into the main walk instead of re-traversing subtrees.
    """
    stack = list(getattr(segment, "segments", ()) or ())
    while stack:
        current = stack.pop()
        if getattr(current, "type", "") == segment_type:
            return True
        stack.extend(getattr(current, "segments", ()) or ())
    return False


def _direct_child_of_type(segment: BaseSegment, segment_type: str) -> BaseSegment | None:
    for child in getattr(segment, "segments", ()) or ():
        if getattr(child, "type", "") == segment_type:
            return child
    return None


class _MetricCounter:
    """Stateful collector for one SQLFluff segment tree walk."""

    def __init__(self, *, cte_aliases: frozenset[str]) -> None:
        self._cte_aliases = cte_aliases
        self.ctes = 0
        self.joins = 0
        self.subqueries = 0
        self.subquery_depth = 0
        self.case_expressions = 0
        self.boolean_operators = 0
        self.window_functions = 0
        self.derived_tables = 0
        self._source_relation_names: set[str] = set()
        self.select_targets = 0
        self.aggregation_complexity = 0
        self._structural = StructuralScanResult(0, 0, 0)
        self.contributors: list[MetricContributor] = []

    @property
    def source_relations(self) -> int:
        return len(self._source_relation_names)

    @property
    def cte_dependency_depth(self) -> int:
        return self._structural.cte_dependency_depth

    @property
    def set_operation_count(self) -> int:
        return self._structural.set_operation_count

    @property
    def expression_depth(self) -> int:
        return self._structural.expression_depth

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

    def _walk_children(
        self,
        segment: BaseSegment,
        active_selects: int,
        nested_depth: int,
        case_depth: int,
        under_cte_scope: bool,
    ) -> None:
        for child in getattr(segment, "segments", ()) or ():
            self.walk(
                child,
                active_selects=active_selects,
                nested_depth=nested_depth,
                case_depth=case_depth,
                under_cte_scope=under_cte_scope,
            )

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

    def _is_aggregate_function_without_over(self, segment: BaseSegment) -> bool:
        if getattr(segment, "type", "") != "function":
            return False
        if _has_descendant_type(segment, "over_clause"):
            return False
        name = _function_name_upper(segment)
        return name in _AGGREGATE_FUNCTION_NAMES

    def _record_source_relation(self, segment: BaseSegment, under_cte_scope: bool) -> None:
        """Count one distinct physical relation from ``from_expression_element``."""
        if getattr(segment, "type", "") != "from_expression_element":
            return
        if self._is_derived_table(segment, under_cte_scope):
            return
        table_expression = _direct_child_of_type(segment, "table_expression")
        if table_expression is None:
            return
        table_ref = _direct_child_of_type(table_expression, "table_reference")
        if table_ref is None:
            return
        key = _relation_key_from_table_reference(table_ref)
        if not key:
            return
        parts = key.split(".")
        if len(parts) == 1 and parts[0] in self._cte_aliases:
            return
        if key not in self._source_relation_names:
            self._source_relation_names.add(key)
            self._add_contributor("source_relations", table_ref, reason="source relation")

    def _update_select_targets(self, segment: BaseSegment) -> None:
        if getattr(segment, "type", "") != "select_clause":
            return
        count = sum(
            1
            for child in getattr(segment, "segments", ()) or ()
            if getattr(child, "type", "") == "select_clause_element"
        )
        if count > self.select_targets:
            self.select_targets = count
            self._add_contributor("select_targets", segment, reason="select list width")

    def _count_groupby_elements(self, segment: BaseSegment) -> None:
        if getattr(segment, "type", "") != "groupby_clause":
            return
        n = sum(
            1
            for child in getattr(segment, "segments", ()) or ()
            if getattr(child, "type", "") in _GROUPING_ELEMENT_TYPES
        )
        if n:
            self.aggregation_complexity += n
            self._add_contributor("aggregation_complexity", segment, reason="group by expressions")

    def _count_having_or_qualify(self, segment: BaseSegment) -> None:
        st = getattr(segment, "type", "")
        if st not in {"having_clause", "qualify_clause"}:
            return
        self.aggregation_complexity += _HAVING_OR_QUALIFY_WEIGHT
        reason = "having clause" if st == "having_clause" else "qualify clause"
        self._add_contributor("aggregation_complexity", segment, reason=reason)

    def _count_aggregate_function(self, segment: BaseSegment) -> None:
        if not self._is_aggregate_function_without_over(segment):
            return
        self.aggregation_complexity += 1
        self._add_contributor("aggregation_complexity", segment, reason="aggregate function")

    def _is_boolean_operator(self, segment: BaseSegment) -> bool:
        return (
            getattr(segment, "type", "") == "binary_operator"
            and getattr(segment, "raw_upper", "") in BOOLEAN_OPERATOR_RAW
        )

    def _is_derived_table(self, segment: BaseSegment, under_cte_scope: bool) -> bool:
        if under_cte_scope or getattr(segment, "type", "") != "from_expression_element":
            return False
        table_expression = _direct_child_of_type(segment, "table_expression")
        if table_expression is None:
            return False
        bracketed = _direct_child_of_type(table_expression, "bracketed")
        return bracketed is not None and _has_descendant_type(bracketed, "select_statement")

    def _count_segment(
        self,
        segment: BaseSegment,
        segment_type: str,
        under_cte_scope: bool,
    ) -> None:
        if segment_type == "from_expression_element":
            self._record_source_relation(segment, under_cte_scope)
            if self._is_derived_table(segment, under_cte_scope):
                self.derived_tables += 1
                self._add_contributor("derived_tables", segment, reason="derived table")
        elif segment_type == "join_clause":
            self.joins += 1
            self._add_contributor("joins", segment, reason="join clause")
        elif segment_type == "case_expression":
            self.case_expressions += 1
            self._add_contributor("case_expressions", segment, reason="case expression")
        elif segment_type == "over_clause":
            self.window_functions += 1
            self._add_contributor("window_functions", segment, reason="window over clause")
        elif segment_type == "select_clause":
            self._update_select_targets(segment)
        elif segment_type == "groupby_clause":
            self._count_groupby_elements(segment)
        elif segment_type in {"having_clause", "qualify_clause"}:
            self._count_having_or_qualify(segment)
        elif segment_type == "function":
            self._count_aggregate_function(segment)
        elif self._is_boolean_operator(segment):
            self.boolean_operators += 1
            self._add_contributor(
                "boolean_operators",
                segment,
                reason="boolean and/or operator",
            )

    def _add_structural_contributor(
        self,
        segment: BaseSegment,
        segment_type: str,
        case_depth: int,
    ) -> None:
        if segment_type == "set_operator":
            self._add_contributor("set_operation_count", segment, reason="set operator")
        elif segment_type == "case_expression" and case_depth > 0:
            self._add_contributor("expression_depth", segment, reason="nested case expression")

    def walk(
        self,
        segment: BaseSegment,
        active_selects: int,
        nested_depth: int,
        case_depth: int,
        under_cte_scope: bool,
    ) -> None:
        """Walk a segment and its children."""
        self._structural = merge_structural_scan(self._structural, segment, case_depth)
        segment_type = getattr(segment, "type", "")

        if segment_type == "common_table_expression":
            # Count the CTE here, then walk only its subtree with under_cte_scope so
            # derived_tables skips inline FROM (SELECT ...) inside the CTE body.
            self.ctes += 1
            self._add_contributor("ctes", segment, reason="common table expression")
            self._walk_children(
                segment,
                active_selects=0,
                nested_depth=0,
                case_depth=case_depth,
                under_cte_scope=True,
            )
            return

        next_active_selects, next_nested_depth = self._select_depths(
            segment,
            segment_type,
            active_selects,
            nested_depth,
        )
        self._count_segment(segment, segment_type, under_cte_scope)
        self._add_structural_contributor(segment, segment_type, case_depth)

        child_case_depth = case_depth + 1 if segment_type == "case_expression" else case_depth
        self._walk_children(
            segment,
            active_selects=next_active_selects,
            nested_depth=next_nested_depth,
            case_depth=child_case_depth,
            under_cte_scope=under_cte_scope,
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
            derived_tables=self.derived_tables,
            source_relations=self.source_relations,
            select_targets=self.select_targets,
            aggregation_complexity=self.aggregation_complexity,
        )


def analyze_segment_tree(root: BaseSegment) -> ComplexityAnalysis:
    """Collect metrics and per-segment contributors from a SQLFluff segment tree."""
    cte_aliases = _gather_all_cte_aliases(root)
    counter = _MetricCounter(cte_aliases=cte_aliases)
    counter.walk(
        root,
        active_selects=0,
        nested_depth=0,
        case_depth=0,
        under_cte_scope=False,
    )
    return ComplexityAnalysis(
        root=root,
        metrics=counter.to_metrics(),
        contributors=tuple(counter.contributors),
    )


def collect_metrics(root: BaseSegment) -> ComplexityMetrics:
    """Collect complexity metrics from a SQLFluff segment tree."""
    return analyze_segment_tree(root).metrics


def _parent_segment(segment: BaseSegment | None) -> BaseSegment | None:
    if segment is None:
        return None
    parent = segment.get_parent()
    if isinstance(parent, tuple):
        return parent[0]
    return parent


def _segment_has_ancestor_of_type(segment: BaseSegment, segment_type: str) -> bool:
    """True when ``segment`` is of ``segment_type`` and an ancestor shares that type.

    Parent walks are capped at 256 hops to avoid unbounded work if parent metadata is
    cyclic or unexpectedly deep.
    """
    if getattr(segment, "type", "") != segment_type:
        return False

    current: BaseSegment | None = segment
    for _ in range(256):
        parent = _parent_segment(current)
        if parent is None:
            break
        if getattr(parent, "type", "") == segment_type:
            return True
        current = parent
    return False


def is_nested_select_statement(segment: BaseSegment) -> bool:
    """Return True when this select_statement sits under another select_statement.

    Used to avoid duplicate rule hits on nested selects. When parent metadata
    is unavailable, returns False so rules keep prior behavior.
    """
    return _segment_has_ancestor_of_type(segment, "select_statement")
