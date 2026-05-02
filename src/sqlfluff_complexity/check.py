"""Compare current analysis results to a saved baseline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from sqlfluff_complexity.core.findings import ComplexityFinding

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from sqlfluff_complexity.baseline import Baseline, BaselineEntry
    from sqlfluff_complexity.core.metrics import ComplexityMetrics
    from sqlfluff_complexity.report import ComplexityReport, ReportEntry

FailOnMode = Literal["regression", "threshold", "none"]

METRIC_KEYS = (
    "boolean_operators",
    "case_expressions",
    "ctes",
    "joins",
    "subqueries",
    "subquery_depth",
    "window_functions",
)


@dataclass(frozen=True)
class CheckSummary:
    """Aggregate counts for a check run."""

    files_checked: int
    regressions: int
    threshold_violations: int
    errors: int


@dataclass(frozen=True)
class CheckRow:
    """One path outcome from comparing current analysis to a baseline."""

    path: str
    status: str
    baseline_score: int | None = None
    current_score: int | None = None
    changed_metrics: dict[str, dict[str, int]] | None = None


@dataclass(frozen=True)
class CheckResult:
    """Full check output for formatting."""

    summary: CheckSummary
    results: tuple[CheckRow, ...] = ()


def _policy_findings(
    findings: list[ComplexityFinding],
) -> list[ComplexityFinding]:
    return [f for f in findings if f.rule_id != "CPX_PARSE_ERROR"]


def _metric_regression(
    baseline_metrics: Mapping[str, int],
    current_metrics: Mapping[str, int],
) -> dict[str, dict[str, int]]:
    changed: dict[str, dict[str, int]] = {}
    for key in METRIC_KEYS:
        b = baseline_metrics.get(key)
        c = current_metrics.get(key)
        if b is None or c is None:
            continue
        if c > b:
            changed[key] = {"baseline": b, "current": c}
    return changed


def _metrics_mapping(metrics: ComplexityMetrics) -> dict[str, int]:
    return {
        "boolean_operators": metrics.boolean_operators,
        "case_expressions": metrics.case_expressions,
        "ctes": metrics.ctes,
        "joins": metrics.joins,
        "subqueries": metrics.subqueries,
        "subquery_depth": metrics.subquery_depth,
        "window_functions": metrics.window_functions,
    }


def _regression_row_for_entry(
    *,
    key: str,
    entry: ReportEntry,
    base_ent: BaselineEntry | None,
) -> CheckRow | None:
    policy_f = _policy_findings(entry.findings)

    if base_ent is None:
        if policy_f:
            return CheckRow(
                path=key,
                status="new_threshold_violation",
                current_score=entry.score,
            )
        return None

    current_metrics = entry.metrics
    current_score = entry.score
    regressed = False
    changed_metrics: dict[str, dict[str, int]] | None = None

    if base_ent.score is not None and current_score is not None and current_score > base_ent.score:
        regressed = True

    if base_ent.metrics is not None and current_metrics is not None:
        cm = _metric_regression(base_ent.metrics, _metrics_mapping(current_metrics))
        if cm:
            regressed = True
            changed_metrics = cm

    if regressed:
        return CheckRow(
            path=key,
            status="regression",
            baseline_score=base_ent.score,
            current_score=current_score,
            changed_metrics=changed_metrics,
        )
    return None


def compare_report_to_baseline(
    report: ComplexityReport,
    *,
    baseline: Baseline,
    path_key: Mapping[Path, str],
    fail_on: FailOnMode,
) -> CheckResult:
    """Compare a fresh report to ``baseline`` according to ``fail_on`` semantics."""
    rows: list[CheckRow] = []
    regressions = 0
    threshold_violations = 0
    errors = 0

    sorted_entries = sorted(report.entries, key=lambda e: path_key[e.path])

    for entry in sorted_entries:
        key = path_key[entry.path]
        base_ent = baseline.entries.get(key)
        parse_failed = bool(entry.errors)

        if parse_failed:
            errors += 1

        policy_f = _policy_findings(entry.findings)

        if fail_on == "threshold" and not parse_failed and policy_f:
            threshold_violations += 1
            rows.append(
                CheckRow(
                    path=key,
                    status="threshold_violation",
                    current_score=entry.score,
                ),
            )
            continue

        if fail_on == "none":
            continue

        if fail_on != "regression":
            continue

        if parse_failed:
            continue

        row = _regression_row_for_entry(key=key, entry=entry, base_ent=base_ent)
        if row is not None:
            regressions += 1
            rows.append(row)

    summary = CheckSummary(
        files_checked=len(sorted_entries),
        regressions=regressions,
        threshold_violations=threshold_violations,
        errors=errors,
    )
    return CheckResult(summary=summary, results=tuple(rows))


def format_check_json(result: CheckResult) -> str:
    """Serialize check output as stable JSON."""
    payload = {
        "results": [
            _check_row_to_dict(row)
            for row in sorted(result.results, key=lambda r: (r.status, r.path))
        ],
        "schema_version": "1.0",
        "summary": {
            "errors": result.summary.errors,
            "files_checked": result.summary.files_checked,
            "regressions": result.summary.regressions,
            "threshold_violations": result.summary.threshold_violations,
        },
        "tool": "sqlfluff-complexity",
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _check_row_to_dict(row: CheckRow) -> dict[str, object]:
    out: dict[str, object] = {"path": row.path, "status": row.status}
    if row.baseline_score is not None:
        out["baseline_score"] = row.baseline_score
    if row.current_score is not None:
        out["current_score"] = row.current_score
    if row.changed_metrics:
        out["changed_metrics"] = {
            k: dict(sorted(v.items())) for k, v in sorted(row.changed_metrics.items())
        }
    return out


def _format_check_result_lines(row: CheckRow) -> list[str]:
    lines: list[str] = []
    if row.status == "regression":
        base_s = row.baseline_score if row.baseline_score is not None else "?"
        cur_s = row.current_score if row.current_score is not None else "?"
        lines.append(f"REGRESSION {row.path} score {base_s} -> {cur_s}")
        if row.changed_metrics:
            for mk, vals in sorted(row.changed_metrics.items()):
                lines.append(f"  {mk}: {vals['baseline']} -> {vals['current']}")
        lines.append("")
        return lines
    if row.status == "new_threshold_violation":
        cur_s = row.current_score if row.current_score is not None else "?"
        lines.append(f"NEW_THRESHOLD_VIOLATION {row.path} score {cur_s}")
        lines.append("")
        return lines
    if row.status == "threshold_violation":
        cur_s = row.current_score if row.current_score is not None else "?"
        lines.append(f"THRESHOLD_VIOLATION {row.path} score {cur_s}")
        lines.append("")
        return lines
    return lines


def format_check_console(result: CheckResult) -> str:
    """Human-readable check summary for terminals."""
    s = result.summary
    lines = [
        "sqlfluff-complexity check",
        f"files_checked: {s.files_checked}",
        f"regressions: {s.regressions}",
        f"threshold_violations: {s.threshold_violations}",
        f"errors: {s.errors}",
        "",
    ]
    for row in sorted(result.results, key=lambda r: (r.status, r.path)):
        lines.extend(_format_check_result_lines(row))
    return "\n".join(lines).rstrip() + "\n"
