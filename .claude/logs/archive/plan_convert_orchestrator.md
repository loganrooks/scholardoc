# Implementation Plan: Convert Orchestrator & Integration

**Created:** 2025-12-24
**Status:** Ready for approval
**Scope:** All four items - orchestrator, SQLite, docs update, integration tests

---

## Summary

Build the `convert()` orchestrator that transforms PDFs into `ScholarDocument` objects by wiring together existing components (PDF reader, OCR pipeline, structure extractor). Add SQLite persistence for large documents, update documentation to reflect actual state, and create integration tests.

---

## Current State

| Component | Location | Status |
|-----------|----------|--------|
| `ScholarDocument` model | `models.py` | ✅ Complete |
| `PDFReader` → `RawDocument` | `readers/pdf_reader.py` | ✅ Complete |
| `OCRPipeline` | `normalizers/ocr_pipeline.py` | ✅ Complete |
| `CascadingExtractor` | `extractors/cascading.py` | ✅ Complete |
| `convert()` function | `__init__.py:109` | ❌ Stub only |
| Integration tests | - | ❌ Missing |
| SQLite persistence | - | ❌ Missing |

---

## Task Breakdown

### 1. Build `convert()` Orchestrator [Medium Complexity]

**File:** `scholardoc/convert.py` (new file)

**Purpose:** Wire existing components into a single coherent pipeline.

**Flow:**
```
PDF Path
    ↓
PDFReader.read() → RawDocument
    ↓
OCRPipeline.detect_line_breaks() → LineBreakCandidates
OCRPipeline.apply_line_breaks() → Clean text
OCRPipeline.detect_errors() → OCRErrorCandidates
    ↓
CascadingExtractor.extract() → StructureResult (sections)
    ↓
DocumentBuilder.build() → ScholarDocument
```

**Sub-tasks:**
- [ ] Create `scholardoc/convert.py` with `convert()` implementation
- [ ] Create `DocumentBuilder` class to construct ScholarDocument from components
- [ ] Handle text position mapping (raw positions → clean text positions)
- [ ] Build page spans from RawDocument pages
- [ ] Build section spans from StructureResult
- [ ] Build paragraph spans from text analysis
- [ ] Populate metadata from PDF metadata
- [ ] Wire OCR quality info into QualityInfo
- [ ] Update `__init__.py` to import real `convert()` function
- [ ] Implement `detect_format()` utility

**Dependencies:** None (uses existing components)

**Risk:** Position mapping complexity when artifacts are removed

---

### 2. Add SQLite Persistence [Low Complexity]

**Files:**
- `scholardoc/models.py` - Add `save_sqlite()` and `load_sqlite()` methods
- Modify `save()` to auto-select format based on size

**Design (from CORE_REPRESENTATION.md):**
```sql
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE content (text TEXT);
CREATE TABLE footnote_refs (position INTEGER, marker TEXT, target_id TEXT);
CREATE TABLE pages (start INTEGER, end INTEGER, label TEXT, idx INTEGER);
CREATE TABLE sections (start INTEGER, end INTEGER, title TEXT, level INTEGER);
CREATE TABLE notes (id TEXT PRIMARY KEY, text TEXT, type TEXT, page_label TEXT);

CREATE INDEX idx_pages_start ON pages(start);
CREATE INDEX idx_footnotes_pos ON footnote_refs(position);
```

**Sub-tasks:**
- [ ] Add `save_sqlite()` method to ScholarDocument
- [ ] Add `load_sqlite()` classmethod to ScholarDocument
- [ ] Modify `save()` to auto-select: JSON if <1MB text, SQLite otherwise
- [ ] Add test for SQLite roundtrip

**Dependencies:** None

**Risk:** Low - straightforward serialization

---

### 3. Update Documentation [Low Complexity]

**Files to update:**
- `ROADMAP.md` - Mark ScholarDocument model as complete
- `CLAUDE.md` - Update "Current Task" section

**Sub-tasks:**
- [ ] Update ROADMAP.md milestone 1.2 checkboxes
- [ ] Update ROADMAP.md milestone 1.7 checkboxes (query methods done)
- [ ] Update CLAUDE.md current task to reflect integration work
- [ ] Add Serena memory update for session handoff

**Dependencies:** After item 1 is complete

**Risk:** None

---

### 4. Add Integration Tests [Medium Complexity]

**File:** `tests/integration/test_convert.py` (new file)

**Test scenarios:**
1. Convert real PDF → ScholarDocument roundtrip
2. OCR pipeline integration (line breaks rejoined)
3. Structure extraction (sections detected)
4. RAG chunk generation with page labels
5. Quality info populated
6. Markdown export with footnotes

**Sub-tasks:**
- [ ] Create `tests/integration/` directory
- [ ] Create test fixtures with sample PDF paths
- [ ] Test: `convert()` returns valid ScholarDocument
- [ ] Test: Page spans match PDF page count
- [ ] Test: Section spans have reasonable confidence
- [ ] Test: `to_rag_chunks()` produces chunks with metadata
- [ ] Test: `to_markdown()` produces valid output
- [ ] Test: Save/load roundtrip preserves all data
- [ ] Test: OCR pipeline detects known errors from validation set

**Dependencies:** Item 1 must be complete

**Risk:** Test PDFs must be committed or referenced

---

## Files Affected

| File | Action | Description |
|------|--------|-------------|
| `scholardoc/convert.py` | Create | Main orchestration logic |
| `scholardoc/__init__.py` | Modify | Import real `convert()` |
| `scholardoc/models.py` | Modify | Add SQLite persistence |
| `tests/integration/test_convert.py` | Create | Integration tests |
| `tests/integration/__init__.py` | Create | Package marker |
| `ROADMAP.md` | Modify | Mark items complete |
| `CLAUDE.md` | Modify | Update current task |

---

## Test Strategy

**Unit Tests (existing):**
- `test_models.py` - ScholarDocument model (788 lines, comprehensive)
- `test_ocr_pipeline.py` - OCR pipeline components
- `test_pdf_reader.py` - PDF reading
- `test_extractors.py` - Structure extraction

**Integration Tests (new):**
- End-to-end `convert()` with real PDFs
- Validation set regression tests (130 error pairs)
- Markdown/RAG output validation

**Test PDFs:**
- Use existing test fixtures in `tests/fixtures/`
- Reference ground truth in `ground_truth/`

---

## Implementation Order

```
1. convert.py (orchestrator)      ← Core deliverable
   ├── DocumentBuilder class
   ├── Position mapping
   └── Wire components

2. Integration tests              ← Validate orchestrator
   ├── Basic convert() test
   └── Component integration tests

3. SQLite persistence             ← Enhancement
   ├── save_sqlite()
   └── load_sqlite()

4. Documentation update           ← Reflect reality
   ├── ROADMAP.md
   └── CLAUDE.md
```

---

## Open Questions

1. **Position Mapping Strategy:**
   - When we remove artifacts (page numbers, footnote markers), positions shift
   - Options:
     a. Track offset map during cleaning
     b. Keep original positions and adjust annotations
     c. Only store final positions (simpler, chosen by design doc)
   - **Recommendation:** Option (c) per CORE_REPRESENTATION.md

2. **Paragraph Detection:**
   - RawDocument has blocks, not paragraphs
   - Need to detect paragraph boundaries from whitespace/formatting
   - **Approach:** Use double-newlines or block boundaries

3. **OCR Error Candidates:**
   - OCRPipeline produces candidates for re-OCR
   - In Phase 1, we flag them but don't actually re-OCR
   - Store in `quality.needs_reocr` field
   - **Decision needed:** Include flagged word positions in output?

---

## Estimated Scope

| Item | Complexity | Lines of Code |
|------|------------|---------------|
| convert.py | Medium | ~300-400 |
| SQLite persistence | Low | ~150 |
| Integration tests | Medium | ~200-300 |
| Doc updates | Low | ~30 |
| **Total** | | ~700-850 |

---

## Success Criteria

- [ ] `scholardoc.convert("test.pdf")` returns valid ScholarDocument
- [ ] ScholarDocument has correct page count and labels
- [ ] Structure extraction produces sections with confidence scores
- [ ] OCR pipeline runs and populates quality info
- [ ] `to_rag_chunks()` produces chunks with page labels
- [ ] `to_markdown()` produces valid Markdown with frontmatter
- [ ] SQLite persistence works for documents >1MB
- [ ] All existing tests still pass (228 tests)
- [ ] Integration tests pass on sample PDFs
- [ ] ROADMAP reflects actual completion state

---

## Approval Request

Does this plan look correct? Should I proceed with implementation starting with the `convert()` orchestrator?
