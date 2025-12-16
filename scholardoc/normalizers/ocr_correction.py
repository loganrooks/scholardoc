"""
OCR Error Detection and Correction for ScholarDoc.

This module provides OCR quality assessment and correction capabilities
based on findings from Spike 08 (embedding robustness testing).

Key findings that drive this implementation:
- 5% character error rate → 0.65 cosine similarity (below usable threshold)
- Single-word errors like "Beautlful" drop similarity to 0.515
- Character confusions (l/1/I, rn/m) are most impactful
- Hyphenation errors have minimal embedding impact

See docs/design/OCR_STRATEGY.md for full design rationale.
"""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field

try:
    from spellchecker import SpellChecker
except ImportError:
    SpellChecker = None  # type: ignore

logger = logging.getLogger(__name__)


# ============================================================================
# OCR Error Patterns (from Spike 05 and Spike 08 analysis)
# ============================================================================

# Common OCR character confusions
CHAR_CONFUSIONS = {
    # l/1/I confusion (most common in Kant PDF: 3,450 instances)
    "l": ["1", "I", "|"],
    "I": ["l", "1", "|"],
    "1": ["l", "I", "|"],
    # O/0 confusion
    "O": ["0", "Q"],
    "0": ["O", "o"],
    "o": ["0", "O"],
    # Shape-similar letters
    "rn": ["m"],
    "m": ["rn"],
    "n": ["ri", "h"],
    "h": ["b", "li"],
    "d": ["cl", "ol"],
    "e": ["c", "o"],
    "c": ["e", "o"],
    "a": ["o", "e"],
    "u": ["v", "n"],
    "v": ["u", "w"],
    # Common OCR artifacts
    "fi": ["fl"],
    "fl": ["fi"],
    "ff": ["fl"],
}

# Patterns that indicate OCR errors
OCR_ERROR_PATTERNS = [
    # Mid-word capitals (from Spike 05: "beautIful", "Iii")
    re.compile(r"\b[a-z]+[A-Z]+[a-z]+"),
    # Digits in words (except common cases like "3rd", "1st")
    re.compile(r"\b[a-z]+[0-9]+[a-z]+\b", re.IGNORECASE),
    # Broken hyphenation at word boundaries
    re.compile(r"\w+-\s+\w+"),
    # Double punctuation
    re.compile(r"[.,;:]{2,}"),
    # Pipe character in text (often l/1/I confusion)
    re.compile(r"\w\|\w"),
]

# Words commonly produced by OCR errors (real-word errors)
COMMON_OCR_MISSPELLINGS = {
    "tbe": "the",
    "arid": "and",
    "thar": "that",
    "tills": "this",
    "hare": "have",
    "bccn": "been",
    "bcing": "being",
    "thcir": "their",
    "wonld": "would",
    "conld": "could",
    "shonld": "should",
    "beautlful": "beautiful",
    "rnorning": "morning",
}


# ============================================================================
# Quality Scoring
# ============================================================================


@dataclass
class OCRQualityScore:
    """
    OCR quality assessment for a text.

    Attributes:
        overall_score: 0.0-1.0, higher is better quality
        error_rate: Estimated character error rate
        suspicious_words: Words flagged as potential OCR errors
        error_patterns: Counts of each error pattern type found
        correctable_words: Words that can be auto-corrected
        confidence: Confidence in the quality assessment
    """

    overall_score: float
    error_rate: float
    suspicious_words: list[str] = field(default_factory=list)
    error_patterns: dict[str, int] = field(default_factory=dict)
    correctable_words: dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0

    @property
    def is_usable_for_rag(self) -> bool:
        """
        Whether this text quality is acceptable for RAG embedding.

        Based on Spike 08 findings: need >0.9 cosine similarity
        which requires <2% character error rate.
        """
        return self.error_rate < 0.02

    @property
    def needs_correction(self) -> bool:
        """Whether correction is recommended."""
        return self.error_rate >= 0.01 or len(self.correctable_words) > 0


def score_ocr_quality(
    text: str,
    spell_check: bool = True,
    detailed: bool = False,
) -> OCRQualityScore:
    """
    Assess the OCR quality of text.

    Args:
        text: Text to analyze
        spell_check: Whether to use spell checker for detection
        detailed: Whether to include detailed word-level analysis

    Returns:
        OCRQualityScore with quality metrics
    """
    if not text or not text.strip():
        return OCRQualityScore(
            overall_score=0.0,
            error_rate=1.0,
            confidence=0.0,
        )

    words = text.split()
    total_words = len(words)
    total_chars = len(text)

    suspicious_words: list[str] = []
    error_patterns: dict[str, int] = {
        "mid_word_caps": 0,
        "digits_in_words": 0,
        "broken_hyphenation": 0,
        "double_punctuation": 0,
        "pipe_in_word": 0,
    }
    correctable_words: dict[str, str] = {}

    # Check for OCR error patterns
    for pattern_name, pattern in [
        ("mid_word_caps", OCR_ERROR_PATTERNS[0]),
        ("digits_in_words", OCR_ERROR_PATTERNS[1]),
        ("broken_hyphenation", OCR_ERROR_PATTERNS[2]),
        ("double_punctuation", OCR_ERROR_PATTERNS[3]),
        ("pipe_in_word", OCR_ERROR_PATTERNS[4]),
    ]:
        matches = pattern.findall(text)
        error_patterns[pattern_name] = len(matches)
        suspicious_words.extend(matches)

    # Check known OCR misspellings
    for word in words:
        word_lower = word.lower().strip(".,;:!?\"'")
        if word_lower in COMMON_OCR_MISSPELLINGS:
            suspicious_words.append(word)
            correctable_words[word_lower] = COMMON_OCR_MISSPELLINGS[word_lower]

    # Spell check for additional detection
    if spell_check and SpellChecker is not None:
        spell = SpellChecker()
        # Get unique words, lowercase, stripped of punctuation
        unique_words = {
            w.lower().strip(".,;:!?\"'()[]") for w in words if len(w) > 2 and w.isalpha()
        }
        misspelled = spell.unknown(unique_words)

        for word in misspelled:
            if word not in suspicious_words:
                suspicious_words.append(word)
                correction = spell.correction(word)
                if correction and correction != word:
                    correctable_words[word] = correction

    # Calculate error rate estimate
    # Weight different error types by severity (based on Spike 08)
    pattern_errors = (
        error_patterns["mid_word_caps"] * 2  # High impact
        + error_patterns["digits_in_words"] * 2
        + error_patterns["pipe_in_word"] * 2
        + error_patterns["broken_hyphenation"] * 0.5  # Low impact per Spike 08
        + error_patterns["double_punctuation"] * 0.5
    )

    # Estimate character errors (rough: ~5 chars per suspicious word)
    estimated_char_errors = pattern_errors * 5 + len(correctable_words) * 3
    error_rate = min(1.0, estimated_char_errors / max(1, total_chars))

    # Calculate overall score (inverse of error rate)
    overall_score = max(0.0, 1.0 - error_rate * 10)  # Scale for visibility

    # Confidence based on sample size
    confidence = min(1.0, total_words / 100)  # Need ~100 words for good estimate

    return OCRQualityScore(
        overall_score=overall_score,
        error_rate=error_rate,
        suspicious_words=suspicious_words if detailed else suspicious_words[:20],
        error_patterns=error_patterns,
        correctable_words=correctable_words
        if detailed
        else dict(list(correctable_words.items())[:10]),
        confidence=confidence,
    )


# ============================================================================
# Correction Functions
# ============================================================================


@dataclass
class CorrectionResult:
    """Result of OCR correction."""

    original_text: str
    corrected_text: str
    changes_made: list[tuple[str, str]]  # (original, corrected)
    confidence: float  # Confidence in corrections

    @property
    def change_count(self) -> int:
        """Number of corrections made."""
        return len(self.changes_made)

    @property
    def was_modified(self) -> bool:
        """Whether any changes were made."""
        return self.original_text != self.corrected_text


def correct_known_patterns(text: str) -> CorrectionResult:
    """
    Apply rule-based corrections for known OCR error patterns.

    This is fast and safe - only fixes well-known OCR artifacts.

    Args:
        text: Text to correct

    Returns:
        CorrectionResult with corrections
    """
    changes: list[tuple[str, str]] = []
    result = text

    # Fix known misspellings
    for wrong, right in COMMON_OCR_MISSPELLINGS.items():
        pattern = re.compile(rf"\b{wrong}\b", re.IGNORECASE)
        matches = pattern.findall(result)
        if matches:
            for match in matches:
                # Preserve original case
                if match[0].isupper():
                    replacement = right.capitalize()
                else:
                    replacement = right
                changes.append((match, replacement))
            result = pattern.sub(
                lambda m, r=right: r.capitalize() if m.group()[0].isupper() else r,
                result,
            )

    # Fix broken hyphenation (word- continuation)
    hyphen_pattern = re.compile(r"(\w+)-\s+(\w+)")
    for match in hyphen_pattern.finditer(text):
        original = match.group(0)
        fixed = match.group(1) + match.group(2)
        if original not in [c[0] for c in changes]:
            changes.append((original, fixed))
    result = hyphen_pattern.sub(r"\1\2", result)

    return CorrectionResult(
        original_text=text,
        corrected_text=result,
        changes_made=changes,
        confidence=0.9,  # High confidence for known patterns
    )


def correct_with_spellcheck(
    text: str,
    min_word_length: int = 4,
    skip_capitalized: bool = True,
) -> CorrectionResult:
    """
    Apply spell-check based corrections.

    More aggressive than pattern-based, but may introduce false corrections.

    Args:
        text: Text to correct
        min_word_length: Minimum word length to consider for correction
        skip_capitalized: Skip words that start with capital (proper nouns)

    Returns:
        CorrectionResult with corrections
    """
    if SpellChecker is None:
        logger.warning("pyspellchecker not installed, skipping spell check")
        return CorrectionResult(
            original_text=text,
            corrected_text=text,
            changes_made=[],
            confidence=0.0,
        )

    spell = SpellChecker()
    changes: list[tuple[str, str]] = []
    words = text.split()
    result_words = []

    for word in words:
        # Extract the core word (without punctuation)
        prefix = ""
        suffix = ""
        core = word

        # Strip leading punctuation
        while core and not core[0].isalnum():
            prefix += core[0]
            core = core[1:]

        # Strip trailing punctuation
        while core and not core[-1].isalnum():
            suffix = core[-1] + suffix
            core = core[:-1]

        # Skip if too short or capitalized proper noun
        if len(core) < min_word_length:
            result_words.append(word)
            continue

        if skip_capitalized and core and core[0].isupper() and core[1:].islower():
            result_words.append(word)
            continue

        # Check spelling
        if core.lower() in spell:
            result_words.append(word)
            continue

        correction = spell.correction(core.lower())
        if correction and correction != core.lower():
            # Preserve case
            if core.isupper():
                corrected_core = correction.upper()
            elif core[0].isupper():
                corrected_core = correction.capitalize()
            else:
                corrected_core = correction

            changes.append((word, prefix + corrected_core + suffix))
            result_words.append(prefix + corrected_core + suffix)
        else:
            result_words.append(word)

    return CorrectionResult(
        original_text=text,
        corrected_text=" ".join(result_words),
        changes_made=changes,
        confidence=0.7,  # Medium confidence for spell check
    )


def correct_ocr_errors(
    text: str,
    use_patterns: bool = True,
    use_spellcheck: bool = True,
    aggressive: bool = False,
) -> CorrectionResult:
    """
    Apply OCR error corrections to text.

    Recommended usage for RAG pipelines:
    - Default settings for general use
    - aggressive=True only for severely degraded text

    Args:
        text: Text to correct
        use_patterns: Apply known pattern corrections (safe, fast)
        use_spellcheck: Apply spell-check corrections (more aggressive)
        aggressive: Use aggressive spell-check settings

    Returns:
        CorrectionResult with all corrections applied
    """
    all_changes: list[tuple[str, str]] = []
    result = text
    confidence = 1.0

    if use_patterns:
        pattern_result = correct_known_patterns(result)
        result = pattern_result.corrected_text
        all_changes.extend(pattern_result.changes_made)
        confidence = min(confidence, pattern_result.confidence)

    if use_spellcheck:
        spell_result = correct_with_spellcheck(
            result,
            min_word_length=3 if aggressive else 4,
            skip_capitalized=not aggressive,
        )
        result = spell_result.corrected_text
        all_changes.extend(spell_result.changes_made)
        confidence = min(confidence, spell_result.confidence)

    return CorrectionResult(
        original_text=text,
        corrected_text=result,
        changes_made=all_changes,
        confidence=confidence,
    )


# ============================================================================
# Normalizer Interface (for future pipeline integration)
# ============================================================================


class OCRCorrectionNormalizer:
    """
    Normalizer for OCR correction in the ScholarDoc pipeline.

    This can be added to the normalizer chain to automatically
    correct OCR errors during document processing.

    Usage:
        normalizer = OCRCorrectionNormalizer(
            min_quality=0.8,
            auto_correct=True,
        )
        # When integrated with pipeline:
        # corrected_doc = normalizer.normalize(raw_doc)
    """

    def __init__(
        self,
        min_quality: float = 0.8,
        auto_correct: bool = True,
        use_spellcheck: bool = True,
        aggressive: bool = False,
        quality_callback: Callable[[OCRQualityScore], None] | None = None,
    ):
        """
        Initialize OCR correction normalizer.

        Args:
            min_quality: Minimum quality score to skip correction
            auto_correct: Whether to automatically apply corrections
            use_spellcheck: Whether to use spell checker
            aggressive: Use aggressive correction settings
            quality_callback: Optional callback for quality scores
        """
        self.min_quality = min_quality
        self.auto_correct = auto_correct
        self.use_spellcheck = use_spellcheck
        self.aggressive = aggressive
        self.quality_callback = quality_callback

    def process_text(self, text: str) -> tuple[str, OCRQualityScore, CorrectionResult | None]:
        """
        Process text through OCR quality check and optional correction.

        Args:
            text: Text to process

        Returns:
            Tuple of (processed_text, quality_score, correction_result)
        """
        # Score quality
        quality = score_ocr_quality(text, spell_check=self.use_spellcheck)

        if self.quality_callback:
            self.quality_callback(quality)

        # Skip correction if quality is good enough
        if quality.overall_score >= self.min_quality and not quality.needs_correction:
            return text, quality, None

        # Apply correction if enabled
        if self.auto_correct:
            correction = correct_ocr_errors(
                text,
                use_patterns=True,
                use_spellcheck=self.use_spellcheck,
                aggressive=self.aggressive,
            )
            return correction.corrected_text, quality, correction

        return text, quality, None
