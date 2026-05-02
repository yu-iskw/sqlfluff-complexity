"""Report generation for SQL complexity metrics."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING

from sqlfluff.core import FluffConfig, Linter
from sqlfluff.core.parser.segments.base import BaseSegment

from sqlfluff_complexity import __version__
from sqlfluff_complexity.core.analysis import (
    MetricContributor,
    format_contributor_examples,
    format_contributor_summary,
    segment_position,
    top_contributors,
    weighted_contributor_samples,
)
from sqlfluff_complexity.core.cpx_config import contributor_display_settings
from sqlfluff_complexity.core.explainability import (
    explain_score_contributors,
    ranked_weighted_contributions,
    refactoring_hint_for_contributors,
)
from sqlfluff_complexity.core.findings import ComplexityFinding, SourceLocation
from sqlfluff_complexity.core.metrics import ComplexityMetrics
from sqlfluff_complexity.core.policy import POLICY_MODES, ComplexityPolicy, resolve_policy
from sqlfluff_complexity.core.remediation import remediation_for_rule
from sqlfluff_complexity.core.scoring import parse_weights
from sqlfluff_complexity.core.segment_tree import analyze_segment_tree
from sqlfluff_complexity.core.violation_messages import metric_threshold_violation_message
from sqlfluff_complexity.reporting.json import findings_to_json_payload
from sqlfluff_complexity.reporting.sarif import findings_to_sarif_payload

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlfluff.core.types import ConfigMappingType


DEFAULT_MAX_JOINS = 8
DEFAULT_MAX_COMPLEXITY_SCORE = 60


@dataclass(frozen=True)
class ReportLimit:
    """One report threshold check."""

    rule_id: str
    metric_name: str
    policy_key: str
    label: str
    config_key: str


REPORT_LIMITS = (
    ReportLimit("CPX_C101", "ctes", "max_ctes", "CTE count", "max_ctes"),
    ReportLimit("CPX_C102", "joins", "max_joins", "Join count", "max_joins"),
    ReportLimit(
        "CPX_C103",
        "subquery_depth",
        "max_subquery_depth",
        "Nested subquery depth",
        "max_subquery_depth",
    ),
    ReportLimit(
        "CPX_C104",
        "case_expressions",
        "max_case_expressions",
        "CASE expression count",
        "max_case_expressions",
    ),
    ReportLimit(
        "CPX_C105",
        "boolean_operators",
        "max_boolean_operators",
        "Boolean operator count",
        "max_boolean_operators",
    ),
    ReportLimit(
        "CPX_C106",
        "window_functions",
        "max_window_functions",
        "Window function count",
        "max_window_functions",
    ),
)


@dataclass(frozen=True)
class ReportEntry:
    """Complexity report data for one SQL file path."""

    path: Path
    metrics: ComplexityMetrics | None = None
    score: int | None = None
    findings: list[ComplexityFinding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ComplexityReport:
    """Report data for a set of SQL file paths."""

    entries: list[ReportEntry]

    @property
    def has_errors(self) -> bool:
        """Return whether any input failed to parse or load."""
        return any(entry.errors for entry in self.entries)


def analyze_paths(
    paths: Sequence[Path], *, dialect: str, config_path: Path | None = None
) -> ComplexityReport:
    """Analyze SQL file paths with SQLFluff and collect complexity metrics."""
    config = _build_config(dialect=dialect, config_path=config_path)
    linter = Linter(config=config)
    return ComplexityReport(entries=[_analyze_path(path, linter, config) for path in paths])


def format_console_report(report: ComplexityReport) -> str:
    """Format a complexity report for terminal output."""
    lines = [
        "sqlfluff-complexity report",
        "path score ctes joins subquery_depth case_expressions boolean_operators window_functions",
    ]
    for entry in report.entries:
        lines.extend(_format_console_entry(entry))
    return "\n".join(lines)


def format_sarif_report(report: ComplexityReport) -> str:
    """Format a complexity report as SARIF 2.1.0 JSON."""
    all_findings = [f for e in report.entries for f in e.findings]
    sarif = findings_to_sarif_payload(all_findings)
    return json.dumps(sarif, indent=2, sort_keys=True)


def format_json_report(report: ComplexityReport) -> str:
    """Format a complexity report as stable JSON for automation."""
    all_findings = [f for e in report.entries for f in e.findings]
    payload = {
        "entries": [_json_entry(entry) for entry in report.entries],
        "findings": [_finding_to_canonical_dict(f) for f in all_findings],
        "schema_version": "1.1",
        "tool": "sqlfluff-complexity",
        "version": __version__,
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _finding_to_canonical_dict(finding: ComplexityFinding) -> dict[str, object]:
    return findings_to_json_payload((finding,))["findings"][0]


def analyze_paths_findings(
    paths: Sequence[Path], *, dialect: str, config_path: Path | None = None
) -> list[ComplexityFinding]:
    """Return flat ComplexityFinding list for all paths (canonical API)."""
    report = analyze_paths(paths, dialect=dialect, config_path=config_path)
    return [f for e in report.entries for f in e.findings]


def _analyze_path(path: Path, linter: Linter, config: FluffConfig) -> ReportEntry:
    try:
        sql = path.read_text(encoding="utf-8")
    except OSError as exc:
        return ReportEntry(
            path=path,
            errors=[f"Could not read file: {exc}"],
            findings=[
                _parse_error_finding(str(path), f"Could not read file: {exc}"),
            ],
        )

    parsed = linter.parse_string(sql, fname=str(path))
    parse_errors = [violation.desc() for violation in parsed.violations]
    if parse_errors or parsed.tree is None:
        fallback = "SQLFluff did not return a parse tree."
        messages = parse_errors or [fallback]
        return ReportEntry(
            path=path,
            errors=messages,
            findings=[_parse_error_finding(str(path), msg) for msg in messages],
        )

    analysis = analyze_segment_tree(parsed.tree)
    metrics = analysis.metrics
    policy = _policy_for_path(config, path)
    score = metrics.score(_weights_from_config(config))
    findings = _findings_for_file(
        path=path,
        segment=parsed.tree,
        metrics=metrics,
        score=score,
        policy=policy,
        contributors=analysis.contributors,
        config=config,
    )
    return ReportEntry(path=path, metrics=metrics, score=score, findings=findings)


def load_fluff_config(*, dialect: str, config_path: Path | None = None) -> FluffConfig:
    """Load a FluffConfig the same way as the report command."""
    return _build_config(dialect=dialect, config_path=config_path)


def validate_cpx_plugin_config(config: FluffConfig) -> None:
    """Validate CPX-related config keys using existing parsers.

    Raises ValueError with a clear message on invalid weights or path overrides.
    """
    parse_weights(config.get("complexity_weights", section=("rules", "CPX_C201"), default=None))
    raw_overrides = config.get("path_overrides", section=("rules", "CPX_C201"), default="")
    mode = str(config.get("mode", section=("rules", "CPX_C201"), default="enforce"))
    if mode not in POLICY_MODES:
        message = f"Complexity policy mode must be one of {sorted(POLICY_MODES)}."
        raise ValueError(message)
    base_policy = replace(_threshold_policy_from_config(config), mode=mode)
    resolve_policy(base_policy, raw_overrides, "__config_check__.sql")


def _build_config(dialect: str, config_path: Path | None) -> FluffConfig:
    overrides: ConfigMappingType = {"dialect": dialect}
    if config_path is None:
        return FluffConfig.from_kwargs(dialect=dialect)
    return FluffConfig.from_root(extra_config_path=str(config_path), overrides=overrides)


def _parse_error_finding(path_str: str, message: str) -> ComplexityFinding:
    return ComplexityFinding(
        rule_id="CPX_PARSE_ERROR",
        metric="parse",
        message=message,
        remediation="Fix syntax or dialect settings so SQLFluff can parse the file.",
        location=SourceLocation(path=path_str, line=1, column=1),
        metrics=ComplexityMetrics(),
        score=None,
        threshold=None,
        contributors=(),
        level="error",
    )


def _anchored_location(
    *,
    path_s: str,
    root_line: int,
    root_col: int,
    metric_key: str | None,
    contributors: tuple[MetricContributor, ...],
) -> SourceLocation:
    """Prefer contributor line/column for ``metric_key``, else any positioned contributor."""
    if metric_key is not None:
        for contributor in contributors:
            if contributor.metric == metric_key and contributor.line is not None:
                col = contributor.column if contributor.column is not None else 1
                return SourceLocation(path=path_s, line=contributor.line, column=col)
    for contributor in contributors:
        if contributor.line is not None:
            col = contributor.column if contributor.column is not None else 1
            return SourceLocation(path=path_s, line=contributor.line, column=col)
    return SourceLocation(path=path_s, line=root_line, column=root_col)


def _findings_for_file(
    *,
    path: Path,
    segment: BaseSegment,
    metrics: ComplexityMetrics,
    score: int,
    policy: ComplexityPolicy,
    contributors: tuple[MetricContributor, ...],
    config: FluffConfig,
) -> list[ComplexityFinding]:
    line, col = segment_position(segment)
    line_i = line if line is not None else 1
    col_i = col if col is not None else 1
    path_s = str(path)

    findings: list[ComplexityFinding] = []

    for limit in REPORT_LIMITS:
        show_contributors, max_c = contributor_display_settings(config, limit.rule_id)
        f = _metric_finding(
            path_s=path_s,
            line=line_i,
            col=col_i,
            metrics=metrics,
            policy=policy,
            limit_spec=limit,
            contributors=contributors,
            show_contributors=show_contributors,
            max_contributors=max_c,
            aggregate_score=score,
        )
        if f is not None:
            findings.append(f)

    if score > policy.max_complexity_score:
        findings.append(
            _c201_finding(
                path_s=path_s,
                line=line_i,
                col=col_i,
                metrics=metrics,
                score=score,
                threshold=policy.max_complexity_score,
                contributors=contributors,
                weights=_weights_from_config(config),
                config=config,
            ),
        )
    return findings


def _metric_finding(
    *,
    path_s: str,
    line: int,
    col: int,
    metrics: ComplexityMetrics,
    policy: ComplexityPolicy,
    limit_spec: ReportLimit,
    contributors: tuple[MetricContributor, ...],
    show_contributors: bool,
    max_contributors: int,
    aggregate_score: int,
) -> ComplexityFinding | None:
    actual = int(getattr(metrics, limit_spec.metric_name))
    max_allowed = int(getattr(policy, limit_spec.policy_key))
    if actual <= max_allowed:
        return None

    label_lower = limit_spec.label[0].lower() + limit_spec.label[1:]
    message = metric_threshold_violation_message(
        rule_id=limit_spec.rule_id,
        description_label=label_lower,
        actual=actual,
        config_key=limit_spec.config_key,
        limit=max_allowed,
        metric_name=limit_spec.metric_name,
        contributors=contributors,
        max_contributors=max_contributors,
        show_contributors=show_contributors,
    )
    rem = remediation_for_rule(limit_spec.rule_id)
    picked = (
        top_contributors(
            contributors,
            metric=limit_spec.metric_name,
            limit=max_contributors,
        )
        if show_contributors
        else ()
    )
    loc = _anchored_location(
        path_s=path_s,
        root_line=line,
        root_col=col,
        metric_key=limit_spec.metric_name,
        contributors=contributors,
    )

    return ComplexityFinding(
        rule_id=limit_spec.rule_id,
        metric=limit_spec.metric_name,
        message=message,
        remediation=rem,
        location=loc,
        metrics=metrics,
        score=actual,
        threshold=max_allowed,
        contributors=picked,
        level="warning",
        aggregate_score=aggregate_score,
    )


def _c201_finding(
    *,
    path_s: str,
    line: int,
    col: int,
    metrics: ComplexityMetrics,
    score: int,
    threshold: int,
    contributors: tuple[MetricContributor, ...],
    weights: dict[str, int],
    config: FluffConfig,
) -> ComplexityFinding:
    rem = remediation_for_rule("CPX_C201")
    show_c201, max_c201 = contributor_display_settings(config, "CPX_C201")
    top_n = max(1, max_c201)

    if not show_c201:
        message = (
            f"CPX_C201: aggregate complexity score {score} exceeds max_complexity_score={threshold}. "
            f"{rem} Metrics: {metrics.format_breakdown()}."
        )
        loc = _anchored_location(
            path_s=path_s,
            root_line=line,
            root_col=col,
            metric_key=None,
            contributors=contributors,
        )
        return ComplexityFinding(
            rule_id="CPX_C201",
            metric="complexity_score",
            message=message,
            remediation=rem,
            location=loc,
            metrics=metrics,
            score=score,
            threshold=threshold,
            contributors=(),
            level="warning",
            aggregate_score=score,
        )

    explain = explain_score_contributors(metrics, weights, max_items=top_n)
    top_keys = [name for name, _ in ranked_weighted_contributions(metrics, weights)[:top_n]]
    hint = refactoring_hint_for_contributors(top_keys)
    examples = format_contributor_examples(
        contributors,
        weights,
        max_items=top_n,
    )
    examples_clause = f" {examples}" if examples else ""
    message = (
        f"CPX_C201: aggregate complexity score {score} exceeds max_complexity_score={threshold}. "
        f"{rem} Metrics: {metrics.format_breakdown()}. "
        f"Top contributors: {explain}.{examples_clause} {hint}"
    )
    picked = weighted_contributor_samples(
        contributors,
        weights,
        max_items=top_n,
    )
    loc = _anchored_location(
        path_s=path_s,
        root_line=line,
        root_col=col,
        metric_key=None,
        contributors=contributors,
    )

    return ComplexityFinding(
        rule_id="CPX_C201",
        metric="complexity_score",
        message=message,
        remediation=rem,
        location=loc,
        metrics=metrics,
        score=score,
        threshold=threshold,
        contributors=picked,
        level="warning",
        aggregate_score=score,
    )


def _policy_for_path(config: FluffConfig, path: Path) -> ComplexityPolicy:
    base_policy = _threshold_policy_from_config(config)
    raw_overrides = config.get("path_overrides", section=("rules", "CPX_C201"), default="")
    return resolve_policy(base_policy, raw_overrides, str(path))


def _weights_from_config(config: FluffConfig) -> dict[str, int]:
    raw_weights = config.get("complexity_weights", section=("rules", "CPX_C201"), default=None)
    return parse_weights(raw_weights)


def _config_int(config: FluffConfig, rule_code: str, key: str, default: int) -> int:
    value = config.get(key, section=("rules", rule_code), default=default)
    return int(value)


def _threshold_policy_from_config(config: FluffConfig) -> ComplexityPolicy:
    """Numeric CPX thresholds from FluffConfig (default ``mode`` for report scoring)."""
    return ComplexityPolicy(
        max_ctes=_config_int(config, "CPX_C101", "max_ctes", 8),
        max_joins=_config_int(config, "CPX_C102", "max_joins", DEFAULT_MAX_JOINS),
        max_subquery_depth=_config_int(config, "CPX_C103", "max_subquery_depth", 3),
        max_case_expressions=_config_int(config, "CPX_C104", "max_case_expressions", 10),
        max_boolean_operators=_config_int(config, "CPX_C105", "max_boolean_operators", 20),
        max_window_functions=_config_int(config, "CPX_C106", "max_window_functions", 10),
        max_complexity_score=_config_int(
            config,
            "CPX_C201",
            "max_complexity_score",
            DEFAULT_MAX_COMPLEXITY_SCORE,
        ),
    )


def _metrics_dict(metrics: ComplexityMetrics) -> dict[str, int]:
    return {
        "boolean_operators": metrics.boolean_operators,
        "case_expressions": metrics.case_expressions,
        "ctes": metrics.ctes,
        "joins": metrics.joins,
        "subqueries": metrics.subqueries,
        "subquery_depth": metrics.subquery_depth,
        "window_functions": metrics.window_functions,
    }


def _json_entry(entry: ReportEntry) -> dict[str, object]:
    legacy: list[dict[str, object]] = []
    detail: list[dict[str, object]] = []
    for finding in entry.findings:
        legacy.append(
            {"level": finding.level, "message": finding.message, "rule_id": finding.rule_id},
        )
        detail.append(_finding_to_canonical_dict(finding))
    base: dict[str, object] = {
        "errors": list(entry.errors),
        "findings": legacy,
        "findings_detail": detail,
        "path": str(entry.path),
    }
    if entry.metrics is None or entry.score is None:
        base["metrics"] = None
        base["score"] = None
        return base
    base["metrics"] = _metrics_dict(entry.metrics)
    base["score"] = entry.score
    return base


def _format_console_entry(entry: ReportEntry) -> list[str]:
    if entry.errors:
        detail = "; ".join(entry.errors)
        return [f"{entry.path} ERROR {detail}"]

    if entry.metrics is None or entry.score is None:
        return [f"{entry.path} ERROR Missing metrics."]

    metrics = entry.metrics
    lines = [
        (
            f"{entry.path} {entry.score} {metrics.ctes} {metrics.joins} "
            f"{metrics.subquery_depth} {metrics.case_expressions} "
            f"{metrics.boolean_operators} {metrics.window_functions}"
        ),
    ]
    for finding in entry.findings:
        if finding.rule_id == "CPX_PARSE_ERROR":
            lines.append(f"  {finding.rule_id}: {finding.message}")
        else:
            summ = (
                format_contributor_summary(finding.contributors, limit=3)
                if finding.contributors
                else ""
            )
            extra = f" [{summ}]" if summ else ""
            lines.append(f"  {finding.rule_id}: {finding.message}{extra}")
    return lines
