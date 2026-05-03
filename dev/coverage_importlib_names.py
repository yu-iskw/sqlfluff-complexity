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

"""Synthetic module names for importlib loading dev coverage helpers.

Nox, tests, and ``coverage_bootstrap`` must use these constants so spec names stay aligned.

``dev/coverage_importlib_meta_access.py`` reads sibling ``coverage_importlib_meta.json`` and
returns ``names_module_spec`` for ``spec_from_file_location`` when loading this module.
"""

BOOTSTRAP_SPEC = "_sqlfluff_dev_coverage_bootstrap"
CLEANUP_IMPL_SPEC = "_sqlfluff_coverage_cleanup_impl"
