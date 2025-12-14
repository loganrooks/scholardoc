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

## Step 4: Break Down Tasks

Create ordered task list:
1. [ ] First task (prerequisite for others)
2. [ ] Second task
3. [ ] ...

For each task, note:
- Estimated complexity (low/medium/high)
- Dependencies on other tasks
- Risk factors

## Step 5: Identify Risks

- What could go wrong?
- What assumptions are we making?
- What needs human decision?

## Step 6: Plan Output

Produce a plan document with:
- Summary (1-2 sentences)
- Tasks with order
- Files affected
- Test strategy
- Open questions

## Ask for Approval

After creating the plan, ask:
"Does this plan look correct? Should I proceed with implementation?"
