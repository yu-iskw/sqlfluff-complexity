"""Tests for package metadata helpers."""

from __future__ import annotations

import sqlfluff_complexity


def test_version_is_non_empty_string() -> None:
    """Import must expose a version string (installed or fallback)."""
    assert isinstance(sqlfluff_complexity.__version__, str)
    assert len(sqlfluff_complexity.__version__) >= 1
