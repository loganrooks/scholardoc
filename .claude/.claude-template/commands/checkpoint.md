---
description: Create session checkpoint - save current state for recovery
allowed-tools: Bash(git:*), Bash(date:*), mcp__serena__*
argument-hint: <note describing current state>
---

# Checkpoint: $ARGUMENTS

Save current session state for recovery or handoff.

## When to Use
- Before risky operations (refactoring, major changes)
- After completing a significant milestone
- Before stepping away mid-task
- When context is complex and worth preserving

## Step 1: Gather Current State

### Git State
```bash
# Current branch and status
git branch --show-current
git status --short

# Recent commits on this branch
git log --oneline -5

# Uncommitted changes summary
git diff --stat HEAD
```

### Active Work
Identify:
- Current task/goal
- Files being modified
- Tests status
- Blockers or pending decisions

## Step 2: Create Checkpoint Memory

```
write_memory("checkpoint_[YYYYMMDD_HHMM]", """
# Checkpoint: $ARGUMENTS

**Created**: [timestamp]
**Branch**: [current branch]

## Current Task
[What you're working on]

## Progress
- [x] Completed items
- [ ] In-progress items
- [ ] Pending items

## Key Context
- [Important decisions made]
- [Assumptions being used]
- [Dependencies or blockers]

## Files Modified
- [file1]: [what changed]
- [file2]: [what changed]

## To Resume
1. [First step to continue]
2. [Second step]

## Notes
$ARGUMENTS
""")
```

## Step 3: Optional Git Checkpoint

If there are uncommitted changes worth preserving:

```bash
# Create a WIP commit (can be amended later)
git add -A
git commit -m "WIP: checkpoint - $ARGUMENTS"
```

Or stash for later:

```bash
git stash push -m "checkpoint: $ARGUMENTS"
```

## Step 4: Confirm

Output:
```markdown
## Checkpoint Created

**Memory**: checkpoint_[timestamp]
**Note**: $ARGUMENTS

### State Captured
- Branch: [branch]
- Modified files: [count]
- Git: [committed/stashed/uncommitted]

### To Restore
Run `/project:resume` or `read_memory("checkpoint_[timestamp]")`
```

## Checkpoint Hygiene

After successful completion of the checkpointed work:
```
delete_memory("checkpoint_[timestamp]")
```

Keep only the most recent 2-3 checkpoints to avoid clutter.
