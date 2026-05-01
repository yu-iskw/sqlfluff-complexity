#!/bin/bash
# Hook: Auto-format Python files after edits
# Triggered by: PostToolUse (Edit|Write) on .py files

set -e

INPUT=$(cat)
FILE_PATH=$(echo "${INPUT}" | jq -r '.tool_input.file_path // empty')

# Only process Python files
if [[ ${FILE_PATH} == *.py ]]; then
	# Check if trunk is available
	if command -v trunk &>/dev/null; then
		trunk fmt "${FILE_PATH}" 2>/dev/null || true
	fi
fi

exit 0
