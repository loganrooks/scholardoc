#!/usr/bin/env python3
"""
Spike 16: Ground Truth Collection with Conservative Selection

Goal: Select pages for review with ZERO false negatives while reducing total pages.

Selection Algorithm:
- SKIP only pages that are DEFINITELY safe (0% error rate + no suspicious patterns)
- REVIEW everything else

Output: JSON file with pages to review, ready for parallel Task agent processing.
"""

import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

# Suspicious OCR patterns that might indicate errors even in "clean" text
SUSPICIOUS_PATTERNS = [
    r"\btl\b",  # could be 'd' misread
    r"\brn\b",  # could be 'm' misread
    r"\bvv\b",  # could be 'w' misread
    r"\bcl\b",  # could be 'd' misread
    r"\bIl\b",  # could be 'H' or 'N' misread
    r"[a-z][A-Z]",  # unexpected case switch mid-word (like "BeautIful")
    r"[A-Z]{2,}[a-z]",  # caps then sudden lowercase
    r"\b[a-z]{1,2}\b",  # very short words (fragments) - excluding common ones
]

# Known short words that are valid
VALID_SHORT_WORDS = {
    "a", "i", "an", "as", "at", "be", "by", "do", "go", "he", "if", "in",
    "is", "it", "me", "my", "no", "of", "on", "or", "so", "to", "up", "us",
    "we", "am", "an", "ok", "vs", "cf", "eg", "ie", "re", "ex", "id", "ad",
}

# Simple word list for spell checking (we'll use a basic approach)
try:
    from spellchecker import SpellChecker
    spell = SpellChecker()
    HAS_SPELLCHECKER = True
except ImportError:
    HAS_SPELLCHECKER = False
    print("Warning: pyspellchecker not installed, using basic word check")


def extract_words(text: str) -> list[str]:
    """Extract words from text."""
    # Remove common artifacts
    text = re.sub(r"[•·§¶†‡]", " ", text)
    # Extract words (letters only, preserving case for pattern detection)
    words = re.findall(r"[A-Za-z]+", text)
    return words


def has_suspicious_patterns(text: str) -> list[str]:
    """Check for patterns that suggest OCR errors."""
    found = []
    for pattern in SUSPICIOUS_PATTERNS:
        matches = re.findall(pattern, text)
        for match in matches:
            # Filter out valid short words
            if match.lower() not in VALID_SHORT_WORDS:
                found.append(match)
    return found


def calculate_error_rate(words: list[str]) -> tuple[float, list[str]]:
    """Calculate spell-check error rate and return unknown words."""
    if not words:
        return 0.0, []

    # Normalize to lowercase for spell checking
    lower_words = [w.lower() for w in words if len(w) > 2]

    if not lower_words:
        return 0.0, []

    if HAS_SPELLCHECKER:
        unknown = spell.unknown(lower_words)
    else:
        # Fallback: very basic check (won't be accurate)
        unknown = set()

    return len(unknown) / len(lower_words), list(unknown)


def analyze_page(doc: fitz.Document, page_num: int) -> dict:
    """Analyze a single page for OCR quality indicators."""
    page = doc[page_num]
    text = page.get_text()

    if not text.strip():
        return {
            "page": page_num + 1,
            "status": "SKIP",
            "reason": "blank_page",
            "word_count": 0,
        }

    words = extract_words(text)
    if len(words) < 10:
        return {
            "page": page_num + 1,
            "status": "SKIP",
            "reason": "too_few_words",
            "word_count": len(words),
        }

    # Check for suspicious patterns
    suspicious = has_suspicious_patterns(text)

    # Calculate error rate
    error_rate, unknown_words = calculate_error_rate(words)

    # Decision logic: SKIP only if DEFINITELY safe
    if error_rate == 0.0 and not suspicious:
        return {
            "page": page_num + 1,
            "status": "SKIP",
            "reason": "clean_page",
            "word_count": len(words),
            "error_rate": 0.0,
        }

    # Everything else needs review
    return {
        "page": page_num + 1,
        "status": "REVIEW",
        "word_count": len(words),
        "error_rate": round(error_rate, 4),
        "unknown_words": unknown_words[:10],  # Sample
        "suspicious_patterns": suspicious[:5],  # Sample
        "text_sample": text[:500],
    }


def analyze_document(pdf_path: str) -> dict:
    """Analyze entire document and produce review manifest."""
    doc = fitz.open(pdf_path)

    results = {
        "document": Path(pdf_path).name,
        "total_pages": len(doc),
        "analysis_date": "2025-12-20",
        "pages_to_skip": [],
        "pages_to_review": [],
    }

    for page_num in range(len(doc)):
        analysis = analyze_page(doc, page_num)

        if analysis["status"] == "SKIP":
            results["pages_to_skip"].append({
                "page": analysis["page"],
                "reason": analysis["reason"],
            })
        else:
            results["pages_to_review"].append(analysis)

    doc.close()

    # Summary
    results["summary"] = {
        "skip_count": len(results["pages_to_skip"]),
        "review_count": len(results["pages_to_review"]),
        "reduction_percent": round(
            100 * len(results["pages_to_skip"]) / results["total_pages"], 1
        ) if results["total_pages"] > 0 else 0,
    }

    return results


def format_for_agent_review(results: dict, batch_size: int = 10) -> list[dict]:
    """Format pages into batches for parallel Task agent review."""
    pages = results["pages_to_review"]
    batches = []

    for i in range(0, len(pages), batch_size):
        batch = pages[i:i + batch_size]
        batches.append({
            "batch_id": i // batch_size + 1,
            "document": results["document"],
            "pages": batch,
        })

    return batches


def main():
    if len(sys.argv) < 2:
        print("Usage: python 16_ground_truth_collection.py <pdf_path>")
        print("\nAnalyzes PDF and outputs pages needing review for ground truth.")
        sys.exit(1)

    pdf_path = sys.argv[1]

    print(f"Analyzing: {pdf_path}")
    print("-" * 60)

    results = analyze_document(pdf_path)

    print(f"Total pages: {results['total_pages']}")
    print(f"Pages to skip: {results['summary']['skip_count']}")
    print(f"Pages to review: {results['summary']['review_count']}")
    print(f"Reduction: {results['summary']['reduction_percent']}%")
    print()

    # Show skip reasons
    skip_reasons = {}
    for p in results["pages_to_skip"]:
        reason = p["reason"]
        skip_reasons[reason] = skip_reasons.get(reason, 0) + 1

    print("Skip reasons:")
    for reason, count in sorted(skip_reasons.items()):
        print(f"  {reason}: {count}")
    print()

    # Show sample of pages to review
    print("Sample pages to review:")
    for p in results["pages_to_review"][:5]:
        print(f"  Page {p['page']}: {p['error_rate']*100:.1f}% error rate")
        if p.get("unknown_words"):
            print(f"    Unknown: {', '.join(p['unknown_words'][:5])}")
        if p.get("suspicious_patterns"):
            print(f"    Suspicious: {', '.join(p['suspicious_patterns'][:3])}")

    # Save full results
    output_path = Path("ground_truth") / f"{Path(pdf_path).stem}_review_manifest.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved manifest to: {output_path}")

    # Also save batches for agent review
    batches = format_for_agent_review(results)
    batches_path = Path("ground_truth") / f"{Path(pdf_path).stem}_review_batches.json"

    with open(batches_path, "w") as f:
        json.dump(batches, f, indent=2)

    print(f"Saved {len(batches)} review batches to: {batches_path}")


if __name__ == "__main__":
    main()
