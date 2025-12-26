---
description: Generate or update documentation for code
allowed-tools: Read, Glob, Grep, Bash(git:*), Bash(ls:*)
argument-hint: <file-or-feature>
---

# Document: $ARGUMENTS

**MODE: DOCUMENTATION GENERATION**

## Step 1: Understand What to Document

- What code/feature needs documentation?
- Who is the audience? (users, developers, maintainers)
- What format is appropriate? (docstrings, README, API docs)

## Step 2: Analyze the Code

Before writing documentation:
- Read the code thoroughly
- Understand the purpose and design
- Identify public API vs internal details
- Note edge cases and gotchas

## Step 3: Documentation Types

### Docstrings (Python)
```python
def function(arg: Type) -> ReturnType:
    """Short description of what function does.

    Longer description if needed, explaining:
    - How it works at a high level
    - When to use it
    - Important behavior notes

    Args:
        arg: Description of the argument

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this happens

    Example:
        >>> function(value)
        expected_result
    """
```

### Module/File Documentation
```python
"""Module name.

Purpose: What this module provides
Usage: How to use it

Key classes/functions:
- ClassName: Brief description
- function_name: Brief description

Dependencies: External dependencies this module requires
"""
```

### README Sections
- **What**: What the project/feature does
- **Why**: Problem it solves
- **How**: Quick start / usage examples
- **Reference**: Detailed API documentation

## Step 4: Quality Checklist

Good documentation:
- [ ] Explains WHY, not just WHAT
- [ ] Includes working examples
- [ ] Covers error cases
- [ ] Uses consistent terminology
- [ ] Stays current with code

Bad documentation:
- [ ] Just restates the code
- [ ] Contains stale/wrong information
- [ ] Missing critical edge cases
- [ ] Assumes too much knowledge

## Step 5: Output Format

Based on the target, generate:

**For functions/classes**: Docstrings in Google/NumPy style
**For modules**: Module-level docstring
**For features**: Markdown documentation
**For APIs**: Usage examples with expected outputs

## Follow Project Conventions

Check existing documentation style:
- Docstring format (Google, NumPy, Sphinx)
- README structure
- Comment style

Match existing patterns.

## Important

- Document behavior, not implementation (unless implementation matters)
- Keep examples simple and runnable
- Update docs when code changes
- Ask if unsure about audience or format
