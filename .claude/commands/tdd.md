---
description: Start test-driven development cycle
allowed-tools: Read, Edit, Write, Bash(uv run pytest:*), Bash(uv run ruff:*), Glob, Grep
argument-hint: <what-to-implement>
---

# TDD Cycle: $ARGUMENTS

## The TDD Rhythm

```
RED → GREEN → REFACTOR → REPEAT
```

### RED: Write a Failing Test

1. Create/find the test file
2. Write ONE test that captures a requirement
3. Run the test - it MUST fail
4. If it passes, your test might be wrong

```bash
uv run pytest tests/path/to/test.py -v -x
```

### GREEN: Make It Pass

1. Write the MINIMUM code to pass the test
2. Don't add extra features
3. Don't worry about elegance yet
4. Just make it green

```bash
uv run pytest tests/path/to/test.py -v
```

### REFACTOR: Clean Up

1. Tests are passing - safe to refactor
2. Improve names, extract functions
3. Remove duplication
4. Run tests after each change

```bash
uv run pytest tests/path/to/test.py -v
```

### REPEAT

Go back to RED with the next requirement.

## Test Location Convention

```
scholardoc/readers/pdf.py     → tests/unit/readers/test_pdf.py
scholardoc/models.py          → tests/unit/test_models.py
scholardoc/normalizers/foo.py → tests/unit/normalizers/test_foo.py
```

## Quick Commands

```bash
# Run specific test
uv run pytest tests/unit/test_models.py::test_function_name -v

# Run with print output
uv run pytest -v -s

# Run and stop on first failure
uv run pytest -v -x

# Run tests matching pattern
uv run pytest -v -k "heading"
```

## Current Focus

$ARGUMENTS
