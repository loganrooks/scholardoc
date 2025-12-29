# OCR Pipeline Implementation Plan - Session 2
**Created:** 2025-12-26
**Status:** DRAFT - Pending Review
**Session:** Continuation of feature/ocr-integration
**Previous Progress:** 2/14 tasks complete (setup phase)

---

## Executive Summary

### Context
We're implementing the validated OCR pipeline from spike 29 into the production codebase. The setup phase is complete (dependencies, module structure, feature branch). This plan covers the implementation phase: porting 6 validated components, integrating with convert.py, and comprehensive testing.

### Objectives
1. **Port validated components** from spike to production with quality improvements
2. **Validate highest-risk component early** (hybrid re-OCR) to fail fast
3. **Maintain 99.2% detection rate** from spike validation
4. **Ensure backward compatibility** (OCR disabled by default)
5. **Complete Phase 1** of OCR integration roadmap

### Strategic Approach
**Risk-First Sequencing**: Implement the highest-risk component (Task 6: reocr.py) second, immediately after the foundation (Task 3: dictionary.py). This validates the most complex part early, before investing time in integration.

**Why Not Sequential (3→4→5→6→7)?**
Sequential discovers Task 6 risks late, after spending time on Tasks 4-5. Our approach validates the hard part early, making the rest feel like cleanup.

### Key Metrics (from Spike Validation)
- **Detection Rate:** 99.2% (129/130 errors caught)
- **False Positive Rate:** 23.4% (acceptable for Phase 1)
- **Performance Target:** <1.5s/page (CPU), <0.5s/page (GPU)
- **Validation Set:** 130 error pairs + 77 correct words

---

## Task Breakdown

### Task 3: Port AdaptiveDictionary ✅ Foundation
**File:** `scholardoc/ocr/dictionary.py`
**Source:** `spikes/29_ocr_pipeline_design.py` (~100 lines)
**Complexity:** LOW
**Risk:** LOW
**Estimated Time:** 30-40 minutes

**Scope:**
- Base dictionary + learned words with safeguards
- Morphological validation (plurals, verb forms, prefixes)
- Pattern validation (has vowels, reasonable length)
- Frequency thresholds for learning new words
- Confidence scoring for unknown words

**Quality Gates:**
- [ ] Type hints on all public methods
- [ ] Docstrings with examples
- [ ] Unit tests for morphological rules
- [ ] Tests for learning safeguards (don't learn OCR errors)
- [ ] Ruff linting passes

**Dependencies:** None (uses pyspellchecker from base deps)
**Blocks:** Tasks 4, 5 (both depend on dictionary)

**Porting Notes:**
- Remove spike timing/print statements
- Add proper logging
- Extract magic numbers to class constants
- Add error handling for dictionary file access

---

### Task 6: Port Hybrid Re-OCR Engine 🔥 HIGHEST RISK
**File:** `scholardoc/ocr/reocr.py`
**Source:** `spikes/29_ocr_pipeline_design.py` (~150 lines)
**Complexity:** HIGH
**Risk:** HIGH
**Estimated Time:** 90-120 minutes

**Scope:**
- GPU detection logic (torch.cuda.is_available())
- Four-tier fallback chain:
  1. docTR (GPU) - 0.402 quality, ~0.45s/page 🏆
  2. Tesseract (CPU) - 0.373 quality, ~1.35s/page ⚡
  3. docTR (CPU) - 0.402 quality, ~4.5s/page 🐌
  4. Skip re-OCR - graceful degradation
- Line-level image cropping from page coordinates
- Word-level text replacement in line context
- Import-time dependency checks
- Error handling and logging

**Quality Gates:**
- [ ] Type hints with Optional for missing deps
- [ ] Comprehensive docstrings
- [ ] Test all 4 fallback scenarios
- [ ] Test GPU available vs unavailable
- [ ] Test missing dependency handling
- [ ] Edge case tests (line at page boundary, rotated text)
- [ ] Performance validation (<1.5s CPU, <0.5s GPU)

**Dependencies:** None (standalone component)
**Blocks:** Task 7 (pipeline needs re-OCR)

**Risk Mitigation:**
1. **GPU detection failures** → Test on both GPU/CPU systems, graceful fallback
2. **Missing dependencies** → Import-time checks with clear errors
3. **Image cropping errors** → Validate crop dimensions, log failures
4. **Re-OCR quality worse** → Compare confidence scores before replacement
5. **Performance regression** → Profile on validation set, optimize hot paths

**WHY DO THIS EARLY:**
- Highest technical complexity (GPU, dependencies, fallback chain)
- Independent (no dependencies on other tasks)
- If this fails, we know before investing time in Tasks 4-5-7
- Validates two-tier dependency strategy works in practice
- Tests the riskiest assumption: line-level re-OCR works reliably

**Testing Strategy:**
```python
# Mock scenarios to test:
1. GPU available + doctr installed → use docTR GPU
2. GPU unavailable + doctr installed → use docTR CPU
3. GPU available + only tesseract → use Tesseract
4. No OCR engines installed → graceful skip with warning
5. Image crop fails → log error, return original text
6. Re-OCR quality worse → keep original text
```

---

### Task 4: Port LineBreakRejoiner
**File:** `scholardoc/ocr/linebreak.py`
**Source:** `spikes/29_ocr_pipeline_design.py` (~80 lines)
**Complexity:** MEDIUM
**Risk:** LOW
**Estimated Time:** 45-60 minutes

**Scope:**
- Block-based filtering (ADR-003)
- Line-end hyphenation detection using PyMuPDF positions
- Dictionary validation before rejoining
- Learn newly discovered words via AdaptiveDictionary
- Only rejoin within same block (prevents margin matches)

**Quality Gates:**
- [ ] Type hints
- [ ] Docstrings
- [ ] Test block filtering (don't join across blocks)
- [ ] Test hyphenation rejoining
- [ ] Test validation against dictionary
- [ ] Edge cases (hyphenated proper nouns, compound words)

**Dependencies:** Task 3 (dictionary.py)
**Blocks:** Task 7 (pipeline)

**Porting Notes:**
- Preserve block filtering logic (validated in spike)
- Add logging for rejected joins (debugging)
- Extract block comparison logic to separate method

---

### Task 5: Port OCRErrorDetector
**File:** `scholardoc/ocr/detector.py`
**Source:** `spikes/29_ocr_pipeline_design.py` (~70 lines)
**Complexity:** MEDIUM
**Risk:** LOW
**Estimated Time:** 45-60 minutes

**Scope:**
- Spellcheck-based error detection
- Morphological analysis for unknown words
- Scholarly vocabulary filtering (German/French/Latin/Greek)
- Adaptive dictionary integration
- Flag suspicious words for re-OCR (don't auto-correct)

**Quality Gates:**
- [ ] Type hints
- [ ] Docstrings
- [ ] Test detection accuracy (≥99% on validation set)
- [ ] Test false positive rate (≤25% acceptable)
- [ ] Test scholarly vocabulary filtering
- [ ] Test morphological validation

**Dependencies:** Task 3 (dictionary.py)
**Blocks:** Task 7 (pipeline)

**Porting Notes:**
- Add scholarly term list as class constant
- Extract morphological rules to separate methods
- Add confidence scoring to flagged words

---

### Task 7: Port OCRPipeline Orchestrator
**File:** `scholardoc/ocr/pipeline.py`
**Source:** `spikes/29_ocr_pipeline_design.py` (~100 lines)
**Complexity:** MEDIUM
**Risk:** MEDIUM (integration point)
**Estimated Time:** 60-90 minutes

**Scope:**
- Orchestrate three stages:
  1. LineBreakRejoiner (prepares text)
  2. OCRErrorDetector (flags suspicious words)
  3. Hybrid re-OCR (corrects flagged words)
- Page-level processing interface
- Performance tracking (corrections made, time spent)
- Error handling and logging
- Graceful degradation if components fail

**Quality Gates:**
- [ ] Type hints
- [ ] Docstrings with usage examples
- [ ] Integration test with all components
- [ ] Test graceful degradation (component failures)
- [ ] Test clean pages (skip re-OCR correctly)
- [ ] Test dirty pages (validate corrections)
- [ ] Performance validation on validation set

**Dependencies:** Tasks 3, 4, 5, 6 (all components)
**Blocks:** Task 9 (convert.py integration)

**Porting Notes:**
- Add pipeline statistics tracking
- Extract stage execution to separate methods
- Add debug logging for each stage

---

### Task 8: Define OCR Data Models
**File:** `scholardoc/models.py` (additions)
**Complexity:** LOW
**Risk:** LOW
**Estimated Time:** 30 minutes

**Scope:**
```python
@dataclass
class OCRConfig:
    enabled: bool = False  # Disabled by default
    engine: str = "auto"  # "auto" | "tesseract" | "doctr"
    confidence_threshold: float = 0.5

@dataclass
class OCRMetadata:
    correction_applied: bool
    original_text: Optional[str]
    confidence: float
    engine_used: Optional[str]

# Add to TextBlock:
ocr_metadata: Optional[OCRMetadata] = None

# Add to ScholarDocument:
ocr_stats: Optional[dict] = None  # {corrections_made, processing_time_ms}
```

**Quality Gates:**
- [ ] Type hints
- [ ] Docstrings
- [ ] Validation tests for models
- [ ] Backward compatibility (existing tests pass)

**Dependencies:** None
**Blocks:** Task 9 (convert.py needs models)

---

### Task 9: Integrate OCR into convert()
**File:** `scholardoc/convert.py` (modifications)
**Complexity:** MEDIUM
**Risk:** HIGH (integration, potential regressions)
**Estimated Time:** 60 minutes

**Scope:**
- Import OCRPipeline
- Check OCRConfig.enabled flag
- Pass page images + extracted text to pipeline
- Replace text with corrected version
- Populate OCR metadata in TextBlocks
- Track OCR statistics in ScholarDocument
- Ensure all existing tests pass (288 tests)

**Quality Gates:**
- [ ] Type hints
- [ ] Docstrings updated
- [ ] All existing tests pass (no regressions)
- [ ] OCR disabled by default (backward compatible)
- [ ] Test with OCR enabled
- [ ] Test with missing optional deps (graceful degradation)

**Dependencies:** Tasks 7, 8 (pipeline + models)
**Blocks:** Task 11-13 (integration tests)

**Integration Points:**
```python
# Before:
text = pdf_reader.extract_text(page)

# After:
text = pdf_reader.extract_text(page)
if config.ocr.enabled:
    page_image = pdf_reader.get_page_image(page)
    text, metadata = ocr_pipeline.process_page(page_image, text)
    # Store metadata for debugging/validation
```

---

### Task 10: Add Configuration Support
**File:** `scholardoc/config.py` (additions)
**Complexity:** LOW
**Risk:** LOW
**Estimated Time:** 30 minutes

**Scope:**
- Default OCRConfig (disabled)
- Environment variable overrides
- Configuration validation
- Clear error messages for missing deps

**Quality Gates:**
- [ ] Type hints
- [ ] Docstrings
- [ ] Test default config (OCR disabled)
- [ ] Test config with OCR enabled
- [ ] Test invalid config handling

**Dependencies:** Task 8 (models)
**Blocks:** None

---

### Task 11: Unit Tests for OCR Components
**Files:** `tests/ocr/test_*.py` (6 new files)
**Complexity:** HIGH
**Risk:** MEDIUM
**Estimated Time:** 60 minutes

**Scope:**
- `test_dictionary.py`: Morphological rules, learning safeguards
- `test_linebreak.py`: Block filtering, hyphenation rejoining
- `test_detector.py`: Detection accuracy, false positives
- `test_reocr.py`: All fallback scenarios, GPU detection, edge cases
- `test_pipeline.py`: Integration, graceful degradation
- `test_models.py`: Model validation, backward compatibility

**Quality Gates:**
- [ ] Test coverage ≥80% for new code
- [ ] All unit tests pass
- [ ] Mock external dependencies (doctr, tesseract)
- [ ] Fast execution (<5s total)

**Dependencies:** Tasks 3-10 (all components)
**Blocks:** None (can run in parallel with Task 12)

---

### Task 12: Integration Tests with Validation Set
**Files:** `tests/ocr/test_integration.py`
**Complexity:** HIGH
**Risk:** MEDIUM
**Estimated Time:** 45 minutes

**Scope:**
- Load validation set (130 error pairs + 77 correct words)
- Test detection rate ≥99%
- Test false positive rate ≤25%
- Test end-to-end convert() with OCR enabled
- Compare outputs to spike performance

**Quality Gates:**
- [ ] Detection rate ≥99% (matches spike)
- [ ] False positive rate ≤25%
- [ ] All 288 existing tests still pass
- [ ] No performance regression

**Dependencies:** Tasks 3-10 (full pipeline)
**Blocks:** None

**Validation Strategy:**
```python
# Load ground truth
validation_set = load_validation_set()

# Test detection
detected = detector.detect_errors(validation_set.ocr_text)
detection_rate = len(detected) / len(validation_set.errors)
assert detection_rate >= 0.99

# Test false positives
flagged_correct = detector.detect_errors(validation_set.correct_words)
fp_rate = len(flagged_correct) / len(validation_set.correct_words)
assert fp_rate <= 0.25
```

---

### Task 13: Performance Validation
**Files:** `tests/ocr/test_performance.py`
**Complexity:** MEDIUM
**Risk:** LOW
**Estimated Time:** 15 minutes

**Scope:**
- Benchmark on validation set
- Measure time per page (clean vs dirty)
- Validate targets: <1.5s CPU, <0.5s GPU
- Memory usage profiling

**Quality Gates:**
- [ ] Clean pages: <50ms overhead
- [ ] Dirty pages (Tesseract): <1.5s
- [ ] Dirty pages (docTR GPU): <0.5s
- [ ] Memory usage: <200MB additional

**Dependencies:** Tasks 3-10 (full pipeline)
**Blocks:** None

---

### Task 14: Update Documentation
**Files:** `ROADMAP.md`, `README.md`
**Complexity:** LOW
**Risk:** LOW
**Estimated Time:** 15 minutes

**Scope:**
- Mark Phase 1 as complete in ROADMAP.md
- Add OCR capabilities to README.md
- Document optional dependencies
- Add usage examples

**Quality Gates:**
- [ ] ROADMAP.md updated
- [ ] README.md mentions OCR
- [ ] Installation instructions clear
- [ ] Usage examples accurate

**Dependencies:** Tasks 3-13 (completion)
**Blocks:** None

---

## Dependencies & Sequencing

### Dependency Graph
```
Task 3 (dictionary) ──┬──> Task 4 (linebreak) ──┐
                      │                          │
                      └──> Task 5 (detector) ────┤
                                                 │
Task 6 (reocr) ──────────────────────────────────┤
                                                 ├──> Task 7 (pipeline) ──┐
                                                 │                         │
Task 8 (models) ─────────────────────────────────┼─────────────────────────┤
                                                                          │
                                                                          ├──> Task 9 (convert)
                                                                          │
Task 10 (config) ────────────────────────────────────────────────────────┘
                                                                          │
                                                                          ├──> Tasks 11-13 (tests)
                                                                          │
                                                                          └──> Task 14 (docs)
```

### Recommended Sequence
**Phase 1: Foundation + Risk Validation (2-3 hours)**
1. Task 3: dictionary.py (30 min) - Unblocks 4 & 5
2. Task 6: reocr.py (90-120 min) - Validate highest risk early

**Phase 2: Component Implementation (2-3 hours)**
3. Task 4: linebreak.py (45 min)
4. Task 5: detector.py (45 min)
5. Task 7: pipeline.py (60 min)

**Phase 3: Integration (2 hours)**
6. Task 8: models.py (30 min)
7. Task 10: config.py (30 min)
8. Task 9: convert.py (60 min)

**Phase 4: Testing & Validation (2-3 hours)**
9. Task 11: Unit tests (60 min)
10. Task 12: Integration tests (45 min)
11. Task 13: Performance tests (15 min)

**Phase 5: Documentation (15 min)**
12. Task 14: Update ROADMAP.md, README.md

**Total Estimated Time:** 8-10 hours

### Why This Sequence?

**Task 3 First:**
- LOW complexity = good warm-up
- Unblocks dependent tasks 4 & 5
- Foundation for validation logic

**Task 6 Second (CRITICAL DECISION):**
- **Highest risk component** (GPU detection, dependency management, fallback chain)
- **Independent** (no dependencies on other tasks)
- **Fail-fast principle**: If this doesn't work, we know before investing time
- **Validates strategy early**: Two-tier dependencies, line-level re-OCR
- If Task 6 fails or is too slow, we adjust strategy before more investment

**Tasks 4-5 Next:**
- Medium complexity after hard task (psychological benefit)
- Both depend on Task 3 (already complete)
- Build on validated foundation

**Task 7 (Pipeline) After Components:**
- Requires ALL components (3-6) to be complete
- Integration validation point
- Orchestration is easier than individual component logic

**Tasks 8-10 (Models/Config/Integration):**
- Complete the module interface
- Wire into main convert() function
- Enable end-to-end flow

**Tasks 11-13 (Tests) Before Documentation:**
- Validate everything works
- Catch regressions
- Benchmark performance

---

## Risk Analysis

### Critical Risks

#### RISK 1: GPU Detection Failures ⚠️ HIGH IMPACT
**Scenario:** torch.cuda.is_available() behaves unexpectedly, or GPU tests fail in CI

**Mitigation:**
- Test on both GPU and CPU systems during development
- Add CI environment flag to skip GPU tests
- Document GPU requirements clearly
- Ensure CPU fallback works reliably

**Recovery:**
- If GPU detection fails: Skip GPU tests in CI, require manual GPU validation pre-merge
- If GPU performance poor: Document as known issue, optimize in Phase 2
- Worst case: Remove GPU path, use Tesseract-only (still functional)

**Detection:** Task 6 implementation will surface this immediately

---

#### RISK 2: Missing Optional Dependencies 🔧 MEDIUM IMPACT
**Scenario:** Users install scholardoc without OCR deps, get cryptic errors

**Mitigation:**
- Clear installation documentation
- Import-time checks with helpful error messages
- Graceful degradation (skip OCR, log warning)
- Test without optional deps installed

**Recovery:**
- Add dependency checker utility
- Improve error messages based on user feedback
- Consider bundling Tesseract (simpler installation)

**Detection:** Task 6, Task 9 (integration testing)

---

#### RISK 3: Detection Rate Regression 📉 HIGH IMPACT
**Scenario:** Ported code doesn't match spike performance (99.2% → lower)

**Mitigation:**
- Port carefully, preserve algorithm logic
- Test incrementally (unit tests per component)
- Compare outputs to spike on validation set
- Debug discrepancies immediately

**Recovery:**
- Diff ported code vs spike code
- Add more unit tests to isolate issue
- May need algorithm adjustments or spike re-validation

**Detection:** Task 12 (integration tests with validation set)

---

#### RISK 4: Integration Breaks Existing Functionality 🚨 CRITICAL
**Scenario:** OCR integration causes regressions in existing features

**Mitigation:**
- Run all 288 existing tests after each change
- OCR disabled by default (backward compatible)
- Comprehensive regression test suite
- Code review before merge

**Recovery:**
- Feature flag rollback (disable OCR in config)
- Fix integration bugs before re-enabling
- Add more regression tests

**Detection:** Task 9 (convert.py integration), Task 12 (regression tests)

---

#### RISK 5: Performance Targets Not Met 🐌 MEDIUM IMPACT
**Scenario:** Re-OCR takes >1.5s per page on CPU (too slow for users)

**Mitigation:**
- Profile hot paths early (Task 13)
- Optimize critical code (line cropping, text replacement)
- Consider caching strategies
- Document performance expectations

**Recovery:**
- Acceptable for Phase 1 (mark as known limitation)
- Defer optimization to Phase 2
- Add performance tuning guide for users
- Consider async processing in future

**Detection:** Task 13 (performance tests)

---

#### RISK 6: Line-Level Cropping Failures 📐 MEDIUM IMPACT
**Scenario:** Line coordinates from PyMuPDF don't work with all PDF types

**Mitigation:**
- Test on diverse PDFs (scanned, digital, mixed)
- Add validation for crop dimensions
- Fallback to word-level or skip if cropping fails
- Log failures for debugging

**Recovery:**
- Collect failing examples
- Investigate PyMuPDF coordinate systems
- Add PDF type detection and adaptive cropping
- Document known limitations

**Detection:** Task 6 (re-OCR testing), Task 12 (integration tests)

---

### Minor Risks

#### Dictionary Learning Over-Permissive 🧠 LOW IMPACT
**Scenario:** Adaptive dictionary learns OCR errors as valid words

**Mitigation:** Frequency thresholds, morphological validation, confidence scoring
**Detection:** Task 11 (unit tests for learning safeguards)

#### Block Filtering Too Aggressive 🧱 LOW IMPACT
**Scenario:** Block-based line-break detection misses valid hyphenations

**Mitigation:** Test on diverse documents, collect edge cases
**Detection:** Task 11 (unit tests), Task 12 (validation set)

#### Scholarly Term Filtering Incomplete 📚 LOW IMPACT
**Scenario:** German/Latin terms still flagged as errors (false positives)

**Mitigation:** Acceptable 23.4% FP rate for Phase 1, expand term list later
**Detection:** Task 12 (false positive rate measurement)

---

## Success Criteria

### Functional Success ✅
- [ ] All 6 OCR components implemented (dictionary, linebreak, detector, reocr, pipeline, integration)
- [ ] All components have unit tests with ≥80% coverage
- [ ] Integration test passes with validation set (130 error pairs + 77 correct words)
- [ ] Detection rate ≥99% (matches spike: 129/130 errors caught)
- [ ] False positive rate ≤25% (matches spike: 18/77 correct words flagged)
- [ ] All 288 existing tests still pass (no regressions)
- [ ] OCR disabled by default (backward compatible)
- [ ] Graceful degradation with missing optional dependencies

### Performance Success ⚡
- [ ] Clean pages: <50ms overhead (detect clean, skip re-OCR)
- [ ] Dirty pages with Tesseract (CPU): <1.5s per page average
- [ ] Dirty pages with docTR (GPU): <0.5s per page average
- [ ] Memory usage: <200MB additional for OCR pipeline
- [ ] No performance regression on non-OCR code paths

### Quality Success 🎯
- [ ] Type hints on all public APIs
- [ ] Docstrings on all classes and public methods
- [ ] Ruff linting passes with no errors
- [ ] Ruff formatting applied consistently
- [ ] Test coverage ≥80% for new OCR code
- [ ] No security vulnerabilities introduced
- [ ] Code review approved before merge

### Integration Success 🔗
- [ ] convert.py accepts OCRConfig parameter
- [ ] ScholarDocument contains OCR metadata when enabled
- [ ] Clear error messages for missing dependencies
- [ ] Installation documentation updated
- [ ] Usage examples in docstrings
- [ ] ADRs referenced in code comments

### Documentation Success 📚
- [ ] ROADMAP.md updated (Phase 1 complete)
- [ ] README.md mentions OCR capabilities
- [ ] Optional dependencies documented
- [ ] Usage examples clear and tested
- [ ] Known limitations documented

---

## Testing Strategy

### Unit Testing Approach
**One test file per component:**
- `tests/ocr/test_dictionary.py` → AdaptiveDictionary
- `tests/ocr/test_linebreak.py` → LineBreakRejoiner
- `tests/ocr/test_detector.py` → OCRErrorDetector
- `tests/ocr/test_reocr.py` → Hybrid re-OCR engine
- `tests/ocr/test_pipeline.py` → OCRPipeline orchestrator
- `tests/ocr/test_models.py` → OCR data models

**Test each component immediately after porting (TDD):**
1. Port component from spike
2. Write unit tests
3. Run tests (ensure passing)
4. Move to next component

**Mock external dependencies:**
- Mock pytesseract.image_to_string()
- Mock doctr DocumentBuilder
- Mock torch.cuda.is_available()
- Fast tests (<5s total)

### Integration Testing Approach
**Use full validation set:**
- Load `ground_truth/validation_set.json`
- 130 OCR error pairs (should be detected)
- 77 correct words (should NOT be flagged, or acceptable FP rate)

**End-to-end testing:**
```python
def test_full_pipeline_on_validation_set():
    validation_set = load_validation_set()

    # Test detection
    detected = ocr_pipeline.detect_errors(validation_set.ocr_text)
    detection_rate = len(detected) / len(validation_set.errors)
    assert detection_rate >= 0.99, f"Detection rate {detection_rate:.1%} below target 99%"

    # Test false positives
    flagged_correct = ocr_pipeline.detect_errors(validation_set.correct_words)
    fp_rate = len(flagged_correct) / len(validation_set.correct_words)
    assert fp_rate <= 0.25, f"FP rate {fp_rate:.1%} above target 25%"

    # Test corrections
    corrected = ocr_pipeline.correct(validation_set.ocr_text)
    # Compare to ground truth...
```

**Regression testing:**
- Run all 288 existing tests after every change
- Ensure OCR disabled by default doesn't break anything
- Test with OCR enabled on existing test PDFs

### Performance Testing Approach
**Benchmark on validation set:**
```python
def test_performance():
    # Clean pages (should skip re-OCR)
    start = time.time()
    ocr_pipeline.process_page(clean_page)
    assert time.time() - start < 0.05, "Clean page overhead too high"

    # Dirty pages with Tesseract (CPU)
    start = time.time()
    ocr_pipeline.process_page(dirty_page, engine="tesseract")
    assert time.time() - start < 1.5, "Tesseract too slow"

    # Dirty pages with docTR (GPU, if available)
    if torch.cuda.is_available():
        start = time.time()
        ocr_pipeline.process_page(dirty_page, engine="doctr")
        assert time.time() - start < 0.5, "docTR GPU too slow"
```

**Memory profiling:**
- Use memory_profiler or tracemalloc
- Ensure <200MB additional memory for OCR pipeline

### Test Data Organization
```
ground_truth/
├── validation_set.json          # 130 error pairs + 77 correct words (USE THIS)
├── ocr_errors/
│   ├── ocr_error_pairs.json     # Subset of validation_set
│   ├── validated_samples.json
│   └── challenging_samples.json
└── ocr_quality/
    └── classified/              # 172 pages, 17k evidence entries
```

**CRITICAL:** Use the FULL validation_set.json (130 pairs), not just ocr_error_pairs.json (30 pairs).

---

## Timeline & Milestones

### Session Breakdown (8-10 hours total)

**Milestone 1: Foundation + Risk Validation (2-3 hours)**
- [ ] Task 3: Port dictionary.py (30-40 min)
- [ ] Task 6: Port reocr.py (90-120 min)
- [ ] Unit tests for both (30 min)
- **Checkpoint:** Highest-risk component validated

**Milestone 2: Component Implementation (2-3 hours)**
- [ ] Task 4: Port linebreak.py (45-60 min)
- [ ] Task 5: Port detector.py (45-60 min)
- [ ] Task 7: Port pipeline.py (60-90 min)
- [ ] Unit tests for all (30 min)
- **Checkpoint:** All OCR components complete

**Milestone 3: Integration (2 hours)**
- [ ] Task 8: Add OCR models (30 min)
- [ ] Task 10: Add config support (30 min)
- [ ] Task 9: Integrate into convert() (60 min)
- **Checkpoint:** End-to-end flow working

**Milestone 4: Testing & Validation (2-3 hours)**
- [ ] Task 11: Unit tests (60 min)
- [ ] Task 12: Integration tests (45 min)
- [ ] Task 13: Performance tests (15 min)
- [ ] Fix any issues discovered (30-60 min buffer)
- **Checkpoint:** All tests passing

**Milestone 5: Documentation & Wrap-up (15-30 min)**
- [ ] Task 14: Update docs (15 min)
- [ ] Final commit and PR preparation (15 min)
- **Checkpoint:** Ready for review

### Flexible Pacing
- **Fast track:** ~8 hours (experienced, no blockers)
- **Standard:** ~9 hours (moderate complexity)
- **Conservative:** ~10 hours (includes debugging time)

### Session Options
**Option A: Single Long Session (8-10 hours)**
- Complete all tasks in one sitting
- Maintains context, minimal ramp-up time
- Requires sustained focus

**Option B: Two Medium Sessions (4-5 hours each)**
- Session 1: Milestones 1-2 (foundation + components)
- Session 2: Milestones 3-5 (integration + testing)
- Natural break point after component implementation

**Option C: Three Short Sessions (3 hours each)**
- Session 1: Milestone 1 (foundation + risk)
- Session 2: Milestones 2-3 (components + integration)
- Session 3: Milestones 4-5 (testing + docs)
- More flexible scheduling, but more context-switching

---

## Rollback Plan

### If Task 6 (reocr.py) Fails
**Scenario:** Can't get hybrid re-OCR working reliably (GPU detection, fallback chain, performance)

**Options:**
1. **Simplify to Tesseract-only:** Remove GPU path, use single-engine fallback
2. **Defer to Phase 2:** Complete other components, mark re-OCR as TODO
3. **Use spike code as-is:** Port spike without production improvements, revisit later

**Decision Criteria:**
- If 2+ hours debugging with no progress → simplify or defer
- If Tesseract-only works → acceptable for Phase 1
- If nothing works → serious problem, may need architecture rethink

---

### If Integration (Task 9) Breaks Existing Tests
**Scenario:** convert.py changes cause regressions in 288 existing tests

**Options:**
1. **Feature flag disabled by default:** Keep OCR code but don't enable by default
2. **Isolate OCR code path:** Ensure zero impact when OCR disabled
3. **Revert and debug:** Roll back integration, fix in isolation, re-integrate

**Decision Criteria:**
- If <5 tests failing → debug and fix
- If 5-20 tests failing → isolate OCR code path better
- If >20 tests failing → revert and rethink integration strategy

---

### If Performance Targets Missed
**Scenario:** Re-OCR takes >2s per page on CPU (unacceptable for users)

**Options:**
1. **Accept for Phase 1:** Document as known limitation, defer optimization
2. **Optimize hot paths:** Profile and optimize critical code
3. **Reduce re-OCR scope:** Only correct high-confidence errors, skip marginal cases

**Decision Criteria:**
- If 1.5-2s → acceptable for Phase 1, document
- If 2-3s → optimize before merge
- If >3s → reduce scope or defer feature

---

### If Detection Rate Drops Below 95%
**Scenario:** Ported code doesn't match spike performance (99.2% → <95%)

**Options:**
1. **Debug discrepancy:** Compare ported code to spike, find regression
2. **Re-validate spike:** Ensure spike results were correct
3. **Accept lower rate:** If 95% is acceptable, document and proceed

**Decision Criteria:**
- If 95-99% → debug for 1 hour, if no fix → accept and document
- If 90-95% → must debug and fix before merge
- If <90% → serious problem, halt and investigate

---

## Code Quality Checklist

Apply to EVERY component:

### Before Committing
- [ ] Type hints on all public methods
- [ ] Docstrings on classes and public methods
- [ ] Error handling for edge cases
- [ ] Logging instead of print statements
- [ ] No hardcoded paths or magic numbers
- [ ] Ruff formatting applied (`uv run ruff format .`)
- [ ] Ruff linting passes (`uv run ruff check .`)
- [ ] Unit tests written and passing
- [ ] No security vulnerabilities (no eval, exec, unsafe pickle)

### Code Review Checklist
- [ ] Preserves spike algorithm logic (don't "improve" validated code)
- [ ] Proper error messages (helpful to users)
- [ ] Performance considerations (no O(n²) in hot paths)
- [ ] Memory efficiency (no unnecessary copies)
- [ ] Testability (dependency injection, mockable)
- [ ] Documentation clarity (examples, edge cases)

---

## Reference Materials

### Spike Code
- **Primary source:** `spikes/29_ocr_pipeline_design.py` (588 lines)
- **Validation framework:** `spikes/30_validation_framework.py`

### Ground Truth Data
- **Validation set:** `ground_truth/validation_set.json` (130 pairs, 77 correct)
- **OCR errors:** `ground_truth/ocr_errors/` (verified samples)

### Architecture Decisions
- **ADR-002:** OCR pipeline architecture (spellcheck as selector)
- **ADR-003:** Line-break detection (block-based filtering)

### Memories
- **ocr_pipeline_architecture:** Pipeline design and validation
- **session_handoff:** Previous session context
- **decision_log:** Architectural decisions made

### Documentation
- **REQUIREMENTS.md:** User stories and acceptance criteria
- **SPEC.md:** Technical specification (DRAFT sections noted)
- **ROADMAP.md:** Phased development plan
- **CLAUDE.md:** Project guidelines and automation

---

## Next Steps

### Immediate Actions
1. **Review this plan** with agents (plan-reviewer, code-reviewer)
2. **Get user approval** for sequencing and approach
3. **Create TodoWrite tracker** for all 12 tasks
4. **Begin Task 3** (dictionary.py) - foundation

### Post-Implementation
1. **Create PR** with comprehensive description
2. **Request code review** from maintainers
3. **Update session_handoff** memory with outcomes
4. **Update decision_log** with lessons learned

---

## Open Questions

### Pre-Implementation
- [ ] **Session length preference?** Single long session (8-10hr) vs multiple shorter sessions?
- [ ] **GPU testing availability?** Can we test GPU path, or CPU-only for now?
- [ ] **Performance acceptable?** If CPU takes 1.5-2s per dirty page, is that OK for Phase 1?

### During Implementation
- [ ] **Re-OCR quality threshold:** What confidence score to require before replacing text?
- [ ] **Scholarly term list:** Should we expand German/French/Latin filtering?
- [ ] **Learning safeguards:** Current frequency threshold OK, or make configurable?

### Post-Implementation
- [ ] **Default OCR setting:** Keep disabled for Phase 1, or enable with conservative config?
- [ ] **GPU in CI:** Worth setting up GPU runner, or manual GPU testing only?
- [ ] **Performance benchmarking:** Add to CI, or manual validation only?

---

**Plan Status:** DRAFT - Awaiting agent review and user approval
**Next Action:** Launch plan-reviewer and code-reviewer agents for validation
