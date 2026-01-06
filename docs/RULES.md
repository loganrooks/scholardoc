# ScholarDoc Development Rules

## ALWAYS

1. **Explore First** - Run spikes before implementing new features
2. **Consult SPEC.md** - Check data models and API design before coding
3. **Write Tests First** - TDD workflow, use `/project:tdd`
4. **Graceful Degradation** - Handle failures gracefully, never hard crash
5. **Preserve Source Info** - Maintain page numbers, positions, citations
6. **Check QUESTIONS.md** - Don't implement unresolved decisions
7. **Use Feature Branches** - Never commit directly to main

## NEVER

1. **Implement Unvalidated Features** - Spikes must validate approaches first
2. **Trust SPEC Over Evidence** - Empirical findings trump documentation
3. **Make Architectural Decisions Without ADR** - Document in docs/adr/
4. **Skip Planning Documents** - Read ROADMAP.md, SPEC.md, QUESTIONS.md
5. **Add Chunking** - Out of scope (see REQUIREMENTS.md)
6. **Use `rm -rf` or `sudo`** - Blocked by hooks
7. **Force Push to Main** - Blocked by hooks

## Code Quality Standards

- **Python 3.11+** - Use modern Python features
- **Type Hints** - Required for all public APIs
- **Docstrings** - Required for modules, classes, public functions
- **Ruff** - Code formatting and linting (runs automatically)
- **pytest** - Test framework with hypothesis for property testing

## Decision Making

When facing architectural decisions:
1. Check existing ADRs in `docs/adr/`
2. If no ADR exists, create one before implementing
3. Document trade-offs and alternatives considered
4. Get review before major changes

## Error Handling Philosophy

- **Graceful degradation** over hard failures
- **Preserve partial results** when possible
- **Log warnings** for recoverable issues
- **Raise exceptions** only for unrecoverable errors
- **Provide context** in error messages
