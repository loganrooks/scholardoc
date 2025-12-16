"""
Normalizers for transforming raw document content.

See SPEC.md for the normalizer pipeline design.
"""

from scholardoc.normalizers.ocr_correction import (
    CorrectionResult,
    OCRCorrectionNormalizer,
    OCRQualityScore,
    correct_known_patterns,
    correct_ocr_errors,
    correct_with_spellcheck,
    score_ocr_quality,
)

__all__ = [
    "OCRQualityScore",
    "CorrectionResult",
    "score_ocr_quality",
    "correct_known_patterns",
    "correct_with_spellcheck",
    "correct_ocr_errors",
    "OCRCorrectionNormalizer",
]
