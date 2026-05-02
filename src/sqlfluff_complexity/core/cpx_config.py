"""CPX rule config keys shared by SQLFluff lint and report (parity)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlfluff.core import FluffConfig

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
