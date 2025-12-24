---
description: Create implementation plan before coding
allowed-tools: Read, Glob, Grep, Bash(git:*), Bash(ls:*), Bash(find:*)
argument-hint: <feature-or-task>
---

# Plan: $ARGUMENTS

## Step 1: Understand the Request

- What exactly is being asked?
- What problem does this solve?
- Who benefits from this?

## Step 2: Research Current State

Check existing code:
- Related modules and functions
- Existing patterns to follow
- Tests that might be affected

Check documentation:
- SPEC.md for design guidance
- REQUIREMENTS.md for acceptance criteria
- QUESTIONS.md for unresolved decisions
- ROADMAP.md for current phase

## Step 3: Identify Scope

**In Scope:**
- List specific changes needed
- Files to create/modify
- Tests to write

**Out of Scope:**
- What this does NOT include
- Future considerations
- Dependencies to avoid

## Step 4: Define TDD Anchors

**These are the tests that will drive implementation.** Be specific about behavior.

### Test Cases to Write First
For each major behavior, define concrete test cases:

```
test_<behavior>_<scenario>:
  Given: [preconditions]
  When: [action]
  Then: [expected outcome]
```

Example:
```
test_convert_simple_pdf_returns_scholar_document:
  Given: A single-page PDF with plain text
  When: convert(path) is called
  Then: Returns ScholarDocument with text content

test_convert_missing_file_raises_error:
  Given: Path to non-existent file
  When: convert(path) is called
  Then: Raises FileNotFoundError with helpful message
```

Categories to cover:
- [ ] Happy path (normal operation)
- [ ] Edge cases (empty input, boundaries)
- [ ] Error conditions (invalid input, missing deps)
- [ ] Integration points (if connecting components)

These test cases become the "done" criteria and drive the `/project:implement` phase.

## Step 5: Break Down Tasks

Create ordered task list:
1. [ ] First task (prerequisite for others)
2. [ ] Second task
3. [ ] ...

For each task, note:
- Estimated complexity (low/medium/high)
- Dependencies on other tasks
- Risk factors

## Step 6: Identify Risks

- What could go wrong?
- What assumptions are we making?
- What needs human decision?

## Step 7: Plan Output

Produce a plan document with:
- Summary (1-2 sentences)
- TDD Anchors (specific test cases from Step 4)
- Tasks with order
- Files affected
- Open questions

The TDD anchors are the most important output - they define "done" and drive implementation.

## Ask for Approval

After creating the plan, ask:
"Does this plan look correct? Should I proceed with implementation?"
