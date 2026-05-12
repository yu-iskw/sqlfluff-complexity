"""Tests for severity propagation in report outputs (JSON, SARIF, console)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from sqlfluff_complexity.cli import main
from sqlfluff_complexity.core.config.severity import SeverityLevel
from sqlfluff_complexity.core.messages.findings import ComplexityFinding, SourceLocation
from sqlfluff_complexity.core.model.metrics import ComplexityMetrics
from sqlfluff_complexity.reporting.sarif import _sarif_level

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Unit tests for ComplexityFinding.level type
# ---------------------------------------------------------------------------


def _dummy_finding(level: SeverityLevel) -> ComplexityFinding:
    return ComplexityFinding(
        rule_id="CPX_C102",
        metric="joins",
        message="CPX_C102: join count 5 exceeds max_joins=4.",
        remediation="Split into smaller models.",
        location=SourceLocation(path=None, line=1, column=1),
        metrics=ComplexityMetrics(),
        score=5,
        threshold=4,
        contributors=(),
        level=level,
    )


class TestFindingLevel:
    def test_level_is_severity_level_instance(self) -> None:
        finding = _dummy_finding(SeverityLevel.warning)
        assert isinstance(finding.level, SeverityLevel)

    def test_level_serializes_as_string(self) -> None:
        finding = _dummy_finding(SeverityLevel.warning)
        dumped = json.dumps({"level": finding.level})
        assert '"warning"' in dumped

    def test_level_equals_string(self) -> None:
        finding = _dummy_finding(SeverityLevel.error)
        assert finding.level == "error"

    @pytest.mark.parametrize("level", [SeverityLevel.info, SeverityLevel.warning, SeverityLevel.error])
    def test_all_levels_accepted(self, level: SeverityLevel) -> None:
        finding = _dummy_finding(level)
        assert finding.level is level


# ---------------------------------------------------------------------------
# SARIF level mapping
# ---------------------------------------------------------------------------


class TestSarifLevelMapping:
    def test_info_maps_to_note(self) -> None:
        assert _sarif_level(SeverityLevel.info) == "note"

    def test_warning_unchanged(self) -> None:
        assert _sarif_level(SeverityLevel.warning) == "warning"

    def test_error_unchanged(self) -> None:
        assert _sarif_level(SeverityLevel.error) == "error"

    def test_note_is_valid_sarif_level(self) -> None:
        valid_sarif_levels = {"none", "note", "warning", "error"}
        for level in SeverityLevel:
            sarif = _sarif_level(level)
            assert sarif in valid_sarif_levels, f"{level!r} mapped to invalid SARIF level {sarif!r}"


# ---------------------------------------------------------------------------
# Integration: default severity is warning
# ---------------------------------------------------------------------------


def test_default_finding_level_is_warning(tmp_path: Path) -> None:
    """Without severity config, all metric findings must have level='warning'."""
    sql_file = tmp_path / "model.sql"
    sql_file.write_text(
        "select * from base join t1 on base.id = t1.id join t2 on base.id = t2.id",
        encoding="utf-8",
    )
    out = tmp_path / "out.json"
    main(
        [
            "report",
            "--dialect",
            "ansi",
            "--format",
            "json",
            "--output",
            str(out),
            str(sql_file),
        ]
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    findings = [f for f in payload.get("findings", []) if f["rule_id"] == "CPX_C102"]
    for finding in findings:
        assert finding["level"] == "warning", f"Expected level='warning', got {finding['level']!r}"


def test_severity_error_config_propagates_to_json(tmp_path: Path) -> None:
    """Configuring severity=error for CPX_C102 must produce error-level JSON findings."""
    sql_file = tmp_path / "model.sql"
    sql_file.write_text(
        "select * from base join t1 on base.id = t1.id join t2 on base.id = t2.id",
        encoding="utf-8",
    )
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        "[sqlfluff:rules:CPX_C102]\nmax_joins = 1\nseverity = error\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.json"
    main(
        [
            "report",
            "--dialect",
            "ansi",
            "--config",
            str(cfg),
            "--format",
            "json",
            "--output",
            str(out),
            str(sql_file),
        ]
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    c102_findings = [f for f in payload.get("findings", []) if f["rule_id"] == "CPX_C102"]
    assert c102_findings, "Expected at least one CPX_C102 finding"
    for finding in c102_findings:
        assert finding["level"] == "error", (
            f"Expected level='error' with severity=error config; got {finding['level']!r}"
        )


def test_severity_band_escalates_to_error(tmp_path: Path) -> None:
    """A severity_band with threshold=2 should produce error when joins=3."""
    sql_file = tmp_path / "model.sql"
    sql_file.write_text(
        "select * from a join b on a.id=b.id join c on a.id=c.id join d on a.id=d.id",
        encoding="utf-8",
    )
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        "[sqlfluff:rules:CPX_C102]\nmax_joins = 1\nseverity = warning\n"
        'severity_bands = [{"threshold": 3, "severity": "error"}]\n',
        encoding="utf-8",
    )
    out = tmp_path / "out.json"
    main(
        [
            "report",
            "--dialect",
            "ansi",
            "--config",
            str(cfg),
            "--format",
            "json",
            "--output",
            str(out),
            str(sql_file),
        ]
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    c102_findings = [f for f in payload.get("findings", []) if f["rule_id"] == "CPX_C102"]
    assert c102_findings, "Expected at least one CPX_C102 finding with 3 joins"
    for finding in c102_findings:
        assert finding["level"] == "error", (
            f"Expected level='error' (band threshold=3, joins=3); got {finding['level']!r}"
        )


def test_sarif_severity_info_maps_to_note(tmp_path: Path) -> None:
    """SARIF output must use 'note' for findings with severity=info."""
    sql_file = tmp_path / "model.sql"
    sql_file.write_text(
        "select * from base join t1 on base.id = t1.id join t2 on base.id = t2.id",
        encoding="utf-8",
    )
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        "[sqlfluff:rules:CPX_C102]\nmax_joins = 1\nseverity = info\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.sarif"
    main(
        [
            "report",
            "--dialect",
            "ansi",
            "--config",
            str(cfg),
            "--format",
            "sarif",
            "--output",
            str(out),
            str(sql_file),
        ]
    )
    sarif = json.loads(out.read_text(encoding="utf-8"))
    c102_results = [r for r in sarif["runs"][0]["results"] if r["ruleId"] == "CPX_C102"]
    assert c102_results, "Expected at least one CPX_C102 SARIF result"
    for result in c102_results:
        assert result["level"] == "note", f"Expected SARIF level='note' for severity=info; got {result['level']!r}"


def test_console_report_includes_severity_prefix(tmp_path: Path) -> None:
    """Console output must prefix each finding line with [warning], [error], or [info]."""
    sql_file = tmp_path / "model.sql"
    sql_file.write_text(
        "select * from base join t1 on base.id = t1.id join t2 on base.id = t2.id",
        encoding="utf-8",
    )
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text("[sqlfluff:rules:CPX_C102]\nmax_joins = 1\n", encoding="utf-8")
    out = tmp_path / "out.txt"
    main(
        [
            "report",
            "--dialect",
            "ansi",
            "--config",
            str(cfg),
            "--format",
            "console",
            "--output",
            str(out),
            str(sql_file),
        ]
    )
    content = out.read_text(encoding="utf-8")
    assert "[warning]" in content, f"Expected '[warning]' prefix in console output; got:\n{content}"
