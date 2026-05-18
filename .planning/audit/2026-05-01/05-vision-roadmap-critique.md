---
audit: vision-roadmap-critique
date: 2026-05-01
auditor: same-vendor-critical (Claude Opus 4.7, fresh session)
scope: plan-level only (PROJECT.md, ROADMAP.md, STATE.md, REVIEW_STRATEGY.md, VISION.md, REQUIREMENTS.md, Phase 1.2 dir, Phase 1.1 sample, repo-governing-reset deliberation)
not-scope: code, tests, runtime behavior
---

# 05 — Vision, Roadmap, and Direction Critique

## Top-line verdict

**Recovering, with two convergent risks worth flagging now.** The repo is not lost — REVIEW_STRATEGY.md is an honest, evidence-rich self-audit and the Phase 1.2 deliberation (`repo-governing-reset-before-phase-2.md`) is a textbook example of the team noticing drift before it compounds. That's healthy. But the recovery is being implemented through a single narrow phase (1.2) while six waves of identified work sit unphased; the milestone's center of gravity (Phase 5: design validation) is at the end of a 7-phase chain that has yet to touch a single verified GT page; and the "design-heavy" frame is doing real epistemic work — it's also doing rhetorical work that justifies postponing the empirical sanity-check. That last move is the one most worth interrogating.

## Strengths (real, specific)

1. **The pivot rationale is genuinely sound** (PROJECT.md L11–13). "You cannot improve what you cannot measure" is not just a slogan here — the evidence is concrete: 32 spikes produced ScholarDoc but zero verified GT exist (STATE.md L113), so Phase 5's claim that the design needs validation is grounded, not aspirational. The diagnosis is right.

2. **The Phase 1.2 deliberation is methodologically exemplary** (`deliberations/repo-governing-reset-before-phase-2.md` L19–28). Toulmin-style options A/B/C, evidence table with corroboration column, named tensions, falsifiable predictions (P1/P2/P3). This is the discipline the team committed to and it's being used. Preserve this template.

3. **The SFP-1 through SFP-6 absorption is structurally honest** (STATE.md L48–52). When the v2 gap analysis surfaced 9 partial-structural gaps, the team adopted Tier 1+2 and *deferred* SFP-7 with explicit reasoning ("4 pages"). That's calibrated triage, not feature-creep. The "~41 lines of additions" framing is accurate, not a euphemism — Plan 01.1 plans show absorption into existing waves, not new waves bolted on.

4. **The "no synthesis" feedback is being honored at vocabulary level**. PROJECT.md and ROADMAP.md describe extraction, measurement, and annotation. Nowhere does a phase claim to produce knowledge synthesis or privilege a methodology. This is a non-trivial piece of self-discipline given how easily the engagement layer drifts toward synthesis framing.

5. **REVIEW_STRATEGY.md is unusually honest about the project's three eras** (L36–46). Naming "Era 1 / Era 2 / Era 3" and admitting "Root docs reflect Era 1, GSD planning reflects Era 3, they describe different projects" is the kind of self-diagnosis that prevents long-term confusion. It's also what gave Phase 1.2 a defensible frame.

## Concerns (ranked)

### CRITICAL-1: Phase 5 is the only phase that touches reality, and it's at the end

**Risk:** The schema (Phase 1 + 1.1, completed) was designed in concentrated sprints over ~3 days each, validated by 312 unit tests instantiating models, regenerating JSON Schema, and updating example files. None of that is empirical validation against real annotation work. Zero verified GT exist (STATE.md L113). The plan is to design extractors (Phase 2), experimentation (Phase 3), and annotation tooling (Phase 4) on top of v2.0.0 schema — and only then, in Phase 5, produce 10–20 verified GT pages that test whether the schema actually fits.

**Evidence:** ROADMAP.md L169–183. Phase 5 success criteria #5 is "Design issues discovered during validation are documented with proposed fixes." That criterion silently admits that schema rework is plausible. If Phase 5 surfaces schema issues, Phases 2–4 may need rework — that's three phases of cascade.

**Why now (not later):** The team has REVIEW_STRATEGY.md R6 stating experimental methodology is "highest priority new work" and explicitly suggesting Phase 3 should precede Phase 2. ROADMAP.md does not adopt this. The C2 checklist item ("consider reordering Phase 3 before Phase 2") sits unticked. This is a known concern with no trace of resolution in PROJECT.md or ROADMAP.md.

**Confidence: high** that the ordering is structurally fragile. **Confidence: medium** that the cost is large (it depends on whether v2.0.0 schema actually fits real annotation cases — which is exactly what's untested).

**What dissolves it:** A documented argument for why Phase 5's schema-rework risk is bounded — e.g., "we already validated the schema against the 85 structural phenomena from gap analysis, the residual risk is small." That argument exists implicitly (Quick-1: "zero blocking gaps") but isn't load-bearing in the roadmap as written.

**Direction:** Either (a) split Phase 5 into "Phase 1.5: pilot annotation of 3–5 pages to surface schema issues before Phase 2" + "Phase 5: full validation corpus", or (b) explicitly write the bounded-risk argument into PROJECT.md so the design-first ordering rests on something other than convention. Don't do both — that's perfectionism.

### CRITICAL-2: The "design-heavy" frame is load-bearing in ways it shouldn't be

**Risk:** "Design-heavy milestone — get architecture right before producing large GT corpus" appears in PROJECT.md L113, ROADMAP.md L5, and as a [Roadmap revision] decision in STATE.md L58. It justifies (1) deferring all ScholarDoc improvements, (2) putting design validation last, (3) running 5 phases of design work without empirical anchors. That's a lot of structural weight on one rhetorical frame.

The frame is *defensible* — but it's defending two distinct claims that get conflated:
- Claim A: "Get the schema right before annotating 100s of pages." (Reasonable.)
- Claim B: "Get the entire stack — schema, extractor interface, experimentation framework, annotation tool — right before any empirical validation." (Much stronger; requires more justification.)

The roadmap commits to Claim B but only justifies Claim A.

**Evidence:** PROJECT.md L106 says "Design-Heavy Milestone: Get architecture right before producing large GT corpus" — that's Claim A. ROADMAP.md Phase 5 places ALL validation last — that's Claim B. The transition between A and B is not argued.

**Why now:** The 1.2 deliberation already noticed the schema/runtime gap ("ScholarGT has completed the schema/config/validation layer, but the next promised layers do not yet exist"). The same critical lens hasn't been applied to schema/empirical-validation gap.

**Confidence: medium-high** that the frame is doing more work than it can support; **medium** that fixing it changes execution materially (it might just change PROJECT.md text).

**What dissolves it:** A single paragraph in PROJECT.md distinguishing A from B and arguing for B specifically — or a pilot-validation phase that backs off B to A.

### HIGH-1: ScholarDoc has lost its self-description

**Risk:** docs/VISION.md (the file CLAUDE.md calls "authoritative") describes ScholarDoc as a standalone PDF-extraction library. PROJECT.md describes a dual-project workspace where ScholarDoc is a deferred plugin. These are not the same project. A new contributor reading the repo top-down (CLAUDE.md → VISION.md) will form a model of the project that contradicts the model formed by reading `.planning/PROJECT.md`.

**Evidence:** docs/VISION.md L1–37 (no mention of ScholarGT, no mention of measurement-foundation framing). PROJECT.md L9 ("Improvements to ScholarDoc are deferred until ScholarGT provides the measurement infrastructure"). REVIEW_STRATEGY.md C1, B4 both flag this; B4 is unticked.

**Why now:** Phase 1.2 plan 01.2-01 names this exact problem ("Authority reset — align README.md, CLAUDE.md, root ROADMAP.md, docs/VISION.md, and STATE.md"). The phase has not started (directory empty except .gitkeep, dated Apr 16). Two weeks of drift since planning, no execution.

**Confidence: high** on the documentation gap; **lower** on the consequence — Logan is the only contributor and knows the state.

**What dissolves it:** Phase 1.2 actually executes Plan 01.2-01.

**Note:** This is the one finding that's already named in a planned phase. The critique is "the phase exists but is stalled" rather than "the issue is unrecognized."

### HIGH-2: "Universal" GT schema is a marketing word doing structural work

**Risk:** SCH-01 (REQUIREMENTS.md L7) says "Universal GT schema — superset of all annotation types ... extensible without restructuring existing GT". The schema currently covers scholarly philosophical texts (footnotes, citations, Greek/Hebrew, Stephanus/Bekker, sous rature). Phase 1.1's SFPs added LayoutRegister and ScriptVariant for Talmud/Rashi corpora, which broadens it — but every label in the schema is still grounded in one corpus type: Western humanities scholarly texts.

The word "universal" is doing two jobs:
- Honest job: "extensible without breaking" (true; `extra="allow"` and config-driven labels support this).
- Marketing job: "covers any scholarly document type." (Untested. Unproven for scientific papers, technical manuals, archival manuscripts, modern multilingual textbooks.)

The failure mode: when a new corpus class arrives, the team discovers the schema's "universality" was scholarly-philosophical-universality, and either (a) extends ad hoc and accumulates inconsistency, or (b) does another v2→v3 schema break.

**Evidence:** ROADMAP.md L5 ("design-heavy: get the schema, extractor interface ... right *before* producing a large GT corpus"). The SFPs already required schema additions to handle previously unmodeled corpus realities (33% of corpus is RTL — that gap was not anticipated in Phase 1). That pattern is likely to repeat.

**Why now:** The team is committing Phase 2 (extractor protocol) to depend on schema stability. If "universal" is aspirational, downstream work inherits the aspiration as a load-bearing assumption.

**Confidence: medium-high.** The team is internally aware (SFP gap analysis itself proves the schema isn't actually universal); the word in the requirement spec doesn't reflect that awareness.

**What dissolves it:** Rename SCH-01 to something honest like "Cross-corpus extensible schema (current scope: scholarly humanities; expandable via SFP process)." Or document the SFP process as the universality mechanism. The current text claims more than the implementation supports.

### HIGH-3: CryptOfCogito dependency is in tension with "prior projects are debris"

**Risk:** The user's stated commitment (feedback_projects_as_debris.md) is that prior projects are failed experiments to extract lessons from, not codebases to merge. PROJECT.md treats CryptOfCogito as: (a) "mature reference and inspiration" (L67, defensible — extracting lessons), but also (b) "scholarly_annotate (proposed): Shared annotation package — may become part of ScholarGT or remain separate" (L61, the merge anti-pattern), and REVIEW_STRATEGY.md R4 explicitly recommends "Extract CryptOfCogito's annotation tool into a `scholarly_annotate` package in this repo. Update it to work with ScholarGT v2.0.0 schema."

R4's framing — "Building from scratch in Phase 4 would duplicate ~2,237 lines of tested code" — is exactly the rationalization Logan rejected.

**Evidence:** PROJECT.md L60–62, REVIEW_STRATEGY.md L114–119, feedback_projects_as_debris.md.

**Why now:** Phase 4 is the annotation tool phase. The decision frame ("rewrite vs adapt") is deferred to Phase 4 planning (ROADMAP.md L165–166). If R4 carries into that planning unchallenged, the deferred decision will arrive pre-loaded with the rejected anti-pattern.

**Confidence: medium-high** that the tension exists; **medium** that it'll bite (Logan can override at Phase 4 planning time).

**What dissolves it:** An explicit decision in PROJECT.md Key Decisions table: "scholarly_annotate is design inspiration only; ScholarGT annotation tool is built fresh from extracted lessons" — or the opposite, with explicit rationale acknowledging the prior commitment.

### HIGH-4: The reset-pattern is showing up twice

**Risk:** Phase 0 (workspace cleanup) and Phase 1.2 (repo governing reset) are both reset/cleanup/authority-restoration phases inserted into a roadmap that was originally 5 design phases. Two of seven phases are reset work. That's not necessarily wrong, but it's a tell — the project is generating drift faster than the roadmap absorbs it.

**Evidence:** ROADMAP.md L15 (Phase 0), L18 (Phase 1.2). Both inserted, both classified as "URGENT" or housekeeping. STATE.md L104–106 ("Roadmap Evolution") names two URGENT insertions.

**Why now:** If a third reset becomes necessary mid-Milestone 1 (plausible — Phase 4 could surface annotation-tool/schema mismatches), the milestone becomes 8+ phases. The "design-heavy" rationale starts to look like "we're discovering things we should have anticipated."

**Confidence: medium.** Two data points isn't a pattern, but it's worth watching.

**What dissolves it:** A pre-mortem section in PROJECT.md or REQUIREMENTS.md naming what could trigger Phase 2.x or 3.x insertions, so the team has explicit warning conditions rather than discovering them in flight.

### MEDIUM-1: Six waves of work, only Wave 5 (partially) phased

REVIEW_STRATEGY.md identifies Waves 1–6 (L233–262). Wave 1 (decisions) is partially closed — R3, R4, R5, R6 have explicit recommendations but no [DECIDED] entries in PROJECT.md Key Decisions table. Wave 2 (git housekeeping) appears done (Phase 0). Wave 3 (documentation) is the work Phase 1.2 attempts but hasn't started. Waves 4 (uv workspace), 5 (design reviews — GT schema critical review!), and 6 (OCR literature review) have no phases.

The GT schema critical review (R3 / E6) is especially notable: REVIEW_STRATEGY.md says "Logan's concerns ... before building Phase 2 (Extractor Interface) on top of it, we should do a critical review." This is exactly the empirical-anchor concern from CRITICAL-1, surfaced in March, not phased.

**Confidence: high** that the work isn't formally captured. **Lower** that all of it should be — some of these may be intentionally dropped.

**Direction:** Append a "Deferred Strategic Work" section to PROJECT.md or ROADMAP.md, with each Wave 4/5/6 item marked as "carried forward / dropped / merged into Phase X." Currently they're in REVIEW_STRATEGY.md (a historical document) and silently fading.

### MEDIUM-2: Velocity numbers in STATE.md are misleading

**Risk:** STATE.md L21–35 reports "Total execution time: 0.8 hours" and "Average duration: 4.0 min" per plan. These measure plan-execution time after planning is complete — not phase calendar time. Phase 1.1 was "completed 2026-02-20" but the verification artifact is dated 2026-02-20 and Phase 1.2 wasn't drafted until 2026-04-16. That's two months between phase 1.1 close and 1.2 draft, with quick tasks in between but no phase progress.

The metric ("plans complete in minutes") performs velocity. Calendar reality (months between phase boundaries) tells a different story.

**Confidence: high** that the metric is performative; **medium** that it matters (Logan probably knows; future-team usability suffers).

**Direction:** Add a "Calendar elapsed" column or replace plan-minutes with phase-weeks. The team committed to honest measurement; the velocity dashboard should honor it.

### MEDIUM-3: ADR-021 is in limbo

REVIEW_STRATEGY.md L74 ("CryptOfCogito pending_decisions.md says 'ADR-021 needed' — Never written") and E11 ("Write it here or in CryptOfCogito?"). This is a strategic decision about integrated architecture, deferred indefinitely. It's listed as an open question in another repo and nobody owns it.

**Confidence: medium.** It might be genuinely deprecated by the ScholarGT-as-independent-platform decision, in which case it should be marked superseded. Right now it's neither superseded nor written.

**Direction:** Mark ADR-021 SUPERSEDED in CryptOfCogito's tracker, with a one-line pointer to the ScholarGT independence decision (PROJECT.md decisions table).

### LOW-1: VISION.md staleness annotation is honest but unactioned

docs/VISION.md L4 says `<!-- Last verified: 2025-12-27 -->`. Today is 2026-05-01 — five months unverified. The mechanism is correct (verification-date comment); the practice has lapsed.

### LOW-2: Milestone 2 is undefined

PROJECT.md says ScholarDoc improvements are "deferred to milestone 2" but Milestone 2's content isn't specified. If Milestone 1 stretches (likely — see MEDIUM-2), the deferred work has no anchor.

## The under-formalized work list

REVIEW_STRATEGY.md ideas not phased anywhere:

| Item | REVIEW_STRATEGY ref | Status |
|------|---------------------|--------|
| Ecosystem vision document (~/CLAUDE.md expansion) | R1, B9 | Not phased |
| Hermeneutic-workspace-plugin integration | R2, G1 | Not phased ("not blocking") |
| GT schema critical review (Logan's concerns) | R3, E6 | Not phased — directly contradicts the CRITICAL-1 concern |
| scholarly_annotate extraction plan | R4, G3 | Phase 4 dependency, undecided |
| OCR literature review (GLM-OCR etc.) | R5, E10 | Not phased |
| Experimental framework as Phase 3 (current order) vs before Phase 2 | R6, C2 | Not adopted |
| uv workspace config | R7, F1 | Phase 1.2 plan 01.2-03 (specific) |
| Serena memory audit (15 files, many stale Dec 2025) | D1–D5 | Not phased |
| ADR-021 (CryptOfCogito integrated architecture) | E11 | Limbo |
| Cross-project Serena memory catalog | G5 | Not phased |
| philo-rag-simple / philograph-mcp deep dives | G4 (PENDING) | Not phased |

**Pattern:** documentation/authority work got phased (Phase 1.2). Strategic/methodological work (R3, R5, R6) and ecosystem-integration work (R1, R2, G1, G2) did not. The unphased items are exactly the ones that would put the schema and roadmap to *empirical* test rather than internal-consistency test.

## Velocity / milestone-sizing read

- Phase 0 + Phase 1: completed ~Feb 18, ~3 days execution.
- Phase 1.1: completed Feb 20, ~2 days execution.
- Phase 1.2: planned Apr 16 (deliberation file), directory still empty May 1 — 2 weeks stalled at planning.
- Total elapsed: ~2.5 months.
- Phases done: 3 of 7+ (Phase 0, Phase 1, Phase 1.1).
- Plans done: 12 of ~20+ projected.

If current velocity holds (plans take minutes; phase boundaries take weeks), Milestone 1 is plausibly 6–9 months elapsed. The "design-heavy" frame justifies this — but PROJECT.md, last updated 2026-02-18, has not been revisited as the milestone has stretched. There's no commitment ("if Milestone 1 exceeds 4 months we trigger X review") that would catch unbounded stretch.

The velocity is consistent with careful, evidence-based work — the discipline is real. It is not consistent with "design-heavy means we ship the design." Two months in, the design has produced a schema; extractor interface, experimentation, annotation tool, and validation remain — and a reset phase is queued before the next design phase begins. The risk is not the pace; it's the absence of a tripwire that would notice unbounded stretch and force a rescope.

## Convergent risks

Three findings point at the same underlying weakness:

- CRITICAL-1 (validation last)
- CRITICAL-2 (design-heavy frame overloaded)
- MEDIUM-1 (R3/E6 GT schema critical review unphased)

All three say: **the schema has not been tested against reality, and the plan does not test it until everything else is built on top.** Treat these as one issue. The fix is not three fixes — it's a single decision about whether/when to insert empirical validation.

Two findings point at calibration discipline:

- HIGH-2 ("universal" overclaims)
- MEDIUM-2 (velocity dashboard performs speed)

Both are calibrated-language failures in artifacts that otherwise do calibrated language well. Same fix: re-read the artifact's own claims and downgrade what the evidence doesn't support.

## Steelman residue

Honest pass over the findings:

- **CRITICAL-1**: The strongest version of the author's choice is "we already did the empirical work — 32 spikes, gap analysis against 85 phenomena, SFP discovery — Phase 5 is just confirming, not discovering." That's plausible. My critique reads Phase 5's "design issues discovered" criterion as evidence of latent doubt; the author would reasonably read it as covering-the-bases rigor. I think my reading is correct but it's not a slam-dunk.

- **CRITICAL-2**: I distinguished Claim A from Claim B fairly cleanly, but the author may simply hold B and consider it self-evident in a research context. Calling the frame "load-bearing rhetoric" is sharper than the evidence supports — it's *also* a real strategic position. Soften to "the frame conflates two claims of different strengths."

- **HIGH-1 (lost self-description)**: This finding is partially dissolved by the existence of Phase 1.2 — the team has named the problem and queued the fix. My critique narrows to "the queue is stalled," which is a legitimate but smaller claim than I implied.

- **HIGH-2 ("universal")**: This is the finding I'm most confident in but it's the one most likely to be dismissed as taste. The author can defend "universal" as marketing register that doesn't claim what I read it as claiming. My ground (calibrated language as committed methodology) is real but the specific word may not rise to a methodology violation.

- **HIGH-3 (CryptOfCogito tension)**: REVIEW_STRATEGY.md was written *before* the explicit "projects-as-debris" feedback was articulated. R4 may reflect an earlier framing that's already been superseded informally. The critique stands but its urgency is lower than I framed.

- **HIGH-4 (reset pattern)**: Two data points. I labeled it "convergent risk." It's a hypothesis worth watching, not a confirmed pattern. Downgrade.

- **MEDIUM-1 (six waves)**: This is one of the strongest findings — REVIEW_STRATEGY.md is a real artifact, the items are concrete, the unphased ones are real. Confidence intact.

## What this audit cannot tell you

- Whether the v2.0.0 schema actually fits real annotation cases. That's empirical and requires Phase 5 work or a pilot.
- Whether the test suite (312 passing tests) covers the right things. I read no test code.
- Whether CryptOfCogito's annotation tool is actually 80% reusable as R4 claims, or 20% reusable. Cross-vendor or codebase audit territory.
- Whether the OCR literature has actually moved (GLM-OCR claim from REVIEW_STRATEGY R5). Substance question.
- Whether Milestone 2 deserves to exist, or whether the project should fork into ScholarGT-only. Strategic question; outside same-vendor structural review.
- Whether the ecosystem (10+ projects) is the right scope or scope-creep dressed as ecosystem thinking. The REVIEW_STRATEGY ecosystem map is large; whether Logan's PhD timeline supports it is a question for Logan, not for me.

---

*End of audit. The team owns the calls; this audit is input, not gate.*
