---
description: Self-improvement review - analyze patterns and enhance workflow
allowed-tools: Read, Glob, Grep, Bash(git:*), Bash(ls:*), Bash(cat:*), mcp__serena__*
argument-hint: [trigger: pr-merge|error|weekly|context-loss]
---

# Self-Improvement Review: $ARGUMENTS

## Step 1: Gather Evidence

### Session Logs
```bash
# Recent session logs
ls -lt .claude/logs/ | head -10

# Review latest session
cat .claude/logs/$(ls -t .claude/logs/ | head -1)
```

### Serena Memories
```
list_memories()
# Review each memory for accuracy
# Check if project_vision is current
```

### Git History
```bash
# Recent commits with fixes
git log --oneline -20 | grep -i "fix"

# PRs with multiple commits (may indicate issues)
git log --oneline -50

# Files changed most frequently
git log --oneline --name-only -50 | grep -v "^[a-f0-9]" | sort | uniq -c | sort -rn | head -10
```

## Step 2: Pattern Detection

Look for these patterns in the evidence:

### Repeated Errors
- [ ] Same error type appears 2+ times
- [ ] Similar fixes applied in multiple places
- [ ] Recurring test failures

### Context Loss
- [ ] Questions about project vision/architecture
- [ ] Confusion about file locations
- [ ] Misunderstanding of workflow

### Workflow Friction
- [ ] Multi-step manual processes
- [ ] Repeated command sequences
- [ ] Inconsistent approaches to same task

### Documentation Gaps
- [ ] Questions answered by reading code (should be in docs)
- [ ] Confusion resolved by explanation (should be documented)
- [ ] Assumptions that needed correction

## Step 3: Proposed Improvements

For each pattern found, propose an action:

| Pattern | Finding | Proposed Action | Target Location |
|---------|---------|-----------------|-----------------|
| | | | |

### Action Types
- **Rule**: Add to CLAUDE.md rules section
- **Memory**: Create/update Serena memory
- **Command**: Add/modify .claude/commands/
- **Hook**: Add/modify .claude/hooks/
- **Doc**: Update documentation
- **Config**: Modify .serena/project.yml

## Step 4: Implementation

For approved improvements:

1. Make the change
2. Test it works as intended
3. Log to improvement_log memory:

```
write_memory("improvement_log", """
## Improvement Log

### [DATE]
- **Trigger**: [pr-merge|error|weekly|context-loss]
- **Finding**: [Description of pattern found]
- **Action**: [What was done]
- **Files**: [Files modified]
- **Verification**: [How we know it works]

[Previous entries...]
""")
```

## Step 5: Summary

Provide:
- Patterns identified (count by type)
- Actions taken
- Actions deferred (and why)
- Recommendations for next review

## Output Format

```markdown
## Self-Improvement Summary

**Trigger**: [What prompted this review]
**Date**: [Current date]

### Patterns Found
- [N] repeated errors
- [N] context loss instances
- [N] workflow friction points
- [N] documentation gaps

### Actions Taken
1. [Action] → [Location]
2. ...

### Deferred
- [Item]: [Reason]

### Next Review
- Recommended: [weekly|after-next-pr|as-needed]
- Focus areas: [...]
```
