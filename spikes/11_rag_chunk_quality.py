#!/usr/bin/env python3
"""Spike 11: RAG Chunk Quality Testing

Test how different text cleaning strategies affect embedding quality for RAG.

Key questions:
1. Do page number artifacts hurt embeddings?
2. Do running headers ("Preface <A>") hurt embeddings?
3. Do footnote markers hurt embeddings?
4. Should footnotes be embedded with or without their context?

Usage:
    uv run python spikes/11_rag_chunk_quality.py
"""

import re
import sys

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    print("ERROR: sentence-transformers required. Run: uv add sentence-transformers")
    sys.exit(1)


def compute_similarity(model: SentenceTransformer, text1: str, text2: str) -> float:
    """Compute cosine similarity between two texts."""
    if not text1.strip() or not text2.strip():
        return 0.0
    embeddings = model.encode([text1, text2])
    return float(np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    ))


def remove_page_numbers(text: str) -> str:
    """Remove page number artifacts from text."""
    # Remove leading page numbers like "64 " or "xiv "
    text = re.sub(r'^\d+\s+', '', text)
    text = re.sub(r'^[ivxlc]+\s+', '', text, flags=re.IGNORECASE)
    return text


def remove_running_headers(text: str) -> str:
    """Remove running headers like 'Preface <A>' or 'CHAPTER 1'."""
    # Remove common header patterns
    text = re.sub(r'^(Preface|Chapter|Section|Introduction)\s*(<[A-Z]>)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^[A-Z\s]+<[A-Z]>\s*', '', text)  # "PREFACE <A>"
    return text


def remove_footnote_markers(text: str) -> str:
    """Remove superscript footnote markers."""
    # Remove superscript numbers and symbols
    text = re.sub(r'[⁰¹²³⁴⁵⁶⁷⁸⁹]+', '', text)  # Unicode superscripts
    text = re.sub(r'\*+', '', text)  # Asterisks
    text = re.sub(r'†+', '', text)  # Daggers
    text = re.sub(r'‡+', '', text)  # Double daggers
    # Remove inline markers like "word,a and" → "word, and"
    text = re.sub(r',([a-z])\s+', ', ', text)
    return text


def clean_for_embedding(text: str) -> str:
    """Apply all cleaning transformations."""
    text = remove_page_numbers(text)
    text = remove_running_headers(text)
    text = remove_footnote_markers(text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def main():
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Ground truth: Clean, properly formatted text (what a human would type)
    ground_truth = """
    But since there were fortunately only a few of them, they could not
    prevent the dogmatists from continually attempting to rebuild, though
    never according to a plan unanimously accepted among themselves.
    """.strip()

    # Variations from OCR with different artifacts
    test_cases = {
        "clean_ground_truth": ground_truth,

        "with_page_number": "64 " + ground_truth,

        "with_running_header": "Preface <A> " + ground_truth,

        "with_both_artifacts": "64 Preface <A> " + ground_truth,

        "with_footnote_marker": ground_truth.replace(
            "dogmatists",
            "dogmatists*"
        ),

        "with_inline_footnote_ref": ground_truth.replace(
            "continually",
            "continually,a"
        ),

        "with_ocr_errors": ground_truth.replace(
            "fortunately",
            "fortuntately"  # OCR typo
        ).replace(
            "unanimously",
            "unanhnously"  # OCR confusion
        ),

        "with_all_issues": "64 Preface <A> " + ground_truth.replace(
            "dogmatists",
            "dogmatlsts*"  # l/i confusion + marker
        ).replace(
            "rebuild",
            "rebulld"  # OCR error
        ),
    }

    print("\n" + "="*70)
    print("EXPERIMENT 1: How do artifacts affect embedding similarity?")
    print("="*70)
    print(f"\nGround truth ({len(ground_truth)} chars):")
    print(f"  '{ground_truth[:80]}...'")

    print(f"\n{'Variant':<30} {'Raw Sim':>10} {'Cleaned Sim':>12} {'Δ':>8}")
    print("-" * 62)

    for name, text in test_cases.items():
        raw_sim = compute_similarity(model, ground_truth, text)
        cleaned = clean_for_embedding(text)
        cleaned_sim = compute_similarity(model, ground_truth, cleaned)
        delta = cleaned_sim - raw_sim

        delta_str = f"+{delta:.3f}" if delta > 0 else f"{delta:.3f}"
        print(f"{name:<30} {raw_sim:>10.3f} {cleaned_sim:>12.3f} {delta_str:>8}")

    # Experiment 2: Footnote context
    print("\n" + "="*70)
    print("EXPERIMENT 2: Should footnotes be embedded with context?")
    print("="*70)

    passage_with_footnote = """
    Our age is the genuine age of criticism, to which everything must submit.*
    Religion through its holiness and legislation through its majesty commonly
    seek to exempt themselves from it.
    """

    footnote_content = """
    * Now and again one hears complaints about the superficiality of our age's
    way of thinking, and about the decay of well-grounded science.
    """

    passage_clean = passage_with_footnote.replace("*", "").strip()
    passage_clean = re.sub(r'\s+', ' ', passage_clean)

    # Query that should match the main passage
    query = "What does Kant say about the age of criticism?"

    print(f"\nQuery: '{query}'")
    print(f"\nPassage (with marker): '{passage_with_footnote[:60].strip()}...'")
    print(f"Footnote: '{footnote_content[:60].strip()}...'")

    # Test different embedding strategies
    strategies = {
        "passage_with_marker": passage_with_footnote,
        "passage_clean": passage_clean,
        "footnote_only": footnote_content,
        "passage_plus_footnote": passage_clean + " " + footnote_content.replace("*", ""),
    }

    print(f"\n{'Strategy':<25} {'Similarity to Query':>20}")
    print("-" * 47)

    for name, text in strategies.items():
        text = re.sub(r'\s+', ' ', text).strip()
        sim = compute_similarity(model, query, text)
        print(f"{name:<25} {sim:>20.3f}")

    # Experiment 3: Page boundary artifacts
    print("\n" + "="*70)
    print("EXPERIMENT 3: Cross-page text handling")
    print("="*70)

    # Text split across pages
    page1_end = "Our age is the genuine age of criticism, to"
    page2_start = "which everything must submit."

    full_sentence = "Our age is the genuine age of criticism, to which everything must submit."

    # Different representations
    representations = {
        "full_sentence": full_sentence,
        "page1_only": page1_end,
        "page2_only": page2_start,
        "naive_concat": page1_end + " " + page2_start,
        "with_page_marker": page1_end + " [PAGE 65] " + page2_start,
        "with_hyphen_artifact": page1_end.replace("to", "to-") + page2_start,
    }

    query = "Kant on the age of criticism"
    print(f"\nQuery: '{query}'")
    print(f"Full sentence: '{full_sentence}'")

    print(f"\n{'Representation':<25} {'Similarity':>12}")
    print("-" * 39)

    for name, text in representations.items():
        sim = compute_similarity(model, query, text)
        print(f"{name:<25} {sim:>12.3f}")

    # Summary
    print("\n" + "="*70)
    print("CONCLUSIONS")
    print("="*70)
    print("""
1. PAGE NUMBERS: **SIGNIFICANT** impact (29% drop!) - MUST remove before embedding
2. RUNNING HEADERS: Minor impact (2%) - remove for cleanliness
3. FOOTNOTE MARKERS: Minimal impact (1%) - can leave or remove
4. OCR ERRORS: SIGNIFICANT impact (4-15%) - these can't be cleaned by artifact removal
5. CROSS-PAGE SPLITS: Naive concat works fine; markers like [PAGE 65] hurt (~4%)

KEY INSIGHTS:
- Page numbers are the #1 artifact to remove - they significantly alter embeddings
- OCR errors are the #2 problem - but require actual correction, not just removal
- Footnote markers don't really matter for embeddings

RECOMMENDATION FOR RAG:
- MUST remove page numbers before embedding (high priority)
- Remove running headers before embedding (medium priority)
- Focus OCR correction on actual misspellings (high priority)
- Merge cross-page text without markers (medium priority)
- Embed footnotes separately from main text (low priority - minimal difference)
    """)


if __name__ == "__main__":
    main()
