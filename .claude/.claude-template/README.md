# Project Development Environment

This directory contains your Claude Code autonomous development system.

## Getting Started

```bash
# Rename this directory to .claude (if not already)
mv .claude-template .claude

# In Claude Code, run init
/project:init
```

## What Init Does

1. **Prerequisites** - Checks for Serena & Sequential-Thinking MCP
2. **Exploration** - 9 parallel agents analyze your codebase
3. **Synthesis** - Evaluates findings, scores project health
4. **Conversation** - Asks about preferences and conflicts
5. **Generation** - Creates project-specific commands, agents, CLAUDE.md
6. **Validation** - Verifies setup works

## Directory Structure

```
.claude/
├── commands/         # Slash commands
│   ├── init.md       # Bootstrap (run once, can self-delete)
│   ├── signal.md     # Capture feedback/corrections
│   ├── checkpoint.md # Save session state
│   └── resume.md     # Restore session context
├── guides/           # Principles for artifact generation
├── init-agents/      # Codebase analyzers (used by init)
├── templates/        # CLAUDE.md and settings.json templates
├── signals/          # Feedback capture storage
└── reviews/          # Review artifacts
```

## After Init

Init generates project-specific artifacts:

| Generated | Purpose |
|-----------|---------|
| `CLAUDE.md` | Project rules, commands, stack info |
| `settings.json` | Permissions for your stack |
| `commands/*.md` | Project-tailored workflows |
| `agents/*.md` | Project-tailored reviewers |
| Serena memories | Persistent project knowledge |

## Available Commands

| Command | Purpose |
|---------|---------|
| `/project:init` | Initialize (run first) |
| `/project:auto <task>` | Autonomous development with review gates |
| `/project:plan <task>` | Create implementation plan |
| `/project:signal` | Capture feedback when something goes wrong |
| `/project:checkpoint` | Save session state before stepping away |
| `/project:resume` | Restore context from previous session |

## Init Modes

```bash
/project:init           # Full 6-phase initialization
/project:init minimal   # Quick setup, skip deep analysis
/project:init validate  # Health check existing setup
/project:init reset     # Clear and reinitialize
```

## Requirements

- **Serena MCP** - Project memory and semantic understanding
- **Sequential-Thinking MCP** - Complex analysis (recommended)

## Customization

**Pre-Init**: Edit `guides/*.md` to change generation principles.

**Post-Init**: Generated commands and agents are fully editable. Changes persist via Serena memories.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| MCP not found | Install Serena and Sequential-Thinking MCP servers |
| Init hangs | Check MCP server logs, try `minimal` mode |
| Wrong detection | Run `/project:init reset` after fixing |
