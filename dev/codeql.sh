#!/bin/bash
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

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Directory for the CodeQL database
DB_DIR=".codeql_db"
# Results file
RESULTS_SARIF="codeql-results.sarif"

# Ignore vendored / fixture trees (for example dbt packages under tmp/) so analysis
# matches maintainable project sources. See .claude/skills/codeql-fix/scripts/render-code-scanning-config.sh
RENDER_SCRIPT="${REPO_ROOT}/.claude/skills/codeql-fix/scripts/render-code-scanning-config.sh"
CODEQL_CONFIG=""
cleanup_codeql_config() {
	if [[ -n ${CODEQL_CONFIG} && -f ${CODEQL_CONFIG} ]]; then
		rm -f "${CODEQL_CONFIG}"
	fi
}

# Check if codeql is installed
if ! command -v codeql &>/dev/null; then
	echo "Error: 'codeql' command not found."
	echo "Please install the CodeQL CLI. See: https://docs.github.com/en/code-security/codeql-cli"
	exit 1
fi

echo "--- Initializing CodeQL Analysis ---"

# Remove existing database if it exists to ensure a fresh scan
if [[ -d ${DB_DIR} ]]; then
	echo "Removing existing CodeQL database at ${DB_DIR}..."
	rm -rf "${DB_DIR}"
fi

# Create CodeQL database
# Note: For Python, we don't need a build command.
echo "Creating CodeQL database..."
CODEQL_CREATE_ARGS=(--language=python --source-root "${REPO_ROOT}")
if [[ -f ${RENDER_SCRIPT} ]]; then
	CODEQL_CONFIG="$(mktemp)"
	trap cleanup_codeql_config EXIT
	bash "${RENDER_SCRIPT}" "${REPO_ROOT}" "${CODEQL_CONFIG}" tmp
	CODEQL_CREATE_ARGS+=(--codescanning-config="${CODEQL_CONFIG}")
else
	echo "Warning: Code scanning config renderer not found at ${RENDER_SCRIPT}; scanning full tree."
fi
codeql database create "${DB_DIR}" "${CODEQL_CREATE_ARGS[@]}"

# Run Analysis
# We use the same 'security-and-quality' suite as defined in CI.
echo "Running CodeQL analysis (security-and-quality suite)..."
# We use the full qualified name for the query suite to ensure it can be found/downloaded.
codeql database analyze "${DB_DIR}" \
	"codeql/python-queries:codeql-suites/python-security-and-quality.qls" \
	--format=sarif-latest \
	--output="${RESULTS_SARIF}" \
	--download

# Create a human-readable summary if possible
# SARIF is JSON, we can extract counts or use codeql bqrs if needed,
# but a simple message about the SARIF file is usually enough for local use.
echo "Analysis complete."
echo "Results saved to: ${RESULTS_SARIF}"

# Optional: Print a brief summary of findings count from SARIF
if command -v jq &>/dev/null; then
	COUNT=$(jq '.runs[0].results | length' "${RESULTS_SARIF}")
	echo "Total findings: ${COUNT}"
	if [[ ${COUNT} -gt 0 ]]; then
		echo "Check ${RESULTS_SARIF} for details or use the CodeQL VS Code extension."
	fi
else
	echo "Install 'jq' to see a summary of findings here."
fi
