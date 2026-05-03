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

"""Remove stale pytest-cov / coverage.py artifacts from a directory (usually repo root).

Policy: delete only ``.coverage``, ``.coverage.*`` (parallel worker shards), and
``coverage.xml``. Do **not** use a ``.coverage*`` glob, which would also match
``.coveragerc``.

Shell ``make clean`` replicates this in ``dev/clean.sh``; keep that script aligned when
changing rules here.

Nox and tests load this module via ``dev/coverage_bootstrap.py`` (``clear_coverage_at``) so
importlib wiring stays in one place.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib


def clear_stale_coverage_data(root: pathlib.Path) -> None:
    """Delete prior coverage data files under ``root`` so pytest-cov + xdist avoid bad merges."""
    (root / ".coverage").unlink(missing_ok=True)
    for path in root.glob(".coverage.*"):
        path.unlink(missing_ok=True)
    (root / "coverage.xml").unlink(missing_ok=True)
