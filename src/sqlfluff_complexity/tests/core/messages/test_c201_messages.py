"""CPX_C201 message builder shared by lint and report."""

from __future__ import annotations

from textwrap import dedent
from pathlib import Path

from sqlfluff_complexity.core.config.scoring import DEFAULT_WEIGHTS
from sqlfluff_complexity.core.messages.c201_messages import C201ViolationParams, build_c201_violation_message
from sqlfluff_complexity.core.scan.segment_tree import analyze_segment_tree
from sqlfluff_complexity.report import analyze_paths
from sqlfluff_complexity.tests.sqlfluff_helpers import lint_sql, rule_violations


def test_build_c201_message_without_contributors() -> None:
    sql = "select 1"
    from sqlfluff.core import Linter

    tree = Linter(dialect="ansi").parse_string(sql).tree
    assert tree is not None
    analysis = analyze_segment_tree(tree)
    weights = DEFAULT_WEIGHTS
    score = analysis.metrics.score(weights)
    message = build_c201_violation_message(
        C201ViolationParams(
            score=score,
            limit=0,
            metrics=analysis.metrics,
            weights=weights,
            contributors=analysis.contributors,
            show_contributors=False,
            max_contributors=3,
        ),
    )
    assert "CPX_C201: aggregate complexity score" in message
    assert "max_complexity_score=0" in message
    assert "Top contributors" not in message


def test_report_c201_message_matches_lint(tmp_path: Path) -> None:
    """Lint description and report finding message use the same builder."""
    sql = tmp_path / "heavy.sql"
    sql.write_text(
        dedent(
            """
            select *
            from a
            join b on a.id = b.id
            join c on b.id = c.id
            join d on c.id = d.id
            """
        ).strip(),
        encoding="utf-8",
    )
    cfg_text = dedent(
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C201

        [sqlfluff:rules:CPX_C201]
        max_complexity_score = 0
        show_contributors = false
        """
    ).strip()
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(cfg_text, encoding="utf-8")

    linted = lint_sql(sql.read_text(encoding="utf-8"), cfg_text, fname=str(sql))
    lint_v = rule_violations(linted, "CPX_C201")
    assert len(lint_v) == 1

    report = analyze_paths([sql], dialect="ansi", config_path=cfg)
    report_findings = [f for e in report.entries for f in e.findings if f.rule_id == "CPX_C201"]
    assert len(report_findings) == 1

    assert lint_v[0].desc().strip() == report_findings[0].message.strip()
