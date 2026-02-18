# Review Workflow Guide

## Purpose

Periodic analysis of development sessions to capture implicit signals, identify improvement opportunities, and propose system enhancements. This workflow runs weekly (or after significant milestones like PR merges) and produces actionable proposals without implementing them.

## Principles

1. **Passive capture, batch analysis** - Data accumulates continuously; analysis happens periodically
2. **Implicit over explicit** - Don't rely solely on `/signal`; detect patterns users didn't consciously report
3. **Retrospective honesty** - Ask "could we have done better?" even when no one complained
4. **Proposals not implementations** - This workflow suggests; humans decide what to apply
5. **Level-aware routing** - Distinguish project-specific fixes from systemic improvements

## Signal Sources

### Signal Format

All explicit signals follow the schema in `templates/formats/signal-format.md`.

### Tier 1: Explicit Signals (High Confidence)
- `.claude/signals/corrections.jsonl` - User-submitted via `/signal`
- Direct user feedback in conversations

### Tier 2: Implicit-Observable (Medium Confidence)
Detected from native Claude logs at `~/.claude/projects$(pwd)/*.jsonl`:

| Pattern | Indicates |
|---------|-----------|
| "no", "stop", "wait", "wrong" | Immediate correction |
| "I already told you", "I said" | Repeated instruction |
| "you should have", "why didn't you" | Missed expectation |
| Same instruction given 2+ times | Context loss or ignoring |
| User rewrites Claude's code entirely | Failed attempt |
| Short frustrated messages after long Claude output | Output missed the mark |

### Tier 3: Implicit-Latent (Lower Confidence)
Detected via retrospective audit of recent changes:

| Area | What to Check |
|------|---------------|
| Code quality | Lint errors introduced, complexity added, patterns violated |
| Architecture | Coupling increased, abstractions wrong, boundaries crossed |
| Version control | Large commits, poor messages, missing atomic commits |
| Testing | New code without tests, inadequate coverage |
| Documentation | Changes without doc updates, stale docs |
| Security | Vulnerabilities introduced, secrets exposed |

## Review Process

### Phase 1: Gather Data

**1.1 Locate signal sources**
```bash
# Explicit signals
cat .claude/signals/corrections.jsonl 2>/dev/null

# Session metrics (from session-logger hook)
ls -lt .claude/logs/sessions/ 2>/dev/null | head -10

# Native Claude logs
CLAUDE_LOG_DIR="$HOME/.claude/projects$(pwd)"
ls -lt "$CLAUDE_LOG_DIR"/*.jsonl 2>/dev/null | head -5

# Git activity since last review
git log --oneline --since="1 week ago"
```

**1.2 Check for previous review**
```
read_memory("last_review_date")
read_memory("pending_improvements")
```

### Phase 2: Analyze Implicit Signals

**2.1 Parse native logs for conversation patterns**

Read recent native log files and identify:
- User messages containing frustration indicators
- Repeated similar instructions (same thing asked 2+ times)
- Corrections following Claude actions
- Sequences where user abandoned Claude's approach

For each potential implicit signal, record using a format compatible with `templates/formats/signal-format.md`, adding:
- `tier`: "implicit-observable"
- `pattern`: "frustration|repeated|correction|abandoned"
- `confidence`: 0.0-1.0
- `source`: "native-log-analysis"

**2.2 Validate medium-confidence signals**

For signals with confidence < 0.7, flag for human review rather than auto-including.

### Phase 3: Retrospective Audit

Review changes since last review against project standards.

**3.1 Read project quality baseline**
- Read `CLAUDE.md` for project conventions and rules
- Read recent commits to understand what was built

**3.2 Audit checklist**

| Category | Question | How to Check |
|----------|----------|--------------|
| VC Practices | Were commits atomic and well-messaged? | `git log --oneline` |
| VC Practices | Any large commits (>10 files)? | `git log --stat` |
| Code Quality | Lint errors in changed files? | Run project linter |
| Code Quality | Complexity increased? | Check for deep nesting, long functions |
| Testing | New code has tests? | Compare changed files to test files |
| Documentation | Docs updated for changes? | Check if docs match code |
| Architecture | Patterns followed? | Compare to existing code style |

**3.3 Generate latent signals**

For each audit finding, record using a format compatible with `templates/formats/signal-format.md`, adding:
- `tier`: "implicit-latent"
- `category`: "vc|quality|testing|docs|architecture"
- `evidence`: specific files/commits that demonstrate the issue
- `confidence`: 0.0-1.0
- `source`: "retrospective-audit"

### Phase 4: Classify Signals

For each signal (explicit + implicit), determine:

**Level Classification**

| Question | If Yes → |
|----------|----------|
| Is this specific to this project's unique context? | Level 2 |
| Would this occur in other projects using our templates? | Level 1 |
| Is this about the generated commands/agents? | Level 1 |
| Is this about project-specific rules/conventions? | Level 2 |

**Severity Classification**

| Severity | Criteria |
|----------|----------|
| P0 | Blocking work or causing errors |
| P1 | Recurring friction, productivity impact |
| P2 | Minor improvement, nice-to-have |

### Phase 5: Diagnose Root Causes

For significant signals (P0, P1, or patterns), trace to root cause:

```
Signal
  → Immediate cause (what directly went wrong)
    → System component (command/agent/hook/doc/memory)
      → Root cause (why the component failed)
```

**System Components**

| Component | Location | Typical Issues |
|-----------|----------|----------------|
| Commands | `.claude/commands/` | Missing step, unclear instruction |
| Agents | `.claude/agents/` | Missing check, weak criteria |
| Hooks | `.claude/hooks/` | Not triggering, wrong timing |
| Documentation | `CLAUDE.md`, `docs/` | Outdated, buried, too long |
| Memories | Serena | Missing, incomplete, stale |
| Guides | `guides/` (Level 1) | Missing principle, bad structure |

### Phase 6: Generate Proposals

For each diagnosed issue, create a proposal:

```markdown
## Proposal: [Short Title]

**Signal**: [What triggered this]
**Tier**: [explicit|implicit-observable|implicit-latent]
**Level**: [1|2]
**Severity**: [P0|P1|P2]

### Diagnosis
[Root cause analysis]

### Proposed Improvement
**Type**: [COMMAND_REFINEMENT|AGENT_REFINEMENT|HOOK_ADDITION|DOC_UPDATE|MEMORY_UPDATE|GUIDE_UPDATE]
**Target**: [Specific file or component]
**Change**: [What to modify]

### Expected Outcome
[How this prevents recurrence]

### Confidence
[High|Medium|Low] - [Why]
```

### Phase 7: Write Output

**7.1 Write proposals file**

Create `.claude/reviews/review_[YYYYMMDD].md` containing:
- Review metadata (date, scope, signal counts)
- All proposals grouped by severity
- Level 1 signals flagged for escalation
- Signals needing human validation (low confidence)

**7.2 Update Serena memories**

Follow schemas in `templates/formats/serena-memory-schemas.md`.

Update `feedback_state`:
```
write_memory("feedback_state", {
  last_review_date: "[today]",
  signals_since_last_review: 0,
  pending_improvements: [proposals],
  next_review_recommended: "[date]"
})
```

Update `improvement_history` with signal details:
```
write_memory("improvement_history", append: {
  date: "[today]",
  signal: {summary, type, diagnosis, level},
  improvement: {type, target, change},
  outcome: {status: "proposed"}
})
```

If any issue has occurred 2+ times, update `recurring_issues`:
```
write_memory("recurring_issues", {...})
```

**7.3 Level 1 signals stay in memories**

No file export needed. Level 1 signals are captured in `improvement_history` with `level: 1`.

claude-enhanced will pull these memories during cross-project review.

## Output Format

```markdown
# Review: [Date]

**Scope**: [week|pr|milestone]
**Period**: [date range]
**Signals Found**: [count by tier]

## Summary

| Severity | Count | Level 1 | Level 2 |
|----------|-------|---------|---------|
| P0 | | | |
| P1 | | | |
| P2 | | | |

## Proposals

### P0 - Critical
[proposals...]

### P1 - Important
[proposals...]

### P2 - Minor
[proposals...]

## Needs Human Validation

[Low-confidence signals that need review before acting]

## Level 1 Escalations

[Signals that indicate systemic issues with claude-enhanced templates/guides]

## Raw Signals

### Explicit
[list]

### Implicit-Observable
[list]

### Implicit-Latent
[list]

## Next Review

Recommended: [date or trigger]
```

## Quality Criteria

Good review:
- [ ] All signal sources checked (not just explicit)
- [ ] Implicit signals validated with evidence
- [ ] Root causes traced, not just symptoms noted
- [ ] Level classification justified
- [ ] Proposals are actionable and specific
- [ ] Low-confidence items flagged for human review

## Anti-patterns

- **Signal shopping**: Only looking at explicit signals, ignoring implicit
- **Over-sensitivity**: Flagging every minor issue as P0
- **Vague proposals**: "Improve the tests" without specifics
- **Skipping diagnosis**: Jumping from signal to solution without root cause
- **Auto-implementing**: This workflow proposes only; never implement directly
- **Ignoring latent issues**: Only reacting to complaints, not auditing proactively

## Adaptation Notes

When running for a specific project:
- Read `CLAUDE.md` for project-specific quality standards
- Use project's lint/test commands (from project config)
- Respect project's conventions when auditing
- Reference project's decision log for context on past choices

## Triggering This Workflow

**Automated (weekly)**:
```bash
claude -p "Read guides/review-workflow.md and execute the review workflow for the past week"
```

**After PR merge**:
```bash
claude -p "Read guides/review-workflow.md and execute the review workflow for PR #[number]"
```

**Manual**:
```
User: "Run a review of the past week"
Claude: [reads this guide and executes]
```

## After Review

Proposals sit in `.claude/reviews/` until a human:
1. Reads the proposals
2. Decides which to implement
3. Asks Claude to apply selected improvements
4. Claude implements conversationally (no special command needed)

The next review will check if implemented improvements actually prevented recurrence (meta-feedback).
