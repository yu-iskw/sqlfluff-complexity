#!/usr/bin/env bash
#  Licensed to the Apache Software Foundation (ASF) under one or more
#  contributor license agreements.  See the NOTICE file distributed with
#  this work for additional information regarding copyright ownership.
#  The ASF licenses this file to You under the Apache License, Version 2.0
#  (the "License"); you may not use this file except in compliance with
#  the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
set -e
set -x

# Constants
SCRIPT_FILE="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "${SCRIPT_FILE}")"
MODULE_DIR="$(dirname "${SCRIPT_DIR}")"

cleaned_dirs=(
	dist
	sdist
	.pytest_cache
)

for cleaned_dir in "${cleaned_dirs[@]}"; do
	if [[ -d "${MODULE_DIR}/${cleaned_dir}" ]]; then
		rm -r "${MODULE_DIR:?}/${cleaned_dir}"
	fi
done

# Stale pytest-cov / coverage.py files can break parallel nox runs (SQLite merge errors).
# Policy matches dev/coverage_cleanup.py, dev/coverage_bootstrap.py, and noxfile (keep in sync).
# Remove .coverage and .coverage.* only — not .coverage* — so .coveragerc is preserved.
rm -f "${MODULE_DIR}/.coverage"
shopt -s nullglob
for cov in "${MODULE_DIR}"/.coverage.*; do
	rm -f "${cov}"
done
shopt -u nullglob
rm -f "${MODULE_DIR}/coverage.xml"
