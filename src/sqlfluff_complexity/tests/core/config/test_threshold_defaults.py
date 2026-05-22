"""Keep recommended numeric thresholds aligned across config surfaces."""

from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path

from sqlfluff_complexity.core.config.policy import ComplexityPolicy
from sqlfluff_complexity.core.config.presets import PRESETS, render_preset_config
from sqlfluff_complexity.core.config.rule_registry import METRIC_RULE_DEFINITIONS


def _plugin_thresholds() -> dict[str, int]:
    plugin_config = Path("src/sqlfluff_complexity/plugin_default_config.cfg")
    parser = ConfigParser()
    parser.read(plugin_config)
    out: dict[str, int] = {}
    for definition in METRIC_RULE_DEFINITIONS:
        section = f"sqlfluff:rules:{definition.rule_id}"
        out[definition.policy_key] = int(parser[section][definition.config_key])
    out["max_complexity_score"] = int(parser["sqlfluff:rules:CPX_C201"]["max_complexity_score"])
    return out


def _preset_recommended_thresholds() -> dict[str, int]:
    preset = PRESETS["recommended"]
    return {
        "max_ctes": preset.max_ctes,
        "max_joins": preset.max_joins,
        "max_subquery_depth": preset.max_subquery_depth,
        "max_case_expressions": preset.max_case_expressions,
        "max_boolean_operators": preset.max_boolean_operators,
        "max_window_functions": preset.max_window_functions,
        "max_cte_dependency_depth": preset.max_cte_dependency_depth,
        "max_nested_case_depth": preset.max_nested_case_depth,
        "max_set_operations": preset.max_set_operations,
        "max_derived_tables": preset.max_derived_tables,
        "max_complexity_score": preset.max_complexity_score,
    }


def _policy_thresholds() -> dict[str, int]:
    policy = ComplexityPolicy()
    return {key: int(getattr(policy, key)) for key in _plugin_thresholds()}


def test_recommended_thresholds_match_complexity_policy() -> None:
    """``ComplexityPolicy`` defaults are the single source for recommended numbers."""
    assert _preset_recommended_thresholds() == _policy_thresholds()


def test_plugin_default_config_matches_complexity_policy() -> None:
    """Packaged plugin defaults must match :class:`ComplexityPolicy` field defaults."""
    assert _plugin_thresholds() == _policy_thresholds()


def test_rendered_recommended_preset_matches_plugin_defaults() -> None:
    """Generated ``config preset recommended`` thresholds must match packaged plugin cfg."""
    rendered = render_preset_config("recommended", dialect="ansi")
    plugin = _plugin_thresholds()
    for key, expected in plugin.items():
        assert f"{key} = {expected}" in rendered


def test_c107_preset_omits_contributor_keys_like_plugin() -> None:
    """CPX_C107 packaged config has no contributor toggles; preset output matches."""
    rendered = render_preset_config("recommended", dialect="ansi")
    c107_block = rendered.split("[sqlfluff:rules:CPX_C107]")[1].split("[sqlfluff:rules:")[0]
    assert "show_contributors" not in c107_block
    assert "max_contributors" not in c107_block
