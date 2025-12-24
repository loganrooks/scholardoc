# ScholarDoc Automation Configuration

> **Purpose:** Maximize Claude Code autonomy while maintaining quality guardrails
> **Philosophy:** Advisory hooks inject context, never block (except catastrophic commands)
> **Status:** ✅ IMPLEMENTED (Advisory-Only)
> **Last Updated:** December 23, 2025

---

## Overview

This configuration creates an "advisory context injection" ecosystem for AI agent development:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                SCHOLARDOC AUTOMATION LAYERS (ADVISORY-ONLY)                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Layer 1: PERMISSIONS (.claude/settings.json)                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ALLOW: Read, Edit(src/**), Bash(uv:*), Bash(git:*), etc.           │   │
│  │ DENY:  rm -rf, sudo, pip install, force push                        │   │
│  │ ASK:   Edit settings.json, rm, git rebase                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  Layer 2: PRE-TOOL HOOKS                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ block-dangerous.py (Bash) - BLOCKING: catastrophic commands only   │   │
│  │ pre-commit-reminder.py (git commit) - ADVISORY: checklist reminder │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  Layer 3: POST-TOOL HOOKS (Edit|Write)                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ post-edit-quality.py - ADVISORY: format, lint, report issues       │   │
│  │ Never blocks - injects warnings via additionalContext              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  Layer 4: STOP HOOKS                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ stop-verify.py - ADVISORY: test status, lint, uncommitted changes  │   │
│  │ • Warns about unpushed commits (>10 = urgent warning)              │   │
│  │ • Logs session summary to .claude/logs/                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  HOOK PHILOSOPHY: Inject context, never interrupt workflow                  │
│  Only block: rm -rf /, fork bombs, curl|sh, dd to disk                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure (Implemented)

```
scholardoc/
├── .claude/
│   ├── settings.json              # Permissions and hook configuration
│   ├── hooks/
│   │   ├── block-dangerous.py     # Pre-tool: block dangerous bash
│   │   ├── post-edit-quality.py   # Post-tool: format/lint Python
│   │   └── stop-verify.py         # Stop: verify completeness + log session
│   ├── commands/
│   │   ├── implement.md           # /project:implement - TDD workflow
│   │   ├── explore.md             # /project:explore - read-only mode
│   │   ├── tdd.md                 # /project:tdd - test-driven cycle
│   │   ├── plan.md                # /project:plan - implementation planning
│   │   ├── review.md              # /project:review - code review
│   │   └── spike.md               # /project:spike - run exploration spikes
│   └── logs/                      # Session logs (TRACKED in git)
├── .gitignore                     # Ignores .claude/settings.local.json only
├── CLAUDE.md
└── pyproject.toml
```

---

## 1. Permissions Configuration

### Correct Syntax Rules

**Important:** Claude Code uses specific syntax for permissions:

| Tool | Syntax | Example |
|------|--------|---------|
| Read/Edit/Write | Glob patterns | `Edit(scholardoc/**)` |
| Bash | **Prefix matching with `:*`** | `Bash(uv:*)` matches `uv sync`, `uv run` |
| All tools | Case-sensitive | `Edit` not `edit` |

### .claude/settings.json (Implemented)

```json
{
  "permissions": {
    "allow": [
      "Read",

      "Edit(scholardoc/**)",
      "Edit(tests/**)",
      "Edit(spikes/**)",
      "Edit(docs/**)",
      "Edit(CLAUDE.md)",
      "Edit(README.md)",
      "Edit(CHANGELOG.md)",
      "Edit(ROADMAP.md)",
      "Edit(REQUIREMENTS.md)",
      "Edit(SPEC.md)",
      "Edit(QUESTIONS.md)",
      "Edit(pyproject.toml)",
      "Edit(.claude/commands/**)",
      "Edit(.claude/hooks/**)",

      "Write(scholardoc/**)",
      "Write(tests/**)",
      "Write(spikes/**)",
      "Write(docs/**)",
      "Write(.claude/commands/**)",
      "Write(.claude/hooks/**)",
      "Write(.claude/logs/**)",

      "Bash(uv sync:*)",
      "Bash(uv run pytest:*)",
      "Bash(uv run ruff:*)",
      "Bash(uv run mypy:*)",
      "Bash(uv run python spikes/:*)",
      "Bash(uv add:*)",
      "Bash(uv remove:*)",
      "Bash(uv:*)",

      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git checkout:*)",
      "Bash(git branch:*)",
      "Bash(git switch:*)",
      "Bash(git stash:*)",
      "Bash(git show:*)",
      "Bash(git fetch:*)",
      "Bash(git pull:*)",
      "Bash(git push:*)",

      "Bash(cat:*)",
      "Bash(head:*)",
      "Bash(tail:*)",
      "Bash(wc:*)",
      "Bash(find:*)",
      "Bash(grep:*)",
      "Bash(ls:*)",
      "Bash(mkdir:*)",
      "Bash(cp:*)",
      "Bash(mv:*)",
      "Bash(touch:*)",
      "Bash(which:*)",
      "Bash(python --version:*)",
      "Bash(python3 --version:*)"
    ],

    "deny": [
      "Bash(rm -rf:*)",
      "Bash(rm -r:*)",
      "Bash(sudo:*)",
      "Bash(chmod 777:*)",
      "Bash(git push --force:*)",
      "Bash(git push -f:*)",
      "Bash(git reset --hard:*)",
      "Bash(pip install:*)",
      "Bash(python -m pip:*)",

      "Edit(.env)",
      "Edit(.env.*)",
      "Edit(.git/**)",
      "Edit(__pycache__/**)",
      "Read(.env)",
      "Read(.env.*)"
    ],

    "ask": [
      "Edit(.claude/settings.json)",
      "Edit(.claude/settings.local.json)",
      "Bash(git rebase:*)",
      "Bash(rm:*)"
    ]
  },

  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-dangerous.py\"",
            "timeout": 10
          }
        ]
      }
    ],

    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/post-edit-quality.py\"",
            "timeout": 60
          }
        ]
      }
    ],

    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/stop-verify.py\"",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

### Permission Categories

| Category | Behavior | Use Case |
|----------|----------|----------|
| `allow` | Auto-approved, no confirmation | Safe, routine operations |
| `deny` | Always blocked | Dangerous operations |
| `ask` | Requires user confirmation | Risky but sometimes needed |

---

## 2. Hook Implementations

### Hook Input Format (JSON via stdin)

```json
{
  "session_id": "abc123",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf /",
    "description": "Delete everything"
  }
}
```

### Hook Output Format (JSON to stdout)

```json
{
  "decision": "allow|deny|block",
  "reason": "Explanation for the decision",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "Extra info for Claude"
  }
}
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - JSON in stdout is processed |
| 2 | Blocking error - stderr shown as error message |
| Other | Non-blocking warning |

### Pre-Tool Hook: block-dangerous.py

Blocks dangerous bash patterns before execution using regex:

```python
dangerous_patterns = [
    (r"rm\s+.*-[rf]", "Recursive/force delete blocked"),
    (r"\|\s*sh\b", "Piping to shell blocked"),
    (r"git\s+push.*--force", "Force push blocked"),
    (r"sudo", "Sudo blocked"),
    (r"pip\s+install", "Use 'uv add' instead"),
    (r"curl.*\|\s*(sh|bash)", "Curl to shell blocked"),
    # ... more patterns
]
```

### Post-Tool Hook: post-edit-quality.py

Runs after Python file edits:

1. `uv run ruff format <file>` - Auto-format
2. `uv run ruff check --fix <file>` - Auto-fix lint issues
3. Report remaining issues (non-blocking)

### Stop Hook: stop-verify.py

Runs when Claude tries to stop:

1. Check tests pass (`uv run pytest`)
2. Check lint clean (`uv run ruff check`)
3. Check for uncommitted changes (`git status`)
4. Log session summary to `.claude/logs/session_YYYYMMDD_HHMMSS.md`

The stop hook is **advisory** - it warns but allows stopping.

---

## 3. Workflow Commands

Commands are markdown files in `.claude/commands/` that define structured workflows.

### Command Syntax

```markdown
---
description: Brief description shown in help
allowed-tools: Tool1, Tool2, Bash(prefix:*)
argument-hint: <arg1> [optional-arg]
---

# Command Title: $ARGUMENTS

Instructions for the workflow...
```

### Available Commands

| Command | Purpose |
|---------|---------|
| `/project:implement <feature>` | TDD implementation workflow |
| `/project:explore <topic>` | Read-only investigation |
| `/project:tdd <what>` | Test-driven development cycle |
| `/project:plan <task>` | Create implementation plan |
| `/project:review [range]` | Code review checklist |
| `/project:spike <#> <pdf>` | Run exploration spike |

### Using Commands

```bash
# In Claude Code conversation:
/project:implement PDF text extraction
/project:explore heading detection
/project:spike 01 sample.pdf
```

---

## 4. Phase-Specific Configuration

### Phase 0: Exploration (Current)

The current configuration is **relaxed for exploration**:

- ✅ TDD not enforced (can edit without tests first)
- ✅ Spikes can be modified freely
- ✅ Documentation can be updated
- ✅ All exploration tools available
- ✅ Quality hooks run but don't block

### Phase 1+: Implementation

When moving to implementation phases, add TDD enforcement:

1. Create `pre-edit-gate.py` hook to require tests
2. Make lint errors blocking (change `decision` to `"block"`)
3. Add coverage threshold checks

---

## 5. Session Logging

Session logs are stored in `.claude/logs/` and **tracked in git** for learning purposes.

### Log Format

```markdown
# Session Log - 2025-12-14T10:30:00

## Status
- Issues: 0
- Warnings: 1

## Changes Since Last Commit
[git diff --stat output]

## Recent Commits
[git log --oneline -5 output]

## Issues Found
None

## Warnings
- Uncommitted changes (3 files)
```

### Using Logs for Improvement

Periodically review logs for:
- Repeated errors → Add rules to prevent
- Common patterns → Add to CLAUDE.md
- Workflow friction → Improve commands/hooks

---

## 6. Quick Reference

### What's Auto-Approved

```
✅ Read any file
✅ Edit: scholardoc/, tests/, spikes/, docs/, .claude/commands/, .claude/hooks/
✅ Write: same directories + .claude/logs/
✅ Bash: uv *, git (most operations)
✅ Bash: ls, cat, grep, find, mkdir, cp, mv, touch
```

### What's Blocked

```
❌ rm -rf, rm -r (use explicit paths)
❌ sudo anything
❌ pip install (use uv add)
❌ git push --force, git reset --hard
❌ Edit/Read .env files
❌ curl/wget | sh
```

### What Needs Confirmation

```
⚠️ Edit .claude/settings.json
⚠️ rm (single file deletion)
⚠️ git rebase
```

---

## 7. Troubleshooting

### Hook Not Running

1. Check file is executable: `chmod +x .claude/hooks/*.py`
2. Check Python available: `which python3`
3. Check JSON syntax in settings.json
4. Check `$CLAUDE_PROJECT_DIR` resolves correctly

### Permission Denied Unexpectedly

1. Check exact pattern match (case-sensitive)
2. Bash uses prefix matching with `:*` (not glob)
3. Look for pattern in `deny` list

### Tests Failing in Stop Hook

1. The stop hook is advisory, not blocking
2. It will warn but allow stopping
3. Fix issues before committing

### Bypassing Hooks (Emergency)

If hooks are blocking legitimate work:

1. Explain in conversation why bypass needed
2. Human can use `.claude/settings.local.json` to override
3. Document why bypass was needed
4. Fix the hook or permission later

---

## 8. Extending the System

### Adding a New Hook

1. Create Python script in `.claude/hooks/`
2. Make executable: `chmod +x .claude/hooks/new-hook.py`
3. Add to settings.json under appropriate event
4. Test with a safe operation

### Adding a New Command

1. Create markdown file in `.claude/commands/`
2. Add frontmatter with description and allowed-tools
3. Write workflow instructions using `$ARGUMENTS`
4. Test with `/project:command-name`

### Updating Permissions

1. Edit `.claude/settings.json`
2. Add pattern to appropriate list (allow/deny/ask)
3. Use `:*` suffix for Bash prefix matching
4. For personal overrides, use `.claude/settings.local.json` (git-ignored)

---

## 9. Summary: What Gets Automated

| Aspect | Automation Level | Human Intervention |
|--------|------------------|-------------------|
| **Read operations** | Fully auto-approved | None |
| **Edit src/tests** | Auto-approved + quality checks | Only if checks fail |
| **Edit docs** | Auto-approved | None |
| **Run tests/lint** | Fully auto-approved | None |
| **Git operations** | Auto-approved (except force push) | None |
| **Edit protected files** | Requires confirmation | Yes |
| **Dangerous bash** | Blocked by hook | Must request bypass |
| **Code quality** | Auto-fixed when possible | Only unfixable issues |
| **Session logging** | Automatic on stop | Review periodically |

### Expected Human Intervention

**Rarely (emergency only):**
- Bypassing safety hooks for hotfix
- Force push after rebase
- Editing settings.json

**Occasionally:**
- Reviewing session logs for patterns
- Approving file deletions
- Resolving unfixable lint errors

**Never:**
- Approving reads
- Approving test runs
- Approving standard edits
- Approving git status/diff/log
