#!/usr/bin/env python3
"""
Spike 06b: Validate Tricky Samples Against Ground Truth

PURPOSE: Verify that extracted samples are actually problematic and establish
         proper ground truth for OCR correction testing.

APPROACH:
1. Extract image regions for each sample
2. Compare OCR text against visual inspection
3. Use spell checking to detect actual errors
4. Compare against known-good parallel texts (when available)
5. Generate validated ground truth pairs: (ocr_text, correct_text)

RUN:
  uv run python spikes/06b_validate_samples.py --sample-check 50
  uv run python spikes/06b_validate_samples.py --category german_terms
  uv run python spikes/06b_validate_samples.py --generate-pairs
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from typing import Optional
import io

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
    print("Warning: spellchecker not available")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@dataclass
class ValidatedSample:
    """A sample with ground truth validation."""
    source_pdf: str
    page_num: int
    category: str
    subcategory: str = ""

    # Original extraction
    extracted_text: str = ""
    context: str = ""

    # Ground truth
    is_ocr_error: bool = False  # True if OCR produced wrong text
    correct_text: str = ""  # What the text should be
    error_type: str = ""  # character_substitution, ligature_split, etc.

    # Validation metadata
    validation_method: str = ""  # spell_check, visual, parallel_text, manual
    confidence: float = 0.0  # How confident we are in the ground truth
    needs_manual_review: bool = True

    # Optional image snippet
    image_path: str = ""

    notes: str = ""


class SampleValidator:
    """Validate extracted samples and establish ground truth."""

    def __init__(self, samples_file: str = "spikes/tricky_samples.json"):
        with open(samples_file) as f:
            self.samples_data = json.load(f)

        self.spell = SpellChecker() if SPELLCHECK_AVAILABLE else None

        # Known corrections dictionary (manually verified)
        self.known_corrections = {
            # Common OCR errors we've verified
            'beautlful': 'beautiful',
            'tbe': 'the',
            'tbat': 'that',
            'wbich': 'which',
            'rnorning': 'morning',
            'rn': 'm',  # When standalone
            # Add more as we verify them
        }

        # Philosophy vocabulary that spell checkers wrongly flag
        self.valid_scholarly_terms = {
            # German
            'dasein', 'sein', 'seiendes', 'seiende', 'vorhandenheit', 'zuhandenheit',
            'mitsein', 'gerede', 'neugier', 'befindlichkeit', 'verstehen', 'rede',
            'sorge', 'angst', 'gewissen', 'schuld', 'entschlossenheit', 'zeitlichkeit',
            'geschichtlichkeit', 'wiederholung', 'augenblick', 'schicksal', 'geschick',
            'ereignis', 'gelassenheit', 'lichtung', 'aufhebung', 'geist', 'wesen',
            'begriff', 'vermittlung', 'negation', 'bestimmung', 'lebenswelt',
            'noema', 'noesis', 'epoché', 'weltanschauung', 'zeitgeist',
            # French
            'différance', 'supplement', 'pharmakon', 'grammatologie', 'déconstruction',
            'écriture', 'présence', 'signifiant', 'signifié', 'épistémè', 'discours',
            'jouissance',
            # Latin
            'priori', 'posteriori', 'passim', 'alia',
            # Philosopher names
            'heidegger', 'husserl', 'derrida', 'foucault', 'nietzsche', 'kierkegaard',
            'schopenhauer', 'wittgenstein', 'habermas', 'gadamer', 'ricoeur', 'levinas',
            'merleau', 'ponty', 'sartre', 'beauvoir', 'deleuze', 'guattari', 'badiou',
            'žižek', 'agamben', 'arendt', 'adorno', 'horkheimer', 'benjamin',
            'hegel', 'kant', 'descartes', 'spinoza', 'leibniz', 'locke', 'hume',
            'berkeley', 'plato', 'aristotle', 'socrates', 'parmenides', 'heraclitus',
        }

    def validate_with_spellcheck(self, text: str) -> tuple[bool, str, float]:
        """
        Use spell checking to detect if text is likely an error.

        Returns: (is_error, suggested_correction, confidence)
        """
        if not self.spell:
            return False, text, 0.0

        # Clean the text
        word = text.lower().strip()

        # Skip if it's a known valid scholarly term
        if word in self.valid_scholarly_terms:
            return False, text, 0.95

        # Skip if it's a number or punctuation
        if not word.isalpha():
            return False, text, 0.5

        # Check if it's in the dictionary
        if word in self.spell:
            return False, text, 0.9

        # It's misspelled - get correction
        correction = self.spell.correction(word)

        if correction and correction != word:
            # Calculate confidence based on edit distance
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(None, word, correction).ratio()
            confidence = similarity * 0.8  # Scale down a bit

            return True, correction, confidence

        # No good correction found - might be valid term we don't know
        return False, text, 0.3

    def validate_known_pattern(self, text: str, category: str) -> tuple[bool, str, float]:
        """
        Check against known OCR error patterns.

        Returns: (is_error, correction, confidence)
        """
        text_lower = text.lower()

        # Direct lookup
        if text_lower in self.known_corrections:
            return True, self.known_corrections[text_lower], 0.95

        # Pattern-based detection
        patterns = [
            # rn -> m confusion
            (r'\brn\b', 'm', 'rn_m', 0.7),
            (r'(\w)rn(\w)', r'\1m\2', 'rn_m_word', 0.6),

            # tbe -> the
            (r'\btbe\b', 'the', 'b_h', 0.9),
            (r'\btbat\b', 'that', 'b_h', 0.9),

            # Common character confusions
            (r'\bcl(\w+)', r'd\1', 'cl_d', 0.5),  # Lower confidence - often wrong
        ]

        for pattern, replacement, error_type, confidence in patterns:
            if re.search(pattern, text_lower):
                corrected = re.sub(pattern, replacement, text_lower)
                if corrected != text_lower:
                    return True, corrected, confidence

        return False, text, 0.0

    def extract_image_region(
        self,
        pdf_path: str,
        page_num: int,
        search_text: str,
        output_dir: Path,
        dpi: int = 150
    ) -> Optional[str]:
        """
        Extract image region around the text for visual verification.

        Returns: path to saved image, or None if failed
        """
        if not PIL_AVAILABLE:
            return None

        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]  # 0-indexed

            # Search for text
            text_instances = page.search_for(search_text)

            if not text_instances:
                doc.close()
                return None

            # Get first match
            rect = text_instances[0]

            # Expand rect for context
            padding = 20
            clip_rect = fitz.Rect(
                rect.x0 - padding,
                rect.y0 - padding,
                rect.x1 + padding,
                rect.y1 + padding
            )

            # Render to image
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat, clip=clip_rect)

            # Save image
            output_dir.mkdir(parents=True, exist_ok=True)
            safe_text = re.sub(r'[^\w]', '_', search_text[:20])
            img_path = output_dir / f"p{page_num}_{safe_text}.png"
            pix.save(str(img_path))

            doc.close()
            return str(img_path)

        except Exception as e:
            print(f"  Warning: Could not extract image: {e}")
            return None

    def validate_sample(self, sample: dict, extract_images: bool = False) -> ValidatedSample:
        """Validate a single sample and determine ground truth."""

        validated = ValidatedSample(
            source_pdf=sample['source_pdf'],
            page_num=sample['page_num'],
            category=sample['category'],
            subcategory=sample.get('subcategory', ''),
            extracted_text=sample['original_text'],
            context=sample.get('context', ''),
        )

        text = sample['original_text']

        # Method 1: Check known patterns
        is_error, correction, conf = self.validate_known_pattern(text, sample['category'])
        if is_error and conf > 0.7:
            validated.is_ocr_error = True
            validated.correct_text = correction
            validated.error_type = 'known_pattern'
            validated.validation_method = 'pattern_match'
            validated.confidence = conf
            validated.needs_manual_review = conf < 0.9
            return validated

        # Method 2: Spell check
        is_error, correction, conf = self.validate_with_spellcheck(text)
        if is_error and conf > 0.5:
            validated.is_ocr_error = True
            validated.correct_text = correction
            validated.error_type = 'spelling'
            validated.validation_method = 'spell_check'
            validated.confidence = conf
            validated.needs_manual_review = True  # Spell check needs review
            return validated

        # Method 3: Category-specific validation
        if sample['category'] == 'german_terms':
            # German terms are likely correct if they match known vocabulary
            if text.lower() in self.valid_scholarly_terms:
                validated.is_ocr_error = False
                validated.correct_text = text
                validated.validation_method = 'vocabulary_match'
                validated.confidence = 0.95
                validated.needs_manual_review = False
                return validated

        elif sample['category'] == 'hyphenation':
            # Hyphenation samples need manual review for correct rejoining
            validated.needs_manual_review = True
            validated.validation_method = 'requires_manual'
            validated.confidence = 0.0
            validated.notes = "Hyphenation requires context to determine correct form"
            return validated

        elif sample['category'] == 'ocr_char_confusion':
            # These are likely errors by definition
            validated.is_ocr_error = True
            validated.validation_method = 'category_heuristic'
            validated.confidence = 0.6
            validated.needs_manual_review = True
            validated.notes = "Character confusion pattern detected, needs verification"
            return validated

        # Default: needs manual review
        validated.validation_method = 'unvalidated'
        validated.confidence = 0.0
        validated.needs_manual_review = True

        return validated

    def validate_samples(
        self,
        max_samples: int = 100,
        categories: Optional[list] = None,
        extract_images: bool = False
    ) -> dict:
        """Validate a batch of samples."""

        results = {
            'validated': [],
            'needs_review': [],
            'statistics': defaultdict(int)
        }

        count = 0
        for pdf_name, pdf_data in self.samples_data.items():
            for sample in pdf_data['samples']:
                if categories and sample['category'] not in categories:
                    continue

                if count >= max_samples:
                    break

                validated = self.validate_sample(sample, extract_images)

                if validated.needs_manual_review:
                    results['needs_review'].append(asdict(validated))
                else:
                    results['validated'].append(asdict(validated))

                # Statistics
                results['statistics'][f"category_{sample['category']}"] += 1
                if validated.is_ocr_error:
                    results['statistics']['confirmed_errors'] += 1
                if validated.needs_manual_review:
                    results['statistics']['needs_review'] += 1
                else:
                    results['statistics']['auto_validated'] += 1

                count += 1

            if count >= max_samples:
                break

        results['statistics'] = dict(results['statistics'])
        return results

    def generate_ground_truth_pairs(self, validated_results: dict) -> list[dict]:
        """Generate (input, expected_output) pairs for testing."""

        pairs = []

        for sample in validated_results['validated']:
            if sample['is_ocr_error'] and sample['correct_text']:
                pairs.append({
                    'input': sample['extracted_text'],
                    'expected': sample['correct_text'],
                    'category': sample['category'],
                    'confidence': sample['confidence'],
                    'source': f"{sample['source_pdf']}:p{sample['page_num']}"
                })

        return pairs

    def print_validation_report(self, results: dict):
        """Print a summary report of validation results."""

        stats = results['statistics']

        print(f"\n{'='*70}")
        print("VALIDATION REPORT")
        print(f"{'='*70}")

        total = stats.get('auto_validated', 0) + stats.get('needs_review', 0)
        print(f"\nTotal samples processed: {total}")
        print(f"Auto-validated: {stats.get('auto_validated', 0)}")
        print(f"Needs manual review: {stats.get('needs_review', 0)}")
        print(f"Confirmed OCR errors: {stats.get('confirmed_errors', 0)}")

        print(f"\n{'='*70}")
        print("BY CATEGORY")
        print(f"{'='*70}")

        for key, value in sorted(stats.items()):
            if key.startswith('category_'):
                cat = key.replace('category_', '')
                print(f"  {cat:30s} {value:4d}")

        print(f"\n{'='*70}")
        print("SAMPLES NEEDING MANUAL REVIEW")
        print(f"{'='*70}")

        for sample in results['needs_review'][:10]:
            print(f"\n  [{sample['category']}] {sample['source_pdf']}:p{sample['page_num']}")
            print(f"    Text: {sample['extracted_text'][:50]}...")
            print(f"    Reason: {sample['validation_method']}")
            if sample['notes']:
                print(f"    Note: {sample['notes']}")

        if len(results['needs_review']) > 10:
            print(f"\n  ... and {len(results['needs_review']) - 10} more")

        print(f"\n{'='*70}")
        print("VALIDATED GROUND TRUTH PAIRS")
        print(f"{'='*70}")

        pairs = self.generate_ground_truth_pairs(results)
        for pair in pairs[:10]:
            print(f"\n  '{pair['input']}' → '{pair['expected']}'")
            print(f"    Category: {pair['category']}, Confidence: {pair['confidence']:.2f}")

        if len(pairs) > 10:
            print(f"\n  ... and {len(pairs) - 10} more pairs")

        return pairs


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate tricky samples")
    parser.add_argument('--sample-check', type=int, default=100, help='Number of samples to validate')
    parser.add_argument('--category', type=str, help='Specific category to validate')
    parser.add_argument('--extract-images', action='store_true', help='Extract image regions')
    parser.add_argument('--output', type=str, default='spikes/validated_samples.json')
    args = parser.parse_args()

    validator = SampleValidator()

    categories = [args.category] if args.category else None

    print(f"Validating up to {args.sample_check} samples...")
    if categories:
        print(f"Categories: {categories}")

    results = validator.validate_samples(
        max_samples=args.sample_check,
        categories=categories,
        extract_images=args.extract_images
    )

    pairs = validator.print_validation_report(results)

    # Save results
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump({
            'results': results,
            'ground_truth_pairs': pairs
        }, f, indent=2)

    print(f"\n✅ Results saved to: {output_path}")

    # Also save just the pairs for easy use in tests
    pairs_path = output_path.with_suffix('.pairs.json')
    with open(pairs_path, 'w') as f:
        json.dump(pairs, f, indent=2)
    print(f"✅ Ground truth pairs saved to: {pairs_path}")


if __name__ == '__main__':
    main()
