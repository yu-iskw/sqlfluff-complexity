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

"""Standalone interactive HTML report for SQL complexity findings.

The generated artifact is metadata-only: it contains paths, metrics, scores,
findings, remediation hints, and contributor snippets already produced by the
analysis pipeline. It never reads SQL source files when rendering, never makes
network requests, and never depends on the ``sqlfluff_complexity`` package once
written to disk.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from html import escape
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlfluff_complexity import __version__

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from typing import Protocol

    from sqlfluff_complexity.core.analysis import MetricContributor
    from sqlfluff_complexity.core.messages.findings import ComplexityFinding

    class ReportEntryLike(Protocol):
        """Report entry shape consumed by the HTML renderer."""

        @property
        def path(self) -> Path:
            raise NotImplementedError

        @property
        def score(self) -> int | None:
            raise NotImplementedError

        @property
        def metrics(self) -> Any:
            raise NotImplementedError

        @property
        def findings(self) -> Sequence[ComplexityFinding]:
            raise NotImplementedError

        @property
        def errors(self) -> Sequence[str]:
            raise NotImplementedError

    class ComplexityReportLike(Protocol):
        """Report shape consumed by the HTML renderer."""

        @property
        def entries(self) -> Sequence[ReportEntryLike]:
            raise NotImplementedError


HTML_VIEW_SCHEMA_VERSION = "html-view-1"
PARSE_ERROR_RULE_ID = "CPX_PARSE_ERROR"

_SCORE_BUCKET_WIDTH = 10
_SCORE_BUCKET_COUNT = 10  # 0-9, 10-19, ..., 90-99 plus an overflow "100+" bucket
_REPORT_TITLE = "sqlfluff-complexity report"


def _directory_key(path: Path) -> str:
    parent = str(path.parent)
    return parent or "."


def _entry_payload(index: int, entry: ReportEntryLike) -> dict[str, Any]:
    metrics = entry.metrics.to_report_counters() if entry.metrics is not None else None
    return {
        "id": index,
        "path": str(entry.path),
        "directory": _directory_key(entry.path),
        "filename": entry.path.name,
        "score": entry.score,
        "metrics": metrics,
        "finding_count": len(entry.findings),
        "error_count": len(entry.errors),
        "has_errors": bool(entry.errors),
    }


def _contributor_payload(contributor: MetricContributor) -> dict[str, Any]:
    return {
        "line": contributor.line,
        "column": contributor.column,
        "metric": contributor.metric,
        "reason": contributor.reason,
        "segment_type": contributor.segment_type,
        "raw": contributor.raw,
    }


def _finding_payload(entry_id: int, finding: ComplexityFinding) -> dict[str, Any]:
    return {
        "entry_id": entry_id,
        "rule_id": finding.rule_id,
        "metric": finding.metric,
        "severity": finding.severity,
        "level": finding.level,
        "line": finding.location.line,
        "column": finding.location.column,
        "score": finding.score,
        "threshold": finding.threshold,
        "aggregate_score": finding.aggregate_score,
        "message": finding.message,
        "remediation": finding.remediation,
        "contributors": [_contributor_payload(c) for c in finding.contributors],
    }


def _median(values: Sequence[int]) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) // 2


def _percentile_nearest_rank(values: Sequence[int], percentile: float) -> int | None:
    if not values:
        return None
    rank = int(len(values) * percentile + 0.999999) - 1
    index = max(0, min(len(values) - 1, rank))
    return values[index]


def _summary_payload(
    entries: Sequence[ReportEntryLike],
    findings: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    parse_error_count = sum(1 for f in findings if f["rule_id"] == PARSE_ERROR_RULE_ID)
    files_with_findings = sum(1 for entry in entries if any(f.rule_id != PARSE_ERROR_RULE_ID for f in entry.findings))
    files_with_errors = sum(1 for entry in entries if entry.errors)
    scores = sorted(entry.score for entry in entries if entry.score is not None)
    finding_count = len(findings)
    return {
        "file_count": len(entries),
        "finding_count": finding_count,
        "parse_error_count": parse_error_count,
        "files_with_findings": files_with_findings,
        "files_with_errors": files_with_errors,
        "scored_file_count": len(scores),
        "max_score": max(scores) if scores else None,
        "median_score": _median(scores) if scores else None,
        "p95_score": _percentile_nearest_rank(scores, 0.95),
    }


def _bucket_record(index: int, count: int) -> dict[str, Any]:
    if index >= _SCORE_BUCKET_COUNT:
        lower = _SCORE_BUCKET_COUNT * _SCORE_BUCKET_WIDTH
        return {"label": f"{lower}+", "min": lower, "max": None, "count": count}
    lower = index * _SCORE_BUCKET_WIDTH
    upper = lower + _SCORE_BUCKET_WIDTH - 1
    return {"label": f"{lower}-{upper}", "min": lower, "max": upper, "count": count}


def _score_buckets(entries: Iterable[ReportEntryLike]) -> list[dict[str, Any]]:
    counter: Counter[int] = Counter()
    for entry in entries:
        if entry.score is None:
            continue
        bucket_index = min(entry.score // _SCORE_BUCKET_WIDTH, _SCORE_BUCKET_COUNT)
        counter[bucket_index] += 1
    return [_bucket_record(index, counter.get(index, 0)) for index in range(_SCORE_BUCKET_COUNT + 1)]


def _empty_rollup() -> dict[str, int]:
    return {"file_count": 0, "finding_count": 0, "max_score": 0, "error_count": 0}


def _directory_rollups(entries: Iterable[ReportEntryLike]) -> list[dict[str, Any]]:
    """Aggregate file counts, finding counts, and max score by directory."""
    rollup: defaultdict[str, dict[str, int]] = defaultdict(_empty_rollup)
    for entry in entries:
        bucket = rollup[_directory_key(entry.path)]
        bucket["file_count"] += 1
        bucket["finding_count"] += len(entry.findings)
        if entry.score is not None and entry.score > bucket["max_score"]:
            bucket["max_score"] = entry.score
        if entry.errors:
            bucket["error_count"] += 1
    rows = [
        {
            "path": directory,
            "files": stats["file_count"],
            "findings": stats["finding_count"],
            "max_score": stats["max_score"],
            "error_count": stats["error_count"],
        }
        for directory, stats in rollup.items()
    ]
    rows.sort(
        key=lambda row: (
            -int(row["findings"]),
            -int(row["max_score"]),
            str(row["path"]),
        ),
    )
    return rows


def _rule_rollups(findings: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    files_by_rule: defaultdict[str, set[int]] = defaultdict(set)
    for finding in findings:
        rule_id = str(finding["rule_id"])
        counter[rule_id] += 1
        files_by_rule[rule_id].add(int(finding["entry_id"]))
    return [
        {
            "rule_id": rule_id,
            "findings": count,
            "files": len(files_by_rule[rule_id]),
        }
        for rule_id, count in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]


def build_html_report_payload(report: ComplexityReportLike) -> dict[str, Any]:
    """Build the internal HTML view payload (not a public schema)."""
    entries = [_entry_payload(index, entry) for index, entry in enumerate(report.entries)]
    findings = [
        _finding_payload(entry_index, finding)
        for entry_index, entry in enumerate(report.entries)
        for finding in entry.findings
    ]
    return {
        "metadata": {
            "schema_version": HTML_VIEW_SCHEMA_VERSION,
            "title": _REPORT_TITLE,
            "tool": "sqlfluff-complexity",
            "version": __version__,
        },
        "summary": _summary_payload(report.entries, findings),
        "score_buckets": _score_buckets(report.entries),
        "directories": _directory_rollups(report.entries),
        "rules": _rule_rollups(findings),
        "entries": entries,
        "findings": findings,
    }


def _safe_json_for_script(payload: dict[str, Any]) -> str:
    """Serialize ``payload`` so it cannot break out of a ``<script>`` tag.

    ``json.dumps`` already escapes backslashes, so we only neutralize HTML-meaningful
    bytes plus the JS-line-terminator code points U+2028 and U+2029.
    """
    return (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _asset_text(name: str) -> str:
    return (Path(__file__).parent / "assets" / name).read_text(encoding="utf-8")


def render_html_report(payload: dict[str, Any]) -> str:
    """Inline CSS/JS assets and embed ``payload`` into one HTML document."""
    css = _asset_text("html_report.css")
    js = _asset_text("html_report.js")
    data = _safe_json_for_script(payload)
    title = escape(_REPORT_TITLE)
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>{title}</title>\n"
        f"  <style>{css}</style>\n"
        "</head>\n"
        "<body>\n"
        '  <main id="app">\n'
        "    <noscript>This report requires JavaScript for filtering and drill-down.</noscript>\n"
        "  </main>\n"
        f'  <script id="report-data" type="application/json">{data}</script>\n'
        f"  <script>{js}</script>\n"
        "</body>\n"
        "</html>\n"
    )


def format_html_report(report: ComplexityReportLike) -> str:
    """Render a standalone HTML dashboard for ``report``."""
    payload = build_html_report_payload(report)
    return render_html_report(payload)
