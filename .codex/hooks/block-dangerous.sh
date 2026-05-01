#!/bin/bash
# Hook: Block dangerous commands
# Triggered by: PreToolUse (Bash)

set -e

INPUT=$(cat)
COMMAND=$(echo "${INPUT}" | jq -r '.tool_input.command // empty')

# Block dangerous patterns
DANGEROUS_PATTERNS=(
	"rm -rf /"
	"rm -rf /*"
	"rm -rf ~"
	"rm -rf ${HOME}"
	"> /dev/sda"
	"mkfs"
	"dd if=/dev/zero"
	":(){:|:&};:"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
	if echo "${COMMAND}" | grep -qF "${pattern}"; then
		echo '{"error": "Blocked: This command pattern is not allowed for safety reasons"}' >&2
		exit 2
	fi
done

# Block force pushes to main/master
if echo "${COMMAND}" | grep -qE "git push.*(-f|--force).*(main|master)"; then
	echo '{"error": "Blocked: Force push to main/master is not allowed"}' >&2
	exit 2
fi

exit 0
