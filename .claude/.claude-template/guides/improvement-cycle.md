# Improvement Cycle Guide

## Purpose

Systematically improve the development system based on signals, routing fixes to the appropriate level (project vs generator).

## Principles

1. **Signals drive improvement** - Don't improve speculatively, improve based on evidence
2. **Root cause, not symptoms** - Trace issues to systemic causes
3. **Proportionate response** - Match fix complexity to problem frequency/severity
4. **Route appropriately** - Project issues stay in project, systemic issues go upstream
5. **Verify improvement** - Check that fixes actually prevent recurrence

## Improvement Phases

### Phase 1: Gather Signals
Collect from multiple sources:
- `.claude/signals/corrections.jsonl` - Human corrections
- Git history - Commits with fix/revert/oops
- Session logs - Errors and failures
- Memories - Noted issues from previous sessions

### Phase 2: Pattern Recognition
Don't fix individual incidents. Look for patterns:
- Same issue 2+ times → Pattern
- Same fix needed across files → Pattern
- Similar corrections from human → Pattern

Categorize patterns:
| Pattern | Frequency | Severity | Impact |
|---------|-----------|----------|--------|

### Phase 3: Root Cause Diagnosis

Trace from signal to system component:
```
Signal
  → Immediate cause (what directly failed)
    → System component (what part of dev system)
      → Root cause (why that component failed)
```

System components:
- Commands (`.claude/commands/`)
- Agents (`.claude/agents/`)
- Hooks (`.claude/hooks/`)
- Documentation (`CLAUDE.md`, docs/)
- Memories (Serena)
- Guides (if Level 1 issue)

### Phase 4: Level Classification

**Level 2 (Project-specific)**:
- Issue is unique to this project's context
- Fix: Modify project's commands/agents/hooks/docs

**Level 1 (Generator)**:
- Issue would occur in other projects too
- Pattern of same fix needed across projects
- Fix: Improve guides, exploration agents, or generation logic

**Mixed**:
- Apply immediate fix at Level 2
- Note pattern for Level 1 review

### Phase 5: Propose Improvement

| Improvement Type | When | Target |
|-----------------|------|--------|
| COMMAND_REFINEMENT | Command missing step | `.claude/commands/` |
| AGENT_REFINEMENT | Review gate inadequate | `.claude/agents/` |
| HOOK_ADDITION | Need automated reminder | `.claude/hooks/` |
| DOC_UPDATE | Information gap | CLAUDE.md or docs/ |
| MEMORY_UPDATE | Cross-session context gap | Serena memories |
| GUIDE_UPDATE | Generator producing suboptimal output | `guides/` (Level 1) |

Priority:
- P0: Blocking/breaking issues
- P1: Significant friction
- P2: Nice-to-have improvements

### Phase 6: Implement and Verify

1. Make the change
2. Test if applicable
3. Self-review with relevant reviewer
4. Log the improvement
5. Archive processed signals

### Phase 7: Level 1 Escalation (if applicable)

If pattern indicates generator issue:
1. Document the pattern clearly
2. Identify which guide or generation logic needs updating
3. Propose specific change to Level 1
4. Note expected impact on future project generation

## Improvement Types Detail

### COMMAND_REFINEMENT
- Missing step that should be present
- Unclear instruction causing mistakes
- Wrong sequence of operations
- Missing escalation trigger

### AGENT_REFINEMENT
- Checklist missing important item
- Verdict criteria too loose/strict
- Missing context in review

### HOOK_ADDITION
- Repeated violation of rule that exists
- Need automated enforcement or reminder
- Pre/post operation validation needed

### DOC_UPDATE
- CLAUDE.md missing important rule
- Documentation out of sync with code
- Missing context that causes confusion

### MEMORY_UPDATE
- Cross-session context getting lost
- Important decisions not recorded
- Project knowledge not captured

### GUIDE_UPDATE (Level 1)
- Guide missing principle that projects need
- Guide structure doesn't support good generation
- Anti-pattern not documented

## Quality Criteria

Good improvement cycle:
- [ ] Based on actual signals, not speculation
- [ ] Identifies patterns, not just incidents
- [ ] Traces to root cause
- [ ] Routes to correct level
- [ ] Improvement is proportionate to problem
- [ ] Verifies fix actually helps

## Anti-patterns

- **Speculative improvement**: Fixing things that aren't broken
- **Symptom treatment**: Adding reminder without fixing cause
- **Over-engineering**: Complex solution for rare edge case
- **Under-engineering**: Doc update when hook is needed
- **Level confusion**: Fixing generator when it's project-specific, or vice versa
- **Improvement fatigue**: Skipping verification

## System Health Metrics

Track to detect system bloat:
- CLAUDE.md size (target: <500 lines)
- Number of commands (target: <15)
- Number of agents (target: <10)
- Number of hooks (target: <10)

If exceeding targets, consider:
- Consolidation
- Moving content to docs/guides
- Removing unused components

## Adaptation Notes

When generating for a project:
- Include signal file paths
- Reference project's system components
- Set appropriate health thresholds for project size
- Include Level 1 escalation path to claude-enhanced
