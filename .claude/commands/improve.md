---
description: Self-improvement cycle with diagnosis and system enhancement
allowed-tools: Read, Glob, Grep, Bash(git:*), Bash(ls:*), Bash(cat:*), Task, mcp__serena__*
argument-hint: [trigger: pr-merge|error|weekly|context-loss|full-audit]
---

# Self-Improvement Cycle: $ARGUMENTS

**MODE: META-IMPROVEMENT WITH DIAGNOSTIC FEEDBACK**

This command runs a full improvement cycle: explore → plan → implement → review, applied to the development SYSTEM itself.

---

## The Meta-Improvement Principle

> The self-improvement workflow IS a development workflow.
> It follows the same explore → plan → implement → review pattern.
> It has its own review gates to catch bad improvements.

---

## Phase 1: EXPLORE (Gather Signals)

### 1.1 Check Signal Log
```bash
# Captured signals awaiting diagnosis
ls -la .claude/logs/signals/ 2>/dev/null | grep -v "^d" | grep -v ".gitkeep"
```

### 1.2 Human Correction Signals
```bash
# Corrections captured via /project:signal
if [ -f .claude/signals/corrections.jsonl ]; then
  echo "=== Human Corrections ==="
  cat .claude/signals/corrections.jsonl
  echo ""
  echo "Count: $(wc -l < .claude/signals/corrections.jsonl) signals"
fi
```

These are high-value signals - moments when the user interrupted or corrected Claude.
Correlate timestamps with native Claude logs to understand what was happening.

### 1.3 Session & Native Logs
```bash
# Enhanced session logs (from session-logger hook)
ls -lt .claude/logs/sessions/ 2>/dev/null | head -10

# Native Claude logs (rich data: tool calls, errors, token usage)
CLAUDE_LOG_DIR="$HOME/.claude/projects$(pwd)"
if [ -d "$CLAUDE_LOG_DIR" ]; then
  echo "Native logs available:"
  ls -lt "$CLAUDE_LOG_DIR"/*.jsonl 2>/dev/null | head -3
fi
```

For comprehensive pattern analysis across sessions:
```
/project:analyze-logs week all
```

### 1.4 Serena Memories
```
list_memories()
read_memory("improvement_log")  # Previous improvements
read_memory("decision_log")     # Decisions that may need review
```

### 1.5 Git History (Error Indicators)
```bash
# Commits indicating issues
git log --oneline -20 | grep -iE "fix|bug|revert|oops|typo"

# Files changed frequently (hotspots)
git log --oneline --name-only -50 | grep -v "^[a-f0-9]" | sort | uniq -c | sort -rn | head -10
```

### 1.6 System Health Check
```bash
# CLAUDE.md length (should be < 500 lines)
wc -l CLAUDE.md

# Agent count (should be < 10)
ls .claude/agents/ | wc -l

# Hook count (should be < 10)
ls .claude/hooks/ | wc -l

# Command count (informational)
ls .claude/commands/ | wc -l
```

### 1.7 Self-Critique by Domain

For each domain, run the relevant reviewer to identify issues:

| Domain | Reviewer | Focus |
|--------|----------|-------|
| Exploration work | exploration-reviewer | Were explorations thorough? |
| Planning work | plan-reviewer | Were plans complete? |
| Code changes | code-reviewer | Any patterns to extract? |
| Documentation | documentation-reviewer | Is docs current? |
| Experiments | experiment-reviewer | Were conclusions valid? |

---

## Phase 2: DIAGNOSE (Analyze Patterns)

### 2.1 Pattern Categories

| Category | Signals | Root Cause Area |
|----------|---------|-----------------|
| Human Corrections | `/project:signal` entries | Missing pattern/rule/reminder |
| Repeated Errors | Same issue 2+ times | Missing command step or agent |
| Human Interruptions | "You should have..." | Missing reminder/hook |
| Context Loss | Re-explanation needed | Memory/docs gap |
| Workflow Friction | Manual multi-step | Missing command |
| Rule Ignored | Documented but not followed | CLAUDE.md bloat or missing hook |
| Technical Debt | TODO accumulation | Missing quality gate |

**Human Corrections Priority**: Signals from `/project:signal` are highest priority.
These are explicit user feedback moments. Correlate with native logs by timestamp.

### 2.2 Deep Pattern Analysis

For comprehensive pattern analysis across multiple sessions:
```
/project:analyze-logs week all
```

This provides:
- Aggregated error/warning frequency
- Git hotspot analysis
- Metric trends
- Prioritized improvement recommendations

### 2.3 For Each Pattern Found

**PARALLELIZATION**: If multiple signals/patterns found, diagnose them in parallel:

```
# Parallel diagnosis (single message, multiple Task calls)
Task(subagent_type="root-cause-analyst", model="sonnet", prompt="Diagnose signal: [pattern-1-description]")
Task(subagent_type="root-cause-analyst", model="sonnet", prompt="Diagnose signal: [pattern-2-description]")
Task(subagent_type="root-cause-analyst", model="sonnet", prompt="Diagnose signal: [pattern-3-description]")
```

For each pattern (sequential if few, parallel if many):
1. Trace to root cause
2. Identify system component
3. Propose improvement type
4. Self-review the diagnosis

### 2.4 Diagnosis Self-Review

Launch diagnostic-agent (or self-review):
- Is root cause analysis sound?
- Is evidence sufficient?
- Were alternatives considered?

---

## Phase 3: PLAN (Propose Improvements)

### 3.1 Improvement Types

| Type | Target | When |
|------|--------|------|
| COMMAND_REFINEMENT | .claude/commands/ | Command missing step |
| AGENT_ADDITION | .claude/agents/ | Missing review gate |
| AGENT_REFINEMENT | .claude/agents/ | Existing agent missed something |
| HOOK_ADDITION | .claude/hooks/ | Need automated reminder |
| INSTRUCTION_COMPRESSION | CLAUDE.md | File too long, rules buried |
| DOCUMENTATION_UPDATE | docs/, CLAUDE.md | Docs out of sync |
| MEMORY_UPDATE | Serena memories | Cross-session context gap |
| WORKFLOW_ADDITION | .claude/commands/ | Process gap |

### 3.2 Improvement Proposals

| Pattern | Diagnosis | Improvement | Type | Priority |
|---------|-----------|-------------|------|----------|
| | | | | |

Priority Levels:
- **P0**: Blocking future work
- **P1**: Causes repeated friction
- **P2**: Nice to have

### 3.3 Improvement Self-Review

**PARALLELIZATION**: Review multiple proposals in parallel if independent:

```
# Parallel improvement review (single message, multiple Task calls)
Task(subagent_type="general-purpose", model="sonnet", prompt="Review improvement proposal: [proposal-1]. Check: addresses root cause? proportionate? unintended consequences? bloat?")
Task(subagent_type="general-purpose", model="sonnet", prompt="Review improvement proposal: [proposal-2]. Check: addresses root cause? proportionate? unintended consequences? bloat?")
```

For each proposal, validate:
- Does improvement address root cause?
- Is it proportionate to the problem?
- Any unintended consequences?
- Does it bloat the system?

**Verdicts:**
- APPROVED → Proceed to implement
- NEEDS_REFINEMENT → Adjust proposal
- REJECTED → Document why and skip

---

## Phase 4: IMPLEMENT (Apply Changes)

### 4.1 Implementation Order
1. P0 improvements first
2. Then P1
3. P2 only if time permits

### 4.2 For Each Approved Improvement

1. **Make the change** (command, agent, hook, doc, memory)
2. **Verify it works** (test if applicable)
3. **Self-review** with relevant domain reviewer
4. **Log** to improvement_log memory

### 4.3 CLAUDE.md Special Handling

If changing CLAUDE.md:
- Check current line count
- If > 500 lines: Consider moving content elsewhere
- Keep only essential rules in CLAUDE.md
- Move workflows to commands, details to docs

---

## Phase 5: REVIEW (Validate & Learn)

### 5.1 Verification

For each implemented improvement:
- [ ] Does it address the original signal?
- [ ] No unintended side effects?
- [ ] Tests still pass?
- [ ] Documentation updated?

### 5.2 Update Improvement Log

```
write_memory("improvement_log", """
## Improvement Log

### [DATE] - Trigger: $ARGUMENTS

**Signals Processed**: [count]
**Diagnoses**:
- [signal] → [root cause]

**Improvements Implemented**:
| Type | Target | Change | Verified |
|------|--------|--------|----------|
| | | | |

**Improvements Deferred**:
- [item]: [reason]

**Improvements Rejected**:
- [item]: [reason]

**System Health After**:
- CLAUDE.md: [lines] lines
- Agents: [count]
- Hooks: [count]

**Lessons Learned**:
- [insight for future improvements]

---
[Previous entries...]
""")
```

### 5.3 Archive Processed Signals

Move processed signals to archived locations:
```bash
# Archive markdown signals
mkdir -p .claude/logs/signals/processed
mv .claude/logs/signals/*.md .claude/logs/signals/processed/ 2>/dev/null

# Archive human corrections (rename with date suffix)
if [ -f .claude/signals/corrections.jsonl ]; then
  mkdir -p .claude/signals/processed
  mv .claude/signals/corrections.jsonl ".claude/signals/processed/corrections_$(date +%Y%m%d).jsonl"
fi
```

---

## Output Summary

```markdown
## Self-Improvement Cycle Complete

**Trigger**: $ARGUMENTS
**Date**: [Current date]

### Exploration Results
| Source | Signals Found |
|--------|---------------|
| Signal log | [count] |
| Session logs | [count] |
| Git history | [count] |
| Domain reviews | [count] |

### System Health
| Metric | Value | Status |
|--------|-------|--------|
| CLAUDE.md lines | [N] | [OK if <500, WARN if >500] |
| Agents | [N] | [OK if <10] |
| Hooks | [N] | [OK if <10] |

### Diagnoses
| Signal | Root Cause | Component |
|--------|------------|-----------|
| | | |

### Improvements
| Status | Type | Target | Change |
|--------|------|--------|--------|
| ✅ Implemented | | | |
| ⏸️ Deferred | | | |
| ❌ Rejected | | | |

### Self-Review Results
- Diagnoses: [N] strong, [N] adequate, [N] weak
- Improvements: [N] approved, [N] refined, [N] rejected

### Next Steps
- Recommended next review: [trigger/timing]
- Focus areas: [areas needing attention]
```

---

## When to Run This Command

| Trigger | When | Focus |
|---------|------|-------|
| pr-merge | After PR merged | Patterns from PR work |
| error | After significant error | Root cause of error |
| weekly | Weekly during active dev | Accumulated patterns |
| context-loss | After re-explanation needed | Memory/doc gaps |
| full-audit | Before major work | Comprehensive review |

---

## Integration with /project:auto

The `/project:auto` command calls `/project:improve` or `/project:diagnose`:
- On escalation (reviewer BLOCKED)
- On repeated test failures
- At end of autonomous run

This creates a closed feedback loop:
```
/project:auto → error/escalation → /project:diagnose → improvement → better /project:auto
```
