---
description: Systematic debugging with hypothesis testing
allowed-tools: Read, Glob, Grep, Bash(git:*), Bash(ls:*), Bash(cat:*), Bash(uv run pytest:*), Bash(python:*)
argument-hint: <error-or-symptom>
---

# Debug: $ARGUMENTS

**MODE: SYSTEMATIC DEBUGGING**

## Step 1: Reproduce the Issue

First, confirm the problem is reproducible:
- What are the exact steps to trigger it?
- What is the expected behavior?
- What is the actual behavior?
- Can you reproduce it consistently?

**DO NOT proceed until you can reproduce the issue.**

## Step 2: Gather Evidence

Collect information before forming hypotheses:
- Error messages and stack traces
- Relevant log output
- Recent changes (git log, git diff)
- Related test failures

## Step 3: Form Hypotheses

Based on evidence, list 2-3 possible root causes:

| # | Hypothesis | Evidence For | Evidence Against |
|---|------------|--------------|------------------|
| 1 | ... | ... | ... |
| 2 | ... | ... | ... |
| 3 | ... | ... | ... |

## Step 4: Test Hypotheses

For each hypothesis (starting with most likely):
1. Design a test that would confirm/refute it
2. Run the test
3. Record the result
4. Update hypothesis ranking

**Key principle:** Eliminate wrong hypotheses quickly, don't just confirm the one you like.

## Step 5: Identify Root Cause

Once you've found the root cause:
- Explain WHY it causes the observed behavior
- Trace the causal chain from root cause to symptom
- Identify if there are related issues

## Step 6: Propose Fix

Present the fix with:
- What needs to change
- Files affected
- Test strategy to verify fix
- Risk assessment (what could this break?)

## Step 7: Reflect and Learn

After fixing:
- Why wasn't this caught earlier?
- Should we add a test to prevent regression?
- Is there a CLAUDE.md rule that would help?

Use: "Reflect, abstract, generalize, add to CLAUDE.md"

## Important

- Don't jump to solutions before understanding the problem
- Don't make multiple changes at once - isolate variables
- Ask before implementing the fix
