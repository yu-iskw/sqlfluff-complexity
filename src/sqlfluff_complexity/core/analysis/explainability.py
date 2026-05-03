"""Pure helpers for explaining aggregate complexity scores."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from sqlfluff_complexity.core.model.metrics import ComplexityMetrics

# Keys that participate in weighted aggregate scoring (order not used for sorting).
_SCORE_METRIC_KEYS: tuple[str, ...] = (
    "ctes",
    "joins",
    "subquery_depth",
    "case_expressions",
    "boolean_operators",
    "window_functions",
    "cte_dependency_depth",
    "set_operation_count",
    "expression_depth",
)

_REFACTORING_PHRASES: dict[str, str] = {
    "joins": "splitting high-fan-in joins",
    "ctes": "breaking long CTE chains",
    "subquery_depth": "flattening nested subqueries",
    "case_expressions": "moving dense CASE logic into upstream models or lookup tables",
    "boolean_operators": "simplifying dense predicates",
    "window_functions": "separating dense window calculations",
    "cte_dependency_depth": "reducing chained CTE dependencies",
    "set_operation_count": "simplifying stacked set operations",
    "expression_depth": "flattening nested CASE expressions",
}


def ranked_weighted_contributions(
    metrics: ComplexityMetrics,
    weights: Mapping[str, int],
) -> list[tuple[str, int]]:
    """Return (metric_name, contribution) pairs sorted for explainability.

    Ignores metrics with zero raw value or zero weight. Sorts by descending
    contribution, then ascending metric name for deterministic tie-breaks.
    """
    pairs: list[tuple[str, int]] = []
    for key in _SCORE_METRIC_KEYS:
        raw = int(getattr(metrics, key))
        weight = int(weights.get(key, 0))
        if raw == 0 or weight == 0:
            continue
        pairs.append((key, raw * weight))

    pairs.sort(key=lambda item: (-item[1], item[0]))
    return pairs


def explain_score_contributors(
    metrics: ComplexityMetrics,
    weights: Mapping[str, int],
    *,
    max_items: int = 3,
) -> str:
    """Format top weighted contributors as a compact ``k=v, ...`` string."""
    ranked = ranked_weighted_contributions(metrics, weights)
    if max_items < 1:
        return ""
    top = ranked[:max_items]
    return ", ".join(f"{name}={value}" for name, value in top)


def refactoring_hint_for_contributors(contributor_keys: Sequence[str]) -> str:
    """Return a short refactoring hint driven by the top contributor metric keys."""
    phrases = [_REFACTORING_PHRASES[k] for k in contributor_keys if k in _REFACTORING_PHRASES]
    suffix = " into smaller intermediate models."
    pair_len = 2

    if not phrases:
        return "Consider breaking the statement into smaller intermediate models."

    if len(phrases) == 1:
        return f"Consider {phrases[0]}{suffix}"

    if len(phrases) == pair_len:
        middle = f"{phrases[0]} or {phrases[1]}"
    else:
        joined = ", ".join(phrases[:-1])
        middle = f"{joined}, or {phrases[-1]}"
    return f"Consider {middle}{suffix}"
