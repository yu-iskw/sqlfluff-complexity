#!/bin/bash
# Hook: Validate git commit messages follow conventional format
# Triggered by: PreToolUse (Bash) for git commit commands

set -e

INPUT=$(cat)
COMMAND=$(echo "${INPUT}" | jq -r '.tool_input.command // empty')

# Only check git commit commands
if ! echo "${COMMAND}" | grep -q "git commit"; then
	exit 0
fi

# Extract commit message if using -m flag
if echo "${COMMAND}" | grep -qE '\-m\s*["\047]'; then
	# Check for conventional commit format
	# Allowed types: feat, fix, docs, style, refactor, test, chore, build, ci, perf
	if ! echo "${COMMAND}" | grep -qE '\-m\s*["\047](feat|fix|docs|style|refactor|test|chore|build|ci|perf)(\(.+\))?:'; then
		echo '{"warning": "Commit message should follow conventional format: type(scope): description"}' >&2
		# Warning only, don't block
	fi
fi

exit 0
