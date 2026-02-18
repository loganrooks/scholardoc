# Session Continuity Guide

## Purpose

Preserve context across sessions so work can resume efficiently without re-explaining or re-discovering.

## Principles

1. **Checkpoint proactively** - Save state before risky operations and at milestones
2. **Assume interruption** - Any session might end unexpectedly
3. **Context is perishable** - What's obvious now won't be obvious later
4. **Handoff to future self** - Write for someone with no context
5. **Clean as you go** - Archive completed checkpoints to reduce clutter

## Memory Naming Convention

**Always include date AND time** in memory names to ensure ordering is unambiguous.

### Format
```
session_YYYYMMDD_HHMM_<description>
checkpoint_YYYYMMDD_HHMM_<description>
```

### Examples
```
session_20260108_1430_init_implementation
checkpoint_20260108_0915_pre_refactor
session_20260108_1745_guides_complete
```

### Why Time Matters
- Multiple sessions can occur on same day
- Enables sorting by filename to find latest
- Removes ambiguity when multiple memories exist
- Supports `list_memories()` → sort → read latest pattern

### Naming Best Practices
- Use 24-hour format (0915, 1430, 2200)
- Keep description brief but meaningful
- Use underscores, not spaces or hyphens
- Lowercase everything

## Checkpoint Protocol

### When to Checkpoint
- Before risky operations (refactoring, major changes)
- After completing a significant milestone
- Before stepping away mid-task
- When context is complex and worth preserving
- Periodically during long sessions (~30 min intervals)

### What to Capture
- Current task/goal
- Progress (completed, in-progress, pending)
- Key decisions made and rationale
- Files modified and why
- Blockers or pending questions
- Concrete steps to resume

### Checkpoint Memory Format

**Memory name**: `checkpoint_YYYYMMDD_HHMM_<description>`

```markdown
# Checkpoint: [brief description]

**Timestamp**: YYYY-MM-DD HH:MM
**Branch**: [current git branch]

## Current Task
[What you're working on]

## Progress
- [x] Completed items
- [ ] In-progress items
- [ ] Pending items

## Key Context
- [Important decisions]
- [Assumptions in use]
- [Dependencies or blockers]

## Files Modified
- [file]: [what changed and why]

## To Resume
1. [First concrete step]
2. [Second step]
3. [Third step]
```

## Resume Protocol

### Steps to Resume
1. Read session handoff memory
2. Check git state (branch, status, recent commits)
3. Load relevant project memories
4. Check for pending tasks or blockers
5. Summarize context for confirmation
6. Confirm ready to continue

### What to Load
- `session_handoff` - Previous session state
- `project_overview` - Project context
- `improvement_roadmap` - Known issues
- `decision_log` - Past decisions
- Recent checkpoint if mid-task

## Handoff Memory Format

**Memory name**: `session_YYYYMMDD_HHMM_<description>`

```markdown
# Session Handoff

**Timestamp**: YYYY-MM-DD HH:MM
**Duration**: [approximate]

## What Was Done
- [Completed work]

## What's In Progress
- [Unfinished work with state]

## Key Decisions Made
- [Decision]: [Rationale]

## Blockers/Questions
- [Any unresolved issues]

## Recommended Next Steps
1. [Priority 1]
2. [Priority 2]

## Context to Load
- [Specific memories or files to read]
```

## Quality Criteria

Good session continuity:
- [ ] Checkpoints capture enough to resume without re-exploration
- [ ] Handoffs are specific about next steps
- [ ] Context is written for someone with no memory of session
- [ ] Old checkpoints are cleaned up after completion
- [ ] Critical decisions are logged, not just in checkpoints

## Anti-patterns

- **Vague checkpoints**: "Working on feature" without specifics
- **Optimistic handoffs**: Assuming next session will remember
- **Checkpoint hoarding**: Never cleaning up old checkpoints
- **Missing blockers**: Not recording what's stuck
- **Implicit context**: Assuming knowledge that isn't written down

## Adaptation Notes

When generating for a project:
- Reference project's specific memory names
- Include project-specific context worth preserving
- Mention project documentation to check on resume
- Adjust checkpoint frequency based on project complexity
