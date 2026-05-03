"""Tests for helpers in ``sqlfluff_complexity.rules.base`` (file root, nested selects)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sqlfluff.core import FluffConfig, Linter
from sqlfluff.core.rules.context import RuleContext

from sqlfluff_complexity.core.config.policy import ComplexityPolicy
from sqlfluff_complexity.core.scan.segment_tree import (
    analyze_segment_tree,
    is_nested_select_statement,
)
from sqlfluff_complexity.rules.base import (
    MetricRuleSpec,
    eval_file_root_metric_threshold,
    file_segment_from_context,
    metric_lint_result,
)
from sqlfluff_complexity.tests.fixture_loader import read_sql_fixture

if TYPE_CHECKING:
    from sqlfluff.core.parser.segments.base import BaseSegment


def _all_segments_of_type(root: BaseSegment, segment_type: str) -> list[BaseSegment]:
    found: list[BaseSegment] = []
    stack: list[BaseSegment] = [root]
    while stack:
        seg = stack.pop()
        if getattr(seg, "type", "") == segment_type:
            found.append(seg)
        stack.extend(reversed(getattr(seg, "segments", ()) or ()))
    return found


def _ancestor_stack_to(root: BaseSegment, target: BaseSegment) -> tuple[BaseSegment, ...]:
    """Ancestors from parse root down to and including the direct parent of ``target``."""

    def dfs(node: BaseSegment, acc: list[BaseSegment]) -> bool:
        for child in getattr(node, "segments", ()) or ():
            if child is target:
                stack.clear()
                stack.extend([*acc, node])
                return True
            if dfs(child, [*acc, node]):
                return True
        return False

    stack: list[BaseSegment] = []
    if not dfs(root, []):
        message = "target segment not found under root"
        raise AssertionError(message)
    return tuple(stack)


def test_file_segment_from_context_finds_file_in_parent_stack_for_inner_select() -> None:
    """``parent_stack`` from root to parent of inner ``select_statement`` includes ``file``."""
    cfg = FluffConfig.from_kwargs(dialect="ansi")
    linter = Linter(config=cfg)
    root = linter.parse_string("select * from (select 1 as x) s").tree
    assert getattr(root, "type", "") == "file"
    selects = _all_segments_of_type(root, "select_statement")
    inner = selects[-1]
    parent_stack = _ancestor_stack_to(root, inner)
    assert parent_stack
    assert getattr(parent_stack[0], "type", "") == "file"
    ctx = RuleContext(
        dialect=linter.dialect,
        fix=False,
        templated_file=None,
        path=Path("m.sql"),
        config=cfg,
        segment=inner,
        parent_stack=parent_stack,
    )
    assert file_segment_from_context(ctx) is root


def test_file_segment_from_context_finds_file_in_parent_stack() -> None:
    """Lint contexts may carry ``file`` on ``parent_stack``."""
    cfg = FluffConfig.from_kwargs(dialect="ansi")
    linter = Linter(config=cfg)
    root = linter.parse_string("select 1").tree
    assert getattr(root, "type", "") == "file"
    inner = root.segments[0]
    ctx = RuleContext(
        dialect=linter.dialect,
        fix=False,
        templated_file=None,
        path=Path("m.sql"),
        config=cfg,
        segment=inner,
        parent_stack=(root,),
    )
    assert file_segment_from_context(ctx) is root


def test_is_nested_select_statement_inner_derived_table() -> None:
    """Inner select in FROM is nested under outer select_statement."""
    root = Linter(dialect="ansi").parse_string("select * from (select 1 as x) s").tree
    selects = _all_segments_of_type(root, "select_statement")
    assert len(selects) >= 2
    inner_sel = selects[-1]
    assert is_nested_select_statement(inner_sel) is True


def test_metric_lint_result_anchor_segment_overrides_context_segment() -> None:
    """Violations can anchor on the analyzed root (e.g. ``file``) when it differs from context."""
    cfg = FluffConfig.from_kwargs(dialect="ansi")
    linter = Linter(config=cfg)
    root = linter.parse_string(read_sql_fixture("ansi", "c108_nested_case")).tree
    assert getattr(root, "type", "") == "file"
    selects = _all_segments_of_type(root, "select_statement")
    inner = selects[0]
    ctx = RuleContext(
        dialect=linter.dialect,
        fix=False,
        templated_file=None,
        path=Path("m.sql"),
        config=cfg,
        segment=inner,
        parent_stack=(root,),
    )
    file_root = file_segment_from_context(ctx)
    analysis = analyze_segment_tree(file_root)
    spec = MetricRuleSpec(
        rule_id="CPX_C108",
        metric_name="expression_depth",
        config_key="max_nested_case_depth",
        policy_key="max_nested_case_depth",
        description_label="nested CASE depth",
    )
    policy = ComplexityPolicy(max_nested_case_depth=1)
    result = metric_lint_result(
        ctx,
        analysis.metrics,
        policy,
        spec,
        precomputed_analysis=analysis,
        anchor_segment=file_root,
    )
    assert result is not None
    assert result.anchor is file_root


def test_metric_lint_result_raises_when_anchor_without_precomputed() -> None:
    """anchor_segment without precomputed_analysis must raise (anchor vs contributors invariant)."""
    cfg = FluffConfig.from_kwargs(dialect="ansi")
    linter = Linter(config=cfg)
    root = linter.parse_string(read_sql_fixture("ansi", "c108_nested_case")).tree
    assert getattr(root, "type", "") == "file"
    selects = _all_segments_of_type(root, "select_statement")
    inner = selects[0]
    ctx = RuleContext(
        dialect=linter.dialect,
        fix=False,
        templated_file=None,
        path=Path("m.sql"),
        config=cfg,
        segment=inner,
        parent_stack=(root,),
    )
    file_root = file_segment_from_context(ctx)
    analysis = analyze_segment_tree(file_root)
    spec = MetricRuleSpec(
        rule_id="CPX_C108",
        metric_name="expression_depth",
        config_key="max_nested_case_depth",
        policy_key="max_nested_case_depth",
        description_label="nested CASE depth",
    )
    policy = ComplexityPolicy(max_nested_case_depth=1)
    with pytest.raises(ValueError, match="anchor_segment requires precomputed_analysis"):
        metric_lint_result(
            ctx,
            analysis.metrics,
            policy,
            spec,
            anchor_segment=file_root,
        )


@pytest.mark.parametrize(
    ("spec", "policy"),
    [
        (
            MetricRuleSpec(
                rule_id="CPX_C108",
                metric_name="expression_depth",
                config_key="max_nested_case_depth",
                policy_key="max_nested_case_depth",
                description_label="nested CASE depth",
            ),
            ComplexityPolicy(max_nested_case_depth=10),
        ),
        (
            MetricRuleSpec(
                rule_id="CPX_C109",
                metric_name="set_operation_count",
                config_key="max_set_operations",
                policy_key="max_set_operations",
                description_label="set operation count",
            ),
            ComplexityPolicy(max_set_operations=10),
        ),
    ],
    ids=["c108", "c109"],
)
def test_eval_file_root_metric_threshold_returns_none_when_under_limit(
    spec: MetricRuleSpec,
    policy: ComplexityPolicy,
) -> None:
    """File-root helper should not emit a lint result when the metric is within policy."""
    cfg = FluffConfig.from_kwargs(dialect="ansi")
    linter = Linter(config=cfg)
    root = linter.parse_string("select 1").tree
    ctx = RuleContext(
        dialect=linter.dialect,
        fix=False,
        templated_file=None,
        path=Path("m.sql"),
        config=cfg,
        segment=root,
        parent_stack=(),
    )
    assert eval_file_root_metric_threshold(ctx, policy, spec) is None


def test_metric_lint_result_raises_when_anchor_and_precomputed_metrics_mismatch() -> None:
    """Passing mismatched metrics vs precomputed_analysis with anchor_segment must fail fast."""
    cfg = FluffConfig.from_kwargs(dialect="ansi")
    linter = Linter(config=cfg)
    nested_root = linter.parse_string(read_sql_fixture("ansi", "c108_nested_case")).tree
    simple_root = linter.parse_string("select 1").tree
    nested_analysis = analyze_segment_tree(nested_root)
    simple_analysis = analyze_segment_tree(simple_root)
    inner = _all_segments_of_type(nested_root, "select_statement")[0]
    ctx = RuleContext(
        dialect=linter.dialect,
        fix=False,
        templated_file=None,
        path=Path("m.sql"),
        config=cfg,
        segment=inner,
        parent_stack=(nested_root,),
    )
    spec = MetricRuleSpec(
        rule_id="CPX_C108",
        metric_name="expression_depth",
        config_key="max_nested_case_depth",
        policy_key="max_nested_case_depth",
        description_label="nested CASE depth",
    )
    policy = ComplexityPolicy(max_nested_case_depth=1)
    with pytest.raises(ValueError, match="anchor_segment and precomputed_analysis disagree"):
        metric_lint_result(
            ctx,
            nested_analysis.metrics,
            policy,
            spec,
            precomputed_analysis=simple_analysis,
            anchor_segment=nested_root,
        )
