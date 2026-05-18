<purpose>
Execute all plans in a phase using wave-based parallel execution. Orchestrator stays lean — delegates plan execution to subagents.
</purpose>

<core_principle>
Orchestrator coordinates, not executes. Each subagent loads the full execute-plan context. Orchestrator: discover plans → analyze deps → group waves → spawn agents → handle checkpoints → collect results.
</core_principle>

<required_reading>
Read STATE.md before any operation to load project context.
</required_reading>

<process>

<step name="initialize" priority="first">
Load all context in one call:

```bash
INIT=$(node ./.claude/get-shit-done/bin/gsd-tools.js init execute-phase "${PHASE_ARG}")
```

Parse JSON for: `executor_model`, `verifier_model`, `commit_docs`, `parallelization`, `branching_strategy`, `branch_name`, `phase_found`, `phase_dir`, `phase_number`, `phase_name`, `phase_slug`, `plans`, `incomplete_plans`, `plan_count`, `incomplete_count`, `state_exists`, `roadmap_exists`.

**If `phase_found` is false:** Error — phase directory not found.
**If `plan_count` is 0:** Error — no plans found in phase.
**If `state_exists` is false but `.planning/` exists:** Offer reconstruct or continue.

When `parallelization` is false, plans within a wave execute sequentially.
</step>

<step name="handle_branching">
Check `branching_strategy` from init:

**"none":** Skip, continue on current branch.

**"phase" or "milestone":** Use pre-computed `branch_name` from init:
```bash
git checkout -b "$BRANCH_NAME" 2>/dev/null || git checkout "$BRANCH_NAME"
```

All subsequent commits go to this branch. User handles merging.
</step>

<step name="validate_phase">
From init JSON: `phase_dir`, `plan_count`, `incomplete_count`.

Report: "Found {plan_count} plans in {phase_dir} ({incomplete_count} incomplete)"
</step>

<!-- Capability gap signals are logged as trace severity during degraded execution.
     They appear in signal collection reports but are NOT persisted to the KB.
     See signal-detection.md Section 12 for the full specification. -->

<capability_adaptation>
## Runtime Capability Adaptation

Before executing waves, check the runtime capability matrix
(read get-shit-done/references/capability-matrix.md if not already loaded).

<capability_check name="parallel_execution">
Check the runtime capability matrix (get-shit-done/references/capability-matrix.md):

If has_capability("task_tool"):
  Execute waves as designed -- spawn gsd-executor via Task() for each plan in the wave.
  Track agent progress, collect results, proceed to next wave.

Else:
  Note to user (first occurrence only): "Note: Running sequentially -- this runtime doesn't support parallel agents."

  Log capability gap signal (trace severity, not persisted to KB):
  - signal_type: capability-gap
  - severity: trace
  - runtime: {detected from path prefix in this workflow file}
  - model: {self-reported model name}
  - description: "task_tool capability unavailable. Degraded from parallel wave execution to sequential plan execution."

  This signal appears in the signal collection report when /gsd:collect-signals
  runs for this phase. It is NOT written to the KB (trace signals are report-only
  per signal-detection.md Section 6).

  For each plan in execution order:
  1. Read the plan file directly
  2. Execute each task in sequence (follow execute-plan.md flow)
  3. Create SUMMARY.md after all tasks complete
  4. Commit task artifacts
  5. Proceed to next plan
  Skip: wave grouping, parallel spawning, agent tracking (init_agent_tracking)
</capability_check>

<capability_check name="hooks_support">
If has_capability("hooks"):
  Configure hooks as normal (update check on SessionStart, etc.).

Else:
  Skip hook configuration.
  Note (first occurrence): "Update checks will run on GSD command invocation instead of session start."

  Log capability gap signal (trace severity, not persisted to KB):
  - signal_type: capability-gap
  - severity: trace
  - runtime: {detected from path prefix}
  - model: {self-reported model name}
  - description: "hooks capability unavailable. Update checks deferred to command invocation."
</capability_check>

</capability_adaptation>

<step name="discover_and_group_plans">
Load plan inventory with wave grouping in one call:

```bash
PLAN_INDEX=$(node ./.claude/get-shit-done/bin/gsd-tools.js phase-plan-index "${PHASE_NUMBER}")
```

Parse JSON for: `phase`, `plans[]` (each with `id`, `wave`, `autonomous`, `objective`, `files_modified`, `task_count`, `has_summary`), `waves` (map of wave number → plan IDs), `incomplete`, `has_checkpoints`.

**Filtering:** Skip plans where `has_summary: true`. If `--gaps-only`: also skip non-gap_closure plans. If all filtered: "No matching incomplete plans" → exit.

Report:
```
## Execution Plan

**Phase {X}: {Name}** — {total_plans} plans across {wave_count} waves

| Wave | Plans | What it builds |
|------|-------|----------------|
| 1 | 01-01, 01-02 | {from plan objectives, 3-8 words} |
| 2 | 01-03 | ... |
```
</step>

<step name="execute_waves">
Execute each wave in sequence. Within a wave: parallel if `PARALLELIZATION=true`, sequential if `false`.

**For each wave:**

1. **Describe what's being built (BEFORE spawning):**

   Read each plan's `<objective>`. Extract what's being built and why.

   ```
   ---
   ## Wave {N}

   **{Plan ID}: {Plan Name}**
   {2-3 sentences: what this builds, technical approach, why it matters}

   Spawning {count} agent(s)...
   ---
   ```

   - Bad: "Executing terrain generation plan"
   - Good: "Procedural terrain generator using Perlin noise — creates height maps, biome zones, and collision meshes. Required before vehicle physics can interact with ground."

2. **Spawn executor agents:**

   Pass paths only — executors read files themselves with their fresh 200k context.
   This keeps orchestrator context lean (~10-15%).

   ```
   Task(
     subagent_type="gsd-executor",
     model="{executor_model}",
     prompt="
       <objective>
       Execute plan {plan_number} of phase {phase_number}-{phase_name}.
       Commit each task atomically. Create SUMMARY.md. Update STATE.md.
       </objective>

       <execution_context>
       @./.claude/get-shit-done/workflows/execute-plan.md
       @./.claude/get-shit-done/templates/summary-standard.md
       @./.claude/get-shit-done/references/checkpoints.md
       @./.claude/get-shit-done/references/tdd.md
       </execution_context>

       <files_to_read>
       Read these files at execution start using the Read tool:
       - Plan: {phase_dir}/{plan_file}
       - State: .planning/STATE.md
       - Config: .planning/config.json (if exists)
       </files_to_read>

       <success_criteria>
       - [ ] All tasks executed
       - [ ] Each task committed individually
       - [ ] SUMMARY.md created in plan directory
       - [ ] STATE.md updated with position and decisions
       </success_criteria>
     "
   )
   ```

3. **Wait for all agents in wave to complete.**

4. **Report completion — spot-check claims first:**

   For each SUMMARY.md:
   - Verify first 2 files from `key-files.created` exist on disk
   - Check `git log --oneline --all --grep="{phase}-{plan}"` returns ≥1 commit
   - Check for `## Self-Check: FAILED` marker

   If ANY spot-check fails: report which plan failed, route to failure handler — ask "Retry plan?" or "Continue with remaining waves?"

   If pass:
   ```
   ---
   ## Wave {N} Complete

   **{Plan ID}: {Plan Name}**
   {What was built — from SUMMARY.md}
   {Notable deviations, if any}

   {If more waves: what this enables for next wave}
   ---
   ```

   - Bad: "Wave 2 complete. Proceeding to Wave 3."
   - Good: "Terrain system complete — 3 biome types, height-based texturing, physics collision meshes. Vehicle physics (Wave 3) can now reference ground surfaces."

5. **Handle failures:**

   **Known Claude Code bug (classifyHandoffIfNeeded):** If an agent reports "failed" with error containing `classifyHandoffIfNeeded is not defined`, this is a Claude Code runtime bug — not a GSD or agent issue. The error fires in the completion handler AFTER all tool calls finish. In this case: run the same spot-checks as step 4 (SUMMARY.md exists, git commits present, no Self-Check: FAILED). If spot-checks PASS → treat as **successful**. If spot-checks FAIL → treat as real failure below.

   For real failures: report which plan failed → ask "Continue?" or "Stop?" → if continue, dependent plans may also fail. If stop, partial completion report.

6. **Execute checkpoint plans between waves** — see `<checkpoint_handling>`.

7. **Proceed to next wave.**
</step>

<step name="checkpoint_handling">
Plans with `autonomous: false` require user interaction.

**Flow:**

1. Spawn agent for checkpoint plan
2. Agent runs until checkpoint task or auth gate → returns structured state
3. Agent return includes: completed tasks table, current task + blocker, checkpoint type/details, what's awaited
4. **Present to user:**
   ```
   ## Checkpoint: [Type]

   **Plan:** 03-03 Dashboard Layout
   **Progress:** 2/3 tasks complete

   [Checkpoint Details from agent return]
   [Awaiting section from agent return]
   ```
5. User responds: "approved"/"done" | issue description | decision selection
6. **Spawn continuation agent (NOT resume)** using continuation-prompt.md template:
   - `{completed_tasks_table}`: From checkpoint return
   - `{resume_task_number}` + `{resume_task_name}`: Current task
   - `{user_response}`: What user provided
   - `{resume_instructions}`: Based on checkpoint type
7. Continuation agent verifies previous commits, continues from resume point
8. Repeat until plan completes or user stops

**Why fresh agent, not resume:** Resume relies on internal serialization that breaks with parallel tool calls. Fresh agents with explicit state are more reliable.

**Checkpoints in parallel waves:** Agent pauses and returns while other parallel agents may complete. Present checkpoint, spawn continuation, wait for all before next wave.
</step>

<step name="aggregate_results">
After all waves:

```markdown
## Phase {X}: {Name} Execution Complete

**Waves:** {N} | **Plans:** {M}/{total} complete

| Wave | Plans | Status |
|------|-------|--------|
| 1 | plan-01, plan-02 | ✓ Complete |
| CP | plan-03 | ✓ Verified |
| 2 | plan-04 | ✓ Complete |

### Plan Details
1. **03-01**: [one-liner from SUMMARY.md]
2. **03-02**: [one-liner from SUMMARY.md]

### Issues Encountered
[Aggregate from SUMMARYs, or "None"]
```
</step>

<step name="cleanup_handoffs">
Clean up any .continue-here files from the completed phase:

```bash
rm -f "${PHASE_DIR}/.continue-here"*.md
```

Phase execution is complete -- any handoff files are now stale.
</step>

<step name="verify_phase_goal">
Verify phase achieved its GOAL, not just completed tasks.

```
Task(
  prompt="Verify phase {phase_number} goal achievement.
Phase directory: {phase_dir}
Phase goal: {goal from ROADMAP.md}
Check must_haves against actual codebase. Create VERIFICATION.md.",
  subagent_type="gsd-verifier",
  model="{verifier_model}"
)
```

Read status:
```bash
grep "^status:" "$PHASE_DIR"/*-VERIFICATION.md | cut -d: -f2 | tr -d ' '
```

| Status | Action |
|--------|--------|
| `passed` | → update_roadmap |
| `human_needed` | Present items for human testing, get approval or feedback |
| `gaps_found` | Present gap summary, offer `/gsd:plan-phase {phase} --gaps` |

**If human_needed:**
```
## ✓ Phase {X}: {Name} — Human Verification Required

All automated checks passed. {N} items need human testing:

{From VERIFICATION.md human_verification section}

"approved" → continue | Report issues → gap closure
```

**If gaps_found:**
```
## ⚠ Phase {X}: {Name} — Gaps Found

**Score:** {N}/{M} must-haves verified
**Report:** {phase_dir}/{phase}-VERIFICATION.md

### What's Missing
{Gap summaries from VERIFICATION.md}

---
## ▶ Next Up

`/gsd:plan-phase {X} --gaps`

<sub>`/clear` first → fresh context window</sub>

Also: `cat {phase_dir}/{phase}-VERIFICATION.md` — full report
Also: `/gsd:verify-work {X}` — manual testing first
```

Gap closure cycle: `/gsd:plan-phase {X} --gaps` reads VERIFICATION.md → creates gap plans with `gap_closure: true` → user runs `/gsd:execute-phase {X} --gaps-only` → verifier re-runs.
</step>

<step name="reconcile_signal_lifecycle">
Reconcile signal lifecycle states after successful verification. This step is best-effort -- failures do not block phase completion.

Only runs if verification passed (`passed` or `human_needed` that was approved).

```bash
# Reconcile signal lifecycle: update signals declared in resolves_signals
# from detected/triaged to remediated
bash ./.claude/get-shit-done/bin/reconcile-signal-lifecycle.sh "${PHASE_DIR}" 2>&1 || echo "Warning: Signal lifecycle reconciliation failed (non-blocking)"
```

This programmatic reconciliation replaces agent-instruction-based lifecycle transitions, which were unreliable in long execution sequences.
</step>

<!-- SIG-01, SIG-02, SIG-04, SIG-05: auto-collection postlude -->
<step name="auto_collect_signals">
Auto-collect signals after successful phase execution. This is a workflow postlude --
it runs as part of the orchestrator on all runtimes (Claude Code, OpenCode, Gemini CLI,
Codex CLI), not as a hook. Cross-runtime compatibility is inherent because all runtimes
read this workflow file.

Only runs if verification passed (`passed` or `human_needed` that was approved).

**1. Check reentrancy guard:**

```bash
LOCK_STATUS=$(node ./.claude/get-shit-done/bin/gsd-tools.js automation check-lock signal_collection --raw 2>/dev/null)
```

Parse `LOCK_STATUS`. If `locked: true` (and not stale): skip auto-collection silently.
This prevents feedback loops if signal collection is already running (SIG-03).

```bash
# Track the skip
node ./.claude/get-shit-done/bin/gsd-tools.js automation track-event signal_collection skip "reentrancy"
```

**2. Resolve automation level:**

```bash
LEVEL=$(node ./.claude/get-shit-done/bin/gsd-tools.js automation resolve-level signal_collection --context-pct {EST_CONTEXT_PCT} --raw 2>/dev/null)
```

Estimate context percentage using wave count as proxy:
- Default: `min(40 + (WAVES_COMPLETED * 10), 80)`
- 1-wave phase: ~50%, 2-wave: ~60%, 3-wave: ~70%, 4+: ~80%
- This is approximate but functional. A static value of 40 would make SIG-05
  deferral non-functional (40 < 60 threshold always). The wave-based proxy
  ensures multi-wave phases trigger deferral appropriately.
- See sig-2026-03-05-phase40-plan-gaps-pre-execution-review for analysis.

Parse `LEVEL.effective` to determine behavior.

**3. Branch on effective level:**

| Level | Name | Behavior |
|-------|------|----------|
| 0 | manual | Skip entirely. Track: `track-event signal_collection skip "level-0"` |
| 1 | nudge | Display nudge message and skip. Track: `track-event signal_collection skip "level-1"` |
| 2 | prompt | Ask user "Collect signals for phase {PHASE_NUMBER}? [y/n]". If yes, proceed. If no, track skip. |
| 3 | auto | Proceed to collection. |

**Nudge message (level 1 or context-deferred):**
```
Signal collection available for phase {PHASE_NUMBER}.
Run `/gsd:collect-signals {PHASE_NUMBER}` to collect signals.
```

**Context-deferred message (level 3 downgraded to 1 by resolve-level):**
If `LEVEL.reasons` contains "context_deferred":
```
Context usage high. Signal collection deferred.
Run `/gsd:collect-signals {PHASE_NUMBER}` in a fresh session.
```

**4. If proceeding (level 2 approved or level 3):**

Acquire the reentrancy lock:
```bash
LOCK=$(node ./.claude/get-shit-done/bin/gsd-tools.js automation lock signal_collection --source phase-completion --raw 2>/dev/null)
```

If `LOCK.locked` is true (another process acquired between check and lock -- race condition):
skip and track `track-event signal_collection skip "lock-race"`.

If lock acquired, invoke the collect-signals workflow for the current phase:

```
Follow the collect-signals.md workflow for phase {PADDED_PHASE}.
This workflow handles:
- Sensor discovery (auto-discovers gsd-*-sensor.md files including the CI sensor)
- Parallel sensor spawning (SIG-02: CI sensor runs alongside artifact and git sensors)
- Output collection and synthesis
- KB persistence and index rebuild
```

The CI sensor inclusion (SIG-02) is automatic -- the collect-signals workflow uses
auto-discovery, so any sensor agent spec matching `gsd-*-sensor.md` (including
`gsd-ci-sensor.md`) is discovered and spawned in parallel.

**5. Release lock, track event, and detect first-run:**

After collection completes (success or failure), release the lock first:
```bash
node ./.claude/get-shit-done/bin/gsd-tools.js automation unlock signal_collection --raw 2>/dev/null
```

On success, track the fire event and capture the returned stats:
```bash
FIRE_STATS=$(node ./.claude/get-shit-done/bin/gsd-tools.js automation track-event signal_collection fire --raw 2>/dev/null)
```

On failure, still release lock but track as skip:
```bash
node ./.claude/get-shit-done/bin/gsd-tools.js automation track-event signal_collection skip "collection-error" --raw 2>/dev/null
```

**6. First-run regime change detection:**

Parse `FIRE_STATS` from step 5 (the track-event fire response already contains the updated
stats). Check if `stats.fires` is 1.

IMPORTANT: Do NOT call `track-event fire` again here. Step 5 already incremented the
counter. Calling it again would double-fire (0->1->2), making the `fires === 1` check
always fail. See sig-2026-03-05-phase40-plan-gaps-pre-execution-review.

If `fires` is 1 (first fire): write a regime_change entry:
```bash
node ./.claude/get-shit-done/bin/gsd-tools.js automation regime-change "Auto-collection enabled" --impact "Signal count per phase expected to increase as automated detection catches issues previously missed" --prior "Manual /gsd:collect-signals invocation only" --raw 2>/dev/null
```

This step is best-effort -- failures do not block phase completion. If any command fails,
log a warning and continue to update_roadmap.
</step>

<step name="update_roadmap">
Mark phase complete in ROADMAP.md (date, status).

```bash
node ./.claude/get-shit-done/bin/gsd-tools.js commit "docs(phase-{X}): complete phase execution" --files .planning/ROADMAP.md .planning/STATE.md .planning/phases/{phase_dir}/*-VERIFICATION.md .planning/REQUIREMENTS.md
```
</step>

<step name="offer_next">

**If more phases:**
```
## Next Up

**Phase {X+1}: {Name}** — {Goal}

`/gsd:plan-phase {X+1}`

<sub>`/clear` first for fresh context</sub>
```

**If milestone complete:**
```
MILESTONE COMPLETE!

All {N} phases executed.

`/gsd:complete-milestone`
```
</step>

</process>

<context_efficiency>
Orchestrator: ~10-15% context. Subagents: fresh 200k each. No polling (Task blocks). No context bleed.
</context_efficiency>

<failure_handling>
- **classifyHandoffIfNeeded false failure:** Agent reports "failed" but error is `classifyHandoffIfNeeded is not defined` → Claude Code bug, not GSD. Spot-check (SUMMARY exists, commits present) → if pass, treat as success
- **Agent fails mid-plan:** Missing SUMMARY.md → report, ask user how to proceed
- **Dependency chain breaks:** Wave 1 fails → Wave 2 dependents likely fail → user chooses attempt or skip
- **All agents in wave fail:** Systemic issue → stop, report for investigation
- **Checkpoint unresolvable:** "Skip this plan?" or "Abort phase execution?" → record partial progress in STATE.md
</failure_handling>

<resumption>
Re-run `/gsd:execute-phase {phase}` → discover_plans finds completed SUMMARYs → skips them → resumes from first incomplete plan → continues wave execution.

STATE.md tracks: last completed plan, current wave, pending checkpoints.
</resumption>
