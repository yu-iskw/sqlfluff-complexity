"""Tests for path-specific complexity policy overrides."""

from __future__ import annotations

import pytest

from sqlfluff_complexity.core.config.policy import ComplexityPolicy, resolve_policy

EXPECTED_STAGING_MAX_COMPLEXITY_SCORE = 40
EXPECTED_TIE_MAX_JOINS = 2
EXPECTED_NORMALIZED_MAX_CTES = 2


def test_resolve_policy_uses_most_specific_matching_override() -> None:
    """The most specific glob should win when multiple path overrides match."""
    policy = resolve_policy(
        ComplexityPolicy(max_joins=8, max_complexity_score=60),
        """
        models/*.sql:max_joins=3
        models/staging/*.sql:max_joins=1,max_complexity_score=40
        """,
        "models/staging/orders.sql",
    )

    assert policy.max_joins == 1
    assert policy.max_complexity_score == EXPECTED_STAGING_MAX_COMPLEXITY_SCORE


def test_resolve_policy_uses_later_override_for_specificity_tie() -> None:
    """Later matches should win when matching globs have equal specificity."""
    policy = resolve_policy(
        ComplexityPolicy(max_joins=8),
        """
        models/*.sql:max_joins=3
        models/*.sql:max_joins=2
        """,
        "models/orders.sql",
    )

    assert policy.max_joins == EXPECTED_TIE_MAX_JOINS


def test_resolve_policy_normalizes_posix_paths() -> None:
    """Backslash paths should match the same policy as POSIX paths."""
    policy = resolve_policy(
        ComplexityPolicy(max_ctes=8),
        "models/staging/*.sql:max_ctes=2",
        r"models\staging\orders.sql",
    )

    assert policy.max_ctes == EXPECTED_NORMALIZED_MAX_CTES


@pytest.mark.parametrize(
    "raw_overrides",
    [
        "models/*.sql:unknown=1",
        "models/*.sql:max_joins=not-an-int",
        "models/*.sql:max_joins=-1",
        "models/*.sql:mode=disabled",
        "models/*.sql max_joins=1",
    ],
)
def test_resolve_policy_rejects_invalid_overrides(raw_overrides: str) -> None:
    """Invalid path override config should fail clearly instead of being ignored."""
    with pytest.raises(ValueError, match=r"override|Unknown|integer|non-negative|mode"):
        resolve_policy(ComplexityPolicy(), raw_overrides, "models/orders.sql")
