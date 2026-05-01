"""Shared helpers for SQLFluff complexity rules."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from sqlfluff.core.rules import LintResult

from sqlfluff_complexity.core.policy import POLICY_MODES, ComplexityPolicy, resolve_policy

if TYPE_CHECKING:
    from sqlfluff.core.rules import RuleContext

    from sqlfluff_complexity.core.metrics import ComplexityMetrics


@dataclass(frozen=True)
class MetricRuleSpec:
    """Configuration for one threshold-based metric rule."""

    rule_id: str
    metric_name: str
    config_key: str
    policy_key: str
    description_label: str
    guidance: str


def resolve_context_policy(context: RuleContext, base_policy: ComplexityPolicy) -> ComplexityPolicy:
    """Resolve path-specific policy for a SQLFluff rule context."""
    mode = context.config.get("mode", section=("rules", "CPX_C201"), default=base_policy.mode)
    if mode not in POLICY_MODES:
        message = f"Complexity policy mode must be one of {sorted(POLICY_MODES)}."
        raise ValueError(message)
    base_policy = replace(base_policy, mode=mode)
    raw_overrides = context.config.get("path_overrides", section=("rules", "CPX_C201"), default="")
    path = str(context.path) if context.path is not None else None
    return resolve_policy(base_policy, raw_overrides, path)


def metric_lint_result(
    context: RuleContext,
    metrics: ComplexityMetrics,
    policy: ComplexityPolicy,
    spec: MetricRuleSpec,
) -> LintResult | None:
    """Build a lint result for one metric threshold, if violated."""
    if policy.mode == "report":
        return None

    actual = int(getattr(metrics, spec.metric_name))
    limit = int(getattr(policy, spec.policy_key))
    if actual <= limit:
        return None

    return LintResult(
        anchor=context.segment,
        description=(
            f"{spec.rule_id}: {spec.description_label} {actual} exceeds "
            f"{spec.config_key}={limit}. {spec.guidance}"
        ),
    )
