"""Centralized remediation text for CPX rules."""

from __future__ import annotations

REMEDIATIONS: dict[str, str] = {
    "CPX_C101": (
        "Consider splitting long CTE chains into clearer transformation phases or upstream models."
    ),
    "CPX_C102": (
        "Consider reducing join fan-in, moving enrichment upstream, or validating whether all joined "
        "relations are needed."
    ),
    "CPX_C103": (
        "Consider replacing deeply nested subqueries with named CTEs or intermediate transformations."
    ),
    "CPX_C104": (
        "Consider moving dense CASE business logic into reference tables, seed data, or upstream "
        "transformations."
    ),
    "CPX_C105": (
        "Consider decomposing complex predicates into named boolean flags or smaller filtering "
        "steps."
    ),
    "CPX_C106": (
        "Consider splitting analytic/window logic into clearer phases or deduplicating repeated "
        "window specifications."
    ),
    "CPX_C107": (
        "Consider splitting the query into simpler intermediate models or reducing chained CTEs."
    ),
    "CPX_C108": (
        "Consider flattening nested CASE logic into smaller expressions, mapping tables, or "
        "upstream classification steps."
    ),
    "CPX_C109": (
        "Consider replacing stacked UNION/INTERSECT/EXCEPT with a single query, staging models, or "
        "a unioned intermediate model."
    ),
    "CPX_C201": (
        "Reduce the largest contributing metric first; inspect the metric breakdown and top "
        "contributors."
    ),
}

CPX_RULE_IDS: tuple[str, ...] = tuple(sorted(REMEDIATIONS))


def remediation_for_rule(rule_id: str) -> str:
    """Return short remediation guidance for a CPX rule id."""
    if rule_id not in CPX_RULE_IDS:
        message = f"Unknown CPX rule_id: {rule_id!r}"
        raise KeyError(message)
    return REMEDIATIONS[rule_id]
