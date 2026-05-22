"""Report generation for SQL complexity metrics."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING

from sqlfluff.core import FluffConfig, Linter
from sqlfluff.core.parser.segments.base import BaseSegment

from sqlfluff_complexity import __version__
from sqlfluff_complexity.core.analysis import (
    MetricContributor,
    format_contributor_summary,
    segment_position,
)
from sqlfluff_complexity.core.config.cpx_config import contributor_display_settings
from sqlfluff_complexity.core.config.policy import (
    CPX_GLOBAL_CONFIG_SECTION,
    POLICY_MODES,
    ComplexityPolicy,
    resolve_policy,
    threshold_policy_from_fluff_config,
)
from sqlfluff_complexity.core.config.rule_registry import REPORT_LIMITS, ReportLimit
from sqlfluff_complexity.core.config.scoring import DEFAULT_WEIGHTS, parse_weights
from sqlfluff_complexity.core.messages.c201_messages import (
    C201ViolationParams,
    build_c201_violation_message,
    pick_c201_report_contributors,
)
from sqlfluff_complexity.core.messages.findings import ComplexityFinding, SourceLocation
from sqlfluff_complexity.core.messages.remediation import remediation_for_rule
from sqlfluff_complexity.core.messages.violation_messages import (
    MetricThresholdViolationParams,
    metric_threshold_violation_message_and_picked,
)
from sqlfluff_complexity.core.model.metrics import ComplexityMetrics
from sqlfluff_complexity.core.scan.segment_tree import analyze_segment_tree
from sqlfluff_complexity.reporting.html import format_html_report as _format_html_report
from sqlfluff_complexity.reporting.json import findings_to_json_payload
from sqlfluff_complexity.reporting.sarif import findings_to_sarif_payload

if TYPE_CHECKING:
    from sqlfluff.core.types import ConfigMappingType


def _default_complexity_weights() -> dict[str, int]:
    return DEFAULT_WEIGHTS.copy()


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
    complexity_weights: dict[str, int] = field(default_factory=_default_complexity_weights)
    scan_roots: tuple[str, ...] = ()

    @property
    def has_errors(self) -> bool:
        """Return whether any input failed to parse or load."""
        return any(entry.errors for entry in self.entries)


def _sql_files_under(root: Path) -> list[Path]:
    """Return regular files under ``root`` whose suffix is ``.sql`` (case-insensitive)."""
    if not root.is_dir():
        return []
    return [candidate for candidate in root.rglob("*") if candidate.is_file() and candidate.suffix.lower() == ".sql"]


def _dedupe_paths_stable(paths: Sequence[Path]) -> list[Path]:
    """Deduplicate paths by resolved location and return sorted by ``str(path)``."""
    seen: dict[str, Path] = {}
    for path in paths:
        try:
            key = str(path.resolve(strict=False))
        except OSError:
            key = str(path)
        if key not in seen:
            seen[key] = path
    return sorted(seen.values(), key=str)


def expand_report_paths(paths: Sequence[Path], *, recursive: bool) -> list[Path]:
    """Return concrete paths to pass to :func:`analyze_paths`.

    When ``recursive`` is false, returns ``paths`` unchanged (caller may validate).

    When ``recursive`` is true, each file argument is kept as-is; each directory is
    expanded to all nested ``*.sql`` files (suffix matched case-insensitively). The
    result is deduplicated and sorted for deterministic output.
    """
    if not recursive:
        return list(paths)

    collected: list[Path] = []
    for path in paths:
        if path.is_dir():
            collected.extend(_sql_files_under(path))
        else:
            collected.append(path)

    return _dedupe_paths_stable(collected)


def cli_scan_roots(paths: Sequence[Path]) -> tuple[str, ...]:
    """Directory roots from ``report`` CLI path arguments (before expansion).

    Uses ``absolute()`` rather than ``resolve()`` so roots match ``entry.path`` on macOS ``/tmp``.
    """
    roots = {str(path.absolute() if path.is_dir() else path.parent.absolute()) for path in paths}
    return tuple(sorted(roots, key=lambda item: (-len(item), item)))


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

    message, picked, rem = metric_threshold_violation_message_and_picked(
        MetricThresholdViolationParams(
            rule_id=limit_spec.rule_id,
            description_label=limit_spec.message_label,
            actual=actual,
            config_key=limit_spec.config_key,
            limit=max_allowed,
            metric_name=limit_spec.metric_name,
            contributors=contributors,
            max_contributors=max_contributors,
            show_contributors=show_contributors,
        ),
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
    loc = _anchored_location(
        path_s=path_s,
        root_line=line,
        root_col=col,
        metric_key=None,
        contributors=contributors,
    )

    message = build_c201_violation_message(
        C201ViolationParams(
            score=score,
            limit=threshold,
            metrics=metrics,
            weights=weights,
            contributors=contributors,
            show_contributors=show_c201,
            max_contributors=max_c201,
        ),
    )
    picked: tuple[MetricContributor, ...] = ()
    if show_c201 and max_c201 >= 1:
        picked = pick_c201_report_contributors(contributors, weights, max_items=max_c201)

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


def _weights_from_config(config: FluffConfig) -> dict[str, int]:
    raw_weights = config.get("complexity_weights", section=CPX_GLOBAL_CONFIG_SECTION, default=None)
    return parse_weights(raw_weights)


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


def _policy_for_path(config: FluffConfig, path: Path) -> ComplexityPolicy:
    base_policy = threshold_policy_from_fluff_config(config)
    raw_overrides = config.get("path_overrides", section=CPX_GLOBAL_CONFIG_SECTION, default="")
    return resolve_policy(base_policy, raw_overrides, str(path))


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


def _build_config(dialect: str, config_path: Path | None) -> FluffConfig:
    overrides: ConfigMappingType = {"dialect": dialect}
    if config_path is None:
        return FluffConfig.from_kwargs(dialect=dialect)
    return FluffConfig.from_root(extra_config_path=str(config_path), overrides=overrides)


def analyze_paths(paths: Sequence[Path], *, dialect: str, config_path: Path | None = None) -> ComplexityReport:
    """Analyze SQL file paths with SQLFluff and collect complexity metrics."""
    config = _build_config(dialect=dialect, config_path=config_path)
    linter = Linter(config=config)
    weights = _weights_from_config(config)
    return ComplexityReport(
        entries=[_analyze_path(path, linter, config) for path in paths],
        complexity_weights=weights,
    )


def _console_message_line(rule_id: str, message: str) -> str:
    """Avoid ``RULE: RULE: ...`` when ``message`` already includes the rule prefix."""
    prefix = f"{rule_id}: "
    if message.startswith(prefix):
        return message
    return f"{prefix}{message}"


def _format_console_entry(entry: ReportEntry) -> list[str]:
    if entry.errors:
        detail = "; ".join(entry.errors)
        return [f"{entry.path} ERROR {detail}"]

    if entry.metrics is None or entry.score is None:
        return [f"{entry.path} ERROR Missing metrics."]

    metrics = entry.metrics
    header_line = (
        f"{entry.path} {entry.score} {metrics.ctes} {metrics.joins} "
        f"{metrics.subquery_depth} {metrics.case_expressions} "
        f"{metrics.boolean_operators} {metrics.window_functions} "
        f"{metrics.cte_dependency_depth} {metrics.set_operation_count} "
        f"{metrics.expression_depth} {metrics.derived_tables}"
    )
    lines = [header_line]
    for finding in entry.findings:
        if finding.rule_id == "CPX_PARSE_ERROR":
            lines.append(f"  {finding.rule_id}: {finding.message}")
        else:
            summ = format_contributor_summary(finding.contributors, limit=3) if finding.contributors else ""
            extra = f" [{summ}]" if summ else ""
            lines.append(f"  {_console_message_line(finding.rule_id, finding.message)}{extra}")
    return lines


def format_console_report(report: ComplexityReport) -> str:
    """Format a complexity report for terminal output."""
    column_headers = (
        "path score ctes joins subquery_depth case_expressions boolean_operators window_functions "
        "cte_dependency_depth set_operation_count expression_depth derived_tables"
    )
    lines = [
        "sqlfluff-complexity report",
        column_headers,
    ]
    for entry in report.entries:
        lines.extend(_format_console_entry(entry))
    return "\n".join(lines)


def format_sarif_report(report: ComplexityReport) -> str:
    """Format a complexity report as SARIF 2.1.0 JSON."""
    all_findings = [f for e in report.entries for f in e.findings]
    sarif = findings_to_sarif_payload(all_findings)
    return json.dumps(sarif, indent=2, sort_keys=True)


def format_html_report(report: ComplexityReport) -> str:
    """Format a complexity report as a standalone interactive HTML dashboard."""
    return _format_html_report(report)


def _finding_to_canonical_dict(finding: ComplexityFinding) -> dict[str, object]:
    return findings_to_json_payload((finding,))["findings"][0]


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
    base["metrics"] = entry.metrics.to_report_counters()
    base["score"] = entry.score
    return base


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


def analyze_paths_findings(
    paths: Sequence[Path], *, dialect: str, config_path: Path | None = None
) -> list[ComplexityFinding]:
    """Return flat ComplexityFinding list for all paths (canonical API)."""
    report = analyze_paths(paths, dialect=dialect, config_path=config_path)
    return [f for e in report.entries for f in e.findings]


def load_fluff_config(*, dialect: str, config_path: Path | None = None) -> FluffConfig:
    """Load a FluffConfig the same way as the report command."""
    return _build_config(dialect=dialect, config_path=config_path)


def validate_cpx_plugin_config(config: FluffConfig) -> None:
    """Validate CPX-related config keys using existing parsers.

    Raises ValueError with a clear message on invalid weights or path overrides.
    """
    parse_weights(config.get("complexity_weights", section=CPX_GLOBAL_CONFIG_SECTION, default=None))
    raw_overrides = config.get("path_overrides", section=CPX_GLOBAL_CONFIG_SECTION, default="")
    mode = str(config.get("mode", section=CPX_GLOBAL_CONFIG_SECTION, default="enforce"))
    if mode not in POLICY_MODES:
        message = f"Complexity policy mode must be one of {sorted(POLICY_MODES)}."
        raise ValueError(message)
    base_policy = replace(threshold_policy_from_fluff_config(config), mode=mode)
    resolve_policy(base_policy, raw_overrides, "__config_check__.sql")


__all__ = (
    "ComplexityReport",
    "ReportEntry",
    "analyze_paths",
    "analyze_paths_findings",
    "cli_scan_roots",
    "expand_report_paths",
    "format_console_report",
    "format_html_report",
    "format_json_report",
    "format_sarif_report",
    "load_fluff_config",
    "validate_cpx_plugin_config",
)
