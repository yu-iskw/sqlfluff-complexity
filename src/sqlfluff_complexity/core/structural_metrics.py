"""Structural metrics derived from SQLFluff parse trees (CTE deps, set ops, expressions)."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from sqlfluff.core.parser.segments.base import BaseSegment


class StructuralScanResult(NamedTuple):
    """Aggregates from one depth-first pass over the parse tree."""

    cte_dependency_depth: int
    set_operation_count: int
    expression_depth: int


# Weak keys: entries drop when parse-tree segments are GC'd. Per-root memo avoids repeated
# full scans when public helpers call compute_structural_metrics on the same tree; per-WITH
# memo avoids duplicating CTE graph work between metric collection and CPX_C107.
_STRUCTURAL_BY_ROOT: weakref.WeakKeyDictionary[BaseSegment, StructuralScanResult] = (
    weakref.WeakKeyDictionary()
)
_CTE_DEPTH_BY_WITH: weakref.WeakKeyDictionary[BaseSegment, int] = weakref.WeakKeyDictionary()


def clear_structural_caches() -> None:
    """Clear memoization for testing isolation (weak-key caches only)."""

    _STRUCTURAL_BY_ROOT.clear()
    _CTE_DEPTH_BY_WITH.clear()


def merge_structural_scan(
    acc: StructuralScanResult,
    segment: BaseSegment,
    case_depth: int,
) -> StructuralScanResult:
    """Fold one segment into structural counters (mirrors :func:`compute_structural_metrics`)."""
    st = getattr(segment, "type", "")
    set_ops = acc.set_operation_count + (1 if st == "set_operator" else 0)
    expr_dep = acc.expression_depth
    if st == "case_expression":
        expr_dep = max(expr_dep, case_depth + 1)
    cte_dep = acc.cte_dependency_depth
    if st == "with_compound_statement":
        cte_dep = max(cte_dep, _cte_dependency_depth_for_with(segment))
    return StructuralScanResult(cte_dep, set_ops, expr_dep)


def compute_structural_metrics(root: BaseSegment) -> StructuralScanResult:
    """Global max CTE chain depth, set-operator count, and max ``case_expression`` nesting in one walk."""
    cached = _STRUCTURAL_BY_ROOT.get(root)
    if cached is not None:
        return cached
    acc = StructuralScanResult(0, 0, 0)
    stack: list[tuple[BaseSegment, int]] = [(root, 0)]
    while stack:
        seg, case_depth = stack.pop()
        acc = merge_structural_scan(acc, seg, case_depth)
        st = getattr(seg, "type", "")
        child_case_depth = case_depth + 1 if st == "case_expression" else case_depth
        children = getattr(seg, "segments", ()) or ()
        stack.extend((ch, child_case_depth) for ch in reversed(children))
    _STRUCTURAL_BY_ROOT[root] = acc
    return acc


def max_cte_dependency_depth(root: BaseSegment) -> int:
    """Longest CTE reference chain within each ``with_compound_statement``; return the global max."""
    return compute_structural_metrics(root).cte_dependency_depth


def count_set_operations(root: BaseSegment) -> int:
    """Count ``set_operator`` segments (UNION / INTERSECT / EXCEPT arms)."""
    return compute_structural_metrics(root).set_operation_count


def max_case_expression_nesting_depth(root: BaseSegment) -> int:
    """Maximum nesting depth of ``case_expression`` segments inside other case expressions."""
    return compute_structural_metrics(root).expression_depth


def _cte_dependency_depth_for_with(with_root: BaseSegment) -> int:
    """Compute longest CTE dependency chain for one WITH compound statement."""
    cached = _CTE_DEPTH_BY_WITH.get(with_root)
    if cached is not None:
        return cached
    cte_segments = list(direct_child_common_table_expressions(with_root))
    if not cte_segments:
        _CTE_DEPTH_BY_WITH[with_root] = 0
        return 0

    names_in_scope = {_cte_alias(cte) for cte in cte_segments}
    names_in_scope.discard("")

    edges = _cte_reference_edges(cte_segments, names_in_scope)

    depth = _longest_dependency_chain_depth(names_in_scope, edges)
    _CTE_DEPTH_BY_WITH[with_root] = depth
    return depth


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
    """Collect normalized bare names from ``table_reference`` segments (best-effort).

    Nested ``WITH`` blocks inside a CTE body are separate scopes; we do not descend into
    ``with_compound_statement`` subtrees so inner-local references are not attributed as
    edges between **this** WITH clause's CTEs (PR review: nested WITH scope).
    """
    names: set[str] = set()
    stack: list[BaseSegment] = [root]
    while stack:
        seg = stack.pop()
        st = getattr(seg, "type", "")
        if st == "with_compound_statement":
            continue
        if st == "table_reference":
            name = _simple_table_reference_name(seg)
            if name:
                names.add(name)
            continue
        children = getattr(seg, "segments", ()) or ()
        stack.extend(reversed(children))
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
