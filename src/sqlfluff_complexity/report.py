"""Report generation for SQL complexity metrics."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sqlfluff.core import FluffConfig, Linter

from sqlfluff_complexity.core.policy import ComplexityPolicy, resolve_policy
from sqlfluff_complexity.core.scoring import parse_weights
from sqlfluff_complexity.core.segment_tree import collect_metrics

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from sqlfluff.core.types import ConfigMappingType

    from sqlfluff_complexity.core.metrics import ComplexityMetrics


DEFAULT_MAX_JOINS = 8
DEFAULT_MAX_COMPLEXITY_SCORE = 60
SARIF_SCHEMA_URL = "https://json.schemastore.org/sarif-2.1.0.json"


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
class ReportFinding:
    """One report finding for a parsed SQL file."""

    rule_id: str
    level: str
    message: str


@dataclass(frozen=True)
class ReportEntry:
    """Complexity report data for one SQL file path."""

    path: Path
    metrics: ComplexityMetrics | None = None
    score: int | None = None
    findings: list[ReportFinding] = field(default_factory=list)
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
    sarif = {
        "version": "2.1.0",
        "$schema": SARIF_SCHEMA_URL,
        "runs": [
            {
                "tool": {"driver": {"name": "sqlfluff-complexity", "rules": _sarif_rules()}},
                "results": _sarif_results(report),
            },
        ],
    }
    return json.dumps(sarif, indent=2, sort_keys=True)


def _analyze_path(path: Path, linter: Linter, config: FluffConfig) -> ReportEntry:
    try:
        sql = path.read_text(encoding="utf-8")
    except OSError as exc:
        return ReportEntry(path=path, errors=[f"Could not read file: {exc}"])

    parsed = linter.parse_string(sql, fname=str(path))
    parse_errors = [violation.desc() for violation in parsed.violations]
    if parse_errors or parsed.tree is None:
        return ReportEntry(
            path=path, errors=parse_errors or ["SQLFluff did not return a parse tree."]
        )

    metrics = collect_metrics(parsed.tree)
    policy = _policy_for_path(config, path)
    score = metrics.score(_weights_from_config(config))
    return ReportEntry(
        path=path, metrics=metrics, score=score, findings=_findings(metrics, score, policy)
    )


def _build_config(dialect: str, config_path: Path | None) -> FluffConfig:
    overrides: ConfigMappingType = {"dialect": dialect}
    if config_path is None:
        return FluffConfig.from_kwargs(dialect=dialect)
    return FluffConfig.from_root(extra_config_path=str(config_path), overrides=overrides)


def _findings(
    metrics: ComplexityMetrics,
    score: int,
    policy: ComplexityPolicy,
) -> list[ReportFinding]:
    findings = [_metric_finding(metrics, policy, limit) for limit in REPORT_LIMITS]
    findings = [finding for finding in findings if finding is not None]
    if score > policy.max_complexity_score:
        findings.append(
            ReportFinding(
                rule_id="CPX_C201",
                level="warning",
                message=(
                    f"Aggregate complexity score {score} exceeds "
                    f"max_complexity_score={policy.max_complexity_score}."
                ),
            ),
        )
    return findings


def _metric_finding(
    metrics: ComplexityMetrics,
    policy: ComplexityPolicy,
    limit: ReportLimit,
) -> ReportFinding | None:
    actual = int(getattr(metrics, limit.metric_name))
    max_allowed = int(getattr(policy, limit.policy_key))
    if actual <= max_allowed:
        return None
    return ReportFinding(
        rule_id=limit.rule_id,
        level="warning",
        message=f"{limit.label} {actual} exceeds {limit.config_key}={max_allowed}.",
    )


def _policy_for_path(config: FluffConfig, path: Path) -> ComplexityPolicy:
    base_policy = ComplexityPolicy(
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
    raw_overrides = config.get("path_overrides", section=("rules", "CPX_C201"), default="")
    return resolve_policy(base_policy, raw_overrides, str(path))


def _weights_from_config(config: FluffConfig) -> dict[str, int]:
    raw_weights = config.get("complexity_weights", section=("rules", "CPX_C201"), default=None)
    return parse_weights(raw_weights)


def _config_int(config: FluffConfig, rule_code: str, key: str, default: int) -> int:
    value = config.get(key, section=("rules", rule_code), default=default)
    return int(value)


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
    lines.extend(f"  {finding.rule_id}: {finding.message}" for finding in entry.findings)
    return lines


def _sarif_rules() -> list[dict[str, object]]:
    return [
        {"id": "CPX_C101", "name": "Too many CTEs"},
        {"id": "CPX_C102", "name": "Too many JOIN clauses"},
        {"id": "CPX_C103", "name": "Nested subquery depth too high"},
        {"id": "CPX_C104", "name": "Too many CASE expressions"},
        {"id": "CPX_C105", "name": "Boolean operator complexity too high"},
        {"id": "CPX_C106", "name": "Too many window functions"},
        {"id": "CPX_C201", "name": "Aggregate complexity score too high"},
        {"id": "CPX_PARSE_ERROR", "name": "SQLFluff parse error"},
    ]


def _sarif_results(report: ComplexityReport) -> list[dict[str, object]]:
    results = []
    for entry in report.entries:
        results.extend(_sarif_error_results(entry))
        results.extend(_sarif_finding_result(entry, finding) for finding in entry.findings)
    return results


def _sarif_error_results(entry: ReportEntry) -> list[dict[str, object]]:
    return [
        _sarif_result(
            path=entry.path,
            rule_id="CPX_PARSE_ERROR",
            level="error",
            message=message,
        )
        for message in entry.errors
    ]


def _sarif_finding_result(entry: ReportEntry, finding: ReportFinding) -> dict[str, object]:
    return _sarif_result(
        path=entry.path,
        rule_id=finding.rule_id,
        level=finding.level,
        message=finding.message,
    )


def _sarif_result(path: Path, rule_id: str, level: str, message: str) -> dict[str, object]:
    return {
        "ruleId": rule_id,
        "level": level,
        "message": {"text": message},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": str(path)},
                },
            },
        ],
    }
