"""Report reads show_contributors / max_contributors per CPX rule section (like lint)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlfluff_complexity.report import analyze_paths

if TYPE_CHECKING:
    from pathlib import Path


def test_report_respects_per_rule_contributor_settings(tmp_path: Path) -> None:
    """CPX_C101 contributor verbosity must not come from CPX_C102 settings."""
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        """
        [sqlfluff:rules:CPX_C101]
        max_ctes = 1
        show_contributors = false

        [sqlfluff:rules:CPX_C102]
        show_contributors = true
        max_contributors = 5
        """,
        encoding="utf-8",
    )
    sql = tmp_path / "two_ctes.sql"
    sql.write_text(
        """
        with a as (select 1), b as (select 2)
        select * from a cross join b
        """,
        encoding="utf-8",
    )
    report = analyze_paths([sql], dialect="ansi", config_path=cfg)
    entry = report.entries[0]
    assert entry.metrics is not None
    c101 = next(f for f in entry.findings if f.rule_id == "CPX_C101")
    assert "Top contributors" not in c101.message
