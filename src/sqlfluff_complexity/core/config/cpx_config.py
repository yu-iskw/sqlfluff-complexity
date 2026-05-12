"""CPX rule config keys shared by SQLFluff lint and report (parity)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlfluff.core import FluffConfig

    from sqlfluff_complexity.core.config.severity import SeverityBand, SeverityLevel

_TRUTHY_STRINGS = frozenset({"1", "true", "yes", "on"})

DEFAULT_MAX_CONTRIBUTORS = 3


def truthy_config_string(raw: object) -> bool:
    """Match SQLFluff CPX rules: treat common string forms as true."""
    return str(raw).strip().lower() in _TRUTHY_STRINGS


def contributor_display_settings(
    config: FluffConfig,
    rule_id: str,
    *,
    default_max_contributors: int = DEFAULT_MAX_CONTRIBUTORS,
) -> tuple[bool, int]:
    """Return ``show_contributors`` and ``max_contributors`` for one rule section."""
    show_raw = config.get("show_contributors", section=("rules", rule_id), default=True)
    max_c = int(
        config.get(
            "max_contributors",
            section=("rules", rule_id),
            default=default_max_contributors,
        ),
    )
    return truthy_config_string(show_raw), max_c


def read_rule_severity(config: FluffConfig, rule_id: str) -> SeverityLevel:
    """Return the configured :class:`SeverityLevel` for *rule_id*.

    Reads the ``severity`` key from the rule's config section and falls back to
    ``warning`` when the key is absent.  Raises
    :class:`~sqlfluff_complexity.core.config.validation.ConfigValidationError`
    for unrecognised values.
    """
    from sqlfluff_complexity.core.config.severity import (  # noqa: PLC0415
        RULE_DEFAULT_POLICIES,
        SeverityLevel,
    )

    raw = config.get("severity", section=("rules", rule_id), default=None)
    if raw is None:
        return RULE_DEFAULT_POLICIES.get(rule_id, RULE_DEFAULT_POLICIES["CPX_C201"]).default_severity
    return SeverityLevel.from_str(str(raw).strip(), config_key=f"{rule_id}.severity")


def read_severity_bands(
    config: FluffConfig,
    rule_id: str,
) -> tuple[SeverityBand, ...]:
    """Return parsed severity bands for *rule_id*, or ``()`` if not configured.

    Raises
    :class:`~sqlfluff_complexity.core.config.validation.ConfigValidationError`
    on malformed band data.
    """
    from sqlfluff_complexity.core.config.policy import parse_severity_bands  # noqa: PLC0415

    raw = config.get("severity_bands", section=("rules", rule_id), default=None)
    return parse_severity_bands(raw, context=f"{rule_id}.severity_bands")


def resolve_rule_severity(
    config: FluffConfig,
    rule_id: str,
    value: int,
) -> SeverityLevel:
    """Resolve the effective severity for *rule_id* given a measured *value*.

    Combines :func:`read_rule_severity`, :func:`read_severity_bands`, and
    :func:`~sqlfluff_complexity.core.config.severity.resolve_severity`.
    """
    from sqlfluff_complexity.core.config.severity import RulePolicy, resolve_severity  # noqa: PLC0415

    policy = RulePolicy(
        default_severity=read_rule_severity(config, rule_id),
        bands=read_severity_bands(config, rule_id),
    )
    return resolve_severity(value, policy)
