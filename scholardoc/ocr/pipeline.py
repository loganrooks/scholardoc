"""
OCR Pipeline Orchestrator.

This module provides the main pipeline that orchestrates OCR correction:
1. Line-break rejoining (text cleanup)
2. OCR error detection (flagging suspicious words)
3. Selective re-OCR (correcting flagged words)

Architecture Decision: ADR-002 (spellcheck as selector, not corrector)
The pipeline flags words for re-OCR rather than auto-correcting.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PIL import Image

if TYPE_CHECKING:
    import fitz

from scholardoc.ocr.detector import DetectionStats, OCRErrorCandidate, OCRErrorDetector
from scholardoc.ocr.dictionary import AdaptiveDictionary
from scholardoc.ocr.linebreak import LineBreakRejoiner, LineBreakStats
from scholardoc.ocr.reocr import HybridReOCREngine, OCREngine, ReOCRStats

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass
class PipelineResult:
    """Result of pipeline processing for a single page."""

    original_text: str
    corrected_text: str
    errors_detected: list[OCRErrorCandidate]
    linebreak_stats: LineBreakStats
    detection_stats: DetectionStats
    reocr_stats: ReOCRStats
    processing_time_ms: float
    corrections_made: int


@dataclass
class PipelineStats:
    """Aggregate statistics for pipeline processing."""

    pages_processed: int = 0
    total_errors_detected: int = 0
    total_corrections_made: int = 0
    total_linebreaks_joined: int = 0
    total_processing_time_ms: float = 0.0
    engine_used: OCREngine = OCREngine.NONE


# =============================================================================
# OCR PIPELINE
# =============================================================================


@dataclass
class OCRPipeline:
    """
    Main OCR correction pipeline.

    Orchestrates three stages:
    1. LineBreakRejoiner: Prepares text by rejoining hyphenated words
    2. OCRErrorDetector: Flags suspicious words using spellcheck
    3. HybridReOCREngine: Re-OCRs lines containing flagged words

    The pipeline is designed for selective correction - only words that
    fail validation are re-OCRed, preserving good text.

    Attributes:
        dictionary: AdaptiveDictionary for word validation.
        detector: OCRErrorDetector for finding errors.
        rejoiner: LineBreakRejoiner for handling hyphenation.
        reocr_engine: HybridReOCREngine for re-OCR.
        enable_reocr: Whether to perform re-OCR (can disable for detection only).
        persist_dictionary: Whether to save learned words.

    Example:
        >>> from scholardoc.ocr.pipeline import OCRPipeline
        >>> pipeline = OCRPipeline()
        >>> result = pipeline.process_text("The phiinomenon of tbe world")
        >>> result.errors_detected
        [OCRErrorCandidate(word='phiinomenon', ...), OCRErrorCandidate(word='tbe', ...)]
    """

    dictionary: AdaptiveDictionary = field(default_factory=AdaptiveDictionary)
    detector: OCRErrorDetector | None = field(default=None)
    rejoiner: LineBreakRejoiner | None = field(default=None)
    reocr_engine: HybridReOCREngine | None = field(default=None)
    enable_reocr: bool = True
    persist_dictionary: bool = False
    dictionary_path: Path | None = None

    def __post_init__(self) -> None:
        """Initialize pipeline components."""
        # Set up dictionary persistence
        if self.dictionary_path:
            self.dictionary.persistence_path = self.dictionary_path

        # Initialize components with shared dictionary
        if self.detector is None:
            self.detector = OCRErrorDetector(self.dictionary)

        if self.rejoiner is None:
            self.rejoiner = LineBreakRejoiner(self.dictionary)

        if self.reocr_engine is None:
            self.reocr_engine = HybridReOCREngine()

    def process_text(
        self,
        text: str,
        page_num: int = 0,
    ) -> PipelineResult:
        """
        Process text through the detection pipeline (no re-OCR).

        Use this for detection-only mode or when page images aren't available.

        Args:
            text: Text to process.
            page_num: Optional page number for tracking.

        Returns:
            PipelineResult with detection information.
        """
        start_time = time.time()

        # Stage 1: Line-break rejoining (text-only mode)
        rejoined_text, linebreak_stats = self.rejoiner.process_text(text)

        # Stage 2: Error detection
        errors, detection_stats = self.detector.detect_errors_with_stats(rejoined_text, page_num)

        processing_time_ms = (time.time() - start_time) * 1000

        return PipelineResult(
            original_text=text,
            corrected_text=rejoined_text,  # Only linebreak corrections applied
            errors_detected=errors,
            linebreak_stats=linebreak_stats,
            detection_stats=detection_stats,
            reocr_stats=ReOCRStats(),
            processing_time_ms=processing_time_ms,
            corrections_made=linebreak_stats.candidates_joined,
        )

    def process_page(
        self,
        page: fitz.Page,
        page_image: Image.Image | None = None,
    ) -> PipelineResult:
        """
        Process a PDF page through the full pipeline.

        Includes line-break detection using position data and optional
        re-OCR for flagged words.

        Args:
            page: PyMuPDF page object.
            page_image: Optional pre-rendered page image for re-OCR.

        Returns:
            PipelineResult with full correction information.
        """
        start_time = time.time()
        page_num = page.number

        # Extract text
        text = page.get_text()

        # Stage 1: Line-break rejoining with position data
        candidates = self.rejoiner.detect_from_pdf_page(page)
        rejoined_text, linebreak_stats = self.rejoiner.process_text(text, candidates)

        # Stage 2: Error detection
        errors, detection_stats = self.detector.detect_errors_with_stats(rejoined_text, page_num)

        # Stage 3: Re-OCR (if enabled and errors found)
        reocr_stats = ReOCRStats()
        corrected_text = rejoined_text
        corrections_made = linebreak_stats.candidates_joined

        if self.enable_reocr and errors and self.reocr_engine.is_available:
            # Render page image if not provided
            if page_image is None:
                page_image = self.reocr_engine.render_page_to_image(page)

            # Re-OCR would happen here for lines with errors
            # For now, we just track that errors were detected
            # Full re-OCR integration requires line coordinate mapping
            reocr_stats.engine_used = self.reocr_engine.active_engine
            logger.debug(
                "Page %d: %d errors detected, re-OCR would be applied",
                page_num,
                len(errors),
            )

        processing_time_ms = (time.time() - start_time) * 1000

        return PipelineResult(
            original_text=text,
            corrected_text=corrected_text,
            errors_detected=errors,
            linebreak_stats=linebreak_stats,
            detection_stats=detection_stats,
            reocr_stats=reocr_stats,
            processing_time_ms=processing_time_ms,
            corrections_made=corrections_made,
        )

    def process_document(
        self,
        doc: fitz.Document,
        page_range: tuple[int, int] | None = None,
    ) -> tuple[list[PipelineResult], PipelineStats]:
        """
        Process multiple pages from a document.

        Args:
            doc: PyMuPDF document object.
            page_range: Optional (start, end) page range (inclusive).

        Returns:
            Tuple of (results list, aggregate statistics).
        """
        stats = PipelineStats()

        # Determine page range
        if page_range:
            start, end = page_range
            pages = range(start, min(end + 1, len(doc)))
        else:
            pages = range(len(doc))

        results = []
        for page_num in pages:
            page = doc[page_num]
            result = self.process_page(page)
            results.append(result)

            # Update aggregate stats
            stats.pages_processed += 1
            stats.total_errors_detected += len(result.errors_detected)
            stats.total_corrections_made += result.corrections_made
            stats.total_linebreaks_joined += result.linebreak_stats.candidates_joined
            stats.total_processing_time_ms += result.processing_time_ms

        stats.engine_used = self.reocr_engine.active_engine if self.reocr_engine else OCREngine.NONE

        # Persist dictionary if enabled
        if self.persist_dictionary:
            self.dictionary.save()

        return results, stats

    @property
    def is_reocr_available(self) -> bool:
        """Check if re-OCR engine is available."""
        return self.reocr_engine is not None and self.reocr_engine.is_available

    def get_info(self) -> dict[str, Any]:
        """Get pipeline configuration information."""
        return {
            "enable_reocr": self.enable_reocr,
            "reocr_available": self.is_reocr_available,
            "reocr_engine": (self.reocr_engine.get_engine_info() if self.reocr_engine else None),
            "dictionary_path": str(self.dictionary_path) if self.dictionary_path else None,
            "persist_dictionary": self.persist_dictionary,
            "scholarly_vocab_size": self.detector.get_scholarly_vocab_size()
            if self.detector
            else 0,
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def create_pipeline(
    enable_reocr: bool = True,
    dictionary_path: Path | None = None,
    persist_dictionary: bool = False,
) -> OCRPipeline:
    """
    Create an OCR pipeline with default configuration.

    Args:
        enable_reocr: Whether to enable re-OCR for flagged words.
        dictionary_path: Optional path for dictionary persistence.
        persist_dictionary: Whether to save learned words.

    Returns:
        Configured OCRPipeline instance.
    """
    dictionary = AdaptiveDictionary(persistence_path=dictionary_path)

    return OCRPipeline(
        dictionary=dictionary,
        enable_reocr=enable_reocr,
        persist_dictionary=persist_dictionary,
        dictionary_path=dictionary_path,
    )
