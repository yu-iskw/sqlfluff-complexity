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

"""Nox sessions for local and CI test orchestration."""

from __future__ import annotations

import functools
import importlib.util
import os
from pathlib import Path
from typing import TYPE_CHECKING

import nox

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import ModuleType


PYTHON_VERSIONS = ("3.10", "3.11", "3.12")
TESTS_PATH = "src/sqlfluff_complexity/tests"
DEFAULT_MARKER = "not dialect_extra and not dbt_templater"

_PYTEST_COV_ARGS = (
    "--cov=sqlfluff_complexity",
    "--cov-report=term-missing",
    "--cov-report=xml",
)

nox.options.sessions = ["tests"]
nox.options.default_venv_backend = "uv"

_REPO_ROOT = Path(__file__).resolve().parent
# Keep in sync: same literal in coverage_bootstrap, test_coverage_cleanup_contract, meta_access docstring.
_META_ACCESS_IMPORTLIB_SPEC = "_sqlfluff_coverage_importlib_meta_access"


@functools.lru_cache(maxsize=1)
def _load_coverage_importlib_meta_access() -> ModuleType:
    """Load ``dev/coverage_importlib_meta_access.py`` (meta JSON reader for importlib names)."""
    path = _REPO_ROOT / "dev" / "coverage_importlib_meta_access.py"
    spec = importlib.util.spec_from_file_location(_META_ACCESS_IMPORTLIB_SPEC, path)
    if spec is None or spec.loader is None:
        message = f"Cannot load coverage importlib meta access from {path}"
        raise RuntimeError(message)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@functools.lru_cache(maxsize=1)
def _load_coverage_importlib_names() -> ModuleType:
    """Load ``dev/coverage_importlib_names.py`` (synthetic importlib spec names)."""
    dev = _REPO_ROOT / "dev"
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


def _clear_coverage_artifacts() -> None:
    """Drop prior coverage files so pytest-cov + xdist do not merge a corrupt SQLite DB.

    Delegates to ``clear_coverage_at`` in ``dev/coverage_bootstrap.py`` (not shipped).
    """
    names = _load_coverage_importlib_names()
    path = _REPO_ROOT / "dev" / "coverage_bootstrap.py"
    spec = importlib.util.spec_from_file_location(names.BOOTSTRAP_SPEC, path)
    if spec is None or spec.loader is None:
        message = f"Cannot load coverage bootstrap from {path}"
        raise RuntimeError(message)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.clear_coverage_at(_REPO_ROOT)


def _uv_sync(session: nox.Session, *additional_groups: str) -> None:
    """Install the project and development dependencies into the Nox environment."""
    groups = ["--group", "dev"]
    for group in additional_groups:
        groups.extend(["--group", group])

    session.run_install(
        "uv",
        "sync",
        "--all-extras",
        *groups,
        f"--python={session.virtualenv.location}",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )


def _pytest_args(marker: str, posargs: Sequence[str]) -> list[str]:
    workers = os.environ.get("PYTEST_XDIST_WORKERS")
    if workers is None:
        # Serial runs in CI avoid flaky interactions between pytest-xdist, coverage,
        # and SQLFluff lazy dialect/rule imports. Override with PYTEST_XDIST_WORKERS.
        workers = "0" if os.environ.get("CI") else "auto"

    args = ["-v", "-s", "-m", marker, *_PYTEST_COV_ARGS]
    if workers != "0":
        args = ["-n", workers, "--dist", "loadfile", *args]

    if posargs:
        return [*args, *posargs]
    return [*args, TESTS_PATH]


def _run_pytest(
    session: nox.Session,
    marker: str,
    *,
    success_codes: Sequence[int] = (0,),
) -> None:
    session.run(
        "python",
        "-m",
        "pytest",
        *_pytest_args(marker, session.posargs),
        success_codes=success_codes,
    )


@nox.session(python=PYTHON_VERSIONS, venv_backend="uv")
def tests(session: nox.Session) -> None:
    """Run the default pytest suite across supported Python versions."""
    _clear_coverage_artifacts()
    _uv_sync(session)
    _run_pytest(session, DEFAULT_MARKER)


@nox.session(python="3.12", venv_backend="uv")
def dialect_extra(session: nox.Session) -> None:
    """Run optional dialect fixture tests."""
    _clear_coverage_artifacts()
    _uv_sync(session)
    _run_pytest(session, "dialect_extra")


@nox.session(python="3.12", venv_backend="uv")
def dbt_templater(session: nox.Session) -> None:
    """Run optional SQLFluff dbt templater compatibility tests."""
    _clear_coverage_artifacts()
    _uv_sync(session, "dbt")
    _run_pytest(session, "dbt_templater", success_codes=(0, 5))
