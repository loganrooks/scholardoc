"""
Document conversion orchestrator.

This module provides the main `convert()` function that transforms PDFs
into ScholarDocument objects by wiring together:
- PDFReader (raw extraction)
- OCRPipeline (text normalization)
- CascadingExtractor (structure extraction)
- DocumentBuilder (assembly)

See docs/design/CORE_REPRESENTATION.md for the ScholarDocument design.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from scholardoc.config import ConversionConfig
from scholardoc.exceptions import ExtractionError, UnsupportedFormatError
from scholardoc.extractors.cascading import CascadingExtractor
from scholardoc.models import (
    DocumentMetadata,
    DocumentType,
    PageQuality,
    PageSpan,
    ParagraphSpan,
    QualityInfo,
    QualityLevel,
    ScholarDocument,
    SectionSpan,
)
from scholardoc.normalizers.ocr_pipeline import OCRPipeline as LegacyOCRPipeline
from scholardoc.ocr.pipeline import create_pipeline as create_new_ocr_pipeline
from scholardoc.readers.pdf_reader import PDFReader, RawDocument

if TYPE_CHECKING:
    from scholardoc.extractors.cascading import StructureResult

logger = logging.getLogger(__name__)

__version__ = "0.1.0"


# ═══════════════════════════════════════════════════════════════════════════════
# Document Builder
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class BuilderContext:
    """Context accumulated during document building."""

    raw_doc: RawDocument
    config: ConversionConfig
    processing_log: list[str] = field(default_factory=list)

    # Text processing results
    clean_text: str = ""
    page_spans: list[PageSpan] = field(default_factory=list)
    paragraph_spans: list[ParagraphSpan] = field(default_factory=list)

    # Structure results
    section_spans: list[SectionSpan] = field(default_factory=list)
    structure_confidence: float = 0.0
    structure_source: str = ""

    # Quality info
    quality: QualityInfo = field(default_factory=QualityInfo)
    page_qualities: list[PageQuality] = field(default_factory=list)
    error_count: int = 0


class DocumentBuilder:
    """
    Builds ScholarDocument from raw extraction results.

    This class handles the transformation from RawDocument (position-aware
    blocks) to ScholarDocument (clean text + position annotations).

    OCR correction is controlled by config.ocr.enabled:
    - False (default): Use legacy pipeline (line-break rejoining + detection only)
    - True: Use new OCR pipeline with optional re-OCR
    """

    def __init__(self, config: ConversionConfig | None = None) -> None:
        """Initialize the builder."""
        self.config = config or ConversionConfig()

        # Initialize OCR pipeline based on config
        if self.config.ocr.enabled:
            self.ocr_pipeline = create_new_ocr_pipeline(
                enable_reocr=self.config.ocr.enable_reocr,
                dictionary_path=self.config.ocr.dictionary_path,
                persist_dictionary=self.config.ocr.persist_dictionary,
            )
            self._use_new_ocr = True
        else:
            self.ocr_pipeline = LegacyOCRPipeline()
            self._use_new_ocr = False

        self.structure_extractor = CascadingExtractor()

    def build(self, raw_doc: RawDocument) -> ScholarDocument:
        """
        Build a ScholarDocument from a RawDocument.

        Args:
            raw_doc: The raw extracted PDF data

        Returns:
            A fully populated ScholarDocument
        """
        ctx = BuilderContext(raw_doc=raw_doc, config=self.config)
        ctx.processing_log.append(f"Starting build from {raw_doc.source_path}")

        # Step 1: Process text with OCR pipeline
        self._process_text(ctx)

        # Step 2: Build page spans
        self._build_page_spans(ctx)

        # Step 3: Build paragraph spans
        self._build_paragraph_spans(ctx)

        # Step 4: Extract structure (sections)
        self._extract_structure(ctx)

        # Step 5: Build metadata
        metadata = self._build_metadata(ctx)

        # Step 6: Assemble final document
        ctx.processing_log.append(
            f"Build complete: {len(ctx.clean_text)} chars, "
            f"{len(ctx.page_spans)} pages, {len(ctx.section_spans)} sections"
        )

        return ScholarDocument(
            text=ctx.clean_text,
            pages=ctx.page_spans,
            sections=ctx.section_spans,
            paragraphs=ctx.paragraph_spans,
            metadata=metadata,
            source_path=raw_doc.source_path,
            quality=ctx.quality,
            processing_log=ctx.processing_log,
        )

    def _process_text(self, ctx: BuilderContext) -> None:
        """
        Process text through OCR pipeline.

        Applies line-break rejoining and detects OCR errors.
        Uses new OCR pipeline if config.ocr.enabled, otherwise uses legacy.
        """
        raw_text = ctx.raw_doc.text
        ctx.processing_log.append(f"Raw text: {len(raw_text)} chars")

        if self._use_new_ocr:
            # New OCR pipeline - returns PipelineResult with full stats
            result = self.ocr_pipeline.process_text(raw_text)
            clean_text = result.corrected_text
            ctx.error_count = len(result.errors_detected)

            ctx.processing_log.append(
                f"After OCR pipeline: {len(clean_text)} chars, "
                f"{result.linebreak_stats.candidates_joined} linebreaks joined, "
                f"{ctx.error_count} errors detected"
            )

            if result.errors_detected:
                # Set quality based on detection stats
                word_count = max(result.detection_stats.words_checked, 1)
                error_rate = ctx.error_count / word_count

                if error_rate > 0.05:
                    ctx.quality.overall = QualityLevel.BAD
                    ctx.quality.overall_confidence = 0.5
                elif error_rate > 0.02:
                    ctx.quality.overall = QualityLevel.MARGINAL
                    ctx.quality.overall_confidence = 0.7
                else:
                    ctx.quality.overall = QualityLevel.GOOD
                    ctx.quality.overall_confidence = 0.9
            else:
                ctx.quality.overall = QualityLevel.GOOD
                ctx.quality.overall_confidence = 0.95

        else:
            # Legacy OCR pipeline
            clean_text = self.ocr_pipeline.apply_line_breaks(raw_text)
            ctx.processing_log.append(f"After line-break rejoining: {len(clean_text)} chars")

            errors = self.ocr_pipeline.detect_errors(clean_text)
            ctx.error_count = len(errors)

            if errors:
                ctx.processing_log.append(f"OCR errors detected: {len(errors)} words")
                # Store pages needing re-OCR (position is tuple: (page, word_index, char_offset))
                pages_with_errors = {e.position[0] for e in errors}
                ctx.quality.needs_reocr = sorted(pages_with_errors)

                error_rate = len(errors) / max(len(clean_text.split()), 1)
                if error_rate > 0.05:
                    ctx.quality.overall = QualityLevel.BAD
                    ctx.quality.overall_confidence = 0.5
                elif error_rate > 0.02:
                    ctx.quality.overall = QualityLevel.MARGINAL
                    ctx.quality.overall_confidence = 0.7
                else:
                    ctx.quality.overall = QualityLevel.GOOD
                    ctx.quality.overall_confidence = 0.9
            else:
                ctx.quality.overall = QualityLevel.GOOD
                ctx.quality.overall_confidence = 0.95

        ctx.clean_text = clean_text

    def _clean_page_text(self, text: str) -> str:
        """Clean page text using appropriate pipeline."""
        if self._use_new_ocr:
            result = self.ocr_pipeline.process_text(text)
            return result.corrected_text
        else:
            return self.ocr_pipeline.apply_line_breaks(text)

    def _build_page_spans(self, ctx: BuilderContext) -> None:
        """Build PageSpan annotations from page positions."""
        # The RawDocument provides page_positions as (start, end) tuples
        # But these positions are in the RAW text, not clean text
        # For now, we'll use a simpler approach: rebuild from pages

        current_pos = 0
        page_spans = []

        for i, page in enumerate(ctx.raw_doc.pages):
            page_text = page.text or ""
            # Apply same cleaning to page text to get accurate length
            clean_page_text = self._clean_page_text(page_text)
            page_len = len(clean_page_text)

            if page_len > 0:
                page_spans.append(
                    PageSpan(
                        start=current_pos,
                        end=current_pos + page_len,
                        label=page.label or str(i + 1),
                        index=page.index,
                    )
                )

            # Account for page separator (\n\n)
            current_pos += page_len + 2

        ctx.page_spans = page_spans
        ctx.processing_log.append(f"Built {len(page_spans)} page spans")

    def _build_paragraph_spans(self, ctx: BuilderContext) -> None:
        """Build ParagraphSpan annotations from text structure."""
        # Detect paragraphs by double-newlines
        paragraphs = []
        text = ctx.clean_text

        # Split on double newlines (or more)
        para_pattern = re.compile(r"\n\n+")
        current_pos = 0

        for match in para_pattern.finditer(text):
            para_end = match.start()
            if para_end > current_pos:
                paragraphs.append(ParagraphSpan(start=current_pos, end=para_end))
            current_pos = match.end()

        # Last paragraph
        if current_pos < len(text):
            paragraphs.append(ParagraphSpan(start=current_pos, end=len(text)))

        ctx.paragraph_spans = paragraphs
        ctx.processing_log.append(f"Built {len(paragraphs)} paragraph spans")

    def _extract_structure(self, ctx: BuilderContext) -> None:
        """Extract document structure (sections) using cascading extractor."""
        try:
            structure: StructureResult = self.structure_extractor.extract(ctx.raw_doc)

            ctx.section_spans = structure.sections
            ctx.structure_confidence = structure.confidence
            ctx.structure_source = structure.primary_source
            ctx.processing_log.extend(structure.processing_log)
            ctx.processing_log.append(
                f"Structure extraction: {len(structure.sections)} sections "
                f"from {structure.primary_source} (conf={structure.confidence:.2f})"
            )
        except Exception as e:
            ctx.processing_log.append(f"Structure extraction failed: {e}")
            logger.warning("Structure extraction failed: %s", e)
            # Continue without structure - graceful degradation

    def _build_metadata(self, ctx: BuilderContext) -> DocumentMetadata:
        """Build document metadata from raw metadata and analysis."""
        raw_meta = ctx.raw_doc.metadata

        # Determine document type from raw metadata hints
        doc_type = DocumentType.GENERIC
        if ctx.raw_doc.has_outline:
            doc_type = DocumentType.BOOK
        elif ctx.raw_doc.page_count < 30:
            doc_type = DocumentType.ARTICLE

        return DocumentMetadata(
            title=raw_meta.get("title"),
            author=raw_meta.get("author"),
            authors=[raw_meta.get("author")] if raw_meta.get("author") else [],
            document_type=doc_type,
            language="en",  # TODO: detect language
            page_count=ctx.raw_doc.page_count,
            source_format="pdf",
            extraction_date=datetime.now(),
            scholardoc_version=__version__,
            raw=raw_meta,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════


def convert(
    source: str | Path,
    config: ConversionConfig | None = None,
) -> ScholarDocument:
    """
    Convert a document to structured ScholarDocument.

    This is the main entry point for ScholarDoc. It handles:
    - Format detection
    - Raw extraction (PDFReader)
    - OCR normalization (line breaks, error detection)
    - Structure extraction (sections via cascading extractor)
    - Document assembly

    Args:
        source: Path to document file
        config: Conversion configuration (uses defaults if None)

    Returns:
        ScholarDocument with text, annotations, and metadata

    Raises:
        FileNotFoundError: If source doesn't exist
        UnsupportedFormatError: If format not supported
        ExtractionError: If extraction fails (when on_extraction_error="raise")

    Example:
        >>> doc = convert("kant.pdf")
        >>> print(doc.text[:100])  # Clean text
        >>> for chunk in doc.to_rag_chunks():
        ...     print(chunk.citation)
    """
    source = Path(source)
    config = config or ConversionConfig()

    # Validate file exists
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    # Detect and validate format
    fmt = detect_format(source)
    if fmt != "pdf":
        raise UnsupportedFormatError(
            f"Format '{fmt}' not yet supported. Currently only PDF is supported."
        )

    try:
        # Read raw document
        reader = PDFReader()
        raw_doc = reader.read(source)

        # Build ScholarDocument
        builder = DocumentBuilder(config)
        doc = builder.build(raw_doc)

        return doc

    except Exception as e:
        if config.on_extraction_error == "raise":
            raise ExtractionError(f"Failed to convert {source}: {e}") from e
        elif config.on_extraction_error == "warn":
            logger.warning("Extraction error for %s: %s", source, e)
            # Return a minimal document with the error
            return ScholarDocument(
                text="",
                source_path=source,
                processing_log=[f"Extraction failed: {e}"],
                quality=QualityInfo(overall=QualityLevel.BAD, overall_confidence=0.0),
            )
        else:  # skip
            raise ExtractionError(f"Failed to convert {source}: {e}") from e


def convert_batch(
    sources: list[str | Path],
    config: ConversionConfig | None = None,
    parallel: bool = False,
    max_workers: int = 4,
):
    """
    Convert multiple documents, yielding results as completed.

    Args:
        sources: Paths to document files
        config: Conversion configuration
        parallel: Whether to process in parallel
        max_workers: Max parallel workers (if parallel=True)

    Yields:
        (path, result) tuples where result is ScholarDocument or Exception
    """
    config = config or ConversionConfig()

    if parallel:
        # TODO: Implement parallel processing in future
        logger.warning("Parallel processing not yet implemented, falling back to sequential")

    for source in sources:
        source = Path(source)
        try:
            doc = convert(source, config)
            yield (source, doc)
        except Exception as e:
            if config.on_extraction_error == "skip":
                continue
            yield (source, e)


def detect_format(path: str | Path) -> str:
    """
    Detect document format from file extension and magic bytes.

    Args:
        path: Path to document file

    Returns:
        Format string: "pdf", "epub", "markdown", etc.

    Raises:
        UnsupportedFormatError: If format cannot be detected or isn't supported
    """
    path = Path(path)

    # Check extension first
    ext = path.suffix.lower()
    ext_map = {
        ".pdf": "pdf",
        ".epub": "epub",
        ".md": "markdown",
        ".markdown": "markdown",
        ".mobi": "mobi",
        ".azw": "mobi",
        ".azw3": "mobi",
    }

    if ext in ext_map:
        return ext_map[ext]

    # Try magic bytes for PDF
    try:
        with open(path, "rb") as f:
            header = f.read(8)
            if header.startswith(b"%PDF"):
                return "pdf"
    except (OSError, PermissionError):
        pass

    raise UnsupportedFormatError(f"Cannot detect format for: {path}")


def supported_formats() -> list[str]:
    """Return list of currently supported input formats."""
    return ["pdf"]  # Phase 1: PDF only
