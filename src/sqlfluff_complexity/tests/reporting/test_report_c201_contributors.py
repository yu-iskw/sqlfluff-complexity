"""Report CPX_C201 honors show_contributors."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlfluff_complexity.report import analyze_paths

if TYPE_CHECKING:
    from pathlib import Path


def test_report_c201_findings_empty_contributors_when_disabled(tmp_path: Path) -> None:
    """JSON/contributors omit segments when CPX_C201 show_contributors is false."""
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        """
        [sqlfluff:rules:CPX_C201]
        max_complexity_score = 4
        show_contributors = false
        complexity_weights = ctes:2,joins:2,subquery_depth:4,case_expressions:2,boolean_operators:1,window_functions:2

        [sqlfluff:rules:CPX_C102]
        max_joins = 99
        """,
        encoding="utf-8",
    )
    sql = tmp_path / "m.sql"
    sql.write_text(
        """
        select case when a.x then 1 else 0 end
        from a
        join b on a.id = b.id
        where a.c = 1 or a.d = 2
        """,
        encoding="utf-8",
    )
    report = analyze_paths([sql], dialect="ansi", config_path=cfg)
    entry = report.entries[0]
    c201 = next(f for f in entry.findings if f.rule_id == "CPX_C201")
    assert c201.contributors == ()
    assert "Top contributors:" not in c201.message


def test_report_c201_findings_empty_contributors_when_max_zero(tmp_path: Path) -> None:
    """max_contributors=0 suppresses contributor lists while show_contributors is true."""
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        """
        [sqlfluff:rules:CPX_C201]
        max_complexity_score = 4
        show_contributors = true
        max_contributors = 0
        complexity_weights = ctes:2,joins:2,subquery_depth:4,case_expressions:2,boolean_operators:1,window_functions:2

        [sqlfluff:rules:CPX_C102]
        max_joins = 99
        """,
        encoding="utf-8",
    )
    sql = tmp_path / "m.sql"
    sql.write_text(
        """
        select case when a.x then 1 else 0 end
        from a
        join b on a.id = b.id
        where a.c = 1 or a.d = 2
        """,
        encoding="utf-8",
    )
    report = analyze_paths([sql], dialect="ansi", config_path=cfg)
    entry = report.entries[0]
    c201 = next(f for f in entry.findings if f.rule_id == "CPX_C201")
    assert c201.contributors == ()
    assert "Top contributors:" not in c201.message
