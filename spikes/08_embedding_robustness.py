#!/usr/bin/env python3
"""
Spike 08: Test Embedding Robustness Against OCR Errors

PURPOSE: Determine if semantic embeddings are actually robust to OCR errors.
         This tests a key assumption for RAG pipeline viability.

RUN:
  uv run python spikes/08_embedding_robustness.py
  uv run python spikes/08_embedding_robustness.py --real-ocr sample.pdf

QUESTIONS TO ANSWER:
1. How much does cosine similarity degrade with OCR errors?
2. Which error types hurt embeddings most?
3. At what error rate do embeddings become unreliable?
4. Is OCR'd text actually "good enough" for RAG?
"""

import sys
import re
import random
from dataclasses import dataclass
from typing import Optional

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Install sentence-transformers: uv add sentence-transformers")
    sys.exit(1)

try:
    import fitz
except ImportError:
    fitz = None


# ============================================================================
# OCR Error Simulation
# ============================================================================

# Common OCR character confusions
CHAR_CONFUSIONS = {
    'l': ['1', 'I', '|'],
    'I': ['l', '1', '|'],
    '1': ['l', 'I', '|'],
    'O': ['0', 'Q'],
    '0': ['O', 'o'],
    'o': ['0', 'O'],
    'S': ['5', '$'],
    '5': ['S', '$'],
    'B': ['8', '3'],
    '8': ['B', '3'],
    'e': ['c', 'o'],
    'c': ['e', 'o'],
    'n': ['m', 'ri'],
    'm': ['n', 'rn'],
    'rn': ['m'],
    'i': ['l', '1', 'j'],
    'a': ['o', 'e'],
    'u': ['v', 'n'],
    'v': ['u', 'w'],
    'h': ['b', 'n'],
    'f': ['t', 'r'],
    't': ['f', 'l'],
    'g': ['q', '9'],
    'q': ['g', '9'],
    'd': ['cl', 'o'],
    'w': ['vv', 'w'],
}

# Words that OCR commonly produces as real-but-wrong words
REAL_WORD_ERRORS = {
    'from': 'form',
    'form': 'from',
    'the': 'tbe',
    'and': 'arid',
    'that': 'thar',
    'this': 'tills',
    'have': 'hare',
    'been': 'bccn',
    'being': 'bcing',
    'their': 'thcir',
    'would': 'wonld',
    'could': 'conld',
    'should': 'shonld',
}


def simulate_char_errors(text: str, error_rate: float = 0.05) -> str:
    """Simulate character-level OCR errors."""
    result = list(text)
    for i, char in enumerate(result):
        if random.random() < error_rate and char in CHAR_CONFUSIONS:
            result[i] = random.choice(CHAR_CONFUSIONS[char])
    return ''.join(result)


def simulate_word_errors(text: str, error_rate: float = 0.05) -> str:
    """Simulate word-level OCR errors (real-word substitutions)."""
    words = text.split()
    for i, word in enumerate(words):
        lower = word.lower()
        if random.random() < error_rate and lower in REAL_WORD_ERRORS:
            # Preserve case
            replacement = REAL_WORD_ERRORS[lower]
            if word[0].isupper():
                replacement = replacement.capitalize()
            words[i] = replacement
    return ' '.join(words)


def simulate_hyphenation_errors(text: str, error_rate: float = 0.1) -> str:
    """Simulate broken hyphenation at line ends."""
    words = text.split()
    result = []
    for word in words:
        if len(word) > 6 and random.random() < error_rate:
            # Break word with hyphen
            mid = len(word) // 2
            result.append(word[:mid] + '-')
            result.append(word[mid:])
        else:
            result.append(word)
    return ' '.join(result)


def simulate_merge_errors(text: str, error_rate: float = 0.05) -> str:
    """Simulate merged words (missing spaces)."""
    words = text.split()
    result = []
    i = 0
    while i < len(words):
        if i < len(words) - 1 and random.random() < error_rate:
            # Merge two words
            result.append(words[i] + words[i + 1])
            i += 2
        else:
            result.append(words[i])
            i += 1
    return ' '.join(result)


def simulate_all_errors(text: str, severity: str = 'medium') -> str:
    """Apply multiple OCR error types."""
    rates = {
        'light': {'char': 0.02, 'word': 0.02, 'hyphen': 0.05, 'merge': 0.02},
        'medium': {'char': 0.05, 'word': 0.05, 'hyphen': 0.1, 'merge': 0.05},
        'heavy': {'char': 0.1, 'word': 0.1, 'hyphen': 0.15, 'merge': 0.1},
    }
    r = rates[severity]

    text = simulate_char_errors(text, r['char'])
    text = simulate_word_errors(text, r['word'])
    text = simulate_hyphenation_errors(text, r['hyphen'])
    text = simulate_merge_errors(text, r['merge'])
    return text


# ============================================================================
# Embedding Comparison
# ============================================================================

@dataclass
class EmbeddingComparison:
    """Results of comparing clean vs corrupted embeddings."""
    clean_text: str
    corrupted_text: str
    error_type: str
    error_rate: float
    cosine_similarity: float
    char_error_rate: float  # Actual measured CER


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def char_error_rate(clean: str, corrupted: str) -> float:
    """Compute character error rate (Levenshtein-based approximation)."""
    # Simple approximation: count different characters
    if len(clean) == 0:
        return 1.0

    # Align by taking min length
    min_len = min(len(clean), len(corrupted))
    errors = sum(1 for i in range(min_len) if clean[i] != corrupted[i])
    errors += abs(len(clean) - len(corrupted))

    return errors / len(clean)


def test_embedding_robustness(
    model: SentenceTransformer,
    texts: list[str],
    error_types: list[str] = ['char', 'word', 'hyphen', 'merge', 'all'],
    error_rates: list[float] = [0.02, 0.05, 0.1, 0.15, 0.2],
) -> list[EmbeddingComparison]:
    """Test how embeddings degrade with different OCR errors."""
    results = []

    for text in texts:
        clean_embedding = model.encode(text)

        for error_type in error_types:
            for rate in error_rates:
                # Generate corrupted text
                if error_type == 'char':
                    corrupted = simulate_char_errors(text, rate)
                elif error_type == 'word':
                    corrupted = simulate_word_errors(text, rate)
                elif error_type == 'hyphen':
                    corrupted = simulate_hyphenation_errors(text, rate)
                elif error_type == 'merge':
                    corrupted = simulate_merge_errors(text, rate)
                elif error_type == 'all':
                    severity = 'light' if rate < 0.05 else 'medium' if rate < 0.1 else 'heavy'
                    corrupted = simulate_all_errors(text, severity)
                else:
                    continue

                # Compute embedding similarity
                corrupted_embedding = model.encode(corrupted)
                similarity = cosine_sim(clean_embedding, corrupted_embedding)
                cer = char_error_rate(text, corrupted)

                results.append(EmbeddingComparison(
                    clean_text=text[:100],
                    corrupted_text=corrupted[:100],
                    error_type=error_type,
                    error_rate=rate,
                    cosine_similarity=similarity,
                    char_error_rate=cer,
                ))

    return results


# ============================================================================
# Real OCR Comparison (PDF vs Clean Text)
# ============================================================================

def extract_pdf_pages(pdf_path: str, pages: list[int]) -> dict[int, str]:
    """Extract text from specific PDF pages."""
    if fitz is None:
        print("PyMuPDF not available for PDF extraction")
        return {}

    doc = fitz.open(pdf_path)
    result = {}
    for page_num in pages:
        if 0 <= page_num < len(doc):
            result[page_num] = doc[page_num].get_text()
    return result


# ============================================================================
# Test Samples
# ============================================================================

PHILOSOPHY_SAMPLES = [
    "The beautiful is that which pleases universally without requiring a concept.",
    "All our knowledge begins with experience, but it does not follow that it arises from experience.",
    "The thing in itself remains unknown to us, we only know appearances.",
    "Freedom is the ratio essendi of the moral law, while the moral law is the ratio cognoscendi of freedom.",
    "The transcendental unity of apperception is the highest principle of all employment of the understanding.",
    "Thoughts without content are empty, intuitions without concepts are blind.",
    "Two things fill the mind with ever new and increasing admiration and reverence: the starry heavens above me and the moral law within me.",
    "Being and Time explores the question of the meaning of Being through an analysis of Dasein.",
    "Différance is neither a word nor a concept, but the possibility of conceptuality.",
    "The Other is not simply an alter ego but a radical exteriority that calls my freedom into question.",
]


# ============================================================================
# Main
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Test embedding robustness against OCR errors')
    parser.add_argument('--real-ocr', type=str, help='PDF file to extract real OCR samples from')
    parser.add_argument('--model', type=str, default='all-MiniLM-L6-v2', help='Sentence transformer model')
    parser.add_argument('--pages', type=str, default='50,100,200,300', help='Pages to sample from PDF')
    args = parser.parse_args()

    print("Loading embedding model...")
    model = SentenceTransformer(args.model)
    print(f"Model: {args.model}")
    print()

    # Test with simulated errors
    print("=" * 70)
    print("SIMULATED OCR ERRORS")
    print("=" * 70)
    print()

    results = test_embedding_robustness(
        model,
        PHILOSOPHY_SAMPLES,
        error_types=['char', 'word', 'hyphen', 'merge', 'all'],
        error_rates=[0.02, 0.05, 0.1, 0.15],
    )

    # Aggregate results by error type and rate
    from collections import defaultdict
    aggregated = defaultdict(list)

    for r in results:
        key = (r.error_type, r.error_rate)
        aggregated[key].append(r.cosine_similarity)

    print(f"{'Error Type':<12} {'Rate':>6} {'Avg Similarity':>15} {'Min':>8} {'Max':>8}")
    print("-" * 55)

    for (error_type, rate), sims in sorted(aggregated.items()):
        avg = np.mean(sims)
        min_sim = np.min(sims)
        max_sim = np.max(sims)

        # Color coding based on similarity
        status = "✓" if avg > 0.9 else "⚠" if avg > 0.8 else "✗"
        print(f"{error_type:<12} {rate:>5.0%} {status} {avg:>13.3f} {min_sim:>8.3f} {max_sim:>8.3f}")

    print()
    print("=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print()
    print("Cosine Similarity Thresholds:")
    print("  > 0.95  Excellent - virtually identical semantic meaning")
    print("  > 0.90  Good - minor degradation, still useful for RAG")
    print("  > 0.80  Marginal - noticeable degradation, may miss matches")
    print("  < 0.80  Poor - significant semantic drift, unreliable")
    print()

    # Show some examples
    print("=" * 70)
    print("EXAMPLE CORRUPTIONS")
    print("=" * 70)
    print()

    sample = PHILOSOPHY_SAMPLES[0]
    print(f"Original: {sample}")
    print()

    for severity in ['light', 'medium', 'heavy']:
        corrupted = simulate_all_errors(sample, severity)
        clean_emb = model.encode(sample)
        corr_emb = model.encode(corrupted)
        sim = cosine_sim(clean_emb, corr_emb)
        print(f"{severity.upper()} ({sim:.3f}): {corrupted}")
        print()

    # Real OCR comparison if PDF provided
    if args.real_ocr:
        print("=" * 70)
        print(f"REAL OCR FROM: {args.real_ocr}")
        print("=" * 70)
        print()

        pages = [int(p) for p in args.pages.split(',')]
        page_texts = extract_pdf_pages(args.real_ocr, pages)

        for page_num, text in page_texts.items():
            # Take first paragraph-ish chunk
            text = text.strip()[:500]
            if len(text) < 50:
                continue

            print(f"--- Page {page_num} ---")
            print(f"Text: {text[:200]}...")
            print()

            # We don't have ground truth, so just show the text
            # and let the user judge quality

    print("=" * 70)
    print("CONCLUSIONS")
    print("=" * 70)
    print()


if __name__ == '__main__':
    main()
