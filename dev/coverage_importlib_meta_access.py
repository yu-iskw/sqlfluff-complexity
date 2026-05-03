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

"""Read ``coverage_importlib_meta.json`` for importlib synthetic module names.

When loading *this* file via importlib, use spec name ``_sqlfluff_coverage_importlib_meta_access``
(see ``noxfile.py``, ``dev/coverage_bootstrap.py``, and contract tests; keep that string in sync).
"""

from __future__ import annotations

import json
from pathlib import Path


def read_meta(dev_root: Path | str) -> dict[str, object]:
    """Load and return the JSON object from ``dev_root/coverage_importlib_meta.json``."""
    path = Path(dev_root) / "coverage_importlib_meta.json"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        message = f"Cannot read coverage importlib meta at {path}: {exc}"
        raise RuntimeError(message) from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        message = f"Invalid JSON in coverage importlib meta {path}: {exc}"
        raise RuntimeError(message) from exc
    if not isinstance(data, dict):
        message = f"Expected JSON object at root in {path}, got {type(data).__name__}"
        raise RuntimeError(message)  # noqa: TRY004 -- meta contract uses RuntimeError
    return data


def _meta_string(meta: dict[str, object], meta_path: Path, key: str) -> str:
    try:
        value = meta[key]
    except KeyError as exc:
        message = f"Expected top-level string key {key!r} in {meta_path}"
        raise RuntimeError(message) from exc
    if not isinstance(value, str):
        message = f"{key!r} in {meta_path} must be a string, got {type(value).__name__}"
        raise RuntimeError(message)  # noqa: TRY004 -- meta contract uses RuntimeError
    return value


def read_names_module_spec_from_meta(meta: dict[str, object], dev_root: Path | str) -> str:
    """Return ``names_module_spec`` given ``meta`` from ``read_meta`` (avoids a second disk read)."""
    meta_path = Path(dev_root) / "coverage_importlib_meta.json"
    return _meta_string(meta, meta_path, "names_module_spec")


def read_names_module_spec(dev_root: Path | str) -> str:
    """Return ``names_module_spec`` from meta JSON for loading ``coverage_importlib_names.py``."""
    return read_names_module_spec_from_meta(read_meta(dev_root), dev_root)
