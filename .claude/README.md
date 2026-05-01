# Claude Code configuration

**Shared** project rules for all coding agents live in the repository root: **[`AGENTS.md`](../AGENTS.md)**. **[`CLAUDE.md`](../CLAUDE.md)** imports that file and then adds only **Claude Code–specific** context.

This directory (`.claude/`) is read **by Claude Code** (and by Cursor for visibility into the same files). It does not replace [AGENTS.md](../AGENTS.md) as the single source of truth for stack, commands, and conventions.

## Structure

```text
.claude/
├── README.md                 # This file
├── settings.json            # Hooks, permissions, and environment
├── settings.local.json.example
├── commands/                 # e.g. mend-adr
├── agents/                    # Subagent definitions (Claude Code Task tool)
│   └── verifier.md
├── skills/                    # Slash-invoked skills (one SKILL.md per folder)
│   ├── build-and-fix/
│   ├── codeql-fix/
│   ├── deep-problem-solving/
│   ├── initialize-project/
│   ├── lint-and-fix/
│   ├── manage-adr/
│   ├── postmortem/
│   ├── problem-solving/
│   ├── python-upgrade/
│   ├── security-scan/
│   ├── setup-dev-env/
│   └── test-and-fix/
└── hooks/
    ├── block-dangerous.sh
    ├── format-python.sh
    └── validate-commit.sh
```

## Quick Start

### Using Skills

Invoke skills with slash commands:

```text
… typical examples (depends on which skills you keep under skills/)
/setup-dev-env
/lint-and-fix
/test-and-fix
```

See the skill name next to each folder in `skills/`; command names may match.

### Using Agents

Agents are specialized assistants invoked via the Task tool:

| Agent        | Purpose                        |
| ------------ | ------------------------------ |
| **verifier** | Runs build → lint → test cycle |

### Self-Improvement

This configuration supports self-evolution. Use `/improve-claude-config` when:

- Claude makes repeated mistakes
- You want to automate a recurring workflow
- New conventions should be documented

## Configuration Files

### settings.json

Contains:

- **permissions**: Allowed and denied commands
- **hooks**: Automatic triggers for tool events
- **env**: Environment variables

### AGENTS.md and CLAUDE.md (repository root)

- [`AGENTS.md`](../AGENTS.md) — Single source of truth for stack, `make` targets, style, testing, security, git, and how every coding tool loads instructions
- [`CLAUDE.md`](../CLAUDE.md) — Imports `AGENTS.md` and adds Claude Code–only material (this directory, self-improvement, hooks, skills)

## Best Practices

1. **Edit [`AGENTS.md`](../AGENTS.md) for shared rules**; keep `CLAUDE.md` lean (import + Claude-only)
2. **Use specific skills**: Don't duplicate knowledge across skills
3. **Test hooks**: Validate hook scripts work before committing
4. **Version control**: Commit configuration changes with clear messages
5. **Self-improve**: Add rules when Claude makes repeated mistakes

## Customization

### Adding a New Skill

1. Create directory: `.claude/skills/<skill-name>/`
2. Create `SKILL.md` with YAML frontmatter and markdown content
3. Invoke with `/<skill-name>`

### Adding a New Hook

1. Create script in `.claude/hooks/`
2. Make executable: `chmod +x .claude/hooks/<script>.sh`
3. Register in `.claude/settings.json` under appropriate event

### Adding a New Agent

1. Create `.claude/agents/<agent-name>.md`
2. Define name, description, tools, and model in frontmatter
3. Write agent instructions in markdown body

## Resources

- [Claude Code documentation](https://code.claude.com/docs)
- [AGENTS.md](../AGENTS.md) — project instructions (all agents)
- [CLAUDE.md](../CLAUDE.md) — Claude Code layer (imports AGENTS)
