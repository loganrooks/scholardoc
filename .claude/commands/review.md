---
description: Review recent changes and code quality
allowed-tools: Read, Glob, Grep, Bash(git:*), Bash(uv run pytest:*), Bash(uv run ruff:*)
argument-hint: [commit-range or file-path]
---

# Review: $ARGUMENTS

## Step 1: Identify Changes

```bash
# Recent commits
git log --oneline -10

# Changes in working directory
git status
git diff

# Specific commit changes
git show <commit>
```

## Step 2: Run Quality Checks

```bash
# Lint check
uv run ruff check scholardoc/ tests/

# Type check (if configured)
uv run mypy scholardoc/

# Run tests
uv run pytest -v
```

## Step 3: Code Review Checklist

For each changed file, check:

### Correctness
- [ ] Does the code do what it's supposed to?
- [ ] Are edge cases handled?
- [ ] Are errors handled gracefully?

### Style
- [ ] Follows existing patterns?
- [ ] Clear variable/function names?
- [ ] Appropriate comments (not too many, not too few)?

### Testing
- [ ] Tests exist for new functionality?
- [ ] Tests actually test the right thing?
- [ ] Edge cases tested?

### Documentation
- [ ] Docstrings for public functions?
- [ ] README updated if needed?
- [ ] CHANGELOG updated?

### Security
- [ ] No hardcoded secrets?
- [ ] Input validation where needed?
- [ ] No obvious vulnerabilities?

## Step 4: Summary

Provide:
- Overall assessment (good/needs work/concerns)
- Specific issues found
- Recommendations
- Questions for the author

## Output Format

```
## Review Summary

**Status**: [APPROVED / NEEDS CHANGES / QUESTIONS]

### Strengths
- ...

### Issues
- [file:line] Issue description

### Recommendations
- ...
```
