# sqlfluff-complexity — project instructions

Authoritative shared instructions for humans and coding agents. How each product loads this repo: [Coding agents & instruction files](#coding-agents--instruction-files).

## Project overview

`sqlfluff-complexity` is a Python package for SQLFluff complexity rules and reporting.
Tooling:

- **Package manager**: [uv](https://github.com/astral-sh/uv)
- **Build system**: [Hatchling](https://hatch.pypa.io/latest/)
- **Linting/formatting**: [Trunk](https://trunk.io/) (Ruff, Pyright, Pylint, Bandit, Semgrep; Ruff is the formatter; Black is not used)
- **Testing**: [pytest](https://docs.pytest.org/)
- **Python**: 3.10+ (see `.python-version` for the pinned version)

## Quick commands

```bash
make setup         # Install dependencies and set up environment
make lint          # Run all linters via Trunk
make lint-python   # Same as `make lint` (trunk check)
make format        # Auto-format code via Trunk
make dead-code     # Find unused code with Vulture (see pyproject [tool.vulture])
make vulture       # Same as make dead-code
make complexity    # Check cyclomatic complexity with Xenon
make xenon         # Same as make complexity
make test          # Run pytest test suite
make coverage      # Run default Python tests with coverage and print missing lines
make coverage-html # Generate an HTML coverage report under htmlcov/
make codeql        # Run local CodeQL analysis
make build         # Build the package
make clean         # Clean build artifacts and coverage outputs
```

## Code style

- Follow the Google Python Style Guide (see `.pylintrc`)
- Use type hints for all public functions
- Imports sorted by Ruff (rule `I`)
- Max line length: 100 characters (Ruff)
- `snake_case` for functions and variables, `PascalCase` for classes

## Testing

- Tests live under `src/sqlfluff_complexity/tests/` (colocated with the package)
- Test files must match `test_*.py`
- Run `make test` before commits
- Run `make coverage` to measure Python test coverage; set `COVERAGE_FAIL_UNDER=<percent>` when enforcing a threshold locally or in CI
- Aim for meaningful coverage on critical paths

## Security

- **Static analysis**: Trunk runs Ruff, **Pyright** (types), Pylint, Bandit, Semgrep, and Trivy for quick feedback
- **Deep analysis**: [GitHub CodeQL](https://codeql.github.com/) path analysis (see `.github/workflows/codeql.yml`)
- **Dependencies**: OSV-Scanner and Trivy
- Use `trunk check` before pushing

## AI guardrails & code quality

- **Cyclomatic complexity**: max **10** per function (Ruff `C901`); run `make complexity` for Xenon enforcement
- **Maintainability**: CodeQL `security-and-quality` tracks long-term health
- If an edit pushes complexity over **10**, refactor into smaller functions before finishing

## Session postmortem (coding agents)

- **Purpose:** After a substantive session, run a retrospective so failures and inefficiencies surface as ranked **Must / Should / Consider** improvements. Template: [`.agents/skills/postmortem/references/postmortem-report-template.md`](.agents/skills/postmortem/references/postmortem-report-template.md).
- **Invocation:** Invoke the `postmortem` skill (e.g. **`/postmortem`** in Claude Code). Load from [`.claude/skills/postmortem/`](.claude/skills/postmortem/) or [`.agents/skills/postmortem/`](.agents/skills/postmortem/) depending on your tool. Keep output **in chat** unless the user asks to persist; the skill does not authorize editing `AGENTS.md`, `CLAUDE.md`, or skills without a separate request.
- **Skip:** Do **not** run after purely mechanical work with no learning signal (e.g. obvious typo, format-only pass, trivial dependency bump with no retries). If the session included debugging, ambiguity, or retries, run a postmortem anyway.

## Git workflow

- Branch from `main`
- Run `make lint && make test` before commits
- Conventional commits: `type(scope): description` (e.g. `feat(api): add user endpoint`)
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- For releases, record changes with the `manage-changelog` skill when [Changie](https://changie.dev/) is available (fragments, batch, merge into `CHANGELOG.md`)

## Architecture

- Package source: `src/sqlfluff_complexity/`
- Dev scripts: `dev/`
- CI/CD: `.github/workflows/`
- **Claude Code** automation: [`.claude/`](.claude/) — see [CLAUDE.md](CLAUDE.md) for how Claude loads this repo and the directory layout
- **Architecture decision records** (ADRs): `docs/adr/`. Use the `manage-adr` skill when the `adr` CLI is installed

## Common gotchas

- Run tools with `uv run …` in the project virtualenv
- Trunk pins tool versions: avoid installing the same linters globally
- Commit `uv.lock` (do not gitignore it)
- If Trunk errors about a missing tool, run `trunk install`

## Parallel or multi-step work (Claude Code)

- This repo does **not** ship a built-in parallel orchestration subagent. For concurrent work, use multiple Task invocations, your editor’s multi-agent features, or your own scripts.
- After substantial or overlapping edits, use the **`verifier`** subagent ([.claude/agents/verifier.md](.claude/agents/verifier.md)) to run **build → lint → test → dependency scan → CodeQL** by delegating each phase to `build-and-fix`, `lint-and-fix`, `test-and-fix`, `security-scan`, and `codeql-fix`.

## Claude Code subagents

Invoked from Claude Code (Task tool or slash flows). Definitions: [`.claude/agents/*.md`](.claude/agents/)

- **`verifier`** — Five-phase verification via preload skills; see [.claude/agents/verifier.md](.claude/agents/verifier.md).

## Claude Code skills

Slash-invoked skills live under [`.claude/skills/<name>/SKILL.md`](.claude/skills/). Use a skill when it matches the task; each `SKILL.md` lists prerequisites (some require a CLI on `PATH`). Skills cite this file and `Makefile` targets rather than linking peer-to-peer to other `SKILL.md` files.

| Skill                  | When to use                                                                 |
| ---------------------- | --------------------------------------------------------------------------- |
| `build-and-fix`        | Build or packaging failures                                                 |
| `codeql-fix`           | Local CodeQL (`make codeql`); requires CodeQL CLI                           |
| `lint-and-fix`         | Trunk / linter failures, formatting issues, or Xenon complexity failures    |
| `test-and-fix`         | Failing tests, coverage checks, or missing-line review                      |
| `setup-dev-env`        | First-time or broken environment                                            |
| `python-upgrade`       | Dependency upgrades with uv                                                 |
| `security-scan`        | Trivy / OSV / Grype (`make scan-vulnerabilities`)                           |
| `initialize-project`   | Renaming the template and bootstrapping                                     |
| `manage-adr`           | ADRs in `docs/adr` (requires `adr` CLI)                                     |
| `postmortem`           | Substantive session end; incidents; skip trivial chore-only sessions        |
| `problem-solving`      | Single-pass XY-aware analysis and scored comparison (default 5 options)     |
| `deep-problem-solving` | Same style of report after **ten** multiple-choice questions (one per turn) |

Some tools load mirrored skills under `.agents/skills/` instead of `.claude/`. Other repos may add `manage-changelog` when Changie is configured (see **Git workflow**).

## Coding agents & instruction files

| Product / channel                                   | How this repo is wired                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Cursor**                                          | Loads root [AGENTS.md](AGENTS.md) and root [CLAUDE.md](CLAUDE.md) for Agent chat (and optional `.cursor/rules/`). [Cursor: Rules](https://cursor.com/docs/rules)                                                                                                                                                                                                                                                                                                                                    |
| **OpenAI Codex**                                    | Merges `~/.codex/AGENTS.md` (or override) with repo [AGENTS.md](AGENTS.md) along the path; default size cap (often 32 KiB) applies to the combined project doc. Project overrides (e.g. `sandbox_mode`, `approval_policy`, `[sandbox_workspace_write]`) can live in [`.codex/config.toml`](.codex/config.toml) when the project is trusted. [Codex: AGENTS.md](https://developers.openai.com/codex/guides/agents-md/), [Codex: Sandboxing](https://developers.openai.com/codex/concepts/sandboxing) |
| **Claude Code**                                     | Reads [CLAUDE.md](CLAUDE.md) (which inlines this file) plus [`.claude/`](.claude/). [Anthropic: CLAUDE.md](https://docs.anthropic.com/en/docs/claude-code/claude-md), [Claude directory](https://code.claude.com/docs/en/claude-directory)                                                                                                                                                                                                                                                          |
| **Gemini CLI**                                      | Project [`.gemini/settings.json`](.gemini/settings.json) includes `AGENTS.md` in `context.fileName` with typical `GEMINI.md` handling. [Gemini: context](https://geminicli.com/docs/cli/gemini-md/)                                                                                                                                                                                                                                                                                                 |
| **GitHub Copilot** (Chat, code review, cloud agent) | Treats root `AGENTS.md` (and `CLAUDE.md` / `GEMINI.md` if present) as **agent instructions**; may also use `.github/copilot-instructions.md` and path-scoped files with defined precedence. [Custom instructions](https://docs.github.com/en/copilot/concepts/prompting/response-customization)                                                                                                                                                                                                     |

**Copilot / GitHub.com:** This repo does not add `.github/copilot-instructions.md`; build, test, and style narrative stay in this file. On GitHub.com, personal instructions override repository content, then path-scoped rules and `copilot-instructions.md` apply (see [Custom instructions](https://docs.github.com/en/copilot/concepts/prompting/response-customization)). **Edit policy:** shared rules here; Claude Code-only behavior, `@AGENTS.md` import, and `.claude/` details in [CLAUDE.md](CLAUDE.md).

### Where things live (quick map)

- **This file** — Stack, `make` targets, style, testing, security, git, ADR pointers, Claude subagent/skill tables
- **[CLAUDE.md](CLAUDE.md)** + **[`.claude/`](.claude/)** — Claude Code entrypoint and automation layout (see CLAUDE.md for directory breakdown and self-improvement rules)
- **`.agents/skills/`** — Skills for tools that do not read `.claude/` (e.g. `postmortem`); may mirror `.claude/skills/`
- **`.gemini/settings.json`** — Gemini CLI project context
- **`.cursor/rules/`** — Optional Cursor rules (e.g. Always Apply); see [Cursor: Rules](https://cursor.com/docs/rules)
- **[`.codex/config.toml`](.codex/config.toml)** — Optional Codex defaults (sandbox, approvals); links above under **OpenAI Codex**
