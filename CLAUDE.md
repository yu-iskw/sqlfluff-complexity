<!-- markdownlint-disable-file MD041 -->

@AGENTS.md

# Claude Code (this repository)

The `@AGENTS.md` import inlines that file at session start (Claude Code reads this file, not [AGENTS.md](AGENTS.md) alone; see [Anthropic: CLAUDE.md](https://docs.anthropic.com/en/docs/claude-code/claude-md)). Put **only** material that is specific to Claude Code below.

## What lives under `.claude/`

- **[`settings.json`](.claude/settings.json)** — Permissions, hooks, environment
- **[`hooks/`](.claude/hooks/)** — Scripts for tool lifecycle events
- **[`skills/`](.claude/skills/)** — Slash skills (`SKILL.md` per directory)
- **[`agents/`](.claude/agents/)** — Subagent prompt files for the Task tool
- **[`commands/`](.claude/commands/)** — One-off command markdown if present

Authoritative list of subagents and skills is in [AGENTS.md](AGENTS.md); definitions stay in the paths above.

## Self-improvement (Claude Code)

- For rules that **every** coding agent should follow, edit [AGENTS.md](AGENTS.md), not this file.
- For hooks, new skills, path-scoped rules, or stricter tool permissions, change files under [`.claude/`](.claude/) and [`settings.json`](.claude/settings.json).
- If the optional `improve-claude-config` skill is added under `.claude/skills/`, use it to evolve the local config safely.

**Other products** (Cursor, Codex, Gemini, Copilot) do not load `skills/`, `agents/`, or `settings.json` automatically—use [AGENTS.md](AGENTS.md) and each tool’s own config as documented there.
