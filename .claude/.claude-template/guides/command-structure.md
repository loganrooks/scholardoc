# Command Structure Guide

## Purpose

Create Claude Code commands that are clear, maintainable, and effective. Commands encode workflows that can be invoked by name.

## Principles

1. **Single responsibility** - Each command does one coherent thing
2. **Clear inputs** - Arguments and their effects are obvious
3. **Predictable outputs** - Users know what to expect
4. **Self-contained** - Don't rely on CLAUDE.md for essential context
5. **Appropriate size** - Enough detail to guide, not overwhelm

## Command Structure

### Frontmatter

```yaml
---
description: Brief one-line description for listing
allowed-tools: Tool1, Tool2, Tool3
argument-hint: [arg1] [--flag]
---
```

**Tool selection:**
- Read/Write/Edit: File operations
- Bash: Shell commands
- Glob/Grep: File finding/searching
- Task: Spawning subagents
- AskUserQuestion: User interaction
- mcp__*: MCP server tools

### Sections

```markdown
# Command Name: $ARGUMENTS

## Purpose
What this command accomplishes (1-2 sentences).

## When to Use
- Scenario 1
- Scenario 2

## Process

### Phase 1: [Name]
What to do and why.

### Phase 2: [Name]
...

## Outputs
What gets created/modified.

## Examples
Show concrete usage.
```

## Size Guidelines

| Command Type | Target Size | Notes |
|--------------|-------------|-------|
| Simple | 50-100 lines | Single focused action |
| Standard | 100-200 lines | Multi-phase workflow |
| Complex | 200-400 lines | Major orchestration |
| Init-style | 400-700 lines | One-time comprehensive setup |

**Remember**: Commands load at session start, not on invoke. Size affects every session.

## Common Patterns

### Exploration Command
```markdown
# Explore: $ARGUMENTS

## Purpose
Investigate [topic] without making changes.

## Process
1. Search for relevant code
2. Read key files
3. Understand patterns
4. Report findings

## Output
Summary of findings, no modifications.
```

### Implementation Command
```markdown
# Implement: $ARGUMENTS

## Purpose
Build [feature] using TDD workflow.

## Process
1. Plan (tests first)
2. Implement (red-green-refactor)
3. Verify (run all tests)
4. Document

## Output
Working code with tests.
```

### Review Command
```markdown
# Review: $ARGUMENTS

## Purpose
Evaluate [target] against quality criteria.

## Process
1. Read the code
2. Check against criteria
3. Identify issues
4. Report findings

## Output
Review report with recommendations.
```

## Tool Scoping

### Minimal (Read-Only)
```yaml
allowed-tools: Read, Glob, Grep
```
For exploration and analysis.

### Standard (File Changes)
```yaml
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
```
For implementation work.

### Full (Agent Spawning)
```yaml
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task, AskUserQuestion
```
For orchestration commands.

### MCP-Enhanced
```yaml
allowed-tools: ..., mcp__serena__*, mcp__sequential-thinking__*
```
For commands needing semantic understanding or complex reasoning.

## Quality Criteria

A good command:
- [ ] Has clear, specific purpose
- [ ] Tools are appropriately scoped
- [ ] Process is sequential and logical
- [ ] Examples show concrete usage
- [ ] Doesn't duplicate CLAUDE.md content
- [ ] Size is appropriate for purpose

## Anti-patterns

- **Kitchen sink**: Command that tries to do everything
- **Vague process**: "Analyze the code" without specifics
- **Wrong tool scope**: Read-only command with Write access
- **CLAUDE.md duplication**: Repeating project rules in command
- **No examples**: Hard to understand intended use
- **Overly prescriptive**: Too rigid for varied situations

## Adaptation Notes

When generating for a project:
- Include project-specific tools and commands
- Reference project conventions
- Match project's command naming style
- Size based on actual workflow complexity
- Include project-relevant examples
