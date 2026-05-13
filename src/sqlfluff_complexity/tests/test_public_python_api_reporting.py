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

"""Smoke tests for the documented public reporting API."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import sqlfluff_complexity.report as report_module

if TYPE_CHECKING:
    from pathlib import Path


def test_report_module___all___matches_documented_public_names() -> None:
    """Guard the documented stable surface (see docs/python-api.md, Report command)."""
    expected = {
        "ComplexityReport",
        "ReportEntry",
        "analyze_paths",
        "analyze_paths_findings",
        "expand_report_paths",
        "format_console_report",
        "format_html_report",
        "format_json_report",
        "format_sarif_report",
        "load_fluff_config",
        "validate_cpx_plugin_config",
    }
    assert set(report_module.__all__) == expected


def test_analyze_paths_format_json_report_schema_version(tmp_path: Path) -> None:
    """JSON report from the public API includes schema_version for automation."""
    sql_file = tmp_path / "model.sql"
    sql_file.write_text("select 1\n", encoding="utf-8")

    paths = report_module.expand_report_paths([sql_file], recursive=False)
    report = report_module.analyze_paths(paths, dialect="ansi", config_path=None)
    assert isinstance(report, report_module.ComplexityReport)
    assert len(report.entries) == 1
    assert isinstance(report.entries[0], report_module.ReportEntry)
    assert not report.has_errors

    payload = json.loads(report_module.format_json_report(report))
    assert payload["schema_version"] == "1.1"
    assert payload["tool"] == "sqlfluff-complexity"

    findings = report_module.analyze_paths_findings(paths, dialect="ansi", config_path=None)
    assert isinstance(findings, list)

    sarif = json.loads(report_module.format_sarif_report(report))
    assert sarif["version"] == "2.1.0"

    html = report_module.format_html_report(report)
    assert "<html" in html.lower()

    console = report_module.format_console_report(report)
    assert "sqlfluff-complexity report" in console

    config = report_module.load_fluff_config(dialect="ansi", config_path=None)
    report_module.validate_cpx_plugin_config(config)
