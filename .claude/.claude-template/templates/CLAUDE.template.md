# {{PROJECT_NAME}}

## Quick Start
1. Read this file
2. Check Serena memories: `project_overview`
3. Run `/project:plan` before changes

## Stack
- **Language**: {{LANGUAGE}}
- **Framework**: {{FRAMEWORK}}
- **Package Manager**: {{PACKAGE_MANAGER}}

## Commands
```bash
# Test
{{TEST_COMMAND}}

# Lint
{{LINT_COMMAND}}

# Build
{{BUILD_COMMAND}}
```

## Health
**Score**: {{HEALTH_SCORE}}/100 | **Assessed**: {{INIT_DATE}}

## Phase
{{PROJECT_PHASE}}

## Workflow
- **Uncertainty**: {{UNCERTAINTY_PREF}}
- **Autonomy**: {{AUTONOMY_PREF}}

## Rules

**ALWAYS:**
- Run tests before committing
- Run lint before committing
{{ADDITIONAL_ALWAYS_RULES}}

**NEVER:**
{{NEVER_RULES}}

## Project Commands
- `/project:auto` - Autonomous development workflow
- `/project:plan` - Create implementation plan
- `/project:explore` - Investigate codebase
- `/project:signal` - Capture feedback/corrections
- `/project:checkpoint` - Save session state
- `/project:resume` - Restore session context

## Architecture
{{ARCHITECTURE_SUMMARY}}

## Key Patterns
{{KEY_PATTERNS}}
