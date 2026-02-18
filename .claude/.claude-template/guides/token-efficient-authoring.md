# Token-Efficient Authoring Guide

## Purpose

Guide for generating commands, agents, and configuration artifacts that minimize token overhead while preserving clarity and effectiveness.

**Why this matters**: Every artifact you generate loads into context at session start. A 200-line command that could be 100 lines costs tokens on every session, not just when invoked.

## Core Principles

### 1. Density Over Volume

| Instead of | Use |
|------------|-----|
| Long explanatory paragraphs | Bullet points or tables |
| Multiple similar examples | One clear example |
| Repeated instructions | Reference to guide |
| Verbose conditionals | Decision tables |

### 2. Structure Carries Meaning

Good structure reduces need for explanation:

```markdown
## Bad: Verbose
First, you should check if there are any uncommitted changes.
If there are uncommitted changes, you should either commit them
or stash them before proceeding. This is important because...

## Good: Structured
### Prerequisites
- No uncommitted changes (commit or stash first)
```

### 3. Reference, Don't Duplicate

If a guide exists, reference it:

```markdown
## Bad: Duplicating
When writing tests, follow TDD: write failing test first,
implement minimal code, refactor. Use Given/When/Then format...
[50 more lines of TDD explanation]

## Good: Referencing
Follow TDD workflow per `guides/tdd.md`.
```

## Size Budgets

| Artifact Type | Target | Max | Notes |
|---------------|--------|-----|-------|
| Simple command | 50-80 lines | 100 | Single focused action |
| Standard command | 100-150 lines | 200 | Multi-phase workflow |
| Complex command | 200-300 lines | 400 | Major orchestration |
| Agent template | 80-120 lines | 150 | Focused analysis task |
| Review agent | 60-100 lines | 120 | Checklist-driven |

**If exceeding max**: Split into multiple commands or extract to guide.

## Writing Patterns

### Commands

```markdown
## Good Pattern
# Command: $ARGUMENTS

Brief purpose (1 sentence).

## Process
1. First step
2. Second step
3. Third step

## Output
What gets produced.
```

```markdown
## Anti-pattern
# Command: $ARGUMENTS

## Overview
This command is designed to help you accomplish [task].
It was created because [history]. You might want to use
this when [scenarios]...

## Background
Before we begin, it's important to understand...
[100 lines of context that belongs in a guide]
```

### Conditionals

```markdown
## Good: Decision Table
| Condition | Action |
|-----------|--------|
| Tests pass | Continue to commit |
| Tests fail | Fix before proceeding |
| No tests | Ask user |

## Bad: Verbose If-Then
If the tests pass, then you should continue to the commit phase.
However, if the tests fail, you should not proceed but instead
fix the failing tests first. In the case where there are no tests...
```

### Examples

```markdown
## Good: One Clear Example
Example:
```bash
/plan add user authentication
```

## Bad: Multiple Redundant Examples
Example 1:
```bash
/plan add user authentication
```

Example 2:
```bash
/plan implement caching layer
```

Example 3:
```bash
/plan refactor database module
```
(All show the same pattern)
```

### Tool Specifications

```markdown
## Good: Compact
allowed-tools: Read, Edit, Bash(git:*), mcp__serena__*

## Acceptable: Categorized (if complex)
allowed-tools:
  - File: Read, Edit, Write
  - Search: Glob, Grep
  - Shell: Bash(git:*), Bash(npm:*)
```

## Token Cost Reference

Approximate token costs to inform decisions:

| Content | ~Tokens |
|---------|---------|
| 1 line of markdown | 10-15 |
| Simple table (5 rows) | 50-80 |
| Code block (10 lines) | 80-120 |
| Paragraph (3 sentences) | 40-60 |
| Full example with context | 100-200 |

**Implication**: A table with 5 rows often conveys more than a 5-paragraph explanation at 1/3 the tokens.

## Artifact-Specific Guidance

### Commands

1. **Frontmatter**: Keep description under 80 chars
2. **Purpose**: One sentence, not a paragraph
3. **Process**: Numbered steps, not prose
4. **Examples**: One per use case, max 2-3 total
5. **Notes**: Only if genuinely needed

### Agents

1. **Focus**: Single analysis domain
2. **Output format**: Specify structure, not content
3. **Checklist style**: Questions/checks, not instructions
4. **Verdict**: Clear pass/fail criteria

### CLAUDE.md Sections

1. **Project-specific only**: Don't repeat framework content
2. **Concise rules**: One line per rule
3. **Reference paths**: Don't explain file contents
4. **Commands list**: Just names + one-line descriptions

## Quality Checklist

Before finalizing any generated artifact:

- [ ] Under size budget?
- [ ] No duplicated guide content?
- [ ] Tables used where appropriate?
- [ ] Examples minimal but clear?
- [ ] Every section necessary?
- [ ] Could any paragraph be a bullet list?
- [ ] Could any list be a table?

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| "Wall of text" | Dense paragraphs | Use structure |
| "Example overload" | 5+ similar examples | Keep 1-2 |
| "Guide duplication" | Repeating tdd.md content | Reference it |
| "Defensive verbosity" | Over-explaining obvious things | Trust the reader |
| "Kitchen sink" | Command does everything | Split it |
| "Placeholder prose" | "This section describes..." | Just describe it |

## Compression Techniques

When editing for size:

1. **Remove meta-commentary**: "In this section we will..." → just do it
2. **Collapse conditions**: Multiple if-then → decision table
3. **Merge similar steps**: "Read file A. Read file B." → "Read files A and B"
4. **Extract to guide**: Reusable content → new guide + reference
5. **Trust conventions**: Don't explain standard patterns

## Summary

**Goal**: Maximum clarity per token

**Method**: Structure, reference, compress

**Test**: "Could this be shorter without losing meaning?"
