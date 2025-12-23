#!/usr/bin/env python3
"""Spike 13: Empirically Test Spell-Check Risk

The concern: Spell-checkers might "correct" valid philosophical terms
to wrong words, damaging embeddings and retrieval.

Tests:
1. What does pyspellchecker actually suggest for philosophy terms?
2. If we auto-correct, how often do we damage valid text?
3. What's the embedding impact of wrong corrections?

Usage:
    uv run python spikes/13_spellcheck_risk.py
"""

import sys

try:
    from spellchecker import SpellChecker
except ImportError:
    print("ERROR: pyspellchecker required. Run: uv add pyspellchecker")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    print("ERROR: sentence-transformers required")
    sys.exit(1)


def compute_similarity(model, text1: str, text2: str) -> float:
    """Compute embedding similarity."""
    embeddings = model.encode([text1, text2])
    return float(np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    ))


# Philosophy terms that are valid but might not be in spell-checker
PHILOSOPHY_TERMS = [
    # Greek-origin
    "aporia", "aletheia", "eudaimonia", "phronesis", "techne", "episteme",
    "nous", "logos", "telos", "arche", "ousia", "praxis", "theoria",
    "dianoia", "doxa", "hexis", "energeia", "entelecheia", "hyle",

    # German-origin (sometimes lowercase)
    "dasein", "zeitgeist", "weltanschauung", "aufhebung", "angst",
    "gestalt", "lebenswelt", "sorge", "mitsein", "zuhandenheit",

    # French-origin
    "differance", "jouissance", "ecriture", "bricolage", "deconstruction",

    # Latin-origin
    "apriori", "aposteriori",  # sometimes written as one word

    # Technical philosophical terms
    "intentionality", "phenomenological", "hermeneutic", "ontological",
    "epistemological", "transcendental", "apophantic", "noematic",
    "eidetic", "hyletic", "noetic", "bracketing", "epoche",

    # Names that might appear lowercase in possessive or discussion
    "heideggerian", "husserlian", "derridean", "foucauldian", "deleuzian",
    "nietzschean", "kantian", "hegelian", "marxist", "freudian",
]

# Actual OCR errors we want to catch
OCR_ERRORS = {
    "beautlful": "beautiful",
    "questlon": "question",
    "underrnine": "undermine",
    "rnetaphysics": "metaphysics",
    "phenornenology": "phenomenology",
    "intentlonality": "intentionality",
    "transcendenta1": "transcendental",
}


def main():
    spell = SpellChecker()

    print("="*70)
    print("EXPERIMENT 1: What does spell-checker suggest for philosophy terms?")
    print("="*70)

    dangerous_corrections = []
    unknown_words = []
    known_words = []

    for term in PHILOSOPHY_TERMS:
        if term in spell:
            known_words.append(term)
        else:
            correction = spell.correction(term)
            if correction and correction != term:
                dangerous_corrections.append((term, correction))
            else:
                unknown_words.append(term)

    print(f"\n✅ Known to spell-checker ({len(known_words)}):")
    print(f"   {', '.join(known_words[:20])}...")

    print(f"\n⚠️  Unknown, no suggestion ({len(unknown_words)}):")
    print(f"   {', '.join(unknown_words[:20])}...")

    print(f"\n🚨 DANGEROUS - Would be 'corrected' ({len(dangerous_corrections)}):")
    for term, correction in dangerous_corrections:
        print(f"   {term} → {correction}")

    print("\n" + "="*70)
    print("EXPERIMENT 2: Embedding damage from wrong corrections")
    print("="*70)

    print("\nLoading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Test sentences with philosophy terms
    test_cases = [
        ("The concept of aporia is central to Derrida's work.",
         "aporia", spell.correction("aporia")),

        ("Heidegger's analysis of dasein reveals our being-in-the-world.",
         "dasein", spell.correction("dasein")),

        ("The phenomenological method requires epoché.",
         "epoché", spell.correction("epoché") if "epoché" not in spell else None),

        ("Aristotle distinguished phronesis from techne.",
         "phronesis", spell.correction("phronesis")),
    ]

    print(f"\n{'Original term':<15} {'Correction':<15} {'Sim to original':<18} {'Damage'}")
    print("-" * 65)

    for sentence, term, correction in test_cases:
        if correction and correction != term:
            corrected_sentence = sentence.replace(term, correction)
            sim = compute_similarity(model, sentence, corrected_sentence)
            damage = 1.0 - sim
            status = "🚨 BAD" if damage > 0.05 else "⚠️  Minor" if damage > 0.01 else "✅ OK"
            print(f"{term:<15} {correction:<15} {sim:<18.3f} {damage:.3f} {status}")
        else:
            print(f"{term:<15} {'(no change)':<15} {'N/A':<18} {'N/A'}")

    print("\n" + "="*70)
    print("EXPERIMENT 3: Does spell-checker catch actual OCR errors?")
    print("="*70)

    print(f"\n{'OCR Error':<20} {'Expected':<20} {'Spell-check suggests':<20} {'Match?'}")
    print("-" * 75)

    for error, expected in OCR_ERRORS.items():
        suggestion = spell.correction(error)
        match = "✅" if suggestion == expected else "❌"
        print(f"{error:<20} {expected:<20} {suggestion or '(none)':<20} {match}")

    print("\n" + "="*70)
    print("EXPERIMENT 4: The Conservative Alternative")
    print("="*70)

    print("""
Instead of general spell-checking, what if we ONLY correct
specific known OCR patterns?

OCR Pattern Corrections (mechanical, not semantic):
- rn → m  (rnorning → morning)
- cl → d  (clog → dog... wait, that's wrong too!)
- l ↔ 1 ↔ I  (on1y → only, but Il → II or Il?)
- tl → ti (beautlful → beautiful)
- vv → w  (vvord → word)

The problem: Even these "mechanical" patterns are risky!
- "clog" is a real word, not "dog"
- "Il" could be Roman numeral II or "Il" (Italian "the")
""")

    # Test some pattern-based corrections
    patterns = [
        ("rnorning", "morning", "rn→m"),
        ("clog", "dog", "cl→d"),  # This would be WRONG
        ("beautlful", "beautiful", "tl→ti"),
        ("vvord", "word", "vv→w"),
        ("on1y", "only", "1→l"),
        ("lIl", "III", "l→I"),  # Ambiguous!
    ]

    print(f"\n{'Input':<15} {'Pattern':<10} {'Output':<15} {'Correct?'}")
    print("-" * 50)

    for inp, expected, pattern in patterns:
        # Simulate pattern replacement (simplified)
        output = inp
        if "rn" in pattern:
            output = inp.replace("rn", "m")
        elif "cl" in pattern:
            output = inp.replace("cl", "d")
        elif "tl" in pattern:
            output = inp.replace("tl", "ti")
        elif "vv" in pattern:
            output = inp.replace("vv", "w")
        elif "1→l" in pattern:
            output = inp.replace("1", "l")

        correct = "✅" if output == expected else "❌ WRONG"
        print(f"{inp:<15} {pattern:<10} {output:<15} {correct}")

    print("\n" + "="*70)
    print("CONCLUSIONS")
    print("="*70)
    print(f"""
FINDINGS:

1. Spell-checker WOULD damage {len(dangerous_corrections)} philosophy terms
   by "correcting" them to wrong words.

2. Even "mechanical" OCR patterns (rn→m, cl→d) can be wrong:
   - "clog" → "dog" is WRONG
   - "lIl" → "III" vs "lil" is ambiguous

3. The generalization problem is REAL:
   - We tested {len(PHILOSOPHY_TERMS)} terms
   - But any book might have terms we didn't think of
   - Testing doesn't prove safety

SAFER ALTERNATIVES:

Option A: DON'T AUTO-CORRECT AT ALL
- Flag potential errors for human review
- Let the user decide
- Safest, but more work for user

Option B: ONLY CORRECT WITH VERY HIGH CONFIDENCE
- Word must be unknown to spell-checker
- Suggestion must have very high similarity to original
- Word must appear only once (not consistent usage)
- Still risky for novel terms

Option C: CORRECT ONLY WHAT WE CAN VERIFY
- If we have the same book in a different edition/format
- Compare and correct based on known-good version
- Not always available

Option D: USE FUZZY RETRIEVAL INSTEAD
- Don't correct the text at all
- Use fuzzy/phonetic matching in the retrieval system
- Query "beautiful" matches "beautlful" at search time
- Zero risk to source text

Option E: EMBED BOTH VERSIONS
- Keep original text
- Also embed "cleaned" version
- Use both for retrieval
- Higher storage, but no information loss
    """)


if __name__ == "__main__":
    main()
