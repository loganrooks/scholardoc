---
description: Initialize autonomous development system with codebase assessment
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task, AskUserQuestion, mcp__serena__*
argument-hint: [mode: full|thorough|minimal|validate|reset]
---

# Project Initialization: $ARGUMENTS

**MODE: INTELLIGENT ONBOARDING WITH CODE REVIEW**

This command sets up the autonomous development system AND assesses the codebase against best practices. It produces actionable findings, not just configuration.

---

## Mode Selection

| Mode | Purpose | Time |
|------|---------|------|
| `full` (default) | Detection + quick assessment + setup | ~2-3 min |
| `thorough` | Full assessment with test runs + coverage | ~5-7 min |
| `minimal` | Just directory structure, skip assessment | ~30 sec |
| `validate` | Health check existing setup | ~1 min |
| `reset` | Clear and reinitialize (preserves memories) | ~2-3 min |

---

## Phase 1: DETECT

### 1.1 Stack Detection

```bash
# Language/Runtime Detection
echo "=== Stack Detection ==="

# Node.js / TypeScript
if [ -f package.json ]; then
  echo "Node.js detected"
  cat package.json | grep -E '"(typescript|ts-node)"' && echo "  → TypeScript"
  cat package.json | grep -E '"(react|vue|angular|svelte)"' && echo "  → Frontend framework detected"
  cat package.json | grep -E '"(next|nuxt|sveltekit)"' && echo "  → Fullstack SSR framework"
  cat package.json | grep -E '"(express|fastify|hono|koa)"' && echo "  → Backend framework"
fi

# Python
if [ -f pyproject.toml ] || [ -f setup.py ] || [ -f requirements.txt ]; then
  echo "Python detected"
  grep -l "django\|flask\|fastapi" pyproject.toml requirements.txt 2>/dev/null && echo "  → Web framework detected"
fi

# Rust
[ -f Cargo.toml ] && echo "Rust detected"

# Go
[ -f go.mod ] && echo "Go detected"

# Ruby
[ -f Gemfile ] && echo "Ruby detected"

# Java/Kotlin
[ -f pom.xml ] || [ -f build.gradle ] || [ -f build.gradle.kts ] && echo "JVM detected"
```

### 1.2 Command Detection (CI as Source of Truth)

```bash
echo "=== Command Detection ==="

# GitHub Actions (most reliable source)
if [ -d .github/workflows ]; then
  echo "GitHub Actions detected - extracting commands:"
  grep -h "run:" .github/workflows/*.yml 2>/dev/null | head -20
fi

# GitLab CI
[ -f .gitlab-ci.yml ] && echo "GitLab CI detected" && grep "script:" .gitlab-ci.yml | head -10

# Package.json scripts
if [ -f package.json ]; then
  echo "npm scripts:"
  cat package.json | grep -A 20 '"scripts"' | head -25
fi

# Python pyproject.toml
if [ -f pyproject.toml ]; then
  echo "pyproject.toml scripts:"
  grep -A 10 '\[tool.poetry.scripts\]\|\[project.scripts\]' pyproject.toml 2>/dev/null
fi

# Makefile
[ -f Makefile ] && echo "Makefile targets:" && grep "^[a-zA-Z].*:" Makefile | head -10
```

### 1.3 Code Style Detection

```bash
echo "=== Code Style Detection ==="

# JavaScript/TypeScript
[ -f .eslintrc* ] || [ -f eslint.config.* ] && echo "ESLint configured"
[ -f .prettierrc* ] || [ -f prettier.config.* ] && echo "Prettier configured"
[ -f tsconfig.json ] && echo "TypeScript configured"

# Python
grep -q "\[tool.ruff\]" pyproject.toml 2>/dev/null && echo "Ruff configured"
grep -q "\[tool.black\]" pyproject.toml 2>/dev/null && echo "Black configured"
grep -q "\[tool.mypy\]" pyproject.toml 2>/dev/null && echo "MyPy configured"
[ -f .flake8 ] && echo "Flake8 configured"

# General
[ -f .editorconfig ] && echo "EditorConfig present"
```

### 1.4 Project Structure Analysis

```bash
echo "=== Project Structure ==="

# Monorepo detection
[ -d packages ] || [ -d apps ] || [ -f pnpm-workspace.yaml ] || [ -f lerna.json ] && echo "Monorepo structure detected"

# Common patterns
[ -d src ] && echo "src/ directory present"
[ -d lib ] && echo "lib/ directory present"
[ -d tests ] || [ -d test ] || [ -d __tests__ ] && echo "Test directory present"
[ -d docs ] && echo "docs/ directory present"

# Database/ORM
[ -f prisma/schema.prisma ] && echo "Prisma ORM detected"
[ -f drizzle.config.ts ] && echo "Drizzle ORM detected"
grep -rq "from sqlalchemy" . 2>/dev/null && echo "SQLAlchemy detected"
```

### 1.5 Git Workflow Detection

```bash
echo "=== Git Workflow ==="

# Default branch
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'

# Existing hooks
[ -d .husky ] && echo "Husky hooks configured"
[ -d .git/hooks ] && ls .git/hooks | grep -v ".sample" | head -5

# Branch protection (check for common patterns)
[ -f .github/CODEOWNERS ] && echo "CODEOWNERS present"
[ -f CONTRIBUTING.md ] && echo "Contributing guide present"
```

### 1.6 Derive Commands

Based on detection, determine the actual commands:

| Detected | Test Command | Lint Command | Build Command |
|----------|--------------|--------------|---------------|
| package.json + jest | `npm test` | `npm run lint` | `npm run build` |
| package.json + vitest | `npm test` | `npm run lint` | `npm run build` |
| pyproject.toml + pytest | `pytest` | `ruff check .` | N/A |
| Cargo.toml | `cargo test` | `cargo clippy` | `cargo build` |
| go.mod | `go test ./...` | `golangci-lint run` | `go build` |

**Priority**: CI config > package scripts > conventions

---

## Phase 2: ASSESS (Parallel Code Review)

**SKIP IF**: `$ARGUMENTS` is "minimal"

### 2.1 Quick Assessment (Default)

Run in parallel:

```
# Security scan
Task(subagent_type="security-engineer", model="sonnet", prompt="""
Quick security scan of this codebase:
1. Check for hardcoded secrets (API keys, passwords, tokens)
2. Look for .env files that shouldn't be committed
3. Check dependency vulnerabilities (read package-lock.json or equivalent)
4. Identify obvious auth/input validation gaps
Return: Score (1-10), critical issues list, recommendations
""")

# Test/Quality assessment
Task(subagent_type="quality-engineer", model="sonnet", prompt="""
Quick quality assessment:
1. Do tests exist? What framework?
2. Estimate coverage from test file count vs source file count
3. Are there integration/E2E tests?
4. Check for obvious testing gaps
Return: Score (1-10), coverage estimate, gaps identified
""")

# Architecture review
Task(subagent_type="Explore", model="sonnet", prompt="""
Quick architecture review:
1. Is there clear separation of concerns?
2. Are there obvious circular dependencies?
3. Is the project structure conventional for the stack?
4. Any code organization red flags?
Return: Score (1-10), structure assessment, recommendations
""")

# Documentation check
Task(subagent_type="Explore", model="sonnet", prompt="""
Documentation completeness check:
1. Does README exist and have setup instructions?
2. Is there API documentation?
3. Are there inline comments where needed?
4. Is there a contributing guide?
Return: Score (1-10), gaps identified
""")
```

### 2.2 CLI Scans (Parallel with agents)

```bash
# Dependency security (run appropriate for stack)
if [ -f package-lock.json ]; then
  npm audit --json 2>/dev/null | head -100
elif [ -f requirements.txt ] || [ -f pyproject.toml ]; then
  pip-audit 2>/dev/null || echo "pip-audit not installed"
elif [ -f Cargo.toml ]; then
  cargo audit 2>/dev/null || echo "cargo-audit not installed"
fi

# Outdated dependencies
if [ -f package.json ]; then
  npm outdated 2>/dev/null | head -20
elif [ -f requirements.txt ]; then
  pip list --outdated 2>/dev/null | head -20
fi

# Lint issue count
if [ -f package.json ]; then
  npx eslint . --format=compact 2>/dev/null | wc -l
elif [ -f pyproject.toml ]; then
  ruff check . --statistics 2>/dev/null | tail -5
fi
```

### 2.3 Thorough Assessment (--thorough only)

Additional checks when `$ARGUMENTS` is "thorough":

```bash
# Actually run tests and get coverage
if [ -f package.json ]; then
  npm test -- --coverage 2>/dev/null | tail -30
elif [ -f pyproject.toml ]; then
  pytest --cov --cov-report=term-missing 2>/dev/null | tail -30
fi
```

Additional agent assessments:
```
Task(subagent_type="Explore", prompt="Deep architecture review: dependency graph, complexity hotspots, code duplication")
Task(subagent_type="security-engineer", prompt="Full security audit: auth flows, data handling, API security")
```

### 2.4 Aggregate Assessment Results

Combine parallel results into health score:

```markdown
## Codebase Health Assessment

**Overall Score**: [X]/100

| Category | Score | Status | Key Issues |
|----------|-------|--------|------------|
| Security | X/10 | [emoji] | [summary] |
| Testing | X/10 | [emoji] | [summary] |
| Code Quality | X/10 | [emoji] | [summary] |
| Architecture | X/10 | [emoji] | [summary] |
| Dependencies | X/10 | [emoji] | [summary] |
| Documentation | X/10 | [emoji] | [summary] |
| CI/CD | X/10 | [emoji] | [summary] |

Status: ✅ Good (8-10) | ⚠️ Needs Work (5-7) | ❌ Critical (<5)
```

### 2.5 Prioritize Findings

```markdown
### Priority Issues

**P0 - Critical** (Security, broken functionality)
- [ ] [Issue description]

**P1 - Important** (Testing gaps, outdated deps)
- [ ] [Issue description]

**P2 - Recommended** (Code quality, docs)
- [ ] [Issue description]

**P3 - Nice to Have** (Minor improvements)
- [ ] [Issue description]
```

---

## Phase 3: INTERACT (Informed by Assessment)

Now ask user questions, informed by what we found:

### 3.1 Critical Findings Check

If P0 issues were found:
```
AskUserQuestion: "We found [N] critical issues:
- [Issue 1]
- [Issue 2]

How should we handle these?"
Options:
- Address immediately after init
- Add to improvement roadmap for later
- Ignore for now (not recommended)
```

### 3.2 Project Identity

```
Question: "What is this project in one sentence?"
Question: "Who are the primary users?"
Question: "Current phase?"
Options: [Planning, Early Development, Active Development, Maintenance]
```

### 3.3 Workflow Preferences

```
Question: "How should uncertainty be handled?"
Options:
- Ask immediately (interactive)
- Make reasonable assumptions, validate later
- Explore first, then ask

Question: "Autonomy level after requirements confirmed?"
Options:
- Full autonomy (only escalate on blockers)
- Moderate (checkpoint before major changes)
- Conservative (confirm each phase)
```

### 3.4 Assessment-Informed Questions

Based on findings, ask targeted questions:

If test coverage is low:
```
Question: "Test coverage is estimated at [X]%. What's your target?"
Options: [Accept current, 60%, 80%, 90%+]
```

If no CI detected:
```
Question: "No CI/CD pipeline detected. Should we set one up?"
Options: [Yes - GitHub Actions, Yes - other, No - manual for now]
```

---

## Phase 4: GENERATE

### 4.1 Create Directory Structure

```bash
mkdir -p .claude/{commands,agents,hooks,logs/signals,signals}
```

### 4.2 Generate CLAUDE.md

Create project-specific CLAUDE.md incorporating:
- Detected stack (no placeholders!)
- Real commands from CI/package.json
- Assessment findings summary
- User preferences from Phase 3

```markdown
# [Project Name]

## Quick Start for AI Assistants
1. Read this file completely
2. Check `improvement_roadmap` memory for known issues
3. Run `/project:plan` before significant coding
4. Use Serena memories for context

## Stack
- **Language**: [Detected]
- **Framework**: [Detected]
- **Testing**: [Detected framework] - `[actual command]`
- **Linting**: [Detected] - `[actual command]`
- **Build**: `[actual command]`

## Health Status
**Last assessed**: [Date]
**Score**: [X]/100

### Known Issues (from init assessment)
- [P0 issues if any]
- [P1 issues summary]

See `improvement_roadmap` memory for full details.

## Development Phase
[From user input]

## Rules
ALWAYS:
- Run `[test command]` before committing
- Run `[lint command]` to check style
- [From constraints]

NEVER:
- [From constraints]
- [From security findings if relevant]

## Commands
- `/project:auto <task>` - Autonomous development
- `/project:explore <topic>` - Investigate codebase
- `/project:plan <feature>` - Create implementation plan
- `/project:improve` - Self-improvement cycle
- `/project:signal [note]` - Capture correction feedback
```

### 4.3 Initialize Serena Memories

```
write_memory("project_overview", """
# Project Overview

**Name**: [name]
**Stack**: [detected stack]
**Phase**: [from user]
**Initialized**: [date]

## Architecture
[From assessment findings]

## Key Patterns
[Detected patterns and conventions]

## Constraints
[From user input]
""")

write_memory("improvement_roadmap", """
# Improvement Roadmap

**Generated by**: /project:init
**Date**: [date]
**Health Score**: [X]/100

## P0 - Critical
- [ ] [Issue with details]

## P1 - Important
- [ ] [Issue with details]

## P2 - Recommended
- [ ] [Issue with details]

## P3 - Nice to Have
- [ ] [Issue with details]

---
Run `/project:improve` to process these items.
""")

write_memory("decision_log", """
# Decision Log

Record architectural decisions here.

## Format
### YYYY-MM-DD: [Decision Title]
**Decision**: [What was decided]
**Rationale**: [Why this choice]
**Trade-offs**: [Downsides and mitigations]

---
Initialized by /project:init on [date]
""")
```

### 4.4 Copy Adapted Templates

Copy from plugin templates, customizing for detected stack:
- Commands (all core commands)
- Agents (reviewers adapted for detected stack)
- Hooks (if applicable)

---

## Phase 5: VALIDATE

### 5.1 Run Detected Commands

```bash
echo "=== Validation ==="

# Test command
echo "Running test command..."
[DETECTED_TEST_COMMAND] && echo "✅ Tests pass" || echo "⚠️ Tests failed/skipped"

# Lint command
echo "Running lint command..."
[DETECTED_LINT_COMMAND] && echo "✅ Lint passes" || echo "⚠️ Lint issues found"

# Build command (if applicable)
if [ -n "[DETECTED_BUILD_COMMAND]" ]; then
  echo "Running build..."
  [DETECTED_BUILD_COMMAND] && echo "✅ Build succeeds" || echo "⚠️ Build failed"
fi
```

### 5.2 Structure Verification

```bash
# Verify all files created
ls -la .claude/
ls -la .claude/commands/ | wc -l
ls -la .claude/agents/ | wc -l

# CLAUDE.md sanity check
wc -l CLAUDE.md
grep -c "{{" CLAUDE.md && echo "⚠️ Unresolved placeholders!" || echo "✅ No placeholders"
```

### 5.3 Memory Verification

```
list_memories()
# Should show: project_overview, improvement_roadmap, decision_log
```

---

## Phase 6: REPORT

```markdown
## Initialization Complete!

### Detection Summary
| Item | Detected |
|------|----------|
| Language | [X] |
| Framework | [X] |
| Test Command | `[X]` |
| Lint Command | `[X]` |
| Build Command | `[X]` |
| CI/CD | [X] |

### Assessment Summary
**Health Score**: [X]/100

| Category | Score | Status |
|----------|-------|--------|
| Security | X/10 | [emoji] |
| Testing | X/10 | [emoji] |
| Code Quality | X/10 | [emoji] |
| Architecture | X/10 | [emoji] |
| Dependencies | X/10 | [emoji] |
| Documentation | X/10 | [emoji] |

### Priority Issues Found
- **P0 (Critical)**: [count]
- **P1 (Important)**: [count]
- **P2 (Recommended)**: [count]

See `improvement_roadmap` memory for details.

### Validation Results
| Check | Result |
|-------|--------|
| Tests | [pass/fail/skip] |
| Lint | [pass/fail/skip] |
| Build | [pass/fail/skip] |
| Structure | ✅ |
| Memories | ✅ |

### Generated Files
- CLAUDE.md ([X] lines)
- .claude/commands/ ([X] commands)
- .claude/agents/ ([X] agents)
- Serena memories: project_overview, improvement_roadmap, decision_log

### Recommended Next Steps

1. **Review findings**: `read_memory("improvement_roadmap")`
2. **Address P0 issues** (if any): `/project:improve`
3. **Start development**: `/project:auto <task>` or `/project:explore <topic>`

### Quick Commands
- `/project:auto <task>` - Autonomous development
- `/project:explore <topic>` - Investigate codebase
- `/project:improve` - Process improvement roadmap
- `/project:signal` - Capture feedback for learning
```

---

## Validate Mode

If `$ARGUMENTS` is "validate":

1. Skip Phases 1-4
2. Run Phase 5 validation checks
3. Compare against expected structure
4. Report health status
5. Suggest fixes for any issues

---

## Reset Mode

If `$ARGUMENTS` is "reset":

1. **Preserve** Serena memories (they contain project knowledge)
2. **Remove** .claude/commands/, .claude/agents/, .claude/hooks/
3. **Remove** CLAUDE.md
4. **Run** full initialization from Phase 1
