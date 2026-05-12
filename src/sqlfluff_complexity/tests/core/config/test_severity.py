"""Unit tests for severity policy parsing and resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlfluff.core import FluffConfig

from sqlfluff_complexity.core.config.severity import (
    RuleSeverityPolicy,
    SeverityBand,
    parse_default_severity,
    parse_severity_bands,
    resolve_severity,
    rule_severity_policy_from_config,
    severity_to_level,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_resolve_severity_prefers_highest_matching_band() -> None:
    policy = RuleSeverityPolicy(
        rule_code="CPX_C102",
        default_severity="info",
        bands=(SeverityBand(min_value=5, severity="warning"), SeverityBand(min_value=9, severity="error")),
    )
    assert resolve_severity(policy, 4) == "info"
    assert resolve_severity(policy, 5) == "warning"
    assert resolve_severity(policy, 12) == "error"


def test_rule_severity_policy_from_config_parses_and_sorts_bands(tmp_path: Path) -> None:
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        """
        [sqlfluff]
        dialect = ansi

        [sqlfluff:rules:CPX_C102]
        severity = info
        severity_bands = [{"min": 13, "severity": "error"}, {"min": 9, "severity": "warning"}]
        """,
        encoding="utf-8",
    )
    config = FluffConfig.from_root(extra_config_path=str(cfg), overrides={"dialect": "ansi"})
    policy = rule_severity_policy_from_config(config, "CPX_C102")
    assert policy.default_severity == "info"
    assert [band.min_value for band in policy.bands] == [9, 13]


def test_invalid_default_severity_raises_clear_error() -> None:
    with pytest.raises(ValueError, match=r"severity"):
        parse_default_severity("urgent", config_key="[sqlfluff:rules:CPX_C102].severity")


@pytest.mark.parametrize(
    ("value", "match"),
    [
        ("{not-json", r"severity_bands"),
        ('{"min":1}', r"expected a JSON list"),
        ('[{"severity":"warning"}]', r"missing required key 'min'"),
        ('[{"min":2}]', r"missing required key 'severity'"),
        ('[{"min":-1,"severity":"warning"}]', r"expected >= 0"),
        ('[{"min":1,"severity":"warning"},{"min":1,"severity":"error"}]', r"duplicate band min=1"),
        ('[{"min":1,"severity":"urgent"}]', r"expected one of"),
    ],
)
def test_invalid_severity_bands_raise_clear_errors(value: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        parse_severity_bands(value, config_key="[sqlfluff:rules:CPX_C102].severity_bands")


def test_severity_to_level_mapping() -> None:
    assert severity_to_level("info") == "note"
    assert severity_to_level("warning") == "warning"
    assert severity_to_level("error") == "error"
