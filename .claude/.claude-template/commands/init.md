---
description: Initialize autonomous development system with comprehensive codebase analysis
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task, AskUserQuestion, mcp__serena__*, mcp__sequential-thinking__*
argument-hint: "[mode: full|minimal|validate|reset]"
---

# Project Initialization: $ARGUMENTS

**Orchestrates comprehensive project analysis through 9 parallel gatherer agents, synthesizes findings, and generates a project-specific development ecosystem.**

---

## Mode Selection

| Mode | Purpose |
|------|---------|
| `full` (default) | 6-phase initialization with all 9 gatherer agents |
| `minimal` | Quick setup - basic detection, skip exploration |
| `validate` | Health check existing setup |
| `reset` | Clear .claude/ and reinitialize |

---

## Phase 0: PREREQUISITES

### 0.1 MCP Server Check

```bash
echo "=== MCP Prerequisites ==="
```

**Required:**
1. **Serena** - Project memory and semantic understanding
2. **Sequential-Thinking** - Complex analysis support

Test availability by calling each. If missing, offer installation guidance or degraded mode.

### 0.2 Project Type Detection

```bash
# Language detection
[ -f package.json ] && echo "NODE"
[ -f pyproject.toml ] && echo "PYTHON"
[ -f Cargo.toml ] && echo "RUST"
[ -f go.mod ] && echo "GO"

# Framework detection
grep -qE "react|vue|angular" package.json 2>/dev/null && echo "FRONTEND"
grep -qE "next|nuxt|remix" package.json 2>/dev/null && echo "FULLSTACK"
grep -qE "express|fastify" package.json 2>/dev/null && echo "BACKEND"
grep -qE "django|flask|fastapi" pyproject.toml 2>/dev/null && echo "PYTHON_WEB"
```

Store detected type for agent customization.

---

## Phase 1: EXPLORATION (9 Parallel Gatherers)

**SKIP IF**: minimal or validate mode

Launch 9 gatherer agents in parallel. Each collects data in its scope. **Agents do NOT analyze or recommend - they return raw findings for Opus to synthesize.**

### 1.1 Spawn All Agents

```
# All 9 run simultaneously with non-overlapping scopes

Task(subagent_type="Explore", model="sonnet", description="Environment data", prompt="""
Read and follow: .claude/init-agents/env-analyzer.md

You are a GATHERER. Collect data about the user's Claude environment:
- ~/.claude/ configuration
- MCP servers available
- User's global agents and commands
- Project .claude/ if exists

Return structured data. Do NOT evaluate quality or make recommendations.
""")

Task(subagent_type="Explore", model="sonnet", description="Project identity", prompt="""
Read and follow: .claude/init-agents/project-identity.md

You are a GATHERER. Collect data about project identity:
- Package manifest content
- README content
- Type indicators (directories, frameworks)
- Maturity signals (version, commits, tags)

Return raw data. Do NOT interpret or recommend.
""")

Task(subagent_type="Explore", model="sonnet", description="Workflow data", prompt="""
Read and follow: .claude/init-agents/workflow-analyzer.md

You are a GATHERER. Collect workflow data:
- CI/CD configuration (verbatim)
- Git commit patterns (counts)
- Scripts from package.json/Makefile
- Hook configuration

Return exact commands and counts. Do NOT evaluate.
""")

Task(subagent_type="Explore", model="sonnet", description="Architecture data", prompt="""
Read and follow: .claude/init-agents/architecture-analyzer.md

You are a GATHERER. Collect architecture data:
- Directory structure
- Import patterns
- Entry points
- Index/barrel files

Return structure and counts. Do NOT judge boundaries or patterns.
""")

Task(subagent_type="Explore", model="sonnet", description="Code quality data", prompt="""
Read and follow: .claude/init-agents/code-quality.md

You are a GATHERER. Collect quality metrics:
- Linter configuration and OUTPUT (run linters)
- File size statistics
- Technical debt marker counts
- Type safety configuration

Return numbers and raw output. Do NOT prioritize issues.
""")

Task(subagent_type="Explore", model="sonnet", description="Security data", prompt="""
Read and follow: .claude/init-agents/security-analyzer.md

You are a GATHERER. Collect security data:
- Potential secret LOCATIONS (never values)
- Dependency audit OUTPUT (run npm audit etc.)
- Auth-related file locations
- .env handling status

CRITICAL: Never include actual secrets. Return locations and audit output only.
""")

Task(subagent_type="Explore", model="sonnet", description="Test data", prompt="""
Read and follow: .claude/init-agents/test-analyzer.md

You are a GATHERER. Collect test data:
- Framework configuration
- Test file inventory
- Coverage configuration
- Test infrastructure (fixtures, mocks)

Return counts and configuration. Do NOT assess quality.
""")

Task(subagent_type="Explore", model="sonnet", description="Documentation data", prompt="""
Read and follow: .claude/init-agents/docs-analyzer.md

You are a GATHERER. Collect documentation data:
- File inventory (README, docs/, ADRs)
- Full README content
- Inline doc counts
- File reference existence check

Return inventory and content. Do NOT evaluate accuracy.
""")

Task(subagent_type="Explore", model="sonnet", description="Workspace data", prompt="""
Read and follow: .claude/init-agents/workspace-hygiene.md

You are a GATHERER. Collect workspace data:
- .gitignore content and coverage
- Temp/backup file inventory
- Large file list
- Untracked files
- Naming patterns

Return lists and counts. Do NOT recommend cleanup.
""")
```

### 1.2 Collect Reports

Wait for all 9 agents. Each returns structured data per their agent file's output format.

---

## Phase 2: SYNTHESIS (Opus Analyzes)

**Opus reviews all gatherer reports and performs analysis.**

### 2.1 Analyze Gathered Data

Using Sequential-Thinking MCP, systematically analyze:

1. **Security posture** - Secret locations, vulnerability counts, .env status
2. **Test health** - Coverage %, test count, framework maturity
3. **Code quality** - Lint error counts, debt markers, type coverage
4. **Architecture** - Pattern indicators, boundary clarity, complexity
5. **Documentation** - Completeness, reference accuracy
6. **Workflow** - CI maturity, automation level
7. **Hygiene** - Artifact status, gitignore completeness

### 2.2 Identify Priorities

```markdown
## Analysis Results

### Critical Issues (P0) - Must address
| Issue | Evidence | Source |
|-------|----------|--------|
| Secrets in repo | [files found] | security-analyzer |
| Failing tests | [test output] | test-analyzer |

### Important Issues (P1)
| Issue | Evidence | Impact |
|-------|----------|--------|

### Recommended (P2)
| Issue | Evidence | Impact |
|-------|----------|--------|

### Health Scores
| Category | Score | Reasoning |
|----------|-------|-----------|
| Security | X/10 | [based on findings] |
| Testing | X/10 | |
| Quality | X/10 | |
| Architecture | X/10 | |
| Documentation | X/10 | |
| Workflow | X/10 | |
| Hygiene | X/10 | |

**Overall**: X/100
```

### 2.3 Identify Conflicts & Opportunities

- **User agent conflicts** - User has X, we have Y with same purpose
- **Leverage opportunities** - User's existing tools we can use
- **Documentation drift** - Docs say X, code shows Y

---

## Phase 3: CONVERSATION

**Ask questions informed by analysis.**

### 3.1 Critical Issue Handling (if P0 found)

```
AskUserQuestion: "Found [N] critical issues: [list]. How to handle?"
- "Address immediately after init"
- "Add to roadmap"
- "I'll handle manually"
```

### 3.2 Conflict Resolution (if env conflicts)

```
AskUserQuestion: "Your [agent] overlaps with our [agent]. Preference?"
- "Use mine"
- "Use yours"
- "Keep both"
```

### 3.3 Project Identity

```
AskUserQuestion: "Project appears to be: [from gatherer data]. Accurate? One-sentence description?"

AskUserQuestion: "Development phase?"
- "Early (v0.x, actively changing)"
- "Active (stable but growing)"
- "Maintenance (stable, occasional)"
- "Legacy (minimal changes)"
```

### 3.4 Workflow Preferences

```
AskUserQuestion: "Uncertainty handling?"
- "Ask immediately"
- "Assume and validate later"
- "Explore first, then ask"

AskUserQuestion: "Autonomy after requirements confirmed?"
- "Full (only escalate blockers)"
- "Moderate (checkpoint before major changes)"
- "Conservative (confirm each step)"
```

---

## Phase 4: GENERATION

**Generate project ecosystem using guides as reference.**

### 4.1 Directory Structure

```bash
mkdir -p .claude/{commands,agents,hooks,logs/signals}
```

### 4.2 Generate CLAUDE.md

**Reference guide**: `.claude/guides/documentation.md` for structure principles.

Generate using actual detected values (no placeholders):

```markdown
# [ACTUAL_PROJECT_NAME]

## Quick Start
1. Read this file
2. Check Serena memories: `project_overview`
3. Run `/project:plan` before changes

## Stack
- **Language**: [DETECTED]
- **Framework**: [DETECTED]
- **Package Manager**: [DETECTED]

## Commands (from CI - verified)
```bash
# Test
[ACTUAL_TEST_COMMAND]

# Lint
[ACTUAL_LINT_COMMAND]

# Build
[ACTUAL_BUILD_COMMAND]
```

## Health
**Score**: [CALCULATED]/100 | **Assessed**: [DATE]

## Phase
[USER_SELECTED]

## Workflow
- **Uncertainty**: [USER_PREF]
- **Autonomy**: [USER_PREF]

## Rules

**ALWAYS:**
- Run tests: `[COMMAND]`
- Run lint: `[COMMAND]`

**NEVER:**
- [FROM_SECURITY_FINDINGS]

## Commands
- `/project:auto` - Autonomous development
- `/project:plan` - Planning
- `/project:signal` - Feedback capture
```

### 4.3 Generate settings.json

Stack-appropriate permissions:

```json
{
  "permissions": {
    "allow": ["[STACK_COMMANDS]", "Bash(git *)"],
    "deny": ["Bash(rm -rf:*)", "Bash(sudo:*)"]
  }
}
```

### 4.4 Generate Commands

**Reference guide**: `.claude/guides/command-structure.md`

For each command, apply guide principles to project context:
- Right-size for project complexity
- Include project-specific tools/commands
- Don't duplicate CLAUDE.md content

**Core commands to generate** (adapt from templates):
- auto.md - Autonomous workflow
- plan.md - Planning
- explore.md - Investigation
- signal.md - Feedback capture
- improve.md - Process improvement

Skip commands that conflict with user's existing.

### 4.5 Generate Agents

**Reference guide**: `.claude/guides/agent-structure.md`

Generate reviewers appropriate for project:
- code-reviewer.md - Use project's lint command, quality standards
- plan-reviewer.md - Use project's architecture patterns

Skip agents that conflict with user's existing.

### 4.6 Initialize Serena Memories

```
mcp__serena__write_memory("project_overview", """
# [PROJECT]
**Type**: [TYPE]
**Stack**: [STACK]
**Phase**: [PHASE]
**Initialized**: [DATE]

## Architecture
[FROM_ARCHITECTURE_GATHERER]

## Key Patterns
[DETECTED_PATTERNS]
""")

mcp__serena__write_memory("improvement_roadmap", """
# Improvement Roadmap
**Score**: [X]/100

## P0 - Critical
[FROM_SYNTHESIS]

## P1 - Important
[FROM_SYNTHESIS]

## P2 - Recommended
[FROM_SYNTHESIS]
""")
```

---

## Phase 5: VALIDATION

### 5.1 Run Commands

```bash
timeout 120 [TEST_COMMAND] 2>&1 | tail -20
timeout 60 [LINT_COMMAND] 2>&1 | tail -20
```

### 5.2 Structure Check

```bash
[ -f CLAUDE.md ] && echo "✅ CLAUDE.md"
[ -d .claude/commands ] && echo "✅ commands/"
grep -c "{{" CLAUDE.md && echo "⚠️ Placeholders!" || echo "✅ No placeholders"
```

### 5.3 Memory Check

```
mcp__serena__list_memories()
```

---

## Phase 6: REPORT & CLEANUP

### 6.1 Final Report

```markdown
## Initialization Complete

### Detection
| Item | Value |
|------|-------|
| Language | [X] |
| Framework | [X] |
| Test | `[X]` |
| Lint | `[X]` |

### Health: [X]/100
| Category | Score |
|----------|-------|
| Security | X/10 |
| Testing | X/10 |
| Quality | X/10 |

### Issues
- P0: [N] critical
- P1: [N] important

### Generated
- CLAUDE.md
- [N] commands
- [N] agents
- Serena memories

### Next Steps
1. Review: `mcp__serena__read_memory("improvement_roadmap")`
2. Start: `/project:auto <task>` or `/project:explore <topic>`
```

### 6.2 Self-Deletion Offer

```
AskUserQuestion: "Init complete. Delete init.md to save context?"
- "Yes, delete (can reinstall from plugin)"
- "No, keep"
```

---

## Mode: MINIMAL

Skip Phase 1-2. Basic detection only. Minimal questions. Generate with defaults.

## Mode: VALIDATE

Skip to Phase 5. Run checks. Report health. Suggest fixes.

## Mode: RESET

Preserve Serena memories. Remove .claude/*. Remove CLAUDE.md. Run full init.
