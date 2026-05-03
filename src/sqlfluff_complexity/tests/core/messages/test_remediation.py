"""Tests for remediation mapping coverage."""

from __future__ import annotations

import pytest

from sqlfluff_complexity.core.messages.remediation import (
    CPX_RULE_IDS,
    remediation_for_rule,
)


@pytest.mark.parametrize("rule_id", CPX_RULE_IDS)
def test_every_cpx_rule_has_remediation(rule_id: str) -> None:
    """Each CPX rule must have non-empty remediation text."""
    text = remediation_for_rule(rule_id)
    assert len(text.strip()) >= 20


def test_unknown_rule_raises() -> None:
    """Unknown rule ids must raise KeyError."""
    with pytest.raises(KeyError, match="Unknown CPX rule_id"):
        remediation_for_rule("CPX_C999")
