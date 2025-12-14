#!/usr/bin/env python3
"""
Spike 05: Evaluate Existing OCR Quality in Philosophy PDFs

PURPOSE: Determine how bad existing OCR text layers are across philosophy PDF sources.
         This informs whether custom OCR is worth the investment.

RUN:
  uv run python spikes/05_ocr_quality_survey.py sample.pdf
  uv run python spikes/05_ocr_quality_survey.py sample.pdf --detailed
  uv run python spikes/05_ocr_quality_survey.py sample.pdf --compare-image

QUESTIONS TO ANSWER:
1. What % of philosophy PDFs have unreliable text layers?
2. What types of errors are most common?
3. Is the text layer good enough, or do we need image extraction?
4. Which sources (Google Books, Internet Archive, etc.) have better/worse OCR?
"""

import sys
import re
from pathlib import Path
from dataclasses import dataclass, field
from collections import Counter
from typing import Optional

try:
    import fitz
except ImportError:
    print("Install PyMuPDF: uv add pymupdf")
    sys.exit(1)


@dataclass
class PageQuality:
    """Quality assessment for a single page."""
    page_num: int
    char_count: int
    garbage_chars: int
    valid_word_ratio: float
    has_text_layer: bool
    has_images: bool
    suspected_issues: list[str] = field(default_factory=list)


@dataclass
class DocumentQuality:
    """Overall quality assessment for a document."""
    path: str
    total_pages: int
    pages_with_text: int
    pages_with_issues: int
    overall_garbage_ratio: float
    overall_valid_word_ratio: float
    error_types: Counter = field(default_factory=Counter)
    page_details: list[PageQuality] = field(default_factory=list)
    recommendation: str = ""


# Common OCR garbage patterns
GARBAGE_PATTERNS = [
    r'[^\x00-\x7F\u00C0-\u024F\u0370-\u03FF\u1F00-\u1FFF]',  # Non-Latin/Greek chars (broad)
    r'[\x00-\x08\x0B\x0C\x0E-\x1F]',  # Control characters
    r'[⁰¹²³⁴⁵⁶⁷⁸⁹]+[a-z]+',  # Superscripts merged with text
    r'\b[A-Z]{10,}\b',  # Long runs of caps (often errors)
    r'[|!1l]{5,}',  # Vertical line confusion
    r'[oO0]{5,}',  # Zero/O confusion runs
]

# Common words to check validity (English + Philosophy terms)
COMMON_WORDS = {
    'the', 'and', 'that', 'this', 'with', 'from', 'which', 'have', 'been',
    'being', 'consciousness', 'reason', 'knowledge', 'truth', 'nature',
    'world', 'mind', 'thought', 'experience', 'existence', 'reality',
    'philosophy', 'concept', 'theory', 'argument', 'question', 'answer',
    'chapter', 'section', 'introduction', 'conclusion', 'notes', 'index',
    # German philosophy terms
    'sein', 'dasein', 'nicht', 'aber', 'oder', 'wenn', 'durch',
    # Common Greek (transliterated for checking)
    'logos', 'nous', 'physis', 'techne', 'polis',
}


def count_garbage_chars(text: str) -> int:
    """Count characters that look like OCR errors."""
    count = 0
    for pattern in GARBAGE_PATTERNS:
        count += len(re.findall(pattern, text))
    return count


def estimate_valid_word_ratio(text: str) -> float:
    """Estimate what fraction of words are valid."""
    # Simple tokenization
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    if not words:
        return 0.0
    
    # Check against common words + basic heuristics
    valid = 0
    for word in words:
        # Known word
        if word in COMMON_WORDS:
            valid += 1
            continue
        # Looks like a word (consonant-vowel patterns)
        if re.search(r'[aeiou]', word) and re.search(r'[bcdfghjklmnpqrstvwxyz]', word):
            # Not too many repeated characters
            if not re.search(r'(.)\1{3,}', word):
                valid += 1
    
    return valid / len(words)


def detect_specific_issues(text: str, page_num: int) -> list[str]:
    """Detect specific OCR issue types."""
    issues = []
    
    # Greek garbling
    if re.search(r'[αβγδεζηθικλμνξοπρστυφχψω]', text):
        # Greek present, check if it's garbled
        greek_words = re.findall(r'[α-ω]+', text)
        if greek_words and any(len(w) > 15 for w in greek_words):
            issues.append("garbled_greek")
    
    # German umlaut issues
    if re.search(r'[äöüÄÖÜß]', text):
        if re.search(r'[äöüÄÖÜß][äöüÄÖÜß]', text):  # Adjacent umlauts = likely error
            issues.append("umlaut_errors")
    
    # Page number confusion
    if page_num < 50:  # Front matter
        if re.search(r'\b[ivxlcdm]{2,}\b', text.lower()):  # Roman numerals
            pass  # Expected
        elif re.search(r'\b[1il][vx]\b', text.lower()):  # Confused roman
            issues.append("roman_numeral_confusion")
    
    # Footnote marker issues
    superscript_pattern = r'[⁰¹²³⁴⁵⁶⁷⁸⁹]+'
    if re.search(superscript_pattern, text):
        # Check if markers are in weird places
        if re.search(superscript_pattern + r'\s*$', text):
            pass  # End of line, probably OK
        elif re.search(r'\s' + superscript_pattern + r'\s', text):
            issues.append("floating_superscripts")
    
    # Line merge issues (no spaces between words)
    long_words = re.findall(r'\b[a-z]{20,}\b', text.lower())
    if long_words:
        issues.append("merged_words")
    
    # Hyphenation issues (broken words)
    if re.search(r'\w-\s*\n\s*\w', text):
        issues.append("broken_hyphenation")
    
    return issues


def assess_page(page, page_num: int) -> PageQuality:
    """Assess OCR quality for a single page."""
    text = page.get_text()
    
    has_text = bool(text.strip())
    has_images = any(block["type"] == 1 for block in page.get_text("dict")["blocks"])
    
    if not has_text:
        return PageQuality(
            page_num=page_num,
            char_count=0,
            garbage_chars=0,
            valid_word_ratio=0.0,
            has_text_layer=False,
            has_images=has_images,
            suspected_issues=["no_text_layer"],
        )
    
    garbage = count_garbage_chars(text)
    valid_ratio = estimate_valid_word_ratio(text)
    issues = detect_specific_issues(text, page_num)
    
    # Add issue flags based on metrics
    if len(text) > 0 and garbage / len(text) > 0.05:
        issues.append("high_garbage_ratio")
    if valid_ratio < 0.5:
        issues.append("low_valid_words")
    
    return PageQuality(
        page_num=page_num,
        char_count=len(text),
        garbage_chars=garbage,
        valid_word_ratio=valid_ratio,
        has_text_layer=True,
        has_images=has_images,
        suspected_issues=issues,
    )


def assess_document(pdf_path: str, max_pages: Optional[int] = None) -> DocumentQuality:
    """Assess OCR quality for entire document."""
    doc = fitz.open(pdf_path)
    
    pages_to_check = min(doc.page_count, max_pages) if max_pages else doc.page_count
    
    page_details = []
    total_chars = 0
    total_garbage = 0
    valid_ratios = []
    error_types = Counter()
    
    for i in range(pages_to_check):
        pq = assess_page(doc[i], i)
        page_details.append(pq)
        
        total_chars += pq.char_count
        total_garbage += pq.garbage_chars
        if pq.valid_word_ratio > 0:
            valid_ratios.append(pq.valid_word_ratio)
        
        for issue in pq.suspected_issues:
            error_types[issue] += 1
    
    doc.close()
    
    # Calculate overall metrics
    garbage_ratio = total_garbage / total_chars if total_chars > 0 else 1.0
    avg_valid_ratio = sum(valid_ratios) / len(valid_ratios) if valid_ratios else 0.0
    pages_with_text = sum(1 for p in page_details if p.has_text_layer)
    pages_with_issues = sum(1 for p in page_details if p.suspected_issues)
    
    # Generate recommendation
    if pages_with_text < pages_to_check * 0.5:
        recommendation = "POOR: Most pages lack text layer - need full OCR"
    elif garbage_ratio > 0.1:
        recommendation = "POOR: High garbage ratio - need re-OCR or heavy correction"
    elif avg_valid_ratio < 0.6:
        recommendation = "DEGRADED: Low word validity - may need re-OCR"
    elif pages_with_issues > pages_to_check * 0.3:
        recommendation = "DEGRADED: Many pages have issues - need correction"
    else:
        recommendation = "ACCEPTABLE: Text layer usable, may need minor correction"
    
    return DocumentQuality(
        path=pdf_path,
        total_pages=pages_to_check,
        pages_with_text=pages_with_text,
        pages_with_issues=pages_with_issues,
        overall_garbage_ratio=garbage_ratio,
        overall_valid_word_ratio=avg_valid_ratio,
        error_types=error_types,
        page_details=page_details,
        recommendation=recommendation,
    )


def print_summary(quality: DocumentQuality):
    """Print summary of document quality."""
    print(f"{'='*70}")
    print(f"OCR QUALITY ASSESSMENT: {quality.path}")
    print(f"{'='*70}")
    print()
    
    print(f"Pages analyzed:     {quality.total_pages}")
    print(f"Pages with text:    {quality.pages_with_text} ({quality.pages_with_text/quality.total_pages*100:.0f}%)")
    print(f"Pages with issues:  {quality.pages_with_issues} ({quality.pages_with_issues/quality.total_pages*100:.0f}%)")
    print()
    print(f"Garbage char ratio: {quality.overall_garbage_ratio:.2%}")
    print(f"Valid word ratio:   {quality.overall_valid_word_ratio:.2%}")
    print()
    
    print(f"{'='*70}")
    print(f"RECOMMENDATION: {quality.recommendation}")
    print(f"{'='*70}")
    print()
    
    if quality.error_types:
        print("Issue breakdown:")
        for issue, count in quality.error_types.most_common():
            print(f"  {issue:<25} {count:>4} pages")
        print()


def print_detailed(quality: DocumentQuality):
    """Print detailed per-page analysis."""
    print(f"\n{'='*70}")
    print("PER-PAGE DETAILS")
    print(f"{'='*70}\n")
    
    for pq in quality.page_details[:30]:  # First 30 pages
        status = "✓" if not pq.suspected_issues else "⚠"
        issues_str = ", ".join(pq.suspected_issues) if pq.suspected_issues else "OK"
        print(f"Page {pq.page_num:>3} {status} | chars: {pq.char_count:>5} | "
              f"garbage: {pq.garbage_chars:>3} | valid: {pq.valid_word_ratio:.0%} | {issues_str}")
    
    if len(quality.page_details) > 30:
        print(f"\n... ({len(quality.page_details) - 30} more pages)")


def compare_with_image_ocr(pdf_path: str, sample_pages: int = 3):
    """Compare text layer with fresh OCR from images."""
    try:
        import pytesseract
        from PIL import Image
        import io
    except ImportError:
        print("For image comparison, install: uv add pytesseract pillow")
        print("Also need Tesseract installed on system")
        return
    
    doc = fitz.open(pdf_path)
    
    print(f"\n{'='*70}")
    print("TEXT LAYER vs IMAGE OCR COMPARISON")
    print(f"{'='*70}\n")
    
    for i in range(min(sample_pages, doc.page_count)):
        page = doc[i]
        
        # Get text layer
        text_layer = page.get_text()[:500]
        
        # Get image and OCR it
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        image_ocr = pytesseract.image_to_string(img)[:500]
        
        print(f"--- Page {i} ---")
        print(f"\nTEXT LAYER (first 500 chars):")
        print(text_layer)
        print(f"\nFRESH OCR (first 500 chars):")
        print(image_ocr)
        print()
        
        # Simple similarity
        text_words = set(text_layer.lower().split())
        ocr_words = set(image_ocr.lower().split())
        if text_words or ocr_words:
            overlap = len(text_words & ocr_words) / max(len(text_words | ocr_words), 1)
            print(f"Word overlap: {overlap:.0%}")
        print()
    
    doc.close()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUsage:")
        print("  uv run python spikes/05_ocr_quality_survey.py <pdf_path>")
        print("  uv run python spikes/05_ocr_quality_survey.py <pdf_path> --detailed")
        print("  uv run python spikes/05_ocr_quality_survey.py <pdf_path> --compare-image")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)
    
    args = set(sys.argv[2:])
    
    # Assess document
    quality = assess_document(pdf_path)
    print_summary(quality)
    
    if "--detailed" in args:
        print_detailed(quality)
    
    if "--compare-image" in args:
        compare_with_image_ocr(pdf_path)
    
    # Guidance
    print(f"\n{'='*70}")
    print("IMPLICATIONS FOR SCHOLARDOC")
    print(f"{'='*70}")
    print("""
Based on this document's quality:

IF ACCEPTABLE:
  → Phase 1-3 approach works (use text layer)
  → May still benefit from sequence correction
  
IF DEGRADED:  
  → Need correction pipeline
  → Structure-aware models important
  → Consider hybrid: text layer + spot verification
  
IF POOR:
  → Must extract from images
  → Full custom OCR pipeline needed
  → Phase 4 becomes essential

TO BUILD CONFIDENCE IN THIS ASSESSMENT:
  Run this on 20+ philosophy PDFs from various sources:
  - Internet Archive: archive.org
  - Google Books: books.google.com
  - JSTOR (if accessible)
  - Project Gutenberg
  - HathiTrust
  
  Track results by source to identify which need most help.
""")


if __name__ == "__main__":
    main()
