#!/usr/bin/env python3
"""
Spike 06c: Generate REAL Ground Truth for OCR Correction Testing

PURPOSE: Create verified (ocr_error, correct_text) pairs by actually detecting
         OCR errors through comparison, not pattern matching.

APPROACH:
1. Compare PDF text against known-good parallel texts (Gutenberg, etc.)
2. Extract image regions and re-OCR to detect discrepancies
3. Use spell checking on OCR'd scans (not born-digital)
4. Manual annotation for small high-quality corpus

RUN:
  uv run python spikes/06c_real_ground_truth.py scan-errors sample.pdf
  uv run python spikes/06c_real_ground_truth.py compare-parallel kant.pdf kant_gutenberg.txt
  uv run python spikes/06c_real_ground_truth.py annotate kant.pdf --pages 50-60
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from typing import Optional
from difflib import SequenceMatcher, get_close_matches

try:
    import fitz
except ImportError:
    print("Install PyMuPDF: uv add pymupdf")
    exit(1)

try:
    from spellchecker import SpellChecker
    SPELLCHECK_AVAILABLE = True
except ImportError:
    SPELLCHECK_AVAILABLE = False


@dataclass
class GroundTruthPair:
    """A verified (ocr_text, correct_text) pair."""
    ocr_text: str  # What the OCR produced
    correct_text: str  # What it should be
    error_type: str  # character_substitution, ligature, hyphenation, etc.
    source_pdf: str
    page_num: int
    context: str = ""
    verification_method: str = ""  # spell_check, parallel_text, manual, re_ocr
    confidence: float = 0.0


# Philosophy vocabulary that spell checkers wrongly flag
VALID_SCHOLARLY_TERMS = {
    # German philosophy
    'dasein', 'sein', 'seiendes', 'seiende', 'vorhandenheit', 'zuhandenheit',
    'mitsein', 'gerede', 'neugier', 'befindlichkeit', 'verstehen', 'rede',
    'sorge', 'angst', 'gewissen', 'schuld', 'entschlossenheit', 'zeitlichkeit',
    'geschichtlichkeit', 'wiederholung', 'augenblick', 'schicksal', 'geschick',
    'ereignis', 'gelassenheit', 'lichtung', 'aufhebung', 'geist', 'wesen',
    'begriff', 'vermittlung', 'negation', 'bestimmung', 'lebenswelt',
    'noema', 'noesis', 'weltanschauung', 'zeitgeist', 'schadenfreude',
    # French philosophy
    'différance', 'differance', 'supplement', 'pharmakon', 'grammatologie',
    'déconstruction', 'deconstruction', 'écriture', 'ecriture', 'présence',
    'signifiant', 'signifié', 'épistémè', 'episteme', 'discours', 'jouissance',
    # Greek transliterations
    'logos', 'nous', 'physis', 'techne', 'polis', 'aletheia', 'episteme',
    'praxis', 'theoria', 'eidos', 'telos', 'arche', 'ousia', 'energeia',
    # Latin terms and abbreviations
    'priori', 'posteriori', 'passim', 'alia', 'facto', 'jure', 'generis',
    'viz', 'ibid', 'ibidem', 'loc', 'cit', 'sic', 'circa', 'ergo',
    'sensus', 'communis', 'modus', 'ponens', 'tollens', 'operandi',
    'vivendi', 'cogito', 'ergo', 'sum', 'vide', 'infra', 'supra',
    'ante', 'post', 'per', 'pro', 'contra', 'qua', 'ipso',
    # Major philosopher names (lowercase for checking)
    'heidegger', 'husserl', 'derrida', 'foucault', 'nietzsche', 'kierkegaard',
    'schopenhauer', 'wittgenstein', 'habermas', 'gadamer', 'ricoeur', 'levinas',
    'merleau', 'ponty', 'sartre', 'beauvoir', 'deleuze', 'guattari', 'badiou',
    'agamben', 'arendt', 'adorno', 'horkheimer', 'benjamin', 'hegel', 'kant',
    'descartes', 'spinoza', 'leibniz', 'locke', 'hume', 'berkeley', 'plato',
    'aristotle', 'socrates', 'parmenides', 'heraclitus', 'thales', 'pythagoras',
    # Scholars commonly cited in philosophy texts
    'hutcheson', 'kivy', 'guyer', 'allison', 'ameriks', 'kemp', 'smith',
    'pluhar', 'meredith', 'bernard', 'crawford', 'zammito', 'ginsborg',
    'budd', 'wenzel', 'crowther', 'makkreel', 'pillow', 'crawford',
    'longuenesse', 'pippin', 'sedgwick', 'stern', 'beiser', 'forster',
    'breazeale', 'lenz', 'boulton', 'burke', 'kuehn', 'cassirer',
    'gregor', 'paton', 'kemp', 'walker', 'friedman', 'beck', 'meerbote',
    'kitcher', 'abela', 'grier', 'watkins', 'langton', 'reath', 'timmermann',
    # German articles and common words appearing in titles/references
    'der', 'die', 'das', 'und', 'zur', 'ein', 'eine', 'einer', 'eines',
    'von', 'mit', 'auf', 'aus', 'bei', 'nach', 'uber', 'über', 'fur', 'für',
    'kritik', 'urteilskraft', 'vernunft', 'reinen', 'praktischen',
    # German philosophical terms that appear in scholarly texts
    'theoretisch', 'praktisch', 'erkennen', 'wissen', 'denken', 'anschauung',
    'verstand', 'einbildungskraft', 'zweckmäßigkeit', 'zweckmassigkeit',
    'transzendental', 'transzendent', 'immanent', 'erscheinung', 'ding',
    # French scholarly terms
    'sur', 'les', 'une', 'des', 'pour', 'dans', 'avec', 'par',
    # Academic publishers
    'routledge', 'springer', 'blackwell', 'wiley', 'oxford', 'cambridge',
    'macmillan', 'palgrave', 'princeton', 'harvard', 'yale', 'stanford',
    'cornell', 'columbia', 'chicago', 'northwestern', 'suny', 'nijhoff',
    'martinus', 'kluwer', 'reidel', 'brill', 'gruyter', 'bobbs', 'merrill',
    'kegan', 'duckworth', 'penguin', 'hackett', 'wadsworth', 'cengage',
    # Common scholarly terms
    'epistemological', 'ontological', 'phenomenological', 'hermeneutic',
    'dialectical', 'transcendental', 'immanent', 'apodictic', 'apperception',
    'intentionality', 'intersubjectivity', 'noumenon', 'noumenal', 'phenomenal',
    'teleological', 'deontological', 'consequentialist', 'cognitivist',
    'noncognitivist', 'intuitionist', 'expressivist', 'projectivist',
    # Terms that appear in philosophical texts but aren't in dictionaries
    'purposiveness', 'purposive', 'subsumption', 'subsume', 'supersensible',
    'determinative', 'reflective', 'heautonomous', 'heteronomous', 'systematicity',
    # Valid words often flagged by spell checkers
    'perceiver', 'perceivers', 'unstatable', 'cognitions', 'cognates',
    'intersubjective', 'subjectivism', 'objectivism', 'representationalism',
    'foundationalism', 'coherentism', 'reliabilism', 'contextualism',
    # More valid philosophical/scholarly terms
    'antinomies', 'antinomy', 'teleologically', 'teleological', 'teleology',
    'encyclopaedic', 'encyclopaedia', 'judgements', 'judgement',
    'analysing', 'characterise', 'characterised', 'recognise', 'recognised',
    'realise', 'realised', 'organisation', 'organised', 'conceptualise',
    'aesthetical', 'synthetical', 'analytical', 'systematical', 'problematics',
    'finality', 'causality', 'modality', 'totality', 'actuality', 'necessity',
    'unprimed', 'subsumed', 'presupposed', 'supersensible', 'apprehension',
    # Kantian/philosophical terms that look like misspellings
    'categorial', 'temporalized', 'spatialized', 'conceptualized', 'schematized',
    'ideated', 'intuited', 'cognized', 'transcendentally', 'synthetically',
    'analyticity', 'apodicticity', 'spontaneity', 'receptivity', 'sensibility',
    'discursivity', 'intuitivity', 'categorially', 'schematism', 'exhibiting',
}


def is_roman_numeral(word: str) -> bool:
    """Check if word is a Roman numeral (i, ii, iii, iv, v, vi, vii, viii, ix, x, etc.)."""
    # Normalize: replace common OCR confusions (l with i, L with I)
    word_normalized = word.lower().replace('l', 'i')

    # Only valid Roman numeral characters
    if not re.match(r'^[ivxcdm]+$', word_normalized):
        return False

    # Generate common Roman numerals programmatically (1-999)
    valid_romans = set()

    # Units
    units = ['', 'i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix']
    tens = ['', 'x', 'xx', 'xxx', 'xl', 'l', 'lx', 'lxx', 'lxxx', 'xc']
    hundreds = ['', 'c', 'cc', 'ccc', 'cd', 'd', 'dc', 'dcc', 'dccc', 'cm']

    # Generate 1-999
    for h in range(10):
        for t in range(10):
            for u in range(10):
                num = h * 100 + t * 10 + u
                if num > 0:
                    roman = hundreds[h] + tens[t] + units[u]
                    valid_romans.add(roman)
                    # Also add version with l->i normalization applied
                    valid_romans.add(roman.replace('l', 'i'))

    return word_normalized in valid_romans


def is_hyphenation_fragment(word: str, context: str) -> bool:
    """
    Check if word looks like a hyphenation fragment from line breaks.

    Heuristics:
    - Very short words (< 5 chars) that are unusual
    - Word appears near a hyphen in context
    - Common word-ending fragments (tion, ment, ing, ed, ly)
    - Common word-beginning fragments (pre, un, re, dis)
    - Words ending in patterns that suggest truncation before suffix
    """
    word_lower = word.lower()

    # Check if word is near a hyphen in context (line-break hyphenation)
    hyphen_nearby = '-' in context or '- ' in context or ' -' in context

    # Common word-ending fragments (likely second half of hyphenated word)
    ending_fragments = {
        'tion', 'ment', 'ness', 'able', 'ible', 'ence', 'ance', 'ious', 'eous',
        'tive', 'sive', 'ful', 'less', 'ity', 'ally', 'ized', 'ised', 'izing',
        'ising', 'ical', 'ular', 'ward', 'wise', 'hood', 'ship', 'ings', 'ments',
        'tions', 'nesses', 'ables', 'ibles', 'ences', 'ances', 'ties', 'lly',
        'ing', 'ive', 'nal', 'lar', 'ual', 'ous', 'ble', 'ply', 'tly',
        # Second halves of hyphenated words
        'tinguishes', 'minate', 'logical', 'tional', 'tively',
    }

    # Common word-beginning fragments (likely first half of hyphenated word)
    beginning_fragments = {
        'pre', 'dis', 'mis', 'over', 'under', 'inter', 'intra', 'trans', 'super',
        'semi', 'anti', 'counter', 'multi', 'poly', 'mono', 'uni', 'bi', 'tri',
        'sub', 'hyper', 'meta', 'para', 'pseudo', 'proto', 'neo', 'post',
        'non', 'self', 'ex', 'co', 'un', 're', 'de', 'en', 'em', 'im', 'in',
        'judg', 'deter', 'percep', 'concep', 'beauti', 'wonder', 'thought',
        'particu', 'determi', 'contin', 'teleol', 'pur', 'incl', 'excl',
        # Common hyphenation break points (word fragments before suffix)
        'critiq', 'subjec', 'objec', 'imagina', 'presupposi', 'supposi',
        'sensa', 'presenta', 'representa', 'condi', 'positi', 'composi',
        'proposi', 'disposi', 'opposi', 'exposi', 'teleo', 'deonto',
        'epistemo', 'ontolo', 'phenomeno', 'hermeneu', 'dialec',
        'transcenden', 'imma', 'cogni', 'recogni', 'posiveness',
        # More hyphenation fragments commonly found
        'appro', 'indi', 'infini', 'espe', 'simi', 'natu',
        'rela', 'proba', 'poten', 'essen', 'funda', 'speci',
        'parti', 'ration', 'moder', 'princi', 'analyti', 'syntheti',
        'empiri', 'transcen', 'philo', 'psycho', 'socio', 'anthro',
        # More fragments found in Kant text
        'distin', 'argu', 'supersen', 'interpre', 'prc', 'ject',
        'neces', 'suffi', 'possi', 'provi', 'asser', 'depen',
        'atten', 'inten', 'exten', 'preten', 'reten', 'conten',
        'compre', 'appre', 'repre', 'expre', 'impre', 'depre',
        'experi', 'compari', 'prepari', 'proce', 'conce', 'rece',
        # Even more fragments found
        'tradi', 'orienta', 'contribu', 'introduc', 'authori', 'inevi',
        'knowl', 'prin', 'accor', 'vol', 'enced', 'cepts', 'tably',
        'activi', 'passivi', 'relativi', 'objecti', 'subjecti', 'effecti',
        'collec', 'protec', 'correc', 'connec', 'selec', 'reflec',
        'charac', 'predica', 'indica', 'dedica', 'applica', 'implica',
        'modifi', 'classi', 'speci', 'verifi', 'justi', 'certi',
        'satis', 'quanti', 'guaran', 'rema', 'assu', 'consu',
        # More fragments
        'corres', 'ponding', 'exhibi', 'mediat', 'transla', 'expe',
        'cau', 'cor', 'pon', 'ding', 'sal', 'tar', 'lar',
        'natu', 'cultu', 'structu', 'litera', 'tempora', 'spa',
        # Even more fragments from Kant text
        'dictions', 'dictory', 'practi', 'cally', 'estab', 'lished',
        'oughts', 'contra', 'ically', 'istically', 'atically',
        'ducted', 'duced', 'duces', 'ducing', 'duce',
    }

    # Common second halves of hyphenated words
    second_halves = {
        'priate', 'cially', 'larly', 'duction', 'cated', 'rial', 'tial',
        'trary', 'cular', 'ticular', 'matic', 'namic', 'logical', 'sophical',
        'mental', 'mental', 'rative', 'native', 'mative', 'sentative',
        'tative', 'atively', 'istically', 'ologically', 'istically',
        # More second halves
        'guished', 'sible', 'tation', 'sary', 'cient', 'dent',
        'tion', 'sion', 'gence', 'dence', 'rence', 'ence',
        'hension', 'dure', 'dural', 'ssion', 'ssary',
    }
    ending_fragments.update(second_halves)

    # If very short and near hyphen, likely a fragment
    if len(word_lower) <= 4 and hyphen_nearby:
        return True

    # Check if it's a known fragment pattern
    if word_lower in ending_fragments or word_lower in beginning_fragments:
        return True

    # Check for words that look incomplete (end in consonant cluster without vowel)
    if len(word_lower) <= 6:
        # Words ending in unusual patterns that suggest truncation
        truncated_endings = ['judg', 'ment', 'tion', 'tive', 'sive', 'ence', 'ance']
        for ending in truncated_endings:
            if word_lower.endswith(ending) or word_lower == ending:
                return True

    # Pattern-based detection: words ending in patterns that suggest
    # truncation before common suffixes like -tion, -tive, -ment, -ness
    # These are truncated words like "imagina-" (from imagination)
    truncation_patterns = [
        # Before -tion/-tions
        r'.*[aeiou]na$',      # imagina-, presenta-, representa-
        r'.*[aeiou]si$',      # presupposi-, supposi-, proposi-
        r'.*[aeiou]ti$',      # sensa-, posi-, condi-
        # Before -tive/-tively
        r'.*ec$',             # subjec-, objec-, projec-
        r'.*iq$',             # critiq- (critique)
        # Before -logical
        r'.*eo$',             # teleo-, stereo-
        r'.*lo$',             # onto-, epistemo-
    ]

    for pattern in truncation_patterns:
        if re.match(pattern, word_lower) and hyphen_nearby:
            return True

    return False


class RealGroundTruthExtractor:
    """Extract real OCR errors with verified ground truth."""

    def __init__(self):
        self.spell = SpellChecker() if SPELLCHECK_AVAILABLE else None
        self.pairs: list[GroundTruthPair] = []

    def is_scanned_pdf(self, doc: fitz.Document) -> bool:
        """Detect if PDF is OCR'd scan vs born-digital."""
        # Check first few pages for signs of OCR
        ocr_indicators = 0
        for i in range(min(10, len(doc))):
            page = doc[i]

            # OCR'd PDFs often have many fonts (from recognition)
            fonts = page.get_fonts()
            if len(fonts) > 20:
                ocr_indicators += 1

            # Check for image blocks (scanned pages)
            blocks = page.get_text("dict")["blocks"]
            has_image = any(b.get("type") == 1 for b in blocks)
            if has_image:
                ocr_indicators += 1

        return ocr_indicators >= 5

    def scan_for_spell_errors(
        self,
        pdf_path: str,
        pages: Optional[range] = None,
        max_errors: int = 100
    ) -> list[GroundTruthPair]:
        """
        Find actual spelling errors in OCR'd text.
        Only useful for scanned/OCR'd PDFs, not born-digital.
        """
        if not self.spell:
            print("Spell checker not available")
            return []

        doc = fitz.open(pdf_path)
        pdf_name = Path(pdf_path).name

        if not self.is_scanned_pdf(doc):
            print(f"Warning: {pdf_name} appears to be born-digital, spell errors may be intentional")

        pairs = []
        skipped = {'roman': 0, 'scholarly': 0, 'dictionary': 0, 'fragment': 0, 'proper_name': 0}
        page_range = pages or range(len(doc))

        for page_idx in page_range:
            if page_idx >= len(doc):
                break

            page = doc[page_idx]
            text = page.get_text()

            # Extract words
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text)

            for word in words:
                if len(pairs) >= max_errors:
                    doc.close()
                    self._print_skip_stats(skipped)
                    return pairs

                word_lower = word.lower()

                # Skip Roman numerals
                if is_roman_numeral(word):
                    skipped['roman'] += 1
                    continue

                # Skip known valid terms
                if word_lower in VALID_SCHOLARLY_TERMS:
                    skipped['scholarly'] += 1
                    continue

                # Skip if in dictionary
                if word_lower in self.spell:
                    skipped['dictionary'] += 1
                    continue

                # Get context for fragment detection
                idx = text.lower().find(word_lower)
                start = max(0, idx - 50)
                end = min(len(text), idx + len(word) + 50)
                context = text[start:end].replace('\n', ' ')

                # Skip hyphenation fragments
                if is_hyphenation_fragment(word, context):
                    skipped['fragment'] += 1
                    continue

                # Skip words that look like proper names (capitalized, not at sentence start)
                if self._looks_like_proper_name(word, context):
                    skipped['proper_name'] += 1
                    continue

                # Get correction
                correction = self.spell.correction(word_lower)

                if correction and correction != word_lower:
                    # Verify this looks like a real OCR error
                    # (close edit distance, common OCR confusions)
                    if self._is_likely_ocr_error(word_lower, correction):
                        pairs.append(GroundTruthPair(
                            ocr_text=word,
                            correct_text=correction,
                            error_type=self._classify_error(word_lower, correction),
                            source_pdf=pdf_name,
                            page_num=page_idx + 1,
                            context=context,
                            verification_method='spell_check',
                            confidence=0.7  # Spell check needs review
                        ))

        doc.close()
        self._print_skip_stats(skipped)
        return pairs

    def _print_skip_stats(self, skipped: dict):
        """Print statistics about skipped words."""
        total = sum(skipped.values())
        if total > 0:
            print(f"\n  Filtering stats:")
            print(f"    Roman numerals skipped: {skipped['roman']}")
            print(f"    Scholarly terms skipped: {skipped['scholarly']}")
            print(f"    Dictionary words skipped: {skipped['dictionary']}")
            print(f"    Hyphenation fragments skipped: {skipped['fragment']}")
            print(f"    Proper names skipped: {skipped['proper_name']}")

    def _looks_like_proper_name(self, word: str, context: str) -> bool:
        """Check if word looks like a proper name (not an OCR error)."""
        # Must be capitalized
        if not word[0].isupper():
            return False

        # Check if it appears after sentence-ending punctuation (not a proper name indicator)
        # Look for patterns like ". Word" or "? Word" which suggest sentence start
        word_pos = context.find(word)
        if word_pos > 0:
            before = context[:word_pos].rstrip()
            if before and before[-1] in '.?!':
                return False  # Likely sentence start, not a name

        # Capitalized word in middle of sentence is likely a proper name
        # Additional check: if it's a short word, be more skeptical
        if len(word) >= 4:
            return True

        return False

    def _is_likely_ocr_error(self, ocr_word: str, correction: str) -> bool:
        """Check if this looks like a real OCR error vs intentional spelling."""
        # Must be close in edit distance
        similarity = SequenceMatcher(None, ocr_word, correction).ratio()
        if similarity < 0.6:
            return False

        # Common OCR confusion patterns
        ocr_patterns = [
            ('rn', 'm'),  # rn -> m
            ('cl', 'd'),  # cl -> d
            ('vv', 'w'),  # vv -> w
            ('li', 'h'),  # li -> h (less common)
            ('ii', 'n'),  # ii -> n
            ('tl', 'd'),  # tl -> d
            ('nn', 'm'),  # nn -> m
        ]

        for bad, good in ocr_patterns:
            if bad in ocr_word and good in correction:
                return True

        # Single character substitution is common in OCR
        if len(ocr_word) == len(correction):
            diffs = sum(1 for a, b in zip(ocr_word, correction) if a != b)
            if diffs <= 2:
                return True

        return similarity > 0.8

    def _classify_error(self, ocr_word: str, correction: str) -> str:
        """Classify the type of OCR error."""
        if 'rn' in ocr_word and 'm' in correction:
            return 'rn_to_m'
        if 'cl' in ocr_word and 'd' in correction:
            return 'cl_to_d'
        if 'vv' in ocr_word and 'w' in correction:
            return 'vv_to_w'

        if len(ocr_word) == len(correction):
            return 'character_substitution'

        return 'unknown'

    def compare_with_parallel_text(
        self,
        pdf_path: str,
        parallel_text_path: str,
        pages: Optional[range] = None
    ) -> list[GroundTruthPair]:
        """
        Compare PDF text against known-good parallel text (e.g., Gutenberg).
        This is the gold standard for ground truth.
        """
        doc = fitz.open(pdf_path)
        pdf_name = Path(pdf_path).name

        with open(parallel_text_path, encoding='utf-8') as f:
            parallel_text = f.read()

        # Normalize parallel text
        parallel_words = set(re.findall(r'\b\w+\b', parallel_text.lower()))

        pairs = []
        page_range = pages or range(len(doc))

        for page_idx in page_range:
            if page_idx >= len(doc):
                break

            page = doc[page_idx]
            text = page.get_text()

            # Find words not in parallel text
            pdf_words = re.findall(r'\b[a-zA-Z]{4,}\b', text)

            for word in pdf_words:
                word_lower = word.lower()

                # Skip if in parallel text (correct)
                if word_lower in parallel_words:
                    continue

                # Skip known vocabulary
                if word_lower in VALID_SCHOLARLY_TERMS:
                    continue

                # Find closest match in parallel text
                matches = get_close_matches(word_lower, parallel_words, n=1, cutoff=0.8)

                if matches:
                    correction = matches[0]

                    idx = text.lower().find(word_lower)
                    start = max(0, idx - 50)
                    end = min(len(text), idx + len(word) + 50)
                    context = text[start:end].replace('\n', ' ')

                    pairs.append(GroundTruthPair(
                        ocr_text=word,
                        correct_text=correction,
                        error_type=self._classify_error(word_lower, correction),
                        source_pdf=pdf_name,
                        page_num=page_idx + 1,
                        context=context,
                        verification_method='parallel_text',
                        confidence=0.9  # High confidence from parallel text
                    ))

        doc.close()
        return pairs

    def create_manual_annotation_file(
        self,
        pdf_path: str,
        output_path: str,
        pages: range
    ):
        """
        Create a YAML file for manual annotation of OCR errors.
        Human annotator fills in correct_text for each suspicious word.
        """
        doc = fitz.open(pdf_path)
        pdf_name = Path(pdf_path).name

        annotations = {
            'pdf': pdf_name,
            'pages': list(pages),
            'annotations': []
        }

        # Find suspicious words for annotation
        for page_idx in pages:
            if page_idx >= len(doc):
                break

            page = doc[page_idx]
            text = page.get_text()

            words = re.findall(r'\b[a-zA-Z]{3,}\b', text)

            for word in words:
                word_lower = word.lower()

                if word_lower in VALID_SCHOLARLY_TERMS:
                    continue

                if self.spell and word_lower not in self.spell:
                    idx = text.lower().find(word_lower)
                    start = max(0, idx - 40)
                    end = min(len(text), idx + len(word) + 40)
                    context = text[start:end].replace('\n', ' ')

                    annotations['annotations'].append({
                        'page': page_idx + 1,
                        'ocr_text': word,
                        'context': context,
                        'correct_text': '',  # Human fills this in
                        'is_error': None,  # Human marks True/False
                        'error_type': '',  # Human classifies
                        'notes': ''
                    })

        doc.close()

        # Save as YAML for easy editing
        import yaml
        with open(output_path, 'w') as f:
            yaml.dump(annotations, f, default_flow_style=False, allow_unicode=True)

        print(f"Created annotation file: {output_path}")
        print(f"Found {len(annotations['annotations'])} words for review")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate real OCR ground truth")
    subparsers = parser.add_subparsers(dest='command')

    # Scan for spell errors
    scan_parser = subparsers.add_parser('scan-errors', help='Find spelling errors in OCR')
    scan_parser.add_argument('pdf', help='PDF file to scan')
    scan_parser.add_argument('--pages', type=str, help='Page range (e.g., 50-100)')
    scan_parser.add_argument('--max', type=int, default=100, help='Max errors to find')
    scan_parser.add_argument('--output', type=str, default='spikes/real_ground_truth.json')

    # Compare with parallel text
    compare_parser = subparsers.add_parser('compare-parallel', help='Compare against known-good text')
    compare_parser.add_argument('pdf', help='PDF file')
    compare_parser.add_argument('parallel', help='Parallel text file (e.g., from Gutenberg)')
    compare_parser.add_argument('--pages', type=str, help='Page range')
    compare_parser.add_argument('--output', type=str, default='spikes/real_ground_truth.json')

    # Create annotation file
    annotate_parser = subparsers.add_parser('annotate', help='Create manual annotation file')
    annotate_parser.add_argument('pdf', help='PDF file')
    annotate_parser.add_argument('--pages', type=str, required=True, help='Page range (e.g., 50-60)')
    annotate_parser.add_argument('--output', type=str, default='spikes/annotations_needed.yaml')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    extractor = RealGroundTruthExtractor()

    # Parse page range
    def parse_pages(pages_str):
        if not pages_str:
            return None
        if '-' in pages_str:
            start, end = map(int, pages_str.split('-'))
            return range(start - 1, end)  # Convert to 0-indexed
        return range(int(pages_str) - 1, int(pages_str))

    if args.command == 'scan-errors':
        pages = parse_pages(args.pages)
        pairs = extractor.scan_for_spell_errors(args.pdf, pages, args.max)

        print(f"\n{'='*70}")
        print(f"REAL OCR ERRORS FOUND: {len(pairs)}")
        print(f"{'='*70}")

        for pair in pairs[:20]:
            print(f"\n  '{pair.ocr_text}' → '{pair.correct_text}'")
            print(f"    Type: {pair.error_type}, Confidence: {pair.confidence:.2f}")
            print(f"    Source: {pair.source_pdf}:p{pair.page_num}")
            print(f"    Context: ...{pair.context[:60]}...")

        if len(pairs) > 20:
            print(f"\n  ... and {len(pairs) - 20} more")

        # Save
        with open(args.output, 'w') as f:
            json.dump([asdict(p) for p in pairs], f, indent=2)
        print(f"\n✅ Saved to: {args.output}")

    elif args.command == 'compare-parallel':
        pages = parse_pages(args.pages)
        pairs = extractor.compare_with_parallel_text(args.pdf, args.parallel, pages)

        print(f"\nFound {len(pairs)} discrepancies with parallel text")

        for pair in pairs[:20]:
            print(f"  '{pair.ocr_text}' → '{pair.correct_text}' (conf: {pair.confidence:.2f})")

        with open(args.output, 'w') as f:
            json.dump([asdict(p) for p in pairs], f, indent=2)
        print(f"\n✅ Saved to: {args.output}")

    elif args.command == 'annotate':
        pages = parse_pages(args.pages)
        extractor.create_manual_annotation_file(args.pdf, args.output, pages)


if __name__ == '__main__':
    main()
