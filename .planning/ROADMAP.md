# Roadmap: ScholarDoc & ScholarGT

## Overview

**Milestone 1: ScholarGT — Ground Truth Annotation Platform** — Design and build an independent, config-driven ground truth annotation platform for scholarly documents. ScholarGT provides the measurement foundation that ScholarDoc (and other projects) need to systematically evaluate and improve extraction quality. This milestone is design-heavy: get the schema, extractor interface, experimentation framework, and annotation tool architecture right before producing a large GT corpus.

## Phases

**Phase Numbering:**
- Integer phases (0, 1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 0: Workspace Cleanup** - Clean up workspace and organize git backlog / uncommitted changes
- [x] **Phase 1: Universal GT Schema** - Config-driven schema with extensibility and per-element verification
- [ ] **Phase 1.1: Schema Taxonomy Review & Revision** - Use-case-driven redesign of label taxonomy, CitationType, ScanQuality, and spatial/semantic distinction (INSERTED)
- [ ] **Phase 2: Extractor Interface** - Pluggable extractor protocol with provenance tracking
- [ ] **Phase 3: Experimentation & Evaluation Framework** - Structured experiments with metrics at pipeline and component level
- [ ] **Phase 4: Annotation Tool** - Visual, ML-assisted annotation with config-driven UI
- [ ] **Phase 5: Design Validation** - Small GT corpus proving the entire system works end-to-end

## Phase Details

### Phase 0: Workspace Cleanup
**Goal**: Clean up the workspace — organize and commit uncommitted changes, resolve git backlog, ensure a clean starting point before design work begins.
**Depends on**: Nothing (first phase)
**Requirements**: None (housekeeping)
**Research**: None
**Success Criteria** (what must be TRUE):
  1. All uncommitted changes are reviewed, organized, and committed (or deliberately discarded)
  2. Working tree is clean — no untracked files that should be tracked, no staged changes left dangling
  3. Branch strategy is clear and consistent
**Plans**: 3 plans in 2 waves

Plans:
- [x] 00-01-PLAN.md — Gitignore updates, PDF manifest, ground_truth docs
- [x] 00-02-PLAN.md — .claude/ infrastructure swap (GSD) and config commits
- [x] 00-03-PLAN.md — Branch archival and merge to main

### Phase 1: Universal GT Schema
**Goal**: A universal, extensible GT schema where projects select the annotation types they need via configuration, with per-element verification tracking.
**Depends on**: Phase 0 (clean workspace)
**Requirements**: SCH-01, SCH-02, SCH-03
**Research**: Review both existing schemas (ScholarDoc v3/v4, CryptOfCogito v0.3.1) in detail. Analyze what a unified superset looks like. Research extensibility patterns (layered files, plugin registries, JSON-LD).
**Success Criteria** (what must be TRUE):
  1. Schema captures the union of ScholarDoc and CryptOfCogito annotation capabilities (spatial hierarchy, semantic richness, philosophy-specific labels)
  2. A project config file selects which annotation types are active — UI and validation adapt accordingly
  3. Default profiles exist for common use cases (extraction evaluation, layout annotation, full scholarly annotation)
  4. Per-element verification status tracks reviewer identity, timestamp, and confidence
  5. New annotation types can be added without modifying existing GT files or breaking the schema
  6. Schema is documented with examples for at least 3 label configurations
**Plans**: 4 plans in 3 waves

Plans:
- [x] 01-01-PLAN.md -- Schema foundation: package structure, base models, label enums, page-level GT
- [x] 01-02-PLAN.md -- Semantic models with discriminated unions, document-level GT
- [x] 01-03-PLAN.md -- Config system with layered YAML profiles (extraction-eval, layout-annotation, full-scholarly)
- [x] 01-04-PLAN.md -- Validation, JSON Schema generation, example GT files, schema guide

### Phase 1.1: Schema Taxonomy Review & Revision (INSERTED)
**Goal**: Redesign the schema from first principles — restructure label taxonomies by downstream evaluation task, consolidate note/footnote/endnote models, add commentary apparatus and cross-page relationship modeling, decompose CitationType into orthogonal axes, replace categorical ScanQuality with measurable attributes, make pages self-describing for partial annotation, and resolve all identified structural tensions.
**Depends on**: Phase 1 (existing schema to revise)
**Requirements**: SCH-01 (revised), SCH-02 (revised)
**Research**: TEI note/apparatus/annotation models, DocLayNet/PubLayNet label taxonomy comparison, philosophy-specific reference system inventory, ALTO/PAGE XML text properties and cross-page models, text span annotation patterns (standoff annotation, overlapping spans), Chicago Manual citation classification, BCP 47 language tagging, multi-label and hierarchical label patterns.
**Success Criteria** (what must be TRUE):
  1. Every label in every enum has a clear justification tied to a specific downstream evaluation task
  2. SpatialLabel contains only labels identifiable from visual page layout — no content-type labels; missing labels added (TOC_AREA, ABSTRACT, etc.); UNKNOWN/AMBIGUOUS available
  3. Footnote and Endnote consolidated into single Note model with differentiating properties (placement, scope, note_source, marker locations); NoteSchema at document level
  4. Commentary apparatus modeled separately from Notes (passage-ref based, multi-layer, external reference coordinates)
  5. CitationType decomposed into orthogonal axes (CitationFormat x ReferenceSystem x citation style) eliminating MarginalRefType duplication
  6. ScanQuality replaced with hybrid model: quick categorical + optional numeric metrics + specific artifact flags + is_scan flag
  7. Page->Region->Text->Span hierarchy explicit; canonical text in Region.text; ContentSpan references by location (page + region_id + char_offset + char_length)
  8. Cross-page relationships modeled explicitly: Region-level continuation flags + page-level dependency metadata (continues_from/to, unresolved_markers, orphan_continuations)
  9. Pages are self-describing: section_context with hierarchical path, cross-page dependencies declared, partial GT annotation supported
  10. DocumentRelationships eliminated -- linkage via embedded references in Note, Citation, CrossReference models; utility graph construction on demand
  11. All structural tensions resolved: LocationRef standardization, BibliographicRecord for full bibliography, semantic element extensibility, consistent cross-page patterns, FormattingType completion
  12. All existing tests updated or replaced, all new tests pass
  13. Config profiles, examples, and schema guide updated to match revised taxonomy
**Plans**: 5 plans in 5 waves

Plans:
- [ ] 01.1-01-PLAN.md — Foundation: LocationRef in base.py, label enum overhaul in labels.py, version bump to 2.0.0
- [ ] 01.1-02-PLAN.md — Core models: Note, Commentary, NoteSchema in semantic.py, Region continuation flags, FormattingAnnotation language field
- [ ] 01.1-03-PLAN.md — Container models: Hybrid PageQuality, PageDependency, SectionContextEntry on PageGT, DocumentGT with NoteSchema
- [ ] 01.1-04-PLAN.md — Integration: __init__.py re-exports, GTProfile new categories, YAML profile updates, validator updates
- [ ] 01.1-05-PLAN.md — Verification: All tests updated, example GT files, schema.json regeneration, SCHEMA_GUIDE.md

### Phase 2: Extractor Interface
**Goal**: Any extraction pipeline can plug into ScholarGT to pre-populate draft GT, with full provenance tracking of what was auto-generated vs human-corrected.
**Depends on**: Phase 1 (schema defines what extractors must produce)
**Requirements**: EXT-01, EXT-02, EXT-03
**Research**: Standard patterns — Protocol-based interfaces, adapter patterns for existing tools (ScholarDoc, Docling, GROBID).
**Success Criteria** (what must be TRUE):
  1. An extractor protocol defines what any pipeline must implement to produce draft GT conforming to the schema
  2. A lightweight built-in extractor (PyMuPDF text + basic layout) works without external dependencies
  3. At least one external extractor adapter exists (ScholarDoc) demonstrating the plugin pattern
  4. Each GT element records which extractor + config produced it and what (if anything) the human changed
  5. Extractors can be configured with different parameters for A/B comparison
**Plans**: TBD

Plans:
- [ ] 02-01: Extractor protocol and built-in lightweight extractor
- [ ] 02-02: ScholarDoc adapter and provenance tracking

### Phase 3: Experimentation & Evaluation Framework
**Goal**: Developers can run structured experiments comparing extractors and components against GT, with tracked and comparable results.
**Depends on**: Phase 1 (schema for GT format), Phase 2 (extractors to compare)
**Requirements**: EXP-01, EXP-02, EXP-03, EVAL-01, EVAL-02
**Research**: Standard patterns — extend existing ScholarDoc evaluation library, custom YAML/JSONL tooling.
**Success Criteria** (what must be TRUE):
  1. An experiment spec (YAML) captures hypothesis, extractor configs, parameter changes, and success criteria
  2. Pipeline-level experiments compare end-to-end results from different extraction systems
  3. Component-level experiments swap individual components (OCR engine, layout detector) while holding others constant
  4. Experiment results logged to JSONL with metrics, timestamps, and full parameter snapshots
  5. Stratified metrics break down performance by element type and source text
  6. A single command evaluates any extractor output against GT and produces a metrics report
  7. CI regression gate fails on metric regression beyond configured threshold
**Plans**: TBD

Plans:
- [ ] 03-01: Evaluation pipeline (metrics, reports, CI gate)
- [ ] 03-02: Experiment framework (YAML spec, runner, JSONL logging, comparison)

### Phase 4: Annotation Tool
**Goal**: A visual, ML-assisted annotation tool where the UI adapts to the project's configured label types, pre-populates via extractors, and flags low-confidence elements for human review.
**Depends on**: Phase 1 (schema drives UI), Phase 2 (extractors pre-populate), Phase 3 (evaluation validates annotations)
**Requirements**: ANN-01, ANN-02, ANN-03
**Research**: Deep review of CryptOfCogito annotation tool (FastAPI + Canvas, RT-DETR, SSE). Decide rewrite vs adapt. Design ML-assisted workflow.
**Success Criteria** (what must be TRUE):
  1. Annotation tool design is documented with architecture decisions (reviewed against Cogito tool)
  2. Canvas-based visual annotation of PDF pages with bounding box creation/editing
  3. Extractors pre-populate draft annotations; low-confidence elements are flagged for human review
  4. UI dynamically adapts to the project's configured label types (not hardcoded)
  5. Per-element verification status is set through the UI with reviewer identity
  6. Annotation workflow minimizes human effort without compromising GT quality
**Plans**: TBD

Plans:
- [ ] 04-01: Annotation tool design review (Cogito tool analysis, architecture decisions)
- [ ] 04-02: Annotation tool implementation

### Phase 5: Design Validation
**Goal**: A small GT corpus validates that the schema, extractors, experimentation framework, and annotation tool work together end-to-end.
**Depends on**: All prior phases
**Requirements**: VAL-01
**Research**: None — this is execution and validation.
**Success Criteria** (what must be TRUE):
  1. 10-20 verified GT pages exist across 3+ source texts (covering footnotes, foreign terms, structural elements)
  2. GT was produced using the annotation tool with extractor pre-population (not hand-written JSON)
  3. At least 2 extractors have been compared using the experimentation framework
  4. Evaluation pipeline produces meaningful metrics that differentiate extractor quality
  5. Design issues discovered during validation are documented with proposed fixes
**Plans**: TBD

Plans:
- [ ] 05-01: GT corpus creation and end-to-end validation

## Progress

**Execution Order:**
Phases execute in numeric order: 0 -> 1 -> 1.1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|---------------|--------|-----------|
| 0. Workspace Cleanup | 3/3 | Complete | 2026-02-18 |
| 1. Universal GT Schema | 4/4 | Complete | 2026-02-18 |
| 1.1 Schema Taxonomy Review | 0/5 | Not started | - |
| 2. Extractor Interface | 0/2 | Not started | - |
| 3. Experimentation & Evaluation | 0/2 | Not started | - |
| 4. Annotation Tool | 0/2 | Not started | - |
| 5. Design Validation | 0/1 | Not started | - |
