# Code Review Guide

## Purpose

Catch bugs, security issues, and quality problems before they reach production.

## Principles

1. **Correctness first** - Does it do what it's supposed to do?
2. **Security always** - Never compromise on security checks
3. **Behavior over style** - Functional issues > aesthetic preferences
4. **Evidence-based** - Point to specific lines, not vague concerns
5. **Actionable feedback** - Every issue should have a clear fix

## Review Checklist

### Correctness
- [ ] Does the code do what it's supposed to do?
- [ ] Are edge cases handled?
- [ ] Are error conditions handled appropriately?
- [ ] Are there off-by-one errors, null checks, type issues?

### Security
- [ ] No hardcoded secrets or credentials?
- [ ] Input validation present where needed?
- [ ] No injection vulnerabilities (SQL, command, XSS)?
- [ ] Proper authentication/authorization?
- [ ] Sensitive data handled appropriately?

### Performance
- [ ] No obvious performance issues (N+1, unnecessary loops)?
- [ ] Appropriate data structures used?
- [ ] No resource leaks (files, connections, memory)?
- [ ] Caching considered where appropriate?

### Maintainability
- [ ] Code is readable and self-documenting?
- [ ] Follows existing project patterns?
- [ ] No unnecessary complexity?
- [ ] Appropriate abstractions (not too many, not too few)?

### Testing
- [ ] Tests exist for new functionality?
- [ ] Tests actually test the right thing?
- [ ] Edge cases and error paths tested?
- [ ] Tests are maintainable, not brittle?

## Verdict Definitions

| Verdict | Meaning | When to Use |
|---------|---------|-------------|
| APPROVED | Code is good to merge | No blocking issues |
| CHANGES_REQUESTED | Issues must be fixed | Bugs, security, or significant quality issues |
| BLOCKED | Critical problem | Security vulnerability, data loss risk, architectural violation |

## Issue Severity

| Severity | Description | Examples |
|----------|-------------|----------|
| Critical | Must fix, blocks merge | Security hole, data corruption, crash |
| Major | Should fix before merge | Bug, missing validation, poor error handling |
| Minor | Nice to fix, not blocking | Style, naming, minor optimization |
| Suggestion | Optional improvement | Alternative approach, future consideration |

## Output Format

```markdown
## Code Review

**Verdict**: [APPROVED | CHANGES_REQUESTED | BLOCKED]

### Summary
[Brief overview of changes and overall assessment]

### Issues Found
| File | Line | Severity | Issue | Suggestion |
|------|------|----------|-------|------------|

### Positive Observations
- [Good practices noticed]

### Suggestions (non-blocking)
- [Nice-to-have improvements]
```

## Quality Criteria

A good code review:
- [ ] Covers all checklist areas
- [ ] Issues are specific (file, line, problem)
- [ ] Suggestions are actionable
- [ ] Verdict matches issue severity
- [ ] Acknowledges good work, not just problems

## Anti-patterns

- **Rubber stamping**: Approving without actually reviewing
- **Nitpicking**: Blocking on style when behavior is correct
- **Vague concerns**: "This feels wrong" without specifics
- **Missing the forest**: Focusing on minor issues, missing critical bugs
- **Harsh tone**: Criticism without constructive suggestions

## Adaptation Notes

When generating for a project:
- Include project-specific patterns to check for
- Reference project's lint rules and conventions
- Add project-specific security considerations
- Mention common pitfalls discovered in this codebase
