#!/bin/bash
set -Eeuo pipefail

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

# Constants
SCRIPT_FILE="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "${SCRIPT_FILE}")"
MODULE_DIR="$(dirname "${SCRIPT_DIR}")"

# Arguments
deps="production"
while (($# > 0)); do
	if [[ $1 == "--deps" ]]; then
		if [[ $2 != "production" && $2 != "development" ]]; then
			echo "Error: deps must be one of 'production' or 'development'"
			exit 1
		fi
		deps="$2"
		shift 2
	else
		echo "Unknown argument: $1"
		exit 1
	fi
done

# Change to the module directory
cd "${MODULE_DIR}"

# Install uv and dependencies
pip install --force-reinstall -r "${MODULE_DIR}/requirements.setup.txt"

# Create virtual environment
uv venv

# Install package and dependencies
if [[ ${deps} == "production" ]]; then
	uv sync
else
	uv sync --all-extras
fi
