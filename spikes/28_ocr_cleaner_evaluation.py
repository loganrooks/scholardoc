#!/usr/bin/env python3
"""
Spike 28: OCR Cleaner Evaluation Against Ground Truth

Tests the OCR correction module against verified OCR error pairs
from ground_truth/ocr_errors/ocr_error_pairs.json.

Measures:
1. True positives: Errors correctly fixed
2. False negatives: Errors missed
3. False positives: Correct text incorrectly changed (if any)
4. Safe skips: Risky corrections flagged for review

Usage:
    uv run python spikes/28_ocr_cleaner_evaluation.py
"""

import json
from dataclasses import dataclass
from pathlib import Path

from scholardoc.normalizers import (
    CorrectionConfig,
    correct_known_patterns,
    correct_with_analysis,
    correct_with_spellcheck,
    score_ocr_quality,
)


@dataclass
class EvaluationResult:
    """Result of evaluating one error pair."""
    ocr_text: str
    correct_text: str
    corrected_to: str
    fixed: bool  # Did we fix it correctly?
    changed: bool  # Did we change the text at all?
    confidence: float
    method: str


def load_ground_truth() -> list[dict]:
    """Load OCR error pairs from ground truth."""
    gt_path = Path(__file__).parent.parent / "ground_truth/ocr_errors/ocr_error_pairs.json"
    with open(gt_path) as f:
        return json.load(f)


def evaluate_pattern_correction(error_pairs: list[dict]) -> list[EvaluationResult]:
    """Evaluate pattern-based correction."""
    results = []

    for pair in error_pairs:
        ocr_text = pair["ocr_text"]
        correct_text = pair["correct_text"]
        context = pair.get("context", ocr_text)

        # Apply pattern correction - returns CorrectionResult
        result = correct_known_patterns(context)
        corrected = result.corrected_text

        # Check if the specific word was fixed
        fixed = correct_text in corrected and ocr_text not in corrected
        changed = result.was_modified

        results.append(EvaluationResult(
            ocr_text=ocr_text,
            correct_text=correct_text,
            corrected_to=corrected[:100] if len(corrected) > 100 else corrected,
            fixed=fixed,
            changed=changed,
            confidence=result.confidence,
            method="pattern"
        ))

    return results


def evaluate_spellcheck_correction(error_pairs: list[dict]) -> list[EvaluationResult]:
    """Evaluate spellcheck-based correction."""
    results = []

    for pair in error_pairs:
        ocr_text = pair["ocr_text"]
        correct_text = pair["correct_text"]

        # Apply spellcheck to just the word - returns CorrectionResult
        result = correct_with_spellcheck(ocr_text)
        corrected = result.corrected_text

        fixed = corrected == correct_text
        changed = result.was_modified

        results.append(EvaluationResult(
            ocr_text=ocr_text,
            correct_text=correct_text,
            corrected_to=corrected,
            fixed=fixed,
            changed=changed,
            confidence=result.confidence,
            method="spellcheck"
        ))

    return results


def evaluate_analysis_correction(error_pairs: list[dict]) -> list[EvaluationResult]:
    """Evaluate analysis-based correction (with confidence thresholds)."""
    results = []

    # Use conservative config
    config = CorrectionConfig.conservative()

    for pair in error_pairs:
        ocr_text = pair["ocr_text"]
        correct_text = pair["correct_text"]
        context = pair.get("context", ocr_text)

        # Apply full analysis
        result = correct_with_analysis(context, config=config)

        # Check if the specific word was fixed
        fixed = correct_text in result.corrected_text and ocr_text not in result.corrected_text

        results.append(EvaluationResult(
            ocr_text=ocr_text,
            correct_text=correct_text,
            corrected_to=result.corrected_text[:100] if len(result.corrected_text) > 100 else result.corrected_text,
            fixed=fixed,
            changed=result.corrected_text != context,
            confidence=result.overall_confidence,
            method="analysis"
        ))

    return results


def print_results(results: list[EvaluationResult], method: str):
    """Print evaluation summary."""
    total = len(results)
    fixed = sum(1 for r in results if r.fixed)
    changed_but_wrong = sum(1 for r in results if r.changed and not r.fixed)
    unchanged = sum(1 for r in results if not r.changed)

    print(f"\n{'='*60}")
    print(f"Method: {method.upper()}")
    print(f"{'='*60}")
    print(f"Total error pairs: {total}")
    print(f"Correctly fixed:   {fixed} ({100*fixed/total:.1f}%)")
    print(f"Changed but wrong: {changed_but_wrong} ({100*changed_but_wrong/total:.1f}%)")
    print(f"Unchanged (missed):{unchanged} ({100*unchanged/total:.1f}%)")

    # Show some examples
    print(f"\n--- Examples of FIXED errors ---")
    for r in [x for x in results if x.fixed][:5]:
        print(f"  '{r.ocr_text}' -> '{r.correct_text}' ✓")

    print(f"\n--- Examples of MISSED errors ---")
    for r in [x for x in results if not x.changed][:5]:
        print(f"  '{r.ocr_text}' (expected: '{r.correct_text}')")

    if changed_but_wrong > 0:
        print(f"\n--- Examples of WRONG corrections ---")
        for r in [x for x in results if x.changed and not x.fixed][:5]:
            # Extract what it was corrected to
            print(f"  '{r.ocr_text}' -> ? (expected: '{r.correct_text}')")


def test_false_positive_rate():
    """Test that correct text is NOT incorrectly changed."""
    print(f"\n{'='*60}")
    print("FALSE POSITIVE TEST (correct text should NOT change)")
    print(f"{'='*60}")

    # Sample of correct scholarly text that should NOT be changed
    correct_samples = [
        "The beautiful is that which pleases universally without requiring a concept.",
        "Phenomenology of Spirit addresses the experience of consciousness.",
        "The categories of understanding are applied to sensible intuitions.",
        "Dasein is characterized by its being-in-the-world.",
        "The transcendental aesthetic concerns space and time as forms of intuition.",
        "Différance names the productive movement of differences.",
        "Being-toward-death is an existential possibility of Dasein.",
        "The noumenal realm remains beyond possible experience.",
    ]

    config = CorrectionConfig.conservative()

    changes = 0
    for text in correct_samples:
        result = correct_with_analysis(text, config=config)
        if result.corrected_text != text:
            changes += 1
            print(f"  CHANGED: '{text}'")
            print(f"       ->: '{result.corrected_text}'")

    print(f"\nFalse positive rate: {changes}/{len(correct_samples)} ({100*changes/len(correct_samples):.1f}%)")


def test_philosophy_vocabulary():
    """Test that philosophy terms are preserved."""
    print(f"\n{'='*60}")
    print("PHILOSOPHY VOCABULARY PRESERVATION")
    print(f"{'='*60}")

    # These should NOT be changed
    philosophy_terms = [
        "Dasein",
        "Ereignis",
        "Aufhebung",
        "Zeitlichkeit",
        "apriori",  # Sometimes hyphenated, sometimes not
        "noumenal",
        "phenomenological",
        "hermeneutic",
        "dialectical",
        "transcendental",
        "ontological",
        "Gestell",
        "Vorhandenheit",
        "Zuhandenheit",
        "différance",  # Derrida
        "aporia",
        "pharmakon",
    ]

    preserved = 0
    for term in philosophy_terms:
        result = correct_with_spellcheck(term)
        if result.corrected_text == term:
            preserved += 1
            print(f"  ✓ Preserved: '{term}'")
        else:
            print(f"  ✗ Changed: '{term}' -> '{result.corrected_text}'")

    print(f"\nPreservation rate: {preserved}/{len(philosophy_terms)} ({100*preserved/len(philosophy_terms):.1f}%)")


def main():
    print("="*60)
    print("OCR CLEANER EVALUATION AGAINST GROUND TRUTH")
    print("="*60)

    # Load ground truth
    error_pairs = load_ground_truth()
    print(f"\nLoaded {len(error_pairs)} verified OCR error pairs")

    # Show sample errors
    print("\n--- Sample errors from ground truth ---")
    for pair in error_pairs[:5]:
        print(f"  '{pair['ocr_text']}' -> '{pair['correct_text']}' ({pair['error_type']})")

    # Evaluate each method
    pattern_results = evaluate_pattern_correction(error_pairs)
    print_results(pattern_results, "Pattern-based")

    spellcheck_results = evaluate_spellcheck_correction(error_pairs)
    print_results(spellcheck_results, "Spellcheck")

    analysis_results = evaluate_analysis_correction(error_pairs)
    print_results(analysis_results, "Full Analysis")

    # Test false positive rate
    test_false_positive_rate()

    # Test philosophy vocabulary preservation
    test_philosophy_vocabulary()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    pattern_fix_rate = sum(1 for r in pattern_results if r.fixed) / len(pattern_results)
    spell_fix_rate = sum(1 for r in spellcheck_results if r.fixed) / len(spellcheck_results)
    analysis_fix_rate = sum(1 for r in analysis_results if r.fixed) / len(analysis_results)

    print(f"Pattern correction rate:   {100*pattern_fix_rate:.1f}%")
    print(f"Spellcheck correction rate:{100*spell_fix_rate:.1f}%")
    print(f"Analysis correction rate:  {100*analysis_fix_rate:.1f}%")

    print("\nNote: Low correction rates may be expected if the module is")
    print("configured conservatively to avoid false corrections (41% damage rate).")


if __name__ == "__main__":
    main()
