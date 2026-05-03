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

# Set up an environment
.PHONY: setup
setup: setup-python

# Set up the python environment.
.PHONY: setup-python
setup-python:
	bash ./dev/setup.sh --deps "development"

# Upgrade Python dependencies (refresh uv.lock, then sync like development setup).
.PHONY: upgrade-deps
upgrade-deps:
	uv lock --upgrade
	uv sync --all-extras

# Check all the coding style.
.PHONY: lint
lint:
	trunk check -a

# Format source codes
.PHONY: format
format:
	trunk fmt -a

# Find unused code (Vulture; reads [tool.vulture] in pyproject.toml).
.PHONY: dead-code vulture
dead-code vulture:
	uv run vulture

# Run unit tests with coverage (pytest-cov / coverage.py).
.PHONY: test coverage
test coverage:
	bash ./dev/test_python.sh

.PHONY: test-dialect-extra
test-dialect-extra:
	NOX_SESSION=dialect_extra bash ./dev/test_python.sh

.PHONY: test-dbt-templater
test-dbt-templater:
	NOX_SESSION=dbt_templater bash ./dev/test_python.sh

# Run local CodeQL analysis.
.PHONY: codeql
codeql:
	bash ./dev/codeql.sh

# Build the package
.PHONY: build
build:
	bash -x ./dev/build.sh

# Clean the environment
.PHONY: clean
clean:
	bash ./dev/clean.sh

all: clean lint test build

# Publish to pypi
.PHONY: publish
publish:
	bash ./dev/publish.sh "pypi"

# Publish to testpypi
.PHONY: test-publish
test-publish:
	bash ./dev/publish.sh "testpypi"

.PHONY: scan-vulnerabilities
scan-vulnerabilities:
	trivy fs .
	osv-scanner scan -r .
	grype .
