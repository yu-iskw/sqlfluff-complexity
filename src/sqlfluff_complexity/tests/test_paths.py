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

"""Unit tests for path discovery."""

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING

from sqlfluff_complexity.paths import (
    discover_sql_paths,
    merge_paths_unique,
    normalize_report_path,
    path_matches_include_exclude,
    read_paths_from_files_stream,
)

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch


def test_discover_sql_recursively(tmp_path: Path) -> None:
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    f1 = tmp_path / "root.sql"
    f1.write_text("select 1", encoding="utf-8")
    f2 = sub / "inner.sql"
    f2.write_text("select 2", encoding="utf-8")
    (tmp_path / "skip.txt").write_text("x", encoding="utf-8")

    out = discover_sql_paths([tmp_path], cwd=tmp_path)
    assert [normalize_report_path(p, root=tmp_path) for p in out] == [
        "a/b/inner.sql",
        "root.sql",
    ]


def test_include_exclude(tmp_path: Path) -> None:
    models = tmp_path / "models"
    models.mkdir()
    (models / "keep.sql").write_text("select 1", encoding="utf-8")
    (models / "skip.sql").write_text("select 1", encoding="utf-8")

    out = discover_sql_paths(
        [models],
        cwd=tmp_path,
        include_globs=("**/*.sql",),
        exclude_globs=("models/skip.sql",),
    )
    assert [normalize_report_path(p, root=tmp_path) for p in out] == ["models/keep.sql"]


def test_direct_file_bypasses_include(tmp_path: Path) -> None:
    f = tmp_path / "x.sql"
    f.write_text("select 1", encoding="utf-8")
    out = discover_sql_paths([f], cwd=tmp_path, include_globs=("models/**/*.sql",))
    assert out == [f.resolve()]


def test_explicit_missing_path_is_kept(tmp_path: Path) -> None:
    """Explicit paths that are not existing files or dirs must stay in the list for read errors."""
    existing = tmp_path / "ok.sql"
    existing.write_text("select 1", encoding="utf-8")
    missing = tmp_path / "nope.sql"
    out = discover_sql_paths([existing, missing], cwd=tmp_path)
    assert set(out) == {existing.resolve(), missing.resolve()}


def test_models_globstar_matches_root_and_nested_under_models(tmp_path: Path) -> None:
    """``models/**/*.sql`` must match both models/a.sql and deeper trees (gitwildmatch)."""
    m = tmp_path / "models"
    m.mkdir()
    (m / "a.sql").write_text("select 1", encoding="utf-8")
    (m / "staging").mkdir()
    (m / "staging" / "b.sql").write_text("select 1", encoding="utf-8")
    (m / "x" / "y").mkdir(parents=True)
    (m / "x" / "y" / "z.sql").write_text("select 1", encoding="utf-8")
    out = discover_sql_paths(
        [m],
        cwd=tmp_path,
        include_globs=("models/**/*.sql",),
        exclude_globs=(),
    )
    rels = [normalize_report_path(p, root=tmp_path) for p in out]
    assert set(rels) == {
        "models/a.sql",
        "models/staging/b.sql",
        "models/x/y/z.sql",
    }


def test_read_paths_from_files_stream(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    txt = tmp_path / "list.txt"
    txt.write_text("a.sql\n\n./b.sql\n", encoding="utf-8")
    (tmp_path / "a.sql").write_text("select 1", encoding="utf-8")
    (tmp_path / "b.sql").write_text("select 2", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    paths = read_paths_from_files_stream(StringIO(txt.read_text()), cwd=tmp_path)
    assert [p.name for p in paths] == ["a.sql", "b.sql"]


def test_path_matches_include_exclude(tmp_path: Path) -> None:
    f = tmp_path / "models" / "a.sql"
    f.parent.mkdir()
    f.write_text("x", encoding="utf-8")
    assert path_matches_include_exclude(
        f,
        cwd=tmp_path,
        include_globs=("**/*.sql",),
        exclude_globs=(),
    )
    assert not path_matches_include_exclude(
        f,
        cwd=tmp_path,
        include_globs=("other/**/*.sql",),
        exclude_globs=(),
    )


def test_merge_paths_unique_deterministic(tmp_path: Path) -> None:
    a = tmp_path / "z.sql"
    b = tmp_path / "a.sql"
    a.write_text("1", encoding="utf-8")
    b.write_text("2", encoding="utf-8")
    merged = merge_paths_unique([b, a, a], cwd=tmp_path)
    assert [normalize_report_path(p, root=tmp_path) for p in merged] == ["a.sql", "z.sql"]
