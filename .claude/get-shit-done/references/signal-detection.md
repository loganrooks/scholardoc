# Signal Detection Reference

## 1. Overview

Defines detection rules, severity classification, polarity assignment, deduplication, and signal management for post-execution analysis of GSD workflow artifacts.

**Consumers:**
- `gsd-signal-collector` agent (automatic post-execution detection)
- `/gsd:signal` command (manual signal creation)
- `/gsd:collect-signals` command (batch signal collection)

**Input artifacts:**
- PLAN.md -- planned tasks, files, verification criteria
- SUMMARY.md -- execution results, deviations, issues
- VERIFICATION.md -- gap analysis against must_haves
- `.planning/config.json` -- model_profile and workflow settings

**Output:** Signal entries written to `.planning/knowledge/signals/{project}/` (or `~/.gsd/knowledge/signals/{project}/` fallback) using the Phase 1 signal template.

## 2. Deviation Detection (SGNL-01)

Compare PLAN.md against SUMMARY.md for each completed plan.

**Detection points:**

| PLAN.md Source | SUMMARY.md Source | What to Check |
|----------------|-------------------|---------------|
| `<tasks>` list (count of `<task>` elements) | `## Task Commits` table (row count) | Task count mismatch (planned vs completed) |
| `files_modified:` frontmatter array | `## Files Created/Modified` section | Unexpected files touched or expected files missing |
| `<verification>` criteria | `## Deviations from Plan` section | Auto-fixes indicate plan gaps or underspecification |
| `must_haves:` truths | VERIFICATION.md `gaps_found` results | Verification gaps -- goals not fully met |

**Positive deviation detection:**
- SUMMARY.md mentions unexpected improvements or cleaner-than-planned outcomes
- Execution completed ahead of schedule (duration well below expected)
- Additional helpful artifacts created beyond plan scope
- These generate positive-polarity signals (see Section 7)

### 2.1 Positive Signal Detection

Positive signals use `signal_category: positive` and one of the following `signal_type` values:

| signal_type | Detection Criteria | Example |
|-------------|-------------------|---------|
| `baseline` | Sensor observes a normal/healthy state worth tracking as a regression guard | "All 35 command files have correct path prefixes after install" |
| `improvement` | Execution outcome is measurably better than planned/expected | "Reduced test suite runtime from 12s to 4s during refactoring" |
| `good-pattern` | Practice or approach worth repeating, identified during execution | "TDD workflow caught 3 edge cases that would have been missed" |

**Detection rules for positive signals:**
1. Positive signals follow the same lifecycle and rigor rules as negative signals, proportional to their severity
2. Severity assignment uses the same criteria as negative signals (e.g., a baseline that guards critical infrastructure is `notable`, not `minor`)
3. Positive signals are persisted to KB using the same persistence rules as negative signals (critical/notable/minor persisted, trace logged only)
4. Counter-evidence for positive signals represents reasons the positive observation might not hold (e.g., "baseline only tested on macOS, not Linux")

**Detection logic:**
1. Count `<task` elements in PLAN.md, count rows in Task Commits table in SUMMARY.md
2. Parse `files_modified` from plan frontmatter, compare against files listed in SUMMARY.md
3. Check "Deviations from Plan" section -- if it contains "Auto-fixed Issues" subsections, each is a deviation signal candidate
4. If VERIFICATION.md exists, check for `gaps_found: true` or partial passes

## 3. Config Mismatch Detection (SGNL-02)

Compare `.planning/config.json` `model_profile` against executor spawn information.

**Model profile expectations:**

| Profile | Expected Executor Model Class |
|---------|-------------------------------|
| `quality` | opus-class (claude-opus-*) |
| `balanced` | sonnet-class (claude-sonnet-*) |

**Detection rules:**
- Only flag mismatches where the outcome was likely affected
- If `quality` profile but sonnet-class executor was used: flag as critical
- If `balanced` profile and sonnet-class was used: expected, no signal
- Harmless fallbacks (e.g., model temporarily unavailable, fallback produced correct results) should not generate signals

**Where to find executor model info:** SUMMARY.md may reference the model used. If not explicitly stated, check git log commit metadata or skip this detection for the plan.

## 4. Struggle Detection (SGNL-03)

Scan SUMMARY.md for indicators of execution difficulty.

**Struggle indicators:**

| Indicator | Source Section | Threshold |
|-----------|---------------|-----------|
| Non-trivial issues encountered | `## Issues Encountered` | Content beyond "None" or "No issues" |
| Multiple auto-fixes | `## Deviations from Plan` | 3+ auto-fix entries in a single plan |
| Checkpoint returns on autonomous plans | `## Deviations from Plan` | Any checkpoint return when plan has `autonomous: true` |
| Disproportionate duration | `## Performance` section | Duration significantly exceeding plan complexity (use judgment) |

**What qualifies as "non-trivial" in Issues Encountered:**
- Error messages, stack traces, or debugging descriptions
- Workarounds applied instead of clean solutions
- External blockers (API outages, auth failures, dependency issues)

**What does NOT qualify:**
- "None" or "No issues encountered"
- Minor notes about expected behavior
- Informational observations without friction

## 5. Frustration Detection (SGNL-06)

Pattern matching for implicit frustration in conversation context. Used by `/gsd:signal` command when scanning recent messages.

**Frustration patterns:**
- "still not working"
- "this is broken"
- "tried everything"
- "keeps failing"
- "doesn't work"
- "same error"
- "frustrated"
- "why won't"
- "makes no sense"
- "wasting time"

**Trigger threshold:** 2+ patterns detected in recent messages suggests a frustration signal.

**Important:** These patterns are indicators, not definitive triggers. The agent uses judgment -- a user saying "this doesn't work yet" in a calm technical context is different from repeated frustrated messages. The patterns inform a suggestion to create a frustration signal, not an automatic signal creation.

**Scope:** Frustration detection applies to `/gsd:signal` manual command context only. Post-execution automatic detection (via `gsd-signal-collector`) does not have access to conversation context and should not attempt frustration detection.

## 6. Severity Auto-Assignment (SGNL-04)

Automatic severity classification based on detection source and impact. Uses four tiers: `critical`, `notable`, `minor`, `trace`.

| Condition | Severity |
|-----------|----------|
| Verification failed (`gaps_found`) | critical |
| Config mismatch (wrong model class spawned) | critical |
| 3+ auto-fixes in a single plan | notable |
| Issues encountered (non-trivial) | notable |
| Positive deviations (unexpected improvements) | notable |
| Single auto-fix | minor |
| Minor file differences (extra helper files created) | minor |
| Task order changed with no impact | minor |
| Capability gap (known runtime limitation) | trace |

**Persistence rules:**
- **critical** -- always persisted to KB
- **notable** -- always persisted to KB
- **minor** -- always persisted to KB
- **trace** -- logged in collection report output only, NOT written to KB. **Enforcement note:** The signal synthesizer (Phase 32) is the enforcement point for trace non-persistence -- it filters trace signals before KB write. Until Phase 32, the signal-collector emits all signals regardless of severity. Consumers of this reference should be aware that trace filtering is NOT yet enforced at the signal-collector level.

**Epistemic rigor requirements by severity tier** (see knowledge-store.md Section 4.3 for full evidence schema):
- **critical** -- `evidence.counter` REQUIRED. System refuses to persist without counter-evidence.
- **notable** -- `evidence` (supporting and/or counter) RECOMMENDED. Signals without evidence are accepted but flagged.
- **minor** -- `evidence` OPTIONAL. Detection context is sufficient.
- **trace** -- not applicable (not persisted to KB).

**Manual override:** The `/gsd:signal` command allows users to set severity explicitly, overriding auto-assignment. Manual signals at any severity level (including trace equivalent) are always persisted since the user explicitly chose to record them.

## 7. Polarity Assignment

Every signal receives a polarity indicating whether the observation is positive, negative, or neutral.

| Detection | Polarity |
|-----------|----------|
| Verification gaps | negative |
| Debugging struggles | negative |
| Config mismatches | negative |
| Frustration indicators | negative |
| Unexpected improvements | positive |
| Ahead-of-schedule completion | positive |
| Cleaner-than-planned implementation | positive |
| Task reordering with no impact | neutral |
| Minor file differences | neutral |

Polarity enables Phase 4 (Reflection Engine) to distinguish problems from happy accidents when analyzing signal patterns.

## 8. Signal Schema Extensions

These optional fields extend the Phase 1 signal schema defined in `knowledge-store.md`. Existing required fields (`severity`, `signal_type`, `phase`, `plan`) remain unchanged.

**Note on `signal_type` enum:** The full set of valid values is: `deviation`, `struggle`, `config-mismatch`, `capability-gap`, `epistemic-gap`, `baseline`, `improvement`, `good-pattern`, `custom`. The extended values (`epistemic-gap`, `baseline`, `improvement`, `good-pattern`) were added in Phase 31 for positive signal detection and epistemic gap tracking.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `signal_category` | enum: positive, negative | negative | Whether the signal represents a positive or negative observation. Replaces `polarity` as the primary positive/negative indicator; `polarity` is retained for backward compatibility. |
| `polarity` | enum: positive, negative, neutral | negative | Whether the signal represents a positive, negative, or neutral observation. Retained for backward compatibility; prefer `signal_category` for new signals. |
| `source` | enum: auto, manual | auto | Whether the signal was detected automatically or created manually via `/gsd:signal` |
| `occurrence_count` | integer | 1 | How many times this signal pattern has been observed (starts at 1) |
| `related_signals` | array of signal IDs | [] | IDs of existing signals that match this signal's pattern (for dedup cross-references) |
| `runtime` | enum: claude-code, opencode, gemini-cli, codex-cli | (omitted) | Runtime that generated this signal. Inferred from workflow file path prefix. Optional -- omit if unknown. |
| `model` | string | (omitted) | LLM model identifier. Self-reported by the executing model. Optional -- omit if unknown. |
| `lifecycle_state` | enum: detected, triaged, remediated, verified, invalidated | detected | Current lifecycle state -- see knowledge-store.md Section 4.2 for full lifecycle state machine |
| `evidence` | object: {supporting: [], counter: []} | {} | Epistemic evidence -- see knowledge-store.md Section 4.3 for rigor requirements by severity |
| `confidence` | enum: high, medium, low | medium | Categorical confidence level |
| `confidence_basis` | string | "" | Text explaining confidence assessment |

**Compatibility:** These fields are added to signal frontmatter alongside the Phase 1 base schema and signal extension fields. Agents that do not recognize these fields can safely ignore them. The Phase 1 index rebuild script processes all frontmatter fields without filtering. Existing signals without the new fields remain valid -- absent fields default to the values shown in the Default column.

**Runtime/model field note:** These fields are optional. Existing signals without runtime/model fields remain valid. Agents that do not recognize these fields can safely ignore them.

### 8.1 Signal Enrichment Fields (Cross-Project Readiness)

These optional fields provide environment context for future cross-project signal sharing. They are auto-populated from the runtime environment and added to new signals only -- do NOT backfill existing signals.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `source` | enum: local, external | local | Whether the signal originated from the local project KB or was shared from another project. The `source` field defaults to `local`. Future cross-project signal sharing will use `source: external`. |
| `environment.os` | string | (auto) | Operating system, auto-populated via `uname -s` |
| `environment.node_version` | string | (auto) | Node.js version, auto-populated via `node --version` |
| `environment.config_profile` | string | (auto) | Model profile from `.planning/config.json`, auto-populated |

**Note on `source` field naming:** The enrichment `source` field (`local`/`external`) tracks signal origin location for cross-project sharing. This is distinct from the existing `source` field in Section 8 (`auto`/`manual`) which tracks detection method. In signal frontmatter, the enrichment field uses `origin: local` to avoid collision with the detection-method `source` field.

**Environment field purpose:** The `environment` fields help diagnose whether a signal is environment-specific (e.g., macOS-only build failure) or universal (e.g., logic error independent of OS). This context is essential for cross-project signal sharing where signals from different environments may have different relevance.

## 9. Deduplication Rules (SGNL-05)

Before writing a new signal, check for related existing signals to avoid redundant entries.

**Deduplication process:**

1. Read existing signals for the project from `.planning/knowledge/index.md` (or `~/.gsd/knowledge/index.md` fallback)
2. For each existing active signal, check match criteria:
   - Same `signal_type` (deviation, struggle, config-mismatch, custom)
   - Same `project`
   - Overlapping tags: 2+ shared tags between new and existing signal
3. If match found:
   - Add all matched signal IDs to the `related_signals` array on the NEW signal
   - Set `occurrence_count` to the highest `occurrence_count` among matched signals + 1
4. Do NOT update existing signals (immutability constraint from Phase 1)
5. Write the new signal with `related_signals` populated

**Why not update existing signals:** Signals are immutable after creation (Phase 1 lifecycle rules). Each signal captures a moment in time. Pattern detection across related signals is the responsibility of Phase 4 (Reflection Engine), which reads `related_signals` to identify recurring issues.

**Cross-phase dedup:** Deduplication checks all active signals for the project, not just the current phase. A recurring auth issue in Phase 2 and Phase 3 should be cross-referenced.

## 10. Per-Phase Signal Cap (SGNL-09)

Prevents signal noise from overwhelming the knowledge base.

**Rules:**
- Maximum **10** persistent signals per phase per project
- Trace signals are never persisted and do not count toward the cap
- `critical`, `notable`, and `minor` signals count toward the cap

**Cap enforcement:**
1. Before writing a new signal, count existing active signals for this phase and project
2. If count < 10: write normally
3. If count >= 10: compare new signal severity against the lowest-severity existing signal
   - If new signal severity >= lowest existing severity: archive the lowest-severity signal (set `status: archived` in its frontmatter), then write the new signal
   - If new signal severity < lowest existing severity: do not persist (log in report only)

**Severity ordering for cap comparison:** critical > notable > minor

**Archival for cap replacement:**
- Set `status: archived` in the replaced signal's frontmatter
- This is the ONE exception to signal immutability -- archival status changes are permitted for cap management
- Archived signals remain in their original file location
- Archived signals are excluded from the index on next rebuild

## 11. Detection Timing

**Automatic detection (post-execution):**
- Runs after all plans in a phase complete
- Invoked via `/gsd:collect-signals {phase-number}` command
- Reads stable output artifacts only: PLAN.md, SUMMARY.md, VERIFICATION.md, config.json
- Does not run mid-execution (wrapper pattern constraint -- cannot modify executor agents)

**Manual detection (anytime):**
- Via `/gsd:signal` command during any conversation
- User can create signals at any time based on their observations
- Frustration detection (SGNL-06) is available in manual mode via conversation context scanning

**No mid-execution detection:**
- Executor agents run in fresh contexts with no signal collection hooks
- Modifying executor agent instructions would violate the fork constraint (additive-only)
- All automatic detection is retrospective, reading artifacts after execution completes

## 12. Capability Gap Detection (SGNL-07)

Detects when a runtime lacks a required capability and degrades gracefully.

**Detection source:** `execute-phase.md` capability_check blocks, specifically the Else branches.

**Signal properties:**
- `signal_type: capability-gap`
- `severity: trace` (known limitations, not errors -- logged in collection report only, NOT persisted to KB)
- `polarity: neutral` (expected behavior, not positive or negative)
- `runtime:` set to the detected runtime

**Detection points:**

| Capability | Detection Location | Description |
|------------|-------------------|-------------|
| `task_tool` | execute-phase.md capability_check "parallel_execution" Else | Parallel wave execution unavailable, degraded to sequential |
| `hooks` | execute-phase.md capability_check "hooks_support" Else | Hook-based update checks unavailable |

**Escalation:** If a capability gap causes an actual execution failure (not just degradation), the resulting signal should be elevated to `notable` or `critical` severity based on impact. Trace is only for expected, handled degradation.

**Important:** Capability gap signals are trace-severity by design. They are NOT persisted to the KB to avoid flooding with repetitive "no task_tool in Codex" entries. They appear in signal collection reports only. If cross-runtime analytics become important in a future milestone, the severity can be re-evaluated.

## 13. Epistemic Gap Detection (SGNL-10)

Detects when the system identifies a domain where evidence is insufficient, unverifiable, or indirect.

**Signal properties:**
- `signal_type: epistemic-gap`
- `signal_category: negative` (gaps represent missing knowledge)
- `confidence: low` (inherently low -- flagging what we DON'T know)
- `severity:` typically `notable` or higher (knowledge gaps are worth tracking)

**Detection criteria:**

A sensor identifies an epistemic gap when any of these conditions hold:

| Condition | Example |
|-----------|---------|
| Missing sensor coverage | "No sensor exists for cross-runtime KB operations" |
| Unverifiable causal claims | "Root cause hypothesis is based on inference, not direct observation" |
| Indirect evidence for key conclusions | "Conclusion derived from absence of errors, not presence of verification" |
| Insufficient evidence base | "Pattern detected from 2 signals but root causes differ" |
| Known blind spots in analysis | "Frustration detection only works for manual signals, not automatic" |

**Lifecycle behavior:**
- Epistemic gap signals follow the same lifecycle as all other signals (detected -> triaged -> remediated -> verified)
- Remediation of an epistemic gap means the knowledge gap has been filled (e.g., new sensor added, direct evidence obtained)
- Verification means the remediation was confirmed to address the gap
- Rigor rules are proportional to severity, same as other signals

**Relationship to other signal types:**
- Epistemic gap signals may cluster with related deviation or struggle signals during pattern detection (if tags overlap)
- An epistemic gap about auth and a deviation about auth are related -- they share the same knowledge domain
- Epistemic gap signals serve as meta-signals: they flag where the system's own observation capabilities are insufficient

---

*Reference version: 1.2.0*
*Created: 2026-02-03*
*Updated: 2026-02-28*
*Phase: 02-signal-collector, 16-cross-runtime-handoff-signal-enrichment, 31-signal-schema-foundation*
