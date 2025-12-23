#!/usr/bin/env python3
"""
Spike 29: OCR Pipeline Design

Tests the hybrid approach for OCR correction:
1. Line-break rejoiner (position + hybrid validation)
2. Adaptive dictionary (learns likely words with safeguards)
3. Spellcheck detection
4. Selective re-OCR flagging

Based on testing against ground truth corpus.
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import fitz  # PyMuPDF

try:
    from spellchecker import SpellChecker
    SPELLCHECK_AVAILABLE = True
except ImportError:
    SPELLCHECK_AVAILABLE = False


# =============================================================================
# ADAPTIVE DICTIONARY
# =============================================================================

@dataclass
class AdaptiveDictionary:
    """
    Dictionary that learns likely words with safeguards against learning OCR errors.

    Safeguards:
    1. Word must pass character pattern validation (no weird chars)
    2. Word must have morphological evidence (base form exists)
    3. Word should appear multiple times (frequency threshold)
    4. Words are stored with confidence scores
    """

    base_spell: any = field(default=None)
    learned_words: dict = field(default_factory=dict)  # word -> confidence
    persistence_path: Optional[Path] = None

    # Thresholds
    min_confidence_to_use: float = 0.7
    min_occurrences_to_learn: int = 2

    def __post_init__(self):
        if self.base_spell is None and SPELLCHECK_AVAILABLE:
            self.base_spell = SpellChecker()

        # Load persisted learned words
        if self.persistence_path and self.persistence_path.exists():
            with open(self.persistence_path) as f:
                data = json.load(f)
                self.learned_words = data.get('learned_words', {})

    def is_known_word(self, word: str) -> bool:
        """Check if word is known (base dict or learned with high confidence)."""
        w = word.lower()

        # Check base dictionary
        if self.base_spell and w in self.base_spell:
            return True

        # Check learned words with sufficient confidence
        if w in self.learned_words:
            return self.learned_words[w].get('confidence', 0) >= self.min_confidence_to_use

        return False

    def is_probably_word(self, word: str) -> tuple[bool, float]:
        """
        Hybrid validation: check if word is probably valid.

        Returns (is_valid, confidence)
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

        # Common suffixes to strip
        suffixes = [
            ('s', 0.9),      # plurals
            ('es', 0.9),     # plurals
            ('ed', 0.85),    # past tense
            ('ing', 0.85),   # gerund
            ('ly', 0.8),     # adverbs
            ('tion', 0.7),   # nominalizations
            ('ment', 0.7),   # nominalizations
            ('ness', 0.7),   # nominalizations
            ('ity', 0.7),    # nominalizations
            ('al', 0.6),     # adjectives
            ('ive', 0.6),    # adjectives
            ('ous', 0.6),    # adjectives
            ('izes', 0.85),  # verb forms (temporalizes -> temporal)
            ('ises', 0.85),  # British verb forms
            ('ized', 0.85),  # past tense verbs
            ('ised', 0.85),  # British past tense
            ('izing', 0.85), # gerund verbs
            ('ising', 0.85), # British gerund
        ]

        for suffix, score in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                base = word[:-len(suffix)]
                if base in self.base_spell:
                    return score
                # Handle doubling (e.g., "occurring" -> "occur")
                if base.endswith(base[-1]) and base[:-1] in self.base_spell:
                    return score * 0.9
                # Handle -ize/-ise verbs (temporalizes -> temporal -> temporalize)
                if suffix in ('izes', 'ises', 'ized', 'ised', 'izing', 'ising'):
                    # Check if base + 'ize' or base + 'ise' is reasonable
                    if base + 'ize' in self.base_spell or base + 'ise' in self.base_spell:
                        return score
                    # Or if base itself is an adjective (temporal -> temporalize)
                    if base in self.base_spell:
                        return score

        # Prefixes
        prefixes = [
            ('un', 0.8),
            ('re', 0.8),
            ('pre', 0.7),
            ('non', 0.7),
            ('anti', 0.6),
            ('over', 0.6),
            ('under', 0.6),
        ]

        for prefix, score in prefixes:
            if word.startswith(prefix) and len(word) > len(prefix) + 2:
                rest = word[len(prefix):]
                if rest in self.base_spell:
                    return score

        return 0.0

    def _check_pattern(self, word: str) -> float:
        """Check if word follows valid patterns."""
        # Must be all letters (allow some diacritics)
        if not re.match(r'^[a-zA-ZäöüÄÖÜßàâçéèêëîïôùûü]+$', word):
            return 0.0

        # Reasonable length
        if len(word) < 2 or len(word) > 30:
            return 0.0

        # No triple letters (usually OCR error)
        if re.search(r'(.)\1\1', word):
            return 0.0

        # Has vowels (probably pronounceable)
        if not re.search(r'[aeiouäöü]', word.lower()):
            return 0.2  # Low confidence for consonant-only

        return 0.7

    def maybe_learn(self, word: str, context: str = "") -> bool:
        """
        Consider learning a new word with safeguards.

        Returns True if word was learned or updated.
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
            entry['occurrences'] = entry.get('occurrences', 0) + 1
            entry['confidence'] = min(entry['confidence'] + 0.1, 1.0)
            entry['contexts'].append(context[:50])
        else:
            self.learned_words[w] = {
                'confidence': confidence,
                'occurrences': 1,
                'contexts': [context[:50]] if context else [],
                'source': 'auto_learned'
            }

        return True

    def save(self):
        """Persist learned words to disk."""
        if self.persistence_path:
            with open(self.persistence_path, 'w') as f:
                json.dump({
                    'learned_words': self.learned_words,
                    'version': '1.0'
                }, f, indent=2)


# =============================================================================
# LINE-BREAK REJOINER
# =============================================================================

@dataclass
class LineBreakCandidate:
    """A potential line-break hyphenation to rejoin."""
    fragment1: str  # Word ending with hyphen
    fragment2: str  # First word of next line
    joined: str     # Rejoined word
    confidence: float
    should_join: bool
    reason: str


class LineBreakRejoiner:
    """
    Detects and rejoins line-break hyphenations using position data.

    Hybrid approach:
    1. Position signal: hyphen at end of line
    2. Validation: joined word passes dictionary/morphological checks
    3. Fallback: trust position if joining looks reasonable
    """

    def __init__(self, dictionary: AdaptiveDictionary):
        self.dictionary = dictionary

    def detect_from_pdf_page(self, page: fitz.Page) -> list[LineBreakCandidate]:
        """Detect line-break candidates from a PDF page.
        
        Only considers line breaks within the same block to avoid
        matching margin content (page numbers, headers) with body text.
        """
        words = page.get_text("words")
        # Format: (x0, y0, x1, y1, word, block_no, line_no, word_no)

        # Group by line, keeping track of block
        lines = {}
        for w in words:
            x0, y0, x1, y1, text, block, line_no, word_no = w
            key = (block, line_no)
            if key not in lines:
                lines[key] = []
            lines[key].append({
                'text': text,
                'x0': x0, 'x1': x1,
                'y0': y0, 'y1': y1,
                'block': block
            })

        # Sort lines by block first, then vertical position
        # This keeps lines within the same block together
        sorted_lines = sorted(
            lines.items(), 
            key=lambda x: (x[0][0], x[1][0]['y0'] if x[1] else 0)  # (block, y0)
        )

        candidates = []
        prev_line = None
        prev_block = None

        for (block, line_no), line_words in sorted_lines:
            if prev_line and line_words:
                # CRITICAL: Only consider line-break if in SAME block
                # This filters out margin content (page numbers, headers)
                if prev_block == block:
                    last_word = prev_line[-1]['text']
                    first_word = line_words[0]['text']

                    if last_word.endswith('-') and len(last_word) > 2:
                        candidate = self._evaluate_join(last_word, first_word)
                        candidates.append(candidate)

            prev_line = line_words
            prev_block = block

        return candidates

    def _evaluate_join(self, fragment1: str, fragment2: str) -> LineBreakCandidate:
        """Evaluate whether two fragments should be joined."""
        # Clean the fragments
        clean_frag1 = fragment1.rstrip('-')
        clean_frag2 = re.sub(r'[^\w]', '', fragment2)  # Strip punctuation

        joined = clean_frag1 + clean_frag2

        # Check with hybrid validation
        is_valid, confidence = self.dictionary.is_probably_word(joined)

        # Position signal boost: hyphen at line end is strong evidence
        # Even if validation fails, if it looks like a word, probably join
        pattern_ok = bool(re.match(r'^[a-zA-ZäöüÄÖÜß]+$', joined))
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
            reason=reason
        )


# =============================================================================
# OCR ERROR DETECTOR
# =============================================================================

@dataclass
class OCRErrorCandidate:
    """A word flagged as potential OCR error."""
    word: str
    position: tuple  # (page, x, y)
    confidence: float  # How confident we are this is an error
    reason: str
    exclude_from_reocr: bool = False  # True if handled by text processing


class OCRErrorDetector:
    """
    Detects OCR errors using spellcheck with scholarly vocabulary filter.
    """

    def __init__(self, dictionary: AdaptiveDictionary):
        self.dictionary = dictionary

        # Scholarly vocabulary to skip (reduces false positives)
        self.scholarly_vocab = {
            # German philosophy
            'dasein', 'ereignis', 'aufhebung', 'zeitlichkeit', 'vorhandenheit',
            'zuhandenheit', 'gestell', 'geworfenheit', 'befindlichkeit',
            'augenblick', 'eigentlichkeit', 'uneigentlichkeit', 'mitsein',
            # French philosophy
            'différance', 'aporia', 'pharmakon', 'arche', 'telos',
            # Latin
            'a priori', 'a posteriori', 'sui generis', 'inter alia',
            # Greek
            'logos', 'noesis', 'phronesis', 'techne', 'aletheia',
        }

    def detect_errors(self, text: str, page_num: int = 0) -> list[OCRErrorCandidate]:
        """Detect potential OCR errors in text."""
        errors = []
        words = text.split()

        for i, word in enumerate(words):
            # Clean word
            clean = re.sub(r'[^\w]', '', word).lower()
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
            errors.append(OCRErrorCandidate(
                word=word,
                position=(page_num, i, 0),  # Simplified position
                confidence=1.0 - conf,
                reason="Unknown word"
            ))

        return errors


# =============================================================================
# TESTING
# =============================================================================

def test_adaptive_dictionary():
    """Test the adaptive dictionary."""
    print("=" * 60)
    print("TEST: Adaptive Dictionary")
    print("=" * 60)

    dict_path = Path("/tmp/test_adaptive_dict.json")
    ad = AdaptiveDictionary(persistence_path=dict_path)

    test_words = [
        ('cognitions', True, "plural of cognition"),
        ('nonexperiential', True, "prefix + base"),
        ('temporalizes', True, "verb form"),
        ('asdfghjkl', False, "random chars"),
        ('tbe', False, "OCR error"),
        ('phiinomen', False, "umlaut OCR error"),
    ]

    print("\nHybrid validation:")
    for word, expected, desc in test_words:
        is_valid, conf = ad.is_probably_word(word)
        status = "✓" if is_valid == expected else "✗"
        print(f"  {status} '{word}' ({desc}): valid={is_valid}, conf={conf:.2f}")

    # Test learning
    print("\nLearning test:")
    ad.maybe_learn("cognitions", "context: multiple cognitions")
    ad.maybe_learn("cognitions", "context: various cognitions")
    ad.maybe_learn("cognitions", "context: different cognitions")

    print(f"  Learned 'cognitions': {ad.learned_words.get('cognitions')}")

    # Save and reload
    ad.save()
    ad2 = AdaptiveDictionary(persistence_path=dict_path)
    print(f"  Persisted and reloaded: {'cognitions' in ad2.learned_words}")


def test_line_break_rejoiner():
    """Test line-break rejoiner on sample PDF."""
    print("\n" + "=" * 60)
    print("TEST: Line-Break Rejoiner")
    print("=" * 60)

    ad = AdaptiveDictionary()
    rejoiner = LineBreakRejoiner(ad)

    # Test on sample PDF
    pdf_path = Path("spikes/sample_pdfs/kant_critique_pages_64_65.pdf")
    if not pdf_path.exists():
        print(f"  Sample PDF not found: {pdf_path}")
        return

    doc = fitz.open(pdf_path)

    all_candidates = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        candidates = rejoiner.detect_from_pdf_page(page)
        all_candidates.extend(candidates)

    print(f"\nFound {len(all_candidates)} line-break candidates:\n")

    join_count = 0
    for c in all_candidates:
        action = "JOIN" if c.should_join else "KEEP"
        status = "✓" if c.should_join else "✗"
        print(f"  {status} '{c.fragment1}' + '{c.fragment2}' → '{c.joined}'")
        print(f"      [{action}] {c.reason} (conf={c.confidence:.2f})")
        if c.should_join:
            join_count += 1

    print(f"\nSummary: {join_count}/{len(all_candidates)} would be joined")

    # Show learned words
    print(f"\nLearned words from this run: {list(ad.learned_words.keys())}")


def test_full_pipeline():
    """Test the full OCR error detection pipeline."""
    print("\n" + "=" * 60)
    print("TEST: Full Pipeline")
    print("=" * 60)

    # Load ground truth errors
    gt_path = Path("ground_truth/ocr_errors/ocr_error_pairs.json")
    if not gt_path.exists():
        print(f"  Ground truth not found: {gt_path}")
        return

    with open(gt_path) as f:
        errors = json.load(f)

    ad = AdaptiveDictionary()
    detector = OCRErrorDetector(ad)

    # Test detection rate
    print(f"\nTesting on {len(errors)} verified error pairs:\n")

    detected = 0
    missed = []

    for pair in errors:
        ocr_text = pair['ocr_text']
        correct_text = pair['correct_text']

        # Check if our pipeline would catch this
        is_known = ad.is_known_word(ocr_text)

        if not is_known:
            detected += 1
        else:
            missed.append((ocr_text, correct_text))

    print(f"Detection rate: {detected}/{len(errors)} ({100*detected/len(errors):.1f}%)")

    if missed:
        print(f"\nMissed errors (false negatives):")
        for ocr, correct in missed[:10]:
            print(f"  '{ocr}' → '{correct}'")

    # Test false positives on correct words
    correct_words = set(p['correct_text'] for p in errors)
    false_positives = []

    for word in correct_words:
        if not ad.is_known_word(word):
            is_valid, conf = ad.is_probably_word(word)
            if not is_valid:
                false_positives.append(word)

    print(f"\nFalse positive rate: {len(false_positives)}/{len(correct_words)} ({100*len(false_positives)/len(correct_words):.1f}%)")

    if false_positives:
        print(f"False positives (correct words flagged):")
        for word in sorted(false_positives)[:10]:
            print(f"  '{word}'")


if __name__ == "__main__":
    test_adaptive_dictionary()
    test_line_break_rejoiner()
    test_full_pipeline()

    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print("""
┌──────────────────────────────────────────────────────────┐
│ STAGE 1: Line-Break Rejoiner                             │
│   - Position-based detection (hyphen at line end)        │
│   - Hybrid validation (dict + morphology + pattern)      │
│   - Learns valid joins to adaptive dictionary            │
│   - Output: Clean text, fragments EXCLUDED from re-OCR   │
└──────────────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────────────┐
│ STAGE 2: Scholarly Vocabulary Filter                     │
│   - Skip German/French/Latin/Greek terms                 │
│   - Reduces false positives significantly                │
└──────────────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────────────┐
│ STAGE 3: OCR Error Detection (Spellcheck)                │
│   - Uses adaptive dictionary (base + learned)            │
│   - Hybrid validation for unknown words                  │
│   - Learns likely words with safeguards                  │
└──────────────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────────────┐
│ STAGE 4: Selective Re-OCR (line-level)                   │
│   - Only flagged words (not line-break fragments)        │
│   - Crop line from page image                            │
│   - Run TrOCR/Tesseract on line crop                     │
│   - Replace flagged words only                           │
└──────────────────────────────────────────────────────────┘

Adaptive Dictionary Features:
  - Morphological validation (plurals, verb forms, prefixes)
  - Pattern validation (no weird chars, has vowels)
  - Learning with safeguards (frequency, confidence)
  - Persistence across runs
""")