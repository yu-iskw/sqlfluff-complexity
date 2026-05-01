---
name: security-scan
description: Scan the repository for vulnerable dependencies and known CVEs using Trivy, OSV-Scanner, and Grype via the Makefile. Use when the user asks to scan for vulnerabilities, check dependencies for CVEs, run OSV/Trivy/Grype, or run make scan-vulnerabilities.
compatibility: Requires `trivy`, `osv-scanner`, and `grype` on PATH (for example via Homebrew or `trunk install` if Trunk provides them in your environment). Run from the repository root after `make setup` or `uv sync` so lockfiles and manifests match what you ship.
---

# Security scan: vulnerable dependencies

## Purpose

Run the template’s **filesystem and dependency vulnerability** checks in one place. The canonical entry point is [`Makefile`](../../../Makefile) target **`scan-vulnerabilities`**, which runs **Trivy**, **OSV-Scanner**, and **Grype** against the repo root.

## When to use

- Scan for CVEs or vulnerable dependencies
- Respond to security review requests for third-party packages
- Verify fixes after bumping dependencies (for example `uv lock`, `uv add`, or edits to `pyproject.toml`)

## How to run

From the repository root:

```bash
make scan-vulnerabilities
```

Equivalent commands (for debugging or CI parity):

```bash
trivy fs .
osv-scanner scan -r .
grype .
```

If a command is missing, install the tool or run `trunk install` per [AGENTS.md](../../../AGENTS.md) when Trunk manages these linters in your setup.

## Fix loop

1. **Identify:** Read each tool’s output. Note file paths (for example `uv.lock`, `pyproject.toml`) and CVE IDs.
2. **Triage:** Separate **direct** dependencies you control from transitive ones; confirm whether findings are reachable in your use case when deciding urgency.
3. **Fix:** Prefer upgrading or replacing packages (`uv lock`, version pins in `pyproject.toml`). Avoid silencing scanners in the template unless the user explicitly wants policy exceptions documented.
4. **Verify:** Run `make scan-vulnerabilities` again until clean or remaining issues are accepted with rationale.

## Termination

- All three commands exit zero and report no actionable issues, or
- Remaining items are documented as accepted risk, or
- You hit a sensible iteration cap (default: 3) and summarize blockers.

## Related commands (repo)

- **Dependency bumps:** `uv add`, `uv lock`, `uv sync` (see [AGENTS.md](../../../AGENTS.md) and [CLAUDE.md](../../../CLAUDE.md)).
- **Code-level static analysis:** `make codeql` (CodeQL CLI).
- **Broader quality gates:** `make lint` (Trunk, including other configured security linters).
