# Requirements: ScholarDoc & ScholarGT

## v1 Requirements (Milestone 1 — ScholarGT)

### Schema (SCH)

- **SCH-01**: Universal GT schema — superset of all annotation types, combining spatial hierarchy (Cogito) with semantic richness (ScholarDoc), extensible without restructuring existing GT
- **SCH-02**: Config-driven label selection — project initialization selects needed annotation types from the universal superset, with sensible defaults per use case
- **SCH-03**: Per-element verification tracking — element-level verification status with reviewer identity, not just document/page-level

### Extractor Interface (EXT)

- **EXT-01**: Pluggable extractor protocol — interface that ScholarDoc, Docling, GROBID, or any pipeline can implement to produce draft GT
- **EXT-02**: Built-in lightweight extractor — minimal PyMuPDF-based extraction so ScholarGT works without external dependencies
- **EXT-03**: Extractor provenance — GT records which extractor + config produced each draft element, and what the human changed

### Experimentation (EXP)

- **EXP-01**: Experiment framework — YAML specs with hypothesis, parameters, success criteria; JSONL run logs; stratified metrics
- **EXP-02**: Pipeline-level comparison — compare end-to-end extraction results from different systems (ScholarDoc vs Docling vs GROBID)
- **EXP-03**: Component-level comparison — swap individual components (OCR engine, layout detector, structure extractor) and compare

### Annotation Tool (ANN)

- **ANN-01**: Annotation tool design — review Cogito tool, decide rewrite vs adapt, design architecture for ML-assisted annotation with verification workflow
- **ANN-02**: Annotation tool implementation — visual annotation (Canvas-based), ML-assisted pre-population, low-confidence flagging for human review
- **ANN-03**: Config-driven annotation UI — UI adapts to project's selected label types (from SCH-02), not hardcoded to one schema

### Evaluation (EVAL)

- **EVAL-01**: Automated evaluation pipeline — single command compares extraction output against GT, produces metrics report (CER/WER, element F1, per-type breakdown)
- **EVAL-02**: CI regression gate — fails build when extraction metrics regress beyond configured threshold

### Validation (VAL)

- **VAL-01**: Design validation corpus — small GT corpus (10-20 pages across 3+ texts) to prove the schema, tool, and evaluation pipeline work end-to-end

## v2 Requirements (Deferred — ScholarDoc improvements)

- **IR-01**: ScholarDocument representation review — enrich IR with bounding boxes, font info, confidence scores, cross-references, annotation layer
- **WR-01**: Writers module — JSON serializer (lossless canonical), Markdown serializer (lossy presentation)
- **OCR-01**: Re-OCR pipeline integration — neural re-OCR for flagged words wired into main pipeline
- **ARCH-01**: Unified architecture plan — repo structure, package boundaries, migration plan
- EPUB/MOBI support
- Cross-document relation mapping
- Corpus database (SQLAlchemy)
- MCP server
- RAG embedding/vector search

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCH-01 | Phase 1 | Pending |
| SCH-02 | Phase 1 | Pending |
| SCH-03 | Phase 1 | Pending |
| EXT-01 | Phase 2 | Pending |
| EXT-02 | Phase 2 | Pending |
| EXT-03 | Phase 2 | Pending |
| EXP-01 | Phase 3 | Pending |
| EXP-02 | Phase 3 | Pending |
| EXP-03 | Phase 3 | Pending |
| ANN-01 | Phase 4 | Pending |
| ANN-02 | Phase 4 | Pending |
| ANN-03 | Phase 4 | Pending |
| EVAL-01 | Phase 3 | Pending |
| EVAL-02 | Phase 3 | Pending |
| VAL-01 | Phase 5 | Pending |
