# Audit Synthesis — ScholarDoc/ScholarGT

**Date:** 2026-05-01
**Orchestrator:** Claude (Opus 4.7, max effort)
**Scope:** Full-repo audit — state, direction, agential readiness, code quality, GSD-2 evaluation, interventions
**Inputs:** five parallel audit reports in this directory + Phase 1.2 deliberation, REVIEW_STRATEGY, current planning artifacts, live code/tests
**Companion deliverable:** `06-interventions.md` (actionable registry)

---

## 1. Executive Summary

**Where we are:** A dual-package repo (`scholardoc/` extraction lib + `scholargt/` GT schema) that pivoted Feb 2026 from "ScholarDoc as standalone library" to "ScholarGT as primary measurement infrastructure, ScholarDoc deferred." Phase 1.1 (schema taxonomy revision with SFP-1..6) closed Feb 20. Two and a half months later, Phase 1.2 (the repo-governing-reset that absorbs March's audit findings) is queued but stalled — its phase directory was created Apr 16 and remains empty May 1. ScholarGT itself is genuinely well-built: clean module DAG, 293/293 tests passing, real independence from ScholarDoc (grep-verified zero cross-imports). ScholarDoc has bit-rotted in exactly the way a "deferred" subsystem does — broken test fixtures, two parallel OCR pipelines, a 1524-line god module, an empty `writers/`. Documentation has drifted across two eras: every root doc still describes Era 1 (ScholarDoc PDF library, Phase 1 in-progress, Dec 2025 context), the test-count claim is 43–62% stale (docs say 257–395; reality is 694), `/project:*` slash commands referenced in CLAUDE.md don't exist, and zero root docs mention ScholarGT.

**Where we are going:** A 5-phase milestone (1.2 → 2 → 3 → 4 → 5) building schema → extractor protocol → experimentation → annotation tool → validation. The plan is *recovering, not lost* — REVIEW_STRATEGY.md and the Phase 1.2 deliberation are the work product of a discipline that catches its own drift. But three findings converge on a single underlying weakness: **the schema (Phase 1+1.1, completed) has never been tested against real annotation work, and the plan defers that test until Phase 5 — after Phases 2/3/4 are built atop it.** The "design-heavy" frame justifying this is doing more rhetorical work than the evidence supports.

**Agential setup: 5/10** — adequate but mismatched. Heavy GSD framework (20 stock agents, 36 commands, 4 hooks, rich `.planning/`) with zero domain specialization, a CLAUDE.md that's grade D (4 months stale), three memory systems with no convention, and `.planning/knowledge/{signals,reflections,spikes}/` empty after 12 plans (GSD's signal-collection design intent unused).

**GSD-2:** **Useful eventually, NOT now.** GSD-2 is a complete architectural pivot (TypeScript CLI on Pi SDK, npm `gsd-pi`, same maintainer, `gsd-1` formally in maintenance) that abandons the Claude Code prompt-framework model entirely. Migration breaks 19 custom agents, 4 hooks, REVIEW_STRATEGY.md, the knowledge subdirectory, and the deliberations pattern. Cost ~20–50h mid-milestone. Right inflection point: spike at Milestone 1 close, migrate at Milestone 2 start *if* the spike succeeds and v2.81+ ships clean (current v2.78.x is mid-stabilization with recent git-safety fixes).

**Bottom line:** This is a research project where careful thinking is the work and code is the byproduct. The discipline is real (REVIEW_STRATEGY, deliberation files, calibrated triage of SFPs). The risks are: (a) schema-validity drift hidden by design-first ordering, (b) doc/authority drift hidden by "we'll get to Phase 1.2 soon," (c) a velocity dashboard that performs speed when calendar reality says months elapsed between phase boundaries, and (d) a tool stack heavier than the differentiation it provides. None of these are emergencies. All of them get worse with time.

---

## 2. Where We Are — Cross-Axis State Snapshot

| Axis | Reality | Most-stale public claim |
|---|---|---|
| **Repo identity** | Dual-package, ScholarGT-primary, ScholarDoc-deferred (per `.planning/PROJECT.md`) | Every root doc says ScholarDoc-only, Era 1 |
| **Active milestone** | Milestone 1: ScholarGT, Phase 1.1 complete, Phase 1.2 queued | Root `ROADMAP.md`: "Phase 1 Complete - OCR Integration Done" (Phase 2 = footnotes) |
| **Current branch** | `feature/01.1-01-foundation-types` (still active, not merged) | Not mentioned in any root doc |
| **Test count** | 694 collected; ~603 pass; 32 unit fail + 29 collection error from one missing PDF | "257" / "312" / "320" / "349" / "395" across files (-43% to -62%) |
| **Working tree** | 116 modified `.claude/` files uncommitted (GSD framework update never finalized) | VERSION says `1.16.0+dev`, config.json says `1.18.3`, recent commit msg says `v1.20.5` |
| **GSD knowledge base** | `.planning/knowledge/{signals,reflections,spikes}/` exist as empty dirs | STATE.md decisions table is the *de facto* knowledge base |
| **Memory systems** | 3 (`.serena/memories/`, `~/.claude/projects/.../memory/`, `.planning/knowledge/`) — no convention | CLAUDE.md still tells agents to use Serena (project-disabled in `~/.claude.json`) |
| **MCP servers** | Only `sequential-thinking` reliably running | CLAUDE.md lists three (Serena/Context7/Sequential); Context7 not configured |
| **Documented commands** | `.claude/commands/gsd/*` (current GSD-Reflect commands) | CLAUDE.md, RULES.md, COMMANDS.md reference 7 `/project:*` commands that never existed |
| **Phase 1.2 readiness** | Roadmap entry exists; phase directory created Apr 16; **no plans drafted** | STATE.md still reads as if Phase 2 is next |

### Code quality state

**ScholarGT (the active deliverable):** Genuinely well-built.
- Module DAG: `base → spatial/labels → semantic/formatting/page → document` (no cycles).
- 293/293 tests pass in 6.3s.
- Independence verified: `grep -rn "scholardoc" scholargt/` returns zero hits.
- Citation decomposition (CitationFormat × ReferenceSystem) is sound design.
- Per-element verification on the `GTElement` base class is the right primitive.
- One real concern: `extra="allow"` on 4 of 5 top-level models silently accepts typos (`Regoin(...)`, `page_indes=0` both validate). Schema tests favor instantiation over behavior.
- Profile YAMLs duplicate enum strings without enum-membership validation.

**ScholarDoc (deferred):** Has bit-rotted.
- 32 unit failures + 29 collection errors all from one missing fixture (`spikes/sample_pdfs/kant_critique_pages_64_65.pdf`, hardcoded path in three test files, gitignored corpus).
- `tests/integration/test_ground_truth_regression.py:103` imports `convert_pdf` — symbol does not exist, currently masked by skip; will fail when a regression PDF lands.
- Two parallel OCR pipelines: `normalizers/ocr_pipeline.py` (708 LOC, "legacy", **default**) and `ocr/pipeline.py` (317 LOC, "new", opt-in only). Dec 2025 integration plan never retired the legacy.
- `models.py` is a 1524-line god module with 27 classes — Era 1 concern.
- `writers/__init__.py` is a 1-line stub since Dec 2025 — `to_markdown()` lives on the model class instead.
- Only 2 TODO markers in entire `scholardoc/` codebase. Hygiene is good; rot is structural, not surface.

**`ground_truth/` (third namespace):** 1.4MB of mixed legacy + active.
- `ground_truth/lib/` (1207 LOC) is *actively imported* by `tests/unit/ground_truth/test_*.py`.
- Everything else is Era 1 prior-art docs and gitignored corpora.
- Unowned — neither under `scholardoc/` nor `scholargt/`. Phase 1.2 should decide whether `ground_truth/lib/` belongs under `scholargt/evaluation/` (likely) or stays a separate toolkit.

**Distribution shape:** `pyproject.toml` ships both packages from one wheel (`packages = ["scholardoc", "scholargt"]`). No `[tool.uv.workspace]` block. If ScholarGT is genuinely independent of ScholarDoc (PROJECT.md L7), the project name and packaging should reflect it — either now via uv workspace, or explicitly decided not to.

---

## 3. Where We Are Going — Direction & Risks

The 5-phase plan (Milestone 1, ScholarGT):

```
Phase 1.2 → Phase 2 → Phase 3 → Phase 4 → Phase 5
(authority    (extractor (experiments (annotation (verified GT
 reset)        protocol)  & metrics)   tool)        corpus)
```

**Strengths of the direction:**
1. The "you cannot improve what you cannot measure" rationale is grounded — not aspirational. Zero verified GT exist; the schema work is justified.
2. Phase 1.1's SFP-1..6 absorption (LayoutRegister, text_direction, ScriptVariant, COLOR, INDEX_AREA, CATCHWORD) was calibrated triage, not feature-creep — Tier 1+2 adopted, SFP-7 deferred with explicit "4 pages" rationale.
3. The Phase 1.2 deliberation is a methodological exemplar (Toulmin-style options A/B/C, evidence corroboration column, falsifiable predictions P1/P2/P3). The discipline is real.
4. "No synthesis" framing is honored throughout — extraction, measurement, annotation only; never "knowledge synthesis."
5. ScholarGT's true independence from ScholarDoc means the Phase 2 extractor seam is unconstrained. No premature coupling.

**The convergent risk** (three findings collapse to one):
The schema (v2.0.0, 312 ScholarGT tests) was designed in concentrated sprints. It has been tested by:
- Instantiating models and asserting fields.
- Regenerating JSON Schema deterministically.
- Updating example files.
- Cross-walking 85 structural phenomena from gap analysis.

It has **not** been tested by:
- A human annotator working through real pages and noticing what the schema can't represent.
- An extractor producing draft GT and a human correcting it.
- A pilot corpus surfacing schema rework needs.

The roadmap defers all of this until Phase 5. Phase 5 success criterion #5 reads "Design issues discovered during validation are documented with proposed fixes" — which silently admits schema rework is plausible. If Phase 5 surfaces issues, Phases 2/3/4 may need rework.

REVIEW_STRATEGY R6 (March 2026) named this: *"Design a proper experiment framework before any new OCR or pipeline work."* It also recommended (R3, E6) a "GT schema critical review" before Phase 2. Neither is phased.

**The secondary risk: doc-authority cascade.**
Phase 1.2 is *queued, not stalled-because-blocked* — it's stalled because nothing forced it forward. Six weeks since REVIEW_STRATEGY.md, two weeks since Phase 1.2's roadmap insertion, the phase directory is empty. The doc drift it's meant to repair has actually *worsened*: STATE.md and ROADMAP.md were both edited Apr 16 but STATE.md wasn't updated to reflect Phase 1.2's insertion — fresh drift inside `.planning/`.

**The tertiary risk: velocity opacity.**
STATE.md reports "Total execution time: 0.8 hours, average duration 4.0 min/plan." That measures plan-execution after planning — not phase calendar time. Calendar reality: Phase 1.1 closed Feb 20; Phase 1.2 drafted Apr 16; today's May 1, 2.5 months elapsed, 3 of 7+ phases done. At current pace, Milestone 1 is plausibly 6–9 months. The dashboard performs speed; the calendar tells a different story. There is no tripwire that would notice unbounded stretch and force a rescope.

**Rhetorical-load issues** (calibrated-language failures):
- "Universal" GT schema (SCH-01) — it's actually scholarly-philosophical-corpus-with-extensible-process. SFPs already proved this (RTL was 33% of corpus and not anticipated in v1).
- "Design-heavy" frame — defends two distinct claims: (A) "get the schema right before annotating 100s of pages" (reasonable); (B) "build everything before any empirical anchor" (much stronger; not separately justified).

---

## 4. How We Are Set Up for Agential Development

**Score: 5/10 — adequate but mismatched.**

What's working:
- `.planning/` structure (PROJECT.md, ROADMAP.md, STATE.md, phase artifacts) is comprehensive.
- STATE.md decision table tagged by plan ID is the strongest evidence trail in the repo.
- `spikes/` (32 numbered + FINDINGS.md + 4 ADRs) is exemplary scientific practice.
- CI matrix exists (Python 3.11/3.12, ruff, pytest).
- User-level prompt-injection guard hook works.
- Sub-package separation is clean.

What's mismatched:
- **CLAUDE.md grade D.** Stale by 4 months. Says "Phase 1: PDF reader and OCR pipeline" (reality: ScholarGT Phase 1.1 done). Lists Serena/Context7/Sequential — Context7 not configured, Serena project-disabled. References `/project:plan` — no such command.
- **Zero domain agents.** All 20 are stock GSD. `grep` for "scholardoc|scholargt|GTElement|extractor|OCR" across `.claude/agents/` returns zero hits. Logan's domain (PDF extraction, OCR, GT schema, philosophy tagging) gets no specialized affordance.
- **GSD's signal/reflection capture is unused.** `.planning/knowledge/signals/` and `reflections/` are empty after 12 completed plans. The decision table in STATE.md substitutes informally; the structured channel goes dark.
- **3 memory systems, no convention.** `.serena/memories/` (15 files, all stale, project-disabled), `~/.claude/projects/.../memory/` (5 files, system-flagged stale at 42 days), `.planning/knowledge/` (empty). New agents have no way to know which is authoritative.
- **CI gap.** `.github/workflows/ci.yml` runs all tests. PDFs are gitignored. When tests reference fixture PDFs (already happening in `tests/unit/test_pdf_reader.py`), CI silently fails or fails loudly with no fetch script for `MANIFEST.md`'s 20 PDFs.
- **Hook drift.** Conventional Commits hook exists but is opt-in via `hooks.community: true` (currently off; commits already follow the convention so flipping it is free). `pip install` is allowlisted at user level despite CLAUDE.md claiming it's blocked.
- **116 modified `.claude/` files** — uncommitted GSD framework update. Cognitive overhead in every session.

---

## 5. GSD-2 Evaluation & Migration Plan

**Verdict: Useful eventually, NOT now. Inflection: Milestone 1 close → spike → Milestone 2 start.**

GSD-2 is the same maintainer's full architectural pivot from "Claude Code prompt framework" to "standalone TypeScript CLI on Pi SDK." It's not a refactor; it's a different tool. The README explicitly: GSD-1 is in maintenance, "active development happens in GSD-2."

What GSD-2 wins on (engineering substrate):
- Real state machine, real git-worktree isolation, real crash recovery (lock files, backoff restart), real cost tracking (per-unit ledger), multi-provider routing.
- Programmatic context injection per task instead of prompt-soup.
- Auto-mode dispatch with timeout supervision, stuck-loop detection, automatic verification with auto-fix retries.

What scholardoc loses on migration:
1. 19 custom `.claude/agents/gsd-*.md` (no equivalent surface in GSD-2; Scout/Researcher/Worker is its own agent set).
2. 4 hook scripts (`.claude/hooks/`) — needs porting to GSD-2's Layer 0/2 hook stack.
3. `REVIEW_STRATEGY.md` (16,717 bytes) and `REVIEW_AUDIT_LOG.md` (11,698 bytes) — bespoke peer-review files with no GSD-2 schema slot.
4. `.planning/knowledge/{signals,reflections,spikes}/` — closest analogue is GSD-2's flat KNOWLEDGE.md plus DB-backed memories (ADR-013). Direct mapping unclear.
5. `.planning/deliberations/` — GSD-Reflect-specific, no GSD-2 analogue.
6. `.planning/quick/` — GSD-2 has `/gsd quick` but storage shape differs.
7. `.serena/memories/` integration — Serena not bundled; coexists or is replaced by GSD-2 memory store.
8. Custom `.claude/commands/gsd/` — GSD-2 ships its own command set.
9. No `/gsd:upgrade-project` analog; `/gsd migrate` is one-way v1→v2.

What carries over via `/gsd migrate`: PROJECT.md, ROADMAP.md (`<details>` blocks and decimal phases supported per docs), REQUIREMENTS.md, phases/ → slices/, plan files → tasks, completion checkboxes, summaries.

**Cost (single-developer hours):** ~20–50h, mid-milestone, with disruption to a working flow.

**Stability concern:** v2.78.0 includes a major git-safety pass — TOCTOU ancestry guards, atomic sync-locks, EXDEV-safe write-gate, off-by-one fixes, fail-closed depth confirmation. v2.78.1 (Apr 25) fixed Windows spawn regressions. These are *recent* solidification, not battle-hardened. Wait for ≥v2.81 before moving production work.

**Sequenced recommendation:**
1. **Now → end of Phase 1.2:** stay on GSD-Reflect 1.20.5+. Phase 1.2 is queued and stalled; don't add tool-migration to its load.
2. **At Milestone 1 close (after Phase 5):** run a 1–2 day spike on a fresh clone. Test `/gsd migrate` on a *copy* of `.planning/`. Verify `<details>` blocks, decimal phases, gap-analysis files, CONTEXT files survive. Observe what's lost.
3. **At Milestone 2 start (only if):** spike succeeded AND GSD-2 hits ≥v2.81 with no regression in git-safety/recovery for 2–3 versions. Plan custom-agents/hooks/REVIEW_STRATEGY reimplementation as Phase 2.0 of Milestone 2.
4. **Earlier-migration tripwires:** GSD-2 hits "stable" tag, OR Logan moves to paid API and needs cost tracking, OR a crash recovery scenario costs >4h of rework, OR multi-provider becomes important.

---

## 6. Cross-Axis Gap Analysis

These are gaps no single audit owns alone — they emerge from cross-comparison.

| # | Gap | Evidence convergence | Severity |
|---|---|---|---|
| **G1** | Schema has never been validated by real annotation work | adversarial CRIT-1, CRIT-2, MED-1; codebase F6 (instantiation tests); doc-drift §7 (R3 never phased) | **CRITICAL** |
| **G2** | Doc/authority drift is unrepaired and now *worsening* | doc-drift §1 (every root doc Era 1), §7 (Phase 1.2 stalled, internal `.planning/` drift now exists); agential C5 (CLAUDE.md grade D) | **CRITICAL** |
| **G3** | 8 architectural decisions never formalized as ADRs | doc-drift §5 | HIGH |
| **G4** | Test count is 43–62% stale across docs; one missing fixture PDF cascades to 61 test failures | codebase F1; doc-drift §2 | HIGH |
| **G5** | "Universal" GT schema is calibrated-language failure | adversarial HIGH-2 | HIGH |
| **G6** | CryptOfCogito `scholarly_annotate` extraction is in tension with "prior projects are debris" feedback | adversarial HIGH-3 | HIGH (latent — bites at Phase 4) |
| **G7** | `.planning/knowledge/{signals,reflections,spikes}/` is the design-intended capture channel and it's empty after 12 plans | agential §"Memory" | HIGH |
| **G8** | Velocity dashboard performs speed; no tripwire for unbounded stretch | adversarial MED-2 | MEDIUM |
| **G9** | Two parallel OCR pipelines, legacy is the default | codebase F3 | MEDIUM |
| **G10** | `ground_truth/` is a third namespace, ownership undecided | codebase F10 | MEDIUM |
| **G11** | No domain-specific agents (`scholargt-schema-validator`, `scholargt-ocr-bench`, `gt-corpus-curator`) | agential §"Custom agent gap" | MEDIUM |
| **G12** | Phase 4 (annotation tool) decision (rewrite vs adapt CryptOfCogito) is deferred to Phase 4 planning; Phase 4 is months away; the rewrite-vs-adapt question affects scope | adversarial HIGH-3 | MEDIUM |
| **G13** | GSD-2 migration timing has no anchor; could drift past Milestone 2 if not pinned | gsd-2 research §"Tripwires" | LOW |
| **G14** | Milestone 2 content is undefined — "ScholarDoc improvements" is not a scope | adversarial LOW-2 | LOW |
| **G15** | `models.py` god-module split deferred to "when ScholarDoc work resumes" — no resumption trigger defined | codebase F4 | LOW |

---

## 7. Brainstorm — Uplift Ideas

Below is a brainstorm. The interventions registry (`06-interventions.md`) is the formalized version with sizing, sequencing, and dependencies.

**Methodological / strategic uplift:**
- Insert **Phase 1.5: Pilot annotation** (3–5 pages of real GT before Phase 2). Gives an empirical anchor; reduces the schema-validity convergent risk.
- Reorder Phase 3 (experimentation framework) before Phase 2 (extractor protocol). Per REVIEW_STRATEGY R6 — you can't really evaluate extractor adapters without metrics infrastructure.
- Write an **explicit "design-heavy" rationale** into PROJECT.md distinguishing Claim A (schema-first before mass annotation) from Claim B (whole-stack-first before any empirical anchor). Either justify B or back off to A.
- Add a **pre-mortem** to PROJECT.md: what conditions trigger Phase 2.x or 3.x insertions? Names the warning conditions explicitly so they're caught early.
- **Calibrate "universal"** in SCH-01 — rename to "cross-corpus extensible (current scope: scholarly humanities; expansion via SFP process)." Or document the SFP process as the universality mechanism.
- Disposition **ADR-021** (CryptOfCogito integrated architecture). Either write it or mark it superseded by ScholarGT independence.
- Define a **Milestone 2 anchor**: which ScholarDoc improvements, in what order, with what trigger.
- **Tripwire** for Milestone 1 stretch: "if Milestone 1 exceeds 4 months elapsed, trigger rescope review."

**Documentation / authority repair:**
- Execute Phase 1.2 plans (already roadmapped).
- Backfill **8 missing ADRs** for decisions in PROJECT.md / STATE.md.
- Replace the velocity metric with a calendar-elapsed metric.
- Update `docs/VISION.md` "Last verified" stamp or remove the stamp mechanism if not maintained.
- Triage `docs/` (~25 files) — mark each current/stale/historical/superseded.

**Repo / packaging:**
- Decide dual-package single-distribution vs `[tool.uv.workspace]` — write the ADR.
- Move `ground_truth/lib/` under `scholargt/evaluation/` (or explicitly keep it separate with rationale).
- Land a small fixture PDF (1–2 pages of Kant Critique) under `tests/fixtures/` to unblock the 61-test cascade.
- Resolve the `convert_pdf` ghost import — alias or rename to `convert`.
- Commit or revert the 116 `.claude/` modifications.
- Reconcile VERSION (1.16.0+dev) / config.json (1.18.3) / commit messages (v1.20.5).

**Agential dev uplift:**
- 3 domain agents: `scholargt-schema-validator`, `scholargt-ocr-bench`, `gt-corpus-curator`. Add 2 more once Phase 2 lands: `extractor-protocol-checker`, `scholargt-decision-archivist`.
- `MEMORY_MAP.md` orientation file documenting which memory system holds what.
- Backfill `.planning/knowledge/signals/` for Phase 1, 1.1 — start the signal capture habit.
- Rewrite CLAUDE.md as a real agent briefing (current branch, current focus, real MCP, real commands, real fixture-PDF policy, ScholarGT vs ScholarDoc map).
- Add a `tests/conftest.py` skip-marker `@pytest.mark.requires_corpus` so CI behaves coherently with the gitignored-PDF reality.
- Flip `hooks.community: true` in `.planning/config.json` to activate the Conventional Commits validator.
- Add a PreToolUse hook preventing edits to `scholargt/generated/schema.json` (regenerated, not edited).

**Methodological knowledge capture:**
- Run `/gsd:collect-signals` on Phase 1.1 to start the knowledge base.
- Audit `.serena/memories/` (15 files, all pre-Phase-1.1) — mass-deprecate or update.
- Decide where deliberations live (Phase 1.2 deliberation is the only one — codify the practice or drop it).

**GSD-2 path:**
- Spike `/gsd migrate` on a copy of `.planning/` at Milestone 1 close.
- Document migration decision criteria.
- If migration approved: phase-2.0 of Milestone 2 reimplements custom agents in GSD-2.

**Strategic / future:**
- OCR literature review (GLM-OCR and recent field advances) — separate phase before any OCR architecture decision.
- Ecosystem vision document (~/CLAUDE.md expansion) — out of scholardoc's scope but Logan's note.
- Hermeneutic-workspace-plugin integration plan — when both sides are ready.
- Cross-corpus validation — test "universal" claim with a non-philosophy corpus before SCH-01 hardens.

---

## 8. Recommended Sequencing

The interventions registry (`06-interventions.md`) sizes and sequences each item. The high-level recommendation:

**Tier 0 — Repair (do now, ≤ 1 week):**
- Commit or revert `.claude/` 116 modifications.
- Land fixture PDF under `tests/fixtures/`; fix three hardcoded paths.
- Fix `convert_pdf` ghost import.
- Reconcile VERSION / config.json / commit-message version chaos.

**Tier 1 — Phase 1.2 expansion (this milestone):**
- Execute Phase 1.2 plans 01.2-01..04 as roadmapped.
- Add Phase 1.2 plan 01.2-05: ADR backfill (8 missing ADRs).
- Add Phase 1.2 plan 01.2-06: domain agents + MEMORY_MAP.md.
- Add Phase 1.2 plan 01.2-07: signal-base backfill + knowledge audit.
- Calibrate SCH-01 wording during Phase 1.2.
- Disposition ADR-021.

**Tier 2 — Methodological insertion (before Phase 2):**
- **Phase 1.5: Pilot Annotation** (NEW — strongly recommended). Annotate 3–5 pages with v2.0.0 schema, surface schema gaps, decide whether they're "carried-forward refinements" or "schema rework needed."
- Decide whether to reorder Phase 3 before Phase 2 based on Phase 1.5 outcomes.
- Write the "design-heavy" rationale paragraph in PROJECT.md.

**Tier 3 — At Milestone 1 close:**
- GSD-2 migration spike.
- Velocity dashboard rewrite.
- Decide Milestone 2 anchor.

**Tier 4 — Milestone 2 onwards:**
- ScholarDoc improvements (writers/, models.py split, OCR-pipeline retire-legacy).
- OCR literature review.
- Hermeneutic-workspace integration.
- GSD-2 migration if approved.

---

## 9. Direct Answer to Your Asks

**"Where are we?"** Phase 1.1 of Milestone 1 (ScholarGT) is genuinely complete and well-built. Phase 1.2 (the repo reset that absorbs March's audit) is roadmapped but stalled at the planning step. Code state is healthy where active (ScholarGT) and bit-rotted where deferred (ScholarDoc). Documentation has Era-1/Era-3 drift across every root file. Working tree has 116 uncommitted GSD-framework files and a version chaos.

**"Where are we going?"** A 5-phase milestone toward a config-driven GT annotation platform with experimentation infrastructure. The direction is sound. The risk is that the schema (already designed) is the *only* part with empirical evidence, and the plan doesn't test it against real annotation until Phase 5. Three audits independently flagged this convergent risk.

**"Are we set up properly for agential development?"** 5/10. Heavy framework, no domain specialization, stale agent briefing, unused signal-capture channel. The fixes are concrete and small. After ~10–15 hours of focused work this becomes a 7–8/10 setup.

**"How do we uplift the repo?"** See §7 (brainstorm) and `06-interventions.md` (registry). The biggest single move is inserting **Phase 1.5: Pilot Annotation** before Phase 2 — it dissolves the convergent schema-validity risk and costs ~1 week. The second biggest is executing Phase 1.2 as roadmapped (it's already there, just stalled). The third is the 3 domain agents (specialized payoff over months).

**"GSD-2?"** Yes eventually, no now. Spike at Milestone 1 close on a copy. Migrate at Milestone 2 start *if* spike succeeds and GSD-2 ships ≥v2.81 with stable git-safety. Migration breaks 19 custom agents, hooks, REVIEW_STRATEGY.md, and the deliberations pattern — costs 20–50h with mid-milestone disruption. Right tool, wrong moment.

**"Are we well prepared for where we are going?"** *Adequately, not strongly.* The discipline is real (REVIEW_STRATEGY, deliberations, calibrated triage). The fragility is that the discipline is producing diagnoses faster than the roadmap absorbs them — six waves of identified work, two waves phased. Phase 1.2 is the test of whether the team can execute what it has already named.

**"Concrete interventions?"** See `06-interventions.md` — 30+ actionable items, each tagged Repair/Methodological/Doc/Code/Agential/Strategic with sizing (XS/S/M/L) and recommended placement (current milestone / next milestone / backlog).

---

*End of synthesis. Next: read `06-interventions.md` for the actionable registry, then decide which to formalize as Phase 1.2 plan additions, new phases, or backlog items.*
