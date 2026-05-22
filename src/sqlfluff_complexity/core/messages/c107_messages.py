"""Shared CPX_C107 CTE dependency depth violation messages for lint."""

from __future__ import annotations

from sqlfluff_complexity.core.messages.remediation import remediation_for_rule


def build_c107_violation_message(*, actual: int, limit: int) -> str:
    """Build the CPX_C107 lint description (per-``with_compound_statement`` scope)."""
    remediation = remediation_for_rule("CPX_C107")
    return f"CPX_C107: CTE dependency depth is {actual}, exceeding max_cte_dependency_depth={limit}. {remediation}"
