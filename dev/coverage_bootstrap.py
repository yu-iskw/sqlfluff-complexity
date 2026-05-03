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

import importlib.util
from pathlib import Path

_SQLFLUFF_COVERAGE_CLEANUP_IMPL = "_sqlfluff_coverage_cleanup_impl"


def clear_coverage_at(repo_root: Path | str, data_root: Path | str | None = None) -> None:
    """Load ``coverage_cleanup`` from ``repo_root``/dev and clear artifacts under ``data_root``.

    Args:
        repo_root: Repository root (directory containing ``dev/coverage_cleanup.py``).
        data_root: Directory whose ``.coverage*`` files to remove; defaults to ``repo_root``.
    """
    root = Path(repo_root)
    target = Path(data_root) if data_root is not None else root
    impl_path = root / "dev" / "coverage_cleanup.py"
    spec = importlib.util.spec_from_file_location(_SQLFLUFF_COVERAGE_CLEANUP_IMPL, impl_path)
    if spec is None or spec.loader is None:
        message = f"Cannot load coverage cleanup from {impl_path}"
        raise RuntimeError(message)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.clear_stale_coverage_data(target)
