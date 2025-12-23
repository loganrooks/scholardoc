#!/usr/bin/env python3
"""
Spike 23: OCR Correction Pipeline Tuning

Test the OCR correction pipeline against ground truth to find optimal hyperparameters.

Goals:
1. Test pipeline on known OCR error pairs
2. Evaluate different CorrectionConfig presets (conservative, balanced, aggressive)
3. Grid search for optimal threshold/weight combinations
4. Measure precision, recall, F1 for corrections

Usage:
    uv run python spikes/23_ocr_pipeline_tuning.py
    uv run python spikes/23_ocr_pipeline_tuning.py --grid-search
    uv run python spikes/23_ocr_pipeline_tuning.py --test-pages
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scholardoc.normalizers.ocr_correction import (
    CorrectionConfig,
    score_ocr_quality,
    correct_ocr_errors,
    correct_known_patterns,
    correct_with_spellcheck,
    correct_with_analysis,
    PHILOSOPHY_VOCABULARY,
    COMMON_OCR_MISSPELLINGS,
)


# ─────────────────────────────────────────────────────────────────────────────
# Ground Truth Loading
# ─────────────────────────────────────────────────────────────────────────────

GROUND_TRUTH_DIR = Path(__file__).parent.parent / "ground_truth"


def load_ocr_error_pairs() -> list[dict]:
    """Load verified OCR error pairs from ground truth."""
    path = GROUND_TRUTH_DIR / "ocr_errors" / "ocr_error_pairs.json"
    if not path.exists():
        print(f"Warning: {path} not found")
        return []

    with open(path) as f:
        data = json.load(f)

    # Handle different formats
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return data.get("pairs", data.get("errors", []))
    return []


def load_challenging_samples() -> list[dict]:
    """Load challenging OCR samples for testing."""
    path = GROUND_TRUTH_DIR / "ocr_errors" / "challenging_samples.json"
    if not path.exists():
        print(f"Warning: {path} not found")
        return []

    with open(path) as f:
        return json.load(f)


def load_page_classifications() -> dict:
    """Load page-level OCR quality classifications."""
    path = GROUND_TRUTH_DIR / "ocr_quality" / "unified_ground_truth.json"
    if not path.exists():
        print(f"Warning: {path} not found")
        return {}

    with open(path) as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# Evaluation Metrics
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EvaluationResult:
    """Results from evaluating correction pipeline."""

    config_name: str
    total_samples: int = 0

    # Correction metrics
    true_positives: int = 0   # Correctly corrected
    false_positives: int = 0  # Wrongly corrected (made worse)
    false_negatives: int = 0  # Should have corrected but didn't
    true_negatives: int = 0   # Correctly left alone

    # Detailed tracking
    correct_corrections: list[tuple] = field(default_factory=list)
    wrong_corrections: list[tuple] = field(default_factory=list)
    missed_corrections: list[tuple] = field(default_factory=list)

    @property
    def precision(self) -> float:
        """Of corrections made, how many were right?"""
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        """Of errors that needed correction, how many did we fix?"""
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def f1(self) -> float:
        """Harmonic mean of precision and recall."""
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def accuracy(self) -> float:
        """Overall accuracy."""
        total = self.true_positives + self.false_positives + self.false_negatives + self.true_negatives
        return (self.true_positives + self.true_negatives) / total if total > 0 else 0.0

    def summary(self) -> str:
        """Return summary string."""
        return (
            f"{self.config_name}:\n"
            f"  Samples: {self.total_samples}\n"
            f"  Precision: {self.precision:.1%}\n"
            f"  Recall: {self.recall:.1%}\n"
            f"  F1: {self.f1:.1%}\n"
            f"  TP={self.true_positives} FP={self.false_positives} "
            f"FN={self.false_negatives} TN={self.true_negatives}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline Testing
# ─────────────────────────────────────────────────────────────────────────────

def test_known_patterns() -> EvaluationResult:
    """Test correction of known OCR error patterns."""
    result = EvaluationResult(config_name="known_patterns")

    # Test the COMMON_OCR_MISSPELLINGS
    for ocr_text, correct_text in COMMON_OCR_MISSPELLINGS.items():
        result.total_samples += 1
        corrected = correct_known_patterns(ocr_text)

        if corrected.corrected_text.lower() == correct_text.lower():
            result.true_positives += 1
            result.correct_corrections.append((ocr_text, correct_text, corrected.corrected_text))
        elif corrected.corrected_text.lower() == ocr_text.lower():
            result.false_negatives += 1
            result.missed_corrections.append((ocr_text, correct_text, corrected.corrected_text))
        else:
            result.false_positives += 1
            result.wrong_corrections.append((ocr_text, correct_text, corrected.corrected_text))

    return result


def test_spellcheck_correction(config: CorrectionConfig) -> EvaluationResult:
    """Test spell-check based correction using correct_with_analysis (config-aware)."""
    result = EvaluationResult(config_name=f"spellcheck_{config.apply_threshold}")

    # Test cases: (ocr_text, expected_correction)
    test_cases = [
        # Known OCR errors that should be corrected
        ("beautlful", "beautiful"),
        ("tbe", "the"),
        ("rnorning", "morning"),
        ("questlon", "question"),
        # Philosophy terms that should NOT be corrected
        ("dasein", "dasein"),
        ("noumenon", "noumenon"),
        ("apperception", "apperception"),
        # Proper nouns that should NOT be corrected
        ("Heidegger", "Heidegger"),
        ("Derrida", "Derrida"),
        # Real words that look like OCR errors
        ("form", "form"),
        ("being", "being"),
    ]

    for ocr_text, expected in test_cases:
        result.total_samples += 1

        try:
            # Use correct_with_analysis which accepts CorrectionConfig
            analyzed = correct_with_analysis(ocr_text, config, min_word_length=3)
            actual = analyzed.corrected_text.lower().strip()
            expected_lower = expected.lower()
            ocr_lower = ocr_text.lower()

            is_error = ocr_lower != expected_lower  # Was it actually an error?
            was_corrected = actual != ocr_lower     # Did we change it?
            correct_result = actual == expected_lower  # Is the result correct?

            if is_error and was_corrected and correct_result:
                result.true_positives += 1
                result.correct_corrections.append((ocr_text, expected, actual))
            elif is_error and not was_corrected:
                result.false_negatives += 1
                result.missed_corrections.append((ocr_text, expected, actual))
            elif not is_error and not was_corrected:
                result.true_negatives += 1
            elif was_corrected and not correct_result:
                result.false_positives += 1
                result.wrong_corrections.append((ocr_text, expected, actual))
            else:
                result.true_negatives += 1

        except Exception as e:
            print(f"  Error processing '{ocr_text}': {e}")
            result.false_negatives += 1

    return result


def test_quality_scoring() -> dict:
    """Test OCR quality scoring on sample texts."""

    test_texts = {
        "clean": "The beautiful morning sunrise illuminated the peaceful valley.",
        "minor_errors": "The beautlful morning sunrise illuminated tbe peaceful valley.",
        "moderate_errors": "Tbe beautlful rnorning sunrise illurninated tbe peaceful valley.",
        "severe_errors": "Tbe beautlful rnorning sunrlse lllurninated tbe peacefuI valIey.",
        "philosophy_clean": "Heidegger's analysis of Dasein reveals the structure of being-in-the-world.",
        "philosophy_ocr": "Heidegger's analysls of Daseln reveals tbe structure of belng-ln-the-world.",
    }

    results = {}
    for name, text in test_texts.items():
        score = score_ocr_quality(text, spell_check=True, detailed=True)
        results[name] = {
            "overall_score": round(score.overall_score, 3),
            "error_rate": round(score.error_rate, 4),
            "usable_for_rag": score.is_usable_for_rag,
            "needs_correction": score.needs_correction,
            "suspicious_words": score.suspicious_words[:5],  # First 5
            "correctable": list(score.correctable_words.items())[:5],
        }

    return results


def test_full_pipeline(aggressive: bool = False) -> EvaluationResult:
    """Test the full correction pipeline (correct_ocr_errors)."""
    result = EvaluationResult(config_name=f"full_pipeline_aggressive={aggressive}")

    # Load ground truth error pairs
    error_pairs = load_ocr_error_pairs()

    if not error_pairs:
        print("No error pairs found, using built-in test cases")
        error_pairs = [
            {"ocr": "beautlful", "correct": "beautiful"},
            {"ocr": "tbe", "correct": "the"},
            {"ocr": "rnorning", "correct": "morning"},
        ]

    for pair in error_pairs[:50]:  # Test first 50
        ocr_text = pair.get("ocr", pair.get("ocr_text", ""))
        correct_text = pair.get("correct", pair.get("correct_text", ""))

        if not ocr_text or not correct_text:
            continue

        result.total_samples += 1

        try:
            # correct_ocr_errors returns CorrectionResult, access .corrected_text
            correction_result = correct_ocr_errors(
                ocr_text,
                use_patterns=True,
                use_spellcheck=True,
                aggressive=aggressive,
            )
            actual = correction_result.corrected_text.lower().strip()
            expected = correct_text.lower().strip()
            ocr_lower = ocr_text.lower().strip()

            is_error = ocr_lower != expected
            was_corrected = actual != ocr_lower
            correct_result = actual == expected

            if is_error and was_corrected and correct_result:
                result.true_positives += 1
            elif is_error and not was_corrected:
                result.false_negatives += 1
                result.missed_corrections.append((ocr_text, correct_text, actual))
            elif not is_error and not was_corrected:
                result.true_negatives += 1
            elif was_corrected and not correct_result:
                result.false_positives += 1
                result.wrong_corrections.append((ocr_text, correct_text, actual))
            else:
                result.true_negatives += 1

        except Exception as e:
            print(f"  Error: {e}")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Grid Search
# ─────────────────────────────────────────────────────────────────────────────

def grid_search_thresholds() -> list[tuple]:
    """Grid search over threshold combinations."""
    results = []

    thresholds = [0.3, 0.5, 0.6, 0.7, 0.8, 0.9]

    for apply_thresh in thresholds:
        for review_thresh in [t for t in thresholds if t < apply_thresh]:
            config = CorrectionConfig(
                apply_threshold=apply_thresh,
                review_threshold=review_thresh,
                skip_threshold=0.1,
            )

            result = test_spellcheck_correction(config)
            results.append((
                apply_thresh,
                review_thresh,
                result.precision,
                result.recall,
                result.f1,
                result.true_positives,
                result.false_positives,
            ))

    # Sort by F1
    results.sort(key=lambda x: x[4], reverse=True)
    return results


def grid_search_weights() -> list[tuple]:
    """Grid search over feature weight combinations."""
    results = []

    # Test different weight emphasis
    weight_configs = [
        ("frequency_heavy", {"frequency_weight": 0.40, "edit_distance_weight": 0.15}),
        ("edit_heavy", {"frequency_weight": 0.15, "edit_distance_weight": 0.40}),
        ("balanced", {"frequency_weight": 0.25, "edit_distance_weight": 0.20}),
        ("scholarly_boost", {"scholarly_boost_weight": 0.25, "frequency_weight": 0.20}),
        ("conservative", {"foreign_marker_weight": 0.25, "first_letter_weight": 0.20}),
    ]

    for name, weights in weight_configs:
        config = CorrectionConfig(**weights)
        result = test_spellcheck_correction(config)
        results.append((
            name,
            result.precision,
            result.recall,
            result.f1,
        ))

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OCR Pipeline Tuning")
    parser.add_argument("--grid-search", action="store_true", help="Run grid search")
    parser.add_argument("--test-pages", action="store_true", help="Test on classified pages")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print("=" * 60)
    print("OCR CORRECTION PIPELINE TESTING")
    print("=" * 60)

    # Test 1: Known patterns
    print("\n1. Testing Known Pattern Correction")
    print("-" * 40)
    result = test_known_patterns()
    print(result.summary())

    # Test 2: Quality scoring
    print("\n2. Testing Quality Scoring")
    print("-" * 40)
    scores = test_quality_scoring()
    for name, score_data in scores.items():
        print(f"  {name}:")
        print(f"    Score: {score_data['overall_score']:.2f}, Error rate: {score_data['error_rate']:.2%}")
        print(f"    Usable for RAG: {score_data['usable_for_rag']}, Needs correction: {score_data['needs_correction']}")
        if score_data['suspicious_words']:
            print(f"    Suspicious: {score_data['suspicious_words']}")

    # Test 3: Preset configurations
    print("\n3. Testing Correction Presets")
    print("-" * 40)

    presets = [
        ("conservative", CorrectionConfig.conservative()),
        ("balanced", CorrectionConfig.balanced()),
        ("aggressive", CorrectionConfig.aggressive()),
    ]

    for name, config in presets:
        print(f"\n  {name.upper()} (apply={config.apply_threshold}, review={config.review_threshold})")
        result = test_spellcheck_correction(config)
        print(f"    Precision: {result.precision:.1%}, Recall: {result.recall:.1%}, F1: {result.f1:.1%}")
        if result.wrong_corrections and args.verbose:
            print(f"    Wrong corrections: {result.wrong_corrections[:3]}")
        if result.missed_corrections and args.verbose:
            print(f"    Missed: {result.missed_corrections[:3]}")

    # Test 4: Full pipeline
    print("\n4. Testing Full Pipeline")
    print("-" * 40)
    result = test_full_pipeline(aggressive=False)
    print(result.summary())
    if result.missed_corrections:
        print(f"\n  Missed corrections (sample):")
        for ocr, correct, actual in result.missed_corrections[:5]:
            print(f"    '{ocr}' → should be '{correct}', got '{actual}'")

    # Grid search
    if args.grid_search:
        print("\n5. Grid Search: Thresholds")
        print("-" * 40)
        threshold_results = grid_search_thresholds()
        print(f"  {'Apply':>6} {'Review':>6} {'Prec':>6} {'Recall':>6} {'F1':>6} {'TP':>4} {'FP':>4}")
        for r in threshold_results[:10]:
            print(f"  {r[0]:>6.2f} {r[1]:>6.2f} {r[2]:>6.1%} {r[3]:>6.1%} {r[4]:>6.1%} {r[5]:>4} {r[6]:>4}")

        print("\n6. Grid Search: Weights")
        print("-" * 40)
        weight_results = grid_search_weights()
        print(f"  {'Config':<20} {'Prec':>8} {'Recall':>8} {'F1':>8}")
        for r in weight_results:
            print(f"  {r[0]:<20} {r[1]:>8.1%} {r[2]:>8.1%} {r[3]:>8.1%}")

    # Summary
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    print("""
Based on Spike 13 findings (41% of philosophy terms damaged by auto-correction):

1. USE CONSERVATIVE SETTINGS for philosophy texts:
   - apply_threshold >= 0.85
   - Only correct high-confidence obvious errors

2. SKIP SPELL-CHECK CORRECTION for:
   - Capitalized words (proper nouns)
   - Words with diacritics (foreign terms)
   - Known philosophy vocabulary

3. PREFER QUALITY SCORING + FUZZY RETRIEVAL over correction:
   - Score text quality to flag problematic pages
   - Let RAG handle minor errors via fuzzy matching
   - Only correct mechanically-detectable patterns (rn→m, tl→ti)

4. RECOMMENDED CONFIG for philosophy texts:
   CorrectionConfig(
       apply_threshold=0.9,
       review_threshold=0.6,
       max_edit_distance=1,
       frequency_weight=0.30,
   )
""")


if __name__ == "__main__":
    main()
