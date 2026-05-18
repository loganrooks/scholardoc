# Documentation Authority Drift Audit

> **Date:** 2026-05-01 | **Sources:** direct grep of 10 listed files, live `pytest --collect-only`, `git log`, `stat`, inspection of `scholardoc/__init__.py`

## Top-line Verdict

**Drift severity: SEVERE and unrepaired.** REVIEW_STRATEGY.md's diagnosis is correct and slightly understated. Six weeks after the March audit, no Wave 2-6 work has shipped. Phase 1.2 was added to `.planning/ROADMAP.md` on 2026-04-16 (uncommitted) but is unstarted. **Every root-level doc still reflects Era 1** (ScholarDoc-only, Phase 1 in-progress, Dec 2025). Zero root docs mention "ScholarGT", "scholargt", or "measurement". One new symptom since March: STATE.md and ROADMAP.md were both edited 2026-04-16, but STATE.md was not updated to reflect Phase 1.2's insertion — internal drift now exists *within* `.planning/`.

The `convert()` API still works (`scholardoc/__init__.py` exports it). But the `/project:plan`, `/project:tdd`, `/project:annotate`, `/project:explore`, `/project:implement`, `/project:refactor`, `/project:spike` slash commands referenced in CLAUDE.md, RULES.md, COMMANDS.md **do not exist** — only `.claude/commands/gsd/*` exist.

## 1. Authority Comparison Matrix

| File | mtime | "Current phase" claim | "Primary deliverable" | Era |
|------|-------|------------------------|------------------------|-----|
| `CLAUDE.md` | 2026-01-06 | "Phase 1: Core Implementation"; "Current: Integrate validated OCR pipeline" (lines 18-21) | ScholarDoc PDF→ScholarDocument lib | **1** |
| `README.md` | 2025-12-23 | "Phase 1 - Core Implementation (OCR pipeline integration)" (line 3, 43) | ScholarDoc; `scholardoc.convert()` API | **1** |
| `ROADMAP.md` (root) | 2026-01-06 | "Phase 1 Complete - OCR Integration Done" (l.3); "Phase 2 (Next): Footnote extraction" (l.12) | ScholarDoc; phases 2-4 = footnotes/formats/OCR | **1** |
| `SPEC.md` | 2025-12-23 | "Draft (Phase 0 validated)" (l.3) | ScholarDoc, `convert(path)→ScholarDocument` | **1** |
| `REQUIREMENTS.md` (root) | 2025-12-23 | "Active Development (Phase 1)" (l.3) | ScholarDoc, US-1..US-12 | **1** |
| `QUESTIONS.md` (root) | 2025-12-18 | "Phase 0 exploration complete" (l.7) | ScholarDoc OCR/structure Qs | **1** |
| `docs/VISION.md` | 2026-01-06 | None; "Last verified: 2025-12-27" (l.4) | ScholarDoc only | **1** |
| `.planning/PROJECT.md` | 2026-02-18 | "Active (Milestone 1 — ScholarGT focused)" (l.30) | **ScholarGT**; ScholarDoc = plugin | **3** |
| `.planning/ROADMAP.md` | 2026-04-16 (uncommitted) | "Phase 1.2: Repo Governing Reset (Not started)"; Phase 1.1 complete 2026-02-20 | ScholarGT platform | **3+** |
| `.planning/STATE.md` | 2026-04-16 (uncommitted) | "Phase 1.1 of 5 ... Phase 1.1 Complete" (l.14) — **does not mention Phase 1.2** | ScholarGT Phase 1.1 complete | **3** |

The pointer cascade (README→CLAUDE.md→docs/VISION.md; SPEC.md/REQUIREMENTS.md→CLAUDE.md#Vision) resolves cleanly mechanically. Semantically all five describe Era 1. `.planning/PROJECT.md` — the actual current authority — is referenced by no root-level doc. CLAUDE.md "Quick Start" tells new readers to "Check ROADMAP.md for current phase" — meaning the Era-1 root ROADMAP.

## 2. Test-Count Truth Table

**Reality (live, 2026-05-01): `pytest --collect-only` reports 694 tests** (one `pytest.mark.slow` warning).

| Doc | file:line | Claim | Delta |
|-----|-----------|-------|-------|
| Root ROADMAP.md | line 201 | "257 tests passing" (Phase 1.1 milestone) | -437 (62% stale) |
| Root ROADMAP.md | line 264, 278 | "320 tests passing" | -374 (54%) |
| Root ROADMAP.md | line 616 | "Phase 1 Complete: 349 tests passing" | -345 (50%) |
| .planning/PROJECT.md | line 65 | "ScholarDoc: 395 tests, 87% coverage" | -299 (43%) |
| .planning/STATE.md | line 15 | "312 passing tests for v2.0.0" | -382 (55%) |
| .planning/REVIEW_STRATEGY.md | lines 105, 219 | "312 tests provide confidence" / "Verify 312+" | -382 (55%) |

**Most-stale claim:** root ROADMAP.md line 201 ("257"). Root ROADMAP.md is the only file telling the test-count story across three different snapshots in one document. The drift is non-monotonic: 312 was the Phase 1.1 schema baseline, and the count grew with SFP plans 01.1-02 through 01.1-05 (and `tests/` for scholardoc continues to exist alongside `scholargt/tests/`). Today's 694 is roughly double anything documented.

## 3. Stale References (file:line)

**Slash commands that don't exist** (only `.claude/commands/gsd/*` is installed):
- `CLAUDE.md:8` `/project:plan`; `CLAUDE.md:38` & `docs/RULES.md:7` `/project:tdd`
- `docs/COMMANDS.md:36, 46-53` — `/project:annotate`, `/project:explore`, `/project:plan`, `/project:spike`, `/project:implement`, `/project:tdd`, `/project:refactor`

**Stale phase claims:**
- `CLAUDE.md:19-21` "Current: Integrate validated OCR pipeline" — completed 2025-12-29 (root ROADMAP l.615).
- `README.md:43` "Phase 1: Core Implementation" — Phase 1 closed Dec 2025; Era 3 ScholarGT milestone is active and unmentioned.
- `README.md:39` "full scanned document support is Phase 4" — invalidated by REVIEW_STRATEGY R5.
- `docs/VISION.md:4` "Last verified: 2025-12-27" — pre-Era-2/3.

**Stale Serena memory refs:** `CLAUDE.md:9` "Use Serena memories: `ocr_pipeline_architecture`, `session_handoff`" — predate Era 3 pivot; Wave 1 R8 memory audit never done.

**API and corpus paths verified working:**
- `README.md:62-83` — `scholardoc.convert(path)` **WORKS** (signature `convert(source, config=None) -> ScholarDocument`).
- `docs/TESTING_METHODOLOGY.md` — `ground_truth/validation_set.json`, `spikes/30_validation_framework.py` both exist.
- `spikes/sample_pdfs/` and `test_files` symlink intact.

## 4. docs/ Directory Triage

| File | mtime | Status |
|------|-------|--------|
| `VISION.md` | 2026-01-06 | **STALE** Era-1, self-declared authoritative; no ScholarGT |
| `COMMANDS.md`, `RULES.md` | 2026-01-06 | **STALE** — both reference `/project:*` commands that don't exist |
| `AUTOMATION_SETUP.md` | 2025-12-23 | **STALE** — claims "✅ IMPLEMENTED" pre-GSD hooks |
| `INIT_TEMPLATES.md`, `LOG_ANALYSIS_AUTOMATION.md` | 2026-01-06 | **HISTORICAL** — `/project:init`, `/project:analyze-logs` never wired |
| `BEST_PRACTICES_ANALYSIS.md` | 2025-12-13 | **HISTORICAL** Dec 2025 critique, pre-GSD |
| `parallelization-guide.md` | 2025-12-26 | **DUPLICATE/HISTORICAL** — superseded by GSD waves |
| `GIT_WORKFLOW.md`, `TESTING_METHODOLOGY.md` | 2026-01-06 | **CURRENT** (paths/branching still valid) |
| `adr/ADR-001..004` | Dec 2025 - Jan 2026 | **CURRENT for ScholarDoc**; ADR-001 header still says "PROPOSED - Pending Spike Validation" though spikes ran |
| `decisions/DECISION_LOG.md` | 2025-12-13 | **EMPTY** — header + "## December 2025" stub, no entries |
| `design/CORE_REPRESENTATION.md`, `STRUCTURE_EXTRACTION.md`, `QUALITY_FILTERING.md` | Dec 2025 | Implemented in `scholardoc/`; doc status still "Proposal" |
| `design/CORE_ABSTRACTION.md`, `EXTENSIBILITY.md`, `FEEDBACK_SYSTEM.md`, `OCR_STRATEGY.md`, `PROCESSING_ARCHITECTURE.md`, `CUSTOM_OCR_DESIGN.md`, `SOUS_ERASURE_DESIGN.md` | Dec 2025 | **HISTORICAL** Proposals/drafts; mostly pre-pivot |
| `design/GROUND_TRUTH_STRATEGY.md` | 2025-12-13 | **SUPERSEDED** by `docs/gt/SCHEMA_GUIDE.md` |
| `design/PROPRIETARY_CITATIONS.md` | 2026-02-18 | **STALE** — cites "Phase 2.4" no longer in roadmap |
| `design/SAMPLE_PDF_ORGANIZATION.md` | 2026-02-18 | **STALE** Proposal |
| `gt/SCHEMA_GUIDE.md` + `gt/examples/*.json` | 2026-02-19 | **CURRENT, AUTHORITATIVE** — only Era-3 docs in `docs/` |

**Pattern:** `docs/` is a Dec 2025 - Jan 2026 fossil bed with two Era-3 survivors (`docs/gt/`). REVIEW_STRATEGY.md B8 ("Review 12 files; mark each") was never executed; this audit just performed it.

## 5. ADR Coverage Gaps

ADR-001..004 remain valid for ScholarDoc. **No ADRs exist for any major decision made Jan-April 2026:**

| Missing ADR | Currently lives in |
|-------------|--------------------|
| ScholarGT independence from ScholarDoc | PROJECT.md l.111; STATE.md `[01-01]` |
| CascadingExtractor over probabilistic fusion (spike 26: 21% agreement) | Root ROADMAP l.601 (decision-log row) |
| Config-driven label selection (GTProfile, universal superset) | PROJECT.md principle 4; STATE.md `[01-03] [01.1-04]` |
| Pluggable extractors with provenance (Phase 2 Protocol) | PROJECT.md l.116; ROADMAP Phase 2 |
| SFP-1..6 schema redesign (v2.0.0): LayoutRegister, text_direction, ScriptVariant, COLOR, INDEX_AREA, CATCHWORD | `.planning/ROADMAP.md` Phase 1.1; STATE.md |
| Single-repo / dual-package; uv workspace deferred | PROJECT.md; REVIEW_STRATEGY R7 |
| Hybrid PageQuality (replaces ScanQuality enum) | STATE.md `[01.1-03]` |
| **CryptOfCogito integrated architecture ("ADR-021")** | — never written; REVIEW_STRATEGY E11 still open |

All eight are first-class architectural decisions, living in PROJECT.md tables and STATE.md bullets — not in `docs/adr/` where README, CLAUDE.md, and SPEC.md point readers. The ADR system itself has drifted: it covers ScholarDoc Era 1 only.

## 6. Cross-File Authority Pointers

The cascade resolves cleanly mechanically: README→CLAUDE.md→docs/VISION.md (self-declared authoritative); SPEC.md+REQUIREMENTS.md→CLAUDE.md#Vision. **No broken links.** Semantically all five describe Era-1 ScholarDoc. CLAUDE.md "Quick Start" sends readers to root ROADMAP (Era 1). No root document instructs readers to read `.planning/`. New contributors land in Era 1 and stay there.

## 7. REVIEW_STRATEGY.md Today

REVIEW_STRATEGY.md (2026-03-19) remains a **largely accurate diagnosis** with three caveats:

1. **Wave 2 (Git Housekeeping A1-A4) is partially done.** Branch `feature/01.1-01-foundation-types` is still active; A1 ("Merge into main") not done.

2. **Wave 3 (Documentation B+C+D) is unstarted.** All B-checkboxes unchecked; underlying drift unchanged. C3 was *partially* attempted 2026-04-16 — STATE.md says "Phase 1.1 Complete" but does not reflect Phase 1.2's simultaneous insertion in ROADMAP.md, producing fresh internal drift.

3. **Phase 1.2 ≈ Wave 3+4 collapsed.** Its success criteria 1-5 cover B1-B6 and parts of F. **Wave 5 (GT schema critical review, experimental methodology, cross-project ADRs) and Wave 6 (OCR literature review) have not been formalized into any phase.** The roadmap jumps from Phase 1.2 (cleanup) directly to Phase 2 (Extractor Interface) — bypassing R3 (GT schema critical review before Phase 2), R6 (experimental-framework-first), and R5 (OCR literature review before architecture). E6, E9, E10, E11 unaddressed.

REVIEW_STRATEGY.md's biggest retrospective miss is **scope underestimation**: Wave 3 was framed as one wave, but ~25 docs need triage, ~8 ADRs need writing, two roadmaps need reconciliation. This is why Phase 1.2 was eventually inserted to absorb part of it. The strategy remains the best available diagnosis; six weeks later it has aged into a still-accurate problem statement documenting how much of its own remediation never shipped.
