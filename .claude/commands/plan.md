---
description: Create implementation plan before coding
allowed-tools: Read, Glob, Grep, Bash(git:*), Bash(ls:*), Bash(find:*)
argument-hint: <feature-or-task>
---

# Plan: $ARGUMENTS

**MODE: PLANNING BEFORE IMPLEMENTATION**

A good plan balances understanding, research, scope, tests, tasks, and risks.

## Step 1: Understand the Request

- **What**: What exactly is being asked?
- **Why**: What problem does this solve?
- **Who**: Who benefits from this?
- **Context**: How does this fit into the larger system?

## Step 2: Research Current State

### Code Analysis
- Related modules and functions
- Existing patterns to follow
- Current tests that might be affected
- Dependencies involved

### Documentation Check
- SPEC.md for design guidance
- REQUIREMENTS.md for acceptance criteria
- QUESTIONS.md for unresolved decisions
- ROADMAP.md for current phase

### Quick Questions
- Has something similar been done before?
- Are there patterns to reuse?
- What can we learn from existing code?

## Step 3: Define Scope

**In Scope:**
- Specific changes needed
- Files to create/modify
- Tests to write/update

**Out of Scope:**
- What this does NOT include
- Future considerations (defer to later)
- Related improvements (separate task)

Clear boundaries prevent scope creep.

## Step 4: Test Strategy

Define how we'll verify success. Use Given/When/Then format:

```
test_<behavior>_<scenario>:
  Given: [preconditions]
  When: [action]
  Then: [expected outcome]
```

Cover these categories:
- **Happy path**: Normal operation works
- **Edge cases**: Boundaries, empty input
- **Errors**: Invalid input, failures
- **Integration**: Connections to other components (if applicable)

Tests define "done" criteria but are ONE part of the plan.

## Step 5: Task Breakdown

Ordered list of work:

| # | Task | Complexity | Dependencies | Risk |
|---|------|------------|--------------|------|
| 1 | ... | Low/Med/High | None/Task# | Low/Med/High |
| 2 | ... | ... | ... | ... |

### Task Ordering Principles
- Prerequisites first
- Riskiest items early (fail fast)
- Tests alongside implementation

## Step 6: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ... | Low/Med/High | Low/Med/High | ... |

### Common Risks
- Incorrect assumptions about existing code
- Missing edge cases
- Performance implications
- Breaking existing functionality

## Step 7: Open Questions

List anything that needs human decision:
- Architectural choices
- Design tradeoffs
- Unclear requirements
- Assumptions that need validation

**Don't proceed past questions that block implementation.**

## Plan Output Summary

Produce a concise plan with:

1. **Summary**: 1-2 sentences describing the goal
2. **Scope**: What's in, what's out
3. **Research Findings**: Key discoveries from Step 2
4. **Test Strategy**: Concrete test cases (from Step 4)
5. **Tasks**: Ordered with dependencies (from Step 5)
6. **Risks**: Top concerns and mitigations
7. **Questions**: Blockers needing human input

## Ask for Approval

After creating the plan, ask:
"Does this plan look correct? Should I proceed with implementation?"

Wait for approval before implementing.
