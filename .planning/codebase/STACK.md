# Technology Stack

**Analysis Date:** 2026-01-28

## Languages

**Primary:**
- Python 3.11+ - Core implementation language
- Supports Python 3.12 (declared in `pyproject.toml` classifiers)

**Secondary:**
- None - Pure Python implementation

## Runtime

**Environment:**
- Python 3.11+ runtime
- No specific version pinning detected (uses system Python or uv-managed version)

**Package Manager:**
- uv (modern Python package manager)
- Lockfile: `uv.lock` present at project root
- pip-compatible fallback via pyproject.toml

## Frameworks

**Core:**
- PyMuPDF (fitz) 1.24.0+ - PDF text extraction and layout analysis
  - ADR-001: Chosen for 32-57x speed advantage over alternatives
  - Provides font info, positions, outline extraction
- Pydantic (implicit via models) - Data validation and serialization
- Pillow 11.3.0+ - Image processing for OCR pipeline

**Testing:**
- pytest 8.0.0+ - Test runner
- pytest-cov 4.1.0+ - Coverage reporting
- hypothesis 6.100.0+ - Property-based testing

**Build/Dev:**
- hatchling - Build backend (PEP 517)
- ruff 0.4.0+ - Linting and formatting (replaces black, isort, flake8)
- uv - Dependency resolution and environment management

## Key Dependencies

**Critical:**
- `pymupdf>=1.24.0` - Core PDF extraction engine
  - Rationale: Speed (32-57x faster than pypdf/pdfplumber per ADR-001)
  - Features: Text blocks with positions, fonts, outline, metadata
  - Location: `scholardoc/readers/pdf_reader.py`

- `pyspellchecker>=0.8.4` - Dictionary-based OCR error detection
  - Role: Flags suspicious words for re-OCR (selector, not corrector per ADR-002)
  - Location: `scholardoc/ocr/dictionary.py`, `scholardoc/normalizers/ocr_pipeline.py`

- `pillow>=11.3.0` - Image operations for OCR
  - Role: PDF page rendering, line cropping for re-OCR
  - Location: `scholardoc/ocr/reocr.py`, `scholardoc/ocr/pipeline.py`

**Optional (OCR Engines):**
- `pytesseract>=0.3.10` - CPU-based OCR (ocr extra)
  - Tier 2 fallback in hybrid re-OCR engine
  - Performance: ~1.35s/page per `scholardoc/ocr/reocr.py:7`

- `python-doctr>=0.6.0` - Neural OCR with GPU support (ocr-gpu extra)
  - Requires torch 2.0.0+, torchvision 0.15.0+
  - Tier 1 (GPU) or Tier 3 (CPU) in hybrid re-OCR engine
  - Performance: ~0.45s/page GPU, ~4.5s/page CPU per `scholardoc/ocr/reocr.py:7-8`

- `ocrfixr>=1.5.0` - Contextual OCR correction with BERT (contextual extra)

**Infrastructure:**
- `pymupdf4llm>=0.0.10` - Enhanced layout analysis (enhanced extra, Phase 2+)
- `streamlit>=1.30.0` - Ground truth annotation UI (ground-truth extra)
  - Location: `ground_truth/scripts/annotate_ui.py`
- `rapidfuzz>=3.0.0` - Fuzzy string matching for evaluation (ground-truth extra)
- `pyyaml>=6.0.0` - Ground truth data format (ground-truth extra)

**Multilingual Support (Optional):**
- `langdetect>=1.0.9` - Language detection (multilingual extra)
- `wordfreq>=3.0.0` - Word frequency data for 40+ languages (multilingual extra)

## Configuration

**Environment:**
- No .env file detected
- Configuration via code: `scholardoc/config.py` (ConversionConfig dataclass)
- OCR engine selection: Auto-detection with fallback chain (docTR GPU → Tesseract → docTR CPU)

**Build:**
- `pyproject.toml` - PEP 517/518 build config
- `[tool.uv]` - PyTorch CUDA 11.8 index for GPU support (GTX 1080 Ti / sm_61 compatible)
- `[tool.ruff]` - Linter config (target Python 3.11, 100 char line length)
- `[tool.pytest.ini_options]` - Test runner config

## Platform Requirements

**Development:**
- Python 3.11+ runtime
- uv package manager (recommended) or pip
- Optional: CUDA 11.8 for GPU-accelerated OCR (GTX 1080 Ti tested)
- Optional: Tesseract OCR binary for CPU re-OCR

**Production:**
- Python 3.11+ runtime
- Linux/macOS/Windows (cross-platform via PyMuPDF)
- Optional: GPU with CUDA 11.8 for high-volume OCR correction
- Deployment target: Not specified (library package, not application)

---

*Stack analysis: 2026-01-28*
