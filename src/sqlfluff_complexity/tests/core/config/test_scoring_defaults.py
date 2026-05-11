"""Tests for keeping aggregate scoring defaults aligned."""

from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path

from sqlfluff_complexity.core.config.presets import WEIGHT_JSON
from sqlfluff_complexity.core.config.scoring import DEFAULT_WEIGHTS, parse_weights


def test_default_weight_surfaces_stay_aligned() -> None:
    """Runtime, preset, and packaged config weights should not drift."""
    plugin_config = Path("src/sqlfluff_complexity/plugin_default_config.cfg")
    parser = ConfigParser()
    parser.read(plugin_config)

    packaged_weights = parser["sqlfluff:rules:CPX_C201"]["complexity_weights"]

    assert parse_weights(packaged_weights) == DEFAULT_WEIGHTS
    assert parse_weights(WEIGHT_JSON) == DEFAULT_WEIGHTS
    assert parse_weights("{}") == DEFAULT_WEIGHTS
