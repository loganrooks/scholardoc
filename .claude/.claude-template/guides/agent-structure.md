# Agent Structure Guide

## Purpose

Create Claude Code agents that perform focused tasks reliably. Agents are invoked by the Task tool and run in isolated context.

## Principles

1. **Bounded scope** - Agents can't see full conversation history
2. **Focused purpose** - One job, done well
3. **Clear outputs** - Structured results that callers can use
4. **Right model** - Match model capability to task needs
5. **Gatherer vs Analyst** - Know which role the agent plays

## Agent Structure

### Frontmatter

```yaml
---
name: agent-name
description: When to invoke this agent (for auto-delegation)
tools: Tool1, Tool2, Tool3
model: sonnet | opus | haiku
---
```

### Sections

```markdown
# Agent Name

## Role
What this agent does (1-2 sentences).

## Scope
### In Scope
- What to analyze/do
- Specific directories/files

### Out of Scope
- What NOT to do
- What other agents handle

## Process
Step-by-step instructions.

## Output Format
Exact structure of results.

## Guidelines
Important considerations.
```

## Model Selection

| Model | Use For | Cost |
|-------|---------|------|
| **haiku** | Simple, fast tasks (formatting, simple extraction) | $ |
| **sonnet** | Most exploration and analysis (gathering, reviewing) | $$ |
| **opus** | Complex judgment, synthesis, planning | $$$ |

**Default to sonnet** unless task is trivially simple (haiku) or requires deep judgment (opus).

## Agent Types

### Gatherer Agent
Collects information, doesn't make judgments.
```markdown
## Role
Gather [information type] from the codebase.

## Output Format
### Findings
- [Raw data, counts, file lists]

### Patterns Observed
- [What was seen, not interpreted]

### Uncertainties
- [What couldn't be determined]
```

### Reviewer Agent
Evaluates against criteria, makes recommendations.
```markdown
## Role
Review [target] against [criteria].

## Output Format
### Assessment
| Criterion | Status | Notes |
|-----------|--------|-------|
| ... | Pass/Fail/Partial | ... |

### Issues Found
- [Severity]: [Issue description]

### Recommendations
- [What should change]
```

### Diagnostic Agent
Investigates problems, identifies root causes.
```markdown
## Role
Diagnose [problem type].

## Output Format
### Symptoms
- [What was observed]

### Investigation
- [Steps taken, evidence gathered]

### Root Cause
[Most likely cause with reasoning]

### Fix Recommendation
[Specific action to resolve]
```

## Tool Scoping

### Read-Only
```yaml
tools: Read, Glob, Grep
```
For gatherers and explorers.

### With Execution
```yaml
tools: Read, Glob, Grep, Bash
```
For agents that need to run commands (linters, tests).

### With Edits
```yaml
tools: Read, Write, Edit, Glob, Grep, Bash
```
For agents that implement changes (rare - most agents report, don't modify).

## Output Structure Best Practices

### Use Markdown Tables
```markdown
| Item | Status | Details |
|------|--------|---------|
| ... | ... | ... |
```

### Use Consistent Headers
```markdown
## Findings
## Issues
## Recommendations
## Uncertainties
```

### Be Specific
```markdown
# Bad
"There are some issues with the code"

# Good
"Found 3 type errors in src/parser.ts:45, :89, :123"
```

## Quality Criteria

A good agent:
- [ ] Has clear, bounded scope
- [ ] Uses appropriate model for task
- [ ] Tools match what's needed
- [ ] Output format is structured and parseable
- [ ] Doesn't try to do too much
- [ ] Can be invoked by Task tool successfully

## Anti-patterns

- **Scope creep**: Agent tries to do everything
- **Wrong model**: Using opus for simple gathering
- **Unstructured output**: Prose instead of structured findings
- **Over-tooled**: Write access for read-only task
- **Duplicated logic**: Same checks in multiple agents
- **Hidden dependencies**: Assumes context not provided

## Adaptation Notes

When generating for a project:
- Match existing agent naming conventions
- Reference project-specific tools/commands
- Include relevant file paths
- Use project terminology
- Size agent scope to project complexity
