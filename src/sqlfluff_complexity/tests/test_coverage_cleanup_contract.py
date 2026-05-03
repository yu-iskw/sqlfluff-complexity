"""Contract for coverage artifact cleanup (dev/coverage_bootstrap.py + noxfile)."""

from __future__ import annotations

import importlib.util
import pathlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType


def _repo_root_containing_dev() -> pathlib.Path:
    """Return the repo root that contains ``dev/coverage_bootstrap.py``."""
    here = pathlib.Path(__file__).resolve()
    for parent in here.parents:
        bootstrap = parent / "dev" / "coverage_bootstrap.py"
        cleanup = parent / "dev" / "coverage_cleanup.py"
        if bootstrap.is_file() and cleanup.is_file():
            return parent
    message = "Could not locate repo root (dev/coverage_bootstrap.py not found in parents)"
    raise RuntimeError(message)


def _load_coverage_bootstrap_module() -> ModuleType:
    """Load ``dev/coverage_bootstrap.py`` (same entry nox uses)."""
    repo_root = _repo_root_containing_dev()
    path = repo_root / "dev" / "coverage_bootstrap.py"
    spec = importlib.util.spec_from_file_location("_sqlfluff_dev_coverage_bootstrap", path)
    if spec is None or spec.loader is None:
        message = f"Cannot load coverage bootstrap from {path}"
        raise RuntimeError(message)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_coverage_cleanup_removes_data_but_not_coveragerc(tmp_path: pathlib.Path) -> None:
    """``.coveragerc`` must survive cleanup; data files and xml must not."""
    (tmp_path / ".coveragerc").write_text("[run]\n", encoding="utf-8")
    (tmp_path / ".coverage").write_bytes(b"sqlite")
    (tmp_path / ".coverage.host.1").write_bytes(b"worker")
    (tmp_path / "coverage.xml").write_text("<coverage/>", encoding="utf-8")

    mod = _load_coverage_bootstrap_module()
    repo = _repo_root_containing_dev()
    mod.clear_coverage_at(repo, tmp_path)

    assert (tmp_path / ".coveragerc").is_file()
    assert not (tmp_path / ".coverage").exists()
    assert not (tmp_path / ".coverage.host.1").exists()
    assert not (tmp_path / "coverage.xml").exists()
