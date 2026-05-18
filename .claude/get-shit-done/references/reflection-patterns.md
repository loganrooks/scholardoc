# Reflection Patterns Reference

Reference specification for pattern detection, lesson distillation, phase-end reflection, and semantic drift detection in the GSD self-improvement loop.

**Version:** 1.2.0
**Phase:** 04-reflection-engine, 31-signal-schema-foundation, 33-enhanced-reflector

---

## 1. Overview

The Reflection Engine is the closing loop of the GSD self-improvement cycle. It transforms accumulated signals into actionable knowledge by:

1. **Detecting patterns** in recurring signals using severity-weighted thresholds
2. **Comparing execution** against plans at phase boundaries
3. **Distilling lessons** from qualifying patterns
4. **Tracking semantic drift** through metric trend analysis
5. **Surfacing improvement suggestions** based on recurring friction points

**Core principle:** The system never makes the same mistake twice. Signals capture what went wrong, patterns identify recurring issues, and lessons prevent future occurrences.

**When reflection runs:**
- On explicit `/gsd:reflect` command
- At phase-end (optional, configurable)
- During milestone completion (optional integration)

**What reflection does NOT do:**
- Modify execution behavior (retrospective only)
- Run continuously (event-driven, not background)
- Require external ML models (heuristics on structured data)

---

## 2. Pattern Detection Rules

### 2.1 Confidence-Weighted Scoring

Pattern detection uses confidence-weighted scoring rather than raw occurrence counts. This weights high-confidence signals more heavily, so a cluster of 3 high-confidence signals surfaces a pattern that 5 low-confidence signals would not.

**Scoring formula:**

```
weighted_score = sum(weight(signal) for signal in cluster)

weight(signal) = confidence_weight * severity_multiplier

confidence_weight:
  high   -> 2.0
  medium -> 1.0
  low    -> 0.5

severity_multiplier:
  critical -> 1.5
  notable  -> 1.0
  minor    -> 0.7
```

**Pattern qualification thresholds (by max severity in cluster):**

| Max Severity | Weighted Score Threshold | Rationale |
|-------------|--------------------------|-----------|
| `critical` | 3.0 | Cannot risk missing dangerous patterns |
| `notable` | 4.0 | High-impact issues warrant attention |
| `minor` | 5.0 | Must be truly recurring, not noise |
| `trace` | N/A | Not persisted to KB, not in pattern detection pool |

**Default confidence for legacy signals:** Signals missing the `confidence` field default to `medium` (weight 1.0). This gives legacy signals neutral weight -- neither penalized nor boosted -- preserving backward compatibility with pre-Phase 31 signals.

**Threshold application:**
```
# Pseudocode for confidence-weighted threshold check

for each cluster:
  weighted_score = 0
  for each signal in cluster:
    confidence = signal.confidence or "medium"  # default for legacy
    confidence_weight = { high: 2.0, medium: 1.0, low: 0.5 }[confidence]
    severity_mult = { critical: 1.5, notable: 1.0, minor: 0.7 }[signal.severity]
    weighted_score += confidence_weight * severity_mult

  max_severity = max(signal.severity for signal in cluster)
  threshold = { critical: 3.0, notable: 4.0, minor: 5.0 }[max_severity]

  if weighted_score >= threshold:
    emit_pattern(cluster, weighted_score)
```

**Worked examples:**

| Scenario | Signals | Calculation | Score | Threshold | Qualifies? |
|----------|---------|-------------|-------|-----------|------------|
| 3 high-confidence critical | 3 signals (high, critical) | 3 * 2.0 * 1.5 | 9.0 | 3.0 | YES -- well above threshold |
| 5 low-confidence minor | 5 signals (low, minor) | 5 * 0.5 * 0.7 | 1.75 | 5.0 | NO -- correctly filters noise |
| 4 medium-confidence notable | 4 signals (medium, notable) | 4 * 1.0 * 1.0 | 4.0 | 4.0 | YES -- qualifies at boundary |
| 2 high-confidence notable + 1 low-confidence notable | 3 mixed signals | 2 * 2.0 * 1.0 + 1 * 0.5 * 1.0 | 4.5 | 4.0 | YES -- mixed confidence works |

### 2.2 Signal Clustering Criteria

Signals cluster into patterns based on shared characteristics. Criteria in priority order:

| Priority | Criteria | Match Strength | Use Case |
|----------|----------|----------------|----------|
| 1 | Same `signal_type` + 2+ overlapping tags | Strongest | Core pattern identification |
| 2 | Same project + same `signal_type` + similar slug | Strong | Project-specific recurrence |
| 3 | Cross-project: same tags + same `signal_type` | Moderate | Candidate global pattern |

**Primary clustering algorithm:**
1. Group signals by `signal_type` (deviation, struggle, config-mismatch, epistemic-gap, baseline, improvement, good-pattern)
2. Within each group, cluster by tag overlap (2+ shared tags)
3. For each cluster, take the highest severity among members
4. Calculate confidence-weighted score for cluster (see Section 2.1)
5. Apply weighted score threshold based on cluster's max severity

**Secondary clustering fallback:** When primary clustering yields fewer than 5 qualifying patterns, apply a relaxed mode to catch thematic patterns fragmented across signal types:
- **Criteria:** Same project + 3+ overlapping tags + any `signal_type`
- **Constraint:** Positive and negative signals still cluster separately (respects `signal_category`)
- **Marking:** Secondary clusters are marked as "cross-type" in output
- **Score penalty:** Secondary clusters receive a 0.8x score multiplier (slightly penalized for weaker `signal_type` coherence)
- **Rationale:** Signals about the same issue may be typed as `deviation`, `struggle`, and `config-mismatch` depending on context. Without secondary clustering, these related signals fragment into separate under-threshold groups and the pattern is missed

**Signal category clustering rules:**
- **Positive and negative signals cluster separately.** A positive baseline and a negative deviation with overlapping tags should NOT cluster together -- they represent fundamentally different observations.
- **Epistemic gap signals may cluster with related deviation or struggle signals** if tags overlap. An epistemic gap about auth and a deviation about auth are related -- they share the same knowledge domain and the gap may explain the deviation.
- Clustering respects `signal_category` first, then applies the standard `signal_type` + tag overlap criteria within each category.

**Example clustering:**
```bash
# Extract pattern keys from index
# Primary: Pattern key = signal_type + first two tags
# Secondary (fallback): Pattern key = project + first three tags (any signal_type)
extract_patterns() {
  grep "^| sig-" "$KB_DIR/index.md" | while read -r row; do
    signal_type=$(get_signal_type_from_file "$row")
    tags=$(echo "$row" | cut -d'|' -f5 | tr -d ' ')
    primary_tags=$(echo "$tags" | cut -d',' -f1-2)
    echo "primary:${signal_type}:${primary_tags}"
  done
}

extract_secondary_patterns() {
  grep "^| sig-" "$KB_DIR/index.md" | while read -r row; do
    project=$(echo "$row" | cut -d'|' -f3 | tr -d ' ')
    tags=$(echo "$row" | cut -d'|' -f5 | tr -d ' ')
    top_tags=$(echo "$tags" | cut -d',' -f1-3)
    echo "secondary:${project}:${top_tags}"
  done
}
```

### 2.3 Pattern Output Format

When a pattern qualifies (meets weighted score threshold), emit in this structure:

```markdown
## Pattern: {pattern-name}

**Signal type:** {deviation|struggle|config-mismatch}
**Cluster type:** {primary | cross-type}
**Occurrences:** {count}
**Weighted score:** {score} (threshold: {threshold})
**Severity:** {highest severity among grouped signals}
**Confidence:** {high|medium|low}

**Signals in pattern:**

| ID | Project | Date | Tags | Confidence | Severity |
|----|---------|------|------|------------|----------|
| sig-X | project-a | 2026-02-01 | tag1, tag2 | high | critical |
| sig-Y | project-b | 2026-02-03 | tag1, tag3 | medium | notable |

**Root cause hypothesis:** {Agent's assessment of why this pattern recurs}

**Recommended action:** {What to do about it}
```

### 2.4 Time and Persistence

**Critical rule:** No time-based rolling windows.

Time-based windows lose infrequent but persistent issues (e.g., library bug recurring across versions over months). Instead:

- **Recency affects priority ranking**, not exclusion
- Old signals with same tags/type still cluster with new signals
- Signals remain in pattern detection pool regardless of age
- Archival (via `status: archived`) is the only exclusion mechanism

### 2.5 Counter-Evidence Seeking (REFLECT-03)

Before confirming a pattern, the reflector actively seeks evidence that contradicts the pattern. This prevents false positives and confirmation bias.

**Counter-evidence sources** (in priority order):

1. **Positive signals with same tags:** Signals with overlapping tags but `signal_category: positive` (positive signals contradict negative patterns). A positive baseline about auth and a negative deviation about auth represent conflicting observations.
2. **Remediated/verified signals:** Signals where the same issue was resolved (`lifecycle_state: remediated` or `verified`). If the issue has been fixed, the pattern may be stale.
3. **Time-decay indicator:** If ALL pattern signals are older than 30 days with no recent recurrence, flag as "potentially stale" (advisory only -- does NOT exclude from detection, per Section 2.4).

**Bounded search:** Examine up to 3 potential counter-examples per pattern. This bounds the analysis effort while still checking for obvious contradictions.

**Index-first counter-evidence search:** Counter-evidence candidates may NOT be in qualifying clusters (e.g., a lone positive signal). To avoid breaking the two-pass context budget model, counter-evidence search MUST use index metadata (tags, signal_category, lifecycle_state columns) to identify candidates first. Only read the full signal file for confirmed counter-evidence candidates (max 3 per pattern). This keeps the additional file reads bounded to 3 * N_patterns, not the entire signal corpus.

**Counter-evidence impact:**

| Counter-Examples Found | Impact |
|----------------------|--------|
| 0 | Pattern confirmed at current confidence |
| 1 | Reduce pattern confidence one level (e.g., high -> medium) |
| 2-3 | Reduce pattern confidence two levels (e.g., high -> low) or flag as "investigate" triage candidate |

Counter-evidence is always cited in the pattern report. The original (pre-adjustment) confidence is preserved alongside the adjusted confidence for transparency.

**Counter-evidence output format:**

```markdown
**Counter-evidence ({N} found):**
- {signal-id}: {why it contradicts the pattern}
- **Impact:** Confidence reduced from {original} to {adjusted}
```

If no counter-evidence is found:
```markdown
**Counter-evidence (0 found):** Pattern confirmed at {confidence} confidence.
```

---

## 3. Phase-End Reflection (RFLC-01)

Compare PLAN.md against SUMMARY.md at phase completion to identify systemic deviations.

### 3.1 Comparison Points

| PLAN.md Source | SUMMARY.md Source | Deviation Type |
|----------------|-------------------|----------------|
| Task count (`<task>` elements) | Task Commits table rows | Task mismatch |
| `files_modified` frontmatter | Files Created/Modified section | File scope creep/shrink |
| Estimated duration (if present) | Actual duration | Time estimation error |
| `must_haves.truths` | VERIFICATION.md results | Goal achievement failure |
| `autonomous: true` | Checkpoint returns documented | Autonomy failure |
| Empty "Issues Encountered" | Non-trivial issues documented | Unexpected friction |

### 3.2 Deviation Analysis

For each comparison point, calculate:
- **Delta:** Absolute difference (e.g., +2 tasks, -1 file)
- **Direction:** Expansion (+) or contraction (-)
- **Impact:** Assessment of whether deviation was beneficial, neutral, or problematic

### 3.3 must_haves vs VERIFICATION.md Gaps

Cross-reference `must_haves` from PLAN.md frontmatter against VERIFICATION.md:

```yaml
# From PLAN.md
must_haves:
  truths:
    - "Pattern detection rules exist for severity-weighted thresholds"
    - "Lesson distillation criteria and flow are documented"
  artifacts:
    - path: "./.claude/get-shit-done/references/reflection-patterns.md"
      provides: "Pattern detection rules"
```

Compare against VERIFICATION.md success criteria results. Any failed criterion is a gap.

### 3.4 Reflection Output Format

```markdown
## Phase {N} Reflection

**Plan:** {phase}-{plan}-PLAN.md
**Summary:** {phase}-{plan}-SUMMARY.md
**Overall alignment:** {high|medium|low}

### Deviations Found

| Category | Planned | Actual | Delta | Impact |
|----------|---------|--------|-------|--------|
| Task count | 5 | 6 | +1 | Auto-fix added |
| File scope | 4 files | 7 files | +3 | Supporting files needed |
| Duration | ~30min | 48min | +60% | Blocking issue encountered |

### Auto-Fixes Applied

| # | Rule | Description | Files |
|---|------|-------------|-------|
| 1 | Rule 1 - Bug | Fixed null pointer in auth | src/auth.ts |
| 2 | Rule 2 - Missing Critical | Added input validation | src/api/users.ts |

### Issues Encountered

[Summary of non-trivial issues from SUMMARY.md]

### Patterns Detected This Phase

[Patterns found from signals collected during this phase]

### Lessons Suggested

[Draft lessons based on deviations and patterns]
```

---

## 4. Lesson Distillation (RFLC-02)

Convert qualifying signal patterns into actionable lesson entries.

### 4.1 Distillation Criteria

A pattern qualifies for lesson distillation when ALL of:
1. **Meets threshold:** Pattern occurrence count meets severity-weighted threshold
2. **Consistent root cause:** Signals in pattern share similar root cause hypothesis
3. **Actionable:** A concrete recommendation can be derived

### 4.2 Lesson Creation Flow

```
1. Identify qualifying pattern
       |
       v
2. Draft lesson content
   - category: From taxonomy (tooling, architecture, testing, workflow, external, environment)
   - insight: One-sentence actionable lesson
   - evidence: List of signal IDs supporting this lesson
   - confidence: Based on occurrence count and consistency
   - durability: workaround, convention, or principle
       |
       v
3. Determine scope (project vs global)
   - Apply heuristics (see 4.3)
       |
       v
4. Document in reflection report
   - Lesson candidates are recorded in the reflection report only (lesson files deprecated)
       |
       v
5. Rebuild index
   - Run kb-rebuild-index.sh
```

### 4.3 Scope Determination Heuristics

**Global scope indicators:**
- References named library or framework (e.g., "Vitest", "Next.js", "Prisma")
- Root cause is external (library bug, documentation gap, tool limitation)
- Would affect any project using similar technology stack
- Signal has `likely_scope: global` hint

**Project scope indicators:**
- References specific file paths (e.g., `src/lib/auth.ts`)
- References project structure or local configuration
- Root cause is internal (our code, our design choices)
- Pattern limited to one project

**Default rule:** When uncertain, default to project-scoped. Safer to keep lessons project-local than pollute global namespace with noise.

**Autonomy tie-in:**
- **YOLO mode:** High-confidence global lessons auto-promote
- **Interactive mode:** Suggest global promotion, user confirms

### 4.4 Lesson Content Structure

From kb-templates/lesson.md:

```yaml
---
id: les-{YYYY-MM-DD}-{slug}
type: lesson
project: {project-name|_global}
tags: [{tag1}, {tag2}]
created: {timestamp}
updated: {timestamp}
durability: {workaround|convention|principle}
status: active
category: {category}
evidence_count: {number}
evidence: [{signal-id-1}, {signal-id-2}]
confidence: {high|medium|low}
---

## Lesson

{One-sentence actionable insight}

## When This Applies

{Conditions, contexts, or triggers}

## Recommendation

{Specific guidance for agents}

## Evidence

{References to supporting signals with descriptions}
```

---

## 5. Cross-Project Detection (SGNL-07)

Scan signals across all projects to identify patterns that transcend individual projects.

### 5.1 Detection Approach

1. **Read index.md** - Already contains all projects' signals
2. **Group by tag + signal_type** - Ignore project field during grouping
3. **Apply severity-weighted thresholds** - Same rules as single-project
4. **Check `likely_scope: global` hints** - Signals flagged at creation time
5. **Validate cross-project span** - Pattern must span 2+ projects

### 5.2 Global Lesson Criteria

A pattern qualifies as global lesson when:
- Pattern spans **2+ distinct projects**
- Signals share **same root cause hypothesis**
- Root cause is **external** (library, framework, tool, environment)

### 5.3 Cross-Project Query

```bash
# Query index for cross-project patterns
# Group by signal_type + tags, ignoring project column

# KB path resolution -- project-local primary, user-global fallback
if [ -d ".planning/knowledge" ]; then KB_DIR=".planning/knowledge"; else KB_DIR="$HOME/.gsd/knowledge"; fi
KB_INDEX="$KB_DIR/index.md"

# Extract all signal rows
grep "^| sig-" "$KB_INDEX" | while read row; do
  project=$(echo "$row" | cut -d'|' -f3 | tr -d ' ')
  tags=$(echo "$row" | cut -d'|' -f5 | tr -d ' ')
  # Track project count per tag combination
  echo "$tags:$project"
done | sort | uniq | cut -d':' -f1 | sort | uniq -c
# Patterns appearing with 2+ unique projects are candidates
```

### 5.4 Cross-Project Access Control

- **Default:** Cross-project detection enabled (KB is user-level)
- **User setting:** Opt-in or opt-out in `/gsd:settings`
- **Per-project override:** `.planning/config.json` can disable cross-project sharing
- **Privacy:** Lessons from private projects stay project-scoped

---

## 6. Semantic Drift Detection (RFLC-06)

Track whether agent output quality degrades over time using heuristic indicators.

### 6.1 Drift Indicators

No ML required. Track these metrics across phases:

| Metric | Source | What It Measures |
|--------|--------|------------------|
| Verification gap rate | VERIFICATION.md `gaps_found` | Are more plans failing verification? |
| Auto-fix frequency | SUMMARY.md "Deviations" | Are plans needing more corrections? |
| Signal severity rate | Signal index | Is critical/notable proportion increasing? |
| Deviation-to-plan ratio | PLAN vs SUMMARY comparison | Are executions deviating more from plans? |

### 6.2 Detection Algorithm

```bash
# Compare recent N phases against baseline M phases
RECENT_PHASES=5
BASELINE_PHASES=10

# Calculate metric rates for recent period
recent_gap_rate=$(calculate_gap_rate last $RECENT_PHASES)
recent_autofix_rate=$(calculate_autofix_rate last $RECENT_PHASES)
recent_severity_rate=$(calculate_severity_rate last $RECENT_PHASES)

# Calculate baseline rates
baseline_gap_rate=$(calculate_gap_rate previous $BASELINE_PHASES)
baseline_autofix_rate=$(calculate_autofix_rate previous $BASELINE_PHASES)
baseline_severity_rate=$(calculate_severity_rate previous $BASELINE_PHASES)

# Flag if recent is 50%+ worse than baseline
for metric in gap_rate autofix_rate severity_rate; do
  if recent > baseline * 1.5; then
    emit_drift_warning "$metric increased by 50%+"
  fi
done
```

### 6.3 Detection Thresholds

| Condition | Assessment |
|-----------|------------|
| All metrics within 20% of baseline | STABLE |
| Any metric 20-50% worse than baseline | DRIFTING |
| Any metric 50%+ worse than baseline | CONCERNING |

### 6.4 Drift Report Format

```markdown
## Semantic Drift Check

**Period:** Last {N} phases
**Baseline:** Previous {M} phases

| Metric | Baseline | Recent | Change | Status |
|--------|----------|--------|--------|--------|
| Verification gaps | 12% | 18% | +50% | CONCERNING |
| Auto-fixes/plan | 1.2 | 1.8 | +50% | CONCERNING |
| Critical signals | 0.4/phase | 0.5/phase | +25% | DRIFTING |
| Deviation ratio | 0.15 | 0.18 | +20% | STABLE |

**Overall assessment:** {STABLE|DRIFTING|CONCERNING}

**Recommendation:**
{If CONCERNING: Review recent plans for pattern, consider pausing for investigation}
{If DRIFTING: Monitor in next phase, flag if continues}
{If STABLE: No action needed}
```

---

## 7. Workflow Improvement Suggestions (RFLC-05)

Generate actionable improvement suggestions based on recurring signal patterns.

### 7.1 Suggestion Triggers

Generate suggestions when:
- Pattern reaches `high` confidence (6+ occurrences)
- Pattern spans multiple phases or plans
- Root cause analysis points to workflow issue

### 7.2 Suggestion Template

```markdown
## Workflow Improvement Suggestion

**Pattern observed:** {pattern-name}
**Occurrences:** {count} across {N} phases
**Impact:** {Description of workflow friction this causes}

**Root cause:** {Why this keeps happening}

**Recommended workflow change:**

1. {Specific modification to workflow/process}
2. {Expected benefit}
3. {How to implement}

**Evidence:**
- {signal-id-1}: {brief description}
- {signal-id-2}: {brief description}
```

### 7.3 Suggestion Categories

| Category | Trigger Pattern | Example Suggestion |
|----------|-----------------|-------------------|
| Planning | Consistent task count mismatches | "Break large tasks into smaller atomic units" |
| Verification | Repeated verification gaps | "Add verification criteria to plan frontmatter" |
| Configuration | Config mismatch patterns | "Document model requirements in CONTEXT.md" |
| Testing | Test-related struggles | "Add test infrastructure check to plan start" |

---

## 8. Category Taxonomy (Authoritative)

Predefined top-level categories with emergent subcategories. **This taxonomy is authoritative.** The reflector agent and lesson templates use these categories. Legacy categories (`debugging`, `performance`, `other`) from earlier agent spec versions map to: `debugging` -> `testing`, `performance` -> `architecture`, `other` -> `workflow`.

### 8.1 Top-Level Categories

| Category | Scope | Examples | Legacy Mappings |
|----------|-------|----------|-----------------|
| `tooling` | Build tools, test runners, linters | Vitest, ESLint, Webpack | -- |
| `architecture` | Code structure, patterns, design, performance | Barrel exports, service layers | `performance` -> `architecture` |
| `testing` | Test strategies, fixtures, mocking, debugging | Snapshot testing, mock setup | `debugging` -> `testing` |
| `workflow` | GSD workflow, CI/CD, automation, uncategorized | Plan structure, verification | `other` -> `workflow` |
| `external` | Third-party services, APIs, libraries | Claude API, npm, OAuth providers | -- |
| `environment` | OS, runtime, configuration | Node versions, env vars | -- |

### 8.2 Subcategory Emergence

Subcategories emerge organically as lessons accumulate:
- `tooling/vitest` - Vitest-specific lessons
- `external/claude-api` - Claude API quirks and workarounds
- `workflow/planning` - GSD planning process lessons

**Naming convention:** `{top-level}/{specific}` using kebab-case

### 8.3 Category Assignment

When creating a lesson:
1. Identify primary concern from pattern context
2. Match to top-level category
3. If pattern is tool/library-specific, add subcategory
4. If no existing subcategory fits and pattern is specific, create new one

---

## 9. Confidence Expression

Use categorical confidence with occurrence count evidence.

### 9.1 Confidence Levels

Confidence uses the three-tier categorical model (`high`, `medium`, `low`) matching the signal schema's `confidence` field values. Confidence levels now feed into weighted scoring (Section 2.1), not just reporting -- a signal's confidence directly affects whether its cluster qualifies as a pattern.

| Level | Criteria | Weighted Score Impact | Expression |
|-------|----------|----------------------|------------|
| `high` | 6+ occurrences, empirical evidence, consistent root cause | 2.0x weight per signal | "high (7 occurrences across 3 projects)" |
| `medium` | 3-5 occurrences, inference from patterns | 1.0x weight per signal (baseline) | "medium (4 occurrences, same root cause)" |
| `low` | 2-3 occurrences, educated guess, or epistemic gap | 0.5x weight per signal | "low (2 occurrences, similar symptoms)" |

### 9.2 Actionability Levels

Based on confidence, lessons have different actionability:

| Confidence | Actionability | Lesson Framing |
|------------|--------------|----------------|
| `high` | Directive | "Always do X when Y occurs" |
| `medium` | Recommendation | "Consider X when encountering Y" |
| `low` | Observation | "Pattern observed: X tends to cause Y" |

### 9.3 Confidence in Output

Always include occurrence count when stating confidence:
- "Confidence: high (12 occurrences, 4 projects)"
- "Confidence: medium (4 occurrences, consistent root cause)"
- "Confidence: low (2 occurrences, same tags)"

---

## 10. Anti-Patterns to Avoid

Common mistakes in reflection implementation.

### 10.1 Time-Based Rolling Windows

**Anti-pattern:** "Delete signals older than 30 days"
**Problem:** Loses infrequent but persistent issues (e.g., library bug recurring across versions)
**Correct approach:** Use recency for priority ranking, not exclusion. Archive via status field only.

### 10.2 Automatic Global Promotion in Interactive Mode

**Anti-pattern:** Auto-promoting lessons to global scope without user confirmation
**Problem:** Pollutes global namespace with project-specific noise
**Correct approach:** In interactive mode, suggest promotion and wait for user confirmation. Auto-promote only in YOLO mode for `high` confidence lessons.

### 10.3 Pattern Detection on Every Signal Write

**Anti-pattern:** Running full pattern detection when each new signal is written
**Problem:** Performance overhead, unnecessary computation
**Correct approach:** Pattern detection runs on reflection trigger (explicit command, phase-end, milestone). Not continuous.

### 10.4 Circular Evidence in Lessons

**Anti-pattern:** Lesson references signals created after the lesson existed
**Problem:** Circular reasoning - lesson can't be evidence for itself
**Correct approach:** Evidence links point to signal IDs created BEFORE the lesson's `created` timestamp. New signals after lesson creation are updates, not circular.

### 10.5 ML-Based Classification

**Anti-pattern:** Using embedding models or semantic similarity for pattern detection
**Problem:** Adds dependencies, opacity, unpredictability
**Correct approach:** Signals have explicit tags and types. String matching on structured frontmatter is sufficient and debuggable.

### 10.6 Modifying Signal Detection Payload

**Anti-pattern:** Editing signal detection payload fields (id, type, project, tags, created, severity, signal_type, signal_category, phase, plan, polarity, source, evidence, confidence, confidence_basis) after creation.
**Problem:** Detection payload captures a moment in time -- the original observation. Modifying it destroys the historical record.
**Correct approach:** Detection payload fields are frozen after creation. Lifecycle fields (`lifecycle_state`, `triage`, `remediation`, `verification`, `lifecycle_log`, `updated`) may be modified as the signal progresses through its lifecycle. See knowledge-store.md Section 10 for the full mutability boundary specification.

---

## 11. Integration Points

### 11.1 Knowledge Store Integration

- Read from: `.planning/knowledge/index.md` (or `~/.gsd/knowledge/index.md` fallback) (signal listing)
- Read from: `.planning/knowledge/signals/{project}/` (or `~/.gsd/knowledge/signals/{project}/` fallback) (signal details)
- Lesson files deprecated -- lesson candidates documented in reflection report only
- Execute: `~/.gsd/bin/kb-rebuild-index.sh` (after writes)

### 11.2 Phase Artifact Integration

- Read from: `.planning/phases/{phase}/` directory
- Files: `*-PLAN.md`, `*-SUMMARY.md`, `*-VERIFICATION.md`
- Extract: Task counts, file lists, deviations, issues

### 11.3 Configuration Integration

- Read from: `.planning/config.json`
- Fields: `mode` (yolo/interactive), `depth`, cross-project settings

---

## 12. Reflect-to-Spike Pipeline (REFLECT-08)

Patterns that cannot be resolved through analysis alone are formatted as spike candidates for investigation via `/gsd:spike`.

### 12.1 Spike Candidate Triggers

A pattern becomes a spike candidate when any of these conditions is met:

| Trigger | Condition | Why a Spike |
|---------|-----------|-------------|
| Investigate triage | `triage.decision = "investigate"` | Pattern exists but root cause is unclear |
| Low confidence after counter-evidence | Adjusted confidence = `low` after counter-evidence seeking (Section 2.5) | Uncertain whether the pattern is real |
| Marginal score | Weighted score below threshold but within 20% of threshold | Borderline pattern that needs more data to confirm or reject |

**Marginal score calculation:**
```
threshold = { critical: 3.0, notable: 4.0, minor: 5.0 }[max_severity]
marginal_threshold = threshold * 0.8

# Pattern is a spike candidate if:
marginal_threshold <= weighted_score < threshold
```

### 12.2 Spike Candidate Output Format

```markdown
### Spike Candidate: {pattern-name}

**Trigger:** {investigate triage | low-confidence pattern | marginal score}
**Question:** {framed as a testable hypothesis}
**Why a spike:** {why analysis alone is insufficient}
**Suggested experiment:** {what to test}
**Related signals:** {signal IDs}
```

**Example:**
```markdown
### Spike Candidate: Context bloat in signal workflow

**Trigger:** marginal score (3.0 weighted, threshold 4.0 for notable, margin 3.2)
**Question:** Does progressive disclosure (index-first, detail-on-demand) reduce signal workflow context usage below 15%?
**Suggested experiment:** Implement index-first approach in signal collector, measure context usage across 5 plan executions, compare against current baseline.
**Related signals:** sig-2026-02-11-signal-workflow-context-bloat, sig-2026-02-18-signal-workflow-context-bloat, sig-2026-02-11-agent-inline-research-context-bloat
```

### 12.3 Spike vs Lesson Distinction

| Root Cause Known? | Actionable? | Output |
|-------------------|-------------|--------|
| Yes | Yes | Lesson (distill into knowledge base) |
| Yes | No (needs structural change) | Spike candidate with architectural question |
| No | N/A | Spike candidate with diagnostic question |

**Key principle:** If the root cause is known and actionable, create a lesson. If the root cause is unclear and needs investigation, create a spike candidate. The reflector does NOT create spike files -- it only identifies candidates.

### 12.4 Integration

- Spike candidates appear in the reflection report under a dedicated "Spike Candidates" section
- Spike candidates can be fed into `/gsd:spike` for investigation
- The reflector does NOT create spike files -- it only identifies and formats candidates
- After a spike is completed, its findings may produce new lessons or invalidate the original pattern

---

*Reference version: 1.2.0*
*Created: 2026-02-05*
*Updated: 2026-02-28*
*Phase: 04-reflection-engine, 31-signal-schema-foundation, 33-enhanced-reflector*
