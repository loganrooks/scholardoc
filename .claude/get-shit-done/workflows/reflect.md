<purpose>

Analyze accumulated signals from the knowledge base, detect recurring patterns using severity-weighted thresholds, distill qualifying patterns into actionable lessons, and optionally run phase-end or semantic drift analysis. This workflow closes the self-improvement loop: signals become patterns become lessons that prevent future mistakes.

</purpose>

<core_principle>

Reflection is retrospective analysis. It reads signals, phase artifacts, and KB state without modifying execution behavior. The workflow validates prerequisites, delegates analysis to the reflector agent, and presents results with appropriate confirmation based on autonomy mode.

</core_principle>

<required_reading>

Read these references for pattern detection rules and distillation criteria:
- get-shit-done/references/reflection-patterns.md
- .claude/agents/knowledge-store.md

Read STATE.md before any operation to load project context.
Read config.json for mode and depth settings.

</required_reading>

<trigger_modes>

1. **Explicit command:** `/gsd:reflect` or `/gsd:reflect {phase}`
2. **Phase-end:** `/gsd:reflect --phase {N}` for specific phase reflection
3. **Cross-project:** `/gsd:reflect --all` for cross-project pattern detection
4. **Milestone:** Called from milestone completion workflow (optional)

</trigger_modes>

<process>

<step name="parse_arguments">

Parse arguments from the command invocation:

```bash
# Default values
SCOPE="project"
PHASE=""
PATTERNS_ONLY=false
DRIFT_CHECK=false

# Parse arguments
for arg in "$@"; do
  case "$arg" in
    --all)
      SCOPE="all"
      ;;
    --phase)
      # Next arg will be phase number
      EXPECT_PHASE=true
      ;;
    --patterns-only)
      PATTERNS_ONLY=true
      ;;
    --drift|--drift-check)
      DRIFT_CHECK=true
      ;;
    [0-9]*)
      if [ "$EXPECT_PHASE" = true ]; then
        PHASE="$arg"
        EXPECT_PHASE=false
      else
        # Bare number = phase argument
        PHASE="$arg"
      fi
      ;;
  esac
done
```

**Argument meanings:**
- `--all`: Cross-project scope (scan all projects in KB)
- `{phase}` or `--phase {N}`: Include phase-end reflection for specific phase
- `--patterns-only`: Skip lesson distillation, report patterns only
- `--drift` or `--drift-check`: Include semantic drift analysis

</step>

<step name="load_configuration">

Read planning configuration:

```bash
# Load config
MODE=$(cat .planning/config.json 2>/dev/null | grep -o '"mode"[[:space:]]*:[[:space:]]*"[^"]*"' | grep -o '"[^"]*"$' | tr -d '"' || echo "interactive")
DEPTH=$(cat .planning/config.json 2>/dev/null | grep -o '"depth"[[:space:]]*:[[:space:]]*"[^"]*"' | grep -o '"[^"]*"$' | tr -d '"' || echo "standard")
COMMIT_PLANNING_DOCS=$(cat .planning/config.json 2>/dev/null | grep -o '"commit_docs"[[:space:]]*:[[:space:]]*[^,}]*' | grep -o 'true\|false' || echo "true")
git check-ignore -q .planning 2>/dev/null && COMMIT_PLANNING_DOCS=false

PROJECT_NAME=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')
```

**Config integration:**
- `mode: yolo` - Auto-approve HIGH confidence lessons
- `mode: interactive` - Present all lesson candidates for confirmation
- `depth: quick` - Check only current project, skip drift check
- `depth: standard` - Current project with drift check
- `depth: comprehensive` - Cross-project with full drift analysis

**Depth auto-adjustments:**
If `DEPTH="comprehensive"` and `SCOPE="project"`, auto-enable `--drift-check` if not already set.
If `SCOPE="all"`, depth is effectively comprehensive regardless of setting.

</step>

<step name="verify_kb_exists">

Check that the knowledge base exists and has content:

```bash
# KB path resolution -- project-local primary, user-global fallback
if [ -d ".planning/knowledge" ]; then
  KB_DIR=".planning/knowledge"
else
  KB_DIR="$HOME/.gsd/knowledge"
fi
KB_INDEX="$KB_DIR/index.md"

if [ ! -f "$KB_INDEX" ]; then
  echo "No knowledge base found at $KB_INDEX"
  echo "Run /gsd:collect-signals first to create the KB and collect signals."
  exit 0
fi

# Count signals in index
SIGNAL_COUNT=$(grep -c "^| sig-" "$KB_INDEX" 2>/dev/null || echo 0)
echo "KB index found with $SIGNAL_COUNT signals"
```

**Empty state handling:**
- No KB: Report "No knowledge base found. Run /gsd:collect-signals first."
- KB exists but no signals: Report "No signals found in knowledge base. Nothing to reflect on."

</step>

<step name="show_lifecycle_dashboard">

Generate and display a lifecycle dashboard at the START of the reflection report. This gives the user immediate context about the KB state before analysis begins.

```bash
# Count signals by lifecycle state from index
# SIG-format signals (ID starts with SIG-) are counted separately as Legacy
UNTRIAGED=0
TRIAGED=0
REMEDIATED=0
VERIFIED=0
INVALIDATED=0
LEGACY=0
WITH_EVIDENCE=0
HIGH_CONFIDENCE=0
TOTAL=0

while IFS='|' read -r _ id lifecycle severity tags _rest; do
  id=$(echo "$id" | tr -d ' ')
  lifecycle=$(echo "$lifecycle" | tr -d ' ')

  # Skip non-signal rows
  [[ "$id" =~ ^sig-|^SIG- ]] || continue

  TOTAL=$((TOTAL + 1))

  # SIG-format signals go to Legacy row
  if [[ "$id" =~ ^SIG- ]]; then
    LEGACY=$((LEGACY + 1))
    continue
  fi

  # Standard-format signals counted by lifecycle_state
  case "$lifecycle" in
    triaged) TRIAGED=$((TRIAGED + 1)) ;;
    remediated) REMEDIATED=$((REMEDIATED + 1)) ;;
    verified) VERIFIED=$((VERIFIED + 1)) ;;
    invalidated) INVALIDATED=$((INVALIDATED + 1)) ;;
    *) UNTRIAGED=$((UNTRIAGED + 1)) ;;  # detected, missing, or empty
  esac
done < "$KB_INDEX"

# Count signals with evidence and high confidence from signal files
for signal_file in "$KB_DIR/signals/$PROJECT_NAME"/*.md; do
  [ -f "$signal_file" ] || continue
  grep -q "^evidence:" "$signal_file" && WITH_EVIDENCE=$((WITH_EVIDENCE + 1))
  grep -q "^confidence: high" "$signal_file" && HIGH_CONFIDENCE=$((HIGH_CONFIDENCE + 1))
done
```

**Output the dashboard:**

```markdown
## Lifecycle Dashboard

| State | Count | Percentage |
|-------|-------|-----------|
| Untriaged (detected) | {UNTRIAGED} | {pct}% |
| Triaged | {TRIAGED} | {pct}% |
| Remediated | {REMEDIATED} | {pct}% |
| Verified | {VERIFIED} | {pct}% |
| Invalidated | {INVALIDATED} | {pct}% |
| Legacy (read-only) | {LEGACY} | {pct}% |
| **Total** | **{TOTAL}** | **100%** |

Signals with evidence: {WITH_EVIDENCE}/{TOTAL} ({pct}%)
High-confidence signals: {HIGH_CONFIDENCE} ({pct}%)
```

**Legacy row explanation:** SIG-format signals (ID starts with `SIG-`) predate the standard schema and cannot be triaged or modified. They are counted separately to avoid inflating the "Untriaged" count as the project matures. They are still included in pattern detection as read-only data.

The dashboard is informational -- it runs before analysis and does not affect subsequent steps.

</step>

<step name="prepare_context">

Read artifact contents to pass to the agent. The `@` syntax does not work across Task() boundaries.

```bash
# Read index.md content
INDEX_CONTENT=$(cat "$KB_INDEX")

# If phase-end reflection, read phase artifacts
if [ -n "$PHASE" ]; then
  PADDED_PHASE=$(printf "%02d" ${PHASE} 2>/dev/null || echo "${PHASE}")
  PHASE_DIR=$(ls -d .planning/phases/${PADDED_PHASE}-* .planning/phases/${PHASE}-* 2>/dev/null | head -1)

  if [ -n "$PHASE_DIR" ]; then
    PLAN_CONTENT=""
    SUMMARY_CONTENT=""
    for plan in "$PHASE_DIR"/*-PLAN.md; do
      [ -f "$plan" ] && PLAN_CONTENT="$PLAN_CONTENT\n--- FILE: $plan ---\n$(cat "$plan")"
    done
    for summary in "$PHASE_DIR"/*-SUMMARY.md; do
      [ -f "$summary" ] && SUMMARY_CONTENT="$SUMMARY_CONTENT\n--- FILE: $summary ---\n$(cat "$summary")"
    done
    VERIFICATION_CONTENT=$(cat "$PHASE_DIR"/*-VERIFICATION.md 2>/dev/null || echo "")
  fi
fi

# Read config for agent
CONFIG_CONTENT=$(cat .planning/config.json 2>/dev/null)
```

For cross-project scope, also read signal files from all project directories:

```bash
if [ "$SCOPE" = "all" ]; then
  SIGNAL_FILES_CONTENT=""
  for project_dir in "$KB_DIR/signals"/*/; do
    [ -d "$project_dir" ] || continue
    for signal_file in "$project_dir"/*.md; do
      [ -f "$signal_file" ] && SIGNAL_FILES_CONTENT="$SIGNAL_FILES_CONTENT\n--- FILE: $signal_file ---\n$(cat "$signal_file")"
    done
  done
fi
```

</step>

<step name="spawn_reflector">

Delegate to the `gsd-reflector` agent with prepared context:

```
Task(
  prompt="Run reflection analysis.

  Scope: {SCOPE}
  Project: {PROJECT_NAME}
  Phase: {PHASE or 'none'}
  Patterns only: {PATTERNS_ONLY}
  Drift check: {DRIFT_CHECK}
  Mode: {MODE}

  Knowledge Base Index:
  {INDEX_CONTENT}

  {If phase specified:}
  Plan artifacts:
  {PLAN_CONTENT}

  Summary artifacts:
  {SUMMARY_CONTENT}

  Verification:
  {VERIFICATION_CONTENT}

  {If scope is all:}
  Signal files:
  {SIGNAL_FILES_CONTENT}

  Config:
  {CONFIG_CONTENT}

  Follow your execution_flow to:
  1. Load and filter signals by lifecycle_state:
     - detected (or missing lifecycle_state for non-SIG signals): Full analysis candidate
     - triaged: Include in pattern detection and lessons, skip triage proposals
     - remediated: Lower weight in pattern detection, track for verification
     - verified: Exclude from active patterns, include in positive pattern analysis
     - invalidated: Exclude entirely
     - SIG-format (ID starts with SIG-): Read-only, include in patterns but do not modify
  2. Detect patterns using confidence-weighted thresholds (not raw counts)
  3. Perform phase-end reflection if phase specified
  4. Generate triage proposals for untriaged signal clusters with:
     - Cluster name, signal list, recommended decision, rationale, priority
     - Decision types: address, dismiss, defer, investigate
  5. Generate remediation suggestions for clusters with decision: address
  6. Identify spike candidates (low-confidence patterns or investigate decisions)
  7. Distill lessons with evidence_snapshots (unless patterns-only)
  8. Check semantic drift (if requested)
  9. Return the structured Reflection Report

  Return the structured Reflection Report when complete.",
  subagent_type="gsd-reflector"
)
```

The agent performs all analysis logic and returns a structured Reflection Report.

</step>

<step name="receive_report">

The reflector agent returns a structured report containing:
- Patterns detected (with type, severity, confidence, weighted score)
- Triage proposals (for untriaged signal clusters)
- Remediation suggestions (for clusters with decision: address)
- Spike candidates (low-confidence patterns or investigate decisions)
- Phase deviations (if phase-end reflection)
- Lesson candidates (with evidence, evidence_snapshots, and scope)
- Drift assessment (if drift check)

Parse the report for triage handling, results presentation, and lesson handling.

</step>

<step name="handle_triage_proposals">

Handle triage proposals from the reflector agent. Triage modifies existing signal files (updating lifecycle_state and triage fields), so it requires appropriate confirmation based on autonomy mode.

**Per-run triage cap:** A maximum of 10 signals may be triaged per reflect run. If more than 10 signals would be triaged across all approved proposals, present the highest-priority proposals first and queue the remainder with a note:

```
Triage cap reached (10 signals). Run /gsd:reflect again to continue triaging remaining clusters.
```

This prevents the first-run scenario where 30+ signal files are modified in a single session, producing an unwieldy git commit and risking context budget exhaustion in the reflector agent.

**Phase 33 triage constraint reminder:** When triaging critical signals that lack `lifecycle_state`, `evidence.supporting` MUST be added first. Once `lifecycle_state` is present, the backward_compat exemption no longer applies and evidence becomes a hard requirement for critical signals. Reference knowledge-store.md Section 4.2.

<if mode="interactive">

Present each triage proposal for user confirmation:

```markdown
### Triage Proposal: {cluster-name}

**Signals:** {N} signals
{list of signal IDs}
**Recommended decision:** {address|dismiss|defer|investigate}
**Rationale:** {why this cluster should be triaged this way}
**Priority:** {critical|high|medium|low}

Approve this triage? (approve / reject / modify)
```

For each response:
- **approve**: Instruct reflector to write triage fields to each signal in the cluster
- **reject**: Skip this cluster (signals remain at detected)
- **modify**: Allow user to change decision and/or priority before applying

Track approved triage count against per-run cap of 10 signals.

</if>

<if mode="yolo">

**YOLO mode triage has higher blast radius than lessons** -- it modifies existing files, not just creating new ones. Auto-approve is limited to bound the blast radius:

- **Auto-approve `address` and `dismiss` decisions ONLY** (these have clear intent and bounded impact)
- **Present `defer` decisions for user confirmation** (deferral is a judgment call about timing)
- **Present `investigate` decisions for user confirmation** (spike candidates need human judgment on resource allocation)

Report all auto-approved decisions in the summary:
```markdown
### Auto-Approved Triage (YOLO Mode)

| Cluster | Decision | Signals | Priority |
|---------|----------|---------|----------|
| {name}  | address  | {N}     | {priority} |
| {name}  | dismiss  | {N}     | {priority} |

**Presented for confirmation:**
- {cluster}: defer ({N} signals) -- deferral requires human judgment
- {cluster}: investigate ({N} signals) -- spike candidates need human judgment
```

**Design rationale:** Unlike lesson auto-approve (creates new files), triage auto-approve modifies existing signal files. Limiting auto-approve to `address` and `dismiss` decisions bounds the blast radius of YOLO mode for triage operations.

</if>

**When triage is approved:** The workflow instructs the reflector agent to write triage fields to each signal in the cluster. The workflow itself does NOT write files -- the reflector does. The reflector must:
1. Read the complete signal file
2. Modify ONLY mutable fields (lifecycle_state, triage, lifecycle_log, updated)
3. Keep ALL frozen detection payload fields unchanged
4. Validate after writing with `frontmatter validate --schema signal`

</step>

<step name="present_results">

Display user-friendly results:

```
--------------------------------------------------------------
 GSD | REFLECTION COMPLETE
--------------------------------------------------------------

**Scope:** {project / cross-project}
**Project:** {PROJECT_NAME}
**Signals analyzed:** {count}
**Patterns detected:** {count}

### Patterns Found

| # | Pattern | Type | Occurrences | Severity | Confidence |
|---|---------|------|-------------|----------|------------|
| 1 | {name}  | {type} | {count}   | {severity} | {confidence} |

{For each pattern: brief root cause hypothesis}

{If phase-end:}
### Phase {N} Deviations

| Category | Planned | Actual | Delta |
|----------|---------|--------|-------|
| Tasks    | {N}     | {N}    | {+/-N}|

Overall alignment: {HIGH|MEDIUM|LOW}

{If drift check:}
### Semantic Drift Assessment

Status: {STABLE|DRIFTING|CONCERNING}

| Metric | Baseline | Recent | Change |
|--------|----------|--------|--------|
| {metric} | {value} | {value} | {%} |

### Remediation Suggestions

{For each triaged cluster with decision: address}

#### {cluster-name}

**Signals:** {signal IDs}
**Suggested approach:** {what to do to address the root cause}
**Suggested plan scope:** {which phase/plan could address this}
**Priority:** {from triage.priority}

{End for each}

> Triaged signals with `decision: address` will be picked up by the planner during `/gsd:plan-phase`.
> Plans can declare `resolves_signals` to automatically move signals to "remediated" on completion.

--------------------------------------------------------------
```

</step>

<step name="handle_lesson_candidates">

**DEPRECATED:** Lesson file writing is no longer performed. Lesson candidates are documented in the reflection report only (output by the reflector agent in its report). The workflow displays them as part of the report but does not write lesson files.

Display lesson candidates from the report for informational purposes only:

```
### Lesson Candidates (Documented in Report Only)

{lesson candidates from reflector report, if any}

Note: Lessons are no longer written as individual KB files. Candidates are preserved in the reflection report at {REPORT_FILE}.
```

</step>

<step name="report_completion">

Display final completion summary:

```
--------------------------------------------------------------
 GSD | REFLECTION SUMMARY
--------------------------------------------------------------

**Scope:** {project / cross-project}
**Signals analyzed:** {count}
**Patterns detected:** {count}
**Lessons created:** {count}
**Signals triaged:** {count}
**Remediation suggestions:** {count}

### Lifecycle Dashboard Summary

| State | Count |
|-------|-------|
| Untriaged | {N} |
| Triaged | {N} (including {new} from this run) |
| Legacy (read-only) | {N} |

{If phase-end:}
**Phase {N} alignment:** {HIGH|MEDIUM|LOW}

{If drift check:}
**Drift status:** {STABLE|DRIFTING|CONCERNING}

### Patterns Found

| Pattern | Confidence | Action |
|---------|------------|--------|
| {name}  | {level}    | Lesson created / Triaged / Logged for reference |

### Triage Results

| Cluster | Decision | Signals | Status |
|---------|----------|---------|--------|
| {name}  | {decision} | {N}   | Approved / Rejected / Pending |

### Lessons Created

| File | Category | Insight |
|------|----------|---------|
| {path} | {category} | {brief} |

### Remediation Suggestions

| Cluster | Priority | Suggested Scope |
|---------|----------|-----------------|
| {name}  | {priority} | {phase/plan} |

--------------------------------------------------------------

Next: Lessons will surface via /gsd:kb-search during future planning.
Triaged signals with decision "address" will surface during /gsd:plan-phase for resolves_signals linkage.

--------------------------------------------------------------
```

</step>

<step name="persist_report">

Write the full reflection report to a persistent file in the knowledge base. This preserves the analytical context (patterns, scores, triage decisions, spike candidates) that would otherwise be lost when the session ends.

```bash
REPORT_DIR="$KB_DIR/reflections/$PROJECT_NAME"
mkdir -p "$REPORT_DIR"
REPORT_FILE="$REPORT_DIR/reflect-$(date +%Y-%m-%d).md"
```

**Report content:** Write the complete reflection output as a markdown file, including:

```markdown
---
project: {PROJECT_NAME}
date: {YYYY-MM-DD}
scope: {SCOPE}
signals_analyzed: {count}
patterns_detected: {count}
lessons_created: {count}
signals_triaged: {count}
spike_candidates: {count}
drift_status: {STABLE|DRIFTING|CONCERNING|N/A}
---

# Reflection Report: {PROJECT_NAME}

Date: {YYYY-MM-DD}
Scope: {SCOPE}

## Lifecycle Dashboard

{dashboard table from show_lifecycle_dashboard step}

## Patterns Detected

{patterns table and root cause hypotheses from present_results step}

## Triage Results

{triage proposals table with decisions and status from handle_triage_proposals step}

## Lessons Created

{lessons table from handle_lesson_creation step}

## Remediation Suggestions

{remediation suggestions from present_results step}

## Spike Candidates

{spike candidates from reflector output, if any}

## Semantic Drift

{drift assessment if drift check was run, otherwise "Not checked"}
```

**Same-day overwrites:** If a report for today already exists, overwrite it. Only the latest run per day is preserved.

**Report is informational:** The report file is a historical record. It is NOT indexed in `index.md` (reflections are not KB entries). Other workflows may read it for context (e.g., planning could reference recent reflection findings).

</step>

<step name="commit_report">

If `COMMIT_PLANNING_DOCS` is true, commit the reflection report:

```bash
if [ "$COMMIT_PLANNING_DOCS" = "true" ]; then
  # Stage reflection report (always written)
  git add "$REPORT_FILE" 2>/dev/null

  git commit -m "docs(reflect): reflection report (${PATTERNS_DETECTED} patterns)

- Scope: ${SCOPE}
- Signals analyzed: ${SIGNAL_COUNT}
- Report: ${REPORT_FILE}"
fi
```

Skip if `COMMIT_PLANNING_DOCS` is false.

</step>

</process>

<empty_state_handling>

**No KB:**
```
No knowledge base found (checked .planning/knowledge/index.md and ~/.gsd/knowledge/index.md)
Run /gsd:collect-signals first to create the KB and collect signals.
```

**KB exists but no signals:**
```
No signals found in knowledge base. Nothing to reflect on.

Signals are collected after phase execution via /gsd:collect-signals.
```

**Signals but no patterns:**
```
{N} signals analyzed but no recurring patterns detected.

Pattern detection requires:
- Critical/high severity: 2+ occurrences
- Medium severity: 4+ occurrences
- Low severity: 5+ occurrences

Consider accumulating more signals or check thresholds in reflection-patterns.md.
```

**Patterns but no lesson candidates:**
```
{N} patterns found but none meet distillation criteria.

Lesson distillation requires:
- Pattern meets threshold (confirmed)
- Consistent root cause across signals
- Actionable recommendation possible

Patterns are logged for future reference.
```

</empty_state_handling>

<error_handling>

**No phase directory (when phase specified):** Report error with available phases.
**Agent failure:** Report what was attempted and the error.
**Write failure:** Report which lesson failed to write and continue with others.
**Index rebuild failure:** Report error but don't fail the workflow.

</error_handling>
