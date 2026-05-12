"""Structured config validation error for CPX rule configuration."""

from __future__ import annotations


class ConfigValidationError(ValueError):
    """A config key has an invalid value.

    Attributes:
        config_key: The dotted config key path, e.g. ``CPX_C101.severity``.
        invalid_value: The value that was rejected.
        expected: Human-readable description of what is expected.
    """

    def __init__(self, config_key: str, invalid_value: object, expected: str) -> None:
        self.config_key = config_key
        self.invalid_value = invalid_value
        self.expected = expected
        super().__init__(f"Invalid value {invalid_value!r} for {config_key}: expected {expected}")
