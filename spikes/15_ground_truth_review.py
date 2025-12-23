#!/usr/bin/env python3
"""Spike 15: Generate Ground Truth Review Data

Creates a structured review of flagged pages for Claude to evaluate.
Outputs page text + flagged words for assessment.

Usage:
    uv run python spikes/15_ground_truth_review.py <pdf> --pages 100 --output review.json
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path

import fitz

try:
    from spellchecker import SpellChecker
except ImportError:
    print("ERROR: pyspellchecker required")
    sys.exit(1)


PHILOSOPHY_WHITELIST = {
    "dasein", "sein", "seiendes", "zeitlichkeit", "aufhebung",
    "sorge", "mitsein", "zuhandenheit", "vorhandenheit", "lebenswelt",
    "logos", "physis", "aletheia", "eidos", "nous", "telos",
    "aporia", "ousia", "techne", "episteme", "phronesis", "praxis",
    "differance", "jouissance", "ecriture", "arche", "bricolage",
    "phenomenological", "hermeneutic", "ontological", "epistemological",
    "heidegger", "husserl", "derrida", "levinas", "gadamer",
    "ricoeur", "sartre", "foucault", "deleuze", "kant", "hegel",
    "aristotle", "plato", "nietzsche", "kierkegaard", "wittgenstein",
}


@dataclass
class PageReview:
    page_num: int
    error_rate: float
    bucket: str
    unknown_words: list[str]
    text_sample: str  # First 500 chars
    full_text: str
    verdict: str = ""  # To be filled: GOOD, MARGINAL, BAD
    reason: str = ""   # Explanation


def extract_words(text: str) -> list[str]:
    import re
    words = re.findall(r'\b[a-zA-Z]+\b', text)
    return [w for w in words if len(w) >= 3]


def analyze_page(page: fitz.Page, spell: SpellChecker) -> tuple[float, list[str]]:
    """Analyze a page and return error rate + unknown words."""
    text = page.get_text()
    words = extract_words(text)

    if len(words) < 10:
        return 0.0, []

    # Sample 50 words
    sample_size = min(50, len(words))
    step = len(words) / sample_size
    sampled = [words[int(i * step)] for i in range(sample_size)]

    unknown = []
    checked = 0

    for word in sampled:
        lower = word.lower()
        if lower in PHILOSOPHY_WHITELIST:
            continue
        checked += 1
        if lower not in spell:
            unknown.append(word)

    rate = len(unknown) / checked if checked > 0 else 0.0
    return rate, unknown


def get_bucket(rate: float) -> str:
    if rate < 0.01:
        return "PASS"
    elif rate < 0.03:
        return "A (1-3%)"
    elif rate < 0.05:
        return "B (3-5%)"
    elif rate < 0.10:
        return "C (5-10%)"
    else:
        return "D (10%+)"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", help="PDF to analyze")
    parser.add_argument("--pages", type=int, default=100, help="Pages to analyze")
    parser.add_argument("--output", default="review.json", help="Output file")
    args = parser.parse_args()

    doc = fitz.open(args.pdf)
    spell = SpellChecker()

    # Analyze all pages
    page_data = []
    for i in range(min(args.pages, len(doc))):
        page = doc[i]
        rate, unknown = analyze_page(page, spell)
        text = page.get_text()

        page_data.append({
            "page_num": i,
            "error_rate": rate,
            "bucket": get_bucket(rate),
            "unknown_words": unknown,
            "text_sample": text[:800] if text else "",
            "full_text": text,
        })

    # Bucket pages
    buckets = defaultdict(list)
    for p in page_data:
        if p["bucket"] != "PASS":
            buckets[p["bucket"]].append(p)

    # Stratified sampling
    sample_rates = {
        "A (1-3%)": 0.15,
        "B (3-5%)": 0.25,
        "C (5-10%)": 0.50,
        "D (10%+)": 1.00,
    }

    review_pages = []
    for bucket_name, pages in buckets.items():
        rate = sample_rates.get(bucket_name, 0.5)
        n = max(1, int(len(pages) * rate))
        sampled = random.sample(pages, min(n, len(pages)))
        review_pages.extend(sampled)

    # Sort by page number
    review_pages.sort(key=lambda x: x["page_num"])

    # Summary
    print(f"Document: {Path(args.pdf).name}")
    print(f"Total pages analyzed: {len(page_data)}")
    print(f"Pages passing (< 1% error): {sum(1 for p in page_data if p['bucket'] == 'PASS')}")
    print(f"\nBucket distribution:")
    for bucket, pages in sorted(buckets.items()):
        print(f"  {bucket}: {len(pages)} pages")
    print(f"\nPages to review: {len(review_pages)}")

    # Save for review
    output = {
        "document": Path(args.pdf).name,
        "total_pages": len(page_data),
        "pages_reviewed": len(review_pages),
        "buckets": {k: len(v) for k, v in buckets.items()},
        "reviews": review_pages,
    }

    Path(args.output).write_text(json.dumps(output, indent=2))
    print(f"\nSaved to {args.output}")

    # Also print first few for immediate review
    print("\n" + "="*70)
    print("SAMPLE PAGES FOR REVIEW")
    print("="*70)

    for p in review_pages[:10]:
        print(f"\n--- Page {p['page_num']} | Bucket: {p['bucket']} | Error: {p['error_rate']:.1%} ---")
        print(f"Unknown words: {', '.join(p['unknown_words'][:10])}")
        print(f"\nText sample:")
        print(p['text_sample'][:400])
        print("...")

    doc.close()


if __name__ == "__main__":
    main()
