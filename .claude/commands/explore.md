---
description: Safe exploration mode (read-only investigation)
allowed-tools: Read, Glob, Grep, Bash(cat:*), Bash(ls:*), Bash(find:*), Bash(head:*), Bash(tail:*), Bash(wc:*), Bash(git log:*), Bash(git show:*), Bash(uv run pytest:*)
argument-hint: <topic-or-question>
---

# Explore: $ARGUMENTS

**MODE: READ-ONLY EXPLORATION**

In this mode:
- Read any files
- Search the codebase
- Run tests to understand behavior
- Run analysis commands
- **NO editing files**
- **NO creating files**

## Investigation Plan

1. Understand the question/topic
2. Identify relevant files and modules
3. Read and analyze code
4. Run tests if helpful
5. Synthesize findings

## Report Format

After exploration, provide:

### Findings
- What you discovered
- How things currently work
- Relevant code locations (file:line format)

### Architecture Notes
- How components interact
- Data flow
- Key abstractions

### Potential Issues
- Bugs or problems found
- Technical debt
- Inconsistencies

### Recommendations
- Suggested improvements
- Next steps if changes are needed
- Questions that need human input

## Important

Only after exploration is complete, ask if I want to proceed with any changes.
Do not make changes during exploration.
