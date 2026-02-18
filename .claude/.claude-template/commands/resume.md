---
description: Resume session - restore context from previous work
allowed-tools: Read, Glob, Grep, Bash(git:*), Bash(ls:*), mcp__serena__*
argument-hint: "[optional: memory-name]"
---

# Session Resume: $ARGUMENTS

Restore context from previous session to continue work efficiently.

## Step 1: Load Session Handoff

```
# Check for handoff from previous session
read_memory("session_handoff")
```

If handoff exists, summarize:
- What was being worked on
- What was accomplished
- What's still in progress
- Key decisions made
- Blockers/questions
- Recommended next steps

## Step 2: Check Recent State

### Git Activity
```bash
# Recent commits
git log --oneline -10

# Current branch and status
git branch
git status

# Any stashed changes?
git stash list
```

### Uncommitted Work
```bash
# Check for work in progress
git diff --stat HEAD
```

## Step 3: Load Relevant Memories

```
# List all available memories
list_memories()

# Always load project vision
read_memory("project_overview")

# Load other relevant memories based on current work
# Look for memories mentioned in handoff or matching current task
```

## Step 4: Check For Pending Tasks

### Session Logs
```bash
# Most recent session log (if exists)
ls -t .claude/logs/ 2>/dev/null | head -1
```

### Open PRs
```bash
gh pr list --state open 2>/dev/null
```

### Improvement Log
```
# Check if improvements were queued
read_memory("improvement_roadmap")
```

## Step 5: Context Summary

Provide a structured summary:

```markdown
## Session Context Restored

### Previous Session
- **Date**: [from handoff]
- **Work**: [what was being done]
- **Status**: [completed/in-progress/blocked]

### Current State
- **Branch**: [current git branch]
- **Uncommitted**: [yes/no, summary if yes]
- **Open PRs**: [list if any]

### Recommended Next Steps
1. [First priority from handoff or logical next step]
2. [Second priority]
3. [Third priority]

### Relevant Context
- **Memories loaded**: [list]
- **Key decisions**: [from handoff or decision_log]
- **Blockers**: [from handoff if any]
```

## Step 6: Confirm Ready

Ask: "Context restored. Ready to continue with [recommended next step]?"

If user has specific argument, focus on that area instead.
