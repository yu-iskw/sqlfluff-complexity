#!/bin/bash
# scripts/create-adr.sh
# Purpose: Create a new ADR non-interactively and return the filename.

# Set VISUAL to true to prevent adr-tools from opening an editor
export VISUAL=true

# Execute adr new with all provided arguments
# adr new returns the relative path of the created ADR to stdout
if CREATED_FILE=$(adr new "$@"); then
	echo "${CREATED_FILE}"
else
	echo "Error: Failed to create ADR. Is 'adr-tools' installed?" >&2
	exit 1
fi
