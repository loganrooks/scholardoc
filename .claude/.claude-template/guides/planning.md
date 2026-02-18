# Planning Guide

## Purpose

Create implementation plans that prevent wasted effort, catch issues early, and enable confident execution.

## Principles

1. **Understand before designing** - Research current state first
2. **Scope explicitly** - Define what's in AND what's out
3. **Tests define done** - Specify how success will be verified
4. **Order by risk** - Tackle risky/uncertain items early (fail fast)
5. **Surface unknowns** - Questions are findings, not failures

## Plan Structure

### 1. Summary
One sentence: what are we doing and why?

### 2. Research Findings
What we learned from exploration:
- Relevant code locations
- Existing patterns to follow
- Dependencies involved
- Prior art or similar implementations

### 3. Scope Definition

**In Scope:**
- Specific changes to make
- Files to create/modify
- Tests to write

**Out of Scope:**
- What this does NOT include
- Related improvements deferred
- Future considerations

### 4. Test Strategy
Define verification using Given/When/Then:

```
test_<behavior>_<scenario>:
  Given: [preconditions]
  When: [action]
  Then: [expected outcome]
```

Cover:
- Happy path (normal operation)
- Edge cases (boundaries, empty input)
- Error conditions (invalid input, failures)

### 5. Task Breakdown

| # | Task | Complexity | Dependencies | Risk |
|---|------|------------|--------------|------|
| 1 | ... | Low/Med/High | None | Low/Med/High |

Ordering principles:
- Prerequisites before dependents
- High-risk items early
- Tests alongside implementation

### 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ... | Low/Med/High | Low/Med/High | ... |

Common risks:
- Incorrect assumptions about existing code
- Missing edge cases
- Performance implications
- Breaking existing functionality

### 7. Open Questions
Blockers needing human decision:
- Architectural choices
- Design tradeoffs
- Unclear requirements
- Assumptions needing validation

**Do not proceed past blocking questions.**

## Quality Criteria

A good plan:
- [ ] Has clear, measurable success criteria
- [ ] Scope is explicit (in AND out)
- [ ] Tasks are ordered with dependencies
- [ ] Risks are identified with mitigations
- [ ] Unknowns are surfaced, not hidden
- [ ] Can be executed without further clarification

## Anti-patterns

- **Vague scope**: "Improve the system" without specifics
- **Missing tests**: No verification strategy
- **Hidden assumptions**: Unstated beliefs that might be wrong
- **Over-planning**: Excessive detail for simple tasks
- **Under-planning**: Skipping risk assessment for complex tasks
- **Optimistic ordering**: Leaving risky items for last

## Adaptation Notes

When generating for a project:
- Reference project's test framework and conventions
- Include project-specific documentation to check (SPEC, REQUIREMENTS, etc.)
- Mention relevant existing patterns found during exploration
- Adjust detail level based on project phase (early = more exploration, mature = more precision)
