#!/usr/bin/env python3
"""Spike 14: Calibrate Quality Filtering Thresholds

Empirically test the multi-stage filtering system to find optimal settings.

Key Questions:
1. How many words to sample per page? (50, 100, 200?)
2. What error rate threshold identifies bad pages? (2%, 5%, 10%?)
3. How does filtering correlate with actual OCR quality?
4. What's the false positive/negative rate at different thresholds?

Metrics:
- Precision: Of pages we flag, how many actually need re-OCR?
- Recall: Of pages that need re-OCR, how many do we catch?
- F1: Balance of precision and recall
- Efficiency: How much re-OCR do we avoid vs blanket approach?

Usage:
    uv run python spikes/14_quality_filtering_calibration.py <pdf> [--pages N]
"""

import argparse
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

try:
    from spellchecker import SpellChecker
except ImportError:
    print("ERROR: pyspellchecker required. Run: uv add pyspellchecker")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    HAS_EMBEDDINGS = True
except ImportError:
    print("WARNING: sentence-transformers not available, skipping embedding tests")
    HAS_EMBEDDINGS = False


# ─────────────────────────────────────────────────────────────────────────────
# Philosophy Vocabulary (for testing profile impact)
# ─────────────────────────────────────────────────────────────────────────────

PHILOSOPHY_WHITELIST = {
    # German phenomenology
    "dasein", "sein", "seiendes", "zeitlichkeit", "aufhebung",
    "sorge", "mitsein", "zuhandenheit", "vorhandenheit", "lebenswelt",
    # Greek terms
    "logos", "physis", "aletheia", "eidos", "nous", "telos",
    "aporia", "ousia", "techne", "episteme", "phronesis", "praxis",
    # French theory
    "differance", "jouissance", "ecriture", "arche", "bricolage",
    # Technical
    "phenomenological", "hermeneutic", "ontological", "epistemological",
    "apophantic", "noematic", "eidetic", "hyletic", "noetic",
    # Common names (lowercase for possessives)
    "heidegger", "husserl", "derrida", "levinas", "gadamer",
    "ricoeur", "sartre", "foucault", "deleuze", "kant", "hegel",
    "aristotle", "plato", "nietzsche", "kierkegaard", "wittgenstein",
}


@dataclass
class PageQualityMetrics:
    """Quality metrics for a single page."""
    page_num: int
    total_words: int
    unknown_words: int
    unknown_after_whitelist: int
    error_rate_raw: float
    error_rate_with_whitelist: float

    # Stage 1 heuristics
    has_images: bool
    font_count: int
    garbage_ratio: float

    # Ground truth (if available)
    actual_quality: float | None = None  # From embedding comparison


@dataclass
class ThresholdResult:
    """Result of testing a specific threshold."""
    threshold: float
    pages_flagged: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float
    efficiency: float  # % of pages NOT flagged


def extract_words(text: str) -> list[str]:
    """Extract words from text, filtering short/numeric."""
    import re
    words = re.findall(r'\b[a-zA-Z]+\b', text)
    return [w for w in words if len(w) >= 3]


def sample_words(words: list[str], n: int) -> list[str]:
    """Sample n words evenly distributed through the list."""
    if len(words) <= n:
        return words
    step = len(words) / n
    return [words[int(i * step)] for i in range(n)]


def calculate_error_rate(
    words: list[str],
    spell: SpellChecker,
    whitelist: set[str] | None = None
) -> tuple[int, int, float]:
    """
    Calculate spell-check error rate.

    Returns: (unknown_count, checked_count, error_rate)
    """
    whitelist = whitelist or set()
    unknown = 0
    checked = 0

    for word in words:
        lower = word.lower()

        # Skip whitelisted terms
        if lower in whitelist:
            continue

        checked += 1
        if lower not in spell:
            unknown += 1

    rate = unknown / checked if checked > 0 else 0.0
    return unknown, checked, rate


def analyze_page_stage1(page: fitz.Page) -> dict:
    """Stage 1: Quick heuristics (instant)."""
    text = page.get_text()

    # Check for images (scanned indicator)
    images = page.get_images()
    has_images = len(images) > 0

    # Count fonts (high count = OCR artifact)
    blocks = page.get_text("dict")["blocks"]
    fonts = set()
    for block in blocks:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    fonts.add(span.get("font", ""))
    font_count = len(fonts)

    # Garbage character ratio
    if len(text) > 0:
        garbage_chars = sum(1 for c in text if ord(c) > 127 and c not in 'àáâãäåæçèéêëìíîïðñòóôõöøùúûüýÿœ')
        garbage_ratio = garbage_chars / len(text)
    else:
        garbage_ratio = 0.0

    return {
        "has_images": has_images,
        "font_count": font_count,
        "garbage_ratio": garbage_ratio,
        "text_length": len(text),
    }


def analyze_page_stage2(
    page: fitz.Page,
    spell: SpellChecker,
    sample_sizes: list[int],
    whitelist: set[str] | None = None
) -> dict:
    """Stage 2: Spell-check sampling with different sample sizes."""
    text = page.get_text()
    all_words = extract_words(text)

    results = {"total_words": len(all_words)}

    for n in sample_sizes:
        sampled = sample_words(all_words, n)

        # Without whitelist
        unknown_raw, checked_raw, rate_raw = calculate_error_rate(sampled, spell)

        # With whitelist
        unknown_wl, checked_wl, rate_wl = calculate_error_rate(sampled, spell, whitelist)

        results[f"sample_{n}"] = {
            "unknown_raw": unknown_raw,
            "rate_raw": rate_raw,
            "unknown_whitelist": unknown_wl,
            "rate_whitelist": rate_wl,
        }

    return results


def estimate_actual_quality(page: fitz.Page, model) -> float:
    """
    Estimate actual page quality using embedding self-similarity.

    Idea: Good text should embed consistently. Poor OCR creates
    embedding "noise" that reduces self-similarity.

    We split the page into chunks and measure their coherence.
    """
    text = page.get_text()
    words = text.split()

    if len(words) < 50:
        return 1.0  # Too short to measure

    # Split into 4 chunks
    chunk_size = len(words) // 4
    chunks = [
        " ".join(words[i*chunk_size:(i+1)*chunk_size])
        for i in range(4)
    ]

    # Embed chunks
    embeddings = model.encode(chunks)

    # Calculate average pairwise similarity
    similarities = []
    for i in range(len(embeddings)):
        for j in range(i+1, len(embeddings)):
            sim = np.dot(embeddings[i], embeddings[j]) / (
                np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
            )
            similarities.append(sim)

    return float(np.mean(similarities))


def evaluate_threshold(
    pages_metrics: list[PageQualityMetrics],
    threshold: float,
    quality_threshold: float = 0.7
) -> ThresholdResult:
    """
    Evaluate a specific error rate threshold.

    Args:
        pages_metrics: Metrics for each page
        threshold: Error rate threshold to test
        quality_threshold: Below this actual quality = needs re-OCR

    Returns:
        ThresholdResult with precision, recall, F1
    """
    pages_with_ground_truth = [p for p in pages_metrics if p.actual_quality is not None]

    if not pages_with_ground_truth:
        # No ground truth, can't calculate precision/recall
        flagged = sum(1 for p in pages_metrics if p.error_rate_with_whitelist > threshold)
        return ThresholdResult(
            threshold=threshold,
            pages_flagged=flagged,
            true_positives=0,
            false_positives=0,
            false_negatives=0,
            precision=0.0,
            recall=0.0,
            f1=0.0,
            efficiency=(len(pages_metrics) - flagged) / len(pages_metrics) if pages_metrics else 0.0,
        )

    true_positives = 0
    false_positives = 0
    false_negatives = 0

    for p in pages_with_ground_truth:
        flagged = p.error_rate_with_whitelist > threshold
        actually_bad = p.actual_quality < quality_threshold

        if flagged and actually_bad:
            true_positives += 1
        elif flagged and not actually_bad:
            false_positives += 1
        elif not flagged and actually_bad:
            false_negatives += 1

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    flagged_count = sum(1 for p in pages_metrics if p.error_rate_with_whitelist > threshold)
    efficiency = (len(pages_metrics) - flagged_count) / len(pages_metrics) if pages_metrics else 0.0

    return ThresholdResult(
        threshold=threshold,
        pages_flagged=flagged_count,
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        precision=precision,
        recall=recall,
        f1=f1,
        efficiency=efficiency,
    )


def main():
    parser = argparse.ArgumentParser(description="Calibrate quality filtering thresholds")
    parser.add_argument("pdf", help="PDF file to analyze")
    parser.add_argument("--pages", type=int, default=50, help="Number of pages to analyze")
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip embedding-based quality estimation")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    analyze_pages = min(args.pages, total_pages)

    print("=" * 70)
    print(f"QUALITY FILTERING CALIBRATION: {pdf_path.name}")
    print("=" * 70)
    print(f"Total pages: {total_pages}, analyzing: {analyze_pages}")

    # Initialize
    spell = SpellChecker()
    model = None
    if HAS_EMBEDDINGS and not args.skip_embeddings:
        print("\nLoading embedding model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')

    sample_sizes = [25, 50, 100, 200]
    pages_metrics = []

    print(f"\nAnalyzing pages with sample sizes: {sample_sizes}")
    print("-" * 70)

    # Analyze pages
    start_time = time.time()

    for i in range(analyze_pages):
        page = doc[i]

        # Stage 1
        stage1 = analyze_page_stage1(page)

        # Stage 2
        stage2 = analyze_page_stage2(page, spell, sample_sizes, PHILOSOPHY_WHITELIST)

        # Use sample_100 as our default
        s100 = stage2.get("sample_100", stage2.get("sample_50", {}))

        # Actual quality (if embeddings available)
        actual_quality = None
        if model is not None:
            actual_quality = estimate_actual_quality(page, model)

        metrics = PageQualityMetrics(
            page_num=i,
            total_words=stage2["total_words"],
            unknown_words=s100.get("unknown_raw", 0),
            unknown_after_whitelist=s100.get("unknown_whitelist", 0),
            error_rate_raw=s100.get("rate_raw", 0.0),
            error_rate_with_whitelist=s100.get("rate_whitelist", 0.0),
            has_images=stage1["has_images"],
            font_count=stage1["font_count"],
            garbage_ratio=stage1["garbage_ratio"],
            actual_quality=actual_quality,
        )
        pages_metrics.append(metrics)

        # Progress
        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{analyze_pages} pages...")

    elapsed = time.time() - start_time
    print(f"\nAnalysis complete in {elapsed:.1f}s ({elapsed/analyze_pages:.2f}s/page)")

    # ─────────────────────────────────────────────────────────────────────────
    # EXPERIMENT 1: Sample Size Comparison
    # ─────────────────────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("EXPERIMENT 1: Sample Size Impact")
    print("=" * 70)
    print("\nQuestion: Does sampling 50 vs 100 vs 200 words change error rate estimates?")

    # Re-analyze a subset to compare sample sizes
    sample_comparison = []
    for i in range(min(20, analyze_pages)):
        page = doc[i]
        stage2 = analyze_page_stage2(page, spell, sample_sizes, PHILOSOPHY_WHITELIST)
        sample_comparison.append({
            "page": i,
            **{f"s{n}": stage2[f"sample_{n}"]["rate_whitelist"] for n in sample_sizes}
        })

    print(f"\n{'Page':<6} {'S25':>8} {'S50':>8} {'S100':>8} {'S200':>8} {'Variance':>10}")
    print("-" * 55)

    variances = []
    for row in sample_comparison:
        rates = [row[f"s{n}"] for n in sample_sizes]
        var = np.var(rates) if rates else 0
        variances.append(var)
        print(f"{row['page']:<6} {row['s25']:>7.1%} {row['s50']:>7.1%} {row['s100']:>7.1%} {row['s200']:>7.1%} {var:>10.4f}")

    print(f"\nMean variance across pages: {np.mean(variances):.4f}")
    print(f"Max variance: {np.max(variances):.4f}")

    if np.mean(variances) < 0.001:
        print("✅ Sample sizes are consistent - 50 words may be sufficient")
    else:
        print("⚠️  Sample sizes show variance - prefer 100+ words")

    # ─────────────────────────────────────────────────────────────────────────
    # EXPERIMENT 2: Error Rate Distribution
    # ─────────────────────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("EXPERIMENT 2: Error Rate Distribution")
    print("=" * 70)

    rates_raw = [p.error_rate_raw for p in pages_metrics]
    rates_wl = [p.error_rate_with_whitelist for p in pages_metrics]

    print(f"\n{'Metric':<30} {'Raw':>12} {'With Whitelist':>15}")
    print("-" * 60)
    print(f"{'Mean error rate':<30} {np.mean(rates_raw):>11.1%} {np.mean(rates_wl):>14.1%}")
    print(f"{'Median error rate':<30} {np.median(rates_raw):>11.1%} {np.median(rates_wl):>14.1%}")
    print(f"{'Std dev':<30} {np.std(rates_raw):>11.1%} {np.std(rates_wl):>14.1%}")
    print(f"{'Min':<30} {np.min(rates_raw):>11.1%} {np.min(rates_wl):>14.1%}")
    print(f"{'Max':<30} {np.max(rates_raw):>11.1%} {np.max(rates_wl):>14.1%}")

    print(f"\n📊 Whitelist impact: {(np.mean(rates_raw) - np.mean(rates_wl)) / np.mean(rates_raw) * 100:.1f}% reduction in error rate")

    # Distribution buckets
    print("\nError rate distribution (with whitelist):")
    buckets = [(0, 0.02), (0.02, 0.05), (0.05, 0.10), (0.10, 0.20), (0.20, 1.0)]
    for low, high in buckets:
        count = sum(1 for r in rates_wl if low <= r < high)
        pct = count / len(rates_wl) * 100
        bar = "█" * int(pct / 2)
        label = f"{low*100:.0f}-{high*100:.0f}%"
        print(f"  {label:>8}: {count:>4} pages ({pct:>5.1f}%) {bar}")

    # ─────────────────────────────────────────────────────────────────────────
    # EXPERIMENT 3: Threshold Optimization
    # ─────────────────────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("EXPERIMENT 3: Threshold Optimization")
    print("=" * 70)

    thresholds = [0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20]

    has_ground_truth = any(p.actual_quality is not None for p in pages_metrics)

    if has_ground_truth:
        print("\n✅ Ground truth available (embedding-based quality)")
        print(f"\n{'Threshold':>10} {'Flagged':>8} {'TP':>5} {'FP':>5} {'FN':>5} {'Precision':>10} {'Recall':>8} {'F1':>8} {'Efficiency':>10}")
        print("-" * 85)

        best_f1 = 0
        best_threshold = 0

        for thresh in thresholds:
            result = evaluate_threshold(pages_metrics, thresh)

            print(f"{thresh:>9.0%} {result.pages_flagged:>8} {result.true_positives:>5} "
                  f"{result.false_positives:>5} {result.false_negatives:>5} "
                  f"{result.precision:>9.1%} {result.recall:>7.1%} {result.f1:>7.2f} {result.efficiency:>9.1%}")

            if result.f1 > best_f1:
                best_f1 = result.f1
                best_threshold = thresh

        print(f"\n🎯 Optimal threshold: {best_threshold:.0%} (F1 = {best_f1:.2f})")
    else:
        print("\n⚠️  No ground truth - showing flagging rates only")
        print(f"\n{'Threshold':>10} {'Pages Flagged':>15} {'Efficiency':>12}")
        print("-" * 40)

        for thresh in thresholds:
            flagged = sum(1 for p in pages_metrics if p.error_rate_with_whitelist > thresh)
            efficiency = (len(pages_metrics) - flagged) / len(pages_metrics)
            print(f"{thresh:>9.0%} {flagged:>15} ({flagged/len(pages_metrics)*100:.1f}%) {efficiency:>11.1%}")

    # ─────────────────────────────────────────────────────────────────────────
    # EXPERIMENT 4: Stage 1 Heuristics Correlation
    # ─────────────────────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("EXPERIMENT 4: Stage 1 Heuristics Analysis")
    print("=" * 70)

    pages_with_images = sum(1 for p in pages_metrics if p.has_images)
    high_font_pages = sum(1 for p in pages_metrics if p.font_count > 20)
    garbage_pages = sum(1 for p in pages_metrics if p.garbage_ratio > 0.01)

    print(f"\nStage 1 Indicators:")
    print(f"  Pages with images: {pages_with_images} ({pages_with_images/len(pages_metrics)*100:.1f}%)")
    print(f"  Pages with >20 fonts: {high_font_pages} ({high_font_pages/len(pages_metrics)*100:.1f}%)")
    print(f"  Pages with >1% garbage: {garbage_pages} ({garbage_pages/len(pages_metrics)*100:.1f}%)")

    # Correlation between Stage 1 and Stage 2
    if pages_with_images > 0:
        img_error_rates = [p.error_rate_with_whitelist for p in pages_metrics if p.has_images]
        no_img_error_rates = [p.error_rate_with_whitelist for p in pages_metrics if not p.has_images]

        if img_error_rates and no_img_error_rates:
            print(f"\nImage pages vs non-image pages:")
            print(f"  Mean error rate (with images): {np.mean(img_error_rates):.1%}")
            print(f"  Mean error rate (no images): {np.mean(no_img_error_rates):.1%}")

            if np.mean(img_error_rates) > np.mean(no_img_error_rates) * 1.5:
                print("  ✅ Image presence correlates with higher error rate (good Stage 1 signal)")
            else:
                print("  ⚠️  Image presence doesn't strongly predict errors")

    # ─────────────────────────────────────────────────────────────────────────
    # EXPERIMENT 5: Auto-Whitelist Potential
    # ─────────────────────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("EXPERIMENT 5: Auto-Whitelist Candidates")
    print("=" * 70)

    # Count all unknown words across document
    unknown_counts = Counter()
    for i in range(analyze_pages):
        page = doc[i]
        text = page.get_text()
        words = extract_words(text)

        for word in words:
            lower = word.lower()
            if lower not in spell and lower not in PHILOSOPHY_WHITELIST:
                unknown_counts[lower] += 1

    # Find candidates (appear 5+ times)
    candidates = [(word, count) for word, count in unknown_counts.most_common(50) if count >= 5]

    print(f"\nWords appearing 5+ times that are 'unknown' (auto-whitelist candidates):")
    print(f"\n{'Word':<25} {'Count':>8} {'Likely Type':<20}")
    print("-" * 55)

    for word, count in candidates[:20]:
        # Guess the type
        if word[0].isupper():
            word_type = "Proper noun"
        elif any(c in word for c in "äöüéèêàâ"):
            word_type = "Foreign term"
        elif len(word) <= 3:
            word_type = "Abbreviation"
        else:
            word_type = "Domain term?"

        print(f"{word:<25} {count:>8} {word_type:<20}")

    if candidates:
        print(f"\n📝 {len(candidates)} candidates could be auto-whitelisted")
        print(f"   This would further reduce false 'error' counts")

    # ─────────────────────────────────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("CALIBRATION SUMMARY")
    print("=" * 70)

    mean_error = np.mean(rates_wl)

    print(f"""
Document: {pdf_path.name}
Pages analyzed: {analyze_pages}

FINDINGS:

1. SAMPLE SIZE
   - Variance between sample sizes: {np.mean(variances):.4f}
   - Recommendation: {'50 words sufficient' if np.mean(variances) < 0.001 else '100+ words recommended'}

2. ERROR RATES (with philosophy whitelist)
   - Mean: {mean_error:.1%}
   - Median: {np.median(rates_wl):.1%}
   - Range: {np.min(rates_wl):.1%} - {np.max(rates_wl):.1%}

3. RECOMMENDED THRESHOLDS
   Based on this document's distribution:
   - Good (no re-OCR): < {np.percentile(rates_wl, 75):.1%}
   - Marginal (warning): {np.percentile(rates_wl, 75):.1%} - {np.percentile(rates_wl, 90):.1%}
   - Re-OCR needed: > {np.percentile(rates_wl, 90):.1%}

4. WHITELIST IMPACT
   - Error rate reduction: {(np.mean(rates_raw) - np.mean(rates_wl)) / np.mean(rates_raw) * 100:.1f}%
   - Auto-whitelist candidates: {len(candidates)}

5. STAGE 1 SIGNALS
   - Image pages: {pages_with_images} ({pages_with_images/len(pages_metrics)*100:.1f}%)
   - High font count: {high_font_pages} ({high_font_pages/len(pages_metrics)*100:.1f}%)

NEXT STEPS:
- Run on multiple documents to verify thresholds generalize
- Test with known-bad OCR pages to validate recall
- Compare flagged pages against docTR re-OCR quality
    """)

    doc.close()


if __name__ == "__main__":
    main()
