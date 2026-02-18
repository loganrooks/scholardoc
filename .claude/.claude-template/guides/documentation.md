# Documentation Guide

## Purpose

Create documentation that helps users and developers understand, use, and contribute to the project effectively.

## Principles

1. **Audience first** - Know who you're writing for
2. **Show, don't tell** - Examples over explanations
3. **Keep it current** - Outdated docs are worse than none
4. **Layer complexity** - Quick start → Details → Reference
5. **Verify accuracy** - Test all code examples

## Documentation Types

### README.md (Entry Point)
Target: New visitors deciding whether to use project
```markdown
# Project Name

One-line description

## Quick Start
Minimum steps to get running

## Features
What it does (bullet points)

## Installation
How to install

## Usage
Basic example

## Documentation
Link to full docs

## Contributing
How to help

## License
```

### API Documentation
Target: Developers integrating with your code
```markdown
## function_name(param1, param2)

Brief description of what it does.

### Parameters
- `param1` (type): Description
- `param2` (type, optional): Description. Default: value

### Returns
- (type): Description

### Raises
- `ErrorType`: When this happens

### Example
\`\`\`python
result = function_name("value", option=True)
\`\`\`
```

### Tutorials
Target: Users learning to accomplish specific tasks
```markdown
# How to [Accomplish Goal]

## Prerequisites
What you need before starting

## Steps

### 1. First Step
Explanation
\`\`\`
code
\`\`\`
Expected result

### 2. Second Step
...

## Troubleshooting
Common issues and solutions

## Next Steps
Related tutorials
```

### Architecture Documentation
Target: Contributors understanding system design
```markdown
# Architecture Overview

## System Context
How this fits in larger ecosystem

## Components
- Component A: Purpose
- Component B: Purpose

## Data Flow
How information moves through system

## Key Decisions
Why things are the way they are (link to ADRs)
```

### ADRs (Architecture Decision Records)
Target: Future maintainers understanding past decisions
```markdown
# ADR-001: [Decision Title]

## Status
Accepted | Superseded | Deprecated

## Context
What situation prompted this decision

## Decision
What we decided

## Consequences
What results from this decision (good and bad)
```

## Documentation Locations

| Type | Location | Update Frequency |
|------|----------|-----------------|
| README | Project root | Each release |
| API docs | Near code (docstrings) | With code changes |
| Tutorials | docs/ | As needed |
| ADRs | docs/adr/ | On major decisions |
| Changelog | CHANGELOG.md | Each release |

## Quality Criteria

Good documentation:
- [ ] Has clear audience identified
- [ ] Includes working code examples
- [ ] Is accurate (matches current behavior)
- [ ] Is discoverable (linked from README)
- [ ] Is scannable (headers, lists, code blocks)
- [ ] Explains WHY, not just WHAT

## Anti-patterns

- **Wall of text**: No structure, no code examples
- **Stale docs**: Doesn't match current code
- **Jargon overload**: Unexplained terminology
- **Missing context**: Assumes too much knowledge
- **Buried important info**: Key details hard to find
- **No examples**: Theory without demonstration
- **Copy-paste errors**: Examples that don't work

## Adaptation Notes

When generating for a project:
- Match project's existing doc style
- Use project's terminology consistently
- Reference actual project paths and commands
- Include project-specific setup requirements
- Link to project's existing documentation
