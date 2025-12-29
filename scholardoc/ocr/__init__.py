"""
OCR correction pipeline for scholarly document processing.

This module provides OCR error detection and correction using:
- Spellcheck-based error detection (not auto-correction)
- Selective re-OCR for flagged words
- Line-break hyphenation rejoining
- Adaptive dictionary with morphological validation

Architecture Decisions:
- ADR-002: Spellcheck as selector for re-OCR, not auto-corrector
- ADR-003: Block-based line-break filtering

Example:
    >>> from scholardoc.ocr import OCRPipeline
    >>> pipeline = OCRPipeline()
    >>> result = pipeline.process_text("The phiinomenon of tbe world")
    >>> [e.word for e in result.errors_detected]
    ['phiinomenon', 'tbe']
"""

from scholardoc.ocr.detector import (
    DetectionStats,
    OCRErrorCandidate,
    OCRErrorDetector,
)
from scholardoc.ocr.dictionary import AdaptiveDictionary
from scholardoc.ocr.linebreak import (
    LineBreakCandidate,
    LineBreakRejoiner,
    LineBreakStats,
)
from scholardoc.ocr.pipeline import (
    OCRPipeline,
    PipelineResult,
    PipelineStats,
    create_pipeline,
)
from scholardoc.ocr.reocr import (
    HybridReOCREngine,
    LineCoordinates,
    OCREngine,
    ReOCRResult,
    ReOCRStats,
)

__all__ = [
    # Pipeline
    "OCRPipeline",
    "PipelineResult",
    "PipelineStats",
    "create_pipeline",
    # Detection
    "OCRErrorDetector",
    "OCRErrorCandidate",
    "DetectionStats",
    # Dictionary
    "AdaptiveDictionary",
    # Line-break
    "LineBreakRejoiner",
    "LineBreakCandidate",
    "LineBreakStats",
    # Re-OCR
    "HybridReOCREngine",
    "OCREngine",
    "ReOCRResult",
    "ReOCRStats",
    "LineCoordinates",
]
