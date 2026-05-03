"""Console report line formatting (regressions for PR review)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlfluff_complexity.report import analyze_paths, format_console_report

if TYPE_CHECKING:
    from pathlib import Path


def test_console_report_no_double_rule_prefix_on_c102(tmp_path: Path) -> None:
    """Metric findings already prefix messages with RULE_ID; console must not duplicate."""
    sql_file = tmp_path / "m.sql"
    sql_file.write_text(
        "select * from a join b on a.id = b.id join c on a.id = c.id\n",
        encoding="utf-8",
    )
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        "[sqlfluff:rules:CPX_C102]\nmax_joins = 1\n",
        encoding="utf-8",
    )
    report = analyze_paths([sql_file], dialect="ansi", config_path=cfg)
    text = format_console_report(report)
    assert "CPX_C102: CPX_C102:" not in text
    assert "CPX_C102: join count" in text


def test_console_report_finding_message_matches_lint_case_expression_label(tmp_path: Path) -> None:
    """Threshold labels must match lint-style phrasing (not ``cASE`` from naive lowercasing)."""
    sql_file = tmp_path / "casey.sql"
    sql_file.write_text(
        "select case when x then 1 else 0 end, case when y then 2 else 3 end from t\n",
        encoding="utf-8",
    )
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        "[sqlfluff:rules:CPX_C104]\nmax_case_expressions = 1\n",
        encoding="utf-8",
    )
    report = analyze_paths([sql_file], dialect="ansi", config_path=cfg)
    entry = report.entries[0]
    c104 = next(f for f in entry.findings if f.rule_id == "CPX_C104")
    assert "CASE expression count" in c104.message or "CASE expression" in c104.message
    assert "cASE" not in c104.message
