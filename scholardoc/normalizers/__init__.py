"""
Normalizers for transforming raw document content.

See SPEC.md for the normalizer pipeline design.

OCR Pipeline (ADR-002, ADR-003):
- OCRPipeline: Main facade for OCR error detection and line-break rejoining
- AdaptiveDictionary: Hybrid dictionary with morphological validation
- LineBreakRejoiner: Block-based line-break detection
- OCRErrorDetector: Spellcheck-based error detection (flags, does NOT correct)

Legacy OCR Correction (deprecated for most use cases):
- correct_with_spellcheck: Auto-correction (41% damage rate on philosophy texts)
- Use OCRPipeline instead for new code
"""

from scholardoc.normalizers.ocr_correction import (
    DEFAULT_CORRECTION_CONFIG,
    WORD_FREQUENCY_AVAILABLE,
    AnalyzedCorrectionResult,
    CorrectionCandidate,
    CorrectionConfig,
    CorrectionResult,
    OCRCorrectionNormalizer,
    OCRQualityScore,
    analyze_correction,
    correct_known_patterns,
    correct_ocr_errors,
    correct_with_analysis,
    correct_with_context,
    correct_with_language_detection,
    correct_with_spellcheck,
    detect_language,
    get_word_frequency,
    is_contextual_available,
    is_language_detection_available,
    score_ocr_quality,
)
from scholardoc.normalizers.ocr_pipeline import (
    SPELLCHECK_AVAILABLE,
    AdaptiveDictionary,
    LineBreakCandidate,
    LineBreakRejoiner,
    OCRErrorCandidate,
    OCRErrorDetector,
    OCRPipeline,
)

__all__ = [
    # OCR Pipeline (recommended - ADR-002, ADR-003)
    "OCRPipeline",
    "AdaptiveDictionary",
    "LineBreakRejoiner",
    "LineBreakCandidate",
    "OCRErrorDetector",
    "OCRErrorCandidate",
    "SPELLCHECK_AVAILABLE",
    # Quality assessment
    "OCRQualityScore",
    "score_ocr_quality",
    # Legacy correction (use OCRPipeline for new code)
    "CorrectionResult",
    "correct_known_patterns",
    "correct_with_spellcheck",
    "correct_with_context",
    "correct_ocr_errors",
    # Multilingual support
    "detect_language",
    "is_language_detection_available",
    "is_contextual_available",
    "correct_with_language_detection",
    # Confidence-based correction (safeguards)
    "CorrectionConfig",
    "DEFAULT_CORRECTION_CONFIG",
    "CorrectionCandidate",
    "AnalyzedCorrectionResult",
    "analyze_correction",
    "correct_with_analysis",
    # Word frequency utilities
    "WORD_FREQUENCY_AVAILABLE",
    "get_word_frequency",
    # Normalizer class
    "OCRCorrectionNormalizer",
]
