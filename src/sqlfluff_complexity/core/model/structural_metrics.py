"""Structural metrics derived from SQLFluff parse trees (CTE deps, set ops, expressions)."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlfluff.core.parser.segments.base import BaseSegment


class StructuralScanResult(NamedTuple):
    """Aggregates from one depth-first pass over the parse tree."""

    cte_dependency_depth: int
    set_operation_count: int
    expression_depth: int


class _TarjanState(NamedTuple):
    """Mutable Tarjan traversal state grouped to keep helper signatures small."""

    index_counter: list[int]
    stack: list[str]
    indices: dict[str, int]
    lowlink: dict[str, int]
    on_stack: set[str]


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
    """Build directed edges ``dependent_alias -> referenced_alias`` among sibling CTEs.

    Reference detection is delegated to :func:`_outer_sibling_table_reference_names` (bare
    identifiers only; qualification and shadowing described there).
    """
    edges: dict[str, set[str]] = {name: set() for name in names_in_scope}
    for cte in cte_segments:
        alias = _cte_alias(cte)
        if not alias:
            continue
        body = _cte_query_body(cte)
        if body is None:
            continue
        for ref in _outer_sibling_table_reference_names(body, names_in_scope):
            if ref != alias:
                edges[alias].add(ref)
    return edges


def _tarjan_relax_edge(
    endpoints: tuple[str, str],
    state: _TarjanState,
    recurse: Callable[[str], None],
) -> None:
    """Single Tarjan edge relaxation step."""
    vertex, succ = endpoints
    if succ not in state.indices:
        recurse(succ)
        state.lowlink[vertex] = min(state.lowlink[vertex], state.lowlink[succ])
    elif succ in state.on_stack:
        state.lowlink[vertex] = min(state.lowlink[vertex], state.indices[succ])


def _tarjan_strongly_connected_components(
    nodes: set[str],
    edges: dict[str, set[str]],
) -> list[list[str]]:
    """Return Tarjan SCC decomposition (each SCC is a list of vertices)."""
    state = _TarjanState([0], [], {}, {}, set())
    sccs: list[list[str]] = []

    def strongconnect(vertex: str) -> None:
        state.indices[vertex] = state.index_counter[0]
        state.lowlink[vertex] = state.index_counter[0]
        state.index_counter[0] += 1
        state.stack.append(vertex)
        state.on_stack.add(vertex)
        for succ in edges.get(vertex, set()):
            _tarjan_relax_edge((vertex, succ), state, strongconnect)
        if state.lowlink[vertex] == state.indices[vertex]:
            sccs.append(_pop_scc(vertex, state))

    for v in nodes:
        if v not in state.indices:
            strongconnect(v)
    return sccs


def _pop_scc(root: str, state: _TarjanState) -> list[str]:
    """Pop one strongly connected component from the Tarjan stack."""
    comp: list[str] = []
    while True:
        vertex = state.stack.pop()
        state.on_stack.discard(vertex)
        comp.append(vertex)
        if vertex == root:
            return comp


def _condensation_successors(
    nodes: set[str],
    edges: dict[str, set[str]],
    vertex_to_comp: dict[str, int],
    num_components: int,
) -> list[set[int]]:
    """Build successor lists for the condensation DAG (edges between distinct SCCs)."""
    succ: list[set[int]] = [set() for _ in range(num_components)]
    for u in nodes:
        iu = vertex_to_comp[u]
        for v in edges.get(u, set()):
            iv = vertex_to_comp[v]
            if iu != iv:
                succ[iu].add(iv)
    return succ


def _longest_path_weighted_condensation(
    weights: list[int],
    succ: list[set[int]],
) -> int:
    """Longest weighted path in a DAG: weight(S) + max path following outgoing condensation edges."""
    memo: dict[int, int] = {}

    def longest_from(comp_id: int) -> int:
        if comp_id in memo:
            return memo[comp_id]
        outs = succ[comp_id]
        if not outs:
            memo[comp_id] = weights[comp_id]
            return memo[comp_id]
        memo[comp_id] = weights[comp_id] + max(longest_from(d) for d in outs)
        return memo[comp_id]

    return max((longest_from(i) for i in range(len(weights))), default=0)


def _longest_dependency_chain_depth(nodes: set[str], edges: dict[str, set[str]]) -> int:
    """Maximum dependency-chain length (node count) along dependent-to-referenced edges.

    Each edge ``u -> v`` means CTE ``u`` references sibling CTE ``v``. Without cycles this matches
    the longest path length in the dependency graph. For cycles, Tarjan SCC condensation avoids
    inflation from naive DFS (each SCC contributes its size once along any path).
    """
    if not nodes:
        return 0
    sccs = _tarjan_strongly_connected_components(nodes, edges)
    vertex_to_comp = {v: i for i, comp in enumerate(sccs) for v in comp}
    weights = [len(comp) for comp in sccs]
    succ = _condensation_successors(nodes, edges, vertex_to_comp, len(sccs))
    return _longest_path_weighted_condensation(weights, succ)


def _cte_alias(cte: BaseSegment) -> str:
    """Alias identifier for a ``common_table_expression`` segment."""
    for child in getattr(cte, "segments", ()) or ():
        if getattr(child, "type", "") == "identifier":
            return _normalize_identifier(getattr(child, "raw", "") or "")
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


def _walk_nested_with_for_outer_refs(
    with_seg: BaseSegment,
    nested_frames: list[set[str]],
    visit: Callable[[BaseSegment], None],
) -> None:
    inner = {_cte_alias(cte) for cte in direct_child_common_table_expressions(with_seg)}
    inner.discard("")
    nested_frames.append(inner)
    try:
        for child in getattr(with_seg, "segments", ()) or ():
            visit(child)
    finally:
        nested_frames.pop()


def _record_outer_sibling_table_ref_if_applicable(
    seg: BaseSegment,
    nested_frames: list[set[str]],
    outer_sibling_names: set[str],
    names: set[str],
) -> None:
    name = _simple_table_reference_name(seg)
    if name and name in outer_sibling_names and not any(name in frame for frame in nested_frames):
        names.add(name)


def _outer_sibling_table_reference_names(
    root: BaseSegment,
    outer_sibling_names: set[str],
) -> set[str]:
    """Bare ``table_reference`` names that resolve to **outer** sibling CTEs for this ``WITH``.

    Only **unqualified** single-identifier ``table_reference`` segments count; dotted names are
    skipped so ``schema.table`` is not attributed to a same-named CTE (false positives). At the
    same time, qualified references are not counted as CTE deps even when they could match a
    sibling spelling (see ``test_metrics_schema_qualified_table_not_counted_as_cte_ref``).

    An unqualified ``FROM t`` that matches a sibling alias is treated as that CTE even if ``t``
    could also be a base table at runtime—this metric is approximate by design.

    Nested ``with_compound_statement`` subtrees are walked; each contributes a set of inner CTE
    aliases (a frame). We record a name only if it is in ``outer_sibling_names`` and **no**
    nested frame on the current DFS path declares that same alias—any inner declaration shadows
    outer siblings with the same spelling (see ``test_metrics_nested_with_*``). Outer sibling refs
    inside nested CTE bodies are included when not shadowed (see
    ``test_metrics_nested_with_inner_cte_refs_outer_sibling`` and
    ``test_metrics_nested_with_outer_select_refs_outer_sibling``).
    """
    collected: set[str] = set()
    nested_frames: list[set[str]] = []

    def visit(seg: BaseSegment) -> None:
        st = getattr(seg, "type", "")
        if st == "with_compound_statement":
            _walk_nested_with_for_outer_refs(seg, nested_frames, visit)
        elif st == "table_reference":
            _record_outer_sibling_table_ref_if_applicable(
                seg, nested_frames, outer_sibling_names, collected
            )
        else:
            for child in getattr(seg, "segments", ()) or ():
                visit(child)

    visit(root)
    return collected


def _simple_table_reference_name(table_ref: BaseSegment) -> str:
    """Return a bare table name for CTE matching, or ``""`` when not a single identifier.

    Multi-identifier (schema-qualified) references return ``""`` so dependency edges do not treat
    ``catalog.orders`` as CTE ``orders`` (see ``test_metrics_schema_qualified_table_not_counted_as_cte_ref``).
    """
    parts: list[str] = []
    for child in getattr(table_ref, "segments", ()) or ():
        if getattr(child, "type", "") == "identifier":
            name = _normalize_identifier(getattr(child, "raw", "") or "")
            if name:
                parts.append(name)
    if len(parts) == 1:
        return parts[0]
    if len(parts) > 1:
        return ""
    raw = (getattr(table_ref, "raw", "") or "").strip()
    return _normalize_identifier(raw)


def _normalize_identifier(raw: str) -> str:
    """Fold unquoted identifiers only; quoted identifiers are case-sensitive."""
    name = raw.strip()
    if not name:
        return ""
    if _is_quoted_identifier(name):
        return name
    return name.lower()


def _is_quoted_identifier(name: str) -> bool:
    return (
        (name.startswith('"') and name.endswith('"'))
        or (name.startswith("`") and name.endswith("`"))
        or (name.startswith("[") and name.endswith("]"))
    )
