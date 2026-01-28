# Codebase Structure

**Analysis Date:** 2026-01-28

## Directory Layout

```
scholardoc/
├── scholardoc/              # Main package
│   ├── readers/             # Format-specific extraction
│   ├── extractors/          # Structure detection
│   ├── normalizers/         # Legacy OCR pipeline
│   ├── ocr/                 # New OCR pipeline
│   ├── writers/             # Output serialization (empty)
│   ├── utils/               # Shared utilities
│   ├── models.py            # Core data structures
│   ├── convert.py           # Pipeline orchestration
│   ├── config.py            # Configuration classes
│   └── exceptions.py        # Custom exceptions
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── fixtures/            # Test data
├── ground_truth/            # Evaluation system
│   ├── lib/                 # Matching/metrics/reports
│   ├── scripts/             # Annotation/evaluation tools
│   ├── documents/           # Ground truth annotations
│   ├── baselines/           # Baseline results
│   └── ocr_quality/         # OCR validation set
├── spikes/                  # Research/exploration (35 files)
├── docs/                    # Documentation
│   ├── design/              # Design documents
│   └── adr/                 # Architecture Decision Records
└── examples/                # Usage examples
```

## Directory Purposes

**scholardoc/readers/:**
- Purpose: Format-specific document reading
- Contains: PDFReader, RawDocument, PageData, TextBlock, OutlineEntry
- Key files: `pdf_reader.py`

**scholardoc/extractors/:**
- Purpose: Structure detection sources and orchestration
- Contains: CascadingExtractor, PDFOutlineSource, HeadingDetectionSource, ToCParserSource, validators, profiles
- Key files:
  - `cascading.py`: Main orchestrator
  - `sources.py`: Detection sources
  - `profiles.py`: Document type profiles (BOOK_PROFILE, ARTICLE_PROFILE, etc.)
  - `validators.py`: Validation rules

**scholardoc/normalizers/:**
- Purpose: Legacy OCR pipeline (deprecated, will merge with ocr/)
- Contains: OCRPipeline (legacy), AdaptiveDictionary (legacy)
- Key files:
  - `ocr_pipeline.py`: Original implementation
  - `ocr_correction.py`: Correction logic

**scholardoc/ocr/:**
- Purpose: New OCR correction pipeline (validated architecture)
- Contains: OCRPipeline, LineBreakRejoiner, OCRErrorDetector, HybridReOCREngine, AdaptiveDictionary
- Key files:
  - `pipeline.py`: Orchestrator
  - `linebreak.py`: Line-break hyphenation handling
  - `detector.py`: Error detection via spellcheck
  - `dictionary.py`: Adaptive dictionary with morphological validation
  - `reocr.py`: Selective re-OCR engine

**scholardoc/writers/:**
- Purpose: Output format serialization
- Contains: Empty (planned for Phase 2)
- Planned: MarkdownWriter, JSONWriter, RAGChunkWriter

**scholardoc/utils/:**
- Purpose: Shared helper functions
- Contains: Currently minimal
- Key files: `__init__.py`

**ground_truth/:**
- Purpose: Evaluation and testing infrastructure
- Contains:
  - `lib/`: matching, metrics, normalize, reports
  - `scripts/`: evaluate.py, annotate_ui.py, compare.py, validate.py
  - `documents/`: YAML ground truth annotations
  - `ocr_quality/`: OCR validation samples (samples/, classified/, reviewed/)
  - `baselines/`: Baseline extraction results

**spikes/:**
- Purpose: Research explorations and prototyping
- Contains: 35 numbered spike files (01_pymupdf_exploration.py to 32+)
- Pattern: Numbered files with descriptive names
- Notable: 05_ocr_quality_survey.py, 06c_real_ground_truth.py, 08_embedding_robustness.py

**tests/:**
- Purpose: Automated testing
- Contains:
  - `unit/`: Component tests (test_models.py, test_pdf_reader.py, test_ocr_*.py)
  - `integration/`: End-to-end tests (test_convert.py, test_ground_truth_regression.py)
  - `fixtures/`: Test data and helpers
  - `conftest.py`: Pytest configuration

**docs/:**
- Purpose: Design documents and decisions
- Contains:
  - `design/`: CORE_REPRESENTATION.md, STRUCTURE_EXTRACTION.md, OCR_STRATEGY.md, etc.
  - `adr/`: ADR-001 (PDF library), ADR-002 (OCR architecture), ADR-003 (line-breaks), ADR-004 (OCR source tracking)
  - Root: RULES.md, TESTING_METHODOLOGY.md, GIT_WORKFLOW.md, COMMANDS.md

## Key File Locations

**Entry Points:**
- `scholardoc/__init__.py`: Public API exports
- `scholardoc/convert.py`: Main conversion orchestration

**Configuration:**
- `pyproject.toml`: Project metadata, dependencies, tool configs (ruff, pytest)
- `scholardoc/config.py`: ConversionConfig, OCRConfig

**Core Logic:**
- `scholardoc/models.py`: ScholarDocument, Span types, metadata (600+ lines)
- `scholardoc/convert.py`: DocumentBuilder, convert(), convert_batch()
- `scholardoc/readers/pdf_reader.py`: PDFReader.read()
- `scholardoc/extractors/cascading.py`: CascadingExtractor.extract()
- `scholardoc/ocr/pipeline.py`: OCRPipeline.process_text()

**Testing:**
- `tests/conftest.py`: Shared fixtures
- `tests/unit/test_models.py`: Model validation tests
- `tests/integration/test_convert.py`: End-to-end conversion tests
- `tests/integration/test_ground_truth_regression.py`: Regression tests

## Naming Conventions

**Files:**
- Modules: `snake_case.py` (e.g., `pdf_reader.py`, `ocr_pipeline.py`)
- Tests: `test_*.py` (e.g., `test_models.py`)
- Spikes: `NN_descriptive_name.py` (e.g., `01_pymupdf_exploration.py`)

**Directories:**
- Packages: `lowercase` or `snake_case` (e.g., `readers`, `ground_truth`)
- Pluralized for collections: `extractors/`, `writers/`, `tests/`

**Classes:**
- PascalCase: `ScholarDocument`, `PDFReader`, `CascadingExtractor`
- Suffix patterns: `*Reader`, `*Source`, `*Validator`, `*Config`, `*Error`

**Functions:**
- snake_case: `convert()`, `detect_format()`, `process_text()`

## Where to Add New Code

**New Format Reader:**
- Implementation: `scholardoc/readers/epub_reader.py` (following PDFReader pattern)
- Tests: `tests/unit/test_epub_reader.py`
- Integration: Register in `convert.py` format detection

**New Structure Source:**
- Implementation: `scholardoc/extractors/sources.py` (extend CandidateSource ABC)
- Tests: `tests/unit/test_extractors.py`
- Integration: Add to CascadingExtractor sources list

**New Output Writer:**
- Implementation: `scholardoc/writers/markdown_writer.py`
- Tests: `tests/unit/test_writers.py`
- Integration: Add method to ScholarDocument (e.g., `.to_markdown()`)

**New OCR Engine:**
- Implementation: `scholardoc/ocr/reocr.py` (extend OCREngine enum, add backend)
- Tests: `tests/unit/test_ocr_module.py`
- Integration: Update HybridReOCREngine selection logic

**Utilities:**
- Shared helpers: `scholardoc/utils/`
- Text processing: Consider adding to `scholardoc/normalizers/` if OCR-related

**New Feature Spike:**
- Implementation: `spikes/NN_feature_name.py` (next available number)
- Output: `spikes/output/NN_feature_name/` if generates artifacts

**Ground Truth Annotation:**
- Document: `ground_truth/documents/document_name.yaml`
- Schema: Follow `ground_truth/SCHEMA.md`
- Validation: Run `ground_truth/scripts/validate.py`

## Special Directories

**spikes/:**
- Purpose: Research and prototyping before implementation
- Generated: No (manual experiments)
- Committed: Yes (code); output/ directory varies

**spikes/output/:**
- Purpose: Spike-generated artifacts (images, CSVs, reports)
- Generated: Yes (by spike scripts)
- Committed: Selectively (key results yes, large binaries no)

**ground_truth/ocr_quality/:**
- Purpose: OCR validation dataset
- Generated: Mixed (samples extracted, classifications manual)
- Committed: Yes
- Subdirectories:
  - `samples/`: Extracted text samples
  - `classified/`: Human-classified error types
  - `reviewed/`: Reviewed annotations
  - `batches/`: Annotation batches

**tests/fixtures/:**
- Purpose: Test data (sample PDFs, expected outputs)
- Generated: No (curated test data)
- Committed: Yes

**tests/fixtures/ground_truth/:**
- Purpose: Ground truth test cases
- Generated: No
- Committed: Yes

**.planning/:**
- Purpose: GSD codebase mapping outputs
- Generated: Yes (by gsd-codebase-mapper)
- Committed: To be determined by GSD workflow

## Module Exports

**Public API (`scholardoc/__init__.py`):**
- Functions: `convert()`, `convert_batch()`, `detect_format()`, `supported_formats()`
- Models: `ScholarDocument`, all Span types, metadata classes
- Config: `ConversionConfig`
- Exceptions: `ScholarDocError`, `UnsupportedFormatError`, `ExtractionError`, `ConfigurationError`

**Package-level exports:**
- `scholardoc.readers`: PDFReader, RawDocument
- `scholardoc.extractors`: CascadingExtractor, all sources, all profiles
- `scholardoc.ocr`: OCRPipeline, all pipeline components
- `scholardoc.normalizers`: Legacy OCRPipeline (for compatibility)

## Import Patterns

**Absolute imports preferred:**
```python
from scholardoc.models import ScholarDocument
from scholardoc.readers.pdf_reader import PDFReader
from scholardoc.extractors.cascading import CascadingExtractor
```

**TYPE_CHECKING for circular imports:**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scholardoc.readers.pdf_reader import RawDocument
```

**Path aliases:**
- None defined (standard Python imports only)

---

*Structure analysis: 2026-01-28*
