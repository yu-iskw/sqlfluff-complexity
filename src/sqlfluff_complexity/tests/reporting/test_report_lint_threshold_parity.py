"""Report vs lint threshold parity for CPX_C108 and CPX_C109."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

from sqlfluff_complexity.report import analyze_paths
from sqlfluff_complexity.tests.fixture_loader import read_sql_fixture
from sqlfluff_complexity.tests.sqlfluff_helpers import lint_sql, rule_violations


def test_report_matches_lint_c108_nested_case(tmp_path: Path) -> None:
    """Same thresholds should yield one CPX_C108 finding in report and lint."""
    sql = read_sql_fixture("ansi", "c108_nested_case")
    sql_path = tmp_path / "model.sql"
    sql_path.write_text(sql, encoding="utf-8")
    cfg = tmp_path / ".sqlfluff"
    cfg_text = """
[sqlfluff]
dialect = ansi

[sqlfluff:rules:CPX_C108]
max_nested_case_depth = 1
"""
    cfg.write_text(cfg_text, encoding="utf-8")

    report = analyze_paths([sql_path], dialect="ansi", config_path=cfg)
    report_findings = [f for e in report.entries for f in e.findings if f.rule_id == "CPX_C108"]
    linted = lint_sql(sql, cfg_text, fname=str(sql_path))
    lint_v = rule_violations(linted, "CPX_C108")

    assert len(report_findings) == 1
    assert len(lint_v) == 1
    assert report_findings[0].threshold == 1
    assert "nested CASE depth 2 exceeds max_nested_case_depth=1" in report_findings[0].message


def test_report_matches_lint_c109_set_operations(tmp_path: Path) -> None:
    """Same thresholds should yield one CPX_C109 finding in report and lint."""
    sql = read_sql_fixture("ansi", "c109_set_ops_two")
    sql_path = tmp_path / "model.sql"
    sql_path.write_text(sql, encoding="utf-8")
    cfg = tmp_path / ".sqlfluff"
    cfg_text = """
[sqlfluff]
dialect = ansi

[sqlfluff:rules:CPX_C109]
max_set_operations = 1
"""
    cfg.write_text(cfg_text, encoding="utf-8")

    report = analyze_paths([sql_path], dialect="ansi", config_path=cfg)
    report_findings = [f for e in report.entries for f in e.findings if f.rule_id == "CPX_C109"]
    linted = lint_sql(sql, cfg_text, fname=str(sql_path))
    lint_v = rule_violations(linted, "CPX_C109")

    assert len(report_findings) == 1
    assert len(lint_v) == 1
    assert report_findings[0].threshold == 1
    assert "set operation count 2 exceeds max_set_operations=1" in report_findings[0].message


def test_report_path_override_max_nested_case_depth_matches_lint_c108(tmp_path: Path) -> None:
    """Report and lint should both use path_overrides for max_nested_case_depth."""
    sql = read_sql_fixture("ansi", "c108_nested_case")
    cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        sql_path = Path("models/staging/orders.sql")
        sql_path.parent.mkdir(parents=True)
        sql_path.write_text(sql, encoding="utf-8")
        cfg = Path(".sqlfluff")
        cfg_text = """
[sqlfluff]
dialect = ansi

[sqlfluff:rules:CPX_C108]
max_nested_case_depth = 10

[sqlfluff:rules:CPX_C201]
path_overrides =
    models/staging/*.sql:max_nested_case_depth=1
"""
        cfg_text = textwrap.dedent(cfg_text).strip()
        cfg.write_text(cfg_text, encoding="utf-8")

        report = analyze_paths([sql_path], dialect="ansi", config_path=cfg)
        report_findings = [f for e in report.entries for f in e.findings if f.rule_id == "CPX_C108"]
        linted = lint_sql(sql, cfg_text, fname=str(sql_path))
        lint_v = rule_violations(linted, "CPX_C108")

        assert len(report_findings) == 1
        assert len(lint_v) == 1
        assert report_findings[0].threshold == 1
        assert "nested CASE depth 2 exceeds max_nested_case_depth=1" in report_findings[0].message
    finally:
        os.chdir(cwd)


def test_report_path_override_max_set_operations_matches_lint_c109(tmp_path: Path) -> None:
    """Report and lint should both use path_overrides for max_set_operations."""
    sql = read_sql_fixture("ansi", "c109_set_ops_two")
    cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        sql_path = Path("models/marts/union_stack.sql")
        sql_path.parent.mkdir(parents=True)
        sql_path.write_text(sql, encoding="utf-8")
        cfg = Path(".sqlfluff")
        cfg_text = """
[sqlfluff]
dialect = ansi

[sqlfluff:rules:CPX_C109]
max_set_operations = 12

[sqlfluff:rules:CPX_C201]
path_overrides =
    models/marts/*.sql:max_set_operations=1
"""
        cfg_text = textwrap.dedent(cfg_text).strip()
        cfg.write_text(cfg_text, encoding="utf-8")

        report = analyze_paths([sql_path], dialect="ansi", config_path=cfg)
        report_findings = [f for e in report.entries for f in e.findings if f.rule_id == "CPX_C109"]
        linted = lint_sql(sql, cfg_text, fname=str(sql_path))
        lint_v = rule_violations(linted, "CPX_C109")

        assert len(report_findings) == 1
        assert len(lint_v) == 1
        assert report_findings[0].threshold == 1
        assert "set operation count 2 exceeds max_set_operations=1" in report_findings[0].message
    finally:
        os.chdir(cwd)
