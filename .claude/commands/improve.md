---
description: Self-improvement review with self-critique agents
allowed-tools: Read, Glob, Grep, Bash(git:*), Bash(ls:*), Bash(cat:*), Task, mcp__serena__*
argument-hint: [trigger: pr-merge|error|weekly|context-loss|full-audit]
---

# Self-Improvement Review: $ARGUMENTS

**MODE: SELF-CRITIQUE AND IMPROVEMENT**

## Trigger-Based Scope

| Trigger | Scope | Focus |
|---------|-------|-------|
| pr-merge | Recent PR changes | Code quality, patterns introduced |
| error | Recent errors/failures | Root cause, prevention |
| weekly | Full workspace | Patterns, friction, debt |
| context-loss | Session transitions | Memory, documentation gaps |
| full-audit | Everything | Comprehensive system review |

---

## Step 1: Gather Evidence

### Session Logs
```bash
ls -lt .claude/logs/ | head -10
```

### Serena Memories
```
list_memories()
read_memory("decision_log")
read_memory("improvement_log")  # if exists
```

### Git History
```bash
# Recent commits with issues
git log --oneline -20 | grep -iE "fix|bug|revert|oops"

# Files changed most (potential hotspots)
git log --oneline --name-only -50 | grep -v "^[a-f0-9]" | sort | uniq -c | sort -rn | head -10
```

### Test Results
```bash
uv run pytest --tb=no -q 2>&1 | tail -20
```

---

## Step 2: Self-Critique by Domain

### 2.1 Exploration Critique
Launch exploration-reviewer on recent exploration work:
- Were explorations thorough before planning?
- Were assumptions validated?
- Any gaps that caused later issues?

### 2.2 Plan Critique
Launch plan-reviewer on recent plans:
- Were plans complete and accurate?
- Did estimates match reality?
- Were risks properly identified?

### 2.3 Code Critique
Launch code-reviewer on recent code:
- Any patterns that should be rules?
- Any repeated mistakes?
- Any tech debt accumulating?

### 2.4 Documentation Critique
Launch documentation-reviewer:
- Is CLAUDE.md current?
- Are memories accurate?
- Any undocumented patterns?

---

## Step 3: Pattern Detection

### Repeated Errors
- [ ] Same error type 2+ times
- [ ] Similar fixes in multiple places
- [ ] Recurring test failures

### Context Loss
- [ ] Questions about project architecture
- [ ] Confusion about file locations
- [ ] Workflow misunderstandings

### Workflow Friction
- [ ] Multi-step manual processes
- [ ] Repeated command sequences
- [ ] Inconsistent approaches

### Technical Debt
- [ ] TODO comments accumulating
- [ ] Temporary fixes becoming permanent
- [ ] Test coverage decreasing

### Documentation Gaps
- [ ] Questions answered by code reading
- [ ] Confusion resolved by explanation
- [ ] Assumptions that needed correction

---

## Step 4: Improvement Proposals

| Pattern | Finding | Proposed Action | Target | Priority |
|---------|---------|-----------------|--------|----------|
| | | | | |

### Action Types
- **Rule**: Add to CLAUDE.md
- **Memory**: Create/update Serena memory
- **Command**: Add/modify .claude/commands/
- **Agent**: Add/modify .claude/agents/
- **Hook**: Add/modify .claude/hooks/
- **Doc**: Update documentation
- **Config**: Modify settings

### Priority Levels
- **P0**: Blocking future work
- **P1**: Causes repeated friction
- **P2**: Nice to have

---

## Step 5: Implementation

For approved improvements:

1. Make the change
2. Verify it works
3. Log to improvement_log:

```
write_memory("improvement_log", """
## Improvement Log

### [DATE]
- **Trigger**: $ARGUMENTS
- **Self-Critique Results**:
  - Exploration: [verdict]
  - Plan: [verdict]
  - Code: [verdict]
  - Documentation: [verdict]
- **Patterns Found**: [list]
- **Actions Taken**: [list with locations]
- **Verification**: [how confirmed]

[Previous entries...]
""")
```

---

## Step 6: Summary

```markdown
## Self-Improvement Summary

**Trigger**: $ARGUMENTS
**Date**: [Current date]

### Self-Critique Results
| Domain | Verdict | Key Issues |
|--------|---------|------------|
| Exploration | | |
| Planning | | |
| Code | | |
| Documentation | | |

### Patterns Found
- [N] repeated errors
- [N] context loss instances
- [N] workflow friction points
- [N] technical debt items
- [N] documentation gaps

### Actions Taken
1. [Action] → [Location]
2. ...

### Deferred
- [Item]: [Reason]

### Systemic Issues
- [Issues requiring architectural change]

### Next Review
- Recommended: [weekly|after-next-pr|as-needed]
- Focus areas: [...]
```

---

## Continuous Improvement Loop

This command should be run:
- After every PR merge (automatic via hooks)
- After any significant error
- Weekly for maintenance
- After context loss incidents
- Before major feature work (full-audit)

The goal is preventing accumulation of:
- Technical debt
- Documentation drift
- Pattern inconsistencies
- Workflow friction
