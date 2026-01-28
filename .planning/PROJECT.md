# ScholarDoc

## What This Is

A Python library that extracts structured knowledge from scholarly PDFs into a rich intermediate representation (`ScholarDocument`) designed for multiple downstream applications: RAG pipelines, Anki generation, citation management, corpus analysis, knowledge graphs, and more. ScholarDoc is the extraction layer in a broader ecosystem — other projects (like CryptOfCogito) consume it as a library and build corpus-level features on top.

## Core Value

**Accurate, rich extraction from scholarly PDFs into a representation that maximizes the number of downstream workflows it can support.** If the extraction is wrong or the representation is too narrow, everything built on top fails.

## Requirements

### Validated

- ✓ PDF text extraction with position/font/style data — existing (PyMuPDF reader)
- ✓ OCR error detection via spellcheck-as-selector — existing (99.2% detection rate)
- ✓ Line-break rejoining with block filtering — existing (ADR-003)
- ✓ Cascading structure extraction (outline → heading → fallback) — existing
- ✓ Document profile detection (book, article, essay, report) — existing (100% accuracy)
- ✓ Clean text with position-based annotations — existing (ScholarDocument model)
- ✓ RAG chunk generation — existing (to_rag_chunks())
- ✓ Markdown output — existing (to_markdown())
- ✓ Evaluation library (normalize, match, metrics, reports) — existing (ground_truth/lib/)
- ✓ Regression testing infrastructure — existing (test_ground_truth_regression.py)

### Active

- [ ] Verified ground truth corpus (annotated + human-verified pages for evaluation)
- [ ] Modular, extensible ground truth schema (start with extraction needs, designed for future layers)
- [ ] Automated evaluation pipeline (run extraction → compare to GT → metrics report)
- [ ] Experimentation framework (hypothesis → spike → evaluation → ADR, with agent support)
- [ ] Unified architecture plan (ScholarDoc + GT system + CryptOfCogito integration)
- [ ] Determine repo structure (monorepo vs multi-repo, shared GT package, migration plan)
- [ ] ScholarDocument representation review (is it rich enough for all intended use cases?)
- [ ] Writers module (JSON, SQLite serialization — currently empty)
- [ ] Re-OCR pipeline integration (neural re-OCR for flagged words — designed but not wired)

### Out of Scope

- Cross-document relation mapping — corpus layer responsibility (CryptOfCogito)
- Corpus database (SQLAlchemy) — belongs to consuming applications, not extraction library
- MCP server — application-level concern
- RAG embedding/vector search — downstream application feature
- UI for annotation — separate package (scholarly_annotate or similar)
- EPUB/MOBI support — defer until PDF extraction is solid and evaluated

## Context

### Ecosystem

ScholarDoc exists within a broader ecosystem of projects:

- **ScholarDoc** (this repo): PDF → structured extraction library
- **CryptOfCogito** (`~/workspace/writings/PHL410_CryptOfCogito`): Philosophy corpus infrastructure for a PHL 410 essay. Has a mature annotation tool (FastAPI + Canvas, RT-DETR layout detection, NMS filtering), GT schema (v0.3.1, JSON-based, page-centric), and 20 ADRs. Currently does its own PDF processing; should consume ScholarDoc.
- **scholarly_annotate** (proposed, not implemented): Shared annotation package extracted from CryptOfCogito's annotation tool. Would serve both ScholarDoc (for GT creation/evaluation) and CryptOfCogito (for corpus annotation).

### Current State

ScholarDoc has 395 tests passing, 87% coverage, and a mature extraction pipeline. But:
- **Zero verified ground truth documents exist.** The evaluation library is built but has nothing to evaluate against.
- **Writers module is empty.** No serialization beyond in-memory use.
- **Re-OCR is designed but not integrated** into the main pipeline.
- **The GT schema (v1.1.0, YAML-based, document-centric) has known design issues** — it was created before understanding what workflows need evaluation (see ground_truth/DIAGNOSTIC_PLAN.md).
- **Session 24 (2026-01-18) proposed an integrated architecture** but it was never implemented: ScholarDoc as extraction lib, scholarly_annotate as shared GT package, CryptOfCogito as corpus app.
- **OCR false positive rate is 23.4%** (mostly German philosophical terms like "Dasein").

### Prior Art (CryptOfCogito)

The CryptOfCogito project made several relevant architectural decisions:
- **ADR-007**: Tiered GT schema (layout → OCR → markers → citations) with config-driven labels
- **ADR-016/020**: Canvas-based annotation tool with integrated RT-DETR detection and live NMS filtering
- **ADR-017**: SQLAlchemy database with Source → Section → Page → Region → Marker hierarchy, stable_id for RAG
- **ADR-018**: Export format (body.md + footnotes.md + index.json) for Claude consumption
- **ADR-019**: RAG vision with genealogical search, deconstructive search, agentic multi-hop
- **ADR-014/015**: OCR pipeline with VLM decision gate (GOT-OCR viable on 11GB VRAM)

### Key Insight: GT Should Be Modular

Ground truth should start with exactly what ScholarDoc needs for extraction evaluation, but be designed so additional annotation layers can be added without restructuring. The GT schema is a superset that ScholarDoc extraction evaluation is one "slice" of. Future layers (semantic annotation, cross-document relations) should be addable without breaking existing GT.

### Chicken-and-Egg Problem

The annotation tool needs to do what ScholarDoc does (extract text, detect regions, identify footnotes) to efficiently pre-populate GT for human verification. But ScholarDoc needs GT to evaluate its extraction. The solution: use ScholarDoc's extraction as the initial draft for GT annotation, then have humans correct it. This creates a virtuous cycle where better extraction → faster annotation → better GT → better evaluation → better extraction.

## Constraints

- **Stack**: Python 3.11+, PyMuPDF (fitz), Pydantic, pytest, uv — established and validated
- **Hardware**: GTX 1080 Ti (11GB VRAM) for GPU workloads, Mac M4 for Claude Desktop
- **License**: PyMuPDF is AGPL — derivative works must also be AGPL (or commercial license)
- **Philosophy Corpus**: Dense texts with footnotes, endnotes, citations, Greek/German/Latin/French terms, sous rature, marginal references (Stephanus/Bekker) — harder than typical academic PDFs
- **Evidence-Based**: All major design decisions must be backed by spike experiments with measurable results (established pattern: 32 spikes completed)
- **Library, Not App**: ScholarDoc is a library consumed by other projects — no UI, no server, no database

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| PyMuPDF as PDF engine | 32-57x faster, best position/font data (ADR-001) | ✓ Good |
| Spellcheck as selector, not corrector | Auto-correction damages 41% of philosophy terms (ADR-002) | ✓ Good |
| Block-based line-break filtering | Prevents margin content matching (ADR-003) | ✓ Good |
| Cascading extraction over fusion | Only 21% agreement between sources — fusion adds noise | ✓ Good |
| Clean text + position annotations | Separation of extraction from presentation | ✓ Good |
| Document profiles for type-specific extraction | 100% accuracy on book detection | ✓ Good |
| Sequential processing (no parallelism) | Acceptable for Phase 1 | — Pending |
| Dual persistence (JSON + SQLite) | JSON for debugging, SQLite for large docs | — Pending |
| ScholarDoc as extraction library, not corpus manager | Clean separation of concerns (Session 24) | — Pending |
| Modular GT starting with extraction needs | Extensible without restructuring | — Pending |
| Repo structure (mono vs multi) | Deferred to architecture plan | — Pending |

---
*Last updated: 2026-01-28 after project initialization*
