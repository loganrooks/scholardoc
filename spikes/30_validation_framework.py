#!/usr/bin/env python3
"""
Spike 30: Proper Validation Framework

Build a comprehensive validation set from ALL ground truth data,
with proper metrics and timing measurements.

Goals:
1. Extract ALL error pairs from classified pages (not just 30)
2. Build proper train/validation/test splits
3. Measure what matters: detection rate, false positives, timing, re-OCR volume
4. Document the validation methodology
"""

import json
import glob
import re
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

# =============================================================================
# VALIDATION SET BUILDER
# =============================================================================

@dataclass
class ErrorPair:
    """A single OCR error with its correction."""
    ocr_text: str
    correct_text: str
    source_doc: str
    source_page: int
    error_type: str  # substitution, hyphenation, umlaut, etc.
    classification: str  # GOOD, MARGINAL, BAD
    context: str = ""


@dataclass
class ValidationSet:
    """A complete validation set with metadata."""
    error_pairs: list[ErrorPair]
    correct_words: set  # Known correct words for false positive testing
    metadata: dict = field(default_factory=dict)

    def summary(self) -> dict:
        by_type = defaultdict(int)
        by_doc = defaultdict(int)
        by_class = defaultdict(int)

        for ep in self.error_pairs:
            by_type[ep.error_type] += 1
            by_doc[ep.source_doc] += 1
            by_class[ep.classification] += 1

        return {
            'total_errors': len(self.error_pairs),
            'correct_words': len(self.correct_words),
            'by_type': dict(by_type),
            'by_document': dict(by_doc),
            'by_classification': dict(by_class),
        }


def extract_error_pairs_from_evidence(evidence: str, doc: str, page: int, classification: str) -> list[ErrorPair]:
    """Extract error pairs from an evidence string."""
    pairs = []

    # Pattern: "word → correction" or "word -> correction"
    # Also handle: "word → correction (description)"

    # Try arrow patterns
    if '→' in evidence:
        parts = evidence.split('→')
    elif '->' in evidence:
        parts = evidence.split('->')
    else:
        return pairs

    if len(parts) >= 2:
        # Extract words from before and after arrow
        ocr_match = re.search(r"['\"]?([a-zA-ZäöüÄÖÜßàâçéèêëîïôùûü]+)['\"]?\s*$", parts[0])
        correct_match = re.search(r"^\s*['\"]?([a-zA-ZäöüÄÖÜßàâçéèêëîïôùûü]+)['\"]?", parts[1])

        if ocr_match and correct_match:
            matches = [(ocr_match.group(1), correct_match.group(1))]
        else:
            matches = []
    else:
        matches = []
    for ocr, correct in matches:
        # Skip if same (not an error)
        if ocr.lower() == correct.lower():
            continue

        # Categorize error type
        if 'ii' in ocr.lower() or 'uu' in ocr.lower():
            error_type = 'umlaut'
        elif len(ocr) < len(correct) * 0.6:
            error_type = 'hyphenation'
        elif any(c in ocr for c in ';;|<>\\'):
            error_type = 'artifact'
        else:
            error_type = 'substitution'

        pairs.append(ErrorPair(
            ocr_text=ocr,
            correct_text=correct,
            source_doc=doc,
            source_page=page,
            error_type=error_type,
            classification=classification,
            context=evidence[:100]
        ))

    return pairs


def build_validation_set_from_ground_truth() -> ValidationSet:
    """Build a comprehensive validation set from ALL ground truth sources."""

    all_pairs = []
    correct_words = set()

    # Source 1: Verified error pairs (high quality)
    verified_path = Path('ground_truth/ocr_errors/ocr_error_pairs.json')
    if verified_path.exists():
        with open(verified_path) as f:
            verified = json.load(f)
        for p in verified:
            all_pairs.append(ErrorPair(
                ocr_text=p['ocr_text'],
                correct_text=p['correct_text'],
                source_doc='verified',
                source_page=p.get('page_number', 0),
                error_type=p.get('error_type', 'unknown'),
                classification='verified',
                context='verified pair'
            ))
            correct_words.add(p['correct_text'])

    # Source 2: Classified pages (bulk extraction)
    for f in glob.glob('ground_truth/ocr_quality/classified/*.json'):
        try:
            with open(f) as fp:
                data = json.load(fp)

            if not isinstance(data, dict):
                continue

            doc_name = data.get('document', 'unknown')
            pages = data.get('classified_pages', [])

            for page in pages:
                if not isinstance(page, dict):
                    continue

                page_num = page.get('page_number', 0)
                classification = page.get('classification', 'UNKNOWN')

                for ev in page.get('evidence', []):
                    if isinstance(ev, str) and '→' in ev:
                        pairs = extract_error_pairs_from_evidence(
                            ev, doc_name, page_num, classification
                        )
                        all_pairs.extend(pairs)
                        for p in pairs:
                            correct_words.add(p.correct_text)
        except Exception as e:
            print(f"Error processing {f}: {e}")

    # Source 3: Other error files
    for f in glob.glob('ground_truth/ocr_errors/*.json'):
        if 'ocr_error_pairs' in f:
            continue  # Already processed
        try:
            with open(f) as fp:
                data = json.load(fp)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'ocr_text' in item:
                        all_pairs.append(ErrorPair(
                            ocr_text=item['ocr_text'],
                            correct_text=item.get('correct_text', ''),
                            source_doc=f,
                            source_page=item.get('page_number', 0),
                            error_type=item.get('error_type', 'unknown'),
                            classification='other',
                            context=''
                        ))
                        if item.get('correct_text'):
                            correct_words.add(item['correct_text'])
        except Exception as e:
            print(f"Error processing {f}: {e}")

    # Deduplicate
    seen = set()
    unique_pairs = []
    for p in all_pairs:
        key = (p.ocr_text.lower(), p.correct_text.lower())
        if key not in seen and p.ocr_text.lower() != p.correct_text.lower():
            seen.add(key)
            unique_pairs.append(p)

    return ValidationSet(
        error_pairs=unique_pairs,
        correct_words=correct_words,
        metadata={
            'sources': ['verified', 'classified', 'other'],
            'extraction_date': time.strftime('%Y-%m-%d'),
        }
    )


# =============================================================================
# METRICS FRAMEWORK
# =============================================================================

@dataclass
class PipelineMetrics:
    """Metrics for evaluating OCR pipeline performance."""

    # Detection metrics
    true_positives: int = 0   # Errors correctly flagged
    false_negatives: int = 0  # Errors missed
    false_positives: int = 0  # Correct words wrongly flagged
    true_negatives: int = 0   # Correct words correctly skipped

    # Volume metrics
    total_words_processed: int = 0
    words_flagged_for_reocr: int = 0
    line_breaks_fixed: int = 0

    # Timing metrics
    total_time_ms: float = 0
    time_per_word_ms: float = 0
    time_per_page_ms: float = 0

    def detection_rate(self) -> float:
        """Percentage of errors detected."""
        total = self.true_positives + self.false_negatives
        return self.true_positives / total if total > 0 else 0

    def false_positive_rate(self) -> float:
        """Percentage of correct words wrongly flagged."""
        total = self.false_positives + self.true_negatives
        return self.false_positives / total if total > 0 else 0

    def reocr_volume_rate(self) -> float:
        """Percentage of words sent to re-OCR."""
        return self.words_flagged_for_reocr / self.total_words_processed if self.total_words_processed > 0 else 0

    def summary(self) -> dict:
        return {
            'detection_rate': f"{self.detection_rate()*100:.1f}%",
            'false_negative_rate': f"{(1-self.detection_rate())*100:.1f}%",
            'false_positive_rate': f"{self.false_positive_rate()*100:.1f}%",
            'reocr_volume': f"{self.reocr_volume_rate()*100:.1f}%",
            'line_breaks_fixed': self.line_breaks_fixed,
            'time_per_page_ms': f"{self.time_per_page_ms:.1f}ms",
        }


# =============================================================================
# TESTING
# =============================================================================

def main():
    print("=" * 70)
    print("BUILDING COMPREHENSIVE VALIDATION SET")
    print("=" * 70)

    vs = build_validation_set_from_ground_truth()
    summary = vs.summary()

    print(f"\nTotal unique error pairs: {summary['total_errors']}")
    print(f"Correct words for FP testing: {summary['correct_words']}")

    print(f"\nBy error type:")
    for t, count in sorted(summary['by_type'].items()):
        print(f"  {t}: {count}")

    print(f"\nBy document:")
    for doc, count in sorted(summary['by_document'].items(), key=lambda x: -x[1]):
        print(f"  {doc}: {count}")

    print(f"\nBy classification:")
    for cls, count in sorted(summary['by_classification'].items()):
        print(f"  {cls}: {count}")

    # Show sample errors
    print(f"\nSample errors:")
    for ep in vs.error_pairs[:10]:
        print(f"  '{ep.ocr_text}' → '{ep.correct_text}' [{ep.error_type}] ({ep.source_doc})")

    # Save validation set for future use
    output_path = Path('ground_truth/validation_set.json')
    output_data = {
        'metadata': vs.metadata,
        'summary': summary,
        'error_pairs': [
            {
                'ocr_text': ep.ocr_text,
                'correct_text': ep.correct_text,
                'source_doc': ep.source_doc,
                'source_page': ep.source_page,
                'error_type': ep.error_type,
                'classification': ep.classification,
            }
            for ep in vs.error_pairs
        ],
        'correct_words': list(vs.correct_words),
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nSaved validation set to: {output_path}")

    # Now test the pipeline
    print("\n" + "=" * 70)
    print("TESTING PIPELINE ON VALIDATION SET")
    print("=" * 70)

    try:
        from spellchecker import SpellChecker
        spell = SpellChecker()
    except ImportError:
        print("SpellChecker not available")
        return

    metrics = PipelineMetrics()
    start_time = time.time()

    # Test detection
    for ep in vs.error_pairs:
        is_flagged = ep.ocr_text.lower() not in spell
        if is_flagged:
            metrics.true_positives += 1
        else:
            metrics.false_negatives += 1

    # Test false positives on correct words
    for word in vs.correct_words:
        is_flagged = word.lower() not in spell
        if is_flagged:
            metrics.false_positives += 1
        else:
            metrics.true_negatives += 1

    metrics.total_time_ms = (time.time() - start_time) * 1000
    metrics.total_words_processed = len(vs.error_pairs) + len(vs.correct_words)
    metrics.time_per_word_ms = metrics.total_time_ms / metrics.total_words_processed

    print(f"\nResults:")
    for k, v in metrics.summary().items():
        print(f"  {k}: {v}")

    # Show false negatives (errors we missed)
    print(f"\nFalse negatives (missed errors):")
    missed = [ep for ep in vs.error_pairs if ep.ocr_text.lower() in spell]
    for ep in missed[:10]:
        print(f"  '{ep.ocr_text}' looks like a valid word (should be '{ep.correct_text}')")
    if len(missed) > 10:
        print(f"  ... and {len(missed) - 10} more")

    # Show false positives (correct words flagged)
    print(f"\nFalse positives (correct words flagged):")
    flagged = [w for w in vs.correct_words if w.lower() not in spell]
    for w in list(flagged)[:10]:
        print(f"  '{w}' flagged but is correct")
    if len(flagged) > 10:
        print(f"  ... and {len(flagged) - 10} more")


if __name__ == "__main__":
    main()
