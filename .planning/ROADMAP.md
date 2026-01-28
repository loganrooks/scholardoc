# Roadmap: ScholarDoc

## Overview

**Milestone 1: Measurement Infrastructure and Architectural Foundations** -- Establish the ground truth, evaluation, and experimentation infrastructure so that ScholarDoc's extraction quality can be systematically measured, improved, and integrated with its ecosystem. Without verified ground truth, every quality claim is unverified; without serialization, output cannot be consumed; without clear architectural boundaries, the monorepo migration will restructure prematurely.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Ground Truth Bootstrap** - Verified GT corpus and automated evaluation pipeline
- [ ] **Phase 2: IR Enrichment and Writers** - Rich intermediate representation and serialization
- [ ] **Phase 3: Experimentation Framework** - Systematic hypothesis-driven improvement workflow
- [ ] **Phase 4: Re-OCR Pipeline Integration** - Neural re-OCR wired into main extraction pipeline
- [ ] **Phase 5: Monorepo Migration** - Unified repository with uv workspaces

## Phase Details

### Phase 1: Ground Truth Bootstrap
**Goal**: Developers can measure ScholarDoc's extraction quality against verified ground truth and catch regressions automatically.
**Depends on**: Nothing (first phase)
**Requirements**: GT-01, GT-02, GT-03
**Research**: Standard patterns -- existing evaluation library is sound, three-stage bootstrap well-documented.
**Success Criteria** (what must be TRUE):
  1. At least 10 human-verified GT pages exist across 3+ source texts, covering footnotes, foreign terms, and structural elements
  2. Running a single command produces a metrics report comparing current extraction against GT (CER/WER, footnote detection F1, per-element breakdown)
  3. CI regression gate fails the build when extraction metrics regress beyond a configured threshold
  4. GT schema supports adding new annotation layers (structure, semantics) without modifying existing GT files
  5. Baseline metrics are recorded and committed as the starting point for improvement tracking
**Plans**: TBD

Plans:
- [ ] 01-01: GT schema design and bootstrap corpus creation
- [ ] 01-02: Automated evaluation pipeline and CI regression gate

### Phase 2: IR Enrichment and Writers
**Goal**: ScholarDocument captures all extraction information losslessly and can be serialized to JSON (canonical) and Markdown (presentation).
**Depends on**: Phase 1 (metrics reveal what the IR is missing)
**Requirements**: IR-01, WR-01
**Research**: Needs Docling DoclingDocument analysis to determine exactly which fields to add. Cross-reference system design is non-trivial.
**Success Criteria** (what must be TRUE):
  1. ScholarDocument includes bounding boxes, font metadata, and confidence scores for extracted elements
  2. Cross-element references link footnote markers to footnote definitions and citations to bibliography entries
  3. ContentElement supports a typed annotation layer for consumer-extensible metadata (Stephanus numbers, Bekker numbers) without core schema modification
  4. JSON round-trip is lossless: serialize then deserialize produces an identical ScholarDocument
  5. Markdown output is generated from the enriched IR through the Writers module (not ad-hoc string building)
**Plans**: TBD

Plans:
- [ ] 02-01: IR enrichment (bounding boxes, fonts, confidence, cross-references, annotations)
- [ ] 02-02: Writers module (JSON canonical serializer, Markdown writer)

### Phase 3: Experimentation Framework
**Goal**: Developers can run structured experiments that test extraction improvements against GT with tracked, comparable results.
**Depends on**: Phase 1 (evaluation infrastructure), Phase 2 (serialization for result persistence)
**Requirements**: EXP-01
**Research**: Standard patterns -- custom JSON tooling, no external research needed.
**Success Criteria** (what must be TRUE):
  1. An experiment spec (YAML) captures hypothesis, parameter changes, success criteria, and can be executed reproducibly
  2. Experiment results are logged to JSONL with metrics, timestamps, and parameter snapshots for comparison across runs
  3. Stratified metrics break down performance by element type (footnotes, headings, body text, foreign terms) and by source text
  4. GT corpus is split into dev/validation sets, and experiments report metrics on both to detect overfitting
**Plans**: TBD

Plans:
- [ ] 03-01: Experiment spec, runner, and metrics tracking

### Phase 4: Re-OCR Pipeline Integration
**Goal**: Flagged OCR errors are automatically corrected by neural re-OCR, measurably reducing the false positive rate on philosophical terms.
**Depends on**: Phase 1 (metrics to target worst performers), Phase 3 (experimentation framework to validate improvements)
**Requirements**: OCR-01
**Research**: Needs spike on GOT-OCR vs Tesseract for philosophy-specific terms on 11GB VRAM (GTX 1080 Ti).
**Success Criteria** (what must be TRUE):
  1. The main extraction pipeline invokes neural re-OCR for words flagged by the spellcheck selector, with no manual intervention
  2. Foreign term CER is tracked as a first-class metric, and re-OCR measurably reduces it compared to baseline
  3. Re-OCR runs within hardware constraints (11GB VRAM) and does not regress processing time beyond an acceptable threshold
  4. The OCR false positive rate (currently 23.4%) is reduced, with the improvement validated against the GT corpus
**Plans**: TBD

Plans:
- [ ] 04-01: Re-OCR spike and pipeline integration

### Phase 5: Monorepo Migration
**Goal**: ScholarDoc, CryptOfCogito, and shared packages live in a unified uv workspace with clear dependency boundaries.
**Depends on**: Phase 2 (library boundaries proven through serialization), Phase 4 (package interfaces stable from use)
**Requirements**: ARCH-01, ARCH-02
**Research**: Standard patterns -- uv workspaces well-documented with multiple reference implementations.
**Success Criteria** (what must be TRUE):
  1. A single uv workspace contains ScholarDoc, CryptOfCogito, and scholarly_testdata as separate packages under packages/
  2. CryptOfCogito imports and uses ScholarDoc as a workspace dependency for PDF extraction (replacing its own extraction code)
  3. scholarly_testdata package provides GT schemas, pytest fixtures, and sample PDFs (via Git LFS) shared by both projects
  4. Each package can be independently published and versioned
  5. CryptOfCogito's git history is preserved via subtree merge
**Plans**: TBD

Plans:
- [ ] 05-01: Workspace setup and package migration
- [ ] 05-02: CryptOfCogito integration and shared testdata package

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|---------------|--------|-----------|
| 1. Ground Truth Bootstrap | 0/2 | Not started | - |
| 2. IR Enrichment and Writers | 0/2 | Not started | - |
| 3. Experimentation Framework | 0/1 | Not started | - |
| 4. Re-OCR Pipeline Integration | 0/1 | Not started | - |
| 5. Monorepo Migration | 0/2 | Not started | - |
