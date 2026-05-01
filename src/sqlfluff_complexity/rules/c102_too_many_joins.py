# Copyright 2025 yu-iskw
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Rule CPX_C102: too many JOIN clauses."""

from __future__ import annotations

from typing import ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler

from sqlfluff_complexity.core.policy import ComplexityPolicy
from sqlfluff_complexity.core.segment_tree import collect_metrics
from sqlfluff_complexity.rules.base import (
    MetricRuleSpec,
    metric_lint_result,
    resolve_context_policy,
)


class Rule_CPX_C102(BaseRule):  # noqa: N801
    """Query contains too many JOIN clauses.

    **Anti-pattern**

    A single statement joins many relations, making the model harder to review.

    **Best practice**

    Split complex relational fan-in across clearer intermediate models.
    """

    groups: tuple[str, ...] = ("all", "complexity")
    config_keywords: ClassVar[list[str]] = ["max_joins"]
    crawl_behaviour = SegmentSeekerCrawler({"select_statement"})
    is_fix_compatible = False
    max_joins: int
    _spec: ClassVar[MetricRuleSpec] = MetricRuleSpec(
        rule_id="CPX_C102",
        metric_name="joins",
        config_key="max_joins",
        policy_key="max_joins",
        description_label="join count",
        guidance="Consider decomposing the model or moving joins upstream.",
    )

    def _eval(self, context: RuleContext) -> LintResult | None:
        """Evaluate the rule."""
        policy = resolve_context_policy(context, ComplexityPolicy(max_joins=int(self.max_joins)))
        return metric_lint_result(context, collect_metrics(context.segment), policy, self._spec)
