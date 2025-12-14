#!/usr/bin/env python3
"""
Spike 06: Ground Truth Corpus Building Tools

PURPOSE: Tools for creating and managing ground truth for OCR evaluation.

WORKFLOW:
1. Find parallel texts (scanned PDF + clean digital text)
2. Align them at page/paragraph level
3. Annotate structural elements (page numbers, headings, footnotes)
4. Verify and document quality

RUN:
  # Download a Project Gutenberg text
  uv run python spikes/06_ground_truth.py download-gutenberg 4280 kant_prolegomena.txt
  
  # Compare scanned PDF text to clean text
  uv run python spikes/06_ground_truth.py compare scan.pdf clean.txt
  
  # Create page number ground truth interactively
  uv run python spikes/06_ground_truth.py annotate-pages scan.pdf
  
  # Validate ground truth file
  uv run python spikes/06_ground_truth.py validate ground_truth.yaml

QUESTIONS TO ANSWER:
1. Can we find parallel texts for our target documents?
2. How accurate is automated alignment?
3. How long does manual annotation take per document?
4. What format works best for ground truth storage?
"""

import sys
import re
import json
import yaml
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from difflib import SequenceMatcher
from collections import defaultdict

try:
    import fitz
except ImportError:
    print("Install PyMuPDF: uv add pymupdf")
    sys.exit(1)


# ============================================================================
# Data Models for Ground Truth
# ============================================================================

@dataclass
class PageNumberAnnotation:
    """Ground truth for a single page number."""
    page_index: int
    label: Optional[str]  # None if no page number
    label_type: str = "none"  # arabic, roman_lower, roman_upper, none
    position: str = "unknown"  # header, footer, unknown
    confidence: float = 1.0  # For manual annotation confidence
    notes: str = ""


@dataclass
class HeadingAnnotation:
    """Ground truth for a heading."""
    page_index: int
    level: int  # 1 = chapter, 2 = section, etc.
    text: str
    bbox: Optional[tuple[float, float, float, float]] = None  # Normalized 0-1


@dataclass
class FootnoteAnnotation:
    """Ground truth for a footnote marker and its content."""
    page_index: int
    marker: str
    marker_bbox: Optional[tuple[float, float, float, float]] = None
    content_bbox: Optional[tuple[float, float, float, float]] = None
    content_preview: str = ""


@dataclass 
class TextSample:
    """Ground truth text for a region of a page."""
    page_index: int
    region_bbox: tuple[float, float, float, float]  # Normalized 0-1
    ground_truth_text: str
    ocr_text: Optional[str] = None  # For comparison


@dataclass
class DocumentGroundTruth:
    """Complete ground truth for a document."""
    # Metadata
    title: str
    author: str
    scan_source: str
    clean_source: Optional[str] = None
    edition: str = ""
    translator: str = ""
    
    # Verification
    alignment_method: str = "none"
    verification_status: str = "unverified"
    verified_by: str = ""
    verification_date: str = ""
    
    # Annotations
    page_numbers: list[PageNumberAnnotation] = field(default_factory=list)
    headings: list[HeadingAnnotation] = field(default_factory=list)
    footnotes: list[FootnoteAnnotation] = field(default_factory=list)
    text_samples: list[TextSample] = field(default_factory=list)
    
    # Notes
    notes: str = ""
    known_issues: list[str] = field(default_factory=list)


# ============================================================================
# Gutenberg Download
# ============================================================================

def download_gutenberg(ebook_id: str, output_path: str):
    """Download a Project Gutenberg text."""
    import urllib.request
    
    # Try different URL patterns
    urls = [
        f"https://www.gutenberg.org/cache/epub/{ebook_id}/pg{ebook_id}.txt",
        f"https://www.gutenberg.org/files/{ebook_id}/{ebook_id}-0.txt",
        f"https://www.gutenberg.org/files/{ebook_id}/{ebook_id}.txt",
    ]
    
    for url in urls:
        try:
            print(f"Trying: {url}")
            urllib.request.urlretrieve(url, output_path)
            print(f"Downloaded to: {output_path}")
            
            # Show preview
            with open(output_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
                print(f"\nFile size: {len(text):,} characters")
                print(f"\nFirst 500 characters:\n{text[:500]}")
            return
        except Exception as e:
            print(f"  Failed: {e}")
    
    print(f"\nCould not download ebook {ebook_id}")
    print("Try finding it manually at: https://www.gutenberg.org/")


# ============================================================================
# Text Comparison / Alignment
# ============================================================================

def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    # Lowercase
    text = text.lower()
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove punctuation for fuzzy matching
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()


def extract_pdf_text_by_page(pdf_path: str) -> list[str]:
    """Extract text from each page of a PDF."""
    doc = fitz.open(pdf_path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return pages


def find_best_alignment(pdf_text: str, clean_text: str, window_size: int = 500) -> tuple[int, float]:
    """
    Find where pdf_text best matches within clean_text.
    Returns (start_position, similarity_score).
    """
    pdf_norm = normalize_text(pdf_text)[:window_size]
    clean_norm = normalize_text(clean_text)
    
    best_pos = 0
    best_score = 0
    
    # Slide window through clean text
    step = window_size // 4
    for i in range(0, len(clean_norm) - window_size, step):
        window = clean_norm[i:i + window_size]
        score = SequenceMatcher(None, pdf_norm, window).ratio()
        if score > best_score:
            best_score = score
            best_pos = i
    
    return best_pos, best_score


def compare_texts(pdf_path: str, clean_text_path: str):
    """Compare PDF text layer against clean text."""
    
    print(f"{'='*70}")
    print("TEXT COMPARISON")
    print(f"{'='*70}\n")
    
    # Load texts
    pdf_pages = extract_pdf_text_by_page(pdf_path)
    with open(clean_text_path, 'r', encoding='utf-8', errors='replace') as f:
        clean_text = f.read()
    
    print(f"PDF pages: {len(pdf_pages)}")
    print(f"Clean text length: {len(clean_text):,} characters")
    print()
    
    # Try to align each page
    print("Page-by-page alignment:\n")
    print(f"{'Page':<6} {'Match %':<10} {'Position':<12} {'PDF Preview':<30}")
    print("-" * 70)
    
    alignments = []
    for i, page_text in enumerate(pdf_pages[:20]):  # First 20 pages
        if len(page_text.strip()) < 50:
            print(f"{i:<6} {'(empty)':<10}")
            alignments.append((i, 0, 0))
            continue
            
        pos, score = find_best_alignment(page_text, clean_text)
        preview = normalize_text(page_text)[:25] + "..."
        print(f"{i:<6} {score*100:>6.1f}%    {pos:>10,}   {preview}")
        alignments.append((i, pos, score))
    
    # Analysis
    print()
    print(f"{'='*70}")
    print("ANALYSIS")
    print(f"{'='*70}\n")
    
    good_matches = sum(1 for _, _, s in alignments if s > 0.7)
    poor_matches = sum(1 for _, _, s in alignments if 0 < s < 0.5)
    
    print(f"Pages with good alignment (>70%): {good_matches}")
    print(f"Pages with poor alignment (<50%): {poor_matches}")
    
    if good_matches > len(alignments) * 0.7:
        print("\n✓ Good candidate for parallel text ground truth")
        print("  Recommendation: Proceed with alignment verification")
    elif good_matches > len(alignments) * 0.4:
        print("\n⚠ Moderate alignment - may be different editions")
        print("  Recommendation: Verify edition/translation match")
    else:
        print("\n✗ Poor alignment - likely different texts")
        print("  Recommendation: Find matching edition or different source")


# ============================================================================
# Interactive Page Number Annotation
# ============================================================================

def annotate_pages_interactive(pdf_path: str, output_path: str):
    """Interactively annotate page numbers."""
    
    doc = fitz.open(pdf_path)
    annotations = []
    
    print(f"{'='*70}")
    print("PAGE NUMBER ANNOTATION")
    print(f"{'='*70}")
    print(f"\nDocument: {pdf_path}")
    print(f"Pages: {doc.page_count}")
    print()
    print("For each page, enter the page number/label as it appears.")
    print("Commands:")
    print("  [number]  - Arabic numeral (e.g., '42')")
    print("  r[roman]  - Roman numeral (e.g., 'riv' for 'iv')")
    print("  R[roman]  - Roman uppercase (e.g., 'RIV' for 'IV')")
    print("  -         - No page number")
    print("  s         - Skip (unknown)")
    print("  q         - Quit and save")
    print("  b         - Go back one page")
    print()
    
    i = 0
    while i < doc.page_count:
        page = doc[i]
        
        # Show page info
        text_preview = page.get_text()[:200].replace('\n', ' ')
        detected_label = page.get_label()
        
        print(f"\n--- Page {i} ---")
        print(f"PDF label (if any): {detected_label}")
        print(f"Text preview: {text_preview[:100]}...")
        
        # Get user input
        user_input = input(f"Page number [{detected_label or '-'}]: ").strip()
        
        if user_input == 'q':
            break
        elif user_input == 'b' and i > 0:
            i -= 1
            annotations.pop()
            continue
        elif user_input == 's':
            ann = PageNumberAnnotation(
                page_index=i,
                label=None,
                label_type="unknown",
                confidence=0.0,
            )
        elif user_input == '-' or user_input == '':
            ann = PageNumberAnnotation(
                page_index=i,
                label=None,
                label_type="none",
            )
        elif user_input.startswith('r'):
            ann = PageNumberAnnotation(
                page_index=i,
                label=user_input[1:],
                label_type="roman_lower",
            )
        elif user_input.startswith('R'):
            ann = PageNumberAnnotation(
                page_index=i,
                label=user_input[1:],
                label_type="roman_upper",
            )
        elif user_input.isdigit():
            ann = PageNumberAnnotation(
                page_index=i,
                label=user_input,
                label_type="arabic",
            )
        else:
            print(f"Unknown input: {user_input}")
            continue
        
        annotations.append(ann)
        i += 1
    
    doc.close()
    
    # Save
    gt = DocumentGroundTruth(
        title="Unknown",
        author="Unknown",
        scan_source=pdf_path,
        verification_status="manual_annotation",
        page_numbers=annotations,
    )
    
    save_ground_truth(gt, output_path)
    print(f"\nSaved {len(annotations)} page annotations to: {output_path}")


# ============================================================================
# Ground Truth I/O
# ============================================================================

def save_ground_truth(gt: DocumentGroundTruth, path: str):
    """Save ground truth to YAML file."""
    
    # Convert to dict, handling nested dataclasses
    def to_dict(obj):
        if hasattr(obj, '__dataclass_fields__'):
            return {k: to_dict(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [to_dict(item) for item in obj]
        elif isinstance(obj, tuple):
            return list(obj)
        else:
            return obj
    
    data = to_dict(gt)
    
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def load_ground_truth(path: str) -> DocumentGroundTruth:
    """Load ground truth from YAML file."""
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Reconstruct dataclasses
    page_numbers = [PageNumberAnnotation(**p) for p in data.get('page_numbers', [])]
    headings = [HeadingAnnotation(**h) for h in data.get('headings', [])]
    footnotes = [FootnoteAnnotation(**fn) for fn in data.get('footnotes', [])]
    text_samples = [TextSample(**ts) for ts in data.get('text_samples', [])]
    
    return DocumentGroundTruth(
        title=data.get('title', ''),
        author=data.get('author', ''),
        scan_source=data.get('scan_source', ''),
        clean_source=data.get('clean_source'),
        edition=data.get('edition', ''),
        translator=data.get('translator', ''),
        alignment_method=data.get('alignment_method', 'none'),
        verification_status=data.get('verification_status', 'unverified'),
        verified_by=data.get('verified_by', ''),
        verification_date=data.get('verification_date', ''),
        page_numbers=page_numbers,
        headings=headings,
        footnotes=footnotes,
        text_samples=text_samples,
        notes=data.get('notes', ''),
        known_issues=data.get('known_issues', []),
    )


def validate_ground_truth(path: str):
    """Validate a ground truth file for consistency."""
    
    print(f"{'='*70}")
    print(f"VALIDATING: {path}")
    print(f"{'='*70}\n")
    
    gt = load_ground_truth(path)
    issues = []
    warnings = []
    
    # Check metadata
    if not gt.title:
        warnings.append("Missing title")
    if not gt.author:
        warnings.append("Missing author")
    if not gt.scan_source:
        issues.append("Missing scan_source")
    
    # Check page number sequence
    if gt.page_numbers:
        print(f"Page number annotations: {len(gt.page_numbers)}")
        
        # Check for gaps
        indices = [p.page_index for p in gt.page_numbers]
        for i in range(len(indices) - 1):
            if indices[i + 1] != indices[i] + 1:
                warnings.append(f"Gap in page index: {indices[i]} → {indices[i+1]}")
        
        # Check sequence logic
        prev_arabic = None
        prev_roman = None
        
        for p in gt.page_numbers:
            if p.label_type == "arabic" and p.label:
                try:
                    num = int(p.label)
                    if prev_arabic is not None and num != prev_arabic + 1:
                        if num != 1:  # Reset to 1 is OK
                            warnings.append(f"Page {p.page_index}: Arabic jump {prev_arabic} → {num}")
                    prev_arabic = num
                except ValueError:
                    issues.append(f"Page {p.page_index}: Invalid arabic '{p.label}'")
    
    # Check headings
    if gt.headings:
        print(f"Heading annotations: {len(gt.headings)}")
        
        # Check heading levels are reasonable
        levels = [h.level for h in gt.headings]
        if max(levels) > 5:
            warnings.append(f"Deep heading level: {max(levels)}")
    
    # Check footnotes
    if gt.footnotes:
        print(f"Footnote annotations: {len(gt.footnotes)}")
        
        # Check for duplicate markers on same page
        by_page = defaultdict(list)
        for fn in gt.footnotes:
            by_page[fn.page_index].append(fn.marker)
        
        for page, markers in by_page.items():
            if len(markers) != len(set(markers)):
                issues.append(f"Page {page}: Duplicate footnote markers")
    
    # Check text samples
    if gt.text_samples:
        print(f"Text sample annotations: {len(gt.text_samples)}")
    
    # Report
    print()
    if issues:
        print("ISSUES (should fix):")
        for issue in issues:
            print(f"  ✗ {issue}")
    
    if warnings:
        print("\nWARNINGS (review):")
        for warning in warnings:
            print(f"  ⚠ {warning}")
    
    if not issues and not warnings:
        print("✓ No issues found")
    
    print()
    print(f"Verification status: {gt.verification_status}")
    if gt.verified_by:
        print(f"Verified by: {gt.verified_by} on {gt.verification_date}")


# ============================================================================
# Main
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nCommands:")
        print("  download-gutenberg <ebook_id> <output.txt>")
        print("  compare <scan.pdf> <clean.txt>")
        print("  annotate-pages <scan.pdf> [output.yaml]")
        print("  validate <ground_truth.yaml>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "download-gutenberg":
        if len(sys.argv) < 4:
            print("Usage: download-gutenberg <ebook_id> <output.txt>")
            sys.exit(1)
        download_gutenberg(sys.argv[2], sys.argv[3])
        
    elif command == "compare":
        if len(sys.argv) < 4:
            print("Usage: compare <scan.pdf> <clean.txt>")
            sys.exit(1)
        compare_texts(sys.argv[2], sys.argv[3])
        
    elif command == "annotate-pages":
        if len(sys.argv) < 3:
            print("Usage: annotate-pages <scan.pdf> [output.yaml]")
            sys.exit(1)
        pdf_path = sys.argv[2]
        output_path = sys.argv[3] if len(sys.argv) > 3 else pdf_path.replace('.pdf', '_ground_truth.yaml')
        annotate_pages_interactive(pdf_path, output_path)
        
    elif command == "validate":
        if len(sys.argv) < 3:
            print("Usage: validate <ground_truth.yaml>")
            sys.exit(1)
        validate_ground_truth(sys.argv[2])
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
