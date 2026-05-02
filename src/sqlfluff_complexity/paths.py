"""Path discovery and normalization for reports, baselines, and checks."""

from __future__ import annotations

import fnmatch
import os
import shutil
import subprocess
import sys
from collections.abc import Iterable, Sequence
from io import StringIO
from pathlib import Path
from typing import TextIO


class GitPathError(RuntimeError):
    """Raised when git cannot list changed files."""


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


def _path_matches_globs(rel_posix: str, patterns: Sequence[str]) -> bool:
    if not patterns:
        return False
    return any(fnmatch.fnmatch(rel_posix, pat) for pat in patterns)


def path_matches_include(rel_posix: str, patterns: Sequence[str]) -> bool:
    """Match ``**/*.sql`` to SQL files at any depth, including repo-root ``*.sql``."""
    if not patterns:
        return False
    return any(
        fnmatch.fnmatch(rel_posix, pat)
        or (pat == "**/*.sql" and fnmatch.fnmatch(rel_posix, "*.sql"))
        for pat in patterns
    )


def _collect_sql_under_directory(
    resolved_dir: Path,
    *,
    base: Path,
    seen: set[Path],
    include_globs: Sequence[str],
    exclude_globs: Sequence[str],
    result: list[Path],
) -> None:
    for dirpath, _dirnames, filenames in os.walk(resolved_dir):
        for name in filenames:
            if not name.endswith(".sql"):
                continue
            file_path = Path(dirpath) / name
            rel = normalize_report_path(file_path, root=base)
            if not path_matches_include(rel, include_globs):
                continue
            if _path_matches_globs(rel, exclude_globs):
                continue
            fp = file_path.resolve()
            if fp not in seen:
                seen.add(fp)
                result.append(fp)


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
    seen: set[Path] = set()
    result: list[Path] = []

    for raw in paths:
        candidate = raw if raw.is_absolute() else base / raw
        resolved = candidate.resolve()
        if resolved.is_file():
            if resolved not in seen:
                seen.add(resolved)
                result.append(resolved)
            continue
        if resolved.is_dir():
            _collect_sql_under_directory(
                resolved,
                base=base,
                seen=seen,
                include_globs=include_globs,
                exclude_globs=exclude_globs,
                result=result,
            )
            continue
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


def _git_executable() -> str:
    git = shutil.which("git")
    if git is None:
        message = "git executable not found on PATH."
        raise GitPathError(message)
    return git


def paths_from_changed_from(
    git_ref: str,
    *,
    cwd: Path | None = None,
    include_globs: Sequence[str] = ("**/*.sql",),
    exclude_globs: Sequence[str] = (),
) -> list[Path]:
    """List changed files vs ``git_ref`` using ``git diff --name-only REF...HEAD``.

    Keeps only paths that exist on disk, are files, match include globs, and do not
    match exclude globs. Raises ``GitPathError`` if git is unavailable or the command fails.
    """
    base = (cwd or Path.cwd()).resolve()
    git_bin = _git_executable()
    try:
        proc = subprocess.run(
            [git_bin, "diff", "--name-only", f"{git_ref}...HEAD"],
            cwd=base,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        message = f"git is not available or failed to start: {exc}"
        raise GitPathError(message) from exc

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        detail = stderr or stdout or f"exit code {proc.returncode}"
        message = f"git diff failed: {detail}"
        raise GitPathError(message)

    names = [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]
    seen: set[Path] = set()
    result: list[Path] = []
    for name in names:
        candidate = Path(name)
        if not candidate.is_absolute():
            candidate = base / candidate
        resolved = candidate.resolve()
        if not resolved.is_file():
            continue
        rel = normalize_report_path(resolved, root=base)
        if not path_matches_include(rel, include_globs):
            continue
        if _path_matches_globs(rel, exclude_globs):
            continue
        if resolved not in seen:
            seen.add(resolved)
            result.append(resolved)
    return sorted(result, key=lambda p: normalize_report_path(p, root=base))


def gather_sql_paths(
    positional: Sequence[Path],
    *,
    cwd: Path | None = None,
    files_from: str | Path | None = None,
    changed_from: str | None = None,
    include_globs: Sequence[str] = ("**/*.sql",),
    exclude_globs: Sequence[str] = (),
) -> list[Path]:
    """Combine positional discovery, ``--files-from``, and ``--changed-from`` sources."""
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
    if changed_from is not None:
        chunks.extend(
            paths_from_changed_from(
                changed_from,
                cwd=base,
                include_globs=include_globs,
                exclude_globs=exclude_globs,
            ),
        )
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
