#!/usr/bin/env python3
"""
Spike 06: Extract Tricky OCR Samples from Philosophy PDFs

PURPOSE: Extract challenging text samples for EXTENSIVE OCR correction testing.
         Covers 25+ categories of problematic text patterns.

RUN:
  uv run python spikes/06_extract_tricky_samples.py
  uv run python spikes/06_extract_tricky_samples.py --pdf sample.pdf
  uv run python spikes/06_extract_tricky_samples.py --extensive  # More samples per category
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from typing import Optional

try:
    import fitz
except ImportError:
    print("Install PyMuPDF: uv add pymupdf")
    exit(1)


@dataclass
class TrickySample:
    """A sample of challenging OCR text."""
    source_pdf: str
    page_num: int
    category: str
    subcategory: str = ""
    original_text: str = ""
    context: str = ""
    position: dict = field(default_factory=dict)
    notes: str = ""
    severity: str = "medium"  # low, medium, high, critical


# =============================================================================
# CATEGORY 1: FOREIGN LANGUAGE TERMS
# =============================================================================

GERMAN_TERMS = [
    # Heidegger vocabulary
    r'\bSein\b', r'\bDasein\b', r'\bSeiendes\b', r'\bSeiende\b',
    r'\bVorhandenheit\b', r'\bZuhandenheit\b', r'\bIn-der-Welt-sein\b',
    r'\bMitsein\b', r'\bSelbst\b', r'\bGerede\b', r'\bNeugier\b',
    r'\bBefindlichkeit\b', r'\bVerstehen\b', r'\bRede\b', r'\bVerfallen\b',
    r'\bSorge\b', r'\bAngst\b', r'\bGewissen\b', r'\bSchuld\b',
    r'\bEntschlossenheit\b', r'\bZeitlichkeit\b', r'\bGeschichtlichkeit\b',
    r'\bWiederholung\b', r'\bAugenblick\b', r'\bSchicksal\b', r'\bGeschick\b',
    r'\bÜberwindung\b', r'\bEreignis\b', r'\bGelassenheit\b', r'\bLichtung\b',
    r'\bAufgehen\b', r'\bAnwesen\b', r'\bVerbergung\b', r'\bEntbergung\b',
    r'\bUnverborgenheit\b', r'\bAletheia\b', r'\bLogos\b', r'\bPhysis\b',
    # Hegel vocabulary
    r'\bAufhebung\b', r'\bGeist\b', r'\bWesen\b', r'\bBegriff\b',
    r'\bVermittlung\b', r'\bNegation\b', r'\bBestimmung\b', r'\bMoment\b',
    # Husserl vocabulary
    r'\bLebenswelt\b', r'\bNoema\b', r'\bNoesis\b', r'\bEpoché\b',
    r'\bEinklammerung\b', r'\bIntentionalität\b',
    # General German
    r'\bWeltanschauung\b', r'\bZeitgeist\b', r'\bAngst\b', r'\bKitsch\b',
]

FRENCH_TERMS = [
    # Derrida vocabulary
    r'\bdifférance\b', r'\btrace\b', r'\bsupplement\b', r'\bpharmakon\b',
    r'\barchécriture\b', r'\bgrammatologie\b', r'\bdéconstruction\b',
    r'\bécriture\b', r'\bsous rature\b', r'\bjeu\b', r'\bdifférence\b',
    r'\bprésence\b', r'\babsence\b', r'\bsignifiant\b', r'\bsignifié\b',
    # Foucault vocabulary
    r'\bépistémè\b', r'\bdiscours\b', r'\bsavoir\b', r'\bpouvoir\b',
    # Lacan vocabulary
    r'\bjouissance\b', r'\bmanque\b', r'\bl\'Autre\b', r'\bobjet petit a\b',
    # General French philosophical terms
    r'\bà priori\b', r'\bà posteriori\b', r'\bvis-à-vis\b', r'\braison d\'être\b',
]

LATIN_TERMS = [
    r'\ba priori\b', r'\ba posteriori\b', r'\bad hoc\b', r'\bad hominem\b',
    r'\bper se\b', r'\bqua\b', r'\bviz\.\b', r'\bi\.e\.\b', r'\be\.g\.\b',
    r'\bcf\.\b', r'\bvs\.\b', r'\bet al\.\b', r'\bibid\.\b', r'\bop\. cit\.\b',
    r'\bloc\. cit\.\b', r'\bpassim\b', r'\bsic\b', r'\binter alia\b',
    r'\bmodus ponens\b', r'\bmodus tollens\b', r'\breductio ad absurdum\b',
    r'\bex nihilo\b', r'\bin toto\b', r'\bmutatis mutandis\b',
    r'\bpace\b', r'\bcontra\b', r'\bde facto\b', r'\bde jure\b',
    r'\bsui generis\b', r'\bprima facie\b', r'\bceteris paribus\b',
]

# =============================================================================
# CATEGORY 2: SPECIAL CHARACTERS AND SYMBOLS
# =============================================================================

GREEK_PATTERNS = [
    (r'[\u0370-\u03FF]+', 'greek_modern'),  # Modern Greek
    (r'[\u1F00-\u1FFF]+', 'greek_polytonic'),  # Extended Greek (polytonic)
]

DIACRITIC_PATTERNS = [
    # Accented vowels (common in French, German, etc.)
    (r'[àáâãäåæ]', 'diacritic_a'),
    (r'[èéêë]', 'diacritic_e'),
    (r'[ìíîï]', 'diacritic_i'),
    (r'[òóôõöø]', 'diacritic_o'),
    (r'[ùúûü]', 'diacritic_u'),
    (r'[ýÿ]', 'diacritic_y'),
    (r'[ñ]', 'diacritic_n'),
    (r'[çć]', 'diacritic_c'),
    # German umlauts specifically
    (r'[äöüÄÖÜß]', 'german_umlaut'),
]

SPECIAL_PUNCTUATION = [
    (r'[\u201C\u201D]', 'curly_quotes_double'),  # Curly double quotes " "
    (r'[\u2018\u2019]', 'curly_quotes_single'),  # Curly single quotes ' '
    (r'[\u00AB\u00BB]', 'guillemets'),  # French quotation marks « »
    (r'[\u201E\u201C]', 'german_quotes'),  # German quotation marks „ "
    (r'\u2014', 'em_dash'),  # Em dash —
    (r'\u2013', 'en_dash'),  # En dash –
    (r'\u2026', 'ellipsis'),  # Horizontal ellipsis …
    (r'\u00B7', 'middle_dot'),  # Middle dot ·
    (r'\u2020', 'dagger'),  # Dagger † (footnote marker)
    (r'\u2021', 'double_dagger'),  # Double dagger ‡
    (r'\u00A7', 'section_sign'),  # Section sign §
    (r'\u00B6', 'pilcrow'),  # Paragraph mark ¶
    (r'\u00A9', 'copyright'),  # Copyright ©
    (r'\u00AE', 'registered'),  # Registered ®
    (r'\u2122', 'trademark'),  # Trademark ™
]

MATHEMATICAL_SYMBOLS = [
    (r'[\u2200\u2203\u2208\u2209\u2282\u2283\u2286\u2287]', 'set_theory'),  # ∀∃∈∉⊂⊃⊆⊇
    (r'[\u2227\u2228\u00AC\u2192\u2194\u22A2\u22A8]', 'logical_operators'),  # ∧∨¬→↔⊢⊨
    (r'[\u2260\u2264\u2265\u2248\u2261\u2262]', 'relations'),  # ≠≤≥≈≡≢
    (r'[\u221E\u2211\u220F\u222B]', 'calculus'),  # ∞∑∏∫
    (r'[\u221A\u221B\u221C]', 'roots'),  # √∛∜
    (r'[\u03B1\u03B2\u03B3\u03B4\u03B5\u03B6\u03B7\u03B8]', 'greek_math'),  # αβγδεζηθ
    (r'[\u00D7\u00F7\u00B1\u2213]', 'arithmetic'),  # ×÷±∓
]

# =============================================================================
# CATEGORY 3: TYPOGRAPHY AND FORMATTING
# =============================================================================

LIGATURE_PATTERNS = [
    # Ligatures that may be split or corrupted
    (r'\bfi\b', 'ligature_fi'),  # Often split from fi ligature
    (r'\bfl\b', 'ligature_fl'),
    (r'\bff\b', 'ligature_ff'),
    (r'\bffi\b', 'ligature_ffi'),
    (r'\bffl\b', 'ligature_ffl'),
    # Words commonly affected by ligature issues
    (r'\b\w*ffi\w*\b', 'word_with_ffi'),  # e.g., "office", "sufficient"
    (r'\b\w*ffl\w*\b', 'word_with_ffl'),  # e.g., "raffle", "baffle"
    (r'\b\w*fi\w*\b', 'word_with_fi'),  # e.g., "find", "first", "definition"
]

SUPERSCRIPT_SUBSCRIPT = [
    (r'[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ]', 'superscript_unicode'),
    (r'[₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎]', 'subscript_unicode'),
    (r'\^\d+', 'caret_superscript'),  # ^1, ^2, etc.
    (r'\d+\s*[A-Za-z]', 'footnote_marker_adjacent'),  # "text1" - number adjacent to text
]

SMALL_CAPS_INDICATORS = [
    # Patterns suggesting small caps (often author names)
    (r'\b[A-Z]{2,}[a-z]+[A-Z]+\b', 'mixed_caps'),  # HEIdegger, DERRida
    (r'\b[A-Z][A-Z]+\b', 'all_caps_word'),  # HEIDEGGER, DERRIDA
]

# =============================================================================
# CATEGORY 4: OCR ERROR PATTERNS
# =============================================================================

OCR_CHAR_CONFUSION = [
    # Common OCR character confusions
    (r'[rn]{2,}', 'rn_m_confusion'),  # rn often misread as m
    (r'[Il1|]{2,}', 'l1I_confusion'),  # l, 1, I, | confusion
    (r'cl', 'cl_d_confusion'),  # cl often misread as d
    (r'vv', 'vv_w_confusion'),  # vv often misread as w
    (r'c[il1]', 'ci_confusion'),  # ci, c1, cl confusion
    (r'[0O]{2,}', 'zero_O_confusion'),  # 0 and O confusion
    (r'[5S]{2,}', 'five_S_confusion'),  # 5 and S confusion
    (r'[8B]{2,}', 'eight_B_confusion'),  # 8 and B confusion
    (r'[6G]{2,}', 'six_G_confusion'),  # 6 and G confusion
    (r'\bth[ce]\b', 'the_confusion'),  # "the" often becomes "thc" or "tbe"
    (r'\btb[ae]\b', 'the_confusion_2'),  # "the" → "tba" or "tbe"
]

OCR_SPACING_ERRORS = [
    (r'\b\w\s+\w\s+\w\s+\w\b', 'spaced_letters'),  # S p a c e d text
    (r'\b\w{10,}\b', 'merged_words'),  # Very long "words" (merged)
    (r'\s{3,}', 'excessive_spacing'),  # Multiple spaces
]

OCR_HYPHENATION = [
    (r'(\w{3,})-\s*\n\s*(\w{3,})', 'line_break_hyphen'),  # word-\nword
    (r'(\w+)-\s+(\w+)', 'broken_compound'),  # word- word (should be word-word)
    (r'(\w+)\s+-\s*(\w+)', 'orphaned_hyphen'),  # word -word or word - word
]

# =============================================================================
# CATEGORY 5: SCHOLARLY APPARATUS
# =============================================================================

CITATION_PATTERNS = [
    (r'\([A-Z][a-z]+,?\s*\d{4}[a-z]?\)', 'parenthetical_citation'),  # (Smith, 2020)
    (r'\([A-Z][a-z]+\s+\d{4}:\s*\d+\)', 'page_citation'),  # (Smith 2020: 45)
    (r'\b[A-Z][a-z]+\s+\(\d{4}\)', 'author_year'),  # Smith (2020)
    (r'pp?\.\s*\d+[-–]\d+', 'page_range'),  # pp. 45-67 or p. 45
    (r'\bvol\.\s*\d+', 'volume_number'),  # vol. 2
    (r'\bno\.\s*\d+', 'issue_number'),  # no. 3
]

CROSS_REFERENCE_PATTERNS = [
    (r'[Ss]ee\s+(?:also\s+)?(?:p\.|page|§|chapter|Ch\.)\s*\d+', 'see_reference'),
    (r'[Cc]f\.\s*(?:p\.|§|above|below)', 'cf_reference'),
    (r'(?:supra|infra)\s+(?:p\.|§|note)\s*\d*', 'supra_infra'),
    (r'§+\s*\d+(?:\.\d+)*', 'section_reference'),  # §4.2.1
    (r'\bfn\.\s*\d+', 'footnote_reference'),  # fn. 23
    (r'\bn\.\s*\d+', 'note_reference'),  # n. 23
]

EDITORIAL_MARKS = [
    (r'\[sic\]', 'sic'),
    (r'\[\.{3}\]', 'ellipsis_brackets'),  # [...]
    (r'\[emphasis\s+(?:added|in\s+original)\]', 'emphasis_note'),
    (r'\[trans\.\]', 'translation_note'),
    (r'\[TN\]', 'translator_note'),  # [TN]
    (r'\[Ed\.\]', 'editor_note'),  # [Ed.]
    (r'\?\?+', 'uncertain_reading'),  # ?? marks uncertain text
    (r'\*{1,3}', 'asterisk_note'),  # * or ** or ***
]

# =============================================================================
# CATEGORY 6: NAMES AND PROPER NOUNS
# =============================================================================

PHILOSOPHER_NAMES = [
    # Often misspelled or flagged by spell checkers
    r'\bHeidegger\b', r'\bHusserl\b', r'\bDerrida\b', r'\bFoucault\b',
    r'\bNietzsche\b', r'\bKierkegaard\b', r'\bSchopenhauer\b', r'\bWittgenstein\b',
    r'\bHabermas\b', r'\bGadamer\b', r'\bRicoeur\b', r'\bLevinas\b',
    r'\bMerleau-Ponty\b', r'\bSartre\b', r'\bBeauvoir\b', r'\bDeleuze\b',
    r'\bGuattari\b', r'\bBadiou\b', r'\bŽižek\b', r'\bAgamben\b',
    r'\bArendt\b', r'\bAdorno\b', r'\bHorkheimer\b', r'\bBenjamin\b',
    r'\bHegel\b', r'\bKant\b', r'\bDescartes\b', r'\bSpinoza\b',
    r'\bLeibniz\b', r'\bLocke\b', r'\bHume\b', r'\bBerkeley\b',
    r'\bPlato\b', r'\bAristotle\b', r'\bSocrates\b', r'\bParmenides\b',
    r'\bHeraclitus\b', r'\bThales\b', r'\bAnaximander\b', r'\bPythagoras\b',
]

# =============================================================================
# CATEGORY 7: SOUS-ERASURE CANDIDATES
# =============================================================================

SOUS_ERASURE_TERMS = [
    'Being', 'being', 'presence', 'present', 'is', 'signified',
    'transcendental', 'origin', 'truth', 'meaning', 'subject',
    'consciousness', 'logos', 'trace', 'differance', 'supplement',
    'sign', 'writing', 'speech', 'voice', 'center', 'structure',
]

# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

def extract_by_pattern_list(
    doc: fitz.Document,
    pdf_name: str,
    patterns: list,
    category: str,
    max_per_page: int = 3,
    max_total: int = 30
) -> list[TrickySample]:
    """Generic extraction for pattern lists."""
    samples = []

    if isinstance(patterns[0], tuple):
        # Pattern with subcategory
        combined = [(p, sub) for p, sub in patterns]
    else:
        # Just patterns
        combined = [(p, category) for p in patterns]

    for page_num, page in enumerate(doc):
        text = page.get_text()
        page_samples = 0

        for pattern, subcategory in combined:
            if page_samples >= max_per_page:
                break
            if len(samples) >= max_total:
                return samples

            for match in re.finditer(pattern, text, re.IGNORECASE):
                start = max(0, match.start() - 80)
                end = min(len(text), match.end() + 80)
                context = text[start:end].replace('\n', ' ').strip()

                samples.append(TrickySample(
                    source_pdf=pdf_name,
                    page_num=page_num + 1,
                    category=category,
                    subcategory=subcategory if isinstance(subcategory, str) else "",
                    original_text=match.group(),
                    context=context,
                    notes=f"Pattern: {pattern[:30]}..."
                ))
                page_samples += 1
                break  # One match per pattern per page

    return samples


def extract_german_terms(doc: fitz.Document, pdf_name: str, max_samples: int = 25) -> list[TrickySample]:
    """Extract German philosophical terms."""
    return extract_by_pattern_list(
        doc, pdf_name, GERMAN_TERMS, 'german_terms',
        max_per_page=3, max_total=max_samples
    )


def extract_french_terms(doc: fitz.Document, pdf_name: str, max_samples: int = 20) -> list[TrickySample]:
    """Extract French philosophical terms."""
    return extract_by_pattern_list(
        doc, pdf_name, FRENCH_TERMS, 'french_terms',
        max_per_page=2, max_total=max_samples
    )


def extract_latin_terms(doc: fitz.Document, pdf_name: str, max_samples: int = 20) -> list[TrickySample]:
    """Extract Latin terms and abbreviations."""
    return extract_by_pattern_list(
        doc, pdf_name, LATIN_TERMS, 'latin_terms',
        max_per_page=3, max_total=max_samples
    )


def extract_greek(doc: fitz.Document, pdf_name: str, max_samples: int = 15) -> list[TrickySample]:
    """Extract Greek text."""
    return extract_by_pattern_list(
        doc, pdf_name, GREEK_PATTERNS, 'greek_chars',
        max_per_page=2, max_total=max_samples
    )


def extract_diacritics(doc: fitz.Document, pdf_name: str, max_samples: int = 20) -> list[TrickySample]:
    """Extract text with diacritical marks."""
    return extract_by_pattern_list(
        doc, pdf_name, DIACRITIC_PATTERNS, 'diacritics',
        max_per_page=3, max_total=max_samples
    )


def extract_special_punctuation(doc: fitz.Document, pdf_name: str, max_samples: int = 20) -> list[TrickySample]:
    """Extract special punctuation marks."""
    return extract_by_pattern_list(
        doc, pdf_name, SPECIAL_PUNCTUATION, 'special_punctuation',
        max_per_page=3, max_total=max_samples
    )


def extract_math_symbols(doc: fitz.Document, pdf_name: str, max_samples: int = 15) -> list[TrickySample]:
    """Extract mathematical and logical symbols."""
    return extract_by_pattern_list(
        doc, pdf_name, MATHEMATICAL_SYMBOLS, 'math_symbols',
        max_per_page=2, max_total=max_samples
    )


def extract_ligatures(doc: fitz.Document, pdf_name: str, max_samples: int = 20) -> list[TrickySample]:
    """Extract potential ligature issues."""
    samples = []

    # Look for words that commonly have ligatures
    ligature_words = [
        r'\boffice\b', r'\bsufficient\b', r'\befficient\b', r'\bdefin\w+\b',
        r'\bfind\b', r'\bfirst\b', r'\bafter\b', r'\bdifferent\b',
        r'\bfloor\b', r'\bflow\b', r'\bflatten\b', r'\bafflict\b',
    ]

    for page_num, page in enumerate(doc):
        text = page.get_text()

        for pattern in ligature_words:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                if len(samples) >= max_samples:
                    return samples

                start = max(0, match.start() - 60)
                end = min(len(text), match.end() + 60)
                context = text[start:end].replace('\n', ' ').strip()

                samples.append(TrickySample(
                    source_pdf=pdf_name,
                    page_num=page_num + 1,
                    category='ligatures',
                    subcategory='ligature_word',
                    original_text=match.group(),
                    context=context,
                    notes=f"Word with potential ligature: {match.group()}"
                ))
                break

    return samples


def extract_superscripts(doc: fitz.Document, pdf_name: str, max_samples: int = 15) -> list[TrickySample]:
    """Extract superscript/subscript patterns."""
    return extract_by_pattern_list(
        doc, pdf_name, SUPERSCRIPT_SUBSCRIPT, 'superscript_subscript',
        max_per_page=2, max_total=max_samples
    )


def extract_ocr_char_errors(doc: fitz.Document, pdf_name: str, max_samples: int = 25) -> list[TrickySample]:
    """Extract OCR character confusion patterns."""
    return extract_by_pattern_list(
        doc, pdf_name, OCR_CHAR_CONFUSION, 'ocr_char_confusion',
        max_per_page=3, max_total=max_samples
    )


def extract_hyphenation(doc: fitz.Document, pdf_name: str, max_samples: int = 20) -> list[TrickySample]:
    """Extract hyphenation issues."""
    samples = []

    for page_num, page in enumerate(doc):
        text = page.get_text()

        # Line-break hyphenation
        pattern = r'(\w{3,})-\s*\n\s*(\w{3,})'
        for match in re.finditer(pattern, text):
            if len(samples) >= max_samples:
                return samples

            word1, word2 = match.groups()
            start = max(0, match.start() - 40)
            end = min(len(text), match.end() + 40)
            context = text[start:end].replace('\n', '⏎')

            samples.append(TrickySample(
                source_pdf=pdf_name,
                page_num=page_num + 1,
                category='hyphenation',
                subcategory='line_break',
                original_text=f"{word1}-{word2}",
                context=context,
                notes=f"Split: {word1}- + {word2}",
                severity='high'
            ))

    return samples


def extract_citations(doc: fitz.Document, pdf_name: str, max_samples: int = 20) -> list[TrickySample]:
    """Extract citation patterns."""
    return extract_by_pattern_list(
        doc, pdf_name, CITATION_PATTERNS, 'citations',
        max_per_page=2, max_total=max_samples
    )


def extract_cross_references(doc: fitz.Document, pdf_name: str, max_samples: int = 15) -> list[TrickySample]:
    """Extract cross-reference patterns."""
    return extract_by_pattern_list(
        doc, pdf_name, CROSS_REFERENCE_PATTERNS, 'cross_references',
        max_per_page=2, max_total=max_samples
    )


def extract_editorial_marks(doc: fitz.Document, pdf_name: str, max_samples: int = 15) -> list[TrickySample]:
    """Extract editorial marks and annotations."""
    return extract_by_pattern_list(
        doc, pdf_name, EDITORIAL_MARKS, 'editorial_marks',
        max_per_page=2, max_total=max_samples
    )


def extract_philosopher_names(doc: fitz.Document, pdf_name: str, max_samples: int = 25) -> list[TrickySample]:
    """Extract philosopher names (often misspelled by OCR)."""
    return extract_by_pattern_list(
        doc, pdf_name, PHILOSOPHER_NAMES, 'philosopher_names',
        max_per_page=3, max_total=max_samples
    )


def extract_sous_erasure_candidates(doc: fitz.Document, pdf_name: str, max_samples: int = 15) -> list[TrickySample]:
    """Extract potential sous-erasure candidates."""
    samples = []

    for page_num, page in enumerate(doc):
        text = page.get_text()

        for term in SOUS_ERASURE_TERMS:
            pattern = rf'\b{term}\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start = max(0, match.start() - 150)
                end = min(len(text), match.end() + 150)
                context = text[start:end].replace('\n', ' ')

                # Filter for philosophical context
                if any(kw in context.lower() for kw in [
                    'metaphysics', 'ontolog', 'phenom', 'deconstruct',
                    'heidegger', 'derrida', 'crossed out', 'under erasure',
                    'strikethrough', 'deletion'
                ]):
                    if len(samples) >= max_samples:
                        return samples

                    samples.append(TrickySample(
                        source_pdf=pdf_name,
                        page_num=page_num + 1,
                        category='sous_erasure_candidate',
                        original_text=match.group(),
                        context=context.strip(),
                        notes="Needs visual verification for X-marks",
                        severity='high'
                    ))
                    break

    return samples


def extract_roman_numerals(doc: fitz.Document, pdf_name: str, max_samples: int = 15) -> list[TrickySample]:
    """Extract Roman numerals (often confused with letters)."""
    samples = []

    # Roman numeral patterns
    patterns = [
        (r'\b[ivxlcdm]+\b', 'lowercase_roman'),  # i, ii, iii, iv, v, vi, vii, viii, ix, x
        (r'\b[IVXLCDM]+\b', 'uppercase_roman'),  # I, II, III, IV, V
    ]

    for page_num, page in enumerate(doc):
        text = page.get_text()

        for pattern, subcat in patterns:
            for match in re.finditer(pattern, text):
                # Filter to actual Roman numerals (not random letters)
                num = match.group().lower()
                if num in ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x',
                          'xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi', 'xvii', 'xviii', 'xix', 'xx',
                          'l', 'c', 'd', 'm', 'xl', 'xc', 'cd', 'cm']:
                    if len(samples) >= max_samples:
                        return samples

                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].replace('\n', ' ')

                    samples.append(TrickySample(
                        source_pdf=pdf_name,
                        page_num=page_num + 1,
                        category='roman_numerals',
                        subcategory=subcat,
                        original_text=match.group(),
                        context=context.strip(),
                        notes="Roman numeral - l/I confusion risk"
                    ))
                    break

    return samples


def extract_block_quotes(doc: fitz.Document, pdf_name: str, max_samples: int = 10) -> list[TrickySample]:
    """Extract block quotes (indented text)."""
    samples = []

    for page_num, page in enumerate(doc):
        # Get text with layout preserved
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block.get("type") == 0:  # Text block
                bbox = block.get("bbox", [0, 0, 0, 0])
                x0 = bbox[0]

                # Check if significantly indented (block quote indicator)
                if x0 > 100:  # Arbitrary threshold for indentation
                    text = ""
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text += span.get("text", "")
                        text += " "

                    if len(text.strip()) > 50:  # Substantial text
                        if len(samples) >= max_samples:
                            return samples

                        samples.append(TrickySample(
                            source_pdf=pdf_name,
                            page_num=page_num + 1,
                            category='block_quote',
                            original_text=text[:100].strip(),
                            context=text[:200].strip(),
                            position={'x0': x0},
                            notes=f"Indented text at x={x0}"
                        ))

    return samples


def extract_page_artifacts(doc: fitz.Document, pdf_name: str, max_samples: int = 15) -> list[TrickySample]:
    """Extract page headers, footers, and running heads."""
    samples = []

    for page_num, page in enumerate(doc):
        text = page.get_text()
        lines = text.split('\n')

        # Check first few and last few lines for headers/footers
        for i, line in enumerate(lines[:3] + lines[-3:]):
            line = line.strip()
            if len(line) > 5 and len(line) < 80:
                # Likely header/footer patterns
                if re.match(r'^\d+$', line):  # Page number
                    if len(samples) >= max_samples:
                        return samples
                    samples.append(TrickySample(
                        source_pdf=pdf_name,
                        page_num=page_num + 1,
                        category='page_artifact',
                        subcategory='page_number',
                        original_text=line,
                        context=line,
                        notes="Standalone page number"
                    ))
                elif re.match(r'^[A-Z][A-Z\s]+$', line):  # ALL CAPS header
                    if len(samples) >= max_samples:
                        return samples
                    samples.append(TrickySample(
                        source_pdf=pdf_name,
                        page_num=page_num + 1,
                        category='page_artifact',
                        subcategory='running_head',
                        original_text=line,
                        context=line,
                        notes="Running head (all caps)"
                    ))

    return samples


def extract_unicode_anomalies(doc: fitz.Document, pdf_name: str, max_samples: int = 20) -> list[TrickySample]:
    """Extract unusual Unicode characters that might cause issues."""
    samples = []

    # Problematic Unicode patterns
    anomaly_patterns = [
        (r'[\u00A0]', 'non_breaking_space'),  # Non-breaking space
        (r'[\u200B-\u200D]', 'zero_width'),  # Zero-width characters
        (r'[\u2028\u2029]', 'line_separator'),  # Line/paragraph separators
        (r'[\uFEFF]', 'bom'),  # Byte order mark
        (r'[\u0080-\u009F]', 'c1_control'),  # C1 control characters
        (r'[\uFFFD]', 'replacement_char'),  # Unicode replacement character
        (r'[\u2000-\u200A]', 'unicode_spaces'),  # Various Unicode spaces
    ]

    for page_num, page in enumerate(doc):
        text = page.get_text()

        for pattern, subcat in anomaly_patterns:
            for match in re.finditer(pattern, text):
                if len(samples) >= max_samples:
                    return samples

                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].replace('\n', ' ')

                # Show hex code for invisible characters
                hex_code = ' '.join(f'U+{ord(c):04X}' for c in match.group())

                samples.append(TrickySample(
                    source_pdf=pdf_name,
                    page_num=page_num + 1,
                    category='unicode_anomaly',
                    subcategory=subcat,
                    original_text=hex_code,
                    context=repr(context),
                    notes=f"Unicode anomaly: {subcat}",
                    severity='medium'
                ))
                break

    return samples


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_pdf(pdf_path: Path, extensive: bool = False) -> dict:
    """Process a single PDF and extract all tricky samples."""
    doc = fitz.open(str(pdf_path))
    pdf_name = pdf_path.name

    print(f"\n{'='*70}")
    print(f"Processing: {pdf_name}")
    print(f"Pages: {len(doc)}")
    print(f"Mode: {'EXTENSIVE' if extensive else 'standard'}")
    print(f"{'='*70}")

    # Multiplier for extensive mode
    mult = 2 if extensive else 1

    all_samples = []

    # Extract each category
    extractors = [
        ('German terms', extract_german_terms, 25 * mult),
        ('French terms', extract_french_terms, 20 * mult),
        ('Latin terms', extract_latin_terms, 20 * mult),
        ('Greek characters', extract_greek, 15 * mult),
        ('Diacritics', extract_diacritics, 20 * mult),
        ('Special punctuation', extract_special_punctuation, 20 * mult),
        ('Math symbols', extract_math_symbols, 15 * mult),
        ('Ligatures', extract_ligatures, 20 * mult),
        ('Superscripts/subscripts', extract_superscripts, 15 * mult),
        ('OCR char confusion', extract_ocr_char_errors, 25 * mult),
        ('Hyphenation', extract_hyphenation, 20 * mult),
        ('Citations', extract_citations, 20 * mult),
        ('Cross-references', extract_cross_references, 15 * mult),
        ('Editorial marks', extract_editorial_marks, 15 * mult),
        ('Philosopher names', extract_philosopher_names, 25 * mult),
        ('Sous-erasure candidates', extract_sous_erasure_candidates, 15 * mult),
        ('Roman numerals', extract_roman_numerals, 15 * mult),
        ('Block quotes', extract_block_quotes, 10 * mult),
        ('Page artifacts', extract_page_artifacts, 15 * mult),
        ('Unicode anomalies', extract_unicode_anomalies, 20 * mult),
    ]

    for name, extractor, max_samples in extractors:
        samples = extractor(doc, pdf_name, max_samples)
        print(f"  {name}: {len(samples)} samples")
        all_samples.extend(samples)

    doc.close()

    # Organize by category
    by_category = defaultdict(list)
    for s in all_samples:
        by_category[s.category].append(asdict(s))

    return {
        'source_pdf': pdf_name,
        'total_samples': len(all_samples),
        'by_category': dict(by_category),
        'samples': [asdict(s) for s in all_samples]
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Extract tricky OCR samples (extensive)")
    parser.add_argument('--pdf', type=str, help='Specific PDF to process')
    parser.add_argument('--output', type=str, default='spikes/tricky_samples.json', help='Output file')
    parser.add_argument('--extensive', action='store_true', help='Extract more samples per category')
    args = parser.parse_args()

    sample_dir = Path('spikes/sample_pdfs')

    if args.pdf:
        pdfs = [Path(args.pdf)]
    else:
        # Process all philosophy PDFs
        pdfs = list(sample_dir.glob('*.pdf'))
        if not pdfs:
            # Fallback to specific files
            pdfs = [
                sample_dir / 'Heidegger_BeingAndTime.pdf',
                sample_dir / 'Derrida_WritingAndDifference.pdf',
                sample_dir / 'Derrida_MarginsOfPhilosophy.pdf',
                sample_dir / 'Heidegger_Pathmarks.pdf',
                sample_dir / 'Kant_CritiqueOfJudgement.pdf',
            ]
        pdfs = [p for p in pdfs if p.exists()]

    if not pdfs:
        print("No PDFs found to process!")
        return

    print(f"\n{'#'*70}")
    print(f"# EXTRACTING TRICKY OCR SAMPLES - EXTENSIVE TESTING")
    print(f"# PDFs to process: {len(pdfs)}")
    print(f"# Categories: 20+")
    print(f"{'#'*70}")

    all_results = {}
    total_samples = 0
    category_totals = defaultdict(int)

    for pdf_path in pdfs:
        results = process_pdf(pdf_path, extensive=args.extensive)
        all_results[results['source_pdf']] = results
        total_samples += results['total_samples']

        for cat, samples in results['by_category'].items():
            category_totals[cat] += len(samples)

    # Save results
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Print comprehensive summary
    print(f"\n{'='*70}")
    print(f"COMPREHENSIVE SUMMARY")
    print(f"{'='*70}")
    print(f"PDFs processed: {len(all_results)}")
    print(f"Total samples extracted: {total_samples}")
    print(f"Output saved to: {output_path}")

    print(f"\n{'='*70}")
    print("SAMPLES BY CATEGORY")
    print(f"{'='*70}")

    for cat, count in sorted(category_totals.items(), key=lambda x: -x[1]):
        bar = '█' * min(count // 2, 30)
        print(f"  {cat:30s} {count:4d} {bar}")

    # Print example from each category
    print(f"\n{'='*70}")
    print("EXAMPLE FROM EACH CATEGORY")
    print(f"{'='*70}")

    shown_categories = set()
    for pdf_name, results in all_results.items():
        for sample in results['samples']:
            cat = sample['category']
            if cat not in shown_categories:
                shown_categories.add(cat)
                print(f"\n[{cat}] ({sample.get('subcategory', '')})")
                print(f"  PDF: {pdf_name}, Page {sample['page_num']}")
                print(f"  Text: {sample['original_text'][:60]}...")
                print(f"  Context: {sample['context'][:80]}...")


if __name__ == '__main__':
    main()
