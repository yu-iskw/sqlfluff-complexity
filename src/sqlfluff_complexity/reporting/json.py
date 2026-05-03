"""Canonical JSON report built from ComplexityFinding objects."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, TextIO

from sqlfluff_complexity import __version__
from sqlfluff_complexity.core.analysis import MetricContributor
from sqlfluff_complexity.core.findings import ComplexityFinding


def _contributor_dict(contributor: MetricContributor) -> dict[str, Any]:
    return {
        "column": contributor.column,
        "line": contributor.line,
        "metric": contributor.metric,
        "raw": contributor.raw,
        "reason": contributor.reason,
        "segment_type": contributor.segment_type,
    }


def _finding_dict(finding: ComplexityFinding) -> dict[str, Any]:
    return {
        "aggregate_score": finding.aggregate_score,
        "column": finding.location.column,
        "contributors": [_contributor_dict(c) for c in finding.contributors],
        "level": finding.level,
        "line": finding.location.line,
        "message": finding.message,
        "metric": finding.metric,
        "metrics": finding.metrics.to_report_counters(),
        "path": finding.location.path,
        "remediation": finding.remediation,
        "rule_id": finding.rule_id,
        "score": finding.score,
        "threshold": finding.threshold,
    }


def findings_to_json_payload(
    findings: Sequence[ComplexityFinding],
) -> dict[str, Any]:
    """Build a stable top-level JSON object for ``findings`` only."""
    return {
        "findings": [_finding_dict(f) for f in findings],
        "version": __version__,
    }


def write_json_report(
    findings: Sequence[ComplexityFinding],
    output: TextIO,
) -> None:
    """Write canonical JSON (pretty-printed, sorted keys) to ``output``."""
    payload = findings_to_json_payload(findings)
    output.write(json.dumps(payload, indent=2, sort_keys=True))
    output.write("\n")
