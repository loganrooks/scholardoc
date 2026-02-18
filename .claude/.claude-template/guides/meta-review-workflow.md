# Meta-Review Workflow Guide

## Purpose

Evaluate whether the improvement system itself is working. This is a higher-order feedback loop - feedback on the feedback system.

Without meta-review, we'd never know if:
- Fixes actually prevent recurrence
- The system is bloating with unused components
- Diagnoses are accurate
- Level 1/Level 2 classification is correct
- The overhead is worth the benefit

## Principles

1. **Measure what matters** - Focus on concrete, measurable outcomes
2. **Trends over snapshots** - Look at direction, not just current state
3. **Honest assessment** - Be willing to find that something isn't working
4. **Proportionate response** - Small problems get small fixes, systemic issues get rethought
5. **Avoid meta-bloat** - Don't let the review process itself become overhead

## Cadence

**Quarterly** - Enough time for:
- Improvements to show impact
- Patterns to accumulate across projects
- Meaningful trend analysis

Can be triggered earlier if:
- Major concerns arise during monthly cross-project review
- Multiple projects report the same recurring issue
- System size targets exceeded

## Metrics

### Primary Metrics

These directly measure if the system is working:

#### 1. Signal Volume Trend

```
For each project:
  signals_this_quarter = count(signals in last 3 months)
  signals_prev_quarter = count(signals in previous 3 months)
  trend = (signals_this_quarter - signals_prev_quarter) / signals_prev_quarter
```

| Trend | Interpretation |
|-------|----------------|
| Decreasing (< -10%) | Good - fewer corrections needed |
| Stable (-10% to +10%) | Neutral - not getting worse |
| Increasing (> +10%) | Concerning - investigate why |

**Caveat**: Increasing signals could mean better capture, not more problems. Check context.

#### 2. Recurrence Rate

```
recurrence_rate = count(issues that recurred) / count(issues with attempted fixes)
```

| Rate | Interpretation |
|------|----------------|
| < 15% | Excellent - fixes are working |
| 15-30% | Acceptable - some fixes need refinement |
| > 30% | Poor - diagnoses or fixes are inadequate |

Pull from `recurring_issues` memory across projects.

#### 3. Fix Effectiveness

```
For each improvement in improvement_history:
  effective = (outcome.recurrence == false)

effectiveness_rate = count(effective) / count(all improvements)
```

| Rate | Interpretation |
|------|----------------|
| > 70% | Good - most fixes work |
| 50-70% | Moderate - room for improvement |
| < 50% | Poor - diagnosis process needs work |

#### 4. Level 1 Hit Rate

```
For each L1 guide update:
  helped = did similar issues stop appearing in other projects?

l1_hit_rate = count(helped) / count(l1_updates)
```

| Rate | Interpretation |
|------|----------------|
| > 60% | Good - L1 classification is accurate |
| 40-60% | Moderate - some misclassification |
| < 40% | Poor - L1/L2 distinction needs work |

### Secondary Metrics

Supporting indicators:

#### 5. System Size (Bloat Check)

For each project, check:

| Component | Target | Warning | Critical |
|-----------|--------|---------|----------|
| CLAUDE.md lines | < 300 | 300-500 | > 500 |
| Commands | < 10 | 10-15 | > 15 |
| Agents | < 8 | 8-12 | > 12 |
| Hooks | < 5 | 5-10 | > 10 |

If critical thresholds exceeded → recommend consolidation.

#### 6. Time to Resolution

```
avg_resolution_time = average(date_fixed - date_signaled) for all improvements
```

Faster is better. If increasing, the process has too much friction.

#### 7. Review Completion Rate

```
completion_rate = projects_that_ran_review / projects_that_should_have
```

If projects aren't running reviews, the system isn't being used.

## Meta-Review Process

### Phase 1: Gather Data

Activate each project and collect:

```
for project in all_projects:
    activate_project(project)

    # Read memories
    feedback_state = read_memory("feedback_state")
    improvement_history = read_memory("improvement_history")
    recurring_issues = read_memory("recurring_issues")

    # Calculate metrics
    signal_count = count_signals_in_period(3_months)
    recurrence_rate = calculate_recurrence_rate(recurring_issues)
    fix_effectiveness = calculate_effectiveness(improvement_history)
    system_size = measure_system_size(project)

    record(project, metrics)
```

### Phase 2: Analyze Trends

Compare to previous meta-review:

```
read_memory("meta_review_state")  # Previous state

for each metric:
    current = calculate_current()
    previous = get_previous()
    trend = determine_trend(current, previous)

    if trend is concerning:
        flag_for_investigation()
```

### Phase 3: Investigate Concerns

For each flagged concern:

1. **Identify scope**: One project or systemic?
2. **Trace root cause**: Why is this metric bad?
3. **Check for confounds**: Is there an innocent explanation?
4. **Propose intervention**: What should change?

Common patterns:

| Symptom | Possible Cause | Investigation |
|---------|---------------|---------------|
| High recurrence | Wrong diagnoses | Review recent diagnoses - were root causes correct? |
| Signal volume increasing | Poor initial setup OR better capture | Check if new projects or existing getting worse |
| Low L1 hit rate | Over-generalizing | Review L1 signals - were they really systemic? |
| System bloat | Treating symptoms not causes | Check if rules overlap or could consolidate |
| Low review completion | Too much friction | Is review process too heavy? |

### Phase 4: Assess Guide Effectiveness

For each guide that was updated based on L1 feedback:

```
guide_updates = read_memory("guide_improvement_log")

for update in guide_updates:
    # Check if similar issues stopped
    projects_affected = update.trigger.projects
    issue_pattern = update.trigger.pattern

    occurrences_before = count_occurrences(issue_pattern, before=update.date)
    occurrences_after = count_occurrences(issue_pattern, after=update.date)

    if occurrences_after < occurrences_before:
        mark_as_effective(update)
    else:
        mark_for_review(update)  # Guide update didn't help
```

### Phase 5: Recommend Adjustments

Based on findings, recommend changes to:

**The improvement process itself:**
- Is the signal format capturing enough context?
- Is the review cadence right?
- Are diagnoses going deep enough?

**Specific guides or templates:**
- Which guides aren't being followed?
- Which guides need updates based on new patterns?

**The metrics we track:**
- Are we measuring the right things?
- Are thresholds appropriate?

**System health:**
- Which projects need attention?
- Is any project's system bloated?

### Phase 6: Update State

Write findings to `meta_review_state`:

```
write_memory("meta_review_state", {
  last_meta_review: today,
  next_meta_review: today + 3_months,

  metrics: {
    signal_volume: {trend, current, previous},
    recurrence_rate: {trend, rate},
    fix_effectiveness: {rate},
    l1_hit_rate: {rate},
    system_sizes: {per_project_summary}
  },

  assessment: {
    system_health: "good|moderate|poor",
    concerns: [...],
    recommendations: [...]
  },

  actions_taken: [
    {action, rationale, date}
  ]
})
```

## Output Format

```markdown
# Meta-Review: [Quarter] [Year]

**Date**: [date]
**Projects Reviewed**: [count]
**Previous Review**: [date]

## Executive Summary

[2-3 sentence assessment: Is the system working? Key concerns?]

## Metrics Dashboard

| Metric | Current | Previous | Trend | Status |
|--------|---------|----------|-------|--------|
| Signal Volume | | | ↓↑→ | 🟢🟡🔴 |
| Recurrence Rate | | | | |
| Fix Effectiveness | | | | |
| L1 Hit Rate | | | | |

## System Health by Project

| Project | CLAUDE.md | Commands | Agents | Hooks | Status |
|---------|-----------|----------|--------|-------|--------|
| | | | | | |

## Concerns Identified

### Concern 1: [Title]
- **Symptom**: [What we observed]
- **Investigation**: [What we found]
- **Root Cause**: [Why it's happening]
- **Recommendation**: [What to do]

## Guide Effectiveness

| Guide Updated | Date | Trigger | Effective? | Notes |
|---------------|------|---------|------------|-------|
| | | | | |

## Recommendations

### Process Changes
- [Changes to how we do reviews/signals/improvements]

### Guide Updates Needed
- [Guides that should be modified]

### Project-Specific Actions
- [Project]: [Action needed]

## Actions Taken This Review

- [x] [Action taken]
- [ ] [Action deferred to next review]

## Next Review

**Scheduled**: [date]
**Focus Areas**: [What to watch]
```

## Warning Signs

Red flags that suggest the system needs significant intervention:

| Warning Sign | What It Means | Response |
|--------------|---------------|----------|
| Recurrence > 40% | Fixes aren't working | Review diagnosis process |
| Signal volume spiking | Something broke or changed | Investigate immediately |
| Multiple projects bloated | Templates generating too much | Simplify templates |
| L1 hit rate < 30% | Misclassifying systemic issues | Revisit L1/L2 criteria |
| Reviews not happening | Process too heavy | Simplify or automate |
| Same L1 pattern 3+ times | Guide updates not sticking | Deeper intervention needed |

## Anti-patterns

- **Metric gaming**: Optimizing numbers instead of outcomes
- **Over-reaction**: Major process changes for minor fluctuations
- **Under-reaction**: Ignoring consistent warning signs
- **Meta-bloat**: Making the review process itself too heavy
- **Blame assignment**: Focusing on "who" instead of "what" and "why"

## Triggering This Workflow

**Scheduled (quarterly)**:
```bash
claude -p "Read guides/meta-review-workflow.md and run quarterly meta-review"
```

**Ad-hoc (concerns arose)**:
```
User: "Run a meta-review, I'm seeing recurring issues across projects"
Claude: [reads this guide and executes]
```

## Relationship to Other Workflows

```
Weekly: Project reviews (per-project)
    ↓
Monthly: Cross-project review (identify L1 patterns)
    ↓
Quarterly: Meta-review (is the system working?)
    ↓
Feeds back into: Guide updates, process changes
```

Meta-review is the highest-level feedback loop. It evaluates everything below it.
