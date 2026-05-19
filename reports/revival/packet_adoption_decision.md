# Packet Adoption Decision — ScholarDoc Revival v5.2 → v5.2-rev1

**Date:** 2026-05-19
**Executor:** Claude (Opus 4.7, /goal mode, packet PROMPT_01)
**Packet under adoption:** `.planning/revival-packet/` (audited at v5.2; revised to v5.2-rev1)
**Audit input:** `reports/revival/packet_audit.md` (2026-05-19, verdict ACCEPT_WITH_REVISIONS)
**Spec:** `.planning/revival-packet/prompts/00_package/PROMPT_01_ADOPT_OR_REVISE_PACKET.md`

---

## 1. Final status

**READY** — packet version `v5.2-rev1` after this prompt.

The packet has been revised in place per the audit's §7 revision proposal. All fifteen revisions (R7.1–R7.15) were applied without refusal. Every touched task spec was re-walked against the audit's executable-cold lens (§4 below) and passes better than before. The 00_package gate exits READY; downstream prompts (`01_audits/`, `02_orchestrators/`, `03_implementation/`, `04_verification/`) are unblocked subject to their stated prerequisites.

## 2. Verdict carried in from audit

**ACCEPT_WITH_REVISIONS** (per `reports/revival/packet_audit.md` §1).

The audit found the packet's architecture sound and its post-falsificationist epistemology defensible, but named structural gaps (Phase 1.2 absent, Tier 0 repairs unscoped, executor undeclared, non-negotiables un-trigger-ed, task specs not executable-cold) that a single revision pass could close. The verdict was not downgraded by anything encountered during adoption; no audit-internal inconsistencies were discovered; no addendum was added to `packet_audit.md`.

## 3. Revisions applied

All fifteen revisions in the audit's §7 worklist were applied. None refused.

| # | File(s) | Change | Audit acceptance criterion | Did it pass? |
|---|---|---|---|---|
| R7.1 | `task_specs/TASKSPEC_PHASE_1_2_RECONCILIATION.md` (new); INDEX.md, README.md, `context/05_known_audit_findings.md` (cross-refs) | New task spec; names ABSORBS / DEFERS_TO / SUPERSEDES / IGNORES per Phase 1.2 plan (01.2-01..04 existing, R6/R7/R8 proposed). | "Reconciliation doc names every 01.2-0X plan with a disposition. No plan is left undecided." | PASS — spec enumerates seven plans, requires exactly one disposition per. Cross-ref bullet added to INDEX.md and README.md "Phase 1.2 awareness" section. |
| R7.2 | `task_specs/TASKSPEC_TIER_0_REPAIRS.md` (new); `prompts/03_implementation/IMPL_TIER_0_REPAIRS.md` (new); INDEX.md (cross-ref) | New task spec naming R1–R5 from May 1 audit `06-interventions.md`; new IMPL prompt; INDEX reference. | "All five repairs appear with named files and named outcomes." | PASS — R1 through R5 each have trigger, change, evidence-PASS, evidence-FAIL, refusal-allowed clauses. |
| R7.3 | `context/01_local_workspace.md` | Replaced sibling list with verified-existing siblings table and confirmed-missing dispositions (RENAMED_OR_ABSORBED / NEEDS_CREATION / OUT_OF_SCOPE / RENAMED_TO_PHILOGRAPH_MCP). | "Running `for d in <every-name>; do test -d ~/workspace/projects/$d ...` returns a result reconcilable with the list." | PASS — list now matches 2026-05-19 `ls ~/workspace/projects/` output; missing repos explicitly dispositioned. |
| R7.4 | README.md "Key positions"; `context/00_nonnegotiables.md` #9; `context/04_project_context.md` Philograph definition | "Philograph (planned / aspirational)" framing; named current downstream proxies (philo-rag-simple, philograph-mcp, Anki, RAG, annotation). | "Every mention of Philograph either names a verifiable artifact or is explicitly marked as planned/aspirational." | PASS — three loci updated; Philograph now marked as planned in README and #9; project_context.md carries the reality-anchored framing. |
| R7.5 | `context/11_executor_contract.md` (new) | Declares Claude Code as required executor; lists required capabilities; gives degradation contract; specifies `@`-reference resolution rule. | "Reading this file allows an executor of any provenance to verify whether it can run the packet." | PASS — capability table + degradation table + resolution rule + executor-verification checklist all present. |
| R7.6 | All 21 files under `prompts/` that use `@`-syntax (option (b) chosen per audit's "Choose (b) for revision cost"; GOAL_LAUNCHER.md already uses fully-qualified paths and was not modified) | One-line "Note: `@`-references are packet-relative" header on each prompt, citing `context/11_executor_contract.md`. | "A cold executor invoked from repo-root cwd can resolve every `@`-reference in every prompt without prior instruction beyond reading the prompt." | PASS — every prompt under `prompts/00_package/`, `prompts/01_audits/`, `prompts/02_orchestrators/`, `prompts/03_implementation/`, `prompts/04_verification/` carries the note; resolution rule is now self-locating. |
| R7.7 | `TASKSPEC_02_GSD_FEASIBILITY_AUDIT.md`, `TASKSPEC_03_REPO_SPLIT_AUDIT.md`, `TASKSPEC_04_DOC_TRUTH_REPAIR.md`, `TASKSPEC_05_PHASE_1_5_SCAFFOLD.md`, `TASKSPEC_06_STRICT_VALIDATION_SPIKE.md`, `TASKSPEC_07_SOURCE_TO_CLEAN_MAPPING_SPIKE.md`, `TASKSPEC_08_HARNESS_LANDSCAPE_RESEARCH.md` | Added `## Acceptance criteria` + `## Failure modes` sections; added decision-criterion rubrics (TASKSPEC_03 4×8 = 32-cell rubric; TASKSPEC_06 three-verdict criterion; TASKSPEC_07 per-transformation four-option verdict; TASKSPEC_05 named required content per file). TASKSPEC_02 added GSD-verdict table and harness-timing table. TASKSPEC_04 named the eight docs. TASKSPEC_08 named prerequisites and 3-tier recommendation contract. | "Each amended spec contains a section titled '## Acceptance criteria' with at least three bulletted criteria; each criterion is testable." | PASS — all seven specs now carry both sections; per-spec re-walk in §4 below confirms each passes executable-cold better than before. |
| R7.8 | `context/12_scope_guard.md` (new) | Packet-level "do not change" list rolling up per-task-spec exclusions. | "The 'do not change' lists scattered across task specs roll up to a single packet-level list." | PASS — 14-item exclusion table + cross-cutting guard + exception rule. |
| R7.9 | `AUTHORITY.md` (new) | Declares Zone A (project-owned, authoritative) vs Zone B (packet-owned, advisory); adoption mechanisms (direct adoption / explicit citation / phase plan / ADR); conflict-resolution table. | "A reader can resolve a hypothetical conflict between a packet report and `.planning/STATE.md` by reading this doc alone." | PASS — conflict table covers five named cases; "When the packet *does* win" section bounds Zone B authority. |
| R7.10 | `context/13_failure_recovery.md` (new) | Three failure types (partial / refused / hard block); `STATUS:` line convention; `BLOCKED.md` sentinel; resumption protocol; required actions per failure mode. | "A cold executor can read this doc and know what to write when its predecessor produced an incomplete report." | PASS — required-action table covers six failure modes; verifier-behavior rule prevents silent consumption. |
| R7.11 | `context/00_nonnegotiables.md` | Added per-rule revision triggers (or explicit "Unconditional" tags) for all thirteen non-negotiables. #12 (GSD-2) restored to the May 1 audit's conditional form ("M2 start, after a spike succeeds and v2.81+ ships clean"). | "Each non-negotiable has either a revision trigger or an explicit 'unconditional, no trigger' tag with reasoning." | PASS — 13/13 entries carry one or the other. |
| R7.12 | `LIFECYCLE.md` | Added "## Status block", "## Status transition firing conditions" (covering all five transitions), and "## Packet revision triggers" (eight named triggers). Version bumped to v5.2-rev1. | "A reader can decide whether the packet is currently valid by checking the listed triggers against project state." | PASS — eight-trigger list lets a reader audit packet validity in one pass; re-audit checklist names the next-revision protocol. |
| R7.13 | `templates/verification_report_template.md` | Rewrote template to carry verification logic per section — Verdict criteria, Checklist with per-item PASS/FAIL evidence guidance, Methodology self-test. Updated `VERIFY_IMPLEMENTATION_OUTPUT.md`, `VERIFY_ORCHESTRATOR_REPORT.md`, `VERIFY_SPIKE_OUTPUTS.md` to use the substantiated template plus prompt-specific verification steps. | "A verifier executing VERIFY_IMPLEMENTATION_OUTPUT can produce a PASS/FAIL with reasoned evidence; the prompt is no longer a heading filler." | PASS — template now bears the verification logic; verification prompts add prompt-specific steps (orchestrator paraphrase check, spike artifact check). |
| R7.14 | `context/14_branch_state.md` (new); cross-ref in `context/05_known_audit_findings.md` | Names current branch `revival/2026-05-audit-and-reset` and commits-overlap table (c2a82cb, 72dd5ab, 6258d1c, b0ca1d7, 6dbea41); declares packet relationship as parallel-complementary. | "A reader unfamiliar with the branch can locate the prior work and understand whether the packet is duplicating it." | PASS — commits-vs-packet-work table is explicit; verification command included. |
| R7.15 | `context/15_rival_approaches.md` (new); README "Key positions" cross-ref | Names "packet-light revival" (R1–R5 + one-page Phase 1.5 plan + start annotating) and "defer to project-owned Phase 1.2 entirely" as rivals; each with reopen triggers. | "The packet now shows its rival rather than foreclosing it." | PASS — two rivals named with triggers; README "Key positions" updated. |

## 4. Operationalizability re-walk (touched specs)

The audit's §6 table marked TASKSPEC_03, 04, 05 as failing executable-cold and TASKSPEC_02, 06, 07, 08 as PARTIAL. Each is re-walked below as a fresh agent would, against the v5.2-rev1 text.

| Spec | Was | Now | Specific change that closed the gap |
|---|---|---|---|
| TASKSPEC_00 | PASS | PASS | Unchanged (was the only original PASS). |
| TASKSPEC_01 | PARTIAL | PARTIAL | **Not addressed in this revision pass** — the audit's §7 R7.7 list omits TASKSPEC_01. Per `reports/revival/packet_audit.md` §6, the gap was "what to do if a sibling repo doesn't exist." That gap is now partially closed by `context/01_local_workspace.md` (which dispositions every named missing sibling) — the spec inherits the disposition from context. Residual ambiguity: the spec still does not name what "passing" looks like for the audit overall. Flagged in §9 as open question OQ-1. |
| TASKSPEC_02 | PARTIAL | PASS | Distinguishing-evidence table per verdict + harness-timing verdict added; acceptance criteria require OBSERVED commands and explicit R1-status check. |
| TASKSPEC_03 | NO | PASS | 4×8 rubric forces scoring; verdict threshold (≥3-point margin OR named tie-breaker, else default D) is unambiguous. |
| TASKSPEC_04 | NO | PASS | Named eight docs to reconcile; named reconciliation target (`.planning/audit/2026-05-01/00-SYNTHESIS.md` + branch commits); named coordination with Phase 1.2-01; acceptance criteria require per-file status entry. |
| TASKSPEC_05 | NO | PASS | Each of the six required files now has explicit required-content list; empty-stub failure mode is named explicitly. |
| TASKSPEC_06 | PARTIAL | PASS | Three-verdict decision criterion with named distinguishing evidence (typo catch rate threshold, false-positive rate < 10%, perf overhead < 50ms). |
| TASKSPEC_07 | PARTIAL | PASS | Per-transformation acceptance criterion (1: precision/recall + false-positive case; 2: ≥3 repetition + non-repetition; 3: marker + non-marker; 4: hyphenated + intentional-hyphen; 5: typo + in-vocab-non-correction). Per-transformation four-option verdict + aggregate decision. |
| TASKSPEC_08 | PARTIAL | PASS | Five prerequisites named with `STATUS:` enforcement; 3-tier recommendation contract (primary / secondary / drop); 6-month revision trigger; web-access degradation per `context/11_executor_contract.md`. |
| TASKSPEC_PHASE_1_2_RECONCILIATION | (new) | PASS | New spec; built with acceptance criteria and failure modes from the start. |
| TASKSPEC_TIER_0_REPAIRS | (new) | PASS | New spec; per-repair (R1–R5) acceptance criteria and failure modes; refusal-allowed clause for R1's user-WIP edge case. |

**Summary:** 9/11 specs pass cold; 0 fail cold; TASKSPEC_01 remains PARTIAL (out-of-scope for this revision pass, residual ambiguity flagged as OQ-1).

No spec regressed. Every touched spec passes the audit's executable-cold lens better than its pre-revision baseline.

## 5. Revisions refused

**None.** All fifteen revisions were applied as proposed in the audit's §7. The two named refusal opportunities (R7.6 option (a) vs (b); R7.15) were resolved by adoption, not refusal:

- **R7.6:** Option (b) — packet-relative `@`-refs with a one-line header note — was chosen per the audit's "Choose (b) for revision cost" recommendation. GOAL_LAUNCHER.md was left unchanged because it already uses fully-qualified `@.planning/revival-packet/...` paths at the top level (where `/goal` text is pasted).
- **R7.15:** The rival approach was specified concretely enough (Rival 1: packet-light = Tier 0 repairs + one-page Phase 1.5 plan + start annotating; Rival 2: defer to project-owned Phase 1.2 entirely) that no refusal was warranted.

## 6. Restructure delta

The verdict was ACCEPT_WITH_REVISIONS, not RESTRUCTURE_PACKET. The packet's architecture (00_package gate → audits → orchestrators → implementations → verification → synthesis) is unchanged. The delta is additive and clarifying:

### Files added (9)

- `.planning/revival-packet/task_specs/TASKSPEC_PHASE_1_2_RECONCILIATION.md`
- `.planning/revival-packet/task_specs/TASKSPEC_TIER_0_REPAIRS.md`
- `.planning/revival-packet/prompts/03_implementation/IMPL_TIER_0_REPAIRS.md`
- `.planning/revival-packet/context/11_executor_contract.md`
- `.planning/revival-packet/context/12_scope_guard.md`
- `.planning/revival-packet/context/13_failure_recovery.md`
- `.planning/revival-packet/context/14_branch_state.md`
- `.planning/revival-packet/context/15_rival_approaches.md`
- `.planning/revival-packet/AUTHORITY.md`

### Files modified (21)

- `.planning/revival-packet/INDEX.md` (v5.2-rev1 notes + adopt-status banner)
- `.planning/revival-packet/README.md` (Key positions reality-anchored; Phase 1.2 awareness; rival mention)
- `.planning/revival-packet/LIFECYCLE.md` (status block, transition firing conditions, packet revision triggers, version bump)
- `.planning/revival-packet/context/00_nonnegotiables.md` (revision triggers added to all 13)
- `.planning/revival-packet/context/01_local_workspace.md` (sibling list reality-anchored)
- `.planning/revival-packet/context/04_project_context.md` (Philograph framing)
- `.planning/revival-packet/context/05_known_audit_findings.md` (Phase 1.2 awareness + branch state cross-ref)
- `.planning/revival-packet/templates/verification_report_template.md` (substantiated with verification logic)
- All 7 of `TASKSPEC_02` through `TASKSPEC_08` (acceptance criteria + failure modes + decision criteria added)
- All 21 prompt files under `prompts/00_package/`, `prompts/01_audits/`, `prompts/02_orchestrators/`, `prompts/03_implementation/`, `prompts/04_verification/` (packet-relative `@`-ref note; some also picked up new context-file references). Exception: `GOAL_LAUNCHER.md` unchanged (already uses fully-qualified paths).

### Files deleted

None.

## 7. Placement decision

**Recommendation (per audit §8): Keep in `.git/info/exclude` for now; relocate to a sibling staging path at archive time.**

### Current state (no change required by this prompt)

- Packet stays at `.planning/revival-packet/`.
- `.git/info/exclude` continues to list `.planning/revival-packet/`.
- No commit; no `.gitignore` change.

### Exact `git` action the user should take next

**No `git add` or `git commit` for the packet itself.** The packet remains intentionally outside repo history at this stage. Per audit §8:

> Committing the packet now mixes operational governance (status changes, version bumps, in-place edits) with code/test history. The packet expects frequent in-place editing (per PROMPT_01); commits would churn.

**`reports/revival/` is a different question.** The audit and adoption reports (`reports/revival/packet_audit.md`, `reports/revival/packet_adoption_decision.md`) are operational artifacts the user may want preserved. The user should decide whether to:

- **Option P-A (recommended for the audit + adoption pair):** Leave `reports/revival/` outside repo history for now (its parent directory is not committed; the contents are tracked only locally). Revisit at next milestone.
- **Option P-B:** Add `reports/revival/` to `.git/info/exclude` explicitly to match the packet's exclusion convention. *Proposed* `.git/info/exclude` change (the user applies, not this prompt):
  ```
  # Revival packet output reports (audit + adoption + downstream verification)
  reports/revival/
  ```
- **Option P-C:** Commit the audit + adoption reports as project artifacts under `reports/revival/` (would require a single `git add reports/revival/packet_audit.md reports/revival/packet_adoption_decision.md` + commit). This option is *not* recommended — the audit's evidentiary style is conversational and would not benefit from being in `main`'s history alongside source.

This prompt does not apply any of P-A/P-B/P-C; the user picks. Per audit §8 and per the packet's non-negotiable on git operations, the placement decision belongs to the user.

### At packet adoption (now)

- No move.
- `LIFECYCLE.md` status block reads `AUDITED_ACCEPTED`, version `v5.2-rev1`.

### At distillation (future trigger: adopted outputs moved to `.planning/phases/`, `docs/adr/`, etc.)

- Move packet to `.planning/revival-packet-archive/v5.2-rev1/` (in-repo) per audit §8 (default), unless packet size or out-of-repo policy dictates the sibling-workspace location.

### At supersession (post-Milestone 1)

- Archive, do not delete (per `LIFECYCLE.md`).
- Populate `templates/packet_archive_manifest_template.yaml` into `archive_manifest_v5.2-rev1.yaml`.

## 8. Lifecycle status

`LIFECYCLE.md` now reads:

```
status: AUDITED_ACCEPTED
version: v5.2-rev1
audited: 2026-05-19
adopted: 2026-05-19
prior_status: STAGED_UNAUDITED
audit_report: reports/revival/packet_audit.md
adoption_decision: reports/revival/packet_adoption_decision.md
```

### Next revision triggers (from `LIFECYCLE.md` "Packet revision triggers" section)

The packet is due for re-audit when any of the following fires:

1. `revival/2026-05-audit-and-reset` merges to `main`.
2. `.planning/audit/2026-05-01/00-SYNTHESIS.md` is amended.
3. More than two task specs need rewriting to accommodate a new finding.
4. Milestone 1 closes.
5. A verification pass downgrades a prior verdict.
6. A non-negotiable's revision trigger fires (per `context/00_nonnegotiables.md`).
7. Either rival approach's reopen-trigger fires (per `context/15_rival_approaches.md`).
8. The user explicitly reopens a packet position.

## 9. What an autonomous agent should run next

The packet is now operational. An autonomous agent picking it up should sequence as follows:

1. **First, run** the local workspace baseline audit (`prompts/01_audits/PROMPT_LOCAL_WORKSPACE_BASELINE_AUDIT.md` → `TASKSPEC_01`). This anchors all subsequent prompts to the live tree.
2. **In parallel, run** the May 1 audit inheritance pass (`prompts/01_audits/PROMPT_MAY_1_AUDIT_INHERITANCE.md`) — produces `reports/revival/may_1_audit_critical_inheritance.md` classifying findings ACCEPT / REVISE / PARK / REJECT / UNKNOWN.
3. **Then, run** the Phase 1.2 reconciliation (`TASKSPEC_PHASE_1_2_RECONCILIATION.md` — needs a dedicated prompt; one can be added if the orchestrator pattern is not preferred). This must complete before `TASKSPEC_04_DOC_TRUTH_REPAIR.md` is invoked, to avoid Phase 1.2-01 drift.
4. **Then, run** the Tier 0 repairs implementation (`prompts/03_implementation/IMPL_TIER_0_REPAIRS.md` → `TASKSPEC_TIER_0_REPAIRS.md`). User commits each R1–R5 atomically after reviewing the produced diff.
5. **Then, run** the GSD feasibility audit (`prompts/02_orchestrators/ORCH_GSD_FEASIBILITY_AND_WORKFLOW_AUDIT.md` → `TASKSPEC_02`).
6. **Then, run** the repo split audit (`prompts/02_orchestrators/ORCH_REPO_SPLIT_ARCHITECTURE_AUDIT.md` → `TASKSPEC_03`) — needs subagent delegation per `context/11_executor_contract.md`.
7. **In parallel with #5–#6**, run the two design orchestrators (`ORCH_SCHOLARDOCUMENT_REQUIREMENTS_AND_DESIGN.md`, `ORCH_SCHOLARGT_SCHEMA_CRITICAL_REVIEW.md`).
8. **Then, run** the Phase 1.5 pilot annotation design (`ORCH_PHASE_1_5_PILOT_ANNOTATION_DESIGN.md`) and the synthetic simulator strategy (`ORCH_SYNTHETIC_SIMULATOR_STRATEGY.md`), noting that the latter must treat `synthetic_test_data` as planned-not-existing per `context/01_local_workspace.md`.
9. **Then, run** the Phase 1.5 scaffold implementation (`prompts/03_implementation/IMPL_PHASE_1_5_SCAFFOLD.md` → `TASKSPEC_05`), which now requires named content per file.
10. **Then, run** the two spikes (`IMPL_STRICT_VALIDATION_SPIKE.md` + `IMPL_SOURCE_TO_CLEAN_MAPPING_SPIKE.md`).
11. **Then, run** the doc-truth-repair (`IMPL_DOC_TRUTH_REPAIR.md` → `TASKSPEC_04`), coordinating with the reconciliation table from step 3.
12. **Then, run** the post-wave synthesis (`ORCH_POST_WAVE_SYNTHESIS.md`).
13. **Optionally last**, run the deferred harness landscape research (`ORCH_DEFERRED_HARNESS_LANDSCAPE_RESEARCH.md` → `TASKSPEC_08`) only if `TASKSPEC_02`'s harness-timing verdict is NOW or AFTER_PHASE_1_5 and all prerequisites are met.

Verification (`prompts/04_verification/VERIFY_*`) should be invoked at each step's completion. The audit verification (`VERIFY_PACKET_AUDIT.md`) is the canonical second-pass on this very audit, and is encouraged before deeper trust is placed in the §7 revision proposal.

### Prerequisites that must hold

- **Executor capability check.** The executor must read `context/11_executor_contract.md` and confirm subagent capability before invoking any `ORCH_*` prompt.
- **Branch awareness.** Before any prompt runs, confirm `context/14_branch_state.md` matches the live state. If the branch has moved, the packet needs a revision trigger fire.
- **Audit verification (optional but recommended).** Run `VERIFY_PACKET_AUDIT.md` as a second-pass on `reports/revival/packet_audit.md` before downstream prompts trust its verdict.
- **Failure-recovery awareness.** Every prompt invocation must check upstream inputs for `STATUS:` markers per `context/13_failure_recovery.md`.

## 10. Open questions surfaced during adoption

Items the audit did not anticipate, surfaced while applying revisions. Each with a recommended next step.

| # | Item | Recommended next step |
|---|---|---|
| OQ-1 | TASKSPEC_01 was not in the audit's §7 R7.7 list, so it remains PARTIAL after this revision pass (audit §6 listed it as PARTIAL, gap: "what passing looks like; what to do if a sibling repo doesn't exist; what 'audit' means beyond `git status`"). The reality-anchored `context/01_local_workspace.md` partially closes the second gap; the first and third remain. | If a future revision pass is triggered, fold TASKSPEC_01 into R7.7-equivalent revisions. For now, the prompt is runnable but produces shallower output than a fully-specified spec would. |
| OQ-2 | The audit did not name a dedicated prompt for `TASKSPEC_PHASE_1_2_RECONCILIATION.md`. The spec exists, but the orchestrator/implementation prompt is absent. | Either (a) the user adds `prompts/02_orchestrators/ORCH_PHASE_1_2_RECONCILIATION.md` or (b) the reconciliation is run as a one-shot read-write task without a packet prompt. Option (b) is acceptable per packet design principles (the spec is the contract; a prompt is convenience). |
| OQ-3 | The audit's R7.13 substantiated the verification template but did not update `VERIFY_PACKET_AUDIT.md` (which was already substantive). I left it unchanged except for the @-ref note. If the substantiated template's evidence-guidance section diverges from VERIFY_PACKET_AUDIT's V1–V9, future verifiers may double-up. | Recommend: when re-auditing the packet, reconcile the template's checklist with VERIFY_PACKET_AUDIT's V1–V9. |
| OQ-4 | The placement decision (§7) presents the user with three options for `reports/revival/`. No option is applied. | User decides P-A / P-B / P-C at adoption time. The packet's authority does not extend to that decision. |
| OQ-5 | `context/14_branch_state.md` names the current branch but does not declare a re-test policy for the named commit list (`c2a82cb`, `72dd5ab`, etc.). If those commit hashes age out (rebases, force-pushes by the user), the file becomes stale silently. | Add a `git log --oneline` re-run command to the file's "How to verify this file is current" section, and consider hash-stability via tags if the branch persists past a month. Recommended for the next revision pass. |

## Appendix A: Files touched (full list)

### New files

- `.planning/revival-packet/AUTHORITY.md`
- `.planning/revival-packet/context/11_executor_contract.md`
- `.planning/revival-packet/context/12_scope_guard.md`
- `.planning/revival-packet/context/13_failure_recovery.md`
- `.planning/revival-packet/context/14_branch_state.md`
- `.planning/revival-packet/context/15_rival_approaches.md`
- `.planning/revival-packet/task_specs/TASKSPEC_PHASE_1_2_RECONCILIATION.md`
- `.planning/revival-packet/task_specs/TASKSPEC_TIER_0_REPAIRS.md`
- `.planning/revival-packet/prompts/03_implementation/IMPL_TIER_0_REPAIRS.md`
- `reports/revival/packet_adoption_decision.md` (this file)

### Modified files

- `.planning/revival-packet/INDEX.md`
- `.planning/revival-packet/README.md`
- `.planning/revival-packet/LIFECYCLE.md`
- `.planning/revival-packet/context/00_nonnegotiables.md`
- `.planning/revival-packet/context/01_local_workspace.md`
- `.planning/revival-packet/context/04_project_context.md`
- `.planning/revival-packet/context/05_known_audit_findings.md`
- `.planning/revival-packet/templates/verification_report_template.md`
- `.planning/revival-packet/task_specs/TASKSPEC_02_GSD_FEASIBILITY_AUDIT.md`
- `.planning/revival-packet/task_specs/TASKSPEC_03_REPO_SPLIT_AUDIT.md`
- `.planning/revival-packet/task_specs/TASKSPEC_04_DOC_TRUTH_REPAIR.md`
- `.planning/revival-packet/task_specs/TASKSPEC_05_PHASE_1_5_SCAFFOLD.md`
- `.planning/revival-packet/task_specs/TASKSPEC_06_STRICT_VALIDATION_SPIKE.md`
- `.planning/revival-packet/task_specs/TASKSPEC_07_SOURCE_TO_CLEAN_MAPPING_SPIKE.md`
- `.planning/revival-packet/task_specs/TASKSPEC_08_HARNESS_LANDSCAPE_RESEARCH.md`
- `.planning/revival-packet/prompts/00_package/PROMPT_00_AUDIT_THIS_PACKET.md`
- `.planning/revival-packet/prompts/00_package/PROMPT_01_ADOPT_OR_REVISE_PACKET.md`
- `.planning/revival-packet/prompts/01_audits/PROMPT_LOCAL_WORKSPACE_BASELINE_AUDIT.md`
- `.planning/revival-packet/prompts/01_audits/PROMPT_MAY_1_AUDIT_INHERITANCE.md`
- `.planning/revival-packet/prompts/02_orchestrators/ORCH_DEFERRED_HARNESS_LANDSCAPE_RESEARCH.md`
- `.planning/revival-packet/prompts/02_orchestrators/ORCH_GSD_FEASIBILITY_AND_WORKFLOW_AUDIT.md`
- `.planning/revival-packet/prompts/02_orchestrators/ORCH_PHASE_1_5_PILOT_ANNOTATION_DESIGN.md`
- `.planning/revival-packet/prompts/02_orchestrators/ORCH_POST_WAVE_SYNTHESIS.md`
- `.planning/revival-packet/prompts/02_orchestrators/ORCH_REPO_SPLIT_ARCHITECTURE_AUDIT.md`
- `.planning/revival-packet/prompts/02_orchestrators/ORCH_SCHOLARDOCUMENT_REQUIREMENTS_AND_DESIGN.md`
- `.planning/revival-packet/prompts/02_orchestrators/ORCH_SCHOLARGT_SCHEMA_CRITICAL_REVIEW.md`
- `.planning/revival-packet/prompts/02_orchestrators/ORCH_SYNTHETIC_SIMULATOR_STRATEGY.md`
- `.planning/revival-packet/prompts/03_implementation/IMPL_DOC_TRUTH_REPAIR.md`
- `.planning/revival-packet/prompts/03_implementation/IMPL_PHASE_1_5_SCAFFOLD.md`
- `.planning/revival-packet/prompts/03_implementation/IMPL_SOURCE_TO_CLEAN_MAPPING_SPIKE.md`
- `.planning/revival-packet/prompts/03_implementation/IMPL_STRICT_VALIDATION_SPIKE.md`
- `.planning/revival-packet/prompts/04_verification/VERIFY_IMPLEMENTATION_OUTPUT.md`
- `.planning/revival-packet/prompts/04_verification/VERIFY_ORCHESTRATOR_REPORT.md`
- `.planning/revival-packet/prompts/04_verification/VERIFY_PACKET_AUDIT.md`
- `.planning/revival-packet/prompts/04_verification/VERIFY_SPIKE_OUTPUTS.md`

### Files unchanged

- `.planning/revival-packet/PLACEMENT.md` (no change — extended via `AUTHORITY.md` rather than direct edit)
- `.planning/revival-packet/prompts/00_package/GOAL_LAUNCHER.md` (already uses fully-qualified `@`-paths)
- `.planning/revival-packet/task_specs/TASKSPEC_00_AUDIT_THIS_PACKET.md` (was the audit's own spec; left unchanged per audit's §1 acknowledgement that it passes cold)
- `.planning/revival-packet/task_specs/TASKSPEC_01_LOCAL_WORKSPACE_BASELINE_AUDIT.md` (not in §7 R7.7 list; flagged as OQ-1)
- All four files in `analysis_reference/`
- `checklists/PACKET_AUDIT_CHECKLIST.md`
- `templates/decision_justification_template.md`, `templates/packet_archive_manifest_template.yaml`

### Files outside the packet that the adoption *recommended* (but did not apply)

- `.git/info/exclude` — optional addition of `reports/revival/` per §7 Option P-B (user applies if desired).

No changes were made to project source, tests, `scholardoc/`, `scholargt/`, `ground_truth/`, or any `.planning/` file outside `.planning/revival-packet/`. No `git commit / push / reset / stash / clean` was run. No `.git/info/exclude` modification was applied.

---

**End of adoption decision.** Per `LIFECYCLE.md`, the packet status is now `AUDITED_ACCEPTED` at version `v5.2-rev1`, and the user is unblocked to invoke any downstream prompt per the sequencing in §9.
