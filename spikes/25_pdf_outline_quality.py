#!/usr/bin/env python3
"""
Spike 25: PDF Outline/Bookmark Quality Evaluation

PURPOSE: Evaluate how useful PDF outlines are for structure extraction.

QUESTIONS TO ANSWER:
1. What % of PDFs have outlines vs don't?
2. How accurate are outline titles vs visual headings?
3. Do outlines include all sections or just chapters?
4. Can we rely on outlines as a high-confidence source?

RUN:
  uv run python spikes/25_pdf_outline_quality.py                    # All PDFs
  uv run python spikes/25_pdf_outline_quality.py sample.pdf         # Single PDF
  uv run python spikes/25_pdf_outline_quality.py --verbose          # Show all entries
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
class OutlineEntry:
    """A single PDF outline/bookmark entry."""
    level: int  # 1-based level (1 = top level)
    title: str
    page_num: int  # 0-based page index
    page_label: str  # Display label if available
    children_count: int = 0


@dataclass
class OutlineAnalysis:
    """Analysis result for a PDF's outline."""
    pdf_path: str
    has_outline: bool
    entry_count: int = 0
    max_depth: int = 0
    entries: list[OutlineEntry] = field(default_factory=list)
    # Quality metrics
    coverage: float = 0.0  # % of pages that have an outline entry pointing to them
    depth_distribution: dict = field(default_factory=dict)  # level -> count
    notes: list[str] = field(default_factory=list)


def extract_outline(doc: fitz.Document) -> list[OutlineEntry]:
    """
    Extract outline/bookmarks from PDF.

    PyMuPDF's get_toc() returns: [[level, title, page, dest], ...]
    """
    toc = doc.get_toc()
    if not toc:
        return []

    entries = []
    for item in toc:
        level = item[0]
        title = item[1] if len(item) > 1 else ""
        page_num = item[2] - 1 if len(item) > 2 else 0  # Convert to 0-based

        # Get page label if available
        page_label = ""
        if 0 <= page_num < doc.page_count:
            page_label = doc[page_num].get_label() or str(page_num + 1)

        entries.append(OutlineEntry(
            level=level,
            title=title,
            page_num=page_num,
            page_label=page_label
        ))

    return entries


def analyze_outline_quality(doc: fitz.Document, entries: list[OutlineEntry]) -> dict:
    """
    Analyze the quality and coverage of the outline.
    """
    if not entries:
        return {"coverage": 0, "max_depth": 0, "depth_dist": {}}

    # Coverage: what % of pages have at least one outline entry?
    pages_with_entries = set(e.page_num for e in entries)
    coverage = len(pages_with_entries) / max(doc.page_count, 1)

    # Depth distribution
    depth_dist = defaultdict(int)
    for e in entries:
        depth_dist[e.level] += 1

    max_depth = max(e.level for e in entries)

    return {
        "coverage": coverage,
        "max_depth": max_depth,
        "depth_dist": dict(depth_dist),
        "pages_covered": len(pages_with_entries),
        "total_pages": doc.page_count
    }


def compare_outline_to_headings(doc: fitz.Document, entries: list[OutlineEntry],
                                 sample_pages: int = 5) -> list[dict]:
    """
    Compare outline entries to actual heading text on pages.

    Returns list of comparisons for validation.
    """
    comparisons = []

    for entry in entries[:sample_pages * 2]:  # Check first few entries
        if entry.page_num < 0 or entry.page_num >= doc.page_count:
            continue

        page = doc[entry.page_num]
        page_text = page.get_text()
        lines = [l.strip() for l in page_text.split('\n') if l.strip()]

        # Look for the outline title in the page text
        title_clean = entry.title.strip().lower()
        found = False
        matched_line = ""

        for line in lines[:20]:  # Check first 20 lines
            line_clean = line.lower()
            # Exact match
            if title_clean == line_clean:
                found = True
                matched_line = line
                break
            # Substring match (outline might be truncated)
            if len(title_clean) > 10 and title_clean in line_clean:
                found = True
                matched_line = line
                break
            # Line contains most of title words
            title_words = set(title_clean.split())
            line_words = set(line_clean.split())
            if len(title_words) > 2 and len(title_words & line_words) >= len(title_words) * 0.8:
                found = True
                matched_line = line
                break

        comparisons.append({
            "outline_title": entry.title,
            "page": entry.page_num,
            "found_in_text": found,
            "matched_line": matched_line[:60] if matched_line else "",
            "first_line": lines[0][:60] if lines else ""
        })

    return comparisons


def analyze_pdf(pdf_path: Path, verbose: bool = False) -> OutlineAnalysis:
    """
    Analyze a PDF's outline/bookmark structure.
    """
    result = OutlineAnalysis(pdf_path=str(pdf_path), has_outline=False)

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        result.notes.append(f"Failed to open: {e}")
        return result

    try:
        # Extract outline
        entries = extract_outline(doc)
        result.entries = entries
        result.has_outline = len(entries) > 0
        result.entry_count = len(entries)

        if not entries:
            result.notes.append("No PDF outline/bookmarks found")
            doc.close()
            return result

        # Analyze quality
        quality = analyze_outline_quality(doc, entries)
        result.coverage = quality["coverage"]
        result.max_depth = quality["max_depth"]
        result.depth_distribution = quality["depth_dist"]
        result.notes.append(f"Coverage: {quality['pages_covered']}/{quality['total_pages']} pages ({quality['coverage']:.1%})")
        result.notes.append(f"Max depth: {quality['max_depth']}")

        # Compare to actual headings
        comparisons = compare_outline_to_headings(doc, entries)
        matches = sum(1 for c in comparisons if c["found_in_text"])
        if comparisons:
            match_rate = matches / len(comparisons)
            result.notes.append(f"Title match rate: {matches}/{len(comparisons)} ({match_rate:.0%})")

        doc.close()
        return result

    except Exception as e:
        result.notes.append(f"Error during analysis: {e}")
        doc.close()
        return result


def print_result(result: OutlineAnalysis, verbose: bool = False):
    """Print analysis result."""
    name = Path(result.pdf_path).name

    if result.has_outline:
        print(f"\n{'='*60}")
        print(f"✅ {name}")
        print(f"{'='*60}")
        print(f"Entries: {result.entry_count}")
        print(f"Max depth: {result.max_depth}")
        print(f"Coverage: {result.coverage:.1%}")

        if result.depth_distribution:
            print(f"Depth distribution:")
            for level in sorted(result.depth_distribution.keys()):
                count = result.depth_distribution[level]
                print(f"  Level {level}: {count} entries")

        if verbose and result.entries:
            print(f"\n--- Outline Entries ---")
            for entry in result.entries[:30]:  # First 30
                indent = "  " * (entry.level - 1)
                page_info = f"p.{entry.page_label}" if entry.page_label else f"idx {entry.page_num}"
                print(f"{indent}[{entry.level}] {entry.title[:45]} → {page_info}")
            if len(result.entries) > 30:
                print(f"  ... and {len(result.entries) - 30} more")

        for note in result.notes:
            print(f"  Note: {note}")
    else:
        print(f"\n❌ {name}: No outline found")
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

    print(f"Analyzing {len(pdf_paths)} PDFs for outline quality...")

    results = []
    for pdf_path in pdf_paths:
        result = analyze_pdf(pdf_path, verbose)
        results.append(result)
        print_result(result, verbose)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    with_outline = [r for r in results if r.has_outline]
    without_outline = [r for r in results if not r.has_outline]

    print(f"Total PDFs analyzed: {len(results)}")
    print(f"With outline: {len(with_outline)} ({100*len(with_outline)/len(results):.0f}%)")
    print(f"Without outline: {len(without_outline)} ({100*len(without_outline)/len(results):.0f}%)")

    if with_outline:
        avg_entries = sum(r.entry_count for r in with_outline) / len(with_outline)
        avg_coverage = sum(r.coverage for r in with_outline) / len(with_outline)
        avg_depth = sum(r.max_depth for r in with_outline) / len(with_outline)

        print(f"\nFor PDFs with outlines:")
        print(f"  Average entries: {avg_entries:.1f}")
        print(f"  Average coverage: {avg_coverage:.1%}")
        print(f"  Average max depth: {avg_depth:.1f}")

        # Depth breakdown
        all_depths = defaultdict(int)
        for r in with_outline:
            for level, count in r.depth_distribution.items():
                all_depths[level] += count

        print(f"\n  Aggregate depth distribution:")
        for level in sorted(all_depths.keys()):
            print(f"    Level {level}: {all_depths[level]} entries")

    # Recommendations
    print(f"\n--- RECOMMENDATIONS ---")
    outline_rate = len(with_outline) / len(results) if results else 0

    if outline_rate < 0.3:
        print("⚠️  Less than 30% of PDFs have outlines")
        print("   PDF outlines should NOT be relied upon as primary source")
    elif outline_rate < 0.6:
        print("⚠️  Only {:.0%} of PDFs have outlines".format(outline_rate))
        print("   PDF outlines useful when present but need fallback")
    else:
        print("✅ {:.0%} of PDFs have outlines - good primary source".format(outline_rate))

    if with_outline:
        avg_cov = sum(r.coverage for r in with_outline) / len(with_outline)
        if avg_cov < 0.05:
            print("⚠️  Very low page coverage ({:.1%}) - outlines only mark major sections".format(avg_cov))
        else:
            print("✅ Reasonable page coverage ({:.1%})".format(avg_cov))


if __name__ == "__main__":
    main()
