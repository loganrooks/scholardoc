---
name: gsd:add-todo
description: Capture idea or task as todo from current conversation context (v1.16.0+dev)
argument-hint: [optional description]
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---

<objective>
Capture an idea, task, or issue that surfaces during a GSD session as a structured todo for later work.

Routes to the add-todo workflow which handles:
- Directory structure creation
- Content extraction from arguments or conversation
- Area inference from file paths
- Priority inference (HIGH/MEDIUM/LOW, defaults to MEDIUM)
- Source tracking (command/conversation/phase/signal)
- Duplicate detection and resolution
- Todo file creation with frontmatter
- STATE.md updates
- Git commits
</objective>

<execution_context>
@.planning/STATE.md
@./.claude/get-shit-done/workflows/add-todo.md
</execution_context>

<process>
**Follow the add-todo workflow** from `@./.claude/get-shit-done/workflows/add-todo.md`.

The workflow handles all logic including:
1. Directory ensuring
2. Existing area checking
3. Content extraction (arguments or conversation)
4. Area inference
5. Priority and source inference
6. Duplicate checking
7. File creation with slug generation (includes priority, source, status fields)
8. STATE.md updates
9. Git commits
</process>
