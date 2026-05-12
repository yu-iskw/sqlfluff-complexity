"""Severity level model for CPX rule findings."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from sqlfluff_complexity.core.config.validation import ConfigValidationError

_SEVERITY_VALUES = ("info", "warning", "error")

# Used inside SeverityLevel ordering methods before the class body is complete.
# Keyed by the string value so no forward reference to the enum is needed.
_RANK_BY_VALUE: dict[str, int] = {"info": 0, "warning": 1, "error": 2}


class SeverityLevel(str, Enum):
    """Severity level for a CPX finding.

    As a ``str`` subclass, values serialise to plain strings in JSON and
    compare equal to the equivalent string literals (``"warning" ==
    SeverityLevel.warning`` is ``True``).
    """

    info = "info"
    warning = "warning"
    error = "error"

    def __str__(self) -> str:
        return self.value

    def __format__(self, format_spec: str) -> str:
        return self.value.__format__(format_spec)

    @classmethod
    def from_str(cls, value: str, *, config_key: str = "severity") -> SeverityLevel:
        """Return the matching level or raise :class:`ConfigValidationError`."""
        try:
            return cls(value)
        except ValueError:
            raise ConfigValidationError(
                config_key=config_key,
                invalid_value=value,
                expected=f"one of: {', '.join(repr(v) for v in _SEVERITY_VALUES)}",
            ) from None

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SeverityLevel):
            return NotImplemented
        return _RANK_BY_VALUE[self] < _RANK_BY_VALUE[other]

    def __le__(self, other: object) -> bool:
        if not isinstance(other, SeverityLevel):
            return NotImplemented
        return _RANK_BY_VALUE[self] <= _RANK_BY_VALUE[other]

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, SeverityLevel):
            return NotImplemented
        return _RANK_BY_VALUE[self] > _RANK_BY_VALUE[other]

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, SeverityLevel):
            return NotImplemented
        return _RANK_BY_VALUE[self] >= _RANK_BY_VALUE[other]


@dataclass(frozen=True)
class SeverityBand:
    """A threshold that activates a specific severity level.

    When the measured metric value is greater than or equal to
    ``threshold``, this band may apply.
    """

    threshold: int
    severity: SeverityLevel


@dataclass(frozen=True)
class RulePolicy:
    """Per-rule severity configuration.

    Attributes:
        default_severity: Level used when no band threshold is reached.
        bands: Ordered bands (ascending by threshold).  The highest-severity
            matching band wins when multiple bands apply.
    """

    default_severity: SeverityLevel = SeverityLevel.warning
    bands: tuple[SeverityBand, ...] = ()


# Default policy for every CPX rule: warning, no bands.
_DEFAULT_RULE_POLICY = RulePolicy()

RULE_DEFAULT_POLICIES: dict[str, RulePolicy] = dict.fromkeys(("CPX_C101", "CPX_C102", "CPX_C103", "CPX_C104", "CPX_C105", "CPX_C106", "CPX_C107", "CPX_C108", "CPX_C109", "CPX_C110", "CPX_C201"), _DEFAULT_RULE_POLICY)

_SEVERITY_RANK: dict[SeverityLevel, int] = {
    SeverityLevel.info: 0,
    SeverityLevel.warning: 1,
    SeverityLevel.error: 2,
}


def resolve_severity(value: int, policy: RulePolicy) -> SeverityLevel:
    """Resolve the effective severity for a measured metric value.

    Scans ``policy.bands`` (expected ascending by threshold) and returns the
    highest-severity band whose threshold is reached.  Falls back to
    ``policy.default_severity`` if no band matches.
    """
    best: SeverityLevel | None = None
    for band in policy.bands:
        if value >= band.threshold and (best is None or _SEVERITY_RANK[band.severity] > _SEVERITY_RANK[best]):
            best = band.severity
    return best if best is not None else policy.default_severity
