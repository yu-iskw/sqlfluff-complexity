"""Tests for ConfigValidationError and parse_severity_bands."""

from __future__ import annotations

import pytest

from sqlfluff_complexity.core.config.policy import parse_severity_bands
from sqlfluff_complexity.core.config.severity import SeverityBand, SeverityLevel
from sqlfluff_complexity.core.config.validation import ConfigValidationError


class TestConfigValidationError:
    def test_structured_fields(self) -> None:
        err = ConfigValidationError("CPX_C101.severity", "critical", 'one of: "info", "warning", "error"')
        assert err.config_key == "CPX_C101.severity"
        assert err.invalid_value == "critical"
        assert "info" in err.expected

    def test_message_format(self) -> None:
        err = ConfigValidationError("CPX_C101.severity", "bad", "expected something")
        msg = str(err)
        assert "CPX_C101.severity" in msg
        assert "'bad'" in msg
        assert "expected something" in msg

    def test_is_value_error(self) -> None:
        err = ConfigValidationError("k", "v", "e")
        assert isinstance(err, ValueError)


class TestParseSeverityBands:
    def test_empty_string_returns_empty_tuple(self) -> None:
        assert parse_severity_bands("") == ()
        assert parse_severity_bands(None) == ()
        assert parse_severity_bands("  ") == ()

    def test_valid_single_band(self) -> None:
        result = parse_severity_bands('[{"threshold": 10, "severity": "error"}]')
        assert len(result) == 1
        assert result[0].threshold == 10
        assert result[0].severity is SeverityLevel.error

    def test_valid_two_bands_sorted(self) -> None:
        result = parse_severity_bands(
            '[{"threshold": 15, "severity": "error"}, {"threshold": 5, "severity": "warning"}]'
        )
        assert len(result) == 2
        assert result[0].threshold == 5
        assert result[1].threshold == 15

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            parse_severity_bands("not-json", context="CPX_C101.severity_bands")
        assert exc_info.value.config_key == "CPX_C101.severity_bands"

    def test_not_array_raises(self) -> None:
        with pytest.raises(ConfigValidationError):
            parse_severity_bands('{"threshold": 10, "severity": "error"}')

    def test_band_missing_threshold_raises(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            parse_severity_bands('[{"severity": "error"}]', context="CPX_C101.severity_bands")
        assert "threshold" in str(exc_info.value)

    def test_band_missing_severity_raises(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            parse_severity_bands('[{"threshold": 10}]', context="CPX_C101.severity_bands")
        assert "severity" in str(exc_info.value)

    def test_band_negative_threshold_raises(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            parse_severity_bands('[{"threshold": -1, "severity": "error"}]')
        assert exc_info.value.invalid_value == -1

    def test_band_non_integer_threshold_raises(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            parse_severity_bands('[{"threshold": "ten", "severity": "error"}]')
        assert exc_info.value.invalid_value == "ten"

    def test_band_invalid_severity_raises(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            parse_severity_bands('[{"threshold": 10, "severity": "critical"}]')
        assert "critical" in str(exc_info.value.invalid_value)

    def test_band_non_string_severity_raises(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            parse_severity_bands('[{"threshold": 10, "severity": 1}]')
        assert exc_info.value.invalid_value == 1

    def test_non_dict_element_raises(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            parse_severity_bands('["not-a-dict"]')
        assert "object" in str(exc_info.value)

    def test_returns_severity_band_instances(self) -> None:
        result = parse_severity_bands('[{"threshold": 5, "severity": "warning"}]')
        assert isinstance(result[0], SeverityBand)
        assert isinstance(result[0].severity, SeverityLevel)
