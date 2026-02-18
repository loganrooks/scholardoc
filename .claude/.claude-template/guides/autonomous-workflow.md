# Autonomous Development Workflow

## Purpose

Guide autonomous development from requirements to completion with appropriate human oversight and quality gates.

## Principles

1. **Requirements before action** - Never implement without confirmed requirements
2. **Explore before planning** - Understand the codebase before designing changes
3. **Plan before coding** - Design the solution before implementing
4. **Test-driven** - Write tests first, implementation second
5. **Incremental progress** - Small commits, frequent checkpoints
6. **Self-review gates** - Validate each phase before proceeding
7. **Explicit escalation** - Return to human when uncertain, blocked, or scope changes

## Workflow Phases

### Phase 0: Requirements Lock-in
**Human-in-loop required**

- Parse the request for intent
- Identify ambiguities, unknowns, implicit assumptions
- Ask clarifying questions (scope, success criteria, constraints)
- Present requirements summary for approval
- **Gate**: Human approves before proceeding

### Phase 1: Exploration
- Investigate relevant code, patterns, dependencies
- Map what exists and how it works
- Identify risks and constraints
- **Gate**: Exploration reviewer validates completeness

### Phase 2: Planning
- Define scope (in/out)
- Design test strategy (Given/When/Then)
- Break into ordered tasks with dependencies
- Assess risks and mitigations
- **Gate**: Plan reviewer validates feasibility

### Phase 3: Implementation
- TDD cycle: test → implement → refactor
- Checkpoint after each significant change
- Update progress in memory
- **Gate**: Code reviewer validates quality

### Phase 4: Validation
- Run full test suite
- Run linter/type checker
- Verify no regressions
- **Gate**: All checks pass

### Phase 5: Completion
- Final commit with descriptive message
- Update session memory with outcomes
- Report summary to human

## Gate Verdicts

| Verdict | Action |
|---------|--------|
| APPROVED | Proceed to next phase |
| NEEDS_WORK | Address issues, re-review |
| BLOCKED | Escalate to human |

## Escalation Triggers

Return to human oversight when:
- Requirements change during development
- Architectural decision challenged by evidence
- Security or data integrity concern discovered
- Same issue fails 3+ attempts
- Reviewer gives BLOCKED verdict twice
- Uncertainty about correct approach

When escalating, provide:
- Current state and progress
- Nature of the blocker
- Options considered
- Recommended path forward

## Quality Criteria

A good autonomous workflow command:
- [ ] Has clear phase boundaries
- [ ] Specifies gate conditions for each phase
- [ ] References project-specific commands (test, lint)
- [ ] Defines escalation triggers
- [ ] Produces a completion report
- [ ] Updates memory for session continuity

## Anti-patterns

- **Skipping requirements**: Implementing based on assumptions
- **Shallow exploration**: Missing dependencies or patterns
- **Monolithic implementation**: Large changes without checkpoints
- **Ignoring gate failures**: Proceeding despite NEEDS_WORK
- **Silent failure**: Not escalating when stuck
- **Incomplete reports**: Not documenting what was done

## Adaptation Notes

When generating for a project:
- Insert actual test/lint/build commands from CLAUDE.md
- Reference project's reviewer agents by name
- Include project-specific escalation criteria if any
- Adjust phase detail based on project complexity
