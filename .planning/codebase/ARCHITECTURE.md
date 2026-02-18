# Architecture

**Analysis Date:** 2026-01-28

## Pattern Overview

**Overall:** Pipeline architecture with staged transformation

**Key Characteristics:**
- Separation of extraction from presentation
- Position-based text annotation system
- Cascading fallback for structure detection
- Dual persistence (JSON + SQLite planned)
- Immutable intermediate representations

## Layers

**Reader Layer:**
- Purpose: Raw extraction from document formats
- Location: `scholardoc/readers/`
- Contains: PDFReader, RawDocument, TextBlock, PageData
- Depends on: PyMuPDF (fitz)
- Used by: DocumentBuilder

**Normalization Layer:**
- Purpose: OCR correction and text cleanup
- Location: `scholardoc/normalizers/`, `scholardoc/ocr/`
- Contains: OCRPipeline (legacy + new), LineBreakRejoiner, OCRErrorDetector, HybridReOCREngine
- Depends on: Reader layer, pyspellchecker, pytesseract (optional), doctr (optional)
- Used by: DocumentBuilder

**Extraction Layer:**
- Purpose: Structure detection from raw content
- Location: `scholardoc/extractors/`
- Contains: CascadingExtractor, PDFOutlineSource, HeadingDetectionSource, ToCParserSource
- Depends on: Reader layer (RawDocument)
- Used by: DocumentBuilder

**Model Layer:**
- Purpose: Core data structures and intermediate representation
- Location: `scholardoc/models.py`
- Contains: ScholarDocument, SectionSpan, PageSpan, DocumentMetadata
- Depends on: Pydantic (dataclasses)
- Used by: All layers

**Writer Layer:**
- Purpose: Output generation and serialization
- Location: `scholardoc/writers/`
- Contains: Empty (planned for Phase 2+)
- Depends on: ScholarDocument
- Used by: Public API

**Orchestration Layer:**
- Purpose: Pipeline coordination and assembly
- Location: `scholardoc/convert.py`
- Contains: DocumentBuilder, BuilderContext, convert(), convert_batch()
- Depends on: All layers
- Used by: Public API (`scholardoc/__init__.py`)

## Data Flow

**Primary Conversion Flow:**

1. `convert(path, config)` → detect format
2. `PDFReader.read(path)` → `RawDocument` (pages, outline, text blocks)
3. `OCRPipeline.process_text(raw_text)` → `PipelineResult` (cleaned text, error candidates)
4. `CascadingExtractor.extract(raw_doc)` → `StructureResult` (section spans)
5. `DocumentBuilder.build(raw_doc)` → `ScholarDocument` (final representation)
6. `ScholarDocument.to_markdown()` / `.to_rag_chunks()` → output

**State Management:**
- BuilderContext accumulates state during document building
- processing_log tracks decisions through pipeline
- Immutable results from each stage (dataclasses with frozen=True)

## Key Abstractions

**RawDocument:**
- Purpose: Intermediate representation between reader and builder
- Examples: `scholardoc/readers/pdf_reader.py` (lines 81-125)
- Pattern: Data class with lazy properties (_text_cache, _page_positions)

**ScholarDocument:**
- Purpose: Final structured representation with clean text + position annotations
- Examples: `scholardoc/models.py` (lines 310-500+)
- Pattern: Pydantic model with derived properties and export methods

**Span:**
- Purpose: Position-based annotation (start, end) in clean text
- Examples: `PageSpan`, `SectionSpan`, `ParagraphSpan`, `FootnoteRef`
- Pattern: Immutable dataclass with position validation

**CascadingExtractor:**
- Purpose: Fallback-based structure detection (outline → heading → ToC → fallback)
- Examples: `scholardoc/extractors/cascading.py` (lines 58-200+)
- Pattern: Source orchestration with confidence scoring

**OCRPipeline:**
- Purpose: Multi-stage text normalization (linebreak → detect → re-OCR)
- Examples: `scholardoc/ocr/pipeline.py` (lines 70-180+)
- Pattern: Orchestrator with pluggable engines

## Entry Points

**Public API:**
- Location: `scholardoc/__init__.py`
- Triggers: User import (`import scholardoc`)
- Responsibilities: Expose convert(), models, exceptions

**convert():**
- Location: `scholardoc/convert.py` (line 347)
- Triggers: User calls `scholardoc.convert(path)`
- Responsibilities: Format detection, reader selection, pipeline orchestration

**DocumentBuilder.build():**
- Location: `scholardoc/convert.py` (line 109)
- Triggers: Called by convert() after reading
- Responsibilities: OCR processing, span building, structure extraction, assembly

## Error Handling

**Strategy:** Configurable degradation with logging

**Patterns:**
- `config.on_extraction_error` controls behavior: "raise", "warn", "skip"
- Graceful degradation: CascadingExtractor returns empty list if no sources work
- Processing log preserves decision trail: `ctx.processing_log.append()`
- Custom exceptions: ScholarDocError → UnsupportedFormatError, ExtractionError, ConfigurationError

## Cross-Cutting Concerns

**Logging:** Python logging module, logger = logging.getLogger(__name__) per module

**Validation:**
- Pydantic for model validation
- Validators in extractors: HierarchyValidator, NoOverlapValidator, TitleQualityValidator
- Config validation in __post_init__

**Authentication:** Not applicable (library, not service)

**Configuration:**
- ConversionConfig: top-level options (output, structure, error handling)
- OCRConfig: nested config (enabled=False by default, thresholds, persistence)
- Profile-based: DocumentProfile for type-specific extraction rules

**Quality Tracking:**
- QualityInfo: overall level (GOOD/MARGINAL/BAD), confidence, needs_reocr pages
- OCRSourceInfo: detected OCR engine from PDF metadata
- PageQuality: per-page quality assessment (planned)

**Extensibility:**
- CandidateSource ABC for new structure sources
- OCREngine enum for new re-OCR backends
- Profile system for document-type customization

---

*Architecture analysis: 2026-01-28*
