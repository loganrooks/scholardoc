---
description: Diagnose system failures and propose improvements
allowed-tools: Read, Glob, Grep, Bash(git:*), Bash(ls:*), Task, mcp__serena__*
argument-hint: <signal-description>
---

# Diagnose: $ARGUMENTS

**MODE: ROOT CAUSE ANALYSIS FOR SYSTEM IMPROVEMENT**

You are diagnosing a development system failure to identify improvements needed in commands, agents, hooks, documentation, or workflows.

---

## Phase 1: Signal Classification

### 1.1 Identify Signal Type

**If $ARGUMENTS describes a specific issue:**
Classify it directly.

**If $ARGUMENTS is "auto" or empty:**
Gather signals from recent activity:

```bash
# Signal files (auto-generated issues)
ls -la .claude/logs/signals/ 2>/dev/null | grep -v "^d" | grep -v ".gitkeep"

# Recent git commits with fixes (indicate issues)
git log --oneline -10 | grep -iE "fix|bug|revert"

# Native Claude logs (rich data: tool calls, errors, token usage)
CLAUDE_LOG_DIR="$HOME/.claude/projects$(pwd)"
if [ -d "$CLAUDE_LOG_DIR" ]; then
  echo "Native logs available for analysis:"
  ls -lt "$CLAUDE_LOG_DIR"/*.jsonl 2>/dev/null | head -3
fi
```

```
# Check memories for recorded issues
list_memories()
read_memory("improvement_log")  # if exists
```

### 1.2 Classify Signal

| Type | Subtype | Examples |
|------|---------|----------|
| Internal | test-failure | pytest failed, CI red |
| Internal | lint-error | ruff/mypy errors |
| Internal | runtime-error | Exception during execution |
| External | human-correction | "you should have...", "why didn't..." |
| External | human-clarification | "what about...?", repeated questions |
| Process | workflow-violation | Skipped step, missed checkpoint |
| Process | escalation | Reviewer gave BLOCKED |
| Process | context-loss | Had to re-explain, memory gap |

**Classification:**
```
Signal: $ARGUMENTS
Type: [Internal|External|Process]
Subtype: [specific subtype]
```

---

## Phase 2: Evidence Gathering

### 2.1 Collect Context

Depending on signal type, gather relevant evidence:

**For Internal Signals:**
```bash
# Recent test output
uv run pytest --tb=short -q 2>&1 | tail -30

# Recent lint output
uv run ruff check . 2>&1 | head -20
```

**For External Signals:**
- Review the human's exact words
- Check what was being done when interruption occurred
- Look for related documentation/commands

**For Process Signals:**
- Check session logs for workflow steps
- Review relevant command definitions
- Check hook configurations

**For Deep Analysis (any signal type):**
```bash
# Parse native Claude logs for tool failures
CLAUDE_LOG_DIR="$HOME/.claude/projects$(pwd)"
if [ -d "$CLAUDE_LOG_DIR" ]; then
  # Find tool errors
  grep -h '"error"' "$CLAUDE_LOG_DIR"/*.jsonl 2>/dev/null | tail -10

  # Tool usage patterns (what was attempted)
  grep -oh '"tool":"[^"]*"' "$CLAUDE_LOG_DIR"/*.jsonl 2>/dev/null | sort | uniq -c | sort -rn | head -10
fi
```

For comprehensive pattern analysis: `/project:analyze-logs session all`

### 2.2 Identify What Should Have Happened

Based on existing system:
- What command should have been followed?
- What agent should have caught this?
- What documentation covers this?
- What hook should have reminded?

---

## Phase 3: Root Cause Tracing

### 3.1 Trace the Chain

```
[Signal]
  → [Immediate cause: what directly caused it]
    → [System component: what part of dev system failed]
      → [Root cause: why that component failed]
```

### 3.2 Identify System Component

| Component | Files | Issues |
|-----------|-------|--------|
| Commands | .claude/commands/*.md | Missing step, unclear instruction |
| Agents | .claude/agents/*.md | Missing review gate, weak criteria |
| Hooks | .claude/hooks/*.md | Not triggering, wrong timing |
| Documentation | CLAUDE.md, docs/ | Outdated, buried, too long |
| Memories | Serena memories | Missing, outdated, incomplete |
| Workflows | Process gaps | Missing command, unclear sequence |

### 3.3 Self-Review: Diagnosis

Launch diagnostic-agent (or self-review) to validate:
```
Is this diagnosis sound?
- Root cause identified?
- Evidence sufficient?
- Alternatives considered?
```

---

## Phase 4: Improvement Proposal

### 4.1 Determine Improvement Type

| Improvement Type | When to Use |
|------------------|-------------|
| COMMAND_REFINEMENT | Command missing step or unclear |
| AGENT_ADDITION | Missing quality gate |
| AGENT_REFINEMENT | Existing agent missed something |
| HOOK_ADDITION | Need automated reminder |
| INSTRUCTION_COMPRESSION | CLAUDE.md too long, rules buried |
| DOCUMENTATION_UPDATE | Docs out of sync |
| MEMORY_UPDATE | Missing cross-session context |
| WORKFLOW_ADDITION | Gap in development process |

### 4.2 Draft Improvement

```markdown
**Improvement Type**: [type]
**Priority**: [P0: blocking | P1: friction | P2: nice-to-have]
**Target**: [specific file or component]

**Current State**:
[What exists now or what's missing]

**Proposed Change**:
[Specific change to make]

**Expected Outcome**:
[How this prevents recurrence]
```

### 4.3 Self-Review: Improvement

Launch improvement-reviewer (or self-review) to validate:
```
Is this improvement appropriate?
- Addresses root cause?
- Proportionate to problem?
- No unintended consequences?
- Doesn't bloat system?
```

---

## Phase 5: Implementation Decision

### 5.1 If Simple and Low-Risk

Implement immediately:
1. Make the change
2. Verify it works
3. Log to improvement_log memory

### 5.2 If Complex or High-Risk

Escalate to human:
```markdown
## Improvement Proposal

**Signal**: [original issue]
**Diagnosis**: [root cause]
**Proposed**: [improvement]
**Needs Approval Because**: [why escalating]

Ready to proceed? [Y/n]
```

---

## Phase 6: Logging

Update improvement_log memory:

```
write_memory("improvement_log", """
## Improvement Log

### [DATE] - [Signal Type]
**Signal**: [description]
**Root Cause**: [diagnosis]
**Improvement**: [what was done]
**Type**: [COMMAND_REFINEMENT, etc.]
**Files Changed**: [list]
**Verification**: [how confirmed]
**Status**: [Implemented|Deferred|Rejected]

[Previous entries...]
""")
```

---

## Output Format

```markdown
## Diagnostic Report

**Date**: [current date]
**Signal**: $ARGUMENTS
**Classification**: [Type] - [Subtype]

### Root Cause Analysis
```
[Signal]
  → [Immediate cause]
    → [System component]
      → [Root cause]
```

### Evidence
- [Key evidence points]

### Improvement Proposal
- **Type**: [improvement type]
- **Priority**: [P0|P1|P2]
- **Target**: [file/component]
- **Change**: [specific change]
- **Expected Outcome**: [prevention mechanism]

### Self-Review Results
- Diagnosis: [Strong|Adequate|Weak]
- Improvement: [APPROVED|NEEDS_REFINEMENT|REJECTED]

### Action Taken
[Implemented|Deferred|Escalated to human]

### Next Steps
[If deferred or need follow-up]
```

---

## Integration Points

This command integrates with:
- `/project:improve` - Can trigger diagnose for each pattern found
- `/project:auto` - Calls diagnose on escalation
- Post-session hooks - Can trigger diagnose on repeated errors
- Signal capture - Reads from .claude/logs/signals/
