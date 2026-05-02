"""Structural metrics derived from SQLFluff parse trees (CTE deps, set ops, expressions)."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlfluff.core.parser.segments.base import BaseSegment


class StructuralScanResult(NamedTuple):
    """Aggregates from one depth-first pass over the parse tree."""

    cte_dependency_depth: int
    set_operation_count: int
    expression_depth: int


def compute_structural_metrics(root: BaseSegment) -> StructuralScanResult:
    """Global max CTE chain depth, set-operator count, and max ``case_expression`` nesting in one walk."""
    set_ops = 0
    max_case = 0
    max_cte_dep = 0
    stack: list[tuple[BaseSegment, int]] = [(root, 0)]
    while stack:
        seg, case_depth = stack.pop()
        st = getattr(seg, "type", "")
        if st == "set_operator":
            set_ops += 1
        elif st == "case_expression":
            max_case = max(max_case, case_depth + 1)
        elif st == "with_compound_statement":
            max_cte_dep = max(max_cte_dep, _cte_dependency_depth_for_with(seg))
        child_case_depth = case_depth + 1 if st == "case_expression" else case_depth
        children = getattr(seg, "segments", ()) or ()
        stack.extend((ch, child_case_depth) for ch in reversed(children))
    return StructuralScanResult(max_cte_dep, set_ops, max_case)


def _cte_dependency_depth_for_with(with_root: BaseSegment) -> int:
    """Compute longest CTE dependency chain for one WITH compound statement."""
    cte_segments = list(direct_child_common_table_expressions(with_root))
    if not cte_segments:
        return 0

    names_in_scope = {_cte_alias(cte) for cte in cte_segments}
    names_in_scope.discard("")

    edges = _cte_reference_edges(cte_segments, names_in_scope)

    return _longest_dependency_chain_depth(names_in_scope, edges)


def cte_dependency_depth_for_with_clause(with_root: BaseSegment) -> int:
    """Longest CTE dependency chain among **direct** CTEs of this ``with_compound_statement`` only.

    Nested ``WITH`` clauses inside a CTE body are separate scopes; use this for CPX_C107 so the
    outer clause is not judged by the inner clause's depth (see aggregate ``ComplexityMetrics``
    ``cte_dependency_depth``, which maxes across all ``WITH`` blocks in the tree).
    """
    return _cte_dependency_depth_for_with(with_root)


def direct_child_common_table_expressions(with_root: BaseSegment) -> tuple[BaseSegment, ...]:
    """Top-level CTE segments directly under a ``with_compound_statement``."""
    return tuple(
        seg
        for seg in getattr(with_root, "segments", ()) or ()
        if getattr(seg, "type", "") == "common_table_expression"
    )


def _cte_reference_edges(
    cte_segments: list[BaseSegment],
    names_in_scope: set[str],
) -> dict[str, set[str]]:
    edges: dict[str, set[str]] = {name: set() for name in names_in_scope}
    for cte in cte_segments:
        alias = _cte_alias(cte)
        if not alias:
            continue
        body = _cte_query_body(cte)
        if body is None:
            continue
        for ref in _table_reference_names(body):
            if ref in names_in_scope and ref != alias:
                edges[alias].add(ref)
    return edges


def _longest_dependency_chain_depth(nodes: set[str], edges: dict[str, set[str]]) -> int:
    """Return max nodes-on-path depth following edges from referenced CTE to dependent CTE."""
    memo: dict[str, int] = {}
    visited_stack: set[str] = set()

    def longest_from(start: str) -> int:
        if start in memo:
            return memo[start]
        if start in visited_stack:
            return 1
        visited_stack.add(start)
        upstream_refs = edges.get(start, set())
        depth = 1 if not upstream_refs else 1 + max(longest_from(p) for p in upstream_refs)
        visited_stack.remove(start)
        memo[start] = depth
        return depth

    return max((longest_from(n) for n in nodes), default=0)


def _cte_alias(cte: BaseSegment) -> str:
    """Alias identifier for a ``common_table_expression`` segment."""
    for child in getattr(cte, "segments", ()) or ():
        if getattr(child, "type", "") == "identifier":
            raw = (getattr(child, "raw", "") or "").strip()
            return raw.lower()
    return ""


def _cte_query_body(cte: BaseSegment) -> BaseSegment | None:
    """Return the bracketed SELECT body of a CTE (after ``AS``), not a column list bracket."""
    children = tuple(getattr(cte, "segments", ()) or ())
    seen_as = False
    for child in children:
        if (
            getattr(child, "type", "") == "keyword"
            and getattr(child, "raw_upper", "").strip() == "AS"
        ):
            seen_as = True
            continue
        if seen_as and getattr(child, "type", "") == "bracketed":
            return child

    bracketeds = [c for c in children if getattr(c, "type", "") == "bracketed"]
    return bracketeds[-1] if bracketeds else None


def _table_reference_names(root: BaseSegment) -> set[str]:
    """Collect normalized bare names from ``table_reference`` segments (best-effort)."""
    names: set[str] = set()
    for seg in _iter_segments(root, "table_reference"):
        name = _simple_table_reference_name(seg)
        if name:
            names.add(name)
    return names


def _simple_table_reference_name(table_ref: BaseSegment) -> str:
    """Bare table name for dependency matching; skip schema-qualified references."""
    parts: list[str] = []
    for child in getattr(table_ref, "segments", ()) or ():
        if getattr(child, "type", "") == "identifier":
            raw = (getattr(child, "raw", "") or "").strip()
            if raw:
                parts.append(raw.lower())
    if len(parts) == 1:
        return parts[0]
    if len(parts) > 1:
        return ""
    raw = (getattr(table_ref, "raw", "") or "").strip()
    return raw.lower() if raw else ""


def _iter_segments(root: BaseSegment, segment_type: str) -> Iterator[BaseSegment]:
    """Depth-first iteration yielding segments of ``segment_type``."""
    stack = [root]
    while stack:
        seg = stack.pop()
        if getattr(seg, "type", "") == segment_type:
            yield seg
        children = getattr(seg, "segments", ()) or ()
        stack.extend(reversed(children))
