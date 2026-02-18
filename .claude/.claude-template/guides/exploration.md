# Exploration Guide

## Purpose

Investigate a codebase systematically to understand what exists before making changes.

## Principles

1. **Read-only first** - Understand before modifying
2. **Map before diving** - Get the big picture, then details
3. **Follow the data** - Trace how data flows through the system
4. **Note patterns** - Identify conventions and idioms in use
5. **Surface assumptions** - Make implicit knowledge explicit

## Exploration Approach

### Start Broad
1. Project structure (directories, key files)
2. Entry points (main, index, app)
3. Configuration (package.json, pyproject.toml, etc.)
4. Documentation (README, docs/, CLAUDE.md)

### Then Focus
1. Relevant modules for the task
2. Dependencies and imports
3. Similar existing functionality
4. Related tests

### Trace Connections
1. What calls this code?
2. What does this code call?
3. What data structures are involved?
4. What external services are touched?

## What to Gather

### Structure Information
- Directory layout
- Module organization
- Entry points
- Build/test configuration

### Pattern Information
- Naming conventions
- Code organization patterns
- Error handling patterns
- Testing patterns

### Dependency Information
- Internal dependencies (what imports what)
- External dependencies (libraries, services)
- Circular dependency risks

### Risk Information
- Areas of complexity
- Known issues or tech debt
- Fragile or sensitive code
- Performance bottlenecks

## Exploration Report Format

```markdown
## Exploration: [topic]

### Findings
- What was discovered
- Key file locations (file:line format)
- How things currently work

### Architecture Notes
- Component interactions
- Data flow
- Key abstractions

### Patterns Observed
- Conventions in use
- Idioms followed
- Exceptions to patterns

### Potential Issues
- Bugs or problems found
- Technical debt
- Inconsistencies

### Risks
- Complexity hotspots
- Fragile dependencies
- Performance concerns

### Open Questions
- Things that need clarification
- Ambiguities discovered
- Assumptions to verify
```

## Quality Criteria

Good exploration:
- [ ] Covers the relevant scope (not too narrow, not too broad)
- [ ] Files and locations are specific (file:line, not "somewhere in auth")
- [ ] Patterns are documented, not assumed
- [ ] Risks and issues are surfaced
- [ ] Open questions are explicit

## Anti-patterns

- **Shallow exploration**: Looking at one file and assuming
- **Over-exploration**: Reading the entire codebase for a small change
- **Missing connections**: Not tracing dependencies
- **Implicit patterns**: Noticing conventions but not documenting them
- **Premature conclusions**: Deciding the solution during exploration

## Exploration vs Planning

Exploration answers: "What exists? How does it work?"
Planning answers: "What should we change? How?"

Don't mix them. Complete exploration, then plan.

## Adaptation Notes

When generating for a project:
- Include project-specific directories to explore
- Reference project's documentation locations
- Mention project's common patterns to look for
- Include project-specific tools for investigation
