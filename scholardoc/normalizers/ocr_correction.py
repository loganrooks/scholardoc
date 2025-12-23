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

# Optional: OCRfixr for BERT-based contextual correction
# Install with: uv pip install ocrfixr  OR  pip install scholardoc[contextual]
# Note: OCRfixr has known compatibility issues with Keras 3 / TensorFlow 2.16+
try:
    from ocrfixr import spellcheck as ocrfixr_spellcheck
except (ImportError, ValueError, ModuleNotFoundError):
    # ValueError: Keras 3 compatibility issue with transformers
    # ImportError/ModuleNotFoundError: ocrfixr or dependencies not installed
    ocrfixr_spellcheck = None  # type: ignore

# Optional: wordfreq for probabilistic scoring
# Install with: uv sync --extra multilingual
try:
    from wordfreq import zipf_frequency

    def get_word_frequency(word: str, lang: str = "en") -> float:
        """Get Zipf frequency for a word (0-8 scale, 0 = not found)."""
        return zipf_frequency(word.lower(), lang)

    WORD_FREQUENCY_AVAILABLE = True
except ImportError:

    def get_word_frequency(word: str, lang: str = "en") -> float:
        """Fallback: return 0 (unknown) for all words."""
        return 0.0

    WORD_FREQUENCY_AVAILABLE = False

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

# Philosophy/scholarly vocabulary - don't flag these as misspellings
# These are valid terms that spell checkers often don't recognize
PHILOSOPHY_VOCABULARY = {
    # German philosophy terms
    "dasein",
    "zeitgeist",
    "weltanschauung",
    "aufhebung",
    "geist",
    "bildung",
    "verstehen",
    "erlebnis",
    "lebenswelt",
    "vorstellung",
    "anschauung",
    # Kantian terms
    "apperception",
    "noumenon",
    "noumena",
    "phenomenal",
    "transcendental",
    "supersensible",
    "antinomy",
    "antinomies",
    "paralogism",
    "schematism",
    "deduction",
    "intuition",
    "intuitions",
    "manifold",
    "sensibility",
    "understanding",
    "judgement",
    "judgment",
    "purposiveness",
    "teleology",
    "teleological",
    "aesthetic",
    "aesthetics",
    "sublime",
    "beautiful",
    # Hegelian terms
    "dialectic",
    "dialectical",
    "aufheben",
    "sublation",
    "negation",
    "determinate",
    "indeterminate",
    "mediation",
    "immediacy",
    "totality",
    # Phenomenology (Husserl, Heidegger)
    "intentionality",
    "epoché",
    "epoche",
    "bracketing",
    "eidetic",
    "noesis",
    "noema",
    "noematic",
    "hyletic",
    "horizonal",
    "existential",
    "existentiale",
    "ontic",
    "ontological",
    "ontology",
    "hermeneutic",
    "hermeneutics",
    "facticity",
    "thrownness",
    "fallenness",
    # Deconstruction/Post-structuralism
    "différance",
    "differance",
    "deconstruction",
    "logocentrism",
    "aporia",
    "supplementarity",
    "iterability",
    "dissemination",
    "grammatology",
    "arche",
    "telos",
    "pharmakon",
    "hymen",
    "trace",
    # Other philosophical terms
    "epistemology",
    "epistemological",
    "metaphysics",
    "metaphysical",
    "phenomenology",
    "phenomenological",
    "axiological",
    "praxis",
    "hermeneutical",
    "intersubjectivity",
    "intersubjective",
    "immanent",
    "immanence",
    "transcendent",
    "transcendence",
    "apodeictic",
    "apodictic",
    "aporetic",
    "categorial",
    "categorical",
    # Linguistic/semiotic terms (common in Derrida, Saussure)
    "phonologism",
    "phonocentrism",
    "grapheme",
    "phoneme",
    "morpheme",
    "signifier",
    "signified",
    "semiotics",
    "semiotic",
    "semiological",
    "semiology",
    "scientificity",
    "fortiori",  # as in "a fortiori"
    "priori",  # as in "a priori"
    "posteriori",  # as in "a posteriori"
    "saussure",
    "saussurean",
    # Proper names (philosophers)
    "kant",
    "hegel",
    "husserl",
    "heidegger",
    "derrida",
    "nietzsche",
    "kierkegaard",
    "schopenhauer",
    "fichte",
    "schelling",
    "gadamer",
    "levinas",
    "merleau",
    "ponty",
    "sartre",
    "beauvoir",
    "camus",
    "wittgenstein",
    "frege",
    "russell",
    "carnap",
    "quine",
    "kripke",
    "rawls",
    "nozick",
    "rorty",
    "habermas",
    "adorno",
    "horkheimer",
    "foucault",
    "deleuze",
    "guattari",
    "lacan",
    "zizek",
    "badiou",
    "aristotle",
    "plato",
    "socrates",
    "descartes",
    "spinoza",
    "leibniz",
    "locke",
    "hume",
    "berkeley",
    "hobbes",
    "rousseau",
    "montesquieu",
}

# Latin scholarly terms (common in philosophy, law, academia)
LATIN_VOCABULARY = {
    # Common Latin phrases
    "priori",
    "posteriori",
    "fortiori",  # a priori, a posteriori, a fortiori
    "facto",
    "jure",  # de facto, de jure
    "nihilo",  # ex nihilo
    "ante",
    "post",  # ante/post
    "circa",
    "ergo",
    "idem",
    "sic",
    "ibid",
    "ibiden",
    "passim",
    "infra",
    "supra",
    "vide",
    "viz",
    "etc",
    "et",
    "al",  # et al., etc.
    # Philosophical Latin
    "cogito",
    "sum",  # cogito ergo sum
    "tabula",
    "rasa",  # tabula rasa
    "esse",
    "ens",
    "quod",
    "qua",
    "sui",
    "generis",  # sui generis
    "modus",
    "ponens",
    "tollens",
    "operandi",
    "vivendi",
    "reductio",
    "absurdum",  # reductio ad absurdum
    "petitio",
    "principii",  # petitio principii
    "causa",
    "causae",
    "finis",
    "telos",
    "substantia",
    "accidens",
    "natura",
    "naturans",
    "naturata",  # Spinoza
    "potentia",
    "actus",
    "ratio",
    "intellectus",
    "voluntas",
    "liberum",
    "arbitrium",
    "res",
    "extensa",
    "cogitans",  # Descartes
    # Legal/academic Latin
    "corpus",
    "habeas",
    "bona",
    "fide",
    "mala",
    "prima",
    "facie",
    "mens",
    "rea",
    "reus",
    "pro",
    "contra",
    "per",
    "se",
    "ipso",
    "mutatis",
    "mutandis",
    "ceteris",
    "paribus",
}

# Greek terms (common in philosophy, often transliterated)
GREEK_VOCABULARY = {
    # Philosophical Greek
    "logos",
    "logoi",
    "eidos",
    "eidetic",
    "physis",
    "techne",
    "telos",
    "teleology",
    "aletheia",  # Heidegger's truth
    "nous",
    "noesis",
    "noetic",
    "psyche",
    "pneuma",
    "sophia",
    "philo",
    "episteme",
    "doxa",
    "praxis",
    "poiesis",
    "theoria",
    "arche",
    "archē",
    "ousia",
    "hypostasis",
    "energeia",
    "dynamis",
    "dunamis",
    "entelechy",
    "entelecheia",
    "hexis",
    "ethos",
    "pathos",
    "mythos",
    "kairos",
    "chronos",
    "agape",
    "eros",
    "philia",
    "arete",
    "virtù",
    "eudaimonia",
    "ataraxia",
    "aporia",
    "aporias",
    "catharsis",
    "mimesis",
    "polis",
    "politeia",
    "kosmos",
    "cosmos",
    "demiurge",
    "demiurgos",
    # Aristotelian terms
    "hylomorphism",
    "hyle",
    "morphe",
    "kategoria",
    "kategoriai",
}

# German common words (for German philosophy texts)
GERMAN_COMMON = {
    # Articles, prepositions, conjunctions
    "der",
    "die",
    "das",
    "den",
    "dem",
    "des",
    "ein",
    "eine",
    "einer",
    "einem",
    "einen",
    "und",
    "oder",
    "aber",
    "denn",
    "weil",
    "von",
    "zu",
    "mit",
    "bei",
    "nach",
    "aus",
    "für",
    "über",
    "unter",
    "zwischen",
    "auf",
    "in",
    "an",
    "um",
    "ist",
    "sind",
    "war",
    "waren",
    "wird",
    "werden",
    "hat",
    "haben",
    "hatte",
    "hatten",
    "kann",
    "können",
    "muss",
    "müssen",
    "als",
    "wenn",
    "dass",
    "ob",
    "nicht",
    "nur",
    "auch",
    "noch",
    "schon",
    "sich",
    "sein",
    "ihr",
    "ihre",
    # Common German philosophy vocabulary
    "seiende",
    "seiendes",  # Heidegger's Being
    "wesen",
    "wesentlich",
    "ding",
    "dinge",
    "grund",
    "gründe",
    "welt",
    "welten",
    "zeit",
    "zeitlich",
    "raum",
    "räumlich",
    "gegenstand",
    "gegenstände",
    "vorstellung",
    "vorstellungen",
    "erkenntnis",
    "erkenntnisse",
    "vernunft",
    "verstand",
    "wille",
    "willen",
    "freiheit",
    "notwendigkeit",
    "möglichkeit",
    "wirklichkeit",
    "erscheinung",
    "erscheinungen",
    "wahrheit",
    "wahrnehmung",
    "urteil",
    "urteile",
    "begriff",
    "begriffe",
    "denken",
    "gedanke",
    "sprache",
    "sprechen",
}

# French scholarly terms (common in theory, Derrida, Lacan, etc.)
FRENCH_VOCABULARY = {
    # Articles, prepositions
    "le",
    "la",
    "les",
    "un",
    "une",
    "des",
    "de",
    "du",
    "au",
    "aux",
    "et",
    "ou",
    "mais",
    "donc",
    "dans",
    "sur",
    "sous",
    "avec",
    "sans",
    "pour",
    "par",
    "entre",
    "est",
    "sont",
    "était",
    "étaient",
    # French theory terms (often untranslated)
    "jouissance",  # Lacan
    "bricolage",
    "bricoleur",  # Lévi-Strauss
    "différance",  # Derrida
    "écriture",
    "parole",
    "mise",
    "en",
    "scène",
    "abyme",  # mise en scène, mise en abyme
    "avant",
    "garde",
    "oeuvre",
    "œuvre",
    "esprit",
    "corps",
    "raison",
    "être",
    "autre",
    "autrui",
    "moi",
    "soi",
    "sens",
    "non",
    "tout",
    "rien",
    "temps",
    "espace",
    "chose",
    "choses",
    "monde",
    "mondes",
    "vie",
    "mort",
    "nom",
    "père",  # Lacan: nom-du-père
    "objet",
    "petit",  # objet petit a
    "réel",
    "imaginaire",
    "symbolique",  # Lacan's registers
    "désir",
    "demande",
    "besoin",
    "signifiant",
    "signifié",
    "sujet",
    "subjectivité",
}

# Combined scholarly vocabulary for quick lookup
SCHOLARLY_VOCABULARY = (
    PHILOSOPHY_VOCABULARY | LATIN_VOCABULARY | GREEK_VOCABULARY | GERMAN_COMMON | FRENCH_VOCABULARY
)


# ============================================================================
# Language Detection (optional)
# ============================================================================

# Supported spell checker languages (pyspellchecker)
SUPPORTED_LANGUAGES = {"en", "de", "fr", "es", "pt", "it", "nl", "ru"}

try:
    from langdetect import DetectorFactory
    from langdetect import detect as langdetect_detect

    # Make language detection deterministic
    DetectorFactory.seed = 0

    def detect_language(text: str) -> str:
        """Detect the dominant language of text using langdetect (Google's algorithm)."""
        try:
            # Need sufficient text for reliable detection
            if len(text.strip()) < 20:
                return "en"
            lang = langdetect_detect(text)
            return lang if lang in SUPPORTED_LANGUAGES else "en"
        except Exception:
            return "en"

    LANGUAGE_DETECTION_AVAILABLE = True
except ImportError:

    def detect_language(text: str) -> str:
        """Fallback: always return English."""
        return "en"

    LANGUAGE_DETECTION_AVAILABLE = False


# ============================================================================
# Correction Analysis (Confidence Scoring)
# ============================================================================

# Foreign language markers - patterns that suggest non-English words
# Note: These are word ENDINGS only to avoid false positives like "beautiful" (contains "eau")
FOREIGN_SUFFIXES = {
    # German suffixes
    "ung",
    "heit",
    "keit",
    "lich",
    "isch",
    "ieren",
    # French suffixes (excluding common English ones)
    "eux",
    "oux",
    "ique",
    # Latin/Greek suffixes
    "ologie",
    "ismus",
    "iae",
    "orum",
    "ae",  # Latin plural
}

# Mid-word markers (more conservative - only apply if word is 6+ chars)
FOREIGN_INFIXES = {
    "sch",  # German: "Geschichte", but not "school"
}


@dataclass
class CorrectionConfig:
    """Configuration for OCR correction confidence scoring.

    Attributes:
        apply_threshold: Minimum confidence to auto-apply (default 0.7)
        review_threshold: Minimum confidence to flag for review (default 0.3)
        skip_threshold: Minimum confidence to even attempt (default 0.1)

        Weight factors (should sum to ~1.0 for interpretability):
        - edit_distance_weight: Penalty weight for edit distance
        - frequency_weight: Weight for word frequency difference
        - ambiguity_weight: Penalty weight for multiple candidates
        - foreign_marker_weight: Penalty weight for foreign word patterns
        - first_letter_weight: Penalty weight for first letter changes
        - scholarly_boost_weight: Bonus for correcting to scholarly terms
    """

    # Thresholds
    apply_threshold: float = 0.7
    review_threshold: float = 0.3
    skip_threshold: float = 0.1

    # Feature weights
    edit_distance_weight: float = 0.20
    frequency_weight: float = 0.25  # Word frequency is highly predictive
    ambiguity_weight: float = 0.15
    foreign_marker_weight: float = 0.15
    first_letter_weight: float = 0.15
    scholarly_boost_weight: float = 0.10

    # Maximum edit distance to consider
    max_edit_distance: int = 2

    # Language for frequency lookups
    language: str = "en"

    @classmethod
    def conservative(cls) -> "CorrectionConfig":
        """Very cautious - only correct obvious errors."""
        return cls(
            apply_threshold=0.85,
            review_threshold=0.5,
            skip_threshold=0.2,
            frequency_weight=0.30,
            edit_distance_weight=0.25,
            max_edit_distance=1,
        )

    @classmethod
    def balanced(cls) -> "CorrectionConfig":
        """Default balanced settings."""
        return cls()

    @classmethod
    def aggressive(cls) -> "CorrectionConfig":
        """More aggressive correction - use with caution."""
        return cls(
            apply_threshold=0.5,
            review_threshold=0.2,
            skip_threshold=0.05,
            frequency_weight=0.35,
            max_edit_distance=3,
        )

    def validate(self) -> None:
        """Validate configuration values."""
        if not (0 <= self.skip_threshold <= self.review_threshold <= self.apply_threshold <= 1):
            raise ValueError("Thresholds must be: 0 <= skip <= review <= apply <= 1")
        if self.max_edit_distance < 1:
            raise ValueError("max_edit_distance must be >= 1")


# Default configuration
DEFAULT_CORRECTION_CONFIG = CorrectionConfig()


@dataclass
class CorrectionCandidate:
    """Analysis of a potential correction."""

    original: str
    suggested: str
    confidence: float  # 0.0-1.0
    edit_distance: int
    candidate_count: int  # Number of alternative corrections
    concerns: list[str] = field(default_factory=list)

    @property
    def is_safe(self) -> bool:
        """Whether this correction is safe to apply automatically."""
        return self.confidence >= 0.7 and self.edit_distance <= 2

    @property
    def needs_review(self) -> bool:
        """Whether this correction should be flagged for human review."""
        return 0.3 <= self.confidence < 0.7

    @property
    def should_skip(self) -> bool:
        """Whether this correction should be skipped."""
        return self.confidence < 0.3


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def analyze_correction(
    word: str,
    spell: "SpellChecker",  # type: ignore
    config: CorrectionConfig | None = None,
) -> CorrectionCandidate | None:
    """
    Analyze a potential correction with weighted confidence scoring.

    Uses a probabilistic approach combining multiple signals:
    1. Word frequency - is the correction a real, common word?
    2. Edit distance - how many characters changed?
    3. Candidate ambiguity - are there multiple plausible corrections?
    4. Foreign word markers - patterns suggesting non-English origin
    5. First letter preservation - corrections usually keep first letter
    6. Scholarly vocabulary - boost for known terms

    Args:
        word: The word to analyze
        spell: SpellChecker instance
        config: CorrectionConfig with thresholds and weights (optional)

    Returns:
        CorrectionCandidate with analysis, or None if word is correct
    """
    if config is None:
        config = DEFAULT_CORRECTION_CONFIG

    word_lower = word.lower()

    # Word is known - no correction needed
    if word_lower in spell:
        return None

    # Word is in scholarly vocabulary - skip
    if word_lower in SCHOLARLY_VOCABULARY:
        return None

    candidates = spell.candidates(word_lower) or set()
    correction = spell.correction(word_lower)

    if not correction or correction == word_lower:
        return None

    # Calculate metrics
    edit_dist = _levenshtein_distance(word_lower, correction)
    candidate_count = len(candidates)

    # =========================================================================
    # Weighted Scoring System
    # =========================================================================
    # Start at 1.0 and subtract weighted penalties
    confidence = 1.0
    concerns: list[str] = []

    # --- Signal 1: Word Frequency (most predictive) ---
    # If wordfreq is available, use it for probabilistic scoring
    if WORD_FREQUENCY_AVAILABLE:
        orig_freq = get_word_frequency(word_lower, config.language)
        corr_freq = get_word_frequency(correction, config.language)

        # High correction frequency + low original frequency = strong signal
        # Zipf scale: 0 = not found, 7+ = very common
        if corr_freq > 0 and orig_freq == 0:
            # Original is NOT a word, correction IS - very good signal
            freq_boost = min(0.3, corr_freq / 20)  # Cap at 0.3 boost
            confidence += freq_boost * config.frequency_weight * 4
        elif corr_freq == 0:
            # Correction is also not a known word - bad signal
            penalty = config.frequency_weight
            confidence -= penalty
            concerns.append("correction not in frequency dictionary")
        elif orig_freq > corr_freq:
            # Original is MORE common than correction - suspicious
            penalty = config.frequency_weight * 0.5
            confidence -= penalty
            concerns.append(f"original more common (zipf {orig_freq:.1f} vs {corr_freq:.1f})")

    # --- Signal 2: Edit Distance ---
    if edit_dist > config.max_edit_distance:
        penalty = config.edit_distance_weight * 2
        confidence -= penalty
        concerns.append(f"high edit distance ({edit_dist})")
    elif edit_dist > 1:
        penalty = config.edit_distance_weight * 0.5
        confidence -= penalty

    # --- Signal 3: Candidate Ambiguity ---
    if candidate_count > 10:
        penalty = config.ambiguity_weight * 1.5
        confidence -= penalty
        concerns.append(f"highly ambiguous ({candidate_count} candidates)")
    elif candidate_count > 5:
        penalty = config.ambiguity_weight * 0.7
        confidence -= penalty
        concerns.append(f"ambiguous ({candidate_count} candidates)")
    elif candidate_count == 1:
        # Only one candidate - good signal
        confidence += config.ambiguity_weight * 0.3

    # --- Signal 4: Foreign Word Markers ---
    has_foreign_suffix = any(word_lower.endswith(suffix) for suffix in FOREIGN_SUFFIXES)
    has_foreign_infix = len(word_lower) >= 6 and any(
        infix in word_lower for infix in FOREIGN_INFIXES
    )
    if has_foreign_suffix or has_foreign_infix:
        penalty = config.foreign_marker_weight
        confidence -= penalty
        concerns.append("possible foreign word")

    # --- Signal 5: First Letter Preservation ---
    if word_lower[0] != correction[0]:
        penalty = config.first_letter_weight
        confidence -= penalty
        concerns.append("first letter changed")

    # --- Signal 6: Scholarly Term Boost ---
    if correction.lower() in SCHOLARLY_VOCABULARY:
        boost = config.scholarly_boost_weight
        confidence += boost
    else:
        # Check if original is close to a different scholarly term
        for vocab_word in SCHOLARLY_VOCABULARY:
            dist = _levenshtein_distance(word_lower, vocab_word)
            if dist <= 2 and vocab_word != correction.lower():
                penalty = config.scholarly_boost_weight
                confidence -= penalty
                concerns.append(f"close to scholarly term '{vocab_word}'")
                break

    # --- Signal 7: Length Similarity ---
    length_diff = abs(len(word) - len(correction))
    if length_diff > 2:
        penalty = 0.1  # Small fixed penalty
        confidence -= penalty
        concerns.append(f"length changed by {length_diff}")

    return CorrectionCandidate(
        original=word,
        suggested=correction,
        confidence=max(0.0, min(1.0, confidence)),
        edit_distance=edit_dist,
        candidate_count=candidate_count,
        concerns=concerns,
    )


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
            # Skip known scholarly vocabulary (philosophy, Latin, Greek, German, French)
            if word in SCHOLARLY_VOCABULARY:
                continue
            if word not in suspicious_words:
                suspicious_words.append(word)
                correction = spell.correction(word)
                if correction and correction != word:
                    correctable_words[word] = correction

    # Calculate error rate estimate
    # Weight different error types by severity (based on Spike 08 & 09)
    # NOTE: mid_word_caps weight=0 because embeddings are perfectly robust to them
    # (e.g., "jUdgment" → 1.000 similarity vs clean text - Spike 09)
    pattern_errors = (
        error_patterns["mid_word_caps"] * 0  # No impact on embeddings! (Spike 09)
        + error_patterns["digits_in_words"] * 2  # High impact
        + error_patterns["pipe_in_word"] * 2  # High impact
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

        # Skip known scholarly vocabulary (philosophy, Latin, Greek, German, French)
        if core.lower() in SCHOLARLY_VOCABULARY:
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


def correct_with_language_detection(
    text: str,
    min_word_length: int = 4,
    skip_capitalized: bool = True,
) -> CorrectionResult:
    """
    Apply spell-check corrections with automatic language detection.

    Detects the dominant language of the text and uses the appropriate
    spell checker dictionary. Always preserves scholarly vocabulary
    regardless of detected language.

    Requires: pip install scholardoc[multilingual]  OR  pip install fast-langdetect

    Args:
        text: Text to correct
        min_word_length: Minimum word length to consider for correction
        skip_capitalized: Skip words that start with capital (proper nouns)

    Returns:
        CorrectionResult with language-aware corrections
    """
    if SpellChecker is None:
        logger.warning("pyspellchecker not installed, skipping spell check")
        return CorrectionResult(
            original_text=text,
            corrected_text=text,
            changes_made=[],
            confidence=0.0,
        )

    # Detect language
    detected_lang = detect_language(text)
    logger.debug(f"Detected language: {detected_lang}")

    # Use appropriate spell checker
    try:
        spell = SpellChecker(language=detected_lang)
    except Exception:
        # Fallback to English if language not supported
        logger.warning(f"Language '{detected_lang}' not supported, falling back to English")
        spell = SpellChecker(language="en")
        detected_lang = "en"

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

        # Skip known scholarly vocabulary (always, regardless of language)
        if core.lower() in SCHOLARLY_VOCABULARY:
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

    # Higher confidence if language detection is available
    confidence = 0.75 if LANGUAGE_DETECTION_AVAILABLE else 0.65

    return CorrectionResult(
        original_text=text,
        corrected_text=" ".join(result_words),
        changes_made=changes,
        confidence=confidence,
    )


def is_language_detection_available() -> bool:
    """Check if language detection (fast-langdetect) is available."""
    return LANGUAGE_DETECTION_AVAILABLE


@dataclass
class AnalyzedCorrectionResult:
    """
    Result of OCR correction with per-word confidence analysis.

    This provides transparency into correction decisions, allowing
    callers to review uncertain corrections before applying them.
    """

    original_text: str
    corrected_text: str
    applied_corrections: list[CorrectionCandidate]  # High confidence, applied
    flagged_corrections: list[CorrectionCandidate]  # Medium confidence, needs review
    skipped_corrections: list[CorrectionCandidate]  # Low confidence, not applied
    overall_confidence: float

    @property
    def has_uncertain_corrections(self) -> bool:
        """Whether there are corrections that need human review."""
        return len(self.flagged_corrections) > 0

    @property
    def total_changes(self) -> int:
        """Total number of corrections applied."""
        return len(self.applied_corrections)

    @property
    def correction_count(self) -> int:
        """Alias for total_changes - number of corrections applied."""
        return self.total_changes


def correct_with_analysis(
    text: str,
    config: CorrectionConfig | None = None,
    min_word_length: int = 4,
    skip_capitalized: bool = True,
) -> AnalyzedCorrectionResult:
    """
    Apply spell-check corrections with detailed per-word confidence analysis.

    This function provides safeguards against bad corrections using
    configurable thresholds and weighted scoring:
    - Only applies corrections with confidence >= config.apply_threshold
    - Flags uncertain corrections for human review
    - Skips corrections that are likely wrong

    Uses word frequency data (if available) for probabilistic scoring.

    Args:
        text: Text to correct
        config: CorrectionConfig with thresholds and weights (uses balanced defaults if None)
        min_word_length: Minimum word length to consider
        skip_capitalized: Skip words that start with capital

    Returns:
        AnalyzedCorrectionResult with detailed breakdown

    Example:
        >>> # Use conservative settings for scholarly texts
        >>> result = correct_with_analysis(text, CorrectionConfig.conservative())
        >>> print(f"Applied {len(result.applied_corrections)} corrections")
        >>> for c in result.flagged_corrections:
        ...     print(f"  Review: {c.original} → {c.suggested} ({c.confidence:.2f})")
    """
    if config is None:
        config = DEFAULT_CORRECTION_CONFIG

    if SpellChecker is None:
        return AnalyzedCorrectionResult(
            original_text=text,
            corrected_text=text,
            applied_corrections=[],
            flagged_corrections=[],
            skipped_corrections=[],
            overall_confidence=0.0,
        )

    spell = SpellChecker()
    words = text.split()
    result_words = []

    applied: list[CorrectionCandidate] = []
    flagged: list[CorrectionCandidate] = []
    skipped: list[CorrectionCandidate] = []

    for word in words:
        # Extract core word without punctuation
        prefix = ""
        suffix = ""
        core = word

        while core and not core[0].isalnum():
            prefix += core[0]
            core = core[1:]

        while core and not core[-1].isalnum():
            suffix = core[-1] + suffix
            core = core[:-1]

        # Skip if too short
        if len(core) < min_word_length:
            result_words.append(word)
            continue

        # Skip capitalized proper nouns
        if skip_capitalized and core and core[0].isupper() and core[1:].islower():
            result_words.append(word)
            continue

        # Analyze the correction using weighted scoring
        analysis = analyze_correction(core, spell, config)

        if analysis is None:
            # Word is correct or in vocabulary
            result_words.append(word)
            continue

        # Categorize based on config thresholds
        if (
            analysis.confidence >= config.apply_threshold
            and analysis.edit_distance <= config.max_edit_distance
        ):
            # High confidence - apply the correction
            corrected = analysis.suggested
            if core.isupper():
                corrected = corrected.upper()
            elif core[0].isupper():
                corrected = corrected.capitalize()

            result_words.append(prefix + corrected + suffix)
            applied.append(analysis)
        elif analysis.confidence >= config.review_threshold:
            # Medium confidence - flag for review but don't apply
            result_words.append(word)
            flagged.append(analysis)
        elif analysis.confidence >= config.skip_threshold:
            # Low confidence - skip but record
            result_words.append(word)
            skipped.append(analysis)
        else:
            # Below skip threshold - don't even record
            result_words.append(word)

    # Calculate overall confidence
    if applied:
        overall_conf = sum(c.confidence for c in applied) / len(applied)
    else:
        overall_conf = 1.0 if not flagged and not skipped else 0.5

    return AnalyzedCorrectionResult(
        original_text=text,
        corrected_text=" ".join(result_words),
        applied_corrections=applied,
        flagged_corrections=flagged,
        skipped_corrections=skipped,
        overall_confidence=overall_conf,
    )


def correct_with_context(text: str) -> CorrectionResult:
    """
    Apply BERT-based contextual OCR correction using OCRfixr.

    This uses a two-step validation: spell suggestions are cross-referenced
    against BERT's context predictions. Corrections only apply when both agree.

    This is more accurate than simple spell check for real-word errors
    but significantly slower (requires BERT inference).

    Requires: pip install scholardoc[contextual]  OR  pip install ocrfixr

    Args:
        text: Text to correct

    Returns:
        CorrectionResult with contextual corrections

    Note:
        - First call will download BERT model (~400MB)
        - Slower than spell check (~1-2s per paragraph)
        - Best for scholarly text where accuracy matters
    """
    if ocrfixr_spellcheck is None:
        logger.warning("OCRfixr not installed. Install with: pip install scholardoc[contextual]")
        return CorrectionResult(
            original_text=text,
            corrected_text=text,
            changes_made=[],
            confidence=0.0,
        )

    try:
        # OCRfixr returns [corrected_text, {(old, new): count}] when return_fixes="T"
        result = ocrfixr_spellcheck(text, return_fixes="T").fix()

        if isinstance(result, list) and len(result) == 2:
            corrected_text, fixes_dict = result
            # Convert fixes dict to our format: list of (original, corrected)
            changes = [(old, new) for (old, new), count in fixes_dict.items() for _ in range(count)]
        else:
            # Fallback if format changes
            corrected_text = result if isinstance(result, str) else text
            changes = []

        return CorrectionResult(
            original_text=text,
            corrected_text=corrected_text,
            changes_made=changes,
            confidence=0.85,  # High confidence - BERT validates context
        )
    except Exception as e:
        logger.warning(f"OCRfixr correction failed: {e}")
        return CorrectionResult(
            original_text=text,
            corrected_text=text,
            changes_made=[],
            confidence=0.0,
        )


def is_contextual_available() -> bool:
    """Check if contextual (BERT-based) correction is available."""
    return ocrfixr_spellcheck is not None


def correct_ocr_errors(
    text: str,
    use_patterns: bool = True,
    use_spellcheck: bool = True,
    use_context: bool = False,
    aggressive: bool = False,
) -> CorrectionResult:
    """
    Apply OCR error corrections to text.

    Recommended usage for RAG pipelines:
    - Default settings for general use
    - use_context=True for highest accuracy (requires OCRfixr)
    - aggressive=True only for severely degraded text

    Args:
        text: Text to correct
        use_patterns: Apply known pattern corrections (safe, fast)
        use_spellcheck: Apply spell-check corrections (more aggressive)
        use_context: Apply BERT-based contextual corrections (slowest, most accurate)
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

    if use_context:
        context_result = correct_with_context(result)
        if context_result.was_modified:
            result = context_result.corrected_text
            all_changes.extend(context_result.changes_made)
            # Context correction has high confidence when it works
            confidence = max(confidence, context_result.confidence)

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
