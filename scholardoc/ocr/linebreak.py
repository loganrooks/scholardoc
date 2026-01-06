"""
Line-break hyphenation rejoiner.

This module detects and rejoins hyphenated words that span line breaks
using PyMuPDF position data for detection and the adaptive dictionary
for validation.

Architecture Decision: ADR-003 (block-based line-break detection)
Only considers line breaks within the same PyMuPDF block to avoid
matching margin content (page numbers, headers) with body text.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import fitz

from scholardoc.ocr.dictionary import AdaptiveDictionary

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Word pattern for validation
WORD_PATTERN = re.compile(r"^[a-zA-ZäöüÄÖÜß]+$")

# Confidence thresholds
MIN_CONFIDENCE_TO_JOIN = 0.3
POSITION_SIGNAL_BOOST = 0.6

# Length constraints
MIN_JOINED_LENGTH = 3
MAX_JOINED_LENGTH = 25
MIN_FRAGMENT_LENGTH = 2


# =============================================================================
# DATA STRUCTURES
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


@dataclass
class LineBreakStats:
    """Statistics for line-break processing."""

    candidates_found: int = 0
    candidates_joined: int = 0
    candidates_rejected: int = 0
    words_learned: int = 0


# =============================================================================
# LINE-BREAK REJOINER
# =============================================================================


class LineBreakRejoiner:
    """
    Detects and rejoins line-break hyphenations using position data.

    Hybrid approach:
    1. Position signal: hyphen at end of line within same block
    2. Validation: joined word passes dictionary/morphological checks
    3. Fallback: trust position if joining looks reasonable

    Block filtering (ADR-003): Only considers consecutive lines within
    the same PyMuPDF block. This prevents matching margin content
    (page numbers, headers, footnote markers) with body text.

    Attributes:
        dictionary: AdaptiveDictionary for word validation.
        learn_words: Whether to learn newly discovered words.

    Example:
        >>> from scholardoc.ocr.linebreak import LineBreakRejoiner
        >>> from scholardoc.ocr.dictionary import AdaptiveDictionary
        >>> rejoiner = LineBreakRejoiner(AdaptiveDictionary())
        >>> candidate = rejoiner.evaluate_join("phenom-", "enology")
        >>> candidate.should_join
        True
        >>> candidate.joined
        'phenomenology'
    """

    def __init__(
        self,
        dictionary: AdaptiveDictionary,
        learn_words: bool = True,
    ):
        """
        Initialize the rejoiner.

        Args:
            dictionary: AdaptiveDictionary for word validation.
            learn_words: Whether to learn newly discovered words.
        """
        self.dictionary = dictionary
        self.learn_words = learn_words

    def detect_from_pdf_page(self, page: fitz.Page) -> list[LineBreakCandidate]:
        """
        Detect line-break candidates from a PDF page.

        Uses PyMuPDF's word extraction with position data. Only considers
        line breaks within the same block (ADR-003) to avoid matching
        margin content with body text.

        Args:
            page: PyMuPDF page object.

        Returns:
            List of LineBreakCandidate objects.
        """
        words = page.get_text("words")
        # Format: (x0, y0, x1, y1, word, block_no, line_no, word_no)

        if not words:
            return []

        # Group by line, keeping track of block
        lines: dict[tuple[int, int], list[dict]] = {}
        for w in words:
            x0, y0, x1, y1, text, block, line_no, word_no = w
            key = (block, line_no)
            if key not in lines:
                lines[key] = []
            lines[key].append(
                {
                    "text": text,
                    "x0": x0,
                    "x1": x1,
                    "y0": y0,
                    "y1": y1,
                    "block": block,
                }
            )

        # Sort lines by block first, then vertical position
        # This keeps lines within the same block together
        sorted_lines = sorted(
            lines.items(),
            key=lambda x: (x[0][0], x[1][0]["y0"] if x[1] else 0),
        )

        candidates = []
        prev_line = None
        prev_block = None

        for (block, _line_no), line_words in sorted_lines:
            if prev_line and line_words:
                # CRITICAL: Only consider line-break if in SAME block
                # This filters out margin content (page numbers, headers)
                if prev_block == block:
                    last_word = prev_line[-1]["text"]
                    first_word = line_words[0]["text"]

                    # Check for hyphenation at line end
                    if last_word.endswith("-") and len(last_word) > MIN_FRAGMENT_LENGTH:
                        candidate = self.evaluate_join(last_word, first_word)
                        candidates.append(candidate)

            prev_line = line_words
            prev_block = block

        return candidates

    def evaluate_join(self, fragment1: str, fragment2: str) -> LineBreakCandidate:
        """
        Evaluate whether two fragments should be joined.

        Args:
            fragment1: Word ending with hyphen (e.g., "phenom-").
            fragment2: First word of next line (e.g., "enology").

        Returns:
            LineBreakCandidate with join decision.
        """
        # Clean the fragments
        clean_frag1 = fragment1.rstrip("-")
        clean_frag2 = re.sub(r"[^\w]", "", fragment2)  # Strip punctuation

        joined = clean_frag1 + clean_frag2

        # Validate length
        if len(joined) < MIN_JOINED_LENGTH or len(joined) > MAX_JOINED_LENGTH:
            return LineBreakCandidate(
                fragment1=fragment1,
                fragment2=fragment2,
                joined=joined,
                confidence=0.0,
                should_join=False,
                reason="Invalid length",
            )

        # Check with hybrid validation
        is_valid, confidence = self.dictionary.is_probably_word(joined)

        # Position signal boost: hyphen at line end is strong evidence
        # Even if validation fails, if it looks like a word, probably join
        pattern_ok = bool(WORD_PATTERN.match(joined))
        reasonable_length = MIN_JOINED_LENGTH <= len(joined) <= MAX_JOINED_LENGTH

        if is_valid:
            should_join = True
            reason = "Valid word (dictionary/morphology)"
        elif pattern_ok and reasonable_length and confidence >= MIN_CONFIDENCE_TO_JOIN:
            should_join = True
            reason = "Looks like word + position signal"
            confidence = max(confidence, POSITION_SIGNAL_BOOST)  # Boost confidence
        else:
            should_join = False
            reason = "Failed validation"

        # Learn the word if we're joining with decent confidence
        if should_join and self.learn_words and confidence >= POSITION_SIGNAL_BOOST:
            learned = self.dictionary.maybe_learn(joined, f"line-break: {fragment1}+{fragment2}")
            if learned:
                logger.debug("Learned word from line-break: %s", joined)

        return LineBreakCandidate(
            fragment1=fragment1,
            fragment2=fragment2,
            joined=joined,
            confidence=confidence,
            should_join=should_join,
            reason=reason,
        )

    def process_text(
        self,
        text: str,
        candidates: list[LineBreakCandidate] | None = None,
    ) -> tuple[str, LineBreakStats]:
        """
        Apply line-break rejoining to text.

        If candidates are provided, uses those. Otherwise, looks for
        hyphenation patterns in the text itself.

        Args:
            text: Text to process.
            candidates: Optional pre-detected candidates.

        Returns:
            Tuple of (processed_text, statistics).
        """
        stats = LineBreakStats()

        if candidates is None:
            # Simple pattern-based detection for plain text
            # Look for "word-\\n" patterns
            pattern = re.compile(r"(\w+)-\s*\n\s*(\w+)")
            candidates = []
            for match in pattern.finditer(text):
                fragment1 = match.group(1) + "-"
                fragment2 = match.group(2)
                candidate = self.evaluate_join(fragment1, fragment2)
                candidates.append(candidate)

        stats.candidates_found = len(candidates)

        # Apply rejoins
        result = text
        for candidate in candidates:
            if candidate.should_join:
                # Replace "fragment1\nfragment2" with "joined"
                # Handle various whitespace patterns
                pattern = re.compile(
                    re.escape(candidate.fragment1) + r"\s*" + re.escape(candidate.fragment2),
                    re.MULTILINE,
                )
                result = pattern.sub(candidate.joined, result)
                stats.candidates_joined += 1
            else:
                stats.candidates_rejected += 1

        return result, stats
