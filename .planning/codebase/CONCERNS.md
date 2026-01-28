# Codebase Concerns

**Analysis Date:** 2026-01-28

## Tech Debt

**Writers Module - Incomplete Implementation:**
- Issue: Module exists but contains only stub - no markdown, JSON, or other output writers implemented
- Files: `scholardoc/writers/__init__.py` (2 lines: stub comment only)
- Impact: Cannot export ScholarDocument to any format despite complete data model
- Fix approach: Implement MarkdownWriter and JSONWriter as specified in `SPEC.md` lines 90-95
- Priority: HIGH - Blocks end-to-end usage

**Utils Module - Empty Placeholder:**
- Issue: Module exists but completely empty except stub comment
- Files: `scholardoc/utils/__init__.py` (2 lines: stub comment only)
- Impact: Low - no utils functionality currently specified
- Fix approach: Remove or populate based on actual need during Phase 2+
- Priority: LOW - Cleanup item

**Parallel Processing Stubbed:**
- Issue: `convert_batch()` function accepts `parallel=True` parameter but implementation is sequential only
- Files: `scholardoc/convert.py:441` (TODO comment), `SPEC.md:310-323`
- Impact: Processing large corpora is slower than advertised
- Fix approach: Implement parallel processing with ProcessPoolExecutor or defer to Phase 2
- Priority: MEDIUM - Performance optimization, not correctness issue

**Language Detection Hardcoded:**
- Issue: OCR correction always uses `language="en"`, no actual language detection
- Files: `scholardoc/convert.py:333` (TODO comment)
- Impact: Suboptimal spell-checking for non-English philosophical texts (German, French, Latin)
- Fix approach: Integrate langdetect (already in pyproject.toml optional deps) or use PDF metadata
- Priority: MEDIUM - Affects quality on multilingual corpus

**Exception Classes Empty:**
- Issue: Custom exception classes defined but have no custom behavior beyond inheritance
- Files: `scholardoc/exceptions.py:24,36,47,59` (all `pass` statements)
- Impact: None - acceptable pattern for exception hierarchies
- Fix approach: No action needed unless custom attributes required
- Priority: NONE - Not a concern

## Known Bugs

**OCR Pipeline False Positive Rate:**
- Symptoms: 23.4% of correctly-spelled words flagged as errors (mostly German philosophical terms)
- Files: `scholardoc/ocr/detector.py`, `scholardoc/normalizers/ocr_correction.py`
- Trigger: Processing German/French/Latin philosophical texts (Dasein, Augenblick, differance, etc.)
- Workaround: Use AdaptiveDictionary learning (already implemented), but requires frequency threshold
- Impact: Wastes compute re-OCRing correct words, but doesn't corrupt output (acceptable per ADR-002)
- Evidence: `docs/adr/ADR-002-ocr-pipeline-architecture.md:169,187`

**Missing Validation Set Documents:**
- Symptoms: No verified ground truth documents exist in `ground_truth/documents/` (only 1 sample YAML)
- Files: `ground_truth/documents/` contains only `derrida_footnotes_sample.yaml`
- Trigger: Running evaluation scripts against full corpus
- Impact: Cannot validate extraction accuracy despite having evaluation framework
- Priority: HIGH - Blocks regression testing and quality validation

## Security Considerations

**File Path Injection:**
- Risk: `convert()` accepts user-provided file paths without explicit validation
- Files: `scholardoc/convert.py:384-389`
- Current mitigation: Python FileNotFoundError on invalid paths, PyMuPDF will reject non-PDF files
- Recommendations: Add explicit path traversal checks if exposing as web API
- Priority: LOW for library, HIGH if exposing HTTP endpoint

**No Input Size Limits:**
- Risk: Malicious PDFs with thousands of pages or embedded bombs could exhaust memory
- Files: `scholardoc/readers/pdf_reader.py:189-194`
- Current mitigation: None
- Recommendations: Add configurable page count limit, memory usage monitoring
- Priority: MEDIUM - Add to ConversionConfig in Phase 2

## Performance Bottlenecks

**Sequential OCR Re-Processing:**
- Problem: Pages processed one at a time, no batch re-OCR optimization
- Files: `scholardoc/ocr/pipeline.py`, `scholardoc/ocr/reocr.py`
- Cause: Pipeline design processes per-page, neural models not batched
- Improvement path: Batch lines for re-OCR across pages (5-10x speedup potential)
- Impact: Significant on large corpora (1000+ page books)
- Priority: Phase 2 optimization

**Large File Complexity:**
- Problem: Two files exceed 1500 lines, indicating potential complexity
- Files:
  - `scholardoc/normalizers/ocr_correction.py` (1,764 lines)
  - `scholardoc/models.py` (1,524 lines)
- Cause: Comprehensive data models (models.py), extensive OCR pattern matching (ocr_correction.py)
- Improvement path: Consider splitting ocr_correction.py into pattern matching + correction modules
- Priority: LOW - Complexity acceptable for domain logic, but monitor for future refactor

## Fragile Areas

**OCR Dictionary Persistence:**
- Files: `scholardoc/ocr/dictionary.py`, `scholardoc/ocr/pipeline.py:89,703`
- Why fragile: AdaptiveDictionary learns words during processing, persistence controlled by flag
- Safe modification: Always test with `persist_dictionary=False` first to avoid corrupting learned vocabulary
- Test coverage: Unit tests exist but integration tests for persistence missing
- Priority: MEDIUM - Add integration test for dictionary save/load cycle

**Spike Code Integration Gap:**
- Files: 35 spike files in `spikes/` directory, 23 production files in `scholardoc/`
- Why fragile: Spikes explored solutions but integration status unclear for some (e.g., ToC parsing, profile detection)
- Safe modification: Check `spikes/FINDINGS.md` and `ROADMAP.md` before reimplementing spike logic
- Test coverage: Spikes have minimal tests (only 10 test function definitions across all spikes)
- Priority: MEDIUM - Document which spikes are integrated, archive the rest

**Ground Truth Evaluation Framework Incomplete:**
- Files: `ground_truth/lib/` (matching, metrics, normalize, reports), `ground_truth/scripts/`
- Why fragile: Complete evaluation library exists but only 1 sample ground truth document
- Safe modification: Validation and evaluation scripts are ready but untested on real corpus
- Test coverage: Scripts exist but cannot run meaningful tests without ground truth data
- Priority: HIGH - Populate `ground_truth/documents/` before claiming validation capability

## Scaling Limits

**Memory Usage - Full Document Load:**
- Current capacity: Entire PDF text loaded into memory as single string
- Limit: Files >1GB PDF (~10,000+ page academic compilations) may exhaust 16GB RAM
- Scaling path: Implement streaming/chunked processing in Phase 3
- Impact: Low - Target corpus is individual books (<500 pages typical)
- Priority: LOW - Document limitation, defer to Phase 3+

**Dictionary Growth Unbounded:**
- Current capacity: AdaptiveDictionary grows indefinitely with learned words
- Limit: Processing 10,000+ documents could create multi-MB dictionary files
- Scaling path: Add LRU eviction policy or frequency-based pruning
- Impact: Disk storage grows, load time increases
- Priority: LOW - Monitor in production, optimize if >100MB dictionaries seen

## Dependencies at Risk

**PySpellChecker Limitations:**
- Risk: Limited multilingual support, no philosophical vocabulary by default
- Impact: High false positive rate on specialized terminology (already observed)
- Migration plan: Consider `pyenchant` (more dictionaries) or `SymSpell` (faster) in Phase 2
- Priority: MEDIUM - Current solution works but monitoring needed

**Optional Dependency Complexity:**
- Risk: 8 optional dependency groups (`ocr`, `ocr-gpu`, `contextual`, `multilingual`, etc.)
- Impact: User confusion about which extras to install, testing matrix explosion
- Migration plan: Simplify to 3 groups: `core`, `full`, `dev` in v0.2.0
- Priority: LOW - Document clearly in Phase 1, restructure later

**OCRfixr Keras Compatibility:**
- Risk: OCRfixr has known Keras 3 compatibility issues (caught in exception handler)
- Impact: Contextual correction unavailable on newer TensorFlow/Keras
- Migration plan: Wait for OCRfixr update or replace with direct transformers usage
- Files: `scholardoc/normalizers/ocr_correction.py:30-34`
- Priority: LOW - Optional feature, documented in code

## Missing Critical Features

**No Output Writers:**
- Problem: Cannot export ScholarDocument to any format (Markdown, JSON, etc.)
- Blocks: End-to-end usage, integration testing, user adoption
- Files: `scholardoc/writers/` module empty
- Priority: CRITICAL - Phase 1 incomplete without this

**No Persistence Layer:**
- Problem: ScholarDocument has no save/load methods despite ADR mentioning "dual persistence"
- Blocks: Caching extracted documents, incremental processing
- Evidence: `QUESTIONS.md` mentions "Dual persistence (JSON + SQLite)" but no implementation found
- Priority: HIGH - Needed for Phase 2 batch processing

**No CLI Interface:**
- Problem: Library-only, no command-line tool for batch conversion
- Blocks: Non-Python users, shell script integration, CI/CD pipelines
- Priority: MEDIUM - Common for document processing tools, defer to Phase 2

**Ground Truth Documents Missing:**
- Problem: Evaluation framework complete but no verified ground truth exists
- Blocks: Regression testing, quality validation, benchmark claims
- Files: Only `ground_truth/documents/derrida_footnotes_sample.yaml` exists
- Priority: HIGH - Cannot validate "99.2% detection rate" claims without this

## Test Coverage Gaps

**Writers Module Untested:**
- What's not tested: All writer functionality (0 tests because module empty)
- Files: No test files for writers
- Risk: When implemented, no tests will catch regressions
- Priority: HIGH - Add tests before implementing writers

**OCR Pipeline Integration Tests Missing:**
- What's not tested: Full pipeline on real PDFs with verification
- Files: `tests/unit/test_ocr_pipeline.py` has 20 skipped tests (pyspellchecker not installed check)
- Risk: Unit tests exist but integration with real documents untested
- Priority: MEDIUM - Add end-to-end OCR test with known good/bad pages

**Ground Truth Evaluation Untested:**
- What's not tested: Evaluation library never run against real ground truth
- Files: `ground_truth/lib/*.py` - no test files found
- Risk: Metric calculations may have bugs, matching logic unverified
- Priority: HIGH - Cannot trust evaluation results without tests

**Spike Code Validation Gap:**
- What's not tested: 35 spike exploration scripts have minimal testing (10 test definitions total)
- Files: All files in `spikes/` directory
- Risk: Spikes validated design but findings not regression-tested
- Priority: LOW - Spikes are research artifacts, not production code

**Optional Dependencies Conditional:**
- What's not tested: Code paths when optional deps missing (e.g., wordfreq, ocrfixr)
- Files: Multiple modules have try/except ImportError blocks
- Risk: Fallback paths may be broken
- Priority: MEDIUM - Add CI matrix testing without optional deps

## Documentation vs Reality Gaps

**SPEC.md Shows Unimplemented Features:**
- Issue: Specification describes complete architecture including writers, normalizers, batch processing
- Reality: Writers empty, batch processing sequential only, some normalizers missing
- Files: `SPEC.md:54-95` vs actual `scholardoc/` implementation
- Impact: User expectations vs actual capabilities mismatch
- Fix: Add "Phase 1 Status" markers in SPEC.md indicating what's implemented
- Priority: HIGH - Documentation debt

**ROADMAP.md Says Phase 1 Complete:**
- Issue: "Phase 1 ✅ DONE" but writers module empty, ground truth missing
- Reality: Core extraction works, OCR pipeline integrated, but no output format
- Files: `ROADMAP.md:3,21` claims complete
- Impact: Misleading status reporting
- Fix: Mark Phase 1 as "Core Implementation Complete - Writers Pending"
- Priority: HIGH - Accurate status needed

**QUESTIONS.md References Dual Persistence:**
- Issue: Multiple references to "Dual persistence (JSON + SQLite) decided but implementation status unclear"
- Reality: No persistence code found in codebase
- Files: ADR or design doc for persistence decision missing
- Impact: Decision documented but never implemented
- Fix: Either implement or mark as Phase 2 feature
- Priority: MEDIUM - Clarify intent

**ADR-002 Claims 99.2% Detection Rate:**
- Issue: Validated on 130 error pairs, but no regression test suite exists
- Reality: One-time spike validation, no ongoing verification
- Files: `docs/adr/ADR-002-ocr-pipeline-architecture.md:163,186`
- Impact: Cannot verify claim holds after code changes
- Fix: Add regression test with validation set
- Priority: HIGH - Scientific claims need reproducibility

## Recommended Priorities

**P0 - Blocks Release:**
1. Implement MarkdownWriter in `scholardoc/writers/` (SPEC.md lines 90-95)
2. Implement JSONWriter for ScholarDocument serialization
3. Add end-to-end test: PDF → ScholarDocument → Markdown output
4. Update ROADMAP.md status to reflect writers completion

**P1 - Quality Foundation:**
1. Populate `ground_truth/documents/` with 5-10 verified test documents
2. Add regression test suite using ground truth validation set
3. Create integration test for OCR pipeline with known error corpus
4. Document which spikes are integrated vs. archived

**P2 - Technical Debt Cleanup:**
1. Add language detection or document hardcoded English assumption
2. Split `scholardoc/normalizers/ocr_correction.py` if complexity grows beyond 2000 lines
3. Simplify optional dependency groups in `pyproject.toml`
4. Add CLI interface for common operations

**P3 - Future Optimization:**
1. Implement batch OCR re-processing for performance
2. Add parallel processing for `convert_batch()`
3. Implement dictionary pruning for unbounded growth
4. Add memory usage monitoring and limits

---

*Concerns audit: 2026-01-28*
