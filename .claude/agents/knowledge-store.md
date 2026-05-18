---
name: knowledge-store
description: Complete reference specification for the GSD persistent knowledge store. Defines file formats, directory layout, schemas, naming conventions, indexing, lifecycle, and concurrency for all knowledge base operations.
version: 2.0.0
---

# Knowledge Store Reference

## 1. Overview

The GSD Knowledge Store is a persistent knowledge base. The primary location is `.planning/knowledge/` (project-local, version-controlled). When `.planning/knowledge/` does not exist, agents fall back to `~/.gsd/knowledge/` (user-global). It stores three entry types: signals (workflow deviations and struggles), reflections (analysis reports), and spikes (structured experiments and decisions).

**Note:** Lessons are deprecated. Existing lesson files remain at `~/.gsd/knowledge/lessons/` as historical artifacts and may still be read for backward compatibility, but no new lesson files are created. Lesson candidates are documented in reflection reports instead.

**Consumers:** GSD-internal agents only. No external tool integration required.

**Philosophy:** The store is a dumb-but-well-organized filing cabinet. Intelligence lives in the agents that read from it. The store provides structure and conventions; agents provide interpretation and relevance judgment.

**Design principles:**
- Agent-first, human-readable -- optimized for LLM consumption but still legible if a human opens a file
- Zero runtime dependencies -- pure Markdown files with YAML frontmatter
- Files are source of truth -- indexes and caches are derived, never authoritative

## 2. Directory Structure

**Primary location (project-local, version-controlled):**
```
.planning/knowledge/
├── signals/
│   └── {project-name}/
│       └── {YYYY-MM-DD}-{slug}.md
├── spikes/
│   └── {project-name}/
│       └── {spike-name}.md
├── reflections/
│   └── {project-name}/
│       └── reflect-{YYYY-MM-DD}.md
└── index.md
```

**Fallback location (user-global, when `.planning/knowledge/` does not exist):**
```
~/.gsd/knowledge/
├── signals/
│   └── ...
├── spikes/
│   └── ...
├── reflections/
│   └── ...
├── lessons/          # DEPRECATED -- historical artifacts only
│   └── {category}/
│       └── {lesson-name}.md
└── index.md
```

**KB path resolution pattern (for agents and scripts):**
```bash
# KB path resolution -- project-local primary, user-global fallback
if [ -d ".planning/knowledge" ]; then
  KB_DIR=".planning/knowledge"
else
  KB_DIR="$HOME/.gsd/knowledge"
fi
```

**Project scoping:**
- Signals and spikes are stored under project subdirectories within their type directory
- Project name is derived from the project's root directory name (kebab-case)
- Global entries (not tied to a specific project) use `_global/` as the project subdirectory name
- Lessons are organized by category subdirectory, not by project (lessons transcend individual projects)
- Reflections are stored under project subdirectories, one per reflect run date (latest overwrites same-day runs)

**Directory creation:**
- Parent directories are created on first write (mkdir -p)
- Empty directories are not pre-created

## 3. Common Base Schema

All entry types share this YAML frontmatter base:

```yaml
---
id: {type-prefix}-{YYYY-MM-DD}-{slug}
type: signal | spike | lesson
project: {project-name} | _global
tags: [tag1, tag2, tag3]
created: 2026-02-02T14:30:00Z
updated: 2026-02-02T14:30:00Z
durability: workaround | convention | principle
status: active | archived
# depends_on: ["prisma >= 4.0", "src/lib/auth.ts exists"]
---
```

**Required fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier: `{type-prefix}-{YYYY-MM-DD}-{slug}` |
| `type` | enum | Entry type: `signal`, `spike`, or `lesson` |
| `project` | string | Project name or `_global` for cross-project entries |
| `tags` | array | Searchable tags from seeded taxonomy + freeform |
| `created` | ISO-8601 | Creation timestamp |
| `updated` | ISO-8601 | Last modification timestamp (same as created for immutable types) |
| `durability` | enum | Knowledge durability class: `workaround`, `convention`, or `principle` |
| `status` | enum | Lifecycle status: `active` or `archived` |

**Optional tracking fields (updated on read):**

| Field | Type | Description |
|-------|------|-------------|
| `retrieval_count` | number | Times this entry has been retrieved by agents |
| `last_retrieved` | ISO-8601 | Last time an agent read this entry |

These fields support future pruning design. Agents should increment `retrieval_count` and update `last_retrieved` when reading an entry for decision-making. Do NOT use these fields for automated decisions yet.

**Optional freshness fields:**

| Field | Type | Description |
|-------|------|-------------|
| `depends_on` | array | Conditions that could invalidate this entry. Each element is a human-readable string describing a dependency (e.g., `"prisma >= 4.0"`, `"src/lib/auth.ts exists"`, `"NOT monorepo"`). Agents read these and use judgment to assess whether the entry is still valid. |

The `depends_on` field supports the knowledge surfacing system's freshness model. When agents retrieve an entry, they check `depends_on` conditions against the current codebase. If conditions no longer hold, the entry is surfaced with a staleness caveat. If `depends_on` is absent, agents fall back to temporal decay heuristics. See `get-shit-done/references/knowledge-surfacing.md` Section 4 for the full freshness checking specification.

**Optional provenance fields:**

| Field | Type | Description |
|-------|------|-------------|
| `runtime` | enum | Runtime that created this entry: `claude-code`, `opencode`, `gemini-cli`, or `codex-cli` |
| `model` | string | LLM model identifier (e.g., `claude-opus-4-6`, `o3`) |
| `gsd_version` | string | GSD version that created this entry (e.g., `1.14.0`). Read from VERSION file or config.json |

These fields are optional for backward compatibility. Existing entries without them remain valid. New entries SHOULD include all three when available.

## 4. Type-Specific Extensions

### Signal Extensions

Added to frontmatter alongside common base fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `severity` | enum | yes | `critical`, `notable`, `minor`, or `trace` |
| `signal_type` | enum | yes | `deviation`, `struggle`, `config-mismatch`, `capability-gap`, `epistemic-gap`, `baseline`, `improvement`, `good-pattern`, or `custom` |
| `signal_category` | enum | no | `positive` or `negative` (defaults to `negative` for backward compatibility). This is the authoritative field for positive/negative classification. `polarity` is retained for backward compatibility but `signal_category` takes precedence when both are present. New signals MUST set both fields consistently. |
| `phase` | number | no | Phase number where signal was captured |
| `plan` | number | no | Plan number where signal was captured |
| `polarity` | enum | no | `positive`, `negative`, or `neutral` (retained for backward compatibility; see `signal_category`) |
| `source` | enum | no | `auto` or `manual` |
| `occurrence_count` | number | no | Times this signal pattern has occurred (default: 1) |
| `related_signals` | array | no | IDs of related signals for cross-referencing |
| `lifecycle_state` | enum | no | Current lifecycle state: `detected`, `triaged`, `remediated`, `verified`, or `invalidated` (default: `detected`). Top-level field for index grep compatibility. |
| `lifecycle_log` | array | no | Array of quoted strings recording state transitions (default: `[]`). Entries MUST be quoted strings in YAML to protect special characters (colons, arrows). Example: `- "detected->triaged by reflector at 2026-02-28T10:00:00Z: rationale"` |
| `evidence` | object | conditional | Contains `supporting` (array of strings) and `counter` (array of strings). Default: `{}`. REQUIRED when severity is `critical`. RECOMMENDED when severity is `notable`. OPTIONAL for `minor`. Not applicable for `trace` (not persisted to KB). |
| `confidence` | enum | no | `high`, `medium`, or `low` (default: `medium`) |
| `confidence_basis` | string | no | Text explaining confidence assessment (default: `""`) |
| `triage` | object | no | Contains `decision` (address/dismiss/defer/investigate), `rationale`, `priority` (critical/high/medium/low), `by`, `at`, `severity_override`. Default: `{}`. Use empty objects `{}` (NOT null) for unset triage -- `reconstructFrontmatter()` silently drops null values (Pitfall 6). Note: `reconstructFrontmatter()` normalizes `triage: {}` to `triage:` (bare key). This is functionally equivalent -- the bare key re-parses as an empty object. The roundtrip is stable. |
| `remediation` | object | no | Contains `status` (planned/in-progress/complete), `resolved_by_plan`, `approach`, `at`. Default: `{}`. Same empty-object convention as triage. |
| `verification` | object | no | Contains `status` (pending/passed/failed), `method` (absence-of-recurrence/active-retest/evidence-review), `evidence_required` (for critical: active-retest), `at`. Default: `{}`. Same empty-object convention as triage. |
| `recurrence_of` | string | no | Signal ID this is a recurrence of (default: `""` -- use empty string, not null) |

### Spike Extensions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `hypothesis` | string | yes | The testable claim being investigated |
| `outcome` | enum | yes | `confirmed`, `rejected`, `partial`, or `inconclusive` |
| `rounds` | number | no | Number of iteration rounds conducted |

### Lesson Extensions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `category` | enum | yes | `architecture`, `workflow`, `tooling`, `testing`, `debugging`, `performance`, or `other` |
| `evidence_count` | number | yes | Number of supporting signals/spikes |
| `evidence` | array | no | List of entry IDs that support this lesson |

### 4.2 Lifecycle State Machine

Signals follow a lifecycle from detection through resolution. The lifecycle state machine tracks where each signal is in this process.

**State diagram:**

```
                    +--> invalidated (terminal, with audit)
                    |
detected --> triaged --> remediated --> verified
   ^           |            |              |
   |           |            |              |
   +-----------+            +--------------+
   (regression: recurrence    (regression: recurrence
    resets to detected)        resets to detected)
```

**State transitions:**

| From | To | Trigger | Who Can Trigger |
|------|-----|---------|----------------|
| (new) | detected | Signal created | signal-collector, human |
| detected | triaged | Triage decision made | reflector, human |
| detected | invalidated | Counter-evidence overwhelms supporting | reflector, human |
| triaged | remediated | Plan with resolves_signals completes | executor (auto), human |
| triaged | detected | (regression) Recurrence detected | synthesizer |
| triaged | invalidated | Counter-evidence overwhelms supporting | reflector, human |
| remediated | verified | Verification criteria met | synthesizer (passive), human |
| remediated | detected | (regression) Recurrence detected | synthesizer |
| verified | detected | (regression) Recurrence detected (severity escalated) | synthesizer |
| any | invalidated | Audit-trailed invalidation | reflector, human |

**Terminal state -- invalidation and archival:** When a signal enters the `invalidated` terminal state, its `status` field is simultaneously set to `archived` to remove it from the active signal pool. The invalidation reason is preserved in `lifecycle_log`. Example lifecycle_log entry: `"triaged->invalidated by reflector at 2026-02-28T10:00:00Z: counter-evidence demonstrates false positive"`.

**Dismissed signals:** Dismissed is a triage decision value (`triage.decision: dismiss`), NOT a lifecycle state. A dismissed signal stays in `triaged` state with `triage.decision: dismiss`. This preserves the four-state lifecycle while recording the dismiss decision.

**Regression paths:** When a signal recurs (a new signal is detected that matches an existing remediated or verified signal), the existing signal regresses to `detected` state. Severity escalation follows the `recurrence_escalation` project setting -- when enabled, recurrence escalates severity (e.g., notable -> critical on second recurrence of a verified signal).

**Skip rules by lifecycle_strictness setting:**

| Setting | Allowed Transitions | Restrictions |
|---------|-------------------|--------------|
| `strict` | All states required in order | No skipping; every transition must go through each intermediate state |
| `flexible` (default) | detected -> remediated allowed (fix without formal triage) | detected -> verified is NOT allowed (must have remediation evidence) |
| `minimal` | Any forward transition allowed | No restrictions on forward movement |

**Existing signals (backward compatibility):** The 46 existing signals have no `lifecycle_state` field. When absent, `lifecycle_state` defaults to `detected`. Bulk triage of existing signals is deferred to Phase 33 (Enhanced Reflector). Schema validation is opt-in -- agents call `frontmatter validate --schema signal` only on NEW signals they create.

**Backward-compat validation (`backward_compat` in FRONTMATTER_SCHEMAS):** When `lifecycle_state` is absent from a signal, `cmdFrontmatterValidate` downgrades conditional `require` fields to warnings (prefixed `backward_compat:`). This allows the 6 pre-existing critical signals (which lack `evidence`) to pass validation. Signals created from the Phase 31+ template always include `lifecycle_state: detected` and receive full strict enforcement.

**Phase 33 triage constraint:** When bulk triage adds `lifecycle_state` to existing critical signals, it MUST also add `evidence` (with at least one `supporting` entry) or downgrade `severity`. Once `lifecycle_state` is present, the backward-compat exemption no longer applies and the conditional evidence requirement becomes a hard failure.

**Legacy SIG-format signals:** 15 legacy SIG-format signals (SIG-260222-*, SIG-260223-*) predate the standard schema and may contain non-standard field values (e.g., `status: resolved`, `type: positive-pattern`). These are readable via `extractFrontmatter()` but are not subject to formal schema validation.

### 4.3 Epistemic Rigor Requirements

Signal quality depends on epistemic rigor -- the discipline of evidence-based reasoning. The system enforces proportional rigor based on signal severity.

**Five epistemic principles:**

1. **Proportional rigor** -- Stakes determine evidence requirements. Critical signals demand full evidence; trace signals need only detection context.
2. **Epistemic humility** -- Acknowledge what the system cannot see. Use `epistemic-gap` signal type to flag blind spots.
3. **Evidence independence** -- Repeated citations of the same fact are NOT corroboration. Independent observations converging on the same conclusion constitute genuine corroboration.
4. **Mandatory counter-evidence** -- Critical claims must be challenged. The system requires counter-evidence for critical signals as a structural safeguard against confirmation bias.
5. **Meta-epistemic reflection** -- The system evaluates its own reasoning quality. Evidence quality is annotated in `confidence_basis` so downstream agents can assess whether the evidence supports justified belief.

**Tiered rigor requirements by severity:**

| Severity | Evidence | Counter-evidence | Confidence | Verification |
|----------|----------|-----------------|------------|--------------|
| `critical` | REQUIRED (hard fail without `evidence.supporting`) | REQUIRED (hard fail without `evidence.counter`) | `confidence_basis` REQUIRED | Active verification required (`active-retest` or `evidence-review`) |
| `notable` | RECOMMENDED (warn if missing) | RECOMMENDED (warn if missing) | RECOMMENDED | Passive verification acceptable (`absence-of-recurrence`) |
| `minor` | Evidence summary sufficient | Not required | OPTIONAL | Evidence summary sufficient |
| `trace` | Minimal -- detection context only | Not required | Not applicable | Not persisted to KB; logged in collection reports only |

**Rigor enforcement behavior** is determined by the project setting `rigor_enforcement`:
- `strict`: Missing required evidence blocks signal creation (hard fail)
- `warn` (default): Missing required evidence produces a warning but allows creation
- `permissive`: No enforcement; rigor is advisory only

**Epistemic gap signals:** Signals with `signal_type: epistemic-gap` explicitly acknowledge blind spots -- areas where the system suspects an issue but lacks tools or evidence to confirm. These signals use `signal_category: negative` (they represent missing knowledge) and `confidence: low` inherently (the system is flagging what it does NOT know).

**Meta-evidence:** The system annotates evidence quality in `confidence_basis`. This enables downstream agents (reflector, synthesizer) to evaluate not just what was observed but how reliable the observation process was. Example: `"3 auto-fixes detected via SUMMARY.md parsing -- high extraction confidence but root cause assessment is speculative"`.

### 4.4 Positive Signals

Positive signals capture healthy states, improvements, and practices worth repeating. They use the same schema as negative signals with different field values.

**Three types of positive signals:**

| Type | signal_type | Description | Example |
|------|-------------|-------------|---------|
| Baseline | `baseline` | Normal/healthy state worth preserving | "All 35 commands have correct path prefixes" |
| Improvement | `improvement` | Measurable improvement over previous state | "Build time reduced 40% after tree-shaking" |
| Good pattern | `good-pattern` | Practice worth repeating across projects | "TDD red-green-refactor prevented 3 integration bugs" |

**Field values for positive signals:**
- `signal_category: positive` (authoritative positive/negative classification)
- `polarity: positive` (retained for backward compatibility; both fields set consistently)
- Same severity tiers apply equally (a critical baseline is possible)

**Lifecycle with semantic reinterpretation:** Positive signals follow the same four-state lifecycle with adjusted semantics:
- `detected` -- Positive pattern observed
- `triaged` -- Confirmed as meaningful (not noise)
- `remediated` -- For positives, this means "baseline reinforced" or "improvement sustained" (skip is common under flexible strictness)
- `verified` -- Baseline confirmed stable over time; improvement confirmed durable

**Triple purpose:**
1. **Lesson inputs** -- Positive patterns feed into lesson distillation (what to repeat)
2. **Regression guards** -- Baselines define the good state; future deviations from baseline trigger negative signals
3. **Cross-project transfer** -- Good patterns that work in one project can be surfaced in others via global promotion

### 4.5 Plan-Signal Linkage

Plans can declare which signals they resolve using the `resolves_signals` frontmatter field. This creates a traceable link from remediation work back to the signals that motivated it.

**`resolves_signals` in PLAN.md frontmatter:**

`resolves_signals` is an optional array field in PLAN.md frontmatter. It contains signal IDs (format: `sig-YYYY-MM-DD-slug`) that the plan's tasks are intended to address.

```yaml
---
phase: 12-auth-hardening
plan: 02
type: execute
resolves_signals:
  - sig-2026-02-15-auth-retry-loop
  - sig-2026-02-18-token-expiry-race
---
```

**How it works:**
- The planner recommends signal IDs based on active triaged signals with `triage.decision: address`
- When plan execution completes successfully, referenced signals transition to `remediated` status (lifecycle_state updated, lifecycle_log entry added, remediation.resolved_by_plan set)
- Non-existent signal IDs produce warnings, not errors (signals may be archived or invalidated between planning and execution)
- The executor performs the lifecycle transition automatically -- no manual intervention required

**Validation:** The `FRONTMATTER_SCHEMAS.plan` schema validates only required fields and does not reject unknown fields, so `resolves_signals` works without code changes to gsd-tools.js.

### 4.6 Verification by Absence (verification_window)

After remediation, signals are passively verified through absence of recurrence. If no recurrence is detected within a configurable number of phases, the signal automatically transitions from `remediated` to `verified`.

**Configuration:**
- `verification_window` is a project-level setting in `signal_lifecycle` config (feature-manifest.json)
- Type: number (integer)
- Default: 3 phases
- Range: 1-10 phases
- Meaning: number of phases with no recurrence before a remediated signal is verified

**How it works:**
1. A signal is marked `remediated` (e.g., via `resolves_signals` on plan completion)
2. The `remediation.at` timestamp records when remediation occurred
3. During each subsequent signal collection run, the synthesizer checks remediated signals
4. If N phases have elapsed since remediation with no recurrence detected, the signal transitions to `verified`
5. The verification method is recorded as `absence-of-recurrence` in the `verification` object

**Lifecycle transition:** `remediated` -> `verified` (triggered by synthesizer, passive)

### 4.7 Recurrence Detection

Recurrence detection identifies when a previously remediated or verified signal reappears, indicating the underlying issue was not fully resolved.

**Matching criteria:** A new signal is considered a recurrence of an existing signal when:
- Same `signal_type` value, AND
- 2 or more overlapping `tags`

The match is evaluated against signals in `remediated` or `verified` lifecycle states.

**When recurrence is detected:**
1. The new signal's `recurrence_of` field is set to the matched signal's ID
2. The matched signal regresses: `lifecycle_state` returns to `detected`
3. A lifecycle_log entry is added: `"verified->detected by synthesizer at {timestamp}: recurrence detected (new signal: {new-signal-id})"`
4. The matched signal's `updated` timestamp is refreshed

**Recurrence escalation:** When the project setting `recurrence_escalation` is enabled (default: true), severity increases one tier on recurrence:
- `minor` -> `notable`
- `notable` -> `critical`
- `critical` remains `critical` (ceiling)

The escalation applies to the NEW signal (the recurrence), not the original. The original signal's severity is a frozen detection payload field.

**Synthesizer responsibility:** Recurrence detection is performed by the synthesizer during signal collection runs. Sensors detect raw signals; the synthesizer correlates them against existing KB entries.

## 5. Body Templates

### Signal Body

```markdown
## What Happened

[Factual description of the observed deviation, struggle, or mismatch]

## Context

[Phase, task, and environmental context surrounding the signal]

## Potential Cause

[Agent's assessment of why this happened -- root cause hypothesis]
```

### Spike Body

```markdown
## Hypothesis

[Full statement of the testable claim]

## Experiment

[What was tested, how, and under what conditions]

## Results

[Observed outcomes with data where applicable]

## Decision

[The decision made based on results -- this is the primary output]

## Consequences

[Known tradeoffs, follow-up work, or risks of this decision]
```

### Lesson Body

```markdown
## Lesson

[Concise statement of the learned principle or pattern]

## When This Applies

[Conditions, contexts, or triggers where this lesson is relevant]

## Recommendation

[Actionable guidance for agents encountering similar situations]

## Evidence

[References to supporting signals and spikes by file path or ID]
```

## 6. Seeded Tag Taxonomy

Initial tags organized by concern. Agents may create new tags freely; these provide consistency starting points.

**Type-of-issue:**
- `auth` -- authentication and authorization issues
- `config` -- configuration and environment issues
- `performance` -- speed, memory, or resource issues
- `error-handling` -- missing or incorrect error handling
- `data` -- data integrity, validation, or transformation issues
- `ui` -- user interface and display issues
- `testing` -- test coverage, reliability, or infrastructure issues

**Workflow:**
- `frustration` -- user expressed frustration or confusion
- `deviation` -- plan deviated from expected execution
- `retry` -- repeated attempts to accomplish a task
- `workaround` -- temporary fix for an underlying issue
- `blocked` -- task was blocked by an external dependency

**Domain:**
- Freeform -- agents create domain-specific tags as needed (e.g., `oauth`, `prisma`, `next-auth`, `rate-limiting`)

## 7. Naming Conventions

| Entry Type | Filename Pattern | Example |
|------------|-----------------|---------|
| Signal | `{YYYY-MM-DD}-{slug}.md` | `2026-02-02-auth-retry-loop.md` |
| Spike | `{spike-name}.md` | `jwt-refresh-strategy.md` |
| Lesson | `{lesson-name}.md` | `always-validate-refresh-tokens.md` |

**Slug rules:**
- Kebab-case (lowercase, hyphens between words)
- Derived from entry title or key concept
- Maximum 50 characters
- No special characters beyond hyphens
- Descriptive enough to identify content without opening file

## 8. ID Format

**Pattern:** `{type-prefix}-{YYYY-MM-DD}-{slug}`

**Type prefixes:**

| Type | Prefix | Example |
|------|--------|---------|
| Signal | `sig-` | `sig-2026-02-02-auth-retry-loop` |
| Spike | `spk-` | `spk-2026-01-28-jwt-refresh-strategy` |
| Lesson | `les-` | `les-2026-02-02-always-validate-refresh-tokens` |

**Uniqueness:** IDs are unique across the entire knowledge store. The combination of type prefix, date, and descriptive slug ensures uniqueness. In the unlikely event of a collision, append a numeric suffix (e.g., `-2`).

## 9. Index Format

The index at `.planning/knowledge/index.md` (or `~/.gsd/knowledge/index.md` fallback) is auto-generated and never hand-edited.

```markdown
# Knowledge Store Index

**Generated:** 2026-02-02T15:00:00Z
**Total entries:** 47

## Signals (23)

| ID | Project | Severity | Lifecycle | Tags | Date | Status |
|----|---------|----------|-----------|------|------|--------|
| sig-2026-02-02-auth-retry-loop | my-app | high | detected | auth, retry | 2026-02-02 | active |

## Spikes (12)

| ID | Project | Outcome | Tags | Date | Status |
|----|---------|---------|------|------|--------|
| spk-2026-01-28-jwt-refresh-strategy | my-app | confirmed | auth, jwt | 2026-01-28 | active |

## Lessons (12)

| ID | Project | Category | Tags | Date | Status |
|----|---------|----------|------|------|--------|
| les-2026-02-02-always-validate-refresh-tokens | _global | architecture | auth, oauth | 2026-02-02 | active |
```

**Index properties:**
- Header includes generation timestamp and total entry count
- Per-type sections with entry counts in section headers
- One markdown table per type with one row per entry
- Signal key fields: Severity, Lifecycle
- Spike key field: Outcome
- Lesson key field: Category
- `lifecycle_state` is a top-level field specifically for index grep compatibility (the `kb-rebuild-index.sh` script uses simple `grep` extraction that only works on top-level fields)
- Archived entries (status: archived) are excluded from index
- Files are source of truth; index is a derived cache

**Rebuild process:**
1. Scan all `.md` files under `signals/`, `spikes/`, and `lessons/`
2. Parse frontmatter from each file
3. Skip entries with `status: archived`
4. Write complete index to temporary file (`index.md.tmp`)
5. Rename temporary file to `index.md` (atomic replacement)

## 10. Lifecycle Rules

**No time-based decay.** Time is a poor heuristic for relevance. A principle is just as relevant after 6 months; a workaround becomes irrelevant when the bug is fixed, not when time passes.

**No hard entry caps.** No 50/200 entry limits. If the knowledge base outgrows flat-file storage, evolve the storage layer (sqlite, embeddings) rather than throwing away knowledge.

**No static relevance scores.** Relevance is contextual -- it depends on the current query/situation, not the entry itself.

**Mutability by type:**

| Type | Mutability | Rationale |
|------|-----------|-----------|
| Signal | Detection payload frozen after creation; lifecycle fields mutable | Signals capture a moment in time (detection payload) but evolve through lifecycle (triage, remediation, verification) |
| Spike | Immutable after creation | Spikes capture an experiment and its outcome |
| Lesson | Update-in-place | Lessons represent current knowledge; update `updated` timestamp on modification |

**Signal mutability boundary (frozen vs mutable fields):**

FROZEN fields (detection payload -- never modified after creation):
- `id`, `type`, `project`, `tags`, `created`, `durability`
- `severity` (initial sensor assessment), `signal_type`, `signal_category`
- `phase`, `plan`, `polarity`, `source`
- `occurrence_count`, `related_signals`
- `runtime`, `model`, `gsd_version`
- `evidence.supporting` (initial), `evidence.counter` (initial)
- `confidence` (initial), `confidence_basis` (initial)
- `recurrence_of`

MUTABLE fields (lifecycle -- modified by authorized agents):
- `lifecycle_state`, `lifecycle_log`
- `triage.*` (decision, rationale, priority, by, at, severity_override)
- `remediation.*` (status, resolved_by_plan, approach, at)
- `verification.*` (status, method, evidence_required, at)
- `updated` (timestamp, tracks most recent lifecycle change)
- `status` (active/archived -- set to archived on invalidation)

**Severity disagreement handling:** `triage.severity_override` records disagreement between the sensor's initial severity assessment and the triage agent's assessment. The original `severity` field (frozen) preserves the sensor's view; `triage.severity_override` captures the triage agent's view. The `severity_conflict_handling` project setting determines which takes precedence for downstream behavior.

**Enforcement:** The mutability boundary is enforced by agent instructions (agent specs define which fields each agent may modify), not by file system permissions. Optional validation warning in gsd-tools.js may be added in future phases.

**Archival:**
- Set `status: archived` in frontmatter
- Archived entries remain in their original location (no file moves)
- Archived entries are excluded from the index
- Archival is manual (agent or user decision), not automated

**Retrieval tracking (optional):**
- `retrieval_count` and `last_retrieved` may be updated when agents read entries
- These fields exist for future pruning design -- no automated decisions based on them yet

## 11. Durability Classes

| Class | Durability | Description | Example |
|-------|-----------|-------------|---------|
| `workaround` | Fragile | Tied to external bugs or limitations; likely to become irrelevant when the underlying issue is fixed | "Use --legacy-peer-deps because npm 9.x has a resolution bug" |
| `convention` | Durable | Project-specific patterns; relevant while the project exists and follows this approach | "This project uses barrel exports for all module directories" |
| `principle` | Highly durable | General wisdom applicable across projects and time | "Always validate both access and refresh token expiry before attempting token refresh" |

**Selection guidance for agents:**
- If the knowledge is tied to a specific version, bug, or external limitation: `workaround`
- If the knowledge is a team/project pattern or convention: `convention`
- If the knowledge would apply to any project in any context: `principle`

## 12. Concurrency

**Write safety:**
- Entry files have unique IDs (type prefix + date + slug) preventing write collisions
- Parallel agents writing entries simultaneously write to different files
- No lock files are needed for entry creation

**Index safety:**
- Index rebuild writes to a temporary file first, then renames atomically
- If two agents rebuild the index simultaneously, last-write-wins (both produce valid indexes)
- Index is idempotent -- rebuilding from the same files always produces the same result

**Read safety:**
- Reading entries is always safe (files are immutable or update-in-place with atomic writes)
- Retrieval tracking updates are best-effort -- a missed increment is acceptable

## 13. Promotion Model

**Project to global promotion:**
1. Change `project` field in frontmatter from `{project-name}` to `_global`
2. Move the file from `{type}/{project-name}/` to `{type}/_global/`
3. Rebuild index to reflect the change

**Global entry availability:**
- Global entries (`project: _global`) are available to all projects
- Agents query the index filtering by project name OR `_global` to find relevant entries
- Cross-project queries omit the project filter to search all entries

---

*Specification version: 2.0.0*
*Created: 2026-02-02*
*Updated: 2026-02-28*
*Phase: 01-knowledge-store (base), 31-signal-schema-foundation (lifecycle, epistemic, mutability, positive signals), 34-signal-plan-linkage (resolves_signals, verification_window, recurrence)*
