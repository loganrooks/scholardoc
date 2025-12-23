"""
OCR Pipeline for ScholarDoc.

This module provides the validated OCR correction pipeline based on ADR-002 and ADR-003:
- Spellcheck as SELECTOR for what needs re-OCR (not auto-correction)
- Line-break rejoining with block-based filtering
- Adaptive dictionary with morphological validation
- Detection rate: 99.2% on validation set

Architecture (see ADR-002):
    STAGE 1: Line-Break Rejoining (position-based, block-filtered)
    STAGE 2: OCR Error Detection (spellcheck flags, does NOT correct)
    STAGE 3: Selective Re-OCR (line-level, external - not in this module)

Usage:
    from scholardoc.normalizers.ocr_pipeline import OCRPipeline

    pipeline = OCRPipeline()

    # Process a PDF page
    line_breaks = pipeline.detect_line_breaks(pdf_page)
    errors = pipeline.detect_errors(text, page_num=0)

    # Get words that need re-OCR
    words_for_reocr = pipeline.get_reocr_candidates(errors)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import fitz

try:
    from spellchecker import SpellChecker

    SPELLCHECK_AVAILABLE = True
except ImportError:
    SpellChecker = None  # type: ignore
    SPELLCHECK_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# ADAPTIVE DICTIONARY
# =============================================================================


@dataclass
class AdaptiveDictionary:
    """
    Dictionary that learns likely words with safeguards against learning OCR errors.

    This is a hybrid validation system that combines:
    1. Base dictionary lookup (pyspellchecker)
    2. Morphological analysis (plurals, verb forms, prefixes)
    3. Pattern validation (character patterns, vowel presence)
    4. Learned vocabulary with confidence scoring

    Safeguards against learning OCR errors:
    - Word must pass character pattern validation
    - Word must have morphological evidence (base form exists)
    - Confidence thresholds for using learned words
    - Frequency tracking for learned words

    See ADR-002 for design rationale.
    """

    base_spell: Any = field(default=None)
    learned_words: dict[str, dict[str, Any]] = field(default_factory=dict)
    persistence_path: Path | None = None

    # Thresholds
    min_confidence_to_use: float = 0.7
    min_occurrences_to_learn: int = 2

    def __post_init__(self) -> None:
        if self.base_spell is None and SPELLCHECK_AVAILABLE:
            self.base_spell = SpellChecker()

        # Load persisted learned words
        if self.persistence_path and self.persistence_path.exists():
            try:
                with open(self.persistence_path) as f:
                    data = json.load(f)
                    self.learned_words = data.get("learned_words", {})
                logger.debug(f"Loaded {len(self.learned_words)} learned words")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Could not load learned words: {e}")

    def is_known_word(self, word: str) -> bool:
        """Check if word is known (base dict or learned with high confidence)."""
        w = word.lower()

        # Check base dictionary
        if self.base_spell and w in self.base_spell:
            return True

        # Check learned words with sufficient confidence
        if w in self.learned_words:
            return self.learned_words[w].get("confidence", 0) >= self.min_confidence_to_use

        return False

    def is_probably_word(self, word: str) -> tuple[bool, float]:
        """
        Hybrid validation: check if word is probably valid.

        Returns:
            Tuple of (is_valid, confidence) where confidence is 0.0-1.0
        """
        w = word.lower()
        confidence = 0.0

        # Direct match
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
        """Check if base forms exist in dictionary."""
        if not self.base_spell:
            return 0.0

        # Common suffixes to strip with confidence scores
        suffixes = [
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

        for suffix, score in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                base = word[: -len(suffix)]
                if base in self.base_spell:
                    return score
                # Handle doubling (e.g., "occurring" -> "occur")
                if base.endswith(base[-1]) and base[:-1] in self.base_spell:
                    return score * 0.9
                # Handle -ize/-ise verbs
                if suffix in ("izes", "ises", "ized", "ised", "izing", "ising"):
                    if base + "ize" in self.base_spell or base + "ise" in self.base_spell:
                        return score
                    if base in self.base_spell:
                        return score

        # Prefixes
        prefixes = [
            ("un", 0.8),
            ("re", 0.8),
            ("pre", 0.7),
            ("non", 0.7),
            ("anti", 0.6),
            ("over", 0.6),
            ("under", 0.6),
        ]

        for prefix, score in prefixes:
            if word.startswith(prefix) and len(word) > len(prefix) + 2:
                rest = word[len(prefix) :]
                if rest in self.base_spell:
                    return score

        return 0.0

    def _check_pattern(self, word: str) -> float:
        """Check if word follows valid character patterns."""
        # Must be all letters (allow some diacritics)
        if not re.match(r"^[a-zA-ZäöüÄÖÜßàâçéèêëîïôùûü]+$", word):
            return 0.0

        # Reasonable length
        if len(word) < 2 or len(word) > 30:
            return 0.0

        # No triple letters (usually OCR error)
        if re.search(r"(.)\1\1", word):
            return 0.0

        # Has vowels (probably pronounceable)
        if not re.search(r"[aeiouäöü]", word.lower()):
            return 0.2  # Low confidence for consonant-only

        return 0.7

    def maybe_learn(self, word: str, context: str = "") -> bool:
        """
        Consider learning a new word with safeguards.

        Args:
            word: The word to potentially learn
            context: Optional context for debugging/auditing

        Returns:
            True if word was learned or updated
        """
        w = word.lower()

        # Don't learn if already in base dictionary
        if self.base_spell and w in self.base_spell:
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
            entry["occurrences"] = entry.get("occurrences", 0) + 1
            entry["confidence"] = min(entry["confidence"] + 0.1, 1.0)
            if context:
                contexts = entry.get("contexts", [])
                contexts.append(context[:50])
                entry["contexts"] = contexts[-5:]  # Keep last 5 contexts
        else:
            self.learned_words[w] = {
                "confidence": confidence,
                "occurrences": 1,
                "contexts": [context[:50]] if context else [],
                "source": "auto_learned",
            }

        return True

    def save(self) -> None:
        """Persist learned words to disk."""
        if self.persistence_path:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.persistence_path, "w") as f:
                json.dump({"learned_words": self.learned_words, "version": "1.0"}, f, indent=2)
            logger.debug(f"Saved {len(self.learned_words)} learned words")


# =============================================================================
# LINE-BREAK REJOINER
# =============================================================================


@dataclass
class LineBreakCandidate:
    """A potential line-break hyphenation to rejoin."""

    fragment1: str  # Word ending with hyphen
    fragment2: str  # First word of next line
    joined: str  # Rejoined word
    confidence: float
    should_join: bool
    reason: str


class LineBreakRejoiner:
    """
    Detects and rejoins line-break hyphenations using PDF position data.

    Uses block-based filtering (ADR-003) to avoid matching margin content
    (page numbers, headers) with body text.

    Algorithm:
    1. Extract words with positions from PDF page
    2. Group by block number (PyMuPDF distinguishes text regions)
    3. Only consider hyphenated line breaks WITHIN the same block
    4. Validate joins against dictionary/morphology
    """

    def __init__(self, dictionary: AdaptiveDictionary) -> None:
        self.dictionary = dictionary

    def detect_from_pdf_page(self, page: fitz.Page) -> list[LineBreakCandidate]:
        """
        Detect line-break candidates from a PDF page.

        Only considers line breaks within the same block to avoid
        matching margin content (page numbers, headers) with body text.

        Args:
            page: PyMuPDF page object

        Returns:
            List of LineBreakCandidate objects
        """
        words = page.get_text("words")
        # Format: (x0, y0, x1, y1, word, block_no, line_no, word_no)

        # Group by line, keeping track of block
        lines: dict[tuple[int, int], list[dict[str, Any]]] = {}
        for w in words:
            x0, y0, x1, y1, text, block, line_no, word_no = w
            key = (int(block), int(line_no))
            if key not in lines:
                lines[key] = []
            lines[key].append(
                {"text": text, "x0": x0, "x1": x1, "y0": y0, "y1": y1, "block": int(block)}
            )

        # Sort lines by block first, then vertical position
        sorted_lines = sorted(
            lines.items(), key=lambda x: (x[0][0], x[1][0]["y0"] if x[1] else 0)
        )

        candidates = []
        prev_line: list[dict[str, Any]] | None = None
        prev_block: int | None = None

        for (block, _line_no), line_words in sorted_lines:
            if prev_line and line_words:
                # CRITICAL: Only consider line-break if in SAME block
                # This filters out margin content (page numbers, headers)
                if prev_block == block:
                    last_word = prev_line[-1]["text"]
                    first_word = line_words[0]["text"]

                    if last_word.endswith("-") and len(last_word) > 2:
                        candidate = self._evaluate_join(last_word, first_word)
                        candidates.append(candidate)

            prev_line = line_words
            prev_block = block

        return candidates

    def detect_from_text(self, text: str) -> list[LineBreakCandidate]:
        """
        Detect line-break candidates from plain text.

        Note: This is less accurate than PDF-based detection since it lacks
        position information. Use detect_from_pdf_page when possible.

        Args:
            text: Plain text with line breaks

        Returns:
            List of LineBreakCandidate objects
        """
        candidates = []
        lines = text.split("\n")

        for i in range(len(lines) - 1):
            line = lines[i].rstrip()
            next_line = lines[i + 1].lstrip()

            if line.endswith("-") and len(line) > 2 and next_line:
                # Get last word of current line and first word of next line
                words = line.split()
                next_words = next_line.split()

                if words and next_words:
                    candidate = self._evaluate_join(words[-1], next_words[0])
                    candidates.append(candidate)

        return candidates

    def _evaluate_join(self, fragment1: str, fragment2: str) -> LineBreakCandidate:
        """Evaluate whether two fragments should be joined."""
        # Clean the fragments
        clean_frag1 = fragment1.rstrip("-")
        clean_frag2 = re.sub(r"[^\w]", "", fragment2)  # Strip punctuation

        joined = clean_frag1 + clean_frag2

        # Check with hybrid validation
        is_valid, confidence = self.dictionary.is_probably_word(joined)

        # Position signal boost: hyphen at line end is strong evidence
        pattern_ok = bool(re.match(r"^[a-zA-ZäöüÄÖÜß]+$", joined))
        reasonable_length = 3 <= len(joined) <= 25

        if is_valid:
            should_join = True
            reason = "Valid word (dictionary/morphology)"
        elif pattern_ok and reasonable_length and confidence >= 0.3:
            should_join = True
            reason = "Looks like word + position signal"
            confidence = max(confidence, 0.6)  # Boost confidence
        else:
            should_join = False
            reason = "Failed validation"

        # Learn the word if we're joining with decent confidence
        if should_join and confidence >= 0.6:
            self.dictionary.maybe_learn(joined, f"line-break: {fragment1}+{fragment2}")

        return LineBreakCandidate(
            fragment1=fragment1,
            fragment2=fragment2,
            joined=joined,
            confidence=confidence,
            should_join=should_join,
            reason=reason,
        )

    def apply_to_text(self, text: str) -> str:
        """
        Apply line-break rejoining to text.

        Args:
            text: Text with potential line-break hyphenations

        Returns:
            Text with hyphenations rejoined where appropriate
        """
        candidates = self.detect_from_text(text)

        # Sort by position (reverse to apply from end)
        result = text
        for candidate in reversed(candidates):
            if candidate.should_join:
                # Replace "word-\nnext" with "wordnext"
                frag1_escaped = re.escape(candidate.fragment1)
                frag2_escaped = re.escape(candidate.fragment2)
                pattern = frag1_escaped + r"\s*\n\s*" + frag2_escaped
                result = re.sub(pattern, candidate.joined, result, count=1)

        return result


# =============================================================================
# OCR ERROR DETECTOR
# =============================================================================


@dataclass
class OCRErrorCandidate:
    """A word flagged as potential OCR error for re-OCR."""

    word: str
    position: tuple[int, int, int]  # (page, word_index, char_offset)
    confidence: float  # How confident we are this is an error (0.0-1.0)
    reason: str
    exclude_from_reocr: bool = False  # True if handled by text processing


# Default scholarly vocabulary to skip (reduces false positives)
DEFAULT_SCHOLARLY_VOCAB: frozenset[str] = frozenset(
    {
        # German philosophy
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
        "verlorenheit",
        "ursprüngliche",
        "eigentümlichen",
        "gewesen",
        "phänomen",
        "überhaupt",
        # French philosophy
        "différance",
        "aporia",
        "pharmakon",
        "arche",
        "telos",
        "sous",
        "rature",
        # Latin
        "priori",
        "posteriori",
        "generis",
        "alia",
        "modus",
        # Greek
        "logos",
        "noesis",
        "phronesis",
        "techne",
        "aletheia",
    }
)


class OCRErrorDetector:
    """
    Detects OCR errors using spellcheck with scholarly vocabulary filter.

    This detector FLAGS words for potential re-OCR but does NOT auto-correct.
    See ADR-002 for design rationale.

    The detection rate on the validation set is 99.2% with a 23.4% false positive
    rate (mostly German philosophical terms, which is acceptable for re-OCR).
    """

    def __init__(
        self,
        dictionary: AdaptiveDictionary,
        scholarly_vocab: frozenset[str] | None = None,
    ) -> None:
        """
        Initialize the detector.

        Args:
            dictionary: AdaptiveDictionary for word validation
            scholarly_vocab: Set of scholarly terms to skip (reduces false positives)
        """
        self.dictionary = dictionary
        self.scholarly_vocab = scholarly_vocab or DEFAULT_SCHOLARLY_VOCAB

    def detect_errors(self, text: str, page_num: int = 0) -> list[OCRErrorCandidate]:
        """
        Detect potential OCR errors in text.

        Args:
            text: Text to analyze
            page_num: Page number for position tracking

        Returns:
            List of OCRErrorCandidate objects for words that may need re-OCR
        """
        errors = []
        words = text.split()

        for i, word in enumerate(words):
            # Clean word
            clean = re.sub(r"[^\w]", "", word).lower()
            if len(clean) < 2:
                continue

            # Skip scholarly vocabulary
            if clean in self.scholarly_vocab:
                continue

            # Check if known
            if self.dictionary.is_known_word(clean):
                continue

            # Check if probably valid
            is_valid, conf = self.dictionary.is_probably_word(clean)
            if is_valid:
                continue

            # Flag as error
            errors.append(
                OCRErrorCandidate(
                    word=word,
                    position=(page_num, i, 0),
                    confidence=1.0 - conf,
                    reason="Unknown word",
                )
            )

        return errors


# =============================================================================
# OCR PIPELINE FACADE
# =============================================================================


class OCRPipeline:
    """
    Main facade for the OCR correction pipeline.

    This class orchestrates the validated OCR pipeline stages:
    1. Line-break rejoining (position-based, block-filtered)
    2. OCR error detection (spellcheck flags, does NOT correct)

    Stage 3 (selective re-OCR) is external to this module since it requires
    image processing (TrOCR/Tesseract).

    Example:
        pipeline = OCRPipeline()

        # Process PDF page
        page = doc[0]  # PyMuPDF page
        line_breaks = pipeline.detect_line_breaks(page)
        text = pipeline.apply_line_breaks(page.get_text())

        # Detect errors for re-OCR
        errors = pipeline.detect_errors(text)
        words_needing_reocr = [e.word for e in errors]
    """

    def __init__(
        self,
        persistence_path: Path | None = None,
        scholarly_vocab: frozenset[str] | None = None,
    ) -> None:
        """
        Initialize the OCR pipeline.

        Args:
            persistence_path: Optional path to persist learned vocabulary
            scholarly_vocab: Optional set of scholarly terms to skip
        """
        self.dictionary = AdaptiveDictionary(persistence_path=persistence_path)
        self.line_break_rejoiner = LineBreakRejoiner(self.dictionary)
        self.error_detector = OCRErrorDetector(self.dictionary, scholarly_vocab)

    def detect_line_breaks(self, page: fitz.Page) -> list[LineBreakCandidate]:
        """
        Detect line-break hyphenations in a PDF page.

        Args:
            page: PyMuPDF page object

        Returns:
            List of LineBreakCandidate objects
        """
        return self.line_break_rejoiner.detect_from_pdf_page(page)

    def detect_line_breaks_text(self, text: str) -> list[LineBreakCandidate]:
        """
        Detect line-break hyphenations in plain text.

        Note: Less accurate than PDF-based detection.

        Args:
            text: Plain text with line breaks

        Returns:
            List of LineBreakCandidate objects
        """
        return self.line_break_rejoiner.detect_from_text(text)

    def apply_line_breaks(self, text: str) -> str:
        """
        Apply line-break rejoining to text.

        Args:
            text: Text with potential hyphenations

        Returns:
            Text with hyphenations rejoined where appropriate
        """
        return self.line_break_rejoiner.apply_to_text(text)

    def detect_errors(self, text: str, page_num: int = 0) -> list[OCRErrorCandidate]:
        """
        Detect potential OCR errors in text.

        Args:
            text: Text to analyze
            page_num: Page number for position tracking

        Returns:
            List of OCRErrorCandidate objects
        """
        return self.error_detector.detect_errors(text, page_num)

    def get_reocr_candidates(
        self, errors: list[OCRErrorCandidate]
    ) -> list[str]:
        """
        Get list of words that need re-OCR.

        Args:
            errors: List of detected errors

        Returns:
            List of words to send to re-OCR
        """
        return [e.word for e in errors if not e.exclude_from_reocr]

    def save_learned_vocabulary(self) -> None:
        """Persist learned vocabulary to disk."""
        self.dictionary.save()

    @property
    def learned_word_count(self) -> int:
        """Number of words learned during processing."""
        return len(self.dictionary.learned_words)
