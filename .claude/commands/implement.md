---
description: TDD implementation workflow (tests first)
allowed-tools: Read, Edit, Write, Bash(uv:*), Bash(git:*), Glob, Grep
argument-hint: <feature-description>
---

# Implement: $ARGUMENTS

Follow this TDD workflow strictly:

## Step 1: Understand

Before writing any code:
- What problem does this solve?
- What are the inputs/outputs?
- What are the edge cases?
- Check SPEC.md for relevant data models
- Check QUESTIONS.md for unresolved decisions

## Step 2: Write Tests First

Create test file in appropriate location:
- Unit tests: `tests/unit/<module>/test_<feature>.py`
- Integration tests: `tests/integration/test_<feature>.py`

Write tests for:
- [ ] Happy path - normal operation
- [ ] Edge cases - boundary conditions
- [ ] Error conditions - expected failures

Run tests to confirm they FAIL:
```bash
uv run pytest tests/unit/path/to/test_file.py -v
```

**DO NOT PROCEED until tests are written and failing.**

## Step 3: Implement Minimum Code

Write just enough code to make tests pass.
- Follow existing patterns in the codebase
- Check SPEC.md for API design
- Hooks will auto-format and lint your code

## Step 4: Refactor

With passing tests, improve the code:
- Extract helper functions if needed
- Improve variable naming
- Add type hints for public APIs
- Keep it simple - no over-engineering

## Step 5: Document

- Add docstrings to public functions
- Update README.md if adding user-facing features
- Update CHANGELOG.md with the change
- If architectural decision, create ADR

## Step 6: Commit

```bash
git add -A
git status
git commit -m "feat: <concise description>"
```

## Current Project Context

- **Phase**: 0 (Exploration) - TDD relaxed for spikes
- **Stack**: Python 3.11+, PyMuPDF, pytest
- **Docs**: SPEC.md, REQUIREMENTS.md, ROADMAP.md
