# Copyright 2025 yu-iskw
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for ``expand_report_paths``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlfluff_complexity.report import cli_scan_roots, expand_report_paths

if TYPE_CHECKING:
    from pathlib import Path


def test_expand_non_recursive_returns_paths_unchanged(tmp_path: Path) -> None:
    """Without recursive mode, order and duplicates are preserved."""
    a = tmp_path / "a.sql"
    b = tmp_path / "b.sql"
    a.write_text("select 1", encoding="utf-8")
    b.write_text("select 2", encoding="utf-8")
    inp = [b, a, b]
    assert expand_report_paths(inp, recursive=False) == inp


def test_expand_recursive_collects_nested_sql_case_insensitive_suffix(tmp_path: Path) -> None:
    """Directories yield nested .sql files; suffix match is case-insensitive."""
    nested = tmp_path / "m" / "n"
    nested.mkdir(parents=True)
    x = tmp_path / "x.sql"
    y = nested / "y.SQL"
    x.write_text("select 1", encoding="utf-8")
    y.write_text("select 2", encoding="utf-8")

    result = expand_report_paths([tmp_path], recursive=True)
    assert result == sorted([x, y], key=str)


def test_expand_recursive_keeps_explicit_files(tmp_path: Path) -> None:
    """Explicit file paths are kept even when they are not ``.sql``."""
    other = tmp_path / "notes.txt"
    other.write_text("x", encoding="utf-8")
    sql_f = tmp_path / "m.sql"
    sql_f.write_text("select 1", encoding="utf-8")

    result = expand_report_paths([other, tmp_path], recursive=True)
    assert result == sorted([other, sql_f], key=str)


def test_expand_recursive_dedupes_overlapping_directories(tmp_path: Path) -> None:
    """The same SQL file discovered twice appears once."""
    sub = tmp_path / "sub"
    sub.mkdir()
    sql_file = sub / "model.sql"
    sql_file.write_text("select 1", encoding="utf-8")

    result = expand_report_paths([tmp_path, sub], recursive=True)
    assert result == [sql_file]


def test_expand_recursive_empty_directory(tmp_path: Path) -> None:
    """An empty tree contributes no paths."""
    assert expand_report_paths([tmp_path], recursive=True) == []


def test_cli_scan_roots_directory_argument(tmp_path: Path) -> None:
    """A directory CLI argument resolves to that directory as the scan root."""
    models = tmp_path / "models"
    models.mkdir()
    roots = cli_scan_roots([models])
    assert roots == (str(models.absolute()),)


def test_cli_scan_roots_file_argument_uses_parent(tmp_path: Path) -> None:
    """A file CLI argument uses its parent directory as the scan root."""
    sql_file = tmp_path / "models" / "orders.sql"
    sql_file.parent.mkdir(parents=True)
    sql_file.write_text("select 1", encoding="utf-8")
    roots = cli_scan_roots([sql_file])
    assert roots == (str(sql_file.parent.absolute()),)


def test_cli_scan_roots_longest_root_first(tmp_path: Path) -> None:
    """Nested scan roots are ordered longest-first for prefix matching."""
    outer = tmp_path / "models"
    inner = outer / "staging"
    inner.mkdir(parents=True)
    roots = cli_scan_roots([outer, inner])
    assert roots[0] == str(inner.absolute())
    assert str(outer.absolute()) in roots
