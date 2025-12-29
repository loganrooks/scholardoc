"""
OCR error detection using spellcheck with scholarly vocabulary filtering.

This module detects potential OCR errors by flagging words that:
- Are not in the base dictionary
- Do not pass morphological validation
- Are not in the scholarly vocabulary whitelist

Architecture Decision: ADR-002 (spellcheck as selector, not corrector)
Flagged words are passed to re-OCR, not auto-corrected.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from scholardoc.ocr.dictionary import AdaptiveDictionary

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Minimum word length to consider for detection
MIN_WORD_LENGTH = 2

# Pattern to extract words from text
WORD_EXTRACTION_PATTERN = re.compile(r"\b[\w']+\b")

# Scholarly vocabulary to skip (reduces false positives)
# German philosophy
GERMAN_TERMS = frozenset(
    {
        "dasein",
        "ereignis",
        "aufhebung",
        "zeitlichkeit",
        "vorhandenheit",
        "zuhandenheit",
        "gestell",
        "geworfenheit",
        "befindlichkeit",
        "augenblick",
        "eigentlichkeit",
        "uneigentlichkeit",
        "mitsein",
        "verstehen",
        "sorge",
        "angst",
        "furcht",
        "rede",
        "gerede",
        "verfallenheit",
        "schuld",
        "gewissen",
        "entschlossenheit",
        "wiederholung",
        "geschichtlichkeit",
        "weltlichkeit",
        "umwelt",
        "mitwelt",
        "selbstwelt",
        "innerweltlich",
        "vorhandensein",
        "zuhandensein",
        "bewandtnis",
        "bedeutsamkeit",
        "erschlossenheit",
        "befinden",
        "stimmung",
        "entwurf",
        "faktizität",
        # Common German words in philosophy texts
        "über",
        "für",
        "und",
        "oder",
        "mit",
        "bei",
        "nach",
        "von",
        "nicht",
        "als",
        "sein",
        "haben",
        "werden",
        "können",
        "müssen",
        "sollen",
        "wollen",
        "dürfen",
        "mögen",
        "lassen",
    }
)

# French philosophy
FRENCH_TERMS = frozenset(
    {
        "différance",
        "aporia",
        "pharmakon",
        "arche",
        "telos",
        "jouissance",
        "bricolage",
        "deconstruction",
        "logocentrism",
        "phallogocentrism",
        "supplementarity",
        "iterability",
        "dissemination",
        "trace",
        "erasure",
        "sous rature",
        # Common French words
        "être",
        "avoir",
        "faire",
        "dire",
        "voir",
        "savoir",
        "pouvoir",
        "vouloir",
        "devoir",
        "falloir",
        "aller",
        "venir",
        "prendre",
        "liberté",
        "égalité",
        "fraternité",
    }
)

# Latin terms
LATIN_TERMS = frozenset(
    {
        "priori",
        "posteriori",
        "generis",
        "alia",
        "fortiori",
        "initio",
        "facto",
        "jure",
        "nihilo",
        "absurdo",
        "infinitum",
        "limine",
        "extremis",
        "situ",
        "vitro",
        "vivo",
        "ante",
        "bellum",
        "post",
        "mortem",
        "passim",
        "ibid",
        "idem",
        "circa",
        "sic",
        "viz",
        "ergo",
        "ipso",
        "per",
        "via",
        "versus",
        "vice",
        "versa",
        "qua",
        "quasi",
        "status",
        "quo",
    }
)

# Greek terms
GREEK_TERMS = frozenset(
    {
        "logos",
        "noesis",
        "phronesis",
        "techne",
        "aletheia",
        "eidos",
        "episteme",
        "doxa",
        "pragma",
        "praxis",
        "theoria",
        "nous",
        "psyche",
        "polis",
        "ethos",
        "pathos",
        "telos",
        "arche",
        "ousia",
        "energeia",
        "dynamis",
        "entelechy",
        "hyle",
        "morphe",
        "kinesis",
        "genesis",
        "physis",
    }
)

# Combined scholarly vocabulary
SCHOLARLY_VOCAB = GERMAN_TERMS | FRENCH_TERMS | LATIN_TERMS | GREEK_TERMS


# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass
class OCRErrorCandidate:
    """A word flagged as potential OCR error."""

    word: str
    original_word: str  # With punctuation
    position: int  # Word index in text
    confidence: float  # How confident we are this is an error (0-1)
    reason: str
    exclude_from_reocr: bool = False  # True if handled by text processing


@dataclass
class DetectionStats:
    """Statistics for error detection."""

    words_checked: int = 0
    errors_detected: int = 0
    skipped_short: int = 0
    skipped_scholarly: int = 0
    skipped_valid: int = 0


# =============================================================================
# OCR ERROR DETECTOR
# =============================================================================


class OCRErrorDetector:
    """
    Detects OCR errors using spellcheck with scholarly vocabulary filter.

    This detector flags words for re-OCR rather than auto-correcting them.
    It filters out:
    - Short words (< 2 chars)
    - Scholarly vocabulary (German, French, Latin, Greek terms)
    - Words in the base dictionary

    Attributes:
        dictionary: AdaptiveDictionary for word validation.
        scholarly_vocab: Set of scholarly terms to skip.
        additional_vocab: Optional additional vocabulary to skip.

    Example:
        >>> from scholardoc.ocr.detector import OCRErrorDetector
        >>> from scholardoc.ocr.dictionary import AdaptiveDictionary
        >>> detector = OCRErrorDetector(AdaptiveDictionary())
        >>> errors = detector.detect_errors("The phiinomenon of tbe world")
        >>> [e.word for e in errors]
        ['phiinomenon', 'tbe']
    """

    def __init__(
        self,
        dictionary: AdaptiveDictionary,
        additional_vocab: set[str] | None = None,
    ):
        """
        Initialize the detector.

        Args:
            dictionary: AdaptiveDictionary for word validation.
            additional_vocab: Optional additional vocabulary to skip.
        """
        self.dictionary = dictionary
        self.scholarly_vocab = SCHOLARLY_VOCAB
        if additional_vocab:
            self.scholarly_vocab = self.scholarly_vocab | additional_vocab

    def _normalize_word(self, word: str) -> str:
        """
        Normalize a word for comparison.

        Applies Unicode NFC normalization and lowercasing.

        Args:
            word: Word to normalize.

        Returns:
            Normalized word.
        """
        # NFC normalization ensures ü is U+00FC, not U+0075 U+0308
        normalized = unicodedata.normalize("NFC", word)
        return normalized.lower()

    def _clean_word(self, word: str) -> str:
        """
        Clean a word by removing punctuation.

        Args:
            word: Word to clean.

        Returns:
            Cleaned word (lowercase, no punctuation).
        """
        # Remove non-word characters except apostrophes
        clean = re.sub(r"[^\w']", "", word)
        # Remove leading/trailing apostrophes
        clean = clean.strip("'")
        return self._normalize_word(clean)

    def is_error(self, word: str) -> bool:
        """
        Check if a single word is likely an OCR error.

        Args:
            word: Word to check.

        Returns:
            True if word is likely an OCR error.
        """
        clean = self._clean_word(word)

        # Skip short words
        if len(clean) < MIN_WORD_LENGTH:
            return False

        # Skip scholarly vocabulary
        if clean in self.scholarly_vocab:
            return False

        # Check if known in dictionary
        # Note: We deliberately don't use is_probably_word() here
        if self.dictionary.is_known_word(clean):
            return False

        return True

    def detect_errors(
        self,
        text: str,
        page_num: int = 0,
    ) -> list[OCRErrorCandidate]:
        """
        Detect potential OCR errors in text.

        Args:
            text: Text to analyze.
            page_num: Optional page number for position tracking.

        Returns:
            List of OCRErrorCandidate objects for flagged words.

        Example:
            >>> detector = OCRErrorDetector(AdaptiveDictionary())
            >>> errors = detector.detect_errors("phenomenology is importnt")
            >>> len(errors)
            1
            >>> errors[0].word
            'importnt'
        """
        if text is None:
            raise ValueError("Input text cannot be None")

        if not text.strip():
            return []

        errors = []
        words = text.split()

        for i, word in enumerate(words):
            # Clean word
            clean = self._clean_word(word)

            if len(clean) < MIN_WORD_LENGTH:
                continue

            # Skip scholarly vocabulary
            if clean in self.scholarly_vocab:
                continue

            # Check if known in dictionary
            # Note: We deliberately don't use is_probably_word() here to avoid
            # false negatives from morphological analysis (e.g., "beening" passes
            # because "been" + "ing" looks valid, but it's not a real word)
            if self.dictionary.is_known_word(clean):
                continue

            # Flag as error - use pattern check for confidence scoring
            _, conf = self.dictionary.is_probably_word(clean)

            errors.append(
                OCRErrorCandidate(
                    word=clean,
                    original_word=word,
                    position=i,
                    confidence=1.0 - conf,
                    reason="Unknown word",
                )
            )

        return errors

    def detect_errors_with_stats(
        self,
        text: str,
        page_num: int = 0,
    ) -> tuple[list[OCRErrorCandidate], DetectionStats]:
        """
        Detect errors and return statistics.

        Args:
            text: Text to analyze.
            page_num: Optional page number for position tracking.

        Returns:
            Tuple of (errors, statistics).
        """
        if text is None:
            raise ValueError("Input text cannot be None")

        stats = DetectionStats()

        if not text.strip():
            return [], stats

        errors = []
        words = text.split()

        for i, word in enumerate(words):
            stats.words_checked += 1

            # Clean word
            clean = self._clean_word(word)

            if len(clean) < MIN_WORD_LENGTH:
                stats.skipped_short += 1
                continue

            # Skip scholarly vocabulary
            if clean in self.scholarly_vocab:
                stats.skipped_scholarly += 1
                continue

            # Check if known in dictionary
            # Note: We deliberately don't use is_probably_word() here
            if self.dictionary.is_known_word(clean):
                stats.skipped_valid += 1
                continue

            # Flag as error - use pattern check for confidence scoring
            _, conf = self.dictionary.is_probably_word(clean)

            errors.append(
                OCRErrorCandidate(
                    word=clean,
                    original_word=word,
                    position=i,
                    confidence=1.0 - conf,
                    reason="Unknown word",
                )
            )
            stats.errors_detected += 1

        return errors, stats

    def get_scholarly_vocab_size(self) -> int:
        """Get the number of terms in scholarly vocabulary."""
        return len(self.scholarly_vocab)
