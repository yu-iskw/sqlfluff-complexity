# {{ project_name }}

A production-ready Python package using modern tooling.

## Features

- **Package Management**: [uv](https://github.com/astral-sh/uv)
- **Build System**: [Hatchling](https://hatch.pypa.io/latest/)
- **Linting & Formatting**: [Trunk](https://trunk.io/) (Ruff, Pyright, Pylint, Bandit; Ruff is also the formatter)
- **Testing**: [pytest](https://docs.pytest.org/)
- **CI/CD**: GitHub Actions

## Security & Quality

This template enforces high security and maintainability standards:

- **[GitHub CodeQL](https://codeql.github.com/)**: Deep analysis using the `security-and-quality` suite to track code health and catch vulnerabilities.
- **Complexity Guardrails**: Cyclomatic complexity is capped at **10** per function (enforced via Ruff `C901`).
- **Trunk Linters**: [Bandit](https://github.com/PyCQA/bandit) (security), [Semgrep](https://semgrep.dev/) (patterns), [Trivy](https://github.com/aquasecurity/trivy) (IaC/Secret scanning), and [OSV-Scanner](https://github.com/google/osv-scanner) (dependencies).

## Development

Conventions, build commands, and AI-agent instructions: see [AGENTS.md](AGENTS.md). Claude Code–specific config lives in `CLAUDE.md` (it imports [AGENTS.md](AGENTS.md)) and in [`.claude/`](.claude/).

```bash
make setup      # Install dependencies and set up environment
make lint       # Run all linters via Trunk
make format     # Auto-format code via Trunk
make test       # Run pytest test suite
```
