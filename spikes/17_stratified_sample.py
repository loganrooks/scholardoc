#!/usr/bin/env python3
"""
Spike 17: Stratified Sampling for Ground Truth Collection

Creates a representative sample of pages for ground truth classification.
Each page gets the FULL text so reviewers can determine TRUE/FALSE classification.

TRUE = Contains actual OCR errors (needs re-OCR)
FALSE = Text is acceptable (even if spell-checker flags unknowns)
"""

import json
import random
import re
import sys
from pathlib import Path

import fitz

try:
    from spellchecker import SpellChecker
    spell = SpellChecker()
except ImportError:
    print("Error: pyspellchecker required. Run: uv add pyspellchecker")
    sys.exit(1)


def extract_words(text: str) -> list[str]:
    """Extract words from text."""
    words = re.findall(r"[A-Za-z]+", text)
    return [w for w in words if len(w) > 2]


def calculate_error_rate(words: list[str]) -> tuple[float, list[str]]:
    """Calculate error rate and return unknown words."""
    if not words:
        return 0.0, []
    lower_words = [w.lower() for w in words]
    unknown = list(spell.unknown(lower_words))
    return len(unknown) / len(lower_words), unknown


def analyze_all_pages(pdf_path: str) -> list[dict]:
    """Analyze all pages and calculate error rates."""
    doc = fitz.open(pdf_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        words = extract_words(text)

        if len(words) < 10:
            continue  # Skip near-empty pages

        error_rate, unknown = calculate_error_rate(words)

        pages.append({
            "page_num": page_num + 1,  # 1-indexed
            "word_count": len(words),
            "error_rate": error_rate,
            "unknown_words": unknown[:20],
            "text": text,
        })

    doc.close()
    return pages


def assign_buckets(pages: list[dict]) -> dict[str, list[dict]]:
    """Assign pages to error-rate buckets."""
    buckets = {
        "A (0-1%)": [],
        "B (1-3%)": [],
        "C (3-5%)": [],
        "D (5-10%)": [],
        "E (10%+)": [],
    }

    for p in pages:
        rate = p["error_rate"]
        if rate < 0.01:
            buckets["A (0-1%)"].append(p)
        elif rate < 0.03:
            buckets["B (1-3%)"].append(p)
        elif rate < 0.05:
            buckets["C (3-5%)"].append(p)
        elif rate < 0.10:
            buckets["D (5-10%)"].append(p)
        else:
            buckets["E (10%+)"].append(p)

    return buckets


def stratified_sample(buckets: dict[str, list[dict]], seed: int = 42) -> list[dict]:
    """Sample from each bucket at different rates."""
    random.seed(seed)

    sample_rates = {
        "A (0-1%)": 0.10,   # 10% - validate "clean" assumption
        "B (1-3%)": 0.20,   # 20%
        "C (3-5%)": 0.50,   # 50%
        "D (5-10%)": 0.75,  # 75%
        "E (10%+)": 1.00,   # 100% - review all high-error pages
    }

    sample = []
    for bucket_name, pages in buckets.items():
        rate = sample_rates[bucket_name]
        n = max(1, int(len(pages) * rate)) if pages else 0

        if pages:
            selected = random.sample(pages, min(n, len(pages)))
            for p in selected:
                p["bucket"] = bucket_name
            sample.extend(selected)

    # Sort by page number
    sample.sort(key=lambda x: x["page_num"])
    return sample


def format_for_review(sample: list[dict], doc_name: str) -> list[dict]:
    """Format sample pages for Task agent review."""
    review_items = []

    for p in sample:
        review_items.append({
            "document": doc_name,
            "page_num": p["page_num"],
            "bucket": p["bucket"],
            "error_rate": round(p["error_rate"] * 100, 1),
            "unknown_words_sample": p["unknown_words"][:10],
            "full_text": p["text"],
        })

    return review_items


def main():
    if len(sys.argv) < 2:
        print("Usage: python 17_stratified_sample.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    doc_name = Path(pdf_path).stem

    print(f"Analyzing: {pdf_path}")
    print("-" * 60)

    # Analyze all pages
    pages = analyze_all_pages(pdf_path)
    print(f"Total pages with text: {len(pages)}")

    # Bucket pages
    buckets = assign_buckets(pages)
    print("\nBucket distribution:")
    for name, bucket_pages in buckets.items():
        print(f"  {name}: {len(bucket_pages)} pages")

    # Create stratified sample
    sample = stratified_sample(buckets)
    print(f"\nStratified sample: {len(sample)} pages")

    # Count per bucket in sample
    sample_buckets = {}
    for p in sample:
        b = p["bucket"]
        sample_buckets[b] = sample_buckets.get(b, 0) + 1

    print("Sample per bucket:")
    for name in buckets.keys():
        orig = len(buckets[name])
        sampled = sample_buckets.get(name, 0)
        pct = (sampled / orig * 100) if orig > 0 else 0
        print(f"  {name}: {sampled}/{orig} ({pct:.0f}%)")

    # Format for review
    review_items = format_for_review(sample, doc_name)

    # Save
    output_dir = Path("ground_truth")
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"{doc_name}_sample_for_review.json"
    with open(output_path, "w") as f:
        json.dump({
            "document": doc_name,
            "total_pages": len(pages),
            "sample_size": len(sample),
            "bucket_distribution": {k: len(v) for k, v in buckets.items()},
            "sample_distribution": sample_buckets,
            "pages": review_items,
        }, f, indent=2)

    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
