# ScholarDoc & ScholarGT

## What This Is

Two related projects planned from this workspace:

**ScholarGT** (primary, milestone 1): An independent, config-driven ground truth annotation platform for scholarly documents. Produces verified GT data with pluggable extractors, per-element verification tracking, provenance, and an extensible universal schema. Designed to serve multiple consumers — ScholarDoc is one, but the platform should accommodate any project that needs structured GT for scholarly PDFs.

**ScholarDoc** (existing): A Python library that extracts structured knowledge from scholarly PDFs into `ScholarDocument`. Serves as one extractor plugin for ScholarGT and as a standalone extraction library for downstream applications. Improvements to ScholarDoc are deferred until ScholarGT provides the measurement infrastructure to evaluate them.

## Core Value

**You cannot improve what you cannot measure.** ScholarGT provides the measurement foundation. ScholarDoc provides the extraction. Together they form a virtuous cycle: better GT → better evaluation → better extraction → faster annotation → better GT.

## Requirements

### Validated (ScholarDoc — existing)

- ✓ PDF text extraction with position/font/style data (PyMuPDF reader)
- ✓ OCR error detection via spellcheck-as-selector (99.2% detection rate)
- ✓ Line-break rejoining with block filtering (ADR-003)
- ✓ Cascading structure extraction (outline → heading → fallback)
- ✓ Document profile detection (book, article, essay, report — 100% accuracy)
- ✓ Clean text with position-based annotations (ScholarDocument model)
- ✓ RAG chunk generation (to_rag_chunks())
- ✓ Markdown output (to_markdown())
- ✓ Evaluation library skeleton (ground_truth/lib/)
- ✓ Regression testing infrastructure (test_ground_truth_regression.py)

### Active (Milestone 1 — ScholarGT focused)

- [ ] Universal GT schema with config-driven label selection and extensibility
- [ ] Pluggable extractor interface (ScholarDoc, Docling, GROBID, lightweight built-in)
- [ ] Experimentation framework (pipeline + component level comparison, YAML specs, metrics)
- [ ] Annotation tool (visual + ML-assisted pre-population + verification workflow)
- [ ] Per-element verification tracking with provenance (which pipeline, what was changed)
- [ ] Small validated GT corpus to prove the design

### Active (Deferred — ScholarDoc improvements)

- [ ] ScholarDocument representation review (richer IR)
- [ ] Writers module (JSON canonical, Markdown presentation)
- [ ] Re-OCR pipeline integration (neural re-OCR for flagged words)
- [ ] Unified repo structure decision

### Out of Scope

- Cross-document relation mapping — corpus layer concern
- Corpus database (SQLAlchemy) — consuming application concern
- MCP server — application-level
- RAG embedding/vector search — downstream feature
- EPUB/MOBI — defer until PDF extraction is solid and evaluated

## Context

### Ecosystem

- **ScholarGT** (to be created): Independent GT annotation platform
- **ScholarDoc** (this repo): PDF → structured extraction library
- **CryptOfCogito** (`~/workspace/writings/PHL410_CryptOfCogito`): Philosophy corpus infrastructure with mature annotation tool (FastAPI + Canvas, RT-DETR, 20 ADRs), GT schema (v0.3.1), SQLAlchemy database
- **scholarly_annotate** (proposed): Shared annotation package — may become part of ScholarGT or remain separate

### Current State

ScholarDoc: 395 tests, 87% coverage, mature extraction pipeline. Zero verified GT. Empty Writers module. Re-OCR designed but not integrated. OCR false positive rate 23.4% on philosophical terms.

CryptOfCogito: Mature annotation tool (2,237 lines Canvas JS), 16 region types, RT-DETR layout detection, tiered GT schema, SSE streaming for batch detection. Valuable as reference and inspiration for ScholarGT.

### GT Schema Comparison

| Feature | ScholarDoc v3/v4 | CryptOfCogito v0.3.1 |
|---------|------------------|----------------------|
| Orientation | Document-centric | Page-centric |
| Spatial | Bboxes on elements | Regions with normalized + pixel bboxes, reading order |
| Structure | Footnotes, endnotes, citations, formatting, xmarks | 16 region types, paragraphs, lines hierarchy |
| Semantic | Note classification (author/translator/editor), corruption model | Text anchors, continuation links |
| Metadata | Document-level (title, author, publisher) | Annotator tracking, review status, difficulty |
| Philosophy-specific | Stephanus, Bekker, sous rature, foreign term tracking | Tiered labels (layout → OCR → markers → citations) |
| Verification | `verified_by` field (document-level) | Per-region review status |
| Config-driven | No | Partially (ADR-007) |

ScholarGT should unify the strengths of both: spatial hierarchy from Cogito, semantic richness from ScholarDoc, plus config-driven selection, per-element verification, and provenance tracking that neither has.

### Key Design Principles for ScholarGT

1. **Independent of any extractor** — defines an extractor interface, ScholarDoc is one plugin
2. **Config-driven labels** — project initialization selects needed annotation types from universal superset
3. **Extensible** — new label types addable without restructuring existing GT
4. **Per-element verification** — not just "page verified" but element-level with reviewer tracking
5. **Provenance** — which extractor/config produced the draft, what the human changed
6. **ML-assisted** — pre-populate via extractors, flag low-confidence for human review
7. **Experimentation-first** — built to support structured experiments comparing extractors and components

### Chicken-and-Egg Solution

ScholarGT uses pluggable extractors to pre-populate drafts. Humans correct low-confidence elements. Corrections improve GT. Better GT enables better evaluation of extractors. Better extractors produce better drafts. The cycle is extractor-agnostic.

## Constraints

- **Stack**: Python 3.11+, PyMuPDF (fitz), Pydantic, pytest, uv
- **Hardware**: GTX 1080 Ti (11GB VRAM), Mac M4 for Claude Desktop
- **License**: PyMuPDF is AGPL
- **Domain**: Dense scholarly texts — footnotes, endnotes, citations, Greek/German/Latin/French, sous rature, Stephanus/Bekker references
- **Evidence-Based**: Design decisions backed by experimentation (32 spikes completed in ScholarDoc)
- **Design-Heavy Milestone**: Get architecture right before producing large GT corpus

## Key Decisions

| Decision | Rationale | Status |
|----------|-----------|--------|
| ScholarGT is independent of ScholarDoc | GT platform serves multiple consumers, not tied to one extractor | ✓ Decided |
| ScholarGT is milestone 1 primary deliverable | Cannot improve extraction without measurement infrastructure | ✓ Decided |
| Design-heavy milestone | Get schema, tool architecture, extractor interface right first | ✓ Decided |
| Config-driven label selection | Projects select needed annotations from universal superset | ✓ Decided |
| Pluggable extractors with built-in lightweight | Extractor interface + minimal built-in + plugins (ScholarDoc, etc.) | ✓ Decided |
| Both pipeline and component level experiments | Compare whole systems AND swap individual components | ✓ Decided |
| Annotation tool: review Cogito, possible rewrite | Carry forward principles (visual, ML-assisted, config-driven) | ✓ Decided |
| Planning in ScholarDoc repo | Code location decided after design phase | ✓ Decided |
| Repo structure | Deferred to after design | — Pending |
| Unified GT schema approach | Deferred to planning | — Pending |
| Single human pass sufficient | Per-element verification tracking for granularity | ✓ Decided |

---
*Last updated: 2026-02-18 after planning revision — ScholarGT as primary deliverable*
