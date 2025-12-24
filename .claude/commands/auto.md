---
description: Autonomous development workflow with self-review gates
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task, TodoWrite, mcp__serena__*
argument-hint: <feature-description>
---

# Autonomous Development: $ARGUMENTS

**MODE: AUTONOMOUS WITH SELF-REVIEW GATES**

You are executing an autonomous development workflow. After requirements are confirmed, proceed through all phases automatically, using reviewer agents at each gate.

---

## Phase 0: Requirements Lock-in (HUMAN-IN-LOOP)

### 0.1 Understand the Request
- Parse $ARGUMENTS for intent
- Identify ambiguities and unknowns

### 0.2 Clarification Questions
Ask focused questions to clarify:
- Scope boundaries (what's in, what's out)
- Success criteria (how will we know it's done)
- Constraints (performance, compatibility, timeline)
- Preferences (approaches, patterns, trade-offs)

### 0.3 Requirements Summary
Present a clear requirements summary:
```
## Requirements Confirmed
- **Goal**: [One sentence]
- **Scope**: [In/Out list]
- **Success Criteria**: [Measurable outcomes]
- **Constraints**: [Hard limits]
```

**GATE 0**: Wait for human approval of requirements. Say:
> "Requirements summary above. Reply 'approved' to proceed autonomously, or provide corrections."

Once approved, proceed automatically through remaining phases.

---

## Phase 1: Exploration (AUTO)

### 1.1 Codebase Investigation
- Search for relevant files and patterns
- Map dependencies and interactions
- Identify existing conventions
- Note potential risks

### 1.2 Self-Review: Exploration
Launch exploration-reviewer agent:
```
Review my exploration findings for $ARGUMENTS:
[Include exploration summary]
```

**GATE 1**: If verdict is APPROVED → continue. If NEEDS_WORK → address gaps and re-review.

---

## Phase 2: Planning (AUTO)

### 2.1 Create Implementation Plan
Generate plan following `/project:plan` structure:
- Scope definition
- Test strategy (Given/When/Then)
- Task breakdown with dependencies
- Risk assessment

### 2.2 Self-Review: Plan
Launch plan-reviewer agent:
```
Review this implementation plan for $ARGUMENTS:
[Include full plan]
```

**GATE 2**: If verdict is APPROVED → continue. If NEEDS_REVISION → revise and re-review.

---

## Phase 3: Implementation (AUTO + CHECKPOINTS)

### 3.1 TDD Cycle
For each task in the plan:
1. Write failing test
2. Implement minimal code to pass
3. Refactor if needed
4. Run full test suite

### 3.2 Checkpoint Protocol
After each significant task:
- Commit changes with descriptive message
- Update Serena memory with progress
- Verify tests still pass

### 3.3 Self-Review: Code
After implementation complete, launch code-reviewer agent:
```
Review the implementation for $ARGUMENTS:
[Include diff or file list]
```

**GATE 3**: If verdict is APPROVED → continue. If CHANGES_REQUESTED → fix and re-review.

---

## Phase 4: Documentation (AUTO)

### 4.1 Update Documentation
- Update/create docstrings
- Update README if needed
- Update CLAUDE.md if patterns changed

### 4.2 Self-Review: Documentation
Launch documentation-reviewer agent:
```
Review documentation updates for $ARGUMENTS:
[Include doc changes]
```

**GATE 4**: If verdict is APPROVED → continue. If NEEDS_IMPROVEMENT → revise and re-review.

---

## Phase 5: Final Validation (AUTO)

### 5.1 Full Test Suite
```bash
uv run pytest
```

### 5.2 Lint Check
```bash
uv run ruff check .
```

### 5.3 Type Check (if applicable)
```bash
uv run mypy .
```

### 5.4 Integration Verification
- Verify no regressions
- Check for unintended side effects

**GATE 5**: All checks must pass. If any fail → fix and re-run.

---

## Phase 6: Completion (AUTO)

### 6.1 Final Commit
Create atomic commit with comprehensive message.

### 6.2 Session Summary
Update Serena memory with:
- What was accomplished
- Key decisions made
- Any remaining work

### 6.3 Report to Human
```
## Autonomous Development Complete

**Feature**: $ARGUMENTS
**Status**: ✅ Complete

### Summary
[What was built]

### Changes Made
[List of files changed]

### Tests
- [X] All tests passing (N total)
- [X] New tests added (M tests)

### Self-Review Results
- Exploration: APPROVED
- Plan: APPROVED
- Code: APPROVED
- Documentation: APPROVED

### Commits
- [commit hash]: [message]

### Notes
[Any important observations or recommendations]
```

---

## Escalation Protocol

Return to human oversight if:
- Requirements fundamentally change during development
- Architectural decision is challenged by evidence
- Security or data integrity concerns arise
- Test failures cannot be resolved after 3 attempts
- Reviewer agent gives BLOCKED/REJECTED verdict twice

When escalating, provide:
1. Current state and progress
2. Nature of the blocker
3. Options considered
4. Recommended path forward
