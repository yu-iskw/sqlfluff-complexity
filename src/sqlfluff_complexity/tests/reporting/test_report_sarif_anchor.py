"""Report SARIF regions anchor near offending segments when possible."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlfluff_complexity.cli import main

if TYPE_CHECKING:
    from pathlib import Path


def test_sarif_join_violation_region_not_always_line_one(tmp_path: Path) -> None:
    """CPX_C102 SARIF region should prefer join_clause position over file root."""
    sql_file = tmp_path / "joins.sql"
    sql_file.write_text(
        """select * from base
join t1 on base.id = t1.id
join t2 on base.id = t2.id
""",
        encoding="utf-8",
    )
    cfg = tmp_path / ".sqlfluff"
    cfg.write_text(
        "[sqlfluff:rules:CPX_C102]\nmax_joins = 1\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.sarif"
    assert (
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
            ],
        )
        == 0
    )
    sarif = json.loads(out.read_text(encoding="utf-8"))
    c102 = next(r for r in sarif["runs"][0]["results"] if r["ruleId"] == "CPX_C102")
    region = c102["locations"][0]["physicalLocation"]["region"]
    assert region["startLine"] >= 2
