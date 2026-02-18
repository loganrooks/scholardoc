# Serena Memory Schemas

Standard schemas for Serena memories used in the feedback system.

## Overview

Two levels of memories:
1. **Project-level**: Written by individual projects during their improvement cycles
2. **claude-enhanced-level**: Written during cross-project review

claude-enhanced pulls from project-level memories to identify systemic patterns.

---

## Project-Level Memories

These memories are written by each project that uses the autonomous-dev system.

### `feedback_state`

Current state of the feedback system for this project.

```yaml
feedback_state:
  last_review_date: "2026-01-08"
  signals_since_last_review: 3
  pending_improvements:
    - id: "prop_001"
      summary: "Add migration reminder to plan command"
      severity: P1
      status: pending
    - id: "prop_002"
      summary: "Update CLAUDE.md with test-first rule"
      severity: P2
      status: pending
  next_review_recommended: "2026-01-15"
```

**When written**: After each review workflow run
**When read**: At session start (via /resume), during cross-project review

---

### `improvement_history`

Log of improvements attempted and their outcomes. This is the primary source for cross-project pattern detection.

```yaml
improvement_history:
  entries:
    - date: "2026-01-08"
      signal:
        summary: "Should check for existing libraries before building custom"
        type: correction
        user_feedback: "wrong approach"
        diagnosis:
          what_happened: "Started implementing custom JWT handling"
          why: "Assumed we needed custom solution"
          should_have: "Checked npm for existing auth libraries"
        level: 1  # Systemic - would happen in other projects
      improvement:
        type: COMMAND_REFINEMENT
        target: "explore.md"
        change: "Added step: check for existing solutions before proposing custom"
      outcome:
        status: applied
        recurrence: false  # Has the issue come back?
        notes: "Working well so far"

    - date: "2026-01-05"
      signal:
        summary: "Forgot to create migration file"
        type: correction
        user_feedback: "You didn't create a migration file"
        diagnosis:
          what_happened: "Modified schema directly without migration"
          why: "Focused on model change, forgot migration step"
          should_have: "Run prisma migrate dev"
        level: 2  # Project-specific
      improvement:
        type: HOOK_ADDITION
        target: "schema-change-reminder.md"
        change: "Added hook to remind about migrations when schema files change"
      outcome:
        status: applied
        recurrence: false
        notes: null
```

**When written**: After applying improvements
**When read**: During review (to check recurrence), during cross-project review

---

### `recurring_issues`

Issues that keep coming back despite attempted fixes. High signal for systemic problems.

```yaml
recurring_issues:
  - issue: "Forgetting to run tests before committing"
    occurrences: 3
    dates: ["2026-01-02", "2026-01-05", "2026-01-08"]
    attempted_fixes:
      - date: "2026-01-03"
        fix: "Added reminder to CLAUDE.md"
        result: "Did not help"
      - date: "2026-01-06"
        fix: "Added pre-commit hook"
        result: "Partially helped, still sometimes bypassed"
    status: unresolved
    escalation_candidate: true  # Suggests Level 1 issue

  - issue: "Over-scoping refactoring tasks"
    occurrences: 2
    dates: ["2025-12-28", "2026-01-04"]
    attempted_fixes:
      - date: "2025-12-29"
        fix: "Added scope confirmation step to refactor command"
        result: "Helped"
    status: resolved
    escalation_candidate: false
```

**When written**: When same issue appears 2+ times
**When read**: During review, during cross-project review (high-value signal)

---

### `learned_preferences`

Project-specific patterns learned from corrections. NOT for cross-project use.

```yaml
learned_preferences:
  - preference: "Use async/await over .then() chains"
    source: "User correction on 2026-01-03"
    applies_to: "JavaScript/TypeScript code"

  - preference: "Always use UserService, not direct DB queries for user operations"
    source: "Architecture decision + correction"
    applies_to: "User-related operations"

  - preference: "Prefer small PRs (< 300 lines)"
    source: "Multiple corrections about PR size"
    applies_to: "Pull requests"
```

**When written**: When pattern emerges from corrections
**When read**: During development in this project (context)

---

## claude-enhanced-Level Memories

Written when reviewing patterns across all projects.

### `level1_patterns`

Patterns identified across multiple projects that indicate systemic issues.

```yaml
level1_patterns:
  last_updated: "2026-01-08"
  patterns:
    - pattern: "Not checking for existing solutions before building custom"
      projects_affected: ["scholardoc", "audiobookify"]
      occurrences: 4
      root_cause: "explore.md doesn't emphasize checking existing solutions"
      proposed_fix: "Update exploration guide to prioritize existing solution check"
      status: identified

    - pattern: "Skipping tests when making 'small' changes"
      projects_affected: ["scholardoc", "acadlib", "philorag"]
      occurrences: 7
      root_cause: "No enforcement mechanism for test runs"
      proposed_fix: "Add to autonomous-workflow guide: always run tests"
      status: fix_applied
      guide_updated: "autonomous-workflow.md"
      date_fixed: "2026-01-05"
```

**When written**: After cross-project review
**When read**: When updating guides, during meta-review

---

### `guide_improvement_log`

History of guide updates based on cross-project feedback.

```yaml
guide_improvement_log:
  entries:
    - date: "2026-01-05"
      guide: "autonomous-workflow.md"
      change: "Added explicit test requirement before phase transitions"
      trigger:
        pattern: "Skipping tests when making small changes"
        projects: ["scholardoc", "acadlib"]
        signals: 5
      outcome: pending_validation  # Need to see if it helps

    - date: "2025-12-20"
      guide: "exploration.md"
      change: "Added 'check existing solutions' as first step"
      trigger:
        pattern: "Building custom when library exists"
        projects: ["scholardoc"]
        signals: 2
      outcome: validated  # Reduced occurrences
```

**When written**: After updating guides
**When read**: During meta-review, when making future guide updates

---

### `meta_review_state`

State of the meta-review process - is the improvement system itself working?

```yaml
meta_review_state:
  last_meta_review: "2026-01-01"
  next_meta_review: "2026-04-01"  # Quarterly

  metrics:
    signal_volume:
      trend: decreasing  # Good sign
      last_month: 12
      previous_month: 18

    recurrence_rate:
      trend: stable
      rate: 0.15  # 15% of issues recur

    level1_hit_rate:
      description: "Do Level 1 fixes actually help other projects?"
      rate: 0.70  # 70% of L1 fixes helped

  assessment:
    system_health: good
    concerns:
      - "Implicit signal detection not yet implemented"
      - "Some projects not running regular reviews"
    recommendations:
      - "Implement native log analysis for implicit signals"
      - "Add review reminder to session-end"
```

**When written**: After quarterly meta-review
**When read**: When assessing system health, planning improvements to the improvement system

---

## Memory Lifecycle

```
Project Session:
  /signal → JSONL file
  Review → reads JSONL → writes feedback_state, improvement_history
  Apply improvement → updates improvement_history with outcome
  Recurring issue → writes to recurring_issues

Cross-Project Review (in claude-enhanced):
  → activate each project
  → read improvement_history, recurring_issues
  → identify patterns
  → write level1_patterns
  → update guides
  → write guide_improvement_log

Meta-Review (quarterly):
  → read all memories
  → assess system health
  → write meta_review_state
```

---

## Reading Memories for Cross-Project Review

When claude-enhanced reviews across projects:

```python
# Pseudocode for cross-project review
projects = ["scholardoc", "acadlib", "audiobookify", ...]
all_signals = []

for project in projects:
    activate_project(project)
    history = read_memory("improvement_history")
    recurring = read_memory("recurring_issues")

    # Extract Level 1 signals and recurring issues
    for entry in history.entries:
        if entry.signal.level == 1:
            all_signals.append(entry)

    for issue in recurring:
        if issue.escalation_candidate:
            all_signals.append(issue)

activate_project("claude-enhanced")
patterns = synthesize_patterns(all_signals)
write_memory("level1_patterns", patterns)
```
