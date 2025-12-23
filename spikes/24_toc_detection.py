#!/usr/bin/env python3
"""
Spike 24: ToC Detection and Parsing

PURPOSE: Validate our ToC parsing design by testing on real PDFs.

QUESTIONS TO ANSWER:
1. What % of our test PDFs have parseable ToCs?
2. What ToC formats exist (dotted leaders, explicit page numbers, nested)?
3. Can we reliably parse ToC entries into (title, level, page) tuples?
4. How do we detect ToC pages vs regular content?

RUN:
  uv run python spikes/24_toc_detection.py                    # All PDFs
  uv run python spikes/24_toc_detection.py sample.pdf         # Single PDF
  uv run python spikes/24_toc_detection.py --verbose          # Detailed output
"""

import sys
import re
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Install PyMuPDF: uv add pymupdf")
    sys.exit(1)


@dataclass
class ToCEntry:
    """A parsed table of contents entry."""
    title: str
    page_ref: str  # "5", "xiv", etc.
    level: int  # 1=chapter, 2=section, etc.
    line_text: str  # Original line for debugging
    confidence: float = 1.0


@dataclass
class ToCDetectionResult:
    """Result of ToC detection for a document."""
    pdf_path: str
    has_toc: bool
    toc_pages: list[int] = field(default_factory=list)
    entries: list[ToCEntry] = field(default_factory=list)
    detection_method: str = ""
    format_type: str = ""  # "dotted_leaders", "explicit_numbers", "nested", etc.
    notes: list[str] = field(default_factory=list)


def detect_toc_pages(doc: fitz.Document, max_pages: int = 30) -> list[int]:
    """
    Detect which pages are likely table of contents.

    Indicators:
    - Contains "contents" or "table of contents"
    - Has dotted leaders (........)
    - Has many page number references
    - Low text density with structured layout
    """
    toc_candidates = []

    for page_num in range(min(max_pages, doc.page_count)):
        page = doc[page_num]
        text = page.get_text().lower()

        score = 0.0
        reasons = []

        # Check for "contents" header
        if "table of contents" in text:
            score += 0.5
            reasons.append("has 'table of contents'")
        elif "contents" in text[:500]:  # Near top of page
            score += 0.4
            reasons.append("has 'contents' near top")

        # Check for dotted leaders
        dotted_pattern = r'\.{5,}'  # 5+ dots
        dots_count = len(re.findall(dotted_pattern, text))
        if dots_count >= 3:
            score += 0.3
            reasons.append(f"has {dots_count} dotted leaders")

        # Check for page number patterns at line ends
        # Pattern: word followed by number at end of line
        page_ref_pattern = r'\s+(\d+|[ivxlc]+)\s*$'
        lines = text.split('\n')
        page_refs = sum(1 for line in lines if re.search(page_ref_pattern, line.strip()))
        if page_refs >= 5:
            score += 0.3
            reasons.append(f"has {page_refs} page references")

        # Check for hierarchical numbering
        hierarchy_pattern = r'^\s*(chapter|part|section|\d+\.|\d+\s|[ivx]+\.)'
        hierarchy_lines = sum(1 for line in lines if re.match(hierarchy_pattern, line.lower()))
        if hierarchy_lines >= 3:
            score += 0.2
            reasons.append(f"has {hierarchy_lines} hierarchical markers")

        # Negative indicators
        if len(text) > 5000:  # Too much text for a ToC page
            score -= 0.2
            reasons.append("too much text")

        if score >= 0.5:
            toc_candidates.append((page_num, score, reasons))

    # Return pages above threshold, sorted by score
    toc_candidates.sort(key=lambda x: -x[1])
    return [p[0] for p in toc_candidates if p[1] >= 0.5]


def parse_toc_entries(doc: fitz.Document, toc_pages: list[int]) -> list[ToCEntry]:
    """
    Parse ToC entries from detected ToC pages.

    Handles formats:
    - Dotted leaders: "Chapter 1 .......... 5"
    - Explicit: "Chapter 1                  5"
    - Nested: "  1.1 Introduction        12"
    """
    entries = []

    for page_num in toc_pages:
        page = doc[page_num]
        text = page.get_text()
        lines = text.split('\n')

        for line in lines:
            entry = parse_toc_line(line)
            if entry:
                entries.append(entry)

    return entries


def parse_toc_line(line: str) -> ToCEntry | None:
    """
    Parse a single ToC line into an entry.

    Returns None if line doesn't look like a ToC entry.
    """
    line = line.strip()
    if not line or len(line) < 3:
        return None

    # Skip obvious non-ToC lines
    skip_patterns = [
        r'^(table of )?contents?$',
        r'^page$',
        r'^\d+$',  # Just a number
        r'^[ivxlc]+$',  # Just roman numerals
    ]
    for pattern in skip_patterns:
        if re.match(pattern, line.lower()):
            return None

    # Try different parsing strategies

    # Strategy 1: Dotted leaders
    # "Chapter 1 .......... 5" or "Introduction...........xiv"
    dotted_match = re.match(r'^(.+?)\s*\.{3,}\s*(\d+|[ivxlc]+)\s*$', line, re.IGNORECASE)
    if dotted_match:
        title = dotted_match.group(1).strip()
        page_ref = dotted_match.group(2).strip()
        level = estimate_level(title, line)
        return ToCEntry(title=title, page_ref=page_ref, level=level, line_text=line)

    # Strategy 2: Explicit spacing with number at end
    # "Chapter 1                  5"
    spaced_match = re.match(r'^(.+?)\s{3,}(\d+|[ivxlc]+)\s*$', line, re.IGNORECASE)
    if spaced_match:
        title = spaced_match.group(1).strip()
        page_ref = spaced_match.group(2).strip()
        level = estimate_level(title, line)
        return ToCEntry(title=title, page_ref=page_ref, level=level, line_text=line)

    # Strategy 3: Number at very end after reasonable title
    # "1. Introduction 5" or "Chapter One 12"
    end_num_match = re.match(r'^(.{10,}?)\s+(\d+|[ivxlc]+)\s*$', line, re.IGNORECASE)
    if end_num_match:
        title = end_num_match.group(1).strip()
        page_ref = end_num_match.group(2).strip()
        # Validate: title shouldn't end with common words that precede numbers
        if not re.search(r'(page|pp?\.|see|cf\.)\s*$', title.lower()):
            level = estimate_level(title, line)
            return ToCEntry(title=title, page_ref=page_ref, level=level,
                          line_text=line, confidence=0.7)

    return None


def estimate_level(title: str, full_line: str) -> int:
    """
    Estimate heading level from title content and formatting.
    """
    title_lower = title.lower()

    # Level 1: Major divisions
    if re.match(r'^(part|book)\s+[ivxlc\d]+', title_lower):
        return 0  # Part/Book level
    if re.match(r'^(chapter|section)\s+[ivxlc\d]+', title_lower):
        return 1
    if title.isupper() and len(title) > 5:  # ALL CAPS titles
        return 1

    # Level by indentation
    leading_spaces = len(full_line) - len(full_line.lstrip())
    if leading_spaces >= 8:
        return 3
    if leading_spaces >= 4:
        return 2

    # Level by numbering pattern
    if re.match(r'^\d+\.\d+\.\d+', title):  # 1.2.3
        return 3
    if re.match(r'^\d+\.\d+', title):  # 1.2
        return 2
    if re.match(r'^\d+\.?\s', title):  # 1. or 1
        return 1

    # Default
    return 2


def detect_toc_format(entries: list[ToCEntry], lines: list[str]) -> str:
    """Determine the ToC format type."""
    if not entries:
        return "none"

    # Check for dotted leaders
    dotted_count = sum(1 for e in entries if '...' in e.line_text)
    if dotted_count > len(entries) * 0.5:
        return "dotted_leaders"

    # Check for hierarchical numbering
    numbered_count = sum(1 for e in entries if re.match(r'^\d+\.', e.title))
    if numbered_count > len(entries) * 0.5:
        return "numbered_hierarchy"

    # Check for indentation-based hierarchy
    indented_count = sum(1 for e in entries if e.level > 1)
    if indented_count > len(entries) * 0.3:
        return "indented_hierarchy"

    return "simple_list"


def analyze_pdf(pdf_path: Path, verbose: bool = False) -> ToCDetectionResult:
    """
    Analyze a PDF for ToC content.
    """
    result = ToCDetectionResult(pdf_path=str(pdf_path), has_toc=False)

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        result.notes.append(f"Failed to open: {e}")
        return result

    try:
        # Step 1: Detect ToC pages
        toc_pages = detect_toc_pages(doc)
        result.toc_pages = toc_pages

        if not toc_pages:
            result.notes.append("No ToC pages detected")
            result.detection_method = "page_scan"
            doc.close()
            return result

        result.has_toc = True
        result.detection_method = "page_scan"
        result.notes.append(f"ToC detected on pages: {toc_pages}")

        # Step 2: Parse ToC entries
        entries = parse_toc_entries(doc, toc_pages)
        result.entries = entries

        if entries:
            # Step 3: Determine format type
            all_lines = []
            for page_num in toc_pages:
                all_lines.extend(doc[page_num].get_text().split('\n'))
            result.format_type = detect_toc_format(entries, all_lines)
            result.notes.append(f"Format: {result.format_type}")
            result.notes.append(f"Parsed {len(entries)} entries")
        else:
            result.notes.append("ToC pages found but no entries parsed")

        doc.close()
        return result

    except Exception as e:
        result.notes.append(f"Error during analysis: {e}")
        doc.close()
        return result


def print_result(result: ToCDetectionResult, verbose: bool = False):
    """Print analysis result."""
    name = Path(result.pdf_path).name

    if result.has_toc:
        print(f"\n{'='*60}")
        print(f"✅ {name}")
        print(f"{'='*60}")
        print(f"ToC Pages: {result.toc_pages}")
        print(f"Format: {result.format_type}")
        print(f"Entries: {len(result.entries)}")

        if verbose and result.entries:
            print(f"\n--- Parsed Entries ---")
            for i, entry in enumerate(result.entries[:20]):  # First 20
                indent = "  " * entry.level
                conf = f" ({entry.confidence:.0%})" if entry.confidence < 1 else ""
                print(f"{indent}L{entry.level}: {entry.title[:50]} → p.{entry.page_ref}{conf}")
            if len(result.entries) > 20:
                print(f"  ... and {len(result.entries) - 20} more")

        for note in result.notes:
            print(f"  Note: {note}")
    else:
        print(f"\n❌ {name}: No ToC detected")
        for note in result.notes:
            print(f"  Note: {note}")


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

    print(f"Analyzing {len(pdf_paths)} PDFs for ToC content...")

    results = []
    for pdf_path in pdf_paths:
        result = analyze_pdf(pdf_path, verbose)
        results.append(result)
        print_result(result, verbose)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    with_toc = [r for r in results if r.has_toc]
    without_toc = [r for r in results if not r.has_toc]

    print(f"Total PDFs analyzed: {len(results)}")
    print(f"With ToC: {len(with_toc)} ({100*len(with_toc)/len(results):.0f}%)")
    print(f"Without ToC: {len(without_toc)} ({100*len(without_toc)/len(results):.0f}%)")

    if with_toc:
        total_entries = sum(len(r.entries) for r in with_toc)
        avg_entries = total_entries / len(with_toc)
        print(f"Total entries parsed: {total_entries}")
        print(f"Average entries per ToC: {avg_entries:.1f}")

        # Format breakdown
        formats = defaultdict(int)
        for r in with_toc:
            formats[r.format_type] += 1
        print(f"\nFormat types:")
        for fmt, count in sorted(formats.items(), key=lambda x: -x[1]):
            print(f"  {fmt}: {count}")

    # Recommendations
    print(f"\n--- RECOMMENDATIONS ---")
    if len(with_toc) / len(results) < 0.5:
        print("⚠️  Less than 50% of PDFs have detectable ToCs")
        print("   Consider: ToC parsing may not be universally useful")
    else:
        print("✅ Majority of PDFs have detectable ToCs")

    avg_parsed = sum(len(r.entries) for r in with_toc) / max(len(with_toc), 1)
    if avg_parsed < 5:
        print("⚠️  Low average entries parsed - parser may need improvement")
    else:
        print(f"✅ Parser extracting good number of entries (avg {avg_parsed:.1f})")


if __name__ == "__main__":
    main()
