"""CPX_C107 shared violation message builder."""

from __future__ import annotations

from sqlfluff_complexity.core.messages.c107_messages import build_c107_violation_message


def test_build_c107_violation_message_preserves_lint_wording() -> None:
    message = build_c107_violation_message(actual=4, limit=3)
    assert "CPX_C107: CTE dependency depth is 4" in message
    assert "max_cte_dependency_depth=3" in message
