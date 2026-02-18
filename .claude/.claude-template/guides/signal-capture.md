# Signal Capture Guide

## Purpose

Capture correction signals during development to enable systematic improvement of both the project configuration and the generation process.

## Principles

1. **Low friction** - Capturing a signal should be instant, not disruptive
2. **Context matters** - A signal without context is hard to diagnose
3. **Signals are data** - Don't analyze in the moment, analyze in improvement cycle
4. **Bare signals are valid** - Even "no stop" without explanation has value
5. **Patterns over incidents** - Individual signals matter less than patterns

## What Constitutes a Signal

### Human Corrections
- "No, stop" / "Wait" / "That's wrong"
- "You should have..."
- "Why didn't you..."
- "I already told you..."

### Workflow Violations
- Skipped a step that shouldn't have been skipped
- Proceeded without required approval
- Missed a checkpoint
- Ignored a gate failure

### Repeated Issues
- Same error occurring 2+ times
- Re-explaining the same concept
- Rediscovering the same constraint

### Quality Failures
- Test failures that should have been caught
- Lint errors that should have been prevented
- Security issues that should have been flagged

## Signal Format

```jsonl
{"ts": "ISO8601", "type": "correction|violation|repeated|quality", "note": "...", "context": "..."}
```

**Minimal signal** (always valid):
```jsonl
{"ts": "2025-01-08T10:30:00Z", "type": "correction", "note": "(bare signal)"}
```

**Rich signal** (more diagnosable):
```jsonl
{"ts": "2025-01-08T10:30:00Z", "type": "correction", "note": "should have checked null", "context": "working on user validation in auth.py"}
```

## Capture Protocol

### Immediate Capture
When signal occurs:
1. Record timestamp
2. Record type
3. Record note (user's words or brief description)
4. Record context if available (what was being done)
5. Continue working - don't stop to analyze

### Signal Storage
- Append to `.claude/signals/corrections.jsonl`
- One JSON object per line (JSONL format)
- Never edit existing signals
- Archive processed signals after improvement cycle

## Signal Categories for Diagnosis

| Category | Indicates | Likely Fix Location |
|----------|-----------|---------------------|
| Human correction | Missing pattern/rule/reminder | Command, CLAUDE.md, or hook |
| Workflow violation | Missing enforcement | Hook or command step |
| Repeated error | Gap in understanding or tooling | Memory, documentation, or guide |
| Quality failure | Inadequate review gate | Agent or checklist |

## Quality Criteria

Good signal capture:
- [ ] Signals are captured immediately, not reconstructed later
- [ ] Enough context to correlate with logs if needed
- [ ] Type classification is accurate
- [ ] Storage is append-only during active work

## Anti-patterns

- **Over-analyzing in the moment**: Stop and diagnose instead of capturing and continuing
- **Sanitizing signals**: Editing to make them "clearer" loses raw information
- **Ignoring bare signals**: They still indicate something happened
- **Delayed capture**: Trying to remember signals later

## Two-Level Routing

Signals inform improvement at two levels:

**Level 2 (Project)**: Fix the specific project configuration
- Command missing a step → Refine command
- Agent missing a check → Refine agent
- CLAUDE.md rule ignored → Add hook or restructure

**Level 1 (Generator)**: Improve what gets generated
- Pattern of same fix across projects → Improve guides
- Exploration consistently missing something → Improve exploration agents
- Generated commands consistently need same refinement → Improve generation logic

## Adaptation Notes

When generating for a project:
- Ensure signal directory exists
- Include signal capture in relevant commands (especially auto)
- Reference signal file in improvement command
- Adjust signal types if project has specific failure modes
