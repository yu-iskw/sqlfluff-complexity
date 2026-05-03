"""Unit tests for CPX rule config parsing shared by lint and report."""

from __future__ import annotations

from sqlfluff_complexity.core.config.cpx_config import truthy_config_string


def test_truthy_config_string_common_values() -> None:
    """Truthiness matches SQLFluff CPX conventions."""
    assert truthy_config_string(True) is True
    assert truthy_config_string("true") is True
    assert truthy_config_string(" YES ") is True
    assert truthy_config_string("no") is False
    assert truthy_config_string("") is False
