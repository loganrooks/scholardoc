# Interventions Registry — ScholarDoc/ScholarGT

**Date:** 2026-05-01 | **Companion to:** `00-SYNTHESIS.md`
**Purpose:** Actionable registry for formalization. Each intervention is sized, typed, sequenced, and traceable to audit evidence. The user (Logan) decides which to formalize as Phase 1.2 plan additions, new phases, quick tasks, or backlog items.

## Legend

| Type | | Sizing | |
|---|---|---|---|
| **REPAIR** | Fix broken state | **XS** | < 1h |
| **DOC** | Documentation/authority work | **S** | 1–4h |
| **METHOD** | Methodological / strategic | **M** | half-day to 1 day |
| **CODE** | Code quality | **L** | 2–5 days |
| **AGENT** | Agential infrastructure | **XL** | 1+ week (becomes a phase) |
| **KB** | Knowledge capture |  | |
| **ADR** | Decision record |  | |
| **TOOL** | Tooling/migration |  | |
| **FUTURE** | Strategic/long-term |  | |

**Placement codes:** `T0` = do now, ≤ 1 week | `1.2+` = add to Phase 1.2 | `1.5*` = new Phase 1.5 (proposed) | `M1-close` = at Milestone 1 close | `M2` = Milestone 2 | `B` = backlog (no current trigger).

---

## Tier 0 — Repair (do this week, ≤ 1 week total)

### R1 [REPAIR/XS/T0] Commit or revert the 116 `.claude/` modifications
**Why:** Working tree noise costs cognitive overhead every session. VERSION says `1.16.0+dev`, config.json says `1.18.3`, recent commit messages reference `v1.20.5`. The state is incoherent.
**What:** `git diff .claude/` to confirm the changes are a clean GSD-Reflect update; commit with `chore: finalize GSD framework update to vX.Y.Z` and pick the right VERSION; OR `git checkout -- .claude/` to revert and re-run `/gsd:update` cleanly.
**Evidence:** agential-readiness §"Bottom line", `git status` 116 files modified.
**Deps:** none.

### R2 [REPAIR/S/T0] Land a small Kant fixture PDF + rewrite three hardcoded paths
**Why:** 32 unit failures + 29 collection errors all from `spikes/sample_pdfs/kant_critique_pages_64_65.pdf` (gitignored). Tests cannot be trusted as a signal until this is fixed.
**What:** Add 1–2 page Kant Critique PDF (public domain) to `tests/fixtures/kant_minimal.pdf`. Add a `kant_pdf` fixture in `tests/conftest.py`. Rewrite `tests/unit/test_pdf_reader.py:30`, `tests/unit/test_extractors.py:38`, `tests/unit/test_ocr_pipeline.py:360` to use the fixture.
**Evidence:** codebase-quality F1.
**Deps:** none.

### R3 [REPAIR/XS/T0] Fix `convert_pdf` ghost import
**Why:** `tests/integration/test_ground_truth_regression.py:103` does `from scholardoc.convert import convert_pdf` — symbol does not exist. Currently masked by skip; fails first time a regression PDF lands.
**What:** Either (a) rename to `convert` and update fixture call site; OR (b) add `convert_pdf = convert` alias in `scholardoc/convert.py`.
**Evidence:** codebase-quality F2.
**Deps:** none.

### R4 [REPAIR/XS/T0] Add `pytest.mark.slow` to `pyproject.toml` known marks
**Why:** Live `pytest --collect-only` warns "Unknown pytest.mark.slow - is this a typo?" because the mark is used but unregistered. Either it's a real mark (register it) or a typo (rename).
**What:** Add to `[tool.pytest.ini_options]`: `markers = ["slow: long-running OCR tests", "requires_corpus: tests needing gitignored PDFs"]`. The `requires_corpus` mark also serves R12.
**Evidence:** codebase-quality (test collection warning).
**Deps:** none.

### R5 [REPAIR/XS/T0] Update `.planning/STATE.md` to reflect Phase 1.2 in roadmap
**Why:** STATE.md was edited 2026-04-16 alongside ROADMAP.md but does not mention Phase 1.2's insertion; "current focus" still reads as if Phase 2 is next. Internal `.planning/` drift now exists.
**What:** Update STATE.md "Current Position" and "Roadmap Evolution" sections to reflect Phase 1.2 insertion. Update the "Last activity" line.
**Evidence:** doc-drift §1.
**Deps:** none.

---

## Tier 1 — Phase 1.2 Expansion (add to current Phase 1.2)

The roadmap entry for Phase 1.2 lists 4 plans (01.2-01..04). Audit evidence supports adding 3 more plans (01.2-05..07) covering ADR backfill, agential uplift, and knowledge-base seeding. All can run in parallel waves.

### Existing Phase 1.2 plans (already roadmapped, restate scope per audit findings)

| Plan | Title | Audit notes / refinements |
|---|---|---|
| 01.2-01 | Authority reset — align README, CLAUDE.md, root ROADMAP, docs/VISION, STATE.md | doc-drift §1 confirms severity. Add: archive root `ROADMAP.md` as "Era 1 history" (B2). Mark `docs/VISION.md` `<!-- Last verified -->` stamp policy (renew or remove). |
| 01.2-02 | Verification reset — fix documented commands, fixture policy, regression-harness | Folds R2, R3, R4 above. Add: document `requires_corpus` skip-marker policy. Confirm CI behaves coherently when corpus PDFs absent. |
| 01.2-03 | Legacy boundary + packaging decision (`ground_truth/`, uv workspace) | codebase F10: `ground_truth/lib/` is *actively imported* (1207 LOC). Decide: move under `scholargt/evaluation/` OR keep separate. Decide uv workspace yes/now. Either way: write ADR. |
| 01.2-04 | Phase 2 contract definition — extractor protocol, provenance, runtime/persistence boundary | No audit refinement. Already well-scoped per the deliberation. |

### New plans proposed for Phase 1.2

### R6 [DOC/M/1.2+] Plan 01.2-05: ADR Backfill
**Why:** 8 architectural decisions made Jan–April 2026 live in PROJECT.md tables and STATE.md bullets — never in `docs/adr/` where every root doc points readers. ADR system itself has drifted to Era-1-only.
**What:** Backfill 8 ADRs (using existing ADR template structure):
- ADR-005: ScholarGT independence from ScholarDoc
- ADR-006: Cascading extraction over probabilistic fusion
- ADR-007: Config-driven label selection (universal-superset principle)
- ADR-008: Pluggable extractors with provenance tracking (Phase 2 protocol)
- ADR-009: Schema v2.0.0 — SFP-1..6 absorption (LayoutRegister, text_direction, ScriptVariant, COLOR, INDEX_AREA, CATCHWORD)
- ADR-010: Single-repo dual-package vs uv workspace (decision per 01.2-03)
- ADR-011: Hybrid PageQuality (replaces ScanQuality enum)
- ADR-012: ADR-021 disposition (write or supersede; see R13)
**Evidence:** doc-drift §5.
**Deps:** 01.2-01 (authority reset).
**Sizing:** ~1h per ADR with template; M total.

### R7 [AGENT/L/1.2+] Plan 01.2-06: Domain agents + MEMORY_MAP
**Why:** Zero domain specialization across 20 agents and 36 commands. Three memory systems with no convention. Logan's domain (PDF, OCR, GT schema) gets no specialized affordance.
**What:**
1. Build `.claude/agents/scholargt-schema-validator.md` — given a YAML profile + GTElement, validates and runs `jsonschema` against `scholargt/generated/schema.json`.
2. Build `.claude/agents/scholargt-ocr-bench.md` — runs an extractor against `ground_truth/ocr_quality/`, computes WER/CER vs baselines, writes a signal.
3. Build `.claude/agents/gt-corpus-curator.md` — diffs `spikes/sample_pdfs/MANIFEST.md` against gitignored disk contents.
4. Write `.planning/MEMORY_MAP.md` — orientation file: where decisions live (PROJECT.md), where signals live (`.planning/knowledge/signals/`), where session handoffs live (STATE.md "Session Continuity"); deprecate `.serena/memories/` until audited.
5. Update CLAUDE.md MCP table to reflect what's actually running (only sequential-thinking).
**Evidence:** agential-readiness §"Custom agent gap analysis", §"Memory system map".
**Deps:** R1 (clean working tree).

### R8 [KB/S/1.2+] Plan 01.2-07: Signal/reflection backfill + Serena audit
**Why:** `.planning/knowledge/{signals,reflections,spikes}/` empty after 12 plans. GSD's signal-collection design intent unused. `.serena/memories/` has 15 stale files.
**What:**
1. Run `/gsd:collect-signals` for Phase 1 and Phase 1.1 to backfill the knowledge base.
2. Audit 15 `.serena/memories/` files: mark current/stale/superseded; delete or update.
3. Flip `hooks.community: true` in `.planning/config.json` to activate Conventional Commits validator (commits already follow convention; flipping is free).
**Evidence:** agential-readiness §"Memory system map", §"Bottom line".
**Deps:** none.

### R9 [DOC/S/1.2+] Calibrate SCH-01 "Universal" wording
**Why:** "Universal GT schema" overclaims. Schema is scholarly-philosophical-corpus + extensible-process. SFP-1..6 already proved the schema isn't actually universal (RTL was 33% of corpus and unanticipated in v1).
**What:** Rewrite SCH-01 in `.planning/REQUIREMENTS.md`: "Cross-corpus extensible GT schema (current scope: scholarly humanities; expansion via SFP process)." OR add a paragraph to PROJECT.md naming the SFP process as the universality mechanism.
**Evidence:** adversarial HIGH-2.
**Deps:** none. Folds into 01.2-01 (authority reset).

### R10 [DOC/S/1.2+] Write the "design-heavy" rationale
**Why:** "Design-heavy" frame defends two distinct claims (schema-first vs whole-stack-first) but PROJECT.md only justifies the first. The second is what the roadmap actually commits to.
**What:** Add a paragraph to PROJECT.md "Constraints" section distinguishing Claim A ("get schema right before mass annotation") from Claim B ("build whole stack before any empirical anchor"). Argue for B explicitly OR back off to A by adopting Phase 1.5 (R14).
**Evidence:** adversarial CRITICAL-2.
**Deps:** R14 decision (Phase 1.5 yes/no).

### R11 [METHOD/XS/1.2+] Add Milestone 1 stretch tripwire to PROJECT.md
**Why:** No commitment that catches unbounded milestone stretch. Velocity dashboard performs speed; calendar reality says months between phase boundaries.
**What:** Add to PROJECT.md "Constraints" or "Decision Log": "If Milestone 1 elapses >4 months, trigger rescope review. If it elapses >6 months, default to Milestone 1 close at next phase boundary regardless of plan completion."
**Evidence:** adversarial MEDIUM-2.
**Deps:** none.

### R12 [METHOD/XS/1.2+] Add Phase 2.x/3.x pre-mortem to PROJECT.md
**Why:** Reset pattern showing up twice (Phase 0, Phase 1.2). If a third reset becomes necessary, the team should have warning conditions explicit, not discovered in flight.
**What:** Add a "Pre-mortem" section to PROJECT.md naming what could trigger Phase 2.x or 3.x insertions. E.g., "Phase 5 pilot annotation surfaces schema rework needs", "OCR literature review (R5) reveals new evaluation methodology requiring framework rework", "extractor protocol contradicts schema assumptions."
**Evidence:** adversarial HIGH-4.
**Deps:** none.

### R13 [ADR/XS/1.2+] ADR-021 disposition
**Why:** "ADR-021 needed (CryptOfCogito integrated architecture) — never written" — strategic decision in limbo since at least March 2026.
**What:** Decide: write ADR-021 in scholardoc/docs/adr/ as "ScholarGT Independence (Supersedes CryptOfCogito Integration ADR-021)" with one-line pointer to ADR-005 (R6); OR mark superseded in CryptOfCogito's tracker.
**Evidence:** doc-drift §5, adversarial MEDIUM-3, REVIEW_STRATEGY E11.
**Deps:** R6 (ADR-005).

---

## Tier 2 — Methodological Insertion (before Phase 2)

### R14 [METHOD/XL/1.5*] **Insert Phase 1.5: Pilot Annotation** *(strongly recommended)*
**Why:** **Single highest-leverage intervention.** Three independent audit findings converge: schema (Phase 1+1.1) has never been tested against real annotation work. Phase 5 is the only phase that touches real GT, and it's at the end of the chain. Risk: Phases 2/3/4 built on a schema whose validity is asserted, not demonstrated.
**What:** New phase between 1.2 and 2:
- **Goal:** Annotate 3–5 pages from corpus using v2.0.0 schema. Document what worked, what didn't fit, what required `extra="allow"` escapes, what needed schema rework.
- **Plans:**
  - 01.5-01: Annotation tooling decision — minimal CLI/JSON entry vs adapting CryptOfCogito viewer (decide R15 here, not at Phase 4)
  - 01.5-02: Pilot annotation execution — 3-5 pages, tracking schema gaps as signals
  - 01.5-03: Schema gap synthesis — categorize (carried-forward/rework-needed/SFP-process), update PROJECT.md "design-heavy" rationale (R10) with concrete evidence
- **Success criteria:**
  1. ≥3 pages of verified GT exist using v2.0.0 schema
  2. Schema gap report names every place v2.0.0 fell short, classified
  3. Phase 2 readiness gate: schema is empirically validated OR a Phase 1.6 schema-rework phase is planned
- **Sizing:** 1–2 weeks elapsed, ~30–60 hours active work.
**Evidence:** adversarial CRITICAL-1, CRITICAL-2, MEDIUM-1; codebase F6 (instantiation tests don't validate behavior); doc-drift §7 (R3 never phased).
**Deps:** Phase 1.2.
**Alternative:** R10 documented bounded-risk argument can substitute IF Logan judges existing gap-analysis-vs-85-phenomena to be sufficient. Pick one.

### R15 [METHOD/M/1.5*] Decide Phase 4 annotation-tool framing now (not later)
**Why:** REVIEW_STRATEGY R4's "Extract CryptOfCogito tool into scholarly_annotate" is exactly the merge anti-pattern Logan rejected (`feedback_projects_as_debris`). Deferring to Phase 4 planning means the rejected framing arrives pre-loaded.
**What:** Add to PROJECT.md Key Decisions table: either (a) "scholarly_annotate is design inspiration only; ScholarGT annotation tool is built fresh from extracted lessons" OR (b) "scholarly_annotate is extracted-and-rebuilt with rationale acknowledging the prior commitment." Decide before Phase 4 planning so the deferred decision arrives clean.
**Evidence:** adversarial HIGH-3, feedback_projects_as_debris.
**Deps:** none. Folds into 01.5-01 if Phase 1.5 adopted.

### R16 [METHOD/S/1.5*] Decide Phase 3-before-Phase-2 reordering
**Why:** REVIEW_STRATEGY R6 explicitly recommended this. C2 checklist item unticked. The argument: you can't really evaluate extractor adapters (Phase 2) without metrics infrastructure (Phase 3).
**What:** After Phase 1.5 outcomes (or in absence, on R10 evidence), formally decide via PROJECT.md Decision Log entry: keep current order OR swap. If swap: update ROADMAP.md.
**Evidence:** adversarial CRITICAL-1, REVIEW_STRATEGY R6/C2.
**Deps:** R14 outcomes.

---

## Tier 3 — At Milestone 1 Close

### R17 [TOOL/M/M1-close] GSD-2 migration spike
**Why:** GSD-2 is genuinely better engineering substrate but breaks 19 custom agents, hooks, REVIEW_STRATEGY.md, deliberations pattern. Need empirical migration cost before commitment.
**What:** Fresh clone of scholardoc. Run `/gsd migrate` on a copy of `.planning/`. Verify `<details>` blocks, decimal phases (1.1, 1.2, 1.5), gap analysis files, CONTEXT files survive. Document what's lost. Estimate full reimplementation hours.
**Evidence:** gsd-2 research §"Recommendation".
**Deps:** Phase 1.2 + Phase 1.5 + Phases 2..5 closed.

### R18 [METHOD/S/M1-close] Velocity dashboard rewrite
**Why:** STATE.md "Total execution time: 0.8 hours, average 4.0 min/plan" performs speed. Calendar reality is 2.5 months for 3 phases.
**What:** Replace plan-minutes metric with calendar-elapsed columns (phase start date, phase end date, weeks elapsed). Optional: keep plan-minutes as secondary metric.
**Evidence:** adversarial MEDIUM-2.
**Deps:** none.

### R19 [METHOD/S/M1-close] Define Milestone 2 anchor
**Why:** PROJECT.md says ScholarDoc improvements "deferred to Milestone 2" but Milestone 2's content unspecified. Without anchor, deferred work has nowhere to land.
**What:** Add Milestone 2 outline to PROJECT.md: which ScholarDoc improvements (writers/, models.py split, OCR-pipeline retire-legacy), in what order, with what trigger. Optionally: Milestone 2 is "GSD-2 migration + ScholarDoc reactivation" if R17 spike succeeds.
**Evidence:** adversarial LOW-2.
**Deps:** R17 outcome.

---

## Tier 4 — Milestone 2 onwards

### R20 [CODE/L/M2] Retire legacy OCR pipeline
**Why:** Two parallel OCR pipelines, legacy is the default. 2,472 lines of duplicate-purpose code with two APIs.
**What:** Delete `scholardoc/normalizers/ocr_pipeline.py` (708 LOC) and dead branches in `convert.py:103-105, 207-235`. Make new pipeline the default. Add deprecation warning ahead of removal.
**Evidence:** codebase-quality F3.
**Deps:** Milestone 2 ScholarDoc reactivation trigger.

### R21 [CODE/L/M2] Split `scholardoc/models.py`
**Why:** 1524-line god module with 27 classes. ScholarGT decomposes equivalent surface across 8 files.
**What:** Split into `models/spans.py`, `models/annotations.py`, `models/quality.py`, `models/document.py`. Move `ScholarDocument.to_markdown()` to `writers/` (R22 unblocked).
**Evidence:** codebase-quality F4.
**Deps:** R20 (less surface area to split).

### R22 [CODE/M/M2] Implement `scholardoc/writers/`
**Why:** 1-line stub since Dec 2025. `to_markdown()` lives in models.py instead.
**What:** Move write methods from models.py to `writers/markdown.py`, `writers/json.py`, `writers/rag_chunks.py`. Keep model methods as thin wrappers.
**Evidence:** codebase-quality F8.
**Deps:** R21.

### R23 [CODE/S/M2] Strict-mode validator path for CI
**Why:** `extra="allow"` on 4 of 5 top-level scholargt models silently accepts typos. Tests catch nothing.
**What:** Add a strict-mode validation path: rebuild GTElement/PageGT/DocumentGT/GTProfile with `extra="forbid"` for CI runs. Accept warnings on real annotation paths (extra="allow" stays for incremental annotation), but flag unknown fields in test/CI.
**Evidence:** codebase-quality F5.
**Deps:** none.

### R24 [CODE/S/M2] Profile YAML enum-membership validation
**Why:** Profiles can ship with `text_blok` typo and CI passes.
**What:** Add validator to `GTProfile` checking spatial/semantic categories against `SpatialLabel`/`SemanticElementType` enum unions, with documented escape hatch for custom project labels.
**Evidence:** codebase-quality F7.
**Deps:** none.

### R25 [METHOD/L/M2] OCR literature review
**Why:** GLM-OCR and recent field advances (REVIEW_STRATEGY R5/E10) never reviewed. Two valid OCR approaches in scholardoc orbit (text-layer-first vs vision-first); decision deferred indefinitely.
**What:** Phase plan: literature review covering GLM-OCR, recent VLM advances, structured comparison vs current docTR-based pipeline. Output: ADR + signal capture + decision on OCR approach for next ScholarDoc work.
**Evidence:** REVIEW_STRATEGY R5/E10/Wave 6.
**Deps:** Milestone 2 ScholarDoc reactivation trigger.

---

## Tier 5 — Backlog (no current trigger, named to prevent silent drift)

### R26 [FUTURE/XL/B] Cross-corpus universality validation
**Why:** "Universal" claim untested for non-philosophy corpora. Pattern of post-hoc SFP additions likely to repeat.
**What:** Pilot annotate 3–5 pages from a non-philosophy corpus (scientific paper, technical manual, archival manuscript). Document SFPs needed. Decide: schema is genuinely universal OR rename to "scholarly humanities."
**Evidence:** adversarial HIGH-2.
**Trigger:** First non-philosophy use case OR third post-v2.0.0 SFP addition.

### R27 [FUTURE/L/B] Hermeneutic-workspace-plugin integration plan
**Why:** REVIEW_STRATEGY R2/G1: scholardoc should power the workspace's `source_ingest` pipeline. Documented intent prevents duplicating extraction logic.
**What:** Document the scholardoc → hermeneutic-workspace-plugin interface (ScholarDocument → workspace library model with R-NNNN IDs).
**Evidence:** REVIEW_STRATEGY R2.
**Trigger:** Workspace's `source_ingest` skill needs an extraction engine.

### R28 [FUTURE/M/B] Ecosystem vision document
**Why:** REVIEW_STRATEGY R1: 14+ project ecosystem with vision distributed across CLAUDE.md files. No single reference point.
**What:** Expand `~/CLAUDE.md` "Project Ecosystem" section into an architectural overview. Out of scholardoc's scope but logged for owner attention.
**Evidence:** REVIEW_STRATEGY R1.
**Trigger:** Logan decides ecosystem coordination needs a single reference.

### R29 [TOOL/L/B] GSD-2 full migration
**Why:** GSD-1 in maintenance per maintainer; GSD-2 is "the future." Eventual end-of-life of current setup.
**What:** Conditional on R17 spike outcomes. If approved: Milestone 2 Phase 2.0 reimplements custom agents, hooks, REVIEW_STRATEGY pattern in GSD-2.
**Evidence:** gsd-2 research.
**Trigger:** R17 spike succeeds AND GSD-2 ≥v2.81 with stable git-safety AND no major regressions for 2-3 versions.

---

## Summary Tables

### By Tier (recommended sequencing)

| Tier | Items | Total sizing | Goal |
|---|---|---|---|
| **T0 — Repair** | R1–R5 | ~6h | Fix broken state. Working tree, tests, STATE drift. |
| **T1 — Phase 1.2 expansion** | R6–R13 | ~30–40h | Execute the queued reset, with audit-informed additions. |
| **T2 — Methodological** | R14–R16 | ~30–60h (R14 dominant) | Insert empirical anchor before Phase 2. |
| **T3 — M1-close** | R17–R19 | ~10–15h | GSD-2 spike, velocity rewrite, M2 anchor. |
| **T4 — M2 onwards** | R20–R25 | ~3–6 weeks | Reactivate ScholarDoc, OCR review. |
| **T5 — Backlog** | R26–R29 | conditional | Named so they don't fade. |

### By Type

| Type | Count | Items |
|---|---|---|
| REPAIR | 5 | R1–R5 |
| DOC | 4 | R9, R10, R6 (also ADR), part of 1.2-01 |
| METHOD | 7 | R10–R12, R14–R16, R18, R19, R25 |
| CODE | 4 | R20–R24 |
| AGENT | 1 (multi-part) | R7 |
| KB | 1 | R8 |
| ADR | 2 | R6, R13 |
| TOOL | 2 | R17, R29 |
| FUTURE | 4 | R26–R29 |

### Decision points the user owns

| # | Decision | Trigger |
|---|---|---|
| 1 | Phase 1.5 yes/no (or R10 documented argument substitute) | Before Phase 2 planning |
| 2 | Phase 3 before Phase 2 reorder | After Phase 1.5 outcomes |
| 3 | scholarly_annotate framing (rebuild fresh vs extract-and-update) | Before Phase 4 planning |
| 4 | uv workspace yes/now vs deferred (per 01.2-03) | During Phase 1.2 |
| 5 | `ground_truth/lib/` ownership (under scholargt vs separate) | During Phase 1.2 |
| 6 | GSD-2 migration approve/decline | After R17 spike |
| 7 | Milestone 2 anchor (ScholarDoc-only vs GSD-2-migration-included) | Before M2 |

---

*End of registry. Next: select interventions, formalize as Phase 1.2 plans (or new phases) using `/gsd:add-phase` or by editing `.planning/ROADMAP.md` and creating phase directories.*
