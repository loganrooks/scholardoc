"""
Adaptive Dictionary for OCR error detection.

This module provides a dictionary that learns likely words with safeguards
against learning OCR errors. Uses hybrid validation combining:
- Base dictionary lookup (pyspellchecker)
- Morphological analysis (suffixes, prefixes)
- Pattern validation (character patterns, vowels)

Architecture Decision: ADR-002 (spellcheck as selector, not corrector)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from spellchecker import SpellChecker

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Thresholds for word learning and validation
DEFAULT_MIN_CONFIDENCE_TO_USE = 0.7
DEFAULT_MIN_OCCURRENCES_TO_LEARN = 2
MIN_WORD_LENGTH = 2
MAX_WORD_LENGTH = 30
MIN_BASE_WORD_LENGTH = 3  # For suffix/prefix stripping

# Allowed characters in words (includes common diacritics)
WORD_PATTERN = re.compile(r"^[a-zA-ZäöüÄÖÜßàâçéèêëîïôùûü]+$")
VOWEL_PATTERN = re.compile(r"[aeiouäöü]", re.IGNORECASE)
TRIPLE_LETTER_PATTERN = re.compile(r"(.)\1\1")

# Morphological suffixes with confidence scores
SUFFIXES = [
    ("s", 0.9),  # plurals
    ("es", 0.9),  # plurals
    ("ed", 0.85),  # past tense
    ("ing", 0.85),  # gerund
    ("ly", 0.8),  # adverbs
    ("tion", 0.7),  # nominalizations
    ("ment", 0.7),  # nominalizations
    ("ness", 0.7),  # nominalizations
    ("ity", 0.7),  # nominalizations
    ("al", 0.6),  # adjectives
    ("ive", 0.6),  # adjectives
    ("ous", 0.6),  # adjectives
    ("izes", 0.85),  # verb forms (temporalizes -> temporal)
    ("ises", 0.85),  # British verb forms
    ("ized", 0.85),  # past tense verbs
    ("ised", 0.85),  # British past tense
    ("izing", 0.85),  # gerund verbs
    ("ising", 0.85),  # British gerund
]

# Morphological prefixes with confidence scores
PREFIXES = [
    ("un", 0.8),
    ("re", 0.8),
    ("pre", 0.7),
    ("non", 0.7),
    ("anti", 0.6),
    ("over", 0.6),
    ("under", 0.6),
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass
class LearnedWordEntry:
    """Entry for a learned word with metadata."""

    confidence: float
    occurrences: int
    contexts: list[str]
    source: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "confidence": self.confidence,
            "occurrences": self.occurrences,
            "contexts": self.contexts,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LearnedWordEntry:
        """Create from dictionary."""
        return cls(
            confidence=data.get("confidence", 0.5),
            occurrences=data.get("occurrences", 1),
            contexts=data.get("contexts", []),
            source=data.get("source", "unknown"),
        )


# =============================================================================
# ADAPTIVE DICTIONARY
# =============================================================================


@dataclass
class AdaptiveDictionary:
    """
    Dictionary that learns likely words with safeguards against learning OCR errors.

    This class implements hybrid validation combining multiple sources:
    1. Base dictionary lookup (pyspellchecker)
    2. Morphological analysis (suffixes like -s, -ed, -ing; prefixes like un-, re-)
    3. Pattern validation (valid characters, vowels, reasonable length)

    Safeguards against learning OCR errors:
    1. Word must pass character pattern validation (no weird chars)
    2. Word should have morphological evidence (base form exists)
    3. Words are stored with confidence scores
    4. Minimum occurrences before treating as fully valid

    Attributes:
        base_spell: Optional SpellChecker instance for base dictionary lookup.
        learned_words: Dictionary of learned words with metadata.
        persistence_path: Optional path for persisting learned words.
        min_confidence_to_use: Minimum confidence to consider a learned word valid.
        min_occurrences_to_learn: Minimum occurrences before learning a word.

    Example:
        >>> from scholardoc.ocr.dictionary import AdaptiveDictionary
        >>> ad = AdaptiveDictionary()
        >>> ad.is_known_word("cognitions")  # plural of known word
        True
        >>> ad.is_known_word("asdfghjkl")  # random chars
        False
        >>> is_valid, confidence = ad.is_probably_word("temporalizes")
        >>> is_valid
        True
    """

    base_spell: SpellChecker | None = field(default=None)
    learned_words: dict[str, LearnedWordEntry] = field(default_factory=dict)
    persistence_path: Path | None = None
    min_confidence_to_use: float = DEFAULT_MIN_CONFIDENCE_TO_USE
    min_occurrences_to_learn: int = DEFAULT_MIN_OCCURRENCES_TO_LEARN

    def __post_init__(self) -> None:
        """Initialize base dictionary and load persisted words."""
        # Initialize base spellchecker if not provided
        if self.base_spell is None:
            try:
                from spellchecker import SpellChecker

                self.base_spell = SpellChecker()
                logger.debug("Initialized base spellchecker")
            except ImportError:
                logger.warning(
                    "pyspellchecker not available; "
                    "dictionary validation will be limited to pattern/morphology"
                )
                self.base_spell = None

        # Load persisted learned words
        if self.persistence_path and self.persistence_path.exists():
            self._load_learned_words()

    def _load_learned_words(self) -> None:
        """Load learned words from persistence file."""
        if not self.persistence_path:
            return

        try:
            with open(self.persistence_path) as f:
                data = json.load(f)
                raw_words = data.get("learned_words", {})
                self.learned_words = {
                    word: LearnedWordEntry.from_dict(entry) for word, entry in raw_words.items()
                }
            logger.info(
                "Loaded %d learned words from %s",
                len(self.learned_words),
                self.persistence_path,
            )
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load learned words: %s", e)
            self.learned_words = {}

    def is_known_word(self, word: str) -> bool:
        """
        Check if word is known (base dict or learned with high confidence).

        Args:
            word: The word to check (case-insensitive).

        Returns:
            True if the word is in the base dictionary or learned with
            sufficient confidence.

        Example:
            >>> ad = AdaptiveDictionary()
            >>> ad.is_known_word("philosophy")
            True
            >>> ad.is_known_word("asdfghjkl")
            False
        """
        w = word.lower()

        # Check base dictionary
        if self.base_spell is not None and w in self.base_spell:
            return True

        # Check learned words with sufficient confidence
        if w in self.learned_words:
            entry = self.learned_words[w]
            return entry.confidence >= self.min_confidence_to_use

        return False

    def is_probably_word(self, word: str) -> tuple[bool, float]:
        """
        Hybrid validation: check if word is probably valid.

        Combines multiple validation sources:
        1. Direct dictionary lookup (confidence 1.0)
        2. Morphological analysis (e.g., "cognitions" -> "cognition" + "s")
        3. Pattern validation (valid characters, has vowels, etc.)

        Args:
            word: The word to validate (case-insensitive).

        Returns:
            Tuple of (is_valid, confidence) where is_valid is True if
            confidence >= 0.5.

        Example:
            >>> ad = AdaptiveDictionary()
            >>> is_valid, conf = ad.is_probably_word("temporalizes")
            >>> is_valid
            True
            >>> conf > 0.5
            True
        """
        w = word.lower()
        confidence = 0.0

        # Direct match is highest confidence
        if self.is_known_word(w):
            return True, 1.0

        # Morphological checks
        morphological_score = self._check_morphology(w)
        if morphological_score > 0:
            confidence = max(confidence, morphological_score)

        # Pattern check (looks like a word)
        pattern_score = self._check_pattern(w)
        confidence = min(confidence + pattern_score * 0.3, 1.0)

        return confidence >= 0.5, confidence

    def _check_morphology(self, word: str) -> float:
        """
        Check if base forms exist in dictionary.

        Strips common suffixes and prefixes to find base forms.

        Args:
            word: The word to analyze (lowercase).

        Returns:
            Confidence score (0.0 to 1.0) based on morphological evidence.
        """
        if self.base_spell is None:
            return 0.0

        # Check suffixes
        for suffix, score in SUFFIXES:
            if word.endswith(suffix) and len(word) > len(suffix) + MIN_BASE_WORD_LENGTH:
                base = word[: -len(suffix)]
                if base in self.base_spell:
                    return score
                # Handle consonant doubling ONLY for -ing and -ed
                # (e.g., "occurring" -> "occur", "stopped" -> "stop")
                # NOT for plurals like "mands" which would wrongly match "man"
                if suffix in ("ing", "ed") and len(base) >= 2:
                    if base.endswith(base[-1]) and base[:-1] in self.base_spell:
                        return score * 0.9
                # Handle -ize/-ise verbs (temporalizes -> temporal -> temporalize)
                if suffix in ("izes", "ises", "ized", "ised", "izing", "ising"):
                    # Check if base + 'ize' or base + 'ise' is reasonable
                    if base + "ize" in self.base_spell or base + "ise" in self.base_spell:
                        return score
                    # Or if base itself is an adjective (temporal -> temporalize)
                    if base in self.base_spell:
                        return score

        # Check prefixes
        for prefix, score in PREFIXES:
            if word.startswith(prefix) and len(word) > len(prefix) + MIN_BASE_WORD_LENGTH:
                rest = word[len(prefix) :]
                if rest in self.base_spell:
                    return score

        return 0.0

    def _check_pattern(self, word: str) -> float:
        """
        Check if word follows valid patterns.

        Validates:
        - Contains only allowed characters (letters + common diacritics)
        - Reasonable length
        - No triple letters (common OCR error)
        - Has vowels (probably pronounceable)

        Args:
            word: The word to validate (any case).

        Returns:
            Pattern score (0.0 to 0.7) based on pattern validity.
        """
        # Must be all letters (allow some diacritics)
        if not WORD_PATTERN.match(word):
            return 0.0

        # Reasonable length
        if len(word) < MIN_WORD_LENGTH or len(word) > MAX_WORD_LENGTH:
            return 0.0

        # No triple letters (usually OCR error)
        if TRIPLE_LETTER_PATTERN.search(word):
            return 0.0

        # Has vowels (probably pronounceable)
        if not VOWEL_PATTERN.search(word):
            return 0.2  # Low confidence for consonant-only

        return 0.7

    def maybe_learn(self, word: str, context: str = "") -> bool:
        """
        Consider learning a new word with safeguards.

        Applies safeguards before learning:
        - Pattern validation (no weird chars)
        - Not already in base dictionary
        - Updates existing entries with occurrence counts

        Args:
            word: The word to potentially learn (case-insensitive).
            context: Optional context string for debugging.

        Returns:
            True if word was learned or updated, False otherwise.

        Example:
            >>> ad = AdaptiveDictionary()
            >>> ad.maybe_learn("nonexperiential", "found in philosophy text")
            True
        """
        w = word.lower()

        # Don't learn if already in base dictionary
        if self.base_spell is not None and w in self.base_spell:
            return False

        # Validate pattern
        pattern_score = self._check_pattern(w)
        if pattern_score < 0.5:
            return False

        # Check morphology
        morph_score = self._check_morphology(w)

        # Calculate confidence
        confidence = (pattern_score + morph_score) / 2

        # Update or create entry
        if w in self.learned_words:
            entry = self.learned_words[w]
            entry.occurrences += 1
            entry.confidence = min(entry.confidence + 0.1, 1.0)
            if context:
                entry.contexts.append(context[:50])
            logger.debug("Updated learned word '%s': occurrences=%d", w, entry.occurrences)
        else:
            self.learned_words[w] = LearnedWordEntry(
                confidence=confidence,
                occurrences=1,
                contexts=[context[:50]] if context else [],
                source="auto_learned",
            )
            logger.debug("Learned new word '%s': confidence=%.2f", w, confidence)

        return True

    def save(self) -> None:
        """
        Persist learned words to disk.

        Saves to the path specified in persistence_path. If no path is set,
        this method does nothing.

        Raises:
            OSError: If the file cannot be written.
        """
        if not self.persistence_path:
            logger.debug("No persistence path set; skipping save")
            return

        try:
            # Ensure parent directory exists
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.persistence_path, "w") as f:
                json.dump(
                    {
                        "learned_words": {
                            word: entry.to_dict() for word, entry in self.learned_words.items()
                        },
                        "version": "1.0",
                    },
                    f,
                    indent=2,
                )
            logger.info(
                "Saved %d learned words to %s",
                len(self.learned_words),
                self.persistence_path,
            )
        except OSError as e:
            logger.error("Failed to save learned words: %s", e)
            raise

    def clear_learned_words(self) -> None:
        """Clear all learned words."""
        self.learned_words.clear()
        logger.info("Cleared all learned words")
