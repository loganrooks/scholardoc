# Requirements: ScholarDoc

## v1 Requirements (Milestone 1)

### Ground Truth (GT)

- **GT-01**: Verified ground truth corpus -- annotated and human-verified pages for evaluation (10-20 pages across 3+ texts)
- **GT-02**: Modular, extensible ground truth schema -- start with extraction needs, designed for future annotation layers
- **GT-03**: Automated evaluation pipeline -- run extraction, compare to GT, produce metrics report with CI regression gate

### Intermediate Representation (IR)

- **IR-01**: ScholarDocument representation review -- enrich IR with bounding boxes, font info, confidence scores, cross-element references, annotation layer

### Writers (WR)

- **WR-01**: Writers module -- JSON serializer (lossless canonical), Markdown serializer (lossy presentation)

### Experimentation (EXP)

- **EXP-01**: Experimentation framework -- hypothesis-driven workflow with YAML spec, JSONL run log, stratified metrics, dev/validation split

### OCR (OCR)

- **OCR-01**: Re-OCR pipeline integration -- neural re-OCR for flagged words wired into main pipeline, foreign term CER tracking

### Architecture (ARCH)

- **ARCH-01**: Unified architecture plan -- ScholarDoc as extraction lib, scholarly_annotate as shared GT package, CryptOfCogito as corpus app
- **ARCH-02**: Determine repo structure -- monorepo with uv workspaces, shared scholarly_testdata package, migration plan

## v2 (Deferred)

- EPUB/MOBI support
- Cross-document relation mapping
- Corpus database (SQLAlchemy)
- MCP server
- RAG embedding/vector search
- Annotation UI (separate package)

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GT-01 | Phase 1 | Pending |
| GT-02 | Phase 1 | Pending |
| GT-03 | Phase 1 | Pending |
| IR-01 | Phase 2 | Pending |
| WR-01 | Phase 2 | Pending |
| EXP-01 | Phase 3 | Pending |
| OCR-01 | Phase 4 | Pending |
| ARCH-01 | Phase 5 | Pending |
| ARCH-02 | Phase 5 | Pending |
