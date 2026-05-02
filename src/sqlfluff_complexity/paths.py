"""Path discovery and normalization for reports, baselines, and checks."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable, Sequence
from io import StringIO
from pathlib import Path
from typing import TextIO

from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern


def normalize_report_path(path: Path, *, root: Path | None = None) -> str:
    """Return a stable POSIX path string, relative to ``root`` when possible.

    ``root`` defaults to the current working directory.
    """
    resolved = path.resolve()
    base = (root if root is not None else Path.cwd()).resolve()
    try:
        rel = resolved.relative_to(base)
        return rel.as_posix()
    except ValueError:
        return resolved.as_posix()


def _gitwildmatch_spec(patterns: Sequence[str]) -> PathSpec | None:
    """Return a PathSpec for git-style globs, or None when ``patterns`` is empty."""
    if not patterns:
        return None
    return PathSpec.from_lines(GitWildMatchPattern, patterns)


def _path_matches_globs(rel_posix: str, patterns: Sequence[str]) -> bool:
    spec = _gitwildmatch_spec(patterns)
    if spec is None:
        return False
    return spec.match_file(rel_posix)


def path_matches_include(rel_posix: str, patterns: Sequence[str]) -> bool:
    """Match relative POSIX paths using gitwildmatch semantics (including ``**``)."""
    if not patterns:
        return False
    spec = _gitwildmatch_spec(patterns)
    if spec is None:
        return False
    return spec.match_file(rel_posix)


def _collect_sql_under_directory(
    resolved_dir: Path,
    *,
    base: Path,
    seen: set[Path],
    include_spec: PathSpec,
    exclude_spec: PathSpec | None,
    result: list[Path],
) -> None:
    for dirpath, _, filenames in os.walk(resolved_dir):
        for name in filenames:
            if not name.endswith(".sql"):
                continue
            file_path = Path(dirpath) / name
            rel = normalize_report_path(file_path, root=base)
            if not include_spec.match_file(rel):
                continue
            if exclude_spec is not None and exclude_spec.match_file(rel):
                continue
            fp = file_path.resolve()
            if fp not in seen:
                seen.add(fp)
                result.append(fp)


def _add_unique_resolved(path: Path, *, seen: set[Path], result: list[Path]) -> None:
    if path in seen:
        return
    seen.add(path)
    result.append(path)


def discover_sql_paths(
    paths: Sequence[Path],
    *,
    cwd: Path | None = None,
    include_globs: Sequence[str] = ("**/*.sql",),
    exclude_globs: Sequence[str] = (),
) -> list[Path]:
    """Expand explicit paths into concrete SQL files for analysis.

    - Each **file** argument is included even when it does not match ``include_globs``.
    - Each **directory** is walked recursively; only ``*.sql`` files are candidates,
      then filtered by ``include_globs`` / ``exclude_globs`` (matched against paths
      relative to ``cwd``, POSIX-style).
    """
    base = (cwd or Path.cwd()).resolve()
    include_spec = _gitwildmatch_spec(include_globs)
    exclude_spec = _gitwildmatch_spec(exclude_globs)
    if include_spec is None:
        return []

    seen: set[Path] = set()
    result: list[Path] = []

    for raw in paths:
        candidate = raw if raw.is_absolute() else base / raw
        resolved = candidate.resolve()
        if resolved.is_file():
            _add_unique_resolved(resolved, seen=seen, result=result)
            continue
        if resolved.is_dir():
            _collect_sql_under_directory(
                resolved,
                base=base,
                seen=seen,
                include_spec=include_spec,
                exclude_spec=exclude_spec,
                result=result,
            )
            continue
        # Missing or non-regular explicit paths: keep so ``report._analyze_path`` can record read errors.
        _add_unique_resolved(resolved, seen=seen, result=result)
    return sorted(result, key=lambda p: normalize_report_path(p, root=base))


def read_paths_from_files_stream(stream: TextIO, *, cwd: Path) -> list[Path]:
    """Parse newline-delimited paths from a text stream; ignore blank lines."""
    lines = stream.read().splitlines()
    base = cwd.resolve()
    seen: set[Path] = set()
    out: list[Path] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        p = Path(stripped)
        if not p.is_absolute():
            p = base / p
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(rp)
    return sorted(out, key=lambda x: normalize_report_path(x, root=base))


def paths_from_files_from(
    files_from: str | Path,
    *,
    cwd: Path | None = None,
) -> list[Path]:
    """Read newline-delimited paths from a file, or stdin when ``files_from`` is ``-``."""
    base = (cwd or Path.cwd()).resolve()
    if str(files_from) == "-":
        return read_paths_from_files_stream(sys.stdin, cwd=base)
    path = Path(files_from)
    if not path.is_absolute():
        path = base / path
    text = path.read_text(encoding="utf-8")
    return read_paths_from_files_stream(StringIO(text), cwd=base)


def gather_sql_paths(
    positional: Sequence[Path],
    *,
    cwd: Path | None = None,
    files_from: str | Path | None = None,
    include_globs: Sequence[str] = ("**/*.sql",),
    exclude_globs: Sequence[str] = (),
) -> list[Path]:
    """Combine positional discovery and ``--files-from`` sources."""
    base = (cwd or Path.cwd()).resolve()
    chunks: list[Path] = []
    if positional:
        chunks.extend(
            discover_sql_paths(
                positional,
                cwd=base,
                include_globs=include_globs,
                exclude_globs=exclude_globs,
            ),
        )
    if files_from is not None:
        for p in paths_from_files_from(files_from, cwd=base):
            if not p.is_file():
                continue
            if not path_matches_include_exclude(
                p,
                cwd=base,
                include_globs=include_globs,
                exclude_globs=exclude_globs,
            ):
                continue
            chunks.append(p)
    return merge_paths_unique(chunks, cwd=base)


def merge_paths_unique(paths: Iterable[Path], *, cwd: Path | None = None) -> list[Path]:
    """Merge path iterables, de-duplicate, and sort deterministically."""
    base = (cwd or Path.cwd()).resolve()
    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(rp)
    return sorted(out, key=lambda x: normalize_report_path(x, root=base))


def path_matches_include_exclude(
    path: Path,
    *,
    cwd: Path | None = None,
    include_globs: Sequence[str] = ("**/*.sql",),
    exclude_globs: Sequence[str] = (),
) -> bool:
    """Return True if ``path`` passes include/exclude filters relative to ``cwd``."""
    base = (cwd or Path.cwd()).resolve()
    rel = normalize_report_path(path, root=base)
    return path_matches_include(rel, include_globs) and not _path_matches_globs(rel, exclude_globs)
