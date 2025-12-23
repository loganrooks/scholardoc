#!/usr/bin/env python3
"""
Spike 26: Multi-Source Structure Fusion Testing

PURPOSE: Test whether combining multiple structure sources improves accuracy.

QUESTIONS TO ANSWER:
1. How often do sources agree on section boundaries?
2. Which source is most reliable when they disagree?
3. Does combining sources improve accuracy over best single source?
4. What fusion strategy works best?

RUN:
  uv run python spikes/26_structure_fusion.py                    # All PDFs
  uv run python spikes/26_structure_fusion.py sample.pdf         # Single PDF
  uv run python spikes/26_structure_fusion.py --verbose          # Detailed output
"""

import sys
import re
import statistics
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Literal

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Install PyMuPDF: uv add pymupdf")
    sys.exit(1)


@dataclass
class SectionCandidate:
    """A proposed section from any source."""
    page_num: int  # Page where section starts
    title: str
    level: int
    confidence: float
    source: str  # "outline", "toc", "heading"


@dataclass
class FusionResult:
    """Result of structure fusion for a document."""
    pdf_path: str

    # Per-source results
    outline_candidates: list[SectionCandidate] = field(default_factory=list)
    toc_candidates: list[SectionCandidate] = field(default_factory=list)
    heading_candidates: list[SectionCandidate] = field(default_factory=list)

    # Agreement metrics
    all_sources_agree: int = 0
    two_sources_agree: int = 0
    single_source_only: int = 0

    # Which sources are available
    has_outline: bool = False
    has_toc: bool = False
    has_headings: bool = False

    notes: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# Source 1: PDF Outline
# ─────────────────────────────────────────────────────────────

def extract_from_outline(doc: fitz.Document) -> list[SectionCandidate]:
    """Extract section candidates from PDF outline/bookmarks."""
    toc = doc.get_toc()
    if not toc:
        return []

    candidates = []
    for item in toc:
        level = item[0]
        title = item[1] if len(item) > 1 else ""
        page_num = item[2] - 1 if len(item) > 2 else 0

        if 0 <= page_num < doc.page_count:
            candidates.append(SectionCandidate(
                page_num=page_num,
                title=title.strip(),
                level=level,
                confidence=0.95,  # Outlines are highly reliable
                source="outline"
            ))

    return candidates


# ─────────────────────────────────────────────────────────────
# Source 2: ToC Parser (simplified from spike 24)
# ─────────────────────────────────────────────────────────────

def extract_from_toc(doc: fitz.Document) -> list[SectionCandidate]:
    """Extract section candidates from detected table of contents."""
    candidates = []

    # Scan first 30 pages for ToC
    for page_num in range(min(30, doc.page_count)):
        page = doc[page_num]
        text = page.get_text().lower()

        # Quick ToC detection
        if "contents" not in text and "table of" not in text:
            continue

        # Found potential ToC page - parse it
        lines = page.get_text().split('\n')

        for line in lines:
            # Look for "Title ... page_number" or "Title    page_number" patterns
            match = re.match(r'^(.+?)\s*\.{3,}\s*(\d+|[ivxlc]+)\s*$', line, re.IGNORECASE)
            if not match:
                match = re.match(r'^(.{10,}?)\s{3,}(\d+|[ivxlc]+)\s*$', line, re.IGNORECASE)

            if match:
                title = match.group(1).strip()
                page_ref = match.group(2).strip()

                # Try to resolve page reference
                target_page = resolve_page_ref(doc, page_ref)

                if target_page is not None:
                    # Estimate level from indentation/numbering
                    level = estimate_level_from_title(title, line)

                    candidates.append(SectionCandidate(
                        page_num=target_page,
                        title=title,
                        level=level,
                        confidence=0.85,
                        source="toc"
                    ))

    return candidates


def resolve_page_ref(doc: fitz.Document, page_ref: str) -> int | None:
    """Resolve a page reference (number or roman numeral) to page index."""
    # Try as Arabic number first
    try:
        num = int(page_ref)
        # Check if any page has this label
        for i in range(doc.page_count):
            if doc[i].get_label() == str(num):
                return i
        # Fallback: assume 1-based index
        if 1 <= num <= doc.page_count:
            return num - 1
    except ValueError:
        pass

    # Try as Roman numeral
    roman_map = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6,
                 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10, 'xi': 11, 'xii': 12,
                 'xiii': 13, 'xiv': 14, 'xv': 15}
    roman_lower = page_ref.lower()
    if roman_lower in roman_map:
        # Front matter pages - try to find matching label
        for i in range(min(50, doc.page_count)):
            label = doc[i].get_label()
            if label and label.lower() == roman_lower:
                return i

    return None


def estimate_level_from_title(title: str, line: str) -> int:
    """Estimate heading level from title content."""
    title_lower = title.lower()

    if re.match(r'^(part|book)\s+[ivxlc\d]+', title_lower):
        return 0
    if re.match(r'^(chapter|section)\s+[ivxlc\d]+', title_lower):
        return 1
    if title.isupper() and len(title) > 5:
        return 1

    leading_spaces = len(line) - len(line.lstrip())
    if leading_spaces >= 6:
        return 3
    if leading_spaces >= 3:
        return 2

    if re.match(r'^\d+\.\d+', title):
        return 2

    return 1


# ─────────────────────────────────────────────────────────────
# Source 3: Heading Detection (simplified from spike 03)
# ─────────────────────────────────────────────────────────────

def extract_from_headings(doc: fitz.Document, sample_pages: int = 50) -> list[SectionCandidate]:
    """
    Extract section candidates from visual heading detection.

    Uses font size analysis to find headings.
    """
    # First pass: collect font size statistics
    font_sizes = []
    for page_num in range(min(sample_pages, doc.page_count)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block.get("type") != 0:  # Text blocks only
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    size = span.get("size", 0)
                    if size > 0:
                        font_sizes.append(size)

    if not font_sizes:
        return []

    # Calculate body text size (most common)
    size_counts = defaultdict(int)
    for size in font_sizes:
        size_counts[round(size, 1)] += 1

    body_size = max(size_counts.keys(), key=lambda s: size_counts[s])
    median_size = statistics.median(font_sizes)

    # Second pass: find headings (text larger than body)
    candidates = []
    heading_threshold = body_size * 1.15  # 15% larger than body

    for page_num in range(min(sample_pages, doc.page_count)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block.get("type") != 0:
                continue

            # Get block text and max font size
            block_text = ""
            max_size = 0
            is_bold = False

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    block_text += span.get("text", "")
                    size = span.get("size", 0)
                    if size > max_size:
                        max_size = size
                    # Check bold flag (bit 4 in PyMuPDF)
                    if span.get("flags", 0) & 16:
                        is_bold = True

            block_text = block_text.strip()

            # Skip empty or very long text (not a heading)
            if not block_text or len(block_text) > 200:
                continue

            # Score as potential heading
            score = 0.0

            if max_size >= heading_threshold:
                score += 0.4 + min(0.3, (max_size - heading_threshold) / 5)

            if is_bold:
                score += 0.25

            # Short text is more likely a heading
            if len(block_text) < 80:
                score += 0.15

            # ALL CAPS or Title Case
            if block_text.isupper():
                score += 0.15
            elif block_text.istitle() and len(block_text.split()) <= 6:
                score += 0.1

            if score >= 0.5:
                # Estimate level from font size
                size_ratio = max_size / body_size
                if size_ratio >= 1.6:
                    level = 1
                elif size_ratio >= 1.3:
                    level = 2
                else:
                    level = 3

                candidates.append(SectionCandidate(
                    page_num=page_num,
                    title=block_text[:100],  # Truncate long titles
                    level=level,
                    confidence=min(0.9, score),
                    source="heading"
                ))

    # Deduplicate (same page, similar title)
    deduped = []
    seen = set()
    for c in candidates:
        key = (c.page_num, c.title[:30].lower())
        if key not in seen:
            seen.add(key)
            deduped.append(c)

    return deduped


# ─────────────────────────────────────────────────────────────
# Fusion Analysis
# ─────────────────────────────────────────────────────────────

def find_agreements(outline: list[SectionCandidate],
                   toc: list[SectionCandidate],
                   heading: list[SectionCandidate],
                   page_tolerance: int = 1) -> dict:
    """
    Find where sources agree and disagree.
    """
    # Build page -> candidates mapping
    outline_pages = {c.page_num: c for c in outline}
    toc_pages = {c.page_num: c for c in toc}
    heading_pages = {c.page_num: c for c in heading}

    all_pages = set(outline_pages.keys()) | set(toc_pages.keys()) | set(heading_pages.keys())

    agreements = {
        "all_three": [],
        "outline_and_toc": [],
        "outline_and_heading": [],
        "toc_and_heading": [],
        "outline_only": [],
        "toc_only": [],
        "heading_only": [],
    }

    for page in sorted(all_pages):
        has_outline = page in outline_pages
        has_toc = page in toc_pages
        has_heading = page in heading_pages

        # Check nearby pages for tolerance
        for delta in range(-page_tolerance, page_tolerance + 1):
            if delta == 0:
                continue
            if page + delta in outline_pages:
                has_outline = True
            if page + delta in toc_pages:
                has_toc = True
            if page + delta in heading_pages:
                has_heading = True

        if has_outline and has_toc and has_heading:
            agreements["all_three"].append(page)
        elif has_outline and has_toc:
            agreements["outline_and_toc"].append(page)
        elif has_outline and has_heading:
            agreements["outline_and_heading"].append(page)
        elif has_toc and has_heading:
            agreements["toc_and_heading"].append(page)
        elif has_outline:
            agreements["outline_only"].append(page)
        elif has_toc:
            agreements["toc_only"].append(page)
        elif has_heading:
            agreements["heading_only"].append(page)

    return agreements


def analyze_pdf(pdf_path: Path, verbose: bool = False) -> FusionResult:
    """
    Analyze a PDF using all three structure sources.
    """
    result = FusionResult(pdf_path=str(pdf_path))

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        result.notes.append(f"Failed to open: {e}")
        return result

    try:
        # Extract from all sources
        result.outline_candidates = extract_from_outline(doc)
        result.toc_candidates = extract_from_toc(doc)
        result.heading_candidates = extract_from_headings(doc)

        result.has_outline = len(result.outline_candidates) > 0
        result.has_toc = len(result.toc_candidates) > 0
        result.has_headings = len(result.heading_candidates) > 0

        # Analyze agreements
        agreements = find_agreements(
            result.outline_candidates,
            result.toc_candidates,
            result.heading_candidates
        )

        result.all_sources_agree = len(agreements["all_three"])
        result.two_sources_agree = (len(agreements["outline_and_toc"]) +
                                    len(agreements["outline_and_heading"]) +
                                    len(agreements["toc_and_heading"]))
        result.single_source_only = (len(agreements["outline_only"]) +
                                     len(agreements["toc_only"]) +
                                     len(agreements["heading_only"]))

        # Summary notes
        result.notes.append(f"Outline: {len(result.outline_candidates)} candidates")
        result.notes.append(f"ToC: {len(result.toc_candidates)} candidates")
        result.notes.append(f"Heading: {len(result.heading_candidates)} candidates")

        total = result.all_sources_agree + result.two_sources_agree + result.single_source_only
        if total > 0:
            result.notes.append(f"All 3 agree: {result.all_sources_agree} ({100*result.all_sources_agree/total:.0f}%)")
            result.notes.append(f"2 agree: {result.two_sources_agree} ({100*result.two_sources_agree/total:.0f}%)")
            result.notes.append(f"1 only: {result.single_source_only} ({100*result.single_source_only/total:.0f}%)")

        doc.close()
        return result

    except Exception as e:
        result.notes.append(f"Error during analysis: {e}")
        doc.close()
        return result


def print_result(result: FusionResult, verbose: bool = False):
    """Print analysis result."""
    name = Path(result.pdf_path).name

    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"{'='*60}")

    sources = []
    if result.has_outline:
        sources.append(f"Outline ({len(result.outline_candidates)})")
    if result.has_toc:
        sources.append(f"ToC ({len(result.toc_candidates)})")
    if result.has_headings:
        sources.append(f"Heading ({len(result.heading_candidates)})")

    if sources:
        print(f"Sources available: {', '.join(sources)}")
    else:
        print("No sources available")

    total = result.all_sources_agree + result.two_sources_agree + result.single_source_only
    if total > 0:
        print(f"\nAgreement analysis:")
        print(f"  All 3 agree:    {result.all_sources_agree:3d} ({100*result.all_sources_agree/total:.0f}%)")
        print(f"  2 sources agree: {result.two_sources_agree:3d} ({100*result.two_sources_agree/total:.0f}%)")
        print(f"  Single source:  {result.single_source_only:3d} ({100*result.single_source_only/total:.0f}%)")

    if verbose:
        print(f"\n--- Outline Candidates (sample) ---")
        for c in result.outline_candidates[:10]:
            print(f"  p.{c.page_num}: L{c.level} {c.title[:40]}")

        print(f"\n--- ToC Candidates (sample) ---")
        for c in result.toc_candidates[:10]:
            print(f"  p.{c.page_num}: L{c.level} {c.title[:40]}")

        print(f"\n--- Heading Candidates (sample) ---")
        for c in result.heading_candidates[:10]:
            print(f"  p.{c.page_num}: L{c.level} [{c.confidence:.0%}] {c.title[:40]}")


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

    print(f"Analyzing {len(pdf_paths)} PDFs for structure fusion...")

    results = []
    for pdf_path in pdf_paths:
        result = analyze_pdf(pdf_path, verbose)
        results.append(result)
        print_result(result, verbose)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    # Source availability
    with_outline = sum(1 for r in results if r.has_outline)
    with_toc = sum(1 for r in results if r.has_toc)
    with_heading = sum(1 for r in results if r.has_headings)

    print(f"\nSource availability:")
    print(f"  Outline: {with_outline}/{len(results)} ({100*with_outline/len(results):.0f}%)")
    print(f"  ToC: {with_toc}/{len(results)} ({100*with_toc/len(results):.0f}%)")
    print(f"  Heading: {with_heading}/{len(results)} ({100*with_heading/len(results):.0f}%)")

    # Agreement stats
    total_all = sum(r.all_sources_agree for r in results)
    total_two = sum(r.two_sources_agree for r in results)
    total_one = sum(r.single_source_only for r in results)
    total = total_all + total_two + total_one

    if total > 0:
        print(f"\nAggregate agreement:")
        print(f"  All 3 agree:    {total_all:3d} ({100*total_all/total:.0f}%)")
        print(f"  2 sources agree: {total_two:3d} ({100*total_two/total:.0f}%)")
        print(f"  Single source:  {total_one:3d} ({100*total_one/total:.0f}%)")

    # Recommendations
    print(f"\n--- RECOMMENDATIONS ---")

    agreement_rate = (total_all + total_two) / max(total, 1)
    if agreement_rate >= 0.7:
        print(f"✅ {agreement_rate:.0%} agreement rate - fusion provides validation")
    elif agreement_rate >= 0.4:
        print(f"⚠️  {agreement_rate:.0%} agreement rate - fusion helps but sources often disagree")
    else:
        print(f"⚠️  {agreement_rate:.0%} agreement rate - sources rarely agree, fusion may add noise")

    if with_outline / len(results) >= 0.6:
        print("✅ Outline available in majority - can use as primary source")
    else:
        print("⚠️  Outline not always available - need heading detection fallback")

    if with_heading / len(results) >= 0.9:
        print("✅ Heading detection works reliably - good universal fallback")


if __name__ == "__main__":
    main()
