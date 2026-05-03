"""Contract for coverage artifact cleanup (dev/coverage_bootstrap.py + noxfile)."""

from __future__ import annotations

import importlib.util
import pathlib
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

# Keep in sync: same literal in noxfile, coverage_bootstrap, and meta_access docstring.
_META_ACCESS_IMPORTLIB_SPEC = "_sqlfluff_coverage_importlib_meta_access"


def _repo_root_containing_dev() -> pathlib.Path:
    """Return the repo root that contains ``dev/coverage_bootstrap.py``."""
    here = pathlib.Path(__file__).resolve()
    for parent in here.parents:
        bootstrap = parent / "dev" / "coverage_bootstrap.py"
        cleanup = parent / "dev" / "coverage_cleanup.py"
        names = parent / "dev" / "coverage_importlib_names.py"
        meta = parent / "dev" / "coverage_importlib_meta.json"
        meta_access = parent / "dev" / "coverage_importlib_meta_access.py"
        if (
            bootstrap.is_file()
            and cleanup.is_file()
            and names.is_file()
            and meta.is_file()
            and meta_access.is_file()
        ):
            return parent
    message = (
        "Could not locate repo root: no ancestor contains dev/coverage_bootstrap.py, "
        "dev/coverage_cleanup.py, dev/coverage_importlib_names.py, "
        "dev/coverage_importlib_meta.json, and dev/coverage_importlib_meta_access.py"
    )
    raise RuntimeError(message)


def _load_coverage_importlib_meta_access() -> ModuleType:
    """Load ``dev/coverage_importlib_meta_access.py`` (same entry nox/bootstrap use)."""
    repo_root = _repo_root_containing_dev()
    path = repo_root / "dev" / "coverage_importlib_meta_access.py"
    spec = importlib.util.spec_from_file_location(_META_ACCESS_IMPORTLIB_SPEC, path)
    if spec is None or spec.loader is None:
        message = f"Cannot load coverage importlib meta access from {path}"
        raise RuntimeError(message)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_coverage_importlib_names() -> ModuleType:
    """Load ``dev/coverage_importlib_names.py`` (same entry nox uses)."""
    repo_root = _repo_root_containing_dev()
    dev = repo_root / "dev"
    path = dev / "coverage_importlib_names.py"
    spec = importlib.util.spec_from_file_location(
        _load_coverage_importlib_meta_access().read_names_module_spec(dev),
        path,
    )
    if spec is None or spec.loader is None:
        message = f"Cannot load coverage importlib names from {path}"
        raise RuntimeError(message)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_coverage_bootstrap_module() -> ModuleType:
    """Load ``dev/coverage_bootstrap.py`` (same entry nox uses)."""
    names = _load_coverage_importlib_names()
    repo_root = _repo_root_containing_dev()
    path = repo_root / "dev" / "coverage_bootstrap.py"
    spec = importlib.util.spec_from_file_location(names.BOOTSTRAP_SPEC, path)
    if spec is None or spec.loader is None:
        message = f"Cannot load coverage bootstrap from {path}"
        raise RuntimeError(message)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_committed_coverage_importlib_meta_json_contract() -> None:
    """Committed ``dev/coverage_importlib_meta.json`` has exactly ``names_module_spec`` (dev tooling)."""
    repo_root = _repo_root_containing_dev()
    dev = repo_root / "dev"
    meta_mod = _load_coverage_importlib_meta_access()
    meta = meta_mod.read_meta(dev)
    assert set(meta) == {"names_module_spec"}
    spec = meta_mod.read_names_module_spec_from_meta(meta, dev)
    assert spec


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


def test_clear_coverage_at_missing_impl_raises(tmp_path: pathlib.Path) -> None:
    """``clear_coverage_at`` must fail fast when ``repo_root/dev/coverage_cleanup.py`` is absent."""
    mod = _load_coverage_bootstrap_module()
    bogus_root = tmp_path / "not_a_repo"
    bogus_root.mkdir()
    with pytest.raises(RuntimeError, match="Expected coverage cleanup at"):
        mod.clear_coverage_at(bogus_root)


def test_read_names_module_spec_missing_meta_raises(tmp_path: pathlib.Path) -> None:
    """Missing ``coverage_importlib_meta.json`` yields a clear ``RuntimeError``."""
    dev_dir = tmp_path / "dev"
    dev_dir.mkdir()
    meta_mod = _load_coverage_importlib_meta_access()
    with pytest.raises(RuntimeError, match="Cannot read coverage importlib meta"):
        meta_mod.read_names_module_spec(dev_dir)


def test_read_names_module_spec_bad_json_raises(tmp_path: pathlib.Path) -> None:
    """Malformed meta JSON yields ``RuntimeError`` mentioning invalid JSON."""
    dev_dir = tmp_path / "dev"
    dev_dir.mkdir()
    (dev_dir / "coverage_importlib_meta.json").write_text("not json {", encoding="utf-8")
    meta_mod = _load_coverage_importlib_meta_access()
    with pytest.raises(RuntimeError, match="Invalid JSON"):
        meta_mod.read_names_module_spec(dev_dir)


def test_read_names_module_spec_wrong_key_raises(tmp_path: pathlib.Path) -> None:
    """Meta JSON without ``names_module_spec`` yields ``RuntimeError``."""
    dev_dir = tmp_path / "dev"
    dev_dir.mkdir()
    (dev_dir / "coverage_importlib_meta.json").write_text("{}", encoding="utf-8")
    meta_mod = _load_coverage_importlib_meta_access()
    with pytest.raises(RuntimeError, match="names_module_spec"):
        meta_mod.read_names_module_spec(dev_dir)


def test_read_names_module_spec_non_string_raises(tmp_path: pathlib.Path) -> None:
    """``names_module_spec`` must be a string in meta JSON."""
    dev_dir = tmp_path / "dev"
    dev_dir.mkdir()
    (dev_dir / "coverage_importlib_meta.json").write_text(
        '{"names_module_spec": 1}',
        encoding="utf-8",
    )
    meta_mod = _load_coverage_importlib_meta_access()
    with pytest.raises(RuntimeError, match="must be a string"):
        meta_mod.read_names_module_spec(dev_dir)


def test_read_meta_non_object_root_raises(tmp_path: pathlib.Path) -> None:
    """JSON root must be an object, not an array or bare string."""
    dev_dir = tmp_path / "dev"
    dev_dir.mkdir()
    (dev_dir / "coverage_importlib_meta.json").write_text("[]", encoding="utf-8")
    meta_mod = _load_coverage_importlib_meta_access()
    with pytest.raises(RuntimeError, match="Expected JSON object at root"):
        meta_mod.read_meta(dev_dir)


def test_read_meta_string_root_raises(tmp_path: pathlib.Path) -> None:
    """JSON root must be an object, not a bare string."""
    dev_dir = tmp_path / "dev"
    dev_dir.mkdir()
    (dev_dir / "coverage_importlib_meta.json").write_text('"x"', encoding="utf-8")
    meta_mod = _load_coverage_importlib_meta_access()
    with pytest.raises(RuntimeError, match="Expected JSON object at root"):
        meta_mod.read_meta(dev_dir)
