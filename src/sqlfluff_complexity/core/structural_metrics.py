"""Structural metrics derived from SQLFluff parse trees (CTE deps, set ops, expressions)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlfluff.core.parser.segments.base import BaseSegment


def max_cte_dependency_depth(root: BaseSegment) -> int:
    """Longest CTE reference chain within each ``with_compound_statement``; return the global max."""
    best = 0
    for with_root in _iter_segments(root, "with_compound_statement"):
        best = max(best, _cte_dependency_depth_for_with(with_root))
    return best


def count_set_operations(root: BaseSegment) -> int:
    """Count ``set_operator`` segments (UNION / INTERSECT / EXCEPT arms)."""
    return sum(1 for _ in _iter_segments(root, "set_operator"))


def max_case_expression_nesting_depth(root: BaseSegment) -> int:
    """Maximum nesting depth of ``case_expression`` segments inside other case expressions."""
    best = 0

    def walk(seg: BaseSegment, case_depth: int) -> None:
        nonlocal best
        st = getattr(seg, "type", "")
        next_depth = case_depth + 1 if st == "case_expression" else case_depth
        if st == "case_expression":
            best = max(best, next_depth)
        for child in getattr(seg, "segments", ()) or ():
            walk(child, next_depth)

    walk(root, 0)
    return best


def _cte_dependency_depth_for_with(with_root: BaseSegment) -> int:
    """Compute longest CTE dependency chain for one WITH compound statement."""
    cte_segments = _direct_child_ctes(with_root)
    if not cte_segments:
        return 0

    names_in_scope = {_cte_alias(cte) for cte in cte_segments}
    names_in_scope.discard("")

    edges = _cte_reference_edges(cte_segments, names_in_scope)

    return _longest_dependency_chain_depth(names_in_scope, edges)


def _direct_child_ctes(with_root: BaseSegment) -> list[BaseSegment]:
    """Only top-level CTEs under the WITH (not nested inside brackets)."""
    return [
        seg
        for seg in _direct_children(with_root)
        if getattr(seg, "type", "") == "common_table_expression"
    ]


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
        preds = edges.get(start, set())
        depth = 1 if not preds else 1 + max(longest_from(p) for p in preds)
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
    """Return the bracketed SELECT body of a CTE, skipping the alias."""
    for child in getattr(cte, "segments", ()) or ():
        if getattr(child, "type", "") == "bracketed":
            return child
    return None


def _table_reference_names(root: BaseSegment) -> set[str]:
    """Collect normalized bare names from ``table_reference`` segments (best-effort)."""
    names: set[str] = set()
    for seg in _iter_segments(root, "table_reference"):
        name = _simple_table_reference_name(seg)
        if name:
            names.add(name)
    return names


def _simple_table_reference_name(table_ref: BaseSegment) -> str:
    """Single-table reference only; dotted names take the last segment; skip if ambiguous."""
    parts: list[str] = []
    for child in getattr(table_ref, "segments", ()) or ():
        if getattr(child, "type", "") == "identifier":
            raw = (getattr(child, "raw", "") or "").strip()
            if raw:
                parts.append(raw.lower())
    if len(parts) == 1:
        return parts[0]
    if len(parts) > 1:
        return parts[-1]
    raw = (getattr(table_ref, "raw", "") or "").strip()
    return raw.lower() if raw else ""


def _direct_children(segment: BaseSegment) -> tuple[BaseSegment, ...]:
    """Children segments tuple."""
    return tuple(getattr(segment, "segments", ()) or ())


def _iter_segments(root: BaseSegment, segment_type: str) -> Iterator[BaseSegment]:
    """Depth-first iteration yielding segments of ``segment_type``."""
    stack = [root]
    while stack:
        seg = stack.pop()
        if getattr(seg, "type", "") == segment_type:
            yield seg
        children = getattr(seg, "segments", ()) or ()
        stack.extend(reversed(children))
