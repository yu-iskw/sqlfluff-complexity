"""Tests for the SeverityLevel, SeverityBand, RulePolicy, and resolve_severity model."""

from __future__ import annotations

import json

import pytest

from sqlfluff_complexity.core.config.severity import (
    RULE_DEFAULT_POLICIES,
    RulePolicy,
    SeverityBand,
    SeverityLevel,
    resolve_severity,
)
from sqlfluff_complexity.core.config.validation import ConfigValidationError

_ALL_CPX_RULE_IDS = (
    "CPX_C101",
    "CPX_C102",
    "CPX_C103",
    "CPX_C104",
    "CPX_C105",
    "CPX_C106",
    "CPX_C107",
    "CPX_C108",
    "CPX_C109",
    "CPX_C110",
    "CPX_C201",
)


class TestSeverityLevelOrdering:
    def test_info_is_lowest(self) -> None:
        assert SeverityLevel.info < SeverityLevel.warning

    def test_warning_is_middle(self) -> None:
        assert SeverityLevel.warning < SeverityLevel.error

    def test_info_is_below_error(self) -> None:
        assert SeverityLevel.info < SeverityLevel.error

    def test_str_equality(self) -> None:
        """SeverityLevel is a str subclass; values equal their string literals."""
        assert SeverityLevel.warning == "warning"
        assert SeverityLevel.error == "error"
        assert SeverityLevel.info == "info"

    def test_json_serialization(self) -> None:
        """str(SeverityLevel) returns the plain value, not the enum repr."""
        payload = {"level": SeverityLevel.warning}
        dumped = json.dumps(payload)
        assert '"warning"' in dumped


class TestSeverityLevelFromStr:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("info", SeverityLevel.info),
            ("warning", SeverityLevel.warning),
            ("error", SeverityLevel.error),
        ],
    )
    def test_valid_values(self, value: str, expected: SeverityLevel) -> None:
        assert SeverityLevel.from_str(value) is expected

    @pytest.mark.parametrize("bad_value", ["critical", "warn", "INFO", "ERROR", "", "none"])
    def test_invalid_raises_config_validation_error(self, bad_value: str) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            SeverityLevel.from_str(bad_value, config_key="CPX_C101.severity")
        err = exc_info.value
        assert err.config_key == "CPX_C101.severity"
        assert err.invalid_value == bad_value
        assert "info" in err.expected
        assert "warning" in err.expected
        assert "error" in err.expected

    def test_default_config_key_in_message(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            SeverityLevel.from_str("bad")
        assert "severity" in str(exc_info.value)


class TestResolveSeverity:
    def test_returns_default_when_no_bands(self) -> None:
        policy = RulePolicy(default_severity=SeverityLevel.warning, bands=())
        assert resolve_severity(9999, policy) is SeverityLevel.warning

    def test_returns_default_when_no_band_matches(self) -> None:
        policy = RulePolicy(
            default_severity=SeverityLevel.info,
            bands=(SeverityBand(threshold=100, severity=SeverityLevel.error),),
        )
        assert resolve_severity(5, policy) is SeverityLevel.info

    def test_returns_band_severity_when_threshold_reached(self) -> None:
        policy = RulePolicy(
            default_severity=SeverityLevel.warning,
            bands=(SeverityBand(threshold=10, severity=SeverityLevel.error),),
        )
        assert resolve_severity(10, policy) is SeverityLevel.error
        assert resolve_severity(11, policy) is SeverityLevel.error

    def test_picks_highest_severity_when_multiple_bands_match(self) -> None:
        policy = RulePolicy(
            default_severity=SeverityLevel.info,
            bands=(
                SeverityBand(threshold=5, severity=SeverityLevel.warning),
                SeverityBand(threshold=10, severity=SeverityLevel.error),
            ),
        )
        assert resolve_severity(10, policy) is SeverityLevel.error
        assert resolve_severity(11, policy) is SeverityLevel.error

    def test_lower_band_does_not_override_higher(self) -> None:
        policy = RulePolicy(
            default_severity=SeverityLevel.info,
            bands=(
                SeverityBand(threshold=5, severity=SeverityLevel.warning),
                SeverityBand(threshold=20, severity=SeverityLevel.error),
            ),
        )
        assert resolve_severity(7, policy) is SeverityLevel.warning
        assert resolve_severity(20, policy) is SeverityLevel.error

    def test_at_threshold_boundary_exact(self) -> None:
        policy = RulePolicy(
            default_severity=SeverityLevel.warning,
            bands=(SeverityBand(threshold=5, severity=SeverityLevel.error),),
        )
        assert resolve_severity(4, policy) is SeverityLevel.warning
        assert resolve_severity(5, policy) is SeverityLevel.error

    def test_value_zero_returns_default(self) -> None:
        policy = RulePolicy(default_severity=SeverityLevel.info)
        assert resolve_severity(0, policy) is SeverityLevel.info

    def test_deterministic_same_threshold_bands(self) -> None:
        """resolve_severity is deterministic for identical policies and values."""
        policy = RulePolicy(
            default_severity=SeverityLevel.info,
            bands=(
                SeverityBand(threshold=5, severity=SeverityLevel.warning),
                SeverityBand(threshold=10, severity=SeverityLevel.error),
            ),
        )
        results = {resolve_severity(12, policy) for _ in range(50)}
        assert results == {SeverityLevel.error}


class TestRuleDefaultPolicies:
    def test_covers_all_cpx_rules(self) -> None:
        for rule_id in _ALL_CPX_RULE_IDS:
            assert rule_id in RULE_DEFAULT_POLICIES, f"{rule_id} missing from RULE_DEFAULT_POLICIES"

    def test_default_severity_is_warning(self) -> None:
        for rule_id, policy in RULE_DEFAULT_POLICIES.items():
            assert policy.default_severity is SeverityLevel.warning, (
                f"{rule_id}: expected default_severity=warning, got {policy.default_severity}"
            )

    def test_no_default_bands(self) -> None:
        for rule_id, policy in RULE_DEFAULT_POLICIES.items():
            assert policy.bands == (), f"{rule_id}: expected empty bands by default, got {policy.bands}"
