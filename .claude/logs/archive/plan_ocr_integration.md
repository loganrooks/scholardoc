# Implementation Plan: OCR Pipeline Integration

**Created:** 2025-12-26
**Status:** Awaiting approval
**Phase:** Phase 1 - Core Implementation

---

## Summary

Integrate the validated OCR correction pipeline into ScholarDoc's main module. The pipeline uses spellcheck as a selector to flag suspicious words, then applies neural re-OCR only where needed. Architecture validated in spike 29 with 99.2% detection rate and 23.4% false positive rate.

---

## Step 1: Understand the Request

### What
Integrate the validated 3-stage OCR pipeline into the main codebase:
1. **Line-break rejoining** - Fix hyphenation artifacts using position data
2. **Error detection** - Flag suspicious words with adaptive spellcheck
3. **Selective re-OCR** - Apply neural OCR only to flagged lines

### Why
- OCR errors harm RAG embeddings (0.5-0.6 similarity vs 0.9+ for clean text)
- Existing embedded OCR has quality issues (validated in spike 05)
- Full re-OCR is too slow; selective approach balances speed and quality

### Who
- **RAG users**: Get cleaner embeddings for better retrieval
- **Anki/flashcard generators**: Get accurate text for study cards
- **Citation managers**: Get correct text for page number references

### Context
- Phase 1 milestone 1.6: Quality filtering
- Builds on PyMuPDF position data from readers module
- Integrates with DocumentBuilder in convert.py
- Follows graceful degradation principle

---

## Step 2: Research Current State

### Existing Components

| Component | Location | Status |
|-----------|----------|--------|
| PyMuPDF reader | `readers/pdf_reader.py` | ✅ Complete |
| Document builder | `convert.py` | ✅ Complete |
| Position data | `RawDocument.pages[].blocks` | ✅ Available |
| Page images | PyMuPDF can extract | ✅ Available |

### Validated Design

**Source:** `spikes/29_ocr_pipeline_design.py` (588 lines)

**Classes to port:**
- `AdaptiveDictionary` - Dictionary with morphological validation
- `LineBreakRejoiner` - Block-filtered line-break detection
- `OCRErrorDetector` - Hybrid spellcheck + morphology
- `OCRPipeline` - Main orchestrator

**Validation:**
- Test set: 130 error pairs, 77 correct words
- Detection rate: 99.2%
- False positive rate: 23.4% (German terms)
- False negatives: 1 (fragment 'es')

### Integration Point

`DocumentBuilder._process_text()` in `convert.py:114`:
```python
def _process_text(self, raw: RawDocument) -> tuple[str, list[QualityIssue]]:
    """Extract and clean text from raw document.

    Current: Basic concatenation
    Future: OCR pipeline here
    """
```

### Dependencies

**External (Two-Tier Strategy):**
- `pyspellchecker` - Already in pyproject.toml
- `pytesseract` - CPU-optimized OCR (0.373 similarity, 2.0s/page, ~1.35s per dirty page line-based)
- `python-doctr[torch]` - GPU-optimized OCR (0.402 similarity, 0.6s/page, ~0.45s per dirty page line-based)
- `torch` - For docTR GPU acceleration
- `Pillow` - Image handling for both engines

**Optional Dependency Strategy:**
```toml
[project.optional-dependencies]
ocr = ["pytesseract>=0.3.10", "Pillow>=10.0"]  # Default: Fast CPU (Tesseract)
ocr-gpu = ["python-doctr[torch]>=0.6", "pytesseract>=0.3.10", "Pillow>=10.0"]  # Premium: Best quality (docTR) + fallback
```

**Internal:**
- `RawDocument` model with position data
- Quality assessment models (already defined)

---

## Step 3: Define Scope

### In Scope

#### Create OCR Module (`scholardoc/ocr/`)
- `pipeline.py` - Main `OCRPipeline` class
- `dictionary.py` - `AdaptiveDictionary` with safeguards
- `linebreak.py` - `LineBreakRejoiner` with block filtering
- `detector.py` - `OCRErrorDetector` with hybrid validation
- `reocr.py` - Hybrid re-OCR wrapper with GPU-first fallback chain:
  - Primary: docTR (GPU) - Best quality, fastest
  - Fallback: Tesseract (CPU) - Good quality, 3x faster on CPU
  - Last resort: docTR (CPU) - Best quality, slow
  - Graceful: None - Skip re-OCR if nothing available
- `__init__.py` - Public exports

#### Integrate with DocumentBuilder
- Add OCR pipeline call in `_process_text()`
- Pass configuration for enable/disable
- Track quality metrics
- Handle errors gracefully

#### Add Configuration
- `config.py` - Add OCR settings:
  - `enable_ocr_correction: bool = True`
  - `min_confidence: float = 0.7`
  - `max_false_positive_rate: float = 0.3`

#### Update Models
- Add `ocr_corrections: list[OCRCorrection]` to `ScholarDocument`
- Define `OCRCorrection` dataclass with before/after/confidence

#### Tests
- Unit tests for each OCR component (dictionary, linebreak, detector)
- Integration tests with real PDFs from validation set
- Performance benchmarks (should be <1s per page)

### Out of Scope

**Deferred to future:**
- Custom neural OCR models (use docTR/Tesseract for now)
- GUI for reviewing corrections
- Batch processing optimization
- Multi-language dictionaries (English only for now)
- Additional OCR engines (EasyOCR, TrOCR, etc.)

**Explicit non-goals:**
- Don't modify spike files (keep as reference)
- Don't re-validate architecture (trust spike results)
- Don't add new OCR techniques (port validated design only)

---

## Step 4: Test Strategy

### Unit Tests (`tests/unit/test_ocr.py`)

#### AdaptiveDictionary
```python
test_dictionary_validates_real_words:
  Given: AdaptiveDictionary with base words
  When: is_valid("philosophy")
  Then: Returns True

test_dictionary_flags_ocr_errors:
  Given: AdaptiveDictionary with base words
  When: is_valid("philosopby")  # 'by' instead of 'phy'
  Then: Returns False

test_dictionary_learns_specialized_terms:
  Given: AdaptiveDictionary, term "Dasein" appears 3 times
  When: is_valid("Dasein")
  Then: Returns True (learned from frequency)

test_dictionary_rejects_morphologically_invalid:
  Given: AdaptiveDictionary
  When: Learning "xyzabc" (no base form exists)
  Then: Does not learn (fails morphological validation)
```

#### LineBreakRejoiner
```python
test_rejoins_hyphenated_words:
  Given: "philo-\nsophy" at end of line
  When: rejoin(blocks)
  Then: Returns "philosophy"

test_block_filter_prevents_margin_matches:
  Given: "meta-" in block 1, "a x" (page marker) in block 2
  When: rejoin(blocks)
  Then: Does NOT join (different blocks)

test_validates_joins_against_dictionary:
  Given: "philosop-\nby" (would create invalid "philosopby")
  When: rejoin(blocks)
  Then: Does NOT join (dictionary validation fails)
```

#### OCRErrorDetector
```python
test_detects_character_substitutions:
  Given: "tbese" (OCR error for "these")
  When: detect_errors(text)
  Then: Flags "tbese" for re-OCR

test_skips_valid_words:
  Given: "philosophy"
  When: detect_errors(text)
  Then: Does NOT flag

test_handles_german_terms:
  Given: "Dasein" (valid German term)
  When: detect_errors(text)
  Then: Flags (acceptable false positive for verification)
```

### Integration Tests (`tests/integration/test_ocr_pipeline.py`)

```python
test_pipeline_on_validation_set:
  Given: validation_set.json with 130 error pairs
  When: Run full pipeline
  Then: Detection rate >= 99%, false positive rate <= 30%

test_pipeline_with_real_pdf:
  Given: Heidegger PDF with known OCR errors
  When: convert(pdf, enable_ocr_correction=True)
  Then: ScholarDocument.ocr_corrections has flagged words

test_pipeline_handles_clean_pdf:
  Given: PDF with no OCR errors
  When: convert(pdf)
  Then: Fast processing (<1s per page), no corrections

test_pipeline_graceful_degradation:
  Given: PDF where Tesseract fails
  When: convert(pdf)
  Then: Returns original text with warning, does not crash
```

### Performance Tests

```python
test_pipeline_performance_clean_pages:
  Given: 10-page PDF with clean OCR
  When: Run pipeline
  Then: Completes in <10 seconds (1s per page)

test_pipeline_performance_dirty_pages:
  Given: 10-page PDF with 30% error rate
  When: Run pipeline
  Then: Completes in <60 seconds (allow re-OCR overhead)
```

---

## Step 5: Task Breakdown

| # | Task | Complexity | Dependencies | Risk |
|---|------|------------|--------------|------|
| 1 | Add dependencies (pytesseract, doctr, torch, Pillow) + pyproject.toml extras | Low | None | Low |
| 2 | Create `scholardoc/ocr/` directory structure | Low | None | Low |
| 3 | Port `AdaptiveDictionary` from spike | Medium | Task 2 | Low |
| 4 | Port `LineBreakRejoiner` from spike | Medium | Task 2 | Low |
| 5 | Port `OCRErrorDetector` from spike | Medium | Task 3 | Low |
| 6 | Implement hybrid re-OCR wrapper (Tesseract + docTR with GPU detection) | High | Task 2 | Medium |
| 7 | Port `OCRPipeline` orchestrator from spike | Medium | Tasks 3-6 | Medium |
| 8 | Add `OCRCorrection` model to models.py | Low | None | Low |
| 9 | Integrate pipeline into DocumentBuilder | Medium | Task 7, 8 | High |
| 10 | Add OCR config to config.py | Low | None | Low |
| 11 | Write unit tests (Tasks 3-5) | Medium | Tasks 3-5 | Low |
| 12 | Write integration tests | High | Task 9 | Medium |
| 13 | Run validation against ground truth | Medium | Task 12 | Low |
| 14 | Update ROADMAP.md milestone 1.6 | Low | Task 13 | Low |

### Task Ordering Rationale
- **Tasks 1-2**: Setup (prerequisites) - includes two-tier optional dependencies
- **Tasks 3-5**: Port individual components (can be parallel)
- **Task 6**: Riskiest item (hybrid re-OCR with 2 engines + GPU detection) - do early to fail fast
- **Task 7**: Orchestrator depends on components
- **Tasks 8-10**: Models and config (can be parallel with 3-7)
- **Task 9**: Integration (depends on everything)
- **Tasks 11-13**: Testing (verify correctness for both engines)
- **Task 14**: Documentation

---

## Step 6: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| No OCR engine available | Low | Medium | Graceful fallback chain: docTR-GPU → Tesseract-CPU → docTR-CPU → skip re-OCR |
| Users without GPU get slow performance | Medium | Low | Default to Tesseract CPU (3x faster than docTR-CPU, only 7% quality loss) |
| Tesseract not installed on system | Medium | Low | Clear error with install instructions, fall back to docTR if available |
| Two engines increase complexity | Medium | Low | Abstract via unified interface, comprehensive testing |
| False positives annoy users | Medium | Low | Document expected rate, provide config to tune |
| Line cropping fails for complex layouts | Low | Medium | Fall back to full page re-OCR, log warning |
| Integration breaks existing tests | Low | High | Make OCR correction opt-in by default during testing |
| Spike code doesn't match production needs | Low | Medium | Port iteratively, validate at each step |

### Critical Risks (High Impact)

**1. Multi-Engine Complexity**
- **Problem**: Managing two different OCR engines (Tesseract + docTR)
- **Solution**:
  - Unified `ReOCREngine` interface
  - Auto-detection and fallback chain
  - Clear logging of which engine is used
  - Comprehensive tests for both engines

**2. Performance on CPU-Only Systems**
- **Problem**: Users without GPU might get slow re-OCR
- **Solution**:
  - Default to Tesseract (fast on CPU: ~1.35s per dirty page)
  - Only use docTR-CPU if explicitly requested
  - Warn users about GPU availability
  - Line-based processing minimizes impact (only ~30% of lines)

**3. Installation Complexity**
- **Problem**: Different install commands for CPU vs GPU users
- **Solution**:
  - `pip install scholardoc[ocr]` → Tesseract (works everywhere)
  - `pip install scholardoc[ocr-gpu]` → docTR + Tesseract (premium quality)
  - Clear docs explaining trade-offs

**3. Breaking Existing Tests**
- **Problem**: New OCR pipeline might alter test outputs
- **Solution**:
  - Default `enable_ocr_correction=False` in tests
  - Update test fixtures incrementally
  - Keep original behavior available

---

## Step 7: Open Questions

### Blocking Questions

**Q1: Should OCR correction be enabled by default?**
- **Options:**
  - A) Enabled by default (better quality, but requires Tesseract)
  - B) Disabled by default (safer, user opts in)
- **Recommendation:** **B - Disabled by default** for Phase 1, enable by default in Phase 2 after validation
- **Rationale:** Avoids breaking users without Tesseract, allows testing period

**Q2: How to handle OCR engine installation?**
- **Options:**
  - A) Required dependency (fails if not installed)
  - B) Single optional extra with one engine
  - C) Two-tier extras: `ocr` (Tesseract) and `ocr-gpu` (docTR + Tesseract)
- **Recommendation:** **C - Two-tier extras ✓ APPROVED**
- **Rationale:**
  - `scholardoc[ocr]` → Tesseract (~10MB, fast on CPU)
  - `scholardoc[ocr-gpu]` → docTR + Tesseract (~500MB, best quality with GPU)
  - Fallback chain: docTR-GPU → Tesseract-CPU → docTR-CPU → skip re-OCR
  - Maximizes compatibility while offering premium option

**Q3: What to do with OCR corrections in output?**
- **Options:**
  - A) Include in main text (corrections applied)
  - B) Store separately (original + corrections)
  - C) Both (original preserved, corrections applied)
- **Recommendation:** **C - Both**
- **Rationale:** Transparency for users, allows verification

### Non-Blocking Questions (Can decide during implementation)

**Q4: Should we cache re-OCR results?**
- Can decide based on performance testing
- Probably yes, but not blocking

**Q5: Should we support custom dictionaries?**
- Defer to Phase 2
- AdaptiveDictionary learns automatically for now

---

## Plan Output Summary

### 1. Summary
Integrate the validated 3-stage OCR pipeline (line-break rejoining → error detection → selective re-OCR) into ScholarDoc's DocumentBuilder. Pipeline achieves 99.2% detection rate. **Two-tier re-OCR strategy**: Tesseract (CPU-optimized, ~1.35s per dirty page) for `scholardoc[ocr]`, docTR (GPU-optimized, ~0.45s per dirty page) for `scholardoc[ocr-gpu]`, with graceful fallback chain for maximum compatibility.

### 2. Scope
**In:** Port 4 validated classes from spike, create `scholardoc/ocr/` module, integrate with DocumentBuilder, add config/models, write comprehensive tests.

**Out:** Custom neural models, GUI, batch optimization, multi-language support, GUI review tools.

### 3. Research Findings
- Spike 29 validated architecture (588 lines, 99.2% detection)
- Spike 10 validated re-OCR engines: docTR (0.402 quality, GPU), Tesseract (0.373 quality, CPU-efficient)
- Integration point identified: `DocumentBuilder._process_text()`
- Dependencies available: PyMuPDF position data, pyspellchecker
- Two-tier strategy: Tesseract (3x faster on CPU) + docTR (best quality on GPU)

### 4. Test Strategy
- **Unit tests**: Each component (dictionary, linebreak, detector, re-OCR)
- **Integration tests**: Full pipeline on validation set (130 pairs)
- **Performance tests**: <1s per clean page, <6s per dirty page
- **Graceful degradation**: Missing Tesseract, re-OCR failure

### 5. Tasks
14 tasks ordered by dependencies:
1. Dependencies (tesseract, Pillow)
2. Module structure
3-5. Port components (parallel)
6. Neural re-OCR (risky, do early)
7. Orchestrator
8-10. Models/config (parallel)
9. Integration (depends on all)
11-14. Testing and documentation

### 6. Risks
- **Medium impact**: Two-engine complexity, CPU performance, installation options
- **Mitigations**: Unified interface, Tesseract CPU fallback (3x faster), two-tier extras (ocr vs ocr-gpu), comprehensive testing

### 7. Questions
**Resolved:**
- Q1: Default disabled ✓ (approved)
- Q2: Two-tier extras (ocr vs ocr-gpu) ✓ (approved)
- Q3: Store both original + corrections ✓ (approved)

**Ready to proceed with implementation.**

---

## ✅ PLAN APPROVED - Ready to Implement

**Strategy:** Two-tier OCR system
- `pip install scholardoc[ocr]` → Tesseract (fast CPU, ~1.35s/page dirty)
- `pip install scholardoc[ocr-gpu]` → docTR + Tesseract (best quality GPU, ~0.45s/page)
- Fallback chain: docTR-GPU → Tesseract-CPU → docTR-CPU → skip re-OCR

**Estimated effort:** ~6-8 hours (14 tasks, hybrid re-OCR wrapper adds complexity but validated designs reduce uncertainty)

**Risk level:** Medium (two engines + GPU detection, but both validated in spikes)

**Next step:** Create feature branch `feature/ocr-integration`, start with Task 1 (add dependencies to pyproject.toml)
