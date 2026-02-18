# External Integrations

**Analysis Date:** 2026-01-28

## APIs & External Services

**None detected**
- ScholarDoc is a standalone library with no external API dependencies
- All processing happens locally using installed libraries
- No cloud services, API keys, or network calls required

## Data Storage

**Databases:**
- SQLite (planned) - `.scholardb` persistence format
  - Status: Mentioned in Serena memory context, implementation not found in codebase
  - Purpose: Structured storage for ScholarDocument objects

**File Storage:**
- Local filesystem only
  - Input: PDF files from local paths
  - Output: JSON (`.scholardoc`), Markdown, plain text
  - Location: `scholardoc/models.py` (save/load methods on ScholarDocument)

**Caching:**
- In-memory only
  - Page position cache: `scholardoc/readers/pdf_reader.py:95-124` (RawDocument._text_cache, _page_positions)
  - No persistent cache layer

## Authentication & Identity

**Auth Provider:**
- Not applicable (library, not application)

## Monitoring & Observability

**Error Tracking:**
- None (library delegates to consumer application)

**Logs:**
- Python logging module
  - Loggers: `scholardoc.ocr.reocr`, `scholardoc.ocr.dictionary`, `scholardoc.normalizers.ocr_pipeline`
  - Consumer controls log level and handlers

## PDF Processing

**PyMuPDF (fitz):**
- Purpose: Core PDF extraction engine
- Version: 1.24.0+
- Integration points:
  - Text extraction: `scholardoc/readers/pdf_reader.py:18` (`import fitz`)
  - Page rendering: `scholardoc/ocr/reocr.py:276-291` (render_page_to_image)
  - Font/layout analysis: `scholardoc/readers/pdf_reader.py:251-292` (_extract_blocks)
  - Outline extraction: `scholardoc/readers/pdf_reader.py:338-357` (_extract_outline)
  - Metadata extraction: `scholardoc/readers/pdf_reader.py:359-370` (_extract_metadata)
- Features used:
  - get_text("dict") for detailed extraction
  - get_text("text") for plain text
  - get_toc() for outline/bookmarks
  - get_pixmap() for image rendering
  - get_images() for image detection
- Configuration: DPI-based rendering (default 300 DPI per `scholardoc/ocr/reocr.py:40`)

## OCR Engines

**Hybrid Re-OCR Architecture:**
- 4-tier fallback strategy (ADR-002: spellcheck as selector, not corrector)
- Implementation: `scholardoc/ocr/reocr.py:198-551` (HybridReOCREngine)

**Tier 1: docTR (GPU):**
- Package: `python-doctr>=0.6.0` (optional, ocr-gpu extra)
- Dependencies: PyTorch 2.0.0+, torchvision 0.15.0+, CUDA 11.8
- Performance: ~0.45s/page
- Integration: `scholardoc/ocr/reocr.py:260-274` (_get_doctr_predictor)
- Detection: `scholardoc/ocr/reocr.py:61-72` (_check_gpu_available)
- Model: Pre-trained OCR predictor from docTR
- Device selection: Auto-detects CUDA availability

**Tier 2: Tesseract (CPU):**
- Package: `pytesseract>=0.3.10` (optional, ocr extra)
- Binary requirement: Tesseract OCR installed on system
- Performance: ~1.35s/page
- Integration: `scholardoc/ocr/reocr.py:330-362` (_reocr_with_tesseract)
- Detection: `scholardoc/ocr/reocr.py:86-99` (_check_tesseract_available)
- Language: English (configurable via lang="eng" parameter)
- Output: Confidence scores per word

**Tier 3: docTR (CPU):**
- Same package as Tier 1, CPU fallback mode
- Performance: ~4.5s/page
- Integration: `scholardoc/ocr/reocr.py:364-404` (_reocr_with_doctr)

**Tier 4: Skip Re-OCR:**
- Graceful degradation when no OCR engine available
- Returns original text unchanged

**Engine Selection:**
- Auto-detection: `scholardoc/ocr/reocr.py:102-132` (detect_available_engines)
- Priority order: GPU → Tesseract → CPU → None
- Override via `preferred_engine` parameter

## Spellcheck Libraries

**pyspellchecker:**
- Package: `pyspellchecker>=0.8.4` (required core dependency)
- Purpose: OCR error detection (not correction per ADR-002)
- Integration: `scholardoc/ocr/dictionary.py:22-23` (SpellChecker import)
- Usage pattern:
  - Flag suspicious words for re-OCR
  - Hybrid validation with morphological analysis
  - Adaptive dictionary learning with safeguards
- Location: `scholardoc/ocr/dictionary.py` (AdaptiveDictionary class)
- Languages: English default, multilingual support via language parameter
- Supported languages: Listed in `scholardoc/normalizers/ocr_correction.py:639`

**Contextual Correction (Optional):**
- Package: `ocrfixr>=1.5.0` (optional, contextual extra)
- Purpose: BERT-based contextual OCR correction
- Status: Declared in dependencies, integration not found in current codebase
- Intended use: Phase 2+ enhancement

## UI Framework

**Streamlit:**
- Package: `streamlit>=1.30.0` (optional, ground-truth extra)
- Purpose: Ground truth annotation UI
- Location: `ground_truth/scripts/annotate_ui.py`
- Features used:
  - st_ace (Ace editor widget) for YAML editing
  - Image display for PDF page rendering
  - Session state management
- Integration points:
  - YAML validation: `ground_truth/scripts/validate.py`
  - PDF visualization: `ground_truth/scripts/visualize.py`
  - Region rendering with PIL: Uses Pillow for image manipulation
- Run command: `streamlit run ground_truth/scripts/annotate_ui.py`

**streamlit-ace:**
- Package: `streamlit-ace>=0.1.0` (optional, ground-truth extra)
- Purpose: Syntax-highlighted YAML editor in annotation UI
- Integration: `ground_truth/scripts/annotate_ui.py:21`

## Evaluation & Testing

**Fuzzy Matching:**
- Package: `rapidfuzz>=3.0.0` (optional, ground-truth extra)
- Purpose: String similarity for ground truth evaluation
- Location: `ground_truth/lib/matching.py` (inferred from evaluation system)

**Tabular Output:**
- Package: `tabulate>=0.9.0` (optional, ground-truth extra)
- Purpose: Formatted output for evaluation reports
- Location: `ground_truth/lib/reports.py` (inferred from evaluation system)

**Data Format:**
- Package: `pyyaml>=6.0.0` (optional, ground-truth extra)
- Purpose: Ground truth annotation file format
- Integration: `ground_truth/scripts/annotate_ui.py:20` (yaml import)
- File location: `ground_truth/documents/` directory

## Language Detection (Optional)

**langdetect:**
- Package: `langdetect>=1.0.9` (optional, multilingual extra)
- Purpose: Automatic language detection for multilingual PDFs
- Implementation: Not found in current codebase (Phase 2+ feature)

**wordfreq:**
- Package: `wordfreq>=3.0.0` (optional, multilingual extra)
- Purpose: Word frequency data for 40+ languages
- Use case: Enhanced dictionary validation for non-English texts
- Implementation: Not found in current codebase (Phase 2+ feature)

## CI/CD & Deployment

**Hosting:**
- Not applicable (library package, not deployed application)

**CI Pipeline:**
- None detected (no .github/workflows, .gitlab-ci.yml, or similar)

**Build System:**
- hatchling (PEP 517 build backend)
- Configuration: `pyproject.toml:101-106` ([build-system] section)

## Environment Configuration

**Required env vars:**
- None (configuration via Python code)

**Secrets location:**
- Not applicable (no external services requiring authentication)

**Optional configuration:**
- OCR engine preference: Set via code (`HybridReOCREngine.preferred_engine`)
- PyTorch CUDA index: Set in `pyproject.toml:109-111` ([tool.uv] section)

## Webhooks & Callbacks

**Incoming:**
- None (library with no server component)

**Outgoing:**
- None (no external service integrations)

---

*Integration audit: 2026-01-28*
