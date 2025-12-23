#!/usr/bin/env python3
"""
Spike 27: Document Profile Auto-Detection

PURPOSE: Test whether we can automatically detect document types.

QUESTIONS TO ANSWER:
1. Can we reliably distinguish books from articles from essays?
2. What are the failure modes of auto-detection?
3. Do we need human override for ambiguous cases?
4. Which indicators are most reliable?

RUN:
  uv run python spikes/27_document_profile_detection.py                    # All PDFs
  uv run python spikes/27_document_profile_detection.py sample.pdf         # Single PDF
  uv run python spikes/27_document_profile_detection.py --verbose          # Detailed scoring
"""

import sys
import re
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Install PyMuPDF: uv add pymupdf")
    sys.exit(1)


class DocumentType(Enum):
    BOOK = "book"
    ARTICLE = "article"
    ESSAY = "essay"
    REPORT = "report"
    GENERIC = "generic"


@dataclass
class ProfileIndicator:
    """A single indicator for document type."""
    name: str
    detected: bool
    score: float  # How much this contributes to profile
    evidence: str = ""


@dataclass
class ProfileDetectionResult:
    """Result of document profile detection."""
    pdf_path: str
    detected_type: DocumentType
    confidence: float
    scores: dict = field(default_factory=dict)  # profile -> score
    indicators: list[ProfileIndicator] = field(default_factory=list)
    # Manual validation
    manual_type: DocumentType | None = None  # For comparison
    notes: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# Indicator Functions
# ─────────────────────────────────────────────────────────────

def check_page_count(doc: fitz.Document) -> list[ProfileIndicator]:
    """Page count indicators."""
    indicators = []
    page_count = doc.page_count

    if page_count > 200:
        indicators.append(ProfileIndicator(
            name="many_pages",
            detected=True,
            score=0.4,
            evidence=f"{page_count} pages"
        ))
    elif page_count > 50:
        indicators.append(ProfileIndicator(
            name="medium_pages",
            detected=True,
            score=0.2,
            evidence=f"{page_count} pages"
        ))
    elif page_count < 30:
        indicators.append(ProfileIndicator(
            name="few_pages",
            detected=True,
            score=0.3,
            evidence=f"{page_count} pages"
        ))

    return indicators


def check_has_toc(doc: fitz.Document) -> list[ProfileIndicator]:
    """Check for table of contents."""
    indicators = []

    # Check first 30 pages for ToC indicators
    toc_found = False
    for page_num in range(min(30, doc.page_count)):
        text = doc[page_num].get_text().lower()
        if "table of contents" in text or ("contents" in text[:500]):
            # Verify it looks like a ToC (has dotted leaders or page numbers)
            if re.search(r'\.{5,}|\s+\d+\s*$', text, re.MULTILINE):
                toc_found = True
                break

    indicators.append(ProfileIndicator(
        name="has_toc",
        detected=toc_found,
        score=0.4 if toc_found else 0,
        evidence="ToC page found" if toc_found else "No ToC detected"
    ))

    return indicators


def check_has_outline(doc: fitz.Document) -> list[ProfileIndicator]:
    """Check for PDF outline/bookmarks."""
    indicators = []

    toc = doc.get_toc()
    has_outline = len(toc) > 0

    indicators.append(ProfileIndicator(
        name="has_outline",
        detected=has_outline,
        score=0.3 if has_outline else 0,
        evidence=f"{len(toc)} outline entries" if has_outline else "No outline"
    ))

    # Deep outline (multiple levels) suggests book
    if toc:
        max_level = max(item[0] for item in toc)
        if max_level >= 3:
            indicators.append(ProfileIndicator(
                name="deep_outline",
                detected=True,
                score=0.2,
                evidence=f"Outline depth: {max_level}"
            ))

    return indicators


def check_has_abstract(doc: fitz.Document) -> list[ProfileIndicator]:
    """Check for abstract section (academic article indicator)."""
    indicators = []

    # Check first 5 pages
    abstract_found = False
    for page_num in range(min(5, doc.page_count)):
        text = doc[page_num].get_text().lower()
        if re.search(r'^abstract\s*$|^abstract:', text, re.MULTILINE):
            abstract_found = True
            break
        if re.search(r'\babstract\b.*\n.{100,}', text):  # Abstract followed by text
            abstract_found = True
            break

    indicators.append(ProfileIndicator(
        name="has_abstract",
        detected=abstract_found,
        score=0.5 if abstract_found else 0,
        evidence="Abstract section found" if abstract_found else "No abstract"
    ))

    return indicators


def check_chapter_indicators(doc: fitz.Document) -> list[ProfileIndicator]:
    """Check for chapter indicators."""
    indicators = []

    chapter_count = 0
    part_count = 0

    # Sample first 100 pages
    for page_num in range(min(100, doc.page_count)):
        text = doc[page_num].get_text()
        # Look for "Chapter X" or "CHAPTER X" patterns
        chapter_count += len(re.findall(r'\bchapter\s+[ivxlc\d]+\b', text, re.IGNORECASE))
        part_count += len(re.findall(r'\bpart\s+[ivxlc\d]+\b', text, re.IGNORECASE))

    if chapter_count >= 3:
        indicators.append(ProfileIndicator(
            name="has_chapters",
            detected=True,
            score=0.5,
            evidence=f"{chapter_count} chapter markers"
        ))

    if part_count >= 2:
        indicators.append(ProfileIndicator(
            name="has_parts",
            detected=True,
            score=0.3,
            evidence=f"{part_count} part markers"
        ))

    return indicators


def check_section_numbering(doc: fitz.Document) -> list[ProfileIndicator]:
    """Check for numbered sections (report indicator)."""
    indicators = []

    numbered_sections = 0

    # Sample pages
    for page_num in range(min(50, doc.page_count)):
        text = doc[page_num].get_text()
        # Pattern: "1.2.3 Section Title" at start of line
        numbered_sections += len(re.findall(r'^\s*\d+\.\d+(?:\.\d+)?\s+[A-Z]', text, re.MULTILINE))

    if numbered_sections >= 5:
        indicators.append(ProfileIndicator(
            name="numbered_sections",
            detected=True,
            score=0.4,
            evidence=f"{numbered_sections} numbered sections"
        ))

    return indicators


def check_bibliography(doc: fitz.Document) -> list[ProfileIndicator]:
    """Check for bibliography/references section."""
    indicators = []

    # Check last 30% of document
    start_page = int(doc.page_count * 0.7)
    bib_found = False

    for page_num in range(start_page, doc.page_count):
        text = doc[page_num].get_text().lower()
        if re.search(r'^(bibliography|references|works cited)\s*$', text, re.MULTILINE):
            bib_found = True
            break

    indicators.append(ProfileIndicator(
        name="has_bibliography",
        detected=bib_found,
        score=0.2 if bib_found else 0,
        evidence="Bibliography found" if bib_found else "No bibliography section"
    ))

    return indicators


def check_metadata(doc: fitz.Document) -> list[ProfileIndicator]:
    """Check PDF metadata for clues."""
    indicators = []
    meta = doc.metadata

    # Check for ISBN (book indicator)
    if meta:
        meta_text = ' '.join(str(v) for v in meta.values() if v)
        if re.search(r'isbn|978-?\d', meta_text.lower()):
            indicators.append(ProfileIndicator(
                name="has_isbn",
                detected=True,
                score=0.4,
                evidence="ISBN in metadata"
            ))

        # Check for DOI (article indicator)
        if re.search(r'doi:|10\.\d{4,}', meta_text.lower()):
            indicators.append(ProfileIndicator(
                name="has_doi",
                detected=True,
                score=0.4,
                evidence="DOI in metadata"
            ))

    return indicators


def check_front_matter(doc: fitz.Document) -> list[ProfileIndicator]:
    """Check for front matter indicators."""
    indicators = []

    # Check first 20 pages for front matter patterns
    has_preface = False
    has_foreword = False
    has_acknowledgments = False

    for page_num in range(min(20, doc.page_count)):
        text = doc[page_num].get_text().lower()
        if re.search(r'^preface\s*$', text, re.MULTILINE):
            has_preface = True
        if re.search(r'^foreword\s*$', text, re.MULTILINE):
            has_foreword = True
        if re.search(r'^acknowledgments?\s*$', text, re.MULTILINE):
            has_acknowledgments = True

    front_matter_count = sum([has_preface, has_foreword, has_acknowledgments])

    if front_matter_count >= 2:
        indicators.append(ProfileIndicator(
            name="has_front_matter",
            detected=True,
            score=0.3,
            evidence=f"Found {front_matter_count} front matter sections"
        ))

    return indicators


# ─────────────────────────────────────────────────────────────
# Profile Scoring
# ─────────────────────────────────────────────────────────────

PROFILE_WEIGHTS = {
    DocumentType.BOOK: {
        "many_pages": 0.8,
        "medium_pages": 0.3,
        "has_toc": 0.7,
        "has_outline": 0.5,
        "deep_outline": 0.4,
        "has_chapters": 0.8,
        "has_parts": 0.6,
        "has_bibliography": 0.2,
        "has_isbn": 0.9,
        "has_front_matter": 0.5,
    },
    DocumentType.ARTICLE: {
        "few_pages": 0.6,
        "medium_pages": 0.3,
        "has_abstract": 0.9,
        "has_bibliography": 0.5,
        "has_doi": 0.9,
    },
    DocumentType.ESSAY: {
        "few_pages": 0.5,
        "medium_pages": 0.3,
        # Essays typically lack ToC, outline, chapters
    },
    DocumentType.REPORT: {
        "medium_pages": 0.3,
        "many_pages": 0.2,
        "numbered_sections": 0.8,
        "has_toc": 0.4,
    },
}


def calculate_profile_scores(indicators: list[ProfileIndicator]) -> dict:
    """Calculate score for each profile based on indicators."""
    scores = {profile: 0.0 for profile in DocumentType}

    indicator_map = {ind.name: ind for ind in indicators if ind.detected}

    for profile, weights in PROFILE_WEIGHTS.items():
        for indicator_name, weight in weights.items():
            if indicator_name in indicator_map:
                scores[profile] += weight * indicator_map[indicator_name].score

    # Normalize
    max_score = max(scores.values()) if scores.values() else 1
    if max_score > 0:
        for profile in scores:
            scores[profile] = scores[profile] / max_score

    return scores


def detect_profile(doc: fitz.Document) -> tuple[DocumentType, float, list[ProfileIndicator], dict]:
    """
    Detect document profile from indicators.

    Returns: (detected_type, confidence, indicators, scores)
    """
    # Collect all indicators
    indicators = []
    indicators.extend(check_page_count(doc))
    indicators.extend(check_has_toc(doc))
    indicators.extend(check_has_outline(doc))
    indicators.extend(check_has_abstract(doc))
    indicators.extend(check_chapter_indicators(doc))
    indicators.extend(check_section_numbering(doc))
    indicators.extend(check_bibliography(doc))
    indicators.extend(check_metadata(doc))
    indicators.extend(check_front_matter(doc))

    # Calculate scores
    scores = calculate_profile_scores(indicators)

    # Find best match
    best_profile = max(scores.keys(), key=lambda p: scores[p])
    confidence = scores[best_profile]

    # If confidence is too low, fall back to generic
    if confidence < 0.3:
        best_profile = DocumentType.GENERIC
        confidence = 1.0 - max(scores.values())  # Confidence in "not the others"

    return best_profile, confidence, indicators, scores


# ─────────────────────────────────────────────────────────────
# Manual Classification (for validation)
# ─────────────────────────────────────────────────────────────

# Known document types for our test PDFs
KNOWN_TYPES = {
    "Derrida_TheBeastAndTheSovereignVol1.pdf": DocumentType.BOOK,
    "Derrida_MarginsOfPhilosophy.pdf": DocumentType.BOOK,
    "Derrida_TheTruthInPainting.pdf": DocumentType.BOOK,
    "Derrida_WritingAndDifference.pdf": DocumentType.BOOK,
    "Heidegger_BeingAndTime.pdf": DocumentType.BOOK,
    "Heidegger_DiscourseOnThinking.pdf": DocumentType.BOOK,
    "Heidegger_Pathmarks.pdf": DocumentType.BOOK,  # Essay collection
    "Kant_CritiqueOfJudgement.pdf": DocumentType.BOOK,
    "Lenin_StateAndRevolution.pdf": DocumentType.BOOK,
    "ComayRebecca_MourningSickness_HegelAndTheFrenchRevolution.pdf": DocumentType.BOOK,
}


def analyze_pdf(pdf_path: Path, verbose: bool = False) -> ProfileDetectionResult:
    """
    Analyze a PDF and detect its profile.
    """
    result = ProfileDetectionResult(
        pdf_path=str(pdf_path),
        detected_type=DocumentType.GENERIC,
        confidence=0.0
    )

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        result.notes.append(f"Failed to open: {e}")
        return result

    try:
        # Detect profile
        detected, confidence, indicators, scores = detect_profile(doc)

        result.detected_type = detected
        result.confidence = confidence
        result.indicators = indicators
        result.scores = {k.value: v for k, v in scores.items()}

        # Check against known type
        filename = Path(pdf_path).name
        if filename in KNOWN_TYPES:
            result.manual_type = KNOWN_TYPES[filename]
            if result.detected_type == result.manual_type:
                result.notes.append("✅ Matches manual classification")
            else:
                result.notes.append(f"❌ Manual: {result.manual_type.value}, Detected: {result.detected_type.value}")

        doc.close()
        return result

    except Exception as e:
        result.notes.append(f"Error during analysis: {e}")
        doc.close()
        return result


def print_result(result: ProfileDetectionResult, verbose: bool = False):
    """Print analysis result."""
    name = Path(result.pdf_path).name

    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"{'='*60}")

    print(f"Detected: {result.detected_type.value.upper()} ({result.confidence:.0%} confidence)")

    if result.manual_type:
        match = "✅" if result.detected_type == result.manual_type else "❌"
        print(f"Manual:   {result.manual_type.value.upper()} {match}")

    if verbose:
        print(f"\n--- Profile Scores ---")
        for profile, score in sorted(result.scores.items(), key=lambda x: -x[1]):
            bar = "█" * int(score * 20)
            print(f"  {profile:10} {score:.2f} {bar}")

        print(f"\n--- Detected Indicators ---")
        detected = [i for i in result.indicators if i.detected]
        for ind in detected:
            print(f"  {ind.name}: {ind.evidence} (+{ind.score:.1f})")

    for note in result.notes:
        print(f"  {note}")


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    # Get PDF paths
    if args:
        pdf_paths = [Path(a) for a in args if Path(a).exists()]
    else:
        # Default: all PDFs in sample_pdfs
        sample_dir = Path(__file__).parent / "sample_pdfs"
        pdf_paths = sorted(sample_dir.glob("*.pdf"))
        # Exclude small test snippets
        pdf_paths = [p for p in pdf_paths if p.stat().st_size > 500_000]

    if not pdf_paths:
        print("No PDFs found. Provide paths or place PDFs in spikes/sample_pdfs/")
        sys.exit(1)

    print(f"Analyzing {len(pdf_paths)} PDFs for document profile...")

    results = []
    for pdf_path in pdf_paths:
        result = analyze_pdf(pdf_path, verbose)
        results.append(result)
        print_result(result, verbose)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    # Detection breakdown
    type_counts = defaultdict(int)
    for r in results:
        type_counts[r.detected_type.value] += 1

    print(f"\nDetected types:")
    for type_name, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {type_name}: {count} ({100*count/len(results):.0f}%)")

    # Accuracy against manual classifications
    with_manual = [r for r in results if r.manual_type]
    if with_manual:
        correct = sum(1 for r in with_manual if r.detected_type == r.manual_type)
        print(f"\nAccuracy (vs manual): {correct}/{len(with_manual)} ({100*correct/len(with_manual):.0f}%)")

        # Show misclassifications
        wrong = [r for r in with_manual if r.detected_type != r.manual_type]
        if wrong:
            print(f"\nMisclassifications:")
            for r in wrong:
                name = Path(r.pdf_path).name
                print(f"  {name}: detected={r.detected_type.value}, actual={r.manual_type.value}")

    # Confidence distribution
    avg_conf = sum(r.confidence for r in results) / len(results)
    low_conf = [r for r in results if r.confidence < 0.5]

    print(f"\nConfidence: avg={avg_conf:.0%}, low (<50%): {len(low_conf)}")

    # Recommendations
    print(f"\n--- RECOMMENDATIONS ---")

    if with_manual:
        accuracy = correct / len(with_manual)
        if accuracy >= 0.8:
            print(f"✅ {accuracy:.0%} accuracy - auto-detection is reliable")
        elif accuracy >= 0.6:
            print(f"⚠️  {accuracy:.0%} accuracy - auto-detection needs tuning")
        else:
            print(f"❌ {accuracy:.0%} accuracy - auto-detection unreliable")

    if low_conf:
        print(f"⚠️  {len(low_conf)} PDFs with low confidence - may need human override")
    else:
        print("✅ All PDFs classified with reasonable confidence")


if __name__ == "__main__":
    main()
