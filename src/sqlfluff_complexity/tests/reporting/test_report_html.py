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

"""Tests for the standalone HTML report formatter."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sqlfluff_complexity.core.model.metrics import ComplexityMetrics
from sqlfluff_complexity.report import (
    ComplexityReport,
    ReportEntry,
    analyze_paths,
    format_html_report,
)
from sqlfluff_complexity.reporting.html import (
    HTML_VIEW_SCHEMA_VERSION,
    build_html_report_payload,
    render_html_report,
)

_REPORT_DATA_RE = re.compile(
    r'<script id="report-data" type="application/json">(.*?)</script>',
    re.DOTALL,
)


def _extract_embedded_payload(html: str) -> dict[str, Any]:
    match = _REPORT_DATA_RE.search(html)
    assert match is not None, "Embedded report-data script tag missing"
    return json.loads(match.group(1))


def test_html_payload_includes_summary_entries_and_findings(tmp_path: Path) -> None:
    """Payload exposes summary, entries, findings, and version metadata."""
    sql_file = tmp_path / "model.sql"
    sql_file.write_text(
        "select * from a join b on a.id = b.id\n",
        encoding="utf-8",
    )
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text("[sqlfluff:rules:CPX_C102]\nmax_joins = 0\n", encoding="utf-8")

    report = analyze_paths([sql_file], dialect="ansi", config_path=cfg)
    payload = build_html_report_payload(report)

    assert payload["metadata"]["schema_version"] == HTML_VIEW_SCHEMA_VERSION
    assert payload["metadata"]["tool"] == "sqlfluff-complexity"
    assert payload["summary"]["file_count"] == 1
    assert payload["summary"]["finding_count"] >= 1
    assert payload["entries"][0]["path"] == str(sql_file)
    assert payload["findings"][0]["rule_id"] == "CPX_C102"
    rule_ids = {rule["rule_id"] for rule in payload["rules"]}
    assert "CPX_C102" in rule_ids


def test_format_html_report_outputs_standalone_document(tmp_path: Path) -> None:
    """Generated HTML is self-contained: no external links, scripts, or fetch calls."""
    sql_file = tmp_path / "model.sql"
    sql_file.write_text("select 1\n", encoding="utf-8")

    html = format_html_report(analyze_paths([sql_file], dialect="ansi"))

    assert html.startswith("<!doctype html>")
    assert "<style>" in html
    assert '<script id="report-data" type="application/json">' in html
    assert "<script src=" not in html
    assert "<link rel=" not in html
    assert "fetch(" not in html
    assert "https://" not in html
    assert "http://" not in html


def test_html_report_escapes_script_breaking_sequences() -> None:
    """Embedded JSON must escape ``</script>`` so it cannot break out of the script tag."""
    raw_path = "</script><script>alert(1)</script>"
    html = render_html_report(
        {
            "metadata": {"schema_version": HTML_VIEW_SCHEMA_VERSION, "tool": "sqlfluff-complexity"},
            "summary": {},
            "score_buckets": [],
            "directories": [],
            "rules": [],
            "entries": [{"id": 0, "path": raw_path}],
            "findings": [],
        },
    )

    assert raw_path not in html
    assert (
        "</script>"
        not in html.split('<script id="report-data"', 1)[1].split(
            "</script>",
            1,
        )[0]
    )
    payload = _extract_embedded_payload(html)
    assert payload["entries"][0]["path"] == raw_path


def test_html_report_does_not_embed_full_sql_source_by_default(tmp_path: Path) -> None:
    """The HTML report should only include parse-tree metadata, not file contents."""
    sql_file = tmp_path / "secret_model.sql"
    marker = "html-report-source-marker"
    sql_file.write_text(
        "-- " + marker + "\nselect 1\n",
        encoding="utf-8",
    )

    html = format_html_report(analyze_paths([sql_file], dialect="ansi"))

    assert marker not in html
    assert str(sql_file) in html


def test_html_report_records_parse_errors(tmp_path: Path) -> None:
    """Parse errors should appear in entries and findings with null metrics/score."""
    sql_file = tmp_path / "bad.sql"
    sql_file.write_text("select from\n", encoding="utf-8")

    report = analyze_paths([sql_file], dialect="ansi")
    payload = build_html_report_payload(report)

    entry = payload["entries"][0]
    assert entry["score"] is None
    assert entry["metrics"] is None
    assert entry["has_errors"] is True
    rule_ids = {finding["rule_id"] for finding in payload["findings"]}
    assert "CPX_PARSE_ERROR" in rule_ids
    assert payload["summary"]["parse_error_count"] >= 1


def test_html_payload_handles_large_report_shape() -> None:
    """Payload construction should comfortably support 10,000+ files."""
    entries = [
        ReportEntry(
            path=Path(f"models/mart/dir_{index % 25}/model_{index}.sql"),
            metrics=ComplexityMetrics(joins=index % 7),
            score=index % 100,
        )
        for index in range(10_000)
    ]
    report = ComplexityReport(entries=entries)

    payload = build_html_report_payload(report)

    assert payload["summary"]["file_count"] == 10_000
    assert len(payload["entries"]) == 10_000
    assert payload["directories"], "Directory rollups should be precomputed"
    assert payload["score_buckets"], "Score distribution should be precomputed"
    assert payload["summary"]["finding_count"] == 0
    bucket_total = sum(bucket["count"] for bucket in payload["score_buckets"])
    assert bucket_total == 10_000


def test_html_assets_are_inlined(tmp_path: Path) -> None:
    """CSS and JS assets should be inlined so the report is offline-portable."""
    sql_file = tmp_path / "model.sql"
    sql_file.write_text("select 1\n", encoding="utf-8")

    html = format_html_report(analyze_paths([sql_file], dialect="ansi"))

    assert "</style>" in html
    style_block = html.split("<style>", 1)[1].split("</style>", 1)[0]
    assert style_block.strip(), "CSS asset should be inlined and non-empty"

    after_data = html.split('id="report-data"', 1)[1]
    script_block = after_data.split("<script>", 1)[1].split("</script>", 1)[0]
    assert script_block.strip(), "JavaScript asset should be inlined and non-empty"
    assert "init" in script_block, "Inlined JS should expose the dashboard init function"
