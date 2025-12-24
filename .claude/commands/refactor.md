---
description: Safe refactoring with test verification
allowed-tools: Read, Glob, Grep, Bash(git:*), Bash(ls:*), Bash(uv run pytest:*), Bash(uv run ruff:*)
argument-hint: <code-to-refactor>
---

# Refactor: $ARGUMENTS

**MODE: SAFE REFACTORING**

## Pre-Refactoring Checks

Before ANY changes:

### 1. Test Coverage
- Run existing tests: `uv run pytest`
- Check coverage for affected code
- **STOP if tests are failing** - fix them first

### 2. Understand Current State
- What does the code currently do?
- Who calls this code? (find references)
- What are the edge cases?
- Are there implicit contracts to preserve?

### 3. Create Safety Net
- Ensure all affected code has tests
- If not, **write tests BEFORE refactoring**
- Tests define the behavior we must preserve

## Refactoring Rules

### Small, Incremental Changes
- One refactoring at a time
- Run tests after EACH change
- Commit after each successful step

### Behavior Preservation
- **No functional changes during refactoring**
- If you find a bug, note it but don't fix it now
- Mixing refactoring with bug fixes is dangerous

### Common Refactorings

| Refactoring | Risk | Verify |
|-------------|------|--------|
| Rename | Low | All references updated |
| Extract function | Low | Behavior unchanged |
| Move code | Medium | Imports/dependencies correct |
| Change signature | High | All callers updated |
| Change data structure | High | All access patterns work |

## Refactoring Plan

1. **Goal**: What improvement are we making? (readability, maintainability, performance)
2. **Scope**: What files will be touched?
3. **Steps**: Ordered list of atomic changes
4. **Verification**: How we'll confirm success

## Execution

For each step:
```
1. Make the change
2. Run: uv run pytest
3. Run: uv run ruff check
4. If passing: commit with descriptive message
5. If failing: revert and reassess
```

## Post-Refactoring

- [ ] All tests pass
- [ ] No new linting errors
- [ ] Code is cleaner/more maintainable
- [ ] No behavior changes (intentional or accidental)
- [ ] Consider: Does this suggest a CLAUDE.md pattern?

## Important

- NEVER refactor without tests as a safety net
- NEVER mix refactoring with feature changes
- ALWAYS be able to revert to the previous state
- Ask before starting if scope is unclear
