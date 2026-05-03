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

"""Bootstrap loading ``dev/coverage_cleanup.py`` for nox and tests (single importlib path)."""

from __future__ import annotations

import functools
import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

# Keep in sync: same literal in noxfile, test_coverage_cleanup_contract, and meta_access docstring.
_META_ACCESS_IMPORTLIB_SPEC = "_sqlfluff_coverage_importlib_meta_access"


@functools.lru_cache(maxsize=1)
def _coverage_importlib_meta_access() -> ModuleType:
    """Load ``dev/coverage_importlib_meta_access.py`` (sibling of this file)."""
    path = Path(__file__).resolve().parent / "coverage_importlib_meta_access.py"
    spec = importlib.util.spec_from_file_location(_META_ACCESS_IMPORTLIB_SPEC, path)
    if spec is None or spec.loader is None:
        message = f"Cannot load coverage importlib meta access from {path}"
        raise RuntimeError(message)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Cache the names module for the process lifetime (nox session / pytest worker).
@functools.lru_cache(maxsize=1)
def _coverage_importlib_names() -> ModuleType:
    """Load ``dev/coverage_importlib_names.py`` (sibling of this file)."""
    dev_root = Path(__file__).resolve().parent
    path = dev_root / "coverage_importlib_names.py"
    spec_name = _coverage_importlib_meta_access().read_names_module_spec(dev_root)
    spec = importlib.util.spec_from_file_location(spec_name, path)
    if spec is None or spec.loader is None:
        message = f"Cannot load coverage importlib names from {path}"
        raise RuntimeError(message)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def clear_coverage_at(repo_root: Path | str, data_root: Path | str | None = None) -> None:
    """Load ``coverage_cleanup`` from ``repo_root``/dev and clear artifacts under ``data_root``.

    Args:
        repo_root: Repository root (directory containing ``dev/coverage_cleanup.py``).
        data_root: Directory whose ``.coverage*`` files to remove; defaults to ``repo_root``.
    """
    root = Path(repo_root)
    target = Path(data_root) if data_root is not None else root
    impl_path = root / "dev" / "coverage_cleanup.py"
    if not impl_path.is_file():
        message = f"Expected coverage cleanup at {impl_path}; is repo_root correct?"
        raise RuntimeError(message)

    names = _coverage_importlib_names()
    spec = importlib.util.spec_from_file_location(names.CLEANUP_IMPL_SPEC, impl_path)
    if spec is None or spec.loader is None:
        message = f"Cannot load coverage cleanup from {impl_path}"
        raise RuntimeError(message)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.clear_stale_coverage_data(target)
