"""SQLFluff CLI smoke tests for the installed complexity plugin."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def _run_sqlfluff_lint(project_dir: Path, sql_file: Path) -> subprocess.CompletedProcess[str]:
    """Run SQLFluff lint through the active Python environment."""
    # The command is fixed; only temp test paths are passed as arguments.
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "sqlfluff", "lint", str(sql_file)],
        cwd=project_dir,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_sqlfluff_cli_reports_cpx_violation(tmp_path: Path) -> None:
    """The SQLFluff CLI should report CPX violations from project config."""
    config_file = tmp_path / ".sqlfluff"
    config_file.write_text(
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C102

        [sqlfluff:rules:CPX_C102]
        max_joins = 1
        """,
        encoding="utf-8",
    )
    sql_file = tmp_path / "model.sql"
    sql_file.write_text(
        """
        select *
        from a
        join b on a.id = b.id
        join c on b.id = c.id
        """,
        encoding="utf-8",
    )

    result = _run_sqlfluff_lint(tmp_path, sql_file)
    combined_output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "CPX_C102" in combined_output
    assert "max_joins=1" in combined_output
