# PR Workflow Guide

## Purpose

Create and review pull requests that enable effective collaboration, maintain code quality, and preserve project history.

## Principles

1. **Small PRs** - Easier to review, faster to merge
2. **One concern per PR** - Don't mix features with refactoring
3. **Self-review first** - Catch obvious issues before others see them
4. **Description matters** - Reviewers need context
5. **Tests required** - No untested code merged

## Creating PRs

### Before Opening PR

```
1. Rebase on latest main
2. Run full test suite
3. Run linters
4. Self-review the diff
5. Ensure commits are clean
```

### PR Title Format

```
type: brief description

Examples:
feat: add user authentication
fix: resolve null pointer in parser
docs: update API documentation
refactor: extract validation logic
test: add integration tests for auth
chore: update dependencies
```

### PR Description Template

```markdown
## Summary
What this PR does in 1-2 sentences.

## Changes
- Specific change 1
- Specific change 2

## Testing
How this was tested:
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing performed

## Screenshots
(If UI changes)

## Related Issues
Closes #123
```

### Commit Hygiene

```
- One logical change per commit
- Imperative mood: "Add feature" not "Added feature"
- Reference issues: "Fix #123: resolve login bug"
- Squash fixup commits before merge
```

## Reviewing PRs

### Review Checklist

**Correctness:**
- [ ] Logic is correct
- [ ] Edge cases handled
- [ ] Error handling appropriate

**Quality:**
- [ ] Code is readable
- [ ] Names are clear
- [ ] No unnecessary complexity

**Testing:**
- [ ] Tests exist for new code
- [ ] Tests are meaningful (not just coverage)
- [ ] Edge cases tested

**Security:**
- [ ] No secrets committed
- [ ] Input validated
- [ ] No injection vulnerabilities

**Documentation:**
- [ ] Public APIs documented
- [ ] Complex logic explained
- [ ] README updated if needed

### Comment Types

```
# Blocking (must fix)
🔴 Bug: This will cause a null pointer exception

# Suggestion (should consider)
🟡 Suggestion: Consider extracting this to a function

# Nitpick (optional)
🟢 Nit: Could rename for clarity

# Question (seeking understanding)
❓ Question: Why did you choose this approach?

# Praise (positive feedback)
✨ Nice: Clean solution!
```

### Review Responses

As author:
```
- Address all blocking comments
- Respond to questions
- Explain if you disagree (with reasoning)
- Don't take feedback personally
```

As reviewer:
```
- Be specific about what needs changing
- Explain why, not just what
- Approve when concerns addressed
- Don't block on nitpicks
```

## PR Size Guidelines

| Size | Lines Changed | Review Time |
|------|--------------|-------------|
| Small | < 200 | < 30 min |
| Medium | 200-500 | 30-60 min |
| Large | > 500 | Break it up |

## Quality Criteria

A good PR:
- [ ] Does one thing
- [ ] Has clear description
- [ ] Tests pass
- [ ] Self-reviewed before requesting review
- [ ] Rebased on latest main
- [ ] Commits are clean and meaningful

## Anti-patterns

- **Mega PR**: 1000+ lines that nobody can review effectively
- **Drive-by commits**: Unrelated changes mixed in
- **Missing context**: Description like "Fix stuff"
- **Review avoidance**: Merging without review
- **Stale PRs**: Open for weeks without attention
- **Defensive responses**: Arguing instead of understanding

## Adaptation Notes

When generating for a project:
- Use project's PR template if it exists
- Reference project's CI requirements
- Include project's branch naming convention
- Note required reviewers or CODEOWNERS
- Include project-specific merge strategy (squash, rebase, merge commit)
