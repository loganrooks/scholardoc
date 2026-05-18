# Repo Review Strategy & Checklist

> **Purpose:** Get scholardoc and its ecosystem into shape for proper GSD Reflect development
> **Created:** 2026-03-19
> **Status:** DRAFT v2 — Incorporates full ecosystem analysis (10+ projects explored)
> **Companion:** See REVIEW_AUDIT_LOG.md for search locations and confidence levels

---

## Situation Assessment

### The Ecosystem (what we actually found)

ScholaDoc is not a standalone project. It's the extraction engine in a **10+ project philosophical research ecosystem**:

```
ACQUISITION        EXTRACTION           SEARCH/ANALYSIS      ORCHESTRATION
zlibrary-mcp  -->  scholardoc      -->  philo-rag-simple --> hermeneutic-workspace-plugin
(find books)       (PDF -> IR)          (RAG search)         (12 skills, 11 MCP tools,
                   |                    |                     reading rounds, drafting)
                   scholargt            philograph-mcp
                   (GT schema)          (knowledge graph)
                   |
                   CryptOfCogito
                   (annotation tool,
                    corpus DB, 20 ADRs)

+ semantic-calibre (library management)  + audiobookify (text -> audio)
+ epistemic-agency (epistemological framework, 47 findings)
+ claude-enhanced (dev infrastructure meta-project)
+ philoso-roo (Hegel-focused suite)  + mcp-vector-database (pgvector backend)
```

**No single ecosystem vision document exists.** The pipeline is described as a one-liner in ~/CLAUDE.md. Individual project visions are siloed.

### The Three Eras (within this repo)

1. **Era 1 (Dec 2025):** ScholarDoc as standalone PDF extraction library. Phases 0-1 completed. 32 spikes, 4 ADRs, root-level docs.

2. **Era 2 (Jan 2026):** Ground truth eval system added. CryptOfCogito comparison done (scholardoc_analysis.md). scholarly_annotate package proposed. Annotation UI design started.

3. **Era 3 (Feb 2026):** Pivot to ScholarGT as primary deliverable. GSD Reflect onboarded. `.planning/` with new roadmap. `scholargt/` package built. Schema v2.0.0 complete (312 tests, 6 SFPs).

**Root problem:** Root docs (CLAUDE.md, ROADMAP.md, SPEC.md) reflect Era 1. GSD planning docs reflect Era 3. They describe different projects.

### Critical Issues

#### 1. THREE competing GT schemas
| Schema | Location | Status |
|--------|----------|--------|
| ScholarDoc ground_truth/ v3/v4 | This repo | Era 1, document-centric, YAML |
| CryptOfCogito v0.3.1 | ~/workspace/writings/ | Era 2, page-centric, JSON, tiered |
| ScholarGT v2.0.0 | This repo, scholargt/ | Era 3, config-driven, Pydantic |

These are actually COMPLEMENTARY, not competing: ScholarGT defines the DATA MODEL, CryptOfCogito's v0.4 designs the STORAGE/QUERY layer. But this isn't documented anywhere.

#### 2. TWO OCR approaches (neither literature-reviewed recently)
| Approach | Project | When to use |
|----------|---------|-------------|
| Text-layer-first | scholardoc | Born-digital PDFs with existing OCR |
| Vision-first (RT-DETR + Surya/EasyOCR) | CryptOfCogito | Scanned PDFs, no text layer |
| VLM (GOT-OCR) | CryptOfCogito (feasibility only) | Potentially all PDFs |
| **GLM-OCR, recent models** | **Not evaluated** | **Unknown** |

#### 3. Experimental methodology is ad-hoc
32 spikes as standalone scripts. No formal experiment design, no reproducibility, small validation set (130 pairs). Cannot rigorously compare OCR approaches or validate GT schema design without a proper framework.

#### 4. Stale documentation across levels
| Doc | Says | Reality |
|-----|------|---------|
| CLAUDE.md | "Phase 1: OCR pipeline" | Phase 1.1 complete |
| Root ROADMAP.md | Phases 2-4: footnotes, formats, OCR | .planning/: extractor, experimentation, annotation |
| .planning/STATE.md | "Phase 1.1 executing" | Complete since Feb 20 |
| CryptOfCogito pending_decisions.md | "ADR-021 needed" | Never written |

#### 5. The hermeneutic workspace needs scholardoc but isn't integrated
hermeneutic-workspace-plugin has `source_ingest` and `text_extract` MCP tools that should use scholardoc as their engine. This isn't documented or implemented.

---

## Recommendations (with rationale)

### R1. Ecosystem Vision Document
**Recommendation:** Expand ~/CLAUDE.md's "Project Ecosystem" section into a proper architectural overview.

**Why:** The vision is currently distributed across 10+ CLAUDE.md files. A single reference point at the workstation level prevents each project from developing in isolation. Keep it concise: pipeline diagram, role descriptions, integration points, design principles. Link to individual project docs for details.

**Why not a new repo/project:** Overhead. This is a ~2 page document, not a codebase.

### R2. ScholarDoc as Hermeneutic Workspace Engine
**Recommendation:** Yes, scholardoc should power the workspace's `source_ingest` pipeline. Document the intended integration now; implement when both sides are ready.

**Why:** They solve the same problem (extract clean structured text from scholarly sources). Duplicating extraction logic across projects is waste.

**What this implies for scholardoc:**
- Stable, well-documented public API (`convert()` function)
- Eventually handle EPUB/MOBI (the workspace needs multi-format)
- Output format compatible with workspace's library model (readings with R-NNNN IDs, section structure)

**Not blocking:** Don't hold up current work for this. Document intent, implement later.

### R3. GT Schema: ScholarGT v2.0.0 is authoritative, but invite critique
**Recommendation:** ScholarGT v2.0.0 is the authoritative ground truth data model. CryptOfCogito's v0.4 DB design informs the future STORAGE layer. Old ground_truth/ directory is legacy.

**Why:** ScholarGT v2.0.0 unifies both predecessors' strengths (spatial from CryptOfCogito, semantic from ScholarDoc). Config-driven profiles, per-element verification, and 6 SFPs are genuine advances. 312 tests provide confidence.

**But:** You mentioned GT design concerns. The v2.0.0 schema was designed in a concentrated sprint. Before building Phase 2 (Extractor Interface) on top of it, we should do a critical review. Specific areas to examine:
- Is the PageGT/DocumentGT split actually the right boundary?
- Are the 8-category GTProfile dimensions orthogonal enough?
- Does the verification model (multi-reviewer per element) work in practice, or is it over-designed?
- How well does the schema handle the hermeneutic workspace's needs (readings, connection annotations, rereading questions)?
- SFP-7 (content_layer) was deferred — should it have been?

### R4. Annotation Tool: Extract from CryptOfCogito
**Recommendation:** Extract CryptOfCogito's annotation tool into a `scholarly_annotate` package in this repo. Update it to work with ScholarGT v2.0.0 schema.

**Why:** CryptOfCogito's tool is working MVP (FastAPI + Canvas, RT-DETR, keyboard shortcuts, continuation linking). Building from scratch in Phase 4 would duplicate ~2,237 lines of tested code. The scholarly_annotate design (from CryptOfCogito's Serena memory) already specifies how to extract it.

**When:** After Phase 2 (Extractor Interface). The tool needs extractors to pre-populate annotations.

### R5. OCR Pipeline: Pause decisions, prioritize methodology
**Recommendation:** Don't make OCR pipeline architecture decisions now. First: (1) build experimental framework, (2) do literature review, (3) then compare approaches rigorously.

**Why:**
- Two valid approaches exist for different use cases (text-layer vs vision-first)
- Recent field advances (GLM-OCR, etc.) haven't been evaluated
- The 32 spikes answered specific questions but aren't a repeatable evaluation framework
- Without proper methodology, any decision is premature

**Priority order:**
1. Experimental methodology design (Phase 3 in .planning/ROADMAP)
2. OCR literature review (GLM-OCR, recent models)
3. Structured comparison of approaches
4. Architecture decision (new ADR)

### R6. Experimental Methodology: Highest priority new work
**Recommendation:** Design a proper experiment framework before any new OCR or pipeline work.

**Why:** Everything depends on rigorous evaluation — GT schema validation, OCR pipeline comparison, extractor quality measurement. Current spikes are exploratory scripts, not a science-grade methodology.

**What the framework needs:**
- Fixed benchmark datasets with known ground truth
- Standardized metrics (CER, WER, structure F1, semantic accuracy)
- Experiment specification format (YAML)
- Results logging (JSONL)
- Statistical analysis (confidence intervals, significance tests)
- Reproducibility guarantees (pinned deps, seeds, documented hardware)
- Clear epistemic commitments (informed by epistemic-agency's Peirce/Dewey grounding)

**Where this lives:** This IS Phase 3 of the .planning/ROADMAP. Consider whether to tackle it before Phase 2, since the extractor interface also needs evaluation infrastructure.

### R7. Repo Structure: Keep current layout, add uv workspace config
**Recommendation:** Keep current directory layout (`scholardoc/`, `scholargt/` at repo root). Add `[tool.uv.workspace]` to pyproject.toml. One `.claude/` at root. `scholarly_annotate/` added as third package later.

**Why minimal change:** The current layout works. uv workspace is a config addition, not a restructuring. Don't reorganize into `packages/` subdirectory — that's unnecessary churn.

**What stays separate:** CryptOfCogito (course project), hermeneutic-workspace-plugin (orchestration), philo-rag-simple, philograph-mcp. They DEPEND ON the infrastructure packages, they're not part of the same repo.

**Repo name:** Keep "scholardoc" — it's the primary identity. ScholarGT serves scholardoc's measurement needs.

### R8. Memory Systems: Keep both, clear separation
**Recommendation:** Use both Serena and Claude Code memory with distinct roles.

- **Serena memories:** Project-level technical knowledge. Version-controlled in repo. Cross-tool compatible. Audit for staleness (many are Dec 2025-Jan 2026).
- **Claude Code memories:** User preferences, workflow feedback, ecosystem-level context. User-specific, persists across projects.

**Don't migrate.** They serve different purposes.

---

## Review Checklist (Updated)

### A. Git Housekeeping
- [ ] **A1.** Merge `feature/01.1-01-foundation-types` into main
- [ ] **A2.** Commit GSD framework updates in `.claude/` separately
- [ ] **A3.** Verify no work lost across branches
- [ ] **A4.** Start fresh branch for review/cleanup work

### B. Documentation Authority Resolution
- [ ] **B1. CLAUDE.md** — Rewrite: dual-project identity, current phase, ecosystem context, correct workflow commands
- [ ] **B2. Root ROADMAP.md** — Archive as "ScholarDoc Phase 0-1 History", add redirect to .planning/ROADMAP.md
- [ ] **B3. Root SPEC.md** — Mark as ScholarDoc-specific (still valid for extraction package), note ScholarGT schema is separate
- [ ] **B4. docs/VISION.md** — Rewrite to reflect full ecosystem role: scholardoc as atomic extraction unit enabling research system
- [ ] **B5. Root QUESTIONS.md** — Review pending questions, close resolved ones, note new questions from ScholarGT work
- [ ] **B6. Root REQUIREMENTS.md** — Archive as Era 1; .planning/REQUIREMENTS.md is authoritative
- [ ] **B7. ground_truth/** — Mark as "legacy Era 1 GT system"; ScholarGT v2.0.0 is authoritative schema; ground_truth/lib/ evaluation code still valuable
- [ ] **B8. docs/design/** — Review 12 files; mark each as current/superseded/historical
- [ ] **B9. Ecosystem vision** — Expand ~/CLAUDE.md "Project Ecosystem" section (R1)

### C. .planning/ Health Check
- [ ] **C1. PROJECT.md** — Update ecosystem context, add CryptOfCogito relationship, hermeneutic workspace connection
- [ ] **C2. ROADMAP.md** — Verify phase status current; consider reordering Phase 3 (experimentation) before Phase 2
- [ ] **C3. STATE.md** — Update: Phase 1.1 COMPLETE, current position is "review/cleanup before Phase 2"
- [ ] **C4. continue-here.md** — Remove or update stale continuation marker

### D. Serena Memory Audit
- [ ] **D1.** Review all 15 memory files against current state
- [ ] **D2.** Update project_vision.md: ecosystem role, measurement-first principle
- [ ] **D3.** Archive stale session checkpoints (Dec 2025)
- [ ] **D4.** Create new session_handoff.md for current state
- [ ] **D5.** Cross-reference CryptOfCogito's Serena memories (scholardoc_analysis.md, scholarly_annotate_design.md, pending_decisions.md) to ensure consistency

### E. Design Decision Audit
- [ ] **E1-E4. ADR-001 through ADR-004** — Still valid for ScholarDoc package; no changes needed
- [ ] **E5. ScholarGT independence** — Valid. Needs uv workspace config to formalize (R7)
- [ ] **E6. GT schema critical review** — Logan's concerns. Schedule deep review before Phase 2 (R3)
- [ ] **E7. CryptOfCogito relationship** — Formalize: extraction (scholardoc) + annotation tool (extract to scholarly_annotate) + corpus DB (CryptOfCogito keeps) (R4)
- [ ] **E8. Repo structure** — Adopt uv workspace (R7)
- [ ] **E9. Experimental methodology** — Design new framework before OCR decisions (R6)
- [ ] **E10. OCR literature review** — Schedule after experimental framework (R5)
- [ ] **E11. CryptOfCogito ADR-021** — The "integrated architecture" ADR that was never written. Write it here or in CryptOfCogito?

### F. Code & Package Structure
- [ ] **F1. uv workspace config** — Add [tool.uv.workspace] to pyproject.toml
- [ ] **F2. scholargt/ pyproject.toml** — If separate workspace member, needs own minimal pyproject
- [ ] **F3. ground_truth/ directory** — Add README marking as legacy; keep evaluation lib code
- [ ] **F4. tests/ organization** — Verify clean separation between scholardoc and scholargt tests
- [ ] **F5. spikes/** — Keep as historical reference; don't archive (still informative)
- [ ] **F6. Run test suite** — Verify 312+ tests pass
- [ ] **F7. Ruff check** — Verify clean

### G. Ecosystem Integration Points (NEW)
- [ ] **G1.** Document scholardoc -> hermeneutic-workspace-plugin integration intent
- [ ] **G2.** Document scholardoc -> philo-rag-simple interface (ScholarDocument -> chunks)
- [ ] **G3.** Document scholarly_annotate extraction plan from CryptOfCogito
- [ ] **G4.** Review philoso-roo and mcp-vector-database for reusable ideas (PENDING agent results)
- [ ] **G5.** Catalog cross-project Serena memories that reference scholardoc

---

## Execution Waves

### Wave 1: Decisions (this conversation)
- Review recommendations R1-R8
- Make binding decisions on each
- Identify any remaining concerns (especially GT schema)

### Wave 2: Git Housekeeping (A1-A4)
- Merge feature branch, commit GSD updates, clean baseline

### Wave 3: Documentation Overhaul (B + C + D)
- CLAUDE.md rewrite
- Archive/update stale docs
- .planning/ state update
- Serena memory audit
- Ecosystem vision in ~/CLAUDE.md

### Wave 4: Code & Config (F + R7)
- uv workspace setup
- Test verification
- Package structure cleanup

### Wave 5: Design Reviews (E)
- GT schema critical review (Logan's concerns)
- Experimental methodology design
- Cross-project architecture decisions

### Wave 6: Research (future)
- OCR literature review (GLM-OCR etc.)
- Experimental framework implementation
- Structured pipeline comparison

---

## Projects Explored (Audit Trail)

| Project | Location | Explored? | Key Findings |
|---------|----------|-----------|--------------|
| scholardoc | ~/workspace/projects/scholardoc/ | DEEP | Dual package, 3 eras of docs, 32 spikes |
| CryptOfCogito | ~/workspace/writings/PHL410_CryptOfCogito/ | DEEP | 20 ADRs, annotation tool MVP, GT v0.3.1, DB v0.4, comparison review |
| hermeneutic-workspace-plugin | ~/workspace/projects/ | DEEP | 12 skills, 11 MCP tools, 811-line architecture spec |
| epistemic-agency | ~/workspace/projects/ | MEDIUM | 47 findings, Peirce/Dewey/Stiegler grounding |
| philo-rag-simple | ~/workspace/projects/ | MEDIUM (deep dive pending) | 10 ADRs, structure-aware RAG |
| philograph-mcp | ~/workspace/projects/ | MEDIUM (deep dive pending) | Knowledge graph, bootstrap phase |
| zlibrary-mcp | ~/workspace/projects/ | MEDIUM | Stable, reusable components |
| claude-enhanced | ~/workspace/projects/ | MEDIUM | Meta-project for dev infrastructure |
| semantic-calibre | ~/workspace/projects/ | LIGHT | Phase 4.4, semantic library |
| audiobookify | ~/workspace/projects/ | LIGHT | v2.5.0, EPUB->M4B |
| philoso-roo | ~/workspace/projects/ | PENDING | Hegel-focused suite |
| mcp-vector-database | ~/workspace/projects/ | PENDING | pgvector backend |
| PHL410 course | ~/workspace/university/ | LIGHT | Domain-aligned, not integrated |
| get-shit-done-reflect | ~/workspace/projects/ | LIGHT | 54 deliberation files |
