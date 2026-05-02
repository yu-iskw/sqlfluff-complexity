"""Shared SQLFluff test helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlfluff.core import FluffConfig, Linter

if TYPE_CHECKING:
    from sqlfluff.core.errors import SQLBaseError
    from sqlfluff.core.linter.linted_file import LintedFile


def join_sql(join_count: int) -> str:
    """Return simple ANSI SQL with a configurable number of joins."""
    join_lines: list[str] = [
        f"join table_{index} on base.id = table_{index}.id" for index in range(1, join_count + 1)
    ]
    return "select *\nfrom base\n" + "\n".join(join_lines)


def lint_sql(sql: str, config: str, *, fname: str = "model.sql") -> LintedFile:
    """Lint SQL through SQLFluff with a config string."""
    return Linter(config=FluffConfig.from_string(config)).lint_string(sql, fname=fname)


def rule_violations(linted: LintedFile, rule_code: str) -> list[SQLBaseError]:
    """Return violations matching one SQLFluff rule code."""
    return [violation for violation in linted.violations if violation.rule_code() == rule_code]
