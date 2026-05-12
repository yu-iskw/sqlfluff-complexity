"""Severity policy parsing and resolution shared by lint and report modes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from sqlfluff.core import FluffConfig

Severity = Literal["info", "warning", "error"]
VALID_SEVERITIES: tuple[Severity, ...] = ("info", "warning", "error")


@dataclass(frozen=True)
class SeverityBand:
    """Severity threshold band for a metric value."""

    min_value: int
    severity: Severity


@dataclass(frozen=True)
class RuleSeverityPolicy:
    """Resolved severity policy for one CPX rule."""

    rule_code: str
    default_severity: Severity
    bands: tuple[SeverityBand, ...]


def _parse_severity(value: str, *, config_key: str) -> Severity:
    parsed = value.strip().lower()
    if parsed not in VALID_SEVERITIES:
        message = (
            f"Invalid {config_key!r} value {value!r}; "
            f"expected one of {list(VALID_SEVERITIES)}."
        )
        raise ValueError(message)
    return parsed


def parse_default_severity(raw_value: object, *, config_key: str) -> Severity:
    """Parse default severity from config value."""
    if raw_value is None:
        return "warning"
    return _parse_severity(str(raw_value), config_key=config_key)


def _load_band_payload(raw_value: object, *, config_key: str) -> list[object]:
    text = str(raw_value).strip()
    if not text:
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        message = (
            f"Invalid {config_key!r} JSON value {raw_value!r}; expected a JSON list of "
            "objects like {'min': 10, 'severity': 'error'}."
        )
        raise ValueError(message) from exc
    if not isinstance(payload, list):
        message = f"Invalid {config_key!r} value {raw_value!r}; expected a JSON list."
        raise ValueError(message)  # noqa: TRY004
    return payload


def _parse_band(item: object, *, index: int, config_key: str) -> SeverityBand:
    if not isinstance(item, dict):
        message = f"Invalid {config_key!r}[{index}] value {item!r}; expected an object."
        raise ValueError(message)  # noqa: TRY004
    if "min" not in item:
        message = f"Invalid {config_key!r}[{index}] value {item!r}; missing required key 'min'."
        raise ValueError(message)
    if "severity" not in item:
        message = f"Invalid {config_key!r}[{index}] value {item!r}; missing required key 'severity'."
        raise ValueError(message)
    min_raw = item["min"]
    if not isinstance(min_raw, int):
        message = f"Invalid {config_key!r}[{index}].min value {min_raw!r}; expected an integer."
        raise ValueError(message)  # noqa: TRY004
    if min_raw < 0:
        message = f"Invalid {config_key!r}[{index}].min value {min_raw!r}; expected >= 0."
        raise ValueError(message)
    return SeverityBand(
        min_value=min_raw,
        severity=_parse_severity(
            str(item["severity"]),
            config_key=f"{config_key}[{index}].severity",
        ),
    )


def parse_severity_bands(raw_value: object, *, config_key: str) -> tuple[SeverityBand, ...]:
    """Parse severity bands from JSON array config value."""
    if raw_value is None:
        return ()
    payload = _load_band_payload(raw_value, config_key=config_key)
    if not payload:
        return ()

    bands: list[SeverityBand] = []
    seen_mins: set[int] = set()
    for index, item in enumerate(payload):
        band = _parse_band(item, index=index, config_key=config_key)
        if band.min_value in seen_mins:
            message = (
                f"Invalid {config_key!r} value {raw_value!r}; duplicate band min={band.min_value}."
            )
            raise ValueError(message)
        seen_mins.add(band.min_value)
        bands.append(band)
    return tuple(sorted(bands, key=lambda band: band.min_value))


def rule_severity_policy_from_config(config: FluffConfig, rule_code: str) -> RuleSeverityPolicy:
    """Build a rule severity policy from SQLFluff config."""
    section = ("rules", rule_code)
    severity_key = "severity"
    bands_key = "severity_bands"
    return RuleSeverityPolicy(
        rule_code=rule_code,
        default_severity=parse_default_severity(
            config.get(severity_key, section=section, default="warning"),
            config_key=f"[sqlfluff:rules:{rule_code}].{severity_key}",
        ),
        bands=parse_severity_bands(
            config.get(bands_key, section=section, default=""),
            config_key=f"[sqlfluff:rules:{rule_code}].{bands_key}",
        ),
    )


def resolve_severity(policy: RuleSeverityPolicy, value: int) -> Severity:
    """Resolve severity for an observed metric value."""
    severity = policy.default_severity
    for band in policy.bands:
        if value >= band.min_value:
            severity = band.severity
    return severity


def severity_to_level(severity: Severity) -> Literal["note", "warning", "error"]:
    """Map internal severity to legacy/reporting level."""
    if severity == "info":
        return "note"
    return severity
