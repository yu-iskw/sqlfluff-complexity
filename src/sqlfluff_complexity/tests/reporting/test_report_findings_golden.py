"""Golden-style assertions for reports built from ComplexityFinding."""

from __future__ import annotations

import json
from pathlib import Path

from sqlfluff_complexity.report import analyze_paths
from sqlfluff_complexity.reporting.json import findings_to_json_payload
from sqlfluff_complexity.reporting.sarif import findings_to_sarif_payload


def _fixture_sql(name: str) -> Path:
    root = Path(__file__).resolve().parent / "fixtures" / "sql" / "ansi"
    return root / name


def test_json_findings_shape_join_fixture(tmp_path: Path) -> None:
    """Report findings expose stable JSON keys for a multi-join fixture."""
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        """
        [sqlfluff:rules:CPX_C102]
        max_joins = 1
        """,
        encoding="utf-8",
    )
    sql_path = tmp_path / "t.sql"
    sql_path.write_text(
        _fixture_sql("c102_joins_two.sql").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    report = analyze_paths([sql_path], dialect="ansi", config_path=cfg)
    findings = [f for e in report.entries for f in e.findings]
    payload = findings_to_json_payload(findings)
    assert payload["version"]
    assert len(payload["findings"]) >= 1
    f0 = payload["findings"][0]
    assert set(f0.keys()) >= {
        "aggregate_score",
        "column",
        "contributors",
        "level",
        "line",
        "message",
        "metric",
        "metrics",
        "path",
        "remediation",
        "rule_id",
        "score",
        "threshold",
    }
    assert f0["rule_id"] == "CPX_C102"
    assert f0["metric"] == "joins"
    assert f0["metrics"]["joins"] >= 2


def test_sarif_metadata_covers_all_rules(tmp_path: Path) -> None:
    """SARIF driver lists metadata for every CPX rule plus parse errors."""
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        """
        [sqlfluff:rules:CPX_C102]
        max_joins = 1
        """,
        encoding="utf-8",
    )
    sql_path = tmp_path / "t.sql"
    sql_path.write_text(
        _fixture_sql("c102_joins_two.sql").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    report = analyze_paths([sql_path], dialect="ansi", config_path=cfg)
    findings = [f for e in report.entries for f in e.findings]
    sarif = findings_to_sarif_payload(findings)
    assert sarif["version"] == "2.1.0"
    rule_ids = {r["id"] for r in sarif["runs"][0]["tool"]["driver"]["rules"]}
    for rid in (
        "CPX_C101",
        "CPX_C102",
        "CPX_C103",
        "CPX_C104",
        "CPX_C105",
        "CPX_C106",
        "CPX_C107",
        "CPX_C201",
        "CPX_PARSE_ERROR",
    ):
        assert rid in rule_ids

    results = sarif["runs"][0]["results"]
    assert results
    c102 = next(r for r in results if r["ruleId"] == "CPX_C102")
    assert "physicalLocation" in c102["locations"][0]
    region = c102["locations"][0]["physicalLocation"]["region"]
    assert region["startLine"] >= 1
    assert "message" in c102
    assert "text" in c102["message"]
    # Valid JSON round-trip
    json.dumps(sarif)


def test_contributor_segment_types_on_complex_fixture(tmp_path: Path) -> None:
    """Golden check: contributors reference expected segment types (not raw SQL)."""
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        """
        [sqlfluff:rules:CPX_C102]
        max_joins = 0
        """,
        encoding="utf-8",
    )
    sql_path = tmp_path / "c201.sql"
    sql_path.write_text(
        _fixture_sql("c201_aggregate_sample.sql").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    report = analyze_paths([sql_path], dialect="ansi", config_path=cfg)
    entry = report.entries[0]
    assert entry.metrics is not None
    all_contribs = [c for f in entry.findings for c in f.contributors]
    segment_types = {c.segment_type for c in all_contribs}
    assert entry.metrics.joins >= 1
    assert "join_clause" in segment_types
