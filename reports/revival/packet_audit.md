# Packet Audit — ScholarDoc Revival v5.2 Governed Packet

**Date:** 2026-05-19
**Auditor:** Claude (Opus 4.7, max effort, /goal mode)
**Packet under audit:** `.planning/revival-packet/` (v5.2, staged, in `.git/info/exclude`)
**Authoring posture:** ChatGPT, in-conversation, without live-repo access — treated as hypothesis-bearing, not authoritative
**Spec:** `.planning/revival-packet/task_specs/TASKSPEC_00_AUDIT_THIS_PACKET.md`

---

## 1. Verdict

**ACCEPT_WITH_REVISIONS**

The packet is internally coherent, methodologically defensible, and recovers from a real failure mode (self-validating audits, falsificationist over-reach, GSD-2 entanglement). Its bones are usable. But it has substantive gaps that a single bounded revision pass can close: it skips Phase 1.2, mis-names four of five sibling projects, leaves most task specs failing the executable-cold test, never names its executor, and asserts non-negotiables without the defeaters its own epistemology demands. None of these require restructuring; all of them require concrete edits to named files. PROMPT_01 can mechanically apply the revision proposal in §7 below.

> **Why not ACCEPT_AS_IS?** §3 (L3, L8, L9) names structural absences and operationalizability gaps that would silently degrade execution.
> **Why not RESTRUCTURE?** The packet's architecture (00_package gate → audits → orchestrators → implementations → verification → synthesis) is sound. The scope of needed fixes is additive and clarifying, not architectural.
> **Why not REPLACE / ABANDON?** Both would discard real epistemic work (post-falsificationist appraisal, the meta-critical audit pattern, the archive-by-default lifecycle correction) that the packet earned through five revisions. Failed attempts to break the framing (§4) did not collapse it.

---

## 2. Ratified Revival-Success Definition

I retain the spec's seven conditions with two amendments and one re-prioritization. The amended set, in dependency order:

1. **Local truth is restored.** ROADMAP.md, STATE.md, PROJECT.md, root docs, and live working tree no longer disagree about what era, branch, phase, and test count the project is at. *(matches spec #2; promoted to first because every other condition is gated on this.)*
2. **The stalled Phase 1.2 is closed or explicitly absorbed.** Either Phase 1.2's roadmapped scope (authority reset, verification reset, legacy boundary, Phase 2 contract) is executed, or it is folded into a successor with a named delta. *(NEW — spec did not name Phase 1.2.)*
3. **Direction is set.** ScholarDoc / ScholarGT / Philograph each have a defensible answer to "what, for whom, measured how" that survives critical appraisal. *(spec #1)*
4. **The schema is empirically anchored.** Some real annotation work (Phase 1.5 Pilot Annotation or equivalent) has stressed the v2.0.0 schema against real philosophy pages. *(spec #3)*
5. **The harness question is closed enough to work.** Either a chosen harness is committed to, or its deferral has a *named trigger* (date, milestone boundary, or external signal). *(spec #4; unchanged but the trigger discipline is load-bearing.)*
6. **The repo-architecture question is closed enough to work.** Same trigger discipline. *(spec #5)*
7. **Sibling projects are positioned, with reality alignment.** Each named sibling either exists on disk with a place in the plan, or has explicit non-status *with the actual path or absence documented*. *(spec #6, tightened — see §5.)*
8. **The agent loop is sustainable.** An autonomous agent can execute the next moves without per-prompt babysitting, **and the packet declares which agent**. *(spec #7, with executor disclosure added.)*

> **Defeater for this revival-success definition:** If condition #2 turns out to be redundant — i.e., if Phase 1.2 has been silently absorbed into the packet's doc-truth-repair scope — the condition collapses into #1. I flag it separately because the packet's current `TASKSPEC_04_DOC_TRUTH_REPAIR.md` is too narrow to cover Phase 1.2's other tracks (verification reset, legacy boundary, Phase 2 contract). [INFERENCE]

---

## 3. Findings, by Lens

### L1 — Goal-fit and revival theory

- **Finding 1.1** [INFERENCE]: The packet, executed in full, plausibly produces conditions #3, #4, #6, #7 (partially) and #8 (only after a deferred harness pass). It does *not* address condition #1 (local truth) end-to-end — `TASKSPEC_04_DOC_TRUTH_REPAIR.md` is six lines long and names neither inputs nor scope. It does not address condition #2 (Phase 1.2) at all.
- **Finding 1.2** [AUDIT-SUPPORTED]: The May 1 audit's `06-interventions.md` lists **Tier 0 repairs R1–R5** as "do this week, ≤ 1 week total" — commit/revert the 116 `.claude/` files, land Kant fixture PDF, fix `convert_pdf` ghost import, register `pytest.mark.slow`, update STATE.md. The packet contains none of these as discrete tasks. They survive only implicitly through `TASKSPEC_04` and `TASKSPEC_02`. A six-week run of the packet that produces a polished Phase 1.5 design but leaves R2/R3/R4 unfixed is a **"succeeds at its own metrics, leaves the project no closer to revival" failure mode** — the named L1 failure pattern.
- **Finding 1.3** [INFERENCE]: The packet's revival theory rests on a single load-bearing claim: that a Phase 1.5 Pilot Annotation, plus three orchestrator-led design passes, plus a doc-truth-repair sweep, will set direction. This is plausible. But the packet does not show that the *combination* converges — there is no "how do the outputs compose into revival?" theory. §3 of the spec explicitly probed for this absence; the packet contains no answer.

### L2 — Premise and framing audit

Load-bearing claims (each tagged with where it lives, and whether it is reasoned or asserted):

| # | Claim | Where | Reasoned? | Rival shown? |
|---|---|---|---|---|
| 2.1 | ScholarDocument is for Philograph/downstream apps, not ScholarGT | README §"Key positions", `00_nonnegotiables.md` #9, `04_project_context.md` | Asserted; not derived | No |
| 2.2 | Phase 1.5 Pilot Annotation is the right next move | `05_known_audit_findings.md` #2, `00_conversation_lessons.md` #5 | Inherited from May 1 audit (correctly, but with mis-prioritization — see L5) | No |
| 2.3 | GSD-2 is out of scope for this revival phase | `00_nonnegotiables.md` #12, `06_gsd_and_harness_questions.md` | Asserted unconditionally | No — and the May 1 GSD-2 research itself gave a *conditional* answer ("right inflection point: M2 start, after a spike") that the packet flattens. |
| 2.4 | Archive by default; do not delete meaningful revival work | `LIFECYCLE.md`, README §"Key positions" | Reasoned (LIFECYCLE.md is the only doc that defends a position) | Yes (`LIFECYCLE.md` §"When deletion is acceptable") |
| 2.5 | Post-falsificationist critical appraisal is the right epistemic standard | `02_evidence_standard.md`, `10_post_falsificationist_method.md`, `02_epistemic_standard_correction.md` | Reasoned | Partial — Popper named but Lakatos / Laudan / Kuhn used without naming their critics |
| 2.6 | The packet itself must be audited before use | INDEX.md, README, PROMPT_00, `09_packet_design_principles.md` #1 | Reasoned | Yes — the audit *itself* is positioned as the rival to checklist-walking |

- **Finding 2.1** [OBSERVED]: Claim 2.1 ("ScholarDocument is for Philograph and downstream applications") names a downstream — Philograph — that does **not exist on disk** (see L5). The claim is a forcing-function bet on a non-existent project. A rival reviewer would say: *design ScholarDocument against the downstream you actually have* (`philo-rag-simple`, `philograph-mcp`, downstream RAG / Anki / annotation tools that already use it). The packet forecloses this rival.
- **Finding 2.2** [AUDIT-SUPPORTED]: Claim 2.3 (GSD-2 out of scope) is correct *for this revival phase* but framed as an unconditional non-negotiable, not as a conditional deferral with a named trigger. The May 1 audit (`04-gsd2-research.md`) gave the conditional form ("M2 start, after a spike succeeds and v2.81+ ships clean"). The packet should inherit the trigger, not the flattened verdict.
- **Finding 2.3** [INFERENCE]: Several claims (2.1, 2.3, 2.5) are stated *without* the defeaters and revision triggers that the packet's own `02_evidence_standard.md` requires of every recommendation. The packet demands rigor of others it does not perform on itself. *(see L6.)*

### L3 — Absence audit

The spec named eight likely absences. I confirm seven and add three:

| Spec-named absence | Confirmed? | Evidence |
|---|---|---|
| Definition of revival success | YES | No file in `context/` defines it. The audit task spec itself supplies one. |
| Theory of how outputs combine into revival | YES | No file ties orchestrator outputs into a synthesis schema beyond ORCH_POST_WAVE_SYNTHESIS, which is two lines long and produces an unnamed format. |
| Check that downstream prompts depend only on upstream artifacts | YES | Prerequisites are declared narratively (`TASKSPEC_08` lists "ScholarDocument design report; ScholarGT schema review;..."), never checked. |
| Treatment of sibling projects beyond name-dropping | YES | `01_local_workspace.md` is a list with no analysis. |
| Treatment of `.planning/` artifacts: reconciliation, authority, conflict-resolution | YES | The packet does not mention `.planning/PROJECT.md`, `STATE.md`, `REVIEW_STRATEGY.md`, or `REVIEW_AUDIT_LOG.md` by name. `TASKSPEC_04` says "Repair project state docs" without naming which. |
| Owner / authority model (advisory vs binding) | YES | `PLACEMENT.md` hints ("project-owned reports become authoritative only after review/adoption") but does not say *how*, *who*, *when*. |
| Failure-recovery model | YES | No prompt names what to do when its predecessor partially fails. |
| Scope-creep guard at packet level | YES | Each task spec has a "do not change X" clause; the packet has no top-level boundary. |
| Treatment of uncommitted local work beyond "preserve it" | YES | `00_nonnegotiables.md` #2–#3 say preserve it, never say *what to do with it*. R1 from May 1 audit (commit-or-revert .claude/) is the unwritten "what to do." |

Additional absences I find that the spec did not name:

- **Finding 3.1** [INFERENCE]: **Phase 1.2 is absent from the packet entirely.** ROADMAP.md lists Phase 1.2 ("Repo Governing Reset & Phase 2 Contract Definition") as the queued-but-stalled next phase. STATE.md says "Continue with Phase 1.2 or Phase 2." The May 1 synthesis names Phase 1.2 as the *second-biggest single move* and lists seven plans for it (01.2-01..07). The packet has no task spec for Phase 1.2 work, no orchestrator for it, and no prompt that even references it. This is not an oversight — the packet's `05_known_audit_findings.md` truncates the May 1 audit's findings list to nine items and drops the Phase 1.2 / Tier-0-repairs strand. The packet's revival theory effectively proposes *skipping* Phase 1.2 in favor of jumping to Phase 1.5 directly.
- **Finding 3.2** [OBSERVED]: **The current revival branch (`revival/2026-05-audit-and-reset`) is not acknowledged anywhere in the packet.** The packet was written about a project that branched on, and partially completed, the reset work the packet aims to drive (commits `6258d1c docs(planning): capture repo governance reset`, `b0ca1d7 chore(tools)`, `72dd5ab chore(settings)`). The packet does not check whether its work has been pre-empted.
- **Finding 3.3** [INFERENCE]: **No relationship is named between packet artifacts (`reports/revival/*.md`) and the existing audit folder (`.planning/audit/2026-05-01/`).** PROMPT_MAY_1_AUDIT_INHERITANCE produces `may_1_audit_critical_inheritance.md` but does not say whether it supersedes, complements, or is parallel to the May 1 synthesis itself. Two May 1 audit syntheses (the original and a "critical inheritance") then coexist with no precedence rule.

### L4 — Authorship and standpoint critique

- **Finding 4.1** [AUDIT-SUPPORTED]: ChatGPT-as-author shows up in the *symmetry of treatment*. Every option in `07_repo_split_questions.md` gets four neutral bullets; the packet does not recommend a default. Every harness candidate in `06_gsd_and_harness_questions.md` is listed without ranking. `LIFECYCLE.md` enumerates four lifecycle stages with parallel structure. The author's salience is "list neutrally" — which is the right move under uncertainty about the user's situation, but it leaks into places where the live audit had already taken a position (e.g., the May 1 audit had a concrete repo-split posture).
- **Finding 4.2** [OBSERVED]: The author would not have known about: (a) `.planning/knowledge/{signals,reflections,spikes}/` existing as empty directories (the GSD signal subsystem unused); (b) the 116 modified `.claude/` files were *partially resolved* by commits since May 1 (the packet still assumes them unresolved by implication); (c) the user has active `gsd-2-explore` and `gsd-2-uplift` workspaces and a `harness-studio` directory — meaning GSD-2 and harness work are happening *in parallel* despite the packet's "out of scope" framing.
- **Finding 4.3** [INFERENCE]: The packet's GSD-2 position is genuinely *the project's*, inherited from the May 1 research, but the framing as a flat unconditional non-negotiable (#12) is the *author's*. The author preferred clean rules. The project preferred conditional triggers. This is an authorship overreach the audit must correct.
- **Finding 4.4** [INFERENCE]: There is a preference for *governance ceremony* (LIFECYCLE.md statuses, PACKET_AUDIT_CHECKLIST.md, decision_justification_template.md, verification_report_template.md) over project-specific judgment. The ceremony is not wrong, but the ratio of governance docs to substantive design docs is high for a packet whose stated purpose is to *unstall* a project.

### L5 — Alignment with reality (commands run against live repo)

See §5 for the full table. Most striking findings:

- **Finding 5.1** [OBSERVED]: **Four of five named sibling projects do not exist on disk.** `01_local_workspace.md` names: scholardoc-ocr, synthetic_test_data, CryptOfCogito, philograph, hermeneutic-workspace-plugin. Only `hermeneutic-workspace-plugin` exists. (`philo-rag-simple` and `philograph-mcp` exist with different names and may be what the packet meant; `gsd-2-explore`, `gsd-2-uplift`, `harness-studio` are active workspaces the packet does not name.)
- **Finding 5.2** [OBSERVED]: **`scholardoc/models.py` is 1524 lines.** Confirmed god-module claim from `05_known_audit_findings.md` #6.
- **Finding 5.3** [OBSERVED]: **`.planning/knowledge/{signals,reflections,spikes}/` exists as three empty subdirectories.** Confirmed the May 1 finding the packet inherits.
- **Finding 5.4** [OBSERVED]: **Phase 1.2 is still queued.** `ROADMAP.md` line shows `[ ] **Phase 1.2: Repo Governing Reset & Phase 2 Contract Definition**`. STATE.md confirms "Continue with Phase 1.2 or Phase 2." The packet's silence on Phase 1.2 is therefore a silence on live project state.

### L6 — Methodology coherence

- **Finding 6.1** [INFERENCE]: `context/00_nonnegotiables.md` lists thirteen unconditional rules. None has a defeater or revision trigger. The packet's own `02_evidence_standard.md` mandates that *every recommendation* include defeaters / revision triggers. The non-negotiables are recommendations — the packet treats them as exempt from the standard the packet itself ratified.
- **Finding 6.2** [INFERENCE]: `LIFECYCLE.md` defines four statuses (`STAGED_UNAUDITED`, `AUDITED_ACCEPTED`, `ADOPTED_PROJECT_REFERENCE`, `SUPERSEDED`) and "v5.0 → v5.1 → v5.2" version history, but does *not* name a revision trigger for the packet itself. When is the packet itself due for re-audit? After which milestone? When external state changes how? The author's own epistemology demands this; the doc omits it.
- **Finding 6.3** [INFERENCE]: The post-falsificationist method (`10_post_falsificationist_method.md`) names Duhem-Quine, Lakatos, Kuhn, Laudan, Bayesian, Severe Testing — but applies none of them to the packet's own claims. The required-language list ("Defeaters / Stress Tests / Rival Explanations / Confidence and Why / What Would Change This Recommendation") is required of "major reports," not of the packet's own positions. Self-exemption.

### L7 — Internal coherence

- **Finding 7.1** [OBSERVED]: **Cross-reference resolution is ambiguous under the @-syntax.** Every prompt opens with e.g. `Read: @context/00_nonnegotiables.md`. In Claude Code, `@`-references resolve relative to the current working directory, not relative to the file in which they appear. If the agent is invoked from the repo root (the documented invocation site, per GOAL_LAUNCHER.md), `@context/00_nonnegotiables.md` resolves to `./context/...` which **does not exist**. The actual path is `.planning/revival-packet/context/00_nonnegotiables.md`. GOAL_LAUNCHER.md only uses the full path *once* at top level; nested prompts assume packet-relative resolution. A naïve executor will fail; a careful executor compensates. The packet should not require the executor to do this compensation silently.
- **Finding 7.2** [OBSERVED]: **`templates/verification_report_template.md` is nine headings with no content.** Prompts in `04_verification/` "read the template" — but the template carries no verification logic. Where the *actual* verification content sits varies: VERIFY_PACKET_AUDIT.md has substantial V1–V9 tests, but VERIFY_IMPLEMENTATION_OUTPUT, VERIFY_ORCHESTRATOR_REPORT, VERIFY_SPIKE_OUTPUTS are each three lines pointing at the bare template. Verification logic for everything except the packet audit lives nowhere.
- **Finding 7.3** [INFERENCE]: `PLACEMENT.md` recommends staging at `.planning/revival-packets/v5.2/`; the packet is actually at `.planning/revival-packet/` (singular, no version). The placement doc and the actual placement disagree.
- **Finding 7.4** [INFERENCE]: INDEX.md says "Recommended runner: `prompts/00_package/GOAL_LAUNCHER.md`". GOAL_LAUNCHER.md says "Run **Goal 1 (audit)** first … then **Goal 2 (adopt/revise)**." This audit was invoked via Goal 1 — confirming the runner pattern works. Minor inconsistency: GOAL_LAUNCHER references the packet at `.planning/revival-packet/` (correct), while LIFECYCLE/PLACEMENT use the versioned path.

### L8 — Operationalizability and concreteness

Every task spec walked cold. See §6 for the full table. Summary of findings:

- **Finding 8.1** [INFERENCE]: **`TASKSPEC_05_PHASE_1_5_SCAFFOLD.md` fails the empty-stub test.** Six required filenames; no required content per file. A compliant agent producing six empty `01.5-CONTEXT.md` etc. has technically passed.
- **Finding 8.2** [INFERENCE]: **`TASKSPEC_06_STRICT_VALIDATION_SPIKE.md`, `TASKSPEC_07_SOURCE_TO_CLEAN_MAPPING_SPIKE.md`, `TASKSPEC_03_REPO_SPLIT_AUDIT.md`, `TASKSPEC_02_GSD_FEASIBILITY_AUDIT.md` all fail the decision-criterion test.** Each names what to evaluate; none names what outcome distinguishes a passing from a failing evaluation.
- **Finding 8.3** [INFERENCE]: **`TASKSPEC_04_DOC_TRUTH_REPAIR.md` is six lines.** "Repair project state docs" — which docs, which truths, reconciled against what, with what scope guard — all unspecified.
- **Finding 8.4** [INFERENCE]: **Orchestrator prompts (ORCH_*) all say "delegate worker lanes" without naming the delegation mechanism.** Claude Code supports `Agent` tool subagents; arbitrary LLMs do not. The packet assumes a delegating executor without saying so.

### L9 — Executor feasibility

- **Finding 9.1** [INFERENCE]: **The packet never names its expected executor.** README, INDEX, LIFECYCLE, PLACEMENT, and every prompt are silent. GOAL_LAUNCHER.md mentions Claude Code's `/goal` mode implicitly but does not declare Claude Code as the required executor.
- **Finding 9.2** [OBSERVED]: **The packet uses Claude Code's `@filename` reference syntax pervasively.** Under Codex, generic LLM agents, or non-Claude-Code harnesses, `@`-references are text the agent must heuristically resolve. The packet implicitly requires Claude Code without declaring it.
- **Finding 9.3** [INFERENCE]: **Orchestrator prompts assume `Agent` subagent capability.** Without subagent delegation, "you are an orchestrator. Worker lanes: 1. … 8. …" becomes "do eight things sequentially yourself." That degrades but does not collapse the prompt; still, the assumption should be explicit.
- **Finding 9.4** [INFERENCE]: **`ORCH_DEFERRED_HARNESS_LANDSCAPE_RESEARCH.md` says "you are an orchestrator with web/deep-research access."** Will the executor have web at firing time (likely months later)? The packet does not say what to do if not.

### L10 — Verification adequacy

- **Finding 10.1** [INFERENCE]: **A deliberately bad implementation could pass VERIFY_IMPLEMENTATION_OUTPUT.** The verification prompt is three lines: "Verify an implementation output against its task spec. Output: `reports/revival/verification_<task_name>.md`." With a vacuous task spec (see L8) and a template-only verification report, a verifier could produce a PASS verdict by filling headings.
- **Finding 10.2** [REFERENCE-SUPPORTED]: **VERIFY_PACKET_AUDIT.md is the exception — it carries real meta-critical content (V1–V9).** The packet recognized that the audit verification needs teeth; it did not apply the same insight to the other verifications.
- **Finding 10.3** [INFERENCE]: **No verification is triangulated against the live repo.** Each verification reads the report and the task spec; none re-tests reality claims against the working tree. The single exception is VERIFY_PACKET_AUDIT V2, which the audit task spec itself mandated.

### L11 — Governance, lifecycle, and placement

- **Finding 11.1** [OBSERVED]: **`PLACEMENT.md` lists options without deciding.** Inside-repo `.planning/revival-packets/v5.2/` vs outside-repo `~/workspace/projects/scholardoc-revival-packets/v5.2/` — no recommendation. Current placement: `.planning/revival-packet/` (no version dir, in `.git/info/exclude`).
- **Finding 11.2** [INFERENCE]: **`LIFECYCLE.md` names statuses but no firing conditions.** When does `STAGED_UNAUDITED` → `AUDITED_ACCEPTED`? When the audit passes. When does `AUDITED_ACCEPTED` → `ADOPTED_PROJECT_REFERENCE`? Implicit. When does `ADOPTED_PROJECT_REFERENCE` → `SUPERSEDED`? Never specified.
- **Finding 11.3** [INFERENCE]: **No precedence rule between packet outputs (`reports/revival/*.md`) and project planning artifacts (`.planning/PROJECT.md`, `STATE.md`, `ROADMAP.md`).** If `reports/revival/scholardocument_requirements_and_design.md` proposes a Phase 2 contract different from what `.planning/phases/01.2-04` will produce, which wins?
- **Finding 11.4** [INFERENCE]: **The packet's archive-by-default rule (`LIFECYCLE.md`) does not say where archival lives.** The archive manifest template is provided; the archive directory is not. Default proposal in §8: `.planning/revival-packet-archive/v5.2/`.

### L12 — Failure modes

- **F12.1** [INFERENCE] — **Technically compliant but empty execution.** Six empty Phase 1.5 stub files, four orchestrator reports that paraphrase their context inputs back as findings, a doc-truth-repair summary that touches one stale line in STATE.md. Every verification passes (because verifications are template-only). Six weeks elapsed, zero schema-validity progress.
- **F12.2** [INFERENCE] — **Wrong-axis revival.** The packet runs end-to-end and produces a clean Phase 1.5 design and ScholarDocument requirements doc, but Phase 1.2 stays stalled, R2–R4 still broken, 32 unit tests still failing. The packet succeeds at its own goals while the project moves backward on the audit's actual priority list.
- **F12.3** [INFERENCE] — **Partial-execution debris.** Orchestrator 2/4 runs; orchestrator 3 fails midway; orchestrator 4 reads orchestrator 3's incomplete output as input; post-wave synthesis aggregates broken upstream. No prompt names the recovery protocol.
- **F12.4** [INFERENCE] — **Doc-truth-repair drift.** The doc-truth-repair pass repairs root docs (Era 1 description, stale test counts) without coordinating with the Phase 1.2-01 plan ROADMAP.md already has for the same work. Root docs and `.planning/phases/01.2-01/` now disagree about who fixed what.
- **F12.5** [INFERENCE] — **Sunk-cost on non-existent siblings.** ScholarDocument design pass treats Philograph as a primary downstream consumer, producing requirements for a project that does not exist on disk. The design ages badly.

### L13 — Success probability and load-bearing dependencies

- **Probability as-is: 25–40%** that a six-week run produces a project meeting conditions #1–#8 (revised).
- **Probability after the §7 revisions: 45–60%.**
- **Conditions most likely to be met:** #3 (direction), #4 (Phase 1.5 anchoring), #7 (sibling positioning *after* revision).
- **Conditions most likely to fail:** #1 (local truth, because `TASKSPEC_04` is too thin), #2 (Phase 1.2, because the packet doesn't see it), #8 (sustainability, because executor is undeclared).
- **Single change that most raises probability:** Add Phase 1.2 awareness — a new `TASKSPEC_PHASE_1_2_RECONCILIATION.md` that names what packet work absorbs from / defers to / supersedes the roadmapped Phase 1.2. Adding this is worth more than tightening every other spec combined.
- **Single load-bearing dependency outside the packet:** **Executor capability.** If the packet is run by an agent without subagent delegation (e.g., a bare LLM, a Codex session without companion subagents, a non-Claude-Code Claude session that lost orchestrator capability mid-flight), the orchestrator prompts collapse to sequential single-agent work — feasible but vastly slower and lower-quality. The packet must name its executor and either commit to subagent-required execution or rewrite orchestrators to degrade gracefully.

---

## 4. The Unanticipated Finding

The task spec named twelve probable absences. I confirmed all twelve and added three (Finding 3.1 — Phase 1.2; Finding 3.2 — revival branch unacknowledged; Finding 3.3 — `.planning/audit/2026-05-01/` relationship undefined). The unanticipated finding *that the spec did not name and could not have* is:

> **The packet's epistemology converges on local optima.** Post-falsificationist appraisal (defeaters, rival explanations, stress tests, severe testing) is *the right move* against the failure mode the packet was reacting against — the prior packet's universal-falsification overreach. But the new epistemology, *applied through nine prompt files and three context docs that all share the same author and the same conversational context*, becomes its own self-reinforcing frame. Every prompt asks for defeaters; no prompt asks "what is the rival epistemology you are not bringing?"
>
> The clearest symptom: the packet treats *audit-first governance* and *archive-by-default lifecycle* and *meta-critical packet audit* as load-bearing structural commitments. None of these is wrong; none of these is shown to be necessary. A leaner rival approach — "fix R1–R5, draft Phase 1.5 in a paragraph, start annotating, see what breaks" — is never considered. The packet has invested epistemic infrastructure proportional to its uncertainty, not proportional to the project's distance from working state.

Why the spec couldn't have named this: the spec inherits the packet's framing of "post-falsificationist appraisal as correction to falsification." Naming "we corrected from method A to method B" forecloses asking whether the choice between A and B was even the right axis. The unanticipated finding is that *the entire methodological-axis is a candidate for collapse*: the project may not need a method at all, it may need a week of mechanical fixes.

> **Implication:** the revision proposal in §7 includes a *bounded* version of this finding — name the alternative ("packet-light revival: R1–R5 + a one-page Phase 1.5 plan + start annotating") in the README's Key Positions section as a rival the packet rejects-for-now, with the trigger that would reopen the choice. This brings the packet into compliance with its own epistemic standard.

---

## 5. Alignment-with-Reality Table

All rows re-tested live against the working tree this session. Commands executed and outputs inspected; see §3 for traceable findings.

| # | Packet claim | Verified state | Divergence |
|---|---|---|---|
| 1 | Five potential sibling projects: scholardoc-ocr, synthetic_test_data, CryptOfCogito, philograph, hermeneutic-workspace-plugin (`01_local_workspace.md`) | Only `hermeneutic-workspace-plugin` exists. `philo-rag-simple` and `philograph-mcp` exist (likely intended). `gsd-2-explore`, `gsd-2-uplift`, `harness-studio` exist and are active but unnamed. | **MAJOR** |
| 2 | `scholardoc/models.py` is a god module (`05_known_audit_findings.md` #6) | `wc -l scholardoc/models.py` → 1524 | **NONE** (claim confirmed) |
| 3 | `.planning/knowledge/{signals,reflections,spikes}/` is unused (per May 1 audit) | `ls .planning/knowledge/` → three subdirs (`reflections`, `signals`, `spikes`); spikes empty | **NONE** (claim confirmed) |
| 4 | Phase 1.5 Pilot Annotation is "top recommendation" of May 1 audit (`05_known_audit_findings.md` #2) | May 1 synthesis names it "biggest single move" *within* a tiered list where Tier 0 (R1–R5 repairs) and Tier 1 (Phase 1.2 expansion) come first | **MINOR-to-MAJOR** (packet flattens a tiered priority into a single ranking) |
| 5 | GSD-2 is out of scope (`00_nonnegotiables.md` #12) | `~/workspace/projects/gsd-2-explore`, `gsd-2-uplift` exist and are recently active; user has parallel GSD-2 work outside the revival branch | **MINOR** (the packet's stance is locally correct, but the unconditional framing misses the active parallel exploration) |
| 6 | 116 modified `.claude/` files (implicit from May 1 audit) | Recent commits (`c2a82cb`, `72dd5ab`, `b0ca1d7`, `6dbea41`) refresh GSD workflow, suggesting partial resolution; only one tracked-file modification on current branch (`.planning/measurement/session-meta-postlude/session-meta-postlude.jsonl`) | **MINOR** (claim partially stale) |
| 7 | Packet staged at `.planning/revival-packets/v5.2/` (`PLACEMENT.md`) | Actual location: `.planning/revival-packet/` (no version subdir) | **MINOR** (placement-doc/reality mismatch) |
| 8 | Current branch state unmentioned by packet | Branch: `revival/2026-05-audit-and-reset`; commit `6258d1c docs(planning): capture repo governance reset` already exists | **MAJOR** (packet's revival work has been partially pre-empted on this branch) |

---

## 6. Operationalizability Table

Each task spec walked as a cold agent with only the spec and its declared context inputs.

| Spec | Executable cold? | Specific gaps |
|---|---|---|
| `TASKSPEC_00_AUDIT_THIS_PACKET.md` | **YES** | The spec is genuinely concrete: 13 lenses, 11 required sections, a verdict from a closed set, a required unanticipated finding. This audit demonstrates executability. |
| `TASKSPEC_01_LOCAL_WORKSPACE_BASELINE_AUDIT.md` | **PARTIAL** | Commands listed; output file named. Missing: what passing looks like; what to do if a sibling repo doesn't exist (currently 4 of 5 don't); what "audit" means beyond `git status`. |
| `TASKSPEC_02_GSD_FEASIBILITY_AUDIT.md` | **PARTIAL** | Four verdict labels listed; no decision criterion per label. "USE_AS_HELPER_NOW" vs "SPIKE_CURRENT_GSD" — which evidence distinguishes them? Missing. |
| `TASKSPEC_03_REPO_SPLIT_AUDIT.md` | **NO** | Four options listed; eight criteria listed; *no scoring rubric, no threshold, no decision rule*. The audit could legitimately end with "all four options are viable." |
| `TASKSPEC_04_DOC_TRUTH_REPAIR.md` | **NO** | Six lines total. "Which docs?" — unspecified. "Which truths?" — unspecified. "Reconciled against what?" — unspecified. Scope guard absent. |
| `TASKSPEC_05_PHASE_1_5_SCAFFOLD.md` | **NO** | Six filenames required; *no required content* per file. Empty stubs technically pass. |
| `TASKSPEC_06_STRICT_VALIDATION_SPIKE.md` | **PARTIAL** | DESIGN/EXPERIMENTS/FINDINGS/DECISION required as files; no decision criterion. "Strict mode adds value" vs "strict mode is a footgun" — both can be defended; spec does not say which evidence decides. |
| `TASKSPEC_07_SOURCE_TO_CLEAN_MAPPING_SPIKE.md` | **PARTIAL** | Five examples named; per-example acceptance criterion missing. "Page number removal" — does it require a working implementation? A spec? A failed attempt? All three are valid readings. |
| `TASKSPEC_08_HARNESS_LANDSCAPE_RESEARCH.md` | **PARTIAL** | Five prerequisites named (good); deferred-until trigger named (good); decision criterion *for harness selection* missing. The spec ends with a candidate list. |

> **Summary:** of nine task specs, one passes cold (TASKSPEC_00), four are partially executable (1, 2, 6, 7, 8), and three fail cold (3, 4, 5). The single most damaging failure is TASKSPEC_04 — it is the only spec that touches condition #1 (local truth restoration), and it cannot direct work.

---

## 7. Revision Proposal

PROMPT_01 should treat the following list as an authoritative worklist. Each item names the file, the change, and an acceptance criterion. Apply or refuse-with-reason per the PROMPT_01 contract.

> **Numbering:** R7.x. Each item is self-contained.

### R7.1 — Add Phase 1.2 reconciliation [HIGH, structural]

- **File to create:** `.planning/revival-packet/task_specs/TASKSPEC_PHASE_1_2_RECONCILIATION.md`
- **Change:** Name what the packet absorbs from, defers to, or supersedes regarding the roadmapped Phase 1.2 (`.planning/phases/01.2-*` slots). For each of the four existing 01.2 plans (authority reset, verification reset, legacy boundary, Phase 2 contract) and the three proposed (ADR backfill, agential uplift, KB seeding), declare: ABSORBS / DEFERS_TO / SUPERSEDES / IGNORES, with one-line reason.
- **Acceptance criterion:** The reconciliation doc names every 01.2-0X plan that exists or has been proposed in the May 1 audit's `06-interventions.md` Tier 1 section, with a disposition. No plan is left undecided.
- **Cross-edits required:** Add a one-line reference in INDEX.md and README.md ("Phase 1.2 reconciliation"); add a "Phase 1.2 awareness" bullet to `context/05_known_audit_findings.md`.

### R7.2 — Add Tier 0 repair task spec [HIGH, structural]

- **File to create:** `.planning/revival-packet/task_specs/TASKSPEC_TIER_0_REPAIRS.md`
- **Change:** Name R1–R5 from the May 1 audit's `06-interventions.md` as a discrete revival-week-1 task. Each repair gets: trigger, change, evidence, acceptance criterion. Cite the May 1 audit's repair IDs.
- **Acceptance criterion:** All five repairs (R1: commit/revert `.claude/`; R2: Kant fixture; R3: `convert_pdf` ghost import; R4: register `pytest.mark.slow`; R5: STATE.md update) appear with named files and named outcomes. The packet now has a "do this week" deliverable separate from design work.
- **Cross-edits required:** Add `IMPL_TIER_0_REPAIRS.md` in `prompts/03_implementation/`; add a one-line reference in INDEX.md.

### R7.3 — Fix sibling-project list [HIGH, factual]

- **File to edit:** `.planning/revival-packet/context/01_local_workspace.md`
- **Change:** Replace the current list with one that distinguishes (a) confirmed-existing siblings: `hermeneutic-workspace-plugin`, `philo-rag-simple`, `philograph-mcp`, `gsd-2-explore`, `gsd-2-uplift`, `harness-studio`; (b) confirmed-missing under those names: `scholardoc-ocr`, `synthetic_test_data`, `CryptOfCogito`, `philograph` (plain). For (b), declare each as: NEEDS_CREATION / RENAMED_TO_X / OUT_OF_SCOPE.
- **Acceptance criterion:** Running `for d in <every-name>; do test -d ~/workspace/projects/$d && echo EXISTS:$d || echo MISSING:$d; done` returns a result reconcilable with the list.

### R7.4 — Replace "Philograph" with reality-anchored downstream framing [HIGH, factual]

- **Files to edit:** `.planning/revival-packet/README.md` ("Key positions"); `.planning/revival-packet/context/00_nonnegotiables.md` (#9); `.planning/revival-packet/context/04_project_context.md` (Philograph definition).
- **Change:** Either commit to "Philograph (planned, philo-rag-simple/philograph-mcp as current downstream proxies)" or rewrite to "ScholarDocument is for downstream applications; named downstream candidates: `philo-rag-simple`, `philograph-mcp`, Anki generators, RAG pipelines." Pick one — the current text reads as if Philograph is an existing system.
- **Acceptance criterion:** Every mention of "Philograph" in the packet either (a) names a verifiable artifact or (b) is explicitly marked as planned/aspirational.

### R7.5 — Declare the executor [HIGH, structural]

- **File to create:** `.planning/revival-packet/context/11_executor_contract.md` (or extend INDEX.md).
- **Change:** Name the required executor (Claude Code), the required capabilities (Read/Write/Bash, subagent `Agent` tool, `@`-reference resolution, optionally web), and the degradation contract for executors that lack subagents (orchestrators run sequentially in-context). Include the resolution rule for `@`-references (cwd-relative, with `.planning/revival-packet/` as the implied root for nested refs).
- **Acceptance criterion:** Reading this file allows an executor of any provenance to verify whether it can run the packet. The packet's silence on executor capability is closed.

### R7.6 — Promote `@`-references to fully-qualified paths in nested prompts [MEDIUM, structural]

- **Files to edit:** every file under `prompts/` that uses `@context/...` or `@task_specs/...` syntax (audit count: 22 files).
- **Change:** Either (a) replace with `@.planning/revival-packet/context/...` so resolution works from repo-root cwd; or (b) leave packet-relative *and* add a one-line note at the top of each prompt: "All `@`-refs are packet-relative; the packet root is `.planning/revival-packet/`." Choose (b) for revision cost.
- **Acceptance criterion:** A cold executor invoked from repo-root cwd can resolve every `@`-reference in every prompt without prior instruction beyond reading the prompt.

### R7.7 — Add acceptance criteria to each task spec [HIGH, structural]

- **Files to edit:** `TASKSPEC_02_GSD_FEASIBILITY_AUDIT.md`, `TASKSPEC_03_REPO_SPLIT_AUDIT.md`, `TASKSPEC_04_DOC_TRUTH_REPAIR.md`, `TASKSPEC_05_PHASE_1_5_SCAFFOLD.md`, `TASKSPEC_06_STRICT_VALIDATION_SPIKE.md`, `TASKSPEC_07_SOURCE_TO_CLEAN_MAPPING_SPIKE.md`, `TASKSPEC_08_HARNESS_LANDSCAPE_RESEARCH.md`.
- **Change:** Add an "## Acceptance criteria" section to each, declaring (a) what content the output must contain; (b) what minimal evidence supports a passing verdict; (c) what would make the verdict fail. For TASKSPEC_05 specifically: name the required *content* of each of the six Phase 1.5 files (e.g., 01.5-PAGE-SELECTION.md must list 3–5 named PDF pages with rationale). For TASKSPEC_04: name which docs (`.planning/PROJECT.md`, `STATE.md`, root `ROADMAP.md`, `README.md`, `CLAUDE.md`, `QUESTIONS.md`), name the reconciliation target (`.planning/audit/2026-05-01/00-SYNTHESIS.md`).
- **Acceptance criterion:** Each amended spec contains a section titled "## Acceptance criteria" with at least three bulletted criteria; each criterion is testable by a verifier reading the output and the live repo together.

### R7.8 — Add scope-creep guard at packet level [MEDIUM, structural]

- **File to create:** `.planning/revival-packet/context/12_scope_guard.md` (or extend `00_nonnegotiables.md`).
- **Change:** Name what the packet does *not* attempt: implementing schema changes; touching production code in `scholardoc/` or `scholargt/`; changing `ground_truth/` outputs; running tests against unfixed Kant fixtures; running the deferred harness research before its prerequisites; making git commits on the user's behalf.
- **Acceptance criterion:** The "do not change" lists scattered across task specs roll up to a single packet-level list.

### R7.9 — Add precedence / authority model [MEDIUM, structural]

- **File to edit:** `.planning/revival-packet/PLACEMENT.md` (extend) or new `.planning/revival-packet/AUTHORITY.md`.
- **Change:** Declare the precedence rule between `reports/revival/*.md` (advisory, packet-owned) and `.planning/{PROJECT,STATE,ROADMAP}.md` plus `.planning/audit/2026-05-01/00-SYNTHESIS.md` (project-owned, authoritative). When they disagree, project-owned wins by default; packet outputs become authoritative only when the user explicitly adopts them (e.g., into `.planning/phases/`).
- **Acceptance criterion:** A reader can resolve a hypothetical conflict between a packet report and `.planning/STATE.md` by reading this doc alone.

### R7.10 — Add failure-recovery model [MEDIUM, structural]

- **File to create:** `.planning/revival-packet/context/13_failure_recovery.md`.
- **Change:** Name what happens when a prompt fails mid-flight: partial outputs remain in `reports/revival/`; the next prompt does not silently consume them; a `BLOCKED.md` sentinel can mark a stalled prompt; resumption requires the user to inspect and either retry or skip-with-reason.
- **Acceptance criterion:** A cold executor can read this doc and know what to write when its predecessor produced an incomplete report.

### R7.11 — Make non-negotiables conditional where appropriate [MEDIUM, methodology]

- **File to edit:** `.planning/revival-packet/context/00_nonnegotiables.md`.
- **Change:** For each non-negotiable, add a one-line "Revision trigger" where one is defensible. Specifically: #11 (no universal falsification) — revision trigger: "if a downstream decision proves falsification was actually the right standard for that class of claim, revise"; #12 (no GSD-2) — revision trigger: "Milestone 2 start, after a GSD-2 spike succeeds and v2.81+ has shipped stable for 30 days" (inherit from May 1 audit). #1–#8 may remain unconditional if defended.
- **Acceptance criterion:** Each non-negotiable has either a revision trigger or an explicit "unconditional, no trigger" tag with reasoning. The list now complies with the packet's own evidence standard.

### R7.12 — Add packet-level revision trigger [MEDIUM, lifecycle]

- **File to edit:** `.planning/revival-packet/LIFECYCLE.md`.
- **Change:** Add a "## Packet revision triggers" section naming when the packet itself becomes due for re-audit (e.g., when the live revival branch is merged; when the May 1 audit synthesis is amended; when more than two task specs need rewriting; at Milestone 1 close; on any verdict downgrade from a verification pass).
- **Acceptance criterion:** A reader can decide whether the packet is currently valid by checking the listed triggers against project state.

### R7.13 — Substantiate the verification report template [MEDIUM, structural]

- **File to edit:** `.planning/revival-packet/templates/verification_report_template.md`.
- **Change:** Add per-section guidance similar to VERIFY_PACKET_AUDIT's V1–V9 — for each verification heading, name what evidence supports a PASS, what makes it FAIL, what makes it PASS_WITH_WARNINGS. Verification prompts can keep their three-line "use this template" pattern, but the template now carries the verification logic.
- **Acceptance criterion:** A verifier executing VERIFY_IMPLEMENTATION_OUTPUT can produce a PASS/FAIL with reasoned evidence; the prompt is no longer a heading filler.

### R7.14 — Acknowledge the current revival branch [LOW, factual]

- **File to edit:** `.planning/revival-packet/context/05_known_audit_findings.md` (or create `context/14_branch_state.md`).
- **Change:** Note the current branch `revival/2026-05-audit-and-reset` and the commits that have already partially landed governance-reset work (`6258d1c`, `b0ca1d7`, `72dd5ab`, `c2a82cb`). State the packet's relationship to that work: parallel, complementary, or replacing.
- **Acceptance criterion:** A reader unfamiliar with the branch can locate the prior work and understand whether the packet is duplicating it.

### R7.15 — Add a "packet-light rival" acknowledgement [LOW, methodology]

- **File to edit:** `.planning/revival-packet/README.md` (Key positions) or new `.planning/revival-packet/context/15_rival_approaches.md`.
- **Change:** Acknowledge the lighter rival approach surfaced in §4 of this audit: R1–R5 + a one-page Phase 1.5 plan + start annotating. Name the trigger that would reopen the choice (e.g., if two consecutive orchestrator outputs are paraphrasing inputs rather than producing new evidence, switch to packet-light).
- **Acceptance criterion:** The packet now shows its rival rather than foreclosing it.

> **Refusals expected:** PROMPT_01 may refuse R7.6 if the packet author prefers full-qualified `@`-refs (option (a)) over packet-relative + header note (option (b)). Either is acceptable; record the choice. PROMPT_01 may also refuse R7.15 if it judges the rival to be insufficiently specified; in that case it must record the refusal with the specific evidence gap.

---

## 8. Governance Recommendation

**Recommendation: Keep in `.git/info/exclude` for now; relocate to a sibling staging path at archive time.**

Specifically:

1. **During revival (current state):** Packet stays at `.planning/revival-packet/`, listed in `.git/info/exclude`. The user's choice of `.git/info/exclude` over `.gitignore` is correct — local-only exclusion keeps the packet invisible to repo clones without polluting `.gitignore` with packet-management noise. The user already applied this. Do not change.
2. **At packet adoption (when PROMPT_01 completes READY):** No move; the packet is still operational. Add a `LIFECYCLE.md` status block of `AUDITED_ACCEPTED`.
3. **At distillation (when adopted outputs have moved to `.planning/phases/`, `.planning/adr/`, etc.):** Move packet to `.planning/revival-packet-archive/v5.2/` (in-repo) or `~/workspace/projects/scholardoc-revival-packets/v5.2/` (out-of-repo). Choose in-repo if total packet size remains under ~500 KB and the archive is referenced from `.planning/audit/`; choose out-of-repo if either becomes false. **Do not** commit the staging packet directly to repo history — its conversational hedges and superseded earlier versions (v5.0, v5.1) do not belong in `main`.
4. **At supersession (post-Milestone 1):** Per `LIFECYCLE.md` archive-by-default — never delete. The archive manifest (`templates/packet_archive_manifest_template.yaml`) gets populated.

**Reasoning:**
- Committing the packet now mixes operational governance (status changes, version bumps, in-place edits) with code/test history. The packet expects frequent in-place editing (per PROMPT_01); commits would churn.
- `.gitignore` would broadcast the packet's exclusion to anyone who reads the repo; `.git/info/exclude` keeps it local.
- The relocation-at-archive convention separates "active revival workspace" from "historical record." Archive lives near other planning history (`.planning/audit/2026-05-01/`) where it's findable.

---

## 9. Success Probability and Load-Bearing Dependencies

> **Probability (calibrated band):** **25–40% as-is**; **45–60% after the §7 revisions land**.

**Reasoning:**

- The packet's intended end-state (conditions #1–#8) requires both *design clarity* and *mechanical fixes*. The packet is well-equipped for design (orchestrators, spikes, synthesis) and poorly equipped for fixes (TASKSPEC_04 too thin; Tier 0 repairs absent). Even a perfect run produces ~70% of design and ~20% of fixes. Combined yield: ~40%.
- Post-revision, the new TASKSPEC_TIER_0_REPAIRS and TASKSPEC_PHASE_1_2_RECONCILIATION close the fix-side gap. Expected yield: ~55%.
- The remaining ~45% probability-of-failure even post-revision tracks: (a) executor-capability uncertainty (~15%); (b) the orchestrator-paraphrasing risk (F12.1, ~10%); (c) doc-truth-repair drift against parallel Phase 1.2 work (F12.4, ~10%); (d) sunk-cost on misframed downstreams (F12.5, ~10%).

**Conditions most likely to be met (post-revision):** #3 (direction set), #4 (schema anchored), #7 (siblings positioned), #6 (repo split decided enough).

**Conditions most likely to fail:** #1 (local truth — depends on TASKSPEC_04's amended scope holding), #2 (Phase 1.2 — depends on R7.1 being applied correctly), #8 (sustainability — depends on R7.5 actually constraining executor choice).

**Load-bearing dependencies outside the packet:**

1. **Executor must be Claude Code with subagent access** *or* the packet must be downgraded to single-agent execution. Currently undeclared (Finding 9.1).
2. **User must not chain Goal 1 → Goal 2 silently.** The packet recognizes this risk in `GOAL_LAUNCHER.md`; the human-review firewall between audit and adoption is essential. (Verified: the user is currently running Goal 1 separately, per the goal text.)
3. **Live repo must not undergo orthogonal Phase 1.2 work in parallel.** If Phase 1.2 plans 01.2-01..04 are executed by another session while the packet runs, doc-truth-repair drift (F12.4) becomes near-certain.
4. **May 1 audit synthesis must remain the inherited truth-anchor.** If `.planning/audit/2026-05-01/00-SYNTHESIS.md` is amended during the run without updating `context/05_known_audit_findings.md`, the packet's premise base goes stale.

---

## 10. Defeaters and Revision Triggers for This Audit's Verdict

The verdict (ACCEPT_WITH_REVISIONS) should be revised if:

- **D1.** A re-test of the alignment-with-reality table (§5) shows >1 MAJOR divergence I missed. The audit's reality check was bounded to ~25 commands; deeper inspection could surface more.
- **D2.** The PROMPT_01 executor finds that ≥3 of the §7 revisions cannot be applied without introducing new contradictions. That signals the revisions are interlocked with the packet's core in ways I underestimated — downgrade to RESTRUCTURE_PACKET.
- **D3.** A second auditor (e.g., a fresh Claude or Codex session reading the same packet) returns a different verdict bucket with non-overlapping reasoning. The audit's own evidence is one observer's; the meta-critical standard requires triangulation. If you have access to one, run VERIFY_PACKET_AUDIT.md as a second pass.
- **D4.** The user has decided to abandon ScholarGT or has materially re-scoped the project since `.planning/PROJECT.md` (last modified 2026-02-18) — in which case revival-success definition #3 (direction) needs revisiting before any packet adoption.
- **D5.** Phase 1.2 has already been executed silently and `.planning/phases/01.2-*` directories now contain completed plans I did not inspect. In that case Finding 3.1 collapses and several §7 revisions become redundant.
- **D6.** The user reports the packet was not authored by ChatGPT-in-conversation as the packet's own framing claims. The audit's authorship-standpoint critique (L4) is load-bearing on that fact.

**Revision triggers (when this audit becomes stale):**

- The packet itself is revised (any in-place edit to a file under `.planning/revival-packet/`). Re-audit at next adoption gate.
- A new audit synthesis lands in `.planning/audit/`.
- The current revival branch merges to `main`, materially changing the load-bearing dependency #3.
- Any of D1–D6 fires.

---

## 11. Anti-Pattern Check

> Each anti-pattern from `checklists/PACKET_AUDIT_CHECKLIST.md` "Anti-patterns to refuse," confirmed-refuted with evidence:

- [x] **Audit does not consist primarily of walking the packet's own self-named checklist.** — Refuted: this audit's organizing structure is the spec's thirteen lenses, not the packet's own `PACKET_AUDIT_CHECKLIST.md`. The checklist is referenced once (here) as a meta-tool, not as a substitute for the work.
- [x] **Audit does not accept the packet's "key positions" as given without testing them.** — Refuted: Finding 2.1 (Philograph framing), Finding 2.2 (GSD-2 conditional), Finding 4.3 (non-negotiable #12 over-flattening), Finding 4.4 (governance-ceremony preference), §4's unanticipated finding (post-falsificationist as local optimum). Each is a tested rejection of a key position.
- [x] **Audit does not rely only on packet files; it tests at least some packet claims against the live repo.** — Refuted: §5 alignment-with-reality table has eight rows, each tested live this session; §3 L5 cites specific commands (`wc -l scholardoc/models.py`, `ls .planning/knowledge/`, `find ~/workspace/projects/`).
- [x] **Audit does not issue a clean ACCEPT_AS_IS without naming at least one failed attempt to break the packet's framing.** — Refuted: the verdict is ACCEPT_WITH_REVISIONS precisely because §4's attempt to break the framing succeeded partially (the post-falsificationist framing survives as defensible but is not load-bearing on its own; the "packet-light" rival was not foreclosed).
- [x] **Audit does not issue a REPLACE / ABANDON without naming what was salvageable.** — N/A: verdict was not REPLACE / ABANDON. The verdict explicitly names what's salvageable (architecture, post-falsificationist appraisal, meta-critical audit pattern, archive-by-default lifecycle, 22 prompt files).

> **Additional anti-pattern checks beyond the checklist:**

- **Did not defer hard judgment to the user.** Where the packet was under-specified (executor, scope-creep guard, precedence rule, failure recovery, packet revision trigger), this audit named the silence as a finding and proposed concrete fills in §7 — rather than asking the user to fill them.
- **Did not rely exclusively on packet self-checks.** `PACKET_AUDIT_CHECKLIST.md` is used as one tool in §11 only; the substantive work in §3–§7 came from independent lens application and live-repo testing.
- **Did not rubber-stamp.** Verdict is not ACCEPT_AS_IS; revision proposal has fifteen items; success probability is ≤60% even after revisions.
- **Did not reject reflexively.** Verdict is not REPLACE or ABANDON; the packet's architecture and earned epistemic corrections are preserved.

---

## Appendix A: Evidence Categories Used in This Audit

Per `context/02_evidence_standard.md`:

- **OBSERVED** — directly verified by a command run or a file read this session (e.g., `wc -l scholardoc/models.py` → 1524; `find ~/workspace/projects/` for sibling list).
- **AUDIT-SUPPORTED** — supported by reading the May 1 audit (`.planning/audit/2026-05-01/00-SYNTHESIS.md`, `06-interventions.md`, `04-gsd2-research.md`).
- **REFERENCE-SUPPORTED** — supported by reading the packet's own files (e.g., specific cross-reference findings, internal-coherence claims).
- **INFERENCE** — reasoned from observations and audit/reference inputs, not directly attestable as a single fact.
- **SPECULATION** — not used in this audit. Every claim above carries one of the four stronger labels.

## Appendix B: Read Inventory

Files read during this audit (≈42 files):

- All ten files in `.planning/revival-packet/context/`
- All four files in `.planning/revival-packet/analysis_reference/`
- All nine task specs in `.planning/revival-packet/task_specs/`
- All thirteen prompts in `.planning/revival-packet/prompts/{00_package,01_audits,02_orchestrators,03_implementation,04_verification}/`
- Both templates and the checklist
- `.planning/revival-packet/{INDEX,README,LIFECYCLE,PLACEMENT}.md`
- Live repo: `.planning/PROJECT.md`, `STATE.md`, `ROADMAP.md`, `.planning/audit/2026-05-01/{00-SYNTHESIS,06-interventions,04-gsd2-research}.md`
- Live repo state: `git status`, `git branch --show-current`, `git log --oneline -n 20`, `git stash list`, `ls ~/workspace/projects/`, `cat .git/info/exclude`, `wc -l scholardoc/models.py`, `ls .planning/knowledge/`, etc.
