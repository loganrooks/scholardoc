#!/usr/bin/env python3
"""
Spike 31: Candidate Page Finder for Ground Truth Labeling

PURPOSE: Programmatically identify promising pages for ground truth annotation.
         Reduces manual exploration by finding pages with specific features.

FEATURES DETECTED:
1. Footnotes (page-bottom small text with markers)
2. Citations (author-year, numeric references, Ak. references)
3. Tables (grid-like structures)
4. Negative examples (pages with body text but no features)

OUTPUT: JSON report with candidate pages grouped by feature type.

RUN:
  uv run python spikes/31_candidate_page_finder.py spikes/sample_pdfs/*.pdf
  uv run python spikes/31_candidate_page_finder.py sample.pdf --output candidates.json
  uv run python spikes/31_candidate_page_finder.py sample.pdf --features footnotes,citations
"""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    import fitz
except ImportError:
    print("Install PyMuPDF: uv add pymupdf")
    sys.exit(1)


@dataclass
class PageCandidate:
    """A page identified as having a specific feature."""

    page_index: int
    page_label: str
    feature_type: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    markers_found: list[str] = field(default_factory=list)


@dataclass
class DocumentReport:
    """Summary of candidates found in a document."""

    pdf_path: str
    total_pages: int
    body_font_size: float
    footnote_candidates: list[PageCandidate] = field(default_factory=list)
    citation_candidates: list[PageCandidate] = field(default_factory=list)
    table_candidates: list[PageCandidate] = field(default_factory=list)
    negative_candidates: list[PageCandidate] = field(default_factory=list)
    endnote_section: dict | None = None
    bibliography_section: dict | None = None


# Citation patterns
CITATION_PATTERNS = {
    "author_year": re.compile(r"\([A-Z][a-z]+(?:\s+(?:and|&)\s+[A-Z][a-z]+)?,?\s*\d{4}[a-z]?\)"),
    "numeric_bracket": re.compile(r"\[\d+(?:[-,]\d+)*\]"),
    "ak_reference": re.compile(r"Ak\.\s*\d+"),
    "page_reference": re.compile(r"(?:pp?\.|pages?)\s*\d+(?:[-–]\d+)?"),
    "cf_reference": re.compile(r"(?:cf\.|see|compare)\s+(?:pp?\.)?\s*\d+", re.IGNORECASE),
}

# Footnote marker patterns
SYMBOLIC_MARKERS = set("*†‡§¶‖#")
FOOTNOTE_START_PATTERN = re.compile(r"^[\d*†‡§¶a-z][\.\)\s]")


def get_body_font_size(doc: fitz.Document, sample_pages: int = 30) -> float:
    """Determine the most common (body) font size from first N pages."""
    from collections import Counter

    size_counts = Counter()

    for page_num in range(min(sample_pages, doc.page_count)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block["type"] != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    size = round(span["size"], 1)
                    text_len = len(span["text"].strip())
                    if text_len > 5:  # Only count substantial text
                        size_counts[size] += text_len

    return size_counts.most_common(1)[0][0] if size_counts else 10.0


def detect_footnotes(page: fitz.Page, body_size: float) -> PageCandidate | None:
    """Detect if page has footnotes in bottom region."""
    page_height = page.rect.height
    page_label = page.get_label() or str(page.number + 1)

    blocks = page.get_text("dict")["blocks"]

    evidence = []
    markers_found = []
    confidence = 0.0

    has_small_text_bottom = False
    has_footnote_markers = False
    has_body_markers = False

    for block in blocks:
        if block["type"] != 0:
            continue

        block_top = block["bbox"][1]

        # Check bottom region (bottom 20%)
        if block_top > page_height * 0.80:
            for line in block.get("lines", []):
                line_text = ""
                sizes = []
                for span in line.get("spans", []):
                    line_text += span["text"]
                    sizes.append(span["size"])

                avg_size = sum(sizes) / len(sizes) if sizes else body_size
                line_text = line_text.strip()

                # Small text in bottom region
                if avg_size < body_size * 0.9 and len(line_text) > 10:
                    has_small_text_bottom = True

                    # Check for footnote marker at start
                    if FOOTNOTE_START_PATTERN.match(line_text):
                        has_footnote_markers = True
                        marker = line_text[0]
                        if marker not in markers_found:
                            markers_found.append(marker)
                        evidence.append(f"Footnote line: {line_text[:60]}...")

                    # Check for symbolic markers
                    if line_text and line_text[0] in SYMBOLIC_MARKERS:
                        has_footnote_markers = True
                        if line_text[0] not in markers_found:
                            markers_found.append(line_text[0])

        # Check body for superscript markers
        else:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    flags = span["flags"]
                    text = span["text"].strip()
                    size = span["size"]

                    # Superscript flag or very small isolated text
                    if flags & 1 or (size < 8 and len(text) <= 3):
                        if (
                            text.isdigit()
                            or text in SYMBOLIC_MARKERS
                            or (len(text) == 1 and text.isalpha())
                        ):
                            has_body_markers = True
                            if text not in markers_found and len(markers_found) < 10:
                                markers_found.append(text)

    # Calculate confidence
    if has_small_text_bottom:
        confidence += 0.3
        evidence.append("Has small text in bottom region")
    if has_footnote_markers:
        confidence += 0.4
        evidence.append("Has footnote markers at line starts")
    if has_body_markers:
        confidence += 0.2
        evidence.append("Has superscript markers in body")

    if confidence >= 0.3:
        return PageCandidate(
            page_index=page.number,
            page_label=page_label,
            feature_type="footnote",
            confidence=confidence,
            evidence=evidence,
            markers_found=markers_found,
        )
    return None


def detect_citations(page: fitz.Page) -> PageCandidate | None:
    """Detect if page has in-text citations."""
    page_label = page.get_label() or str(page.number + 1)
    text = page.get_text()

    evidence = []
    markers_found = []
    confidence = 0.0

    for pattern_name, pattern in CITATION_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            confidence += 0.2
            unique_matches = list(set(matches))[:5]
            markers_found.extend(unique_matches)
            evidence.append(f"{pattern_name}: {unique_matches}")

    if confidence >= 0.2:
        return PageCandidate(
            page_index=page.number,
            page_label=page_label,
            feature_type="citation",
            confidence=min(confidence, 1.0),
            evidence=evidence,
            markers_found=markers_found[:10],
        )
    return None


def detect_tables(page: fitz.Page) -> PageCandidate | None:
    """Detect if page has table-like structures."""
    page_label = page.get_label() or str(page.number + 1)

    # Use PyMuPDF's table detection
    try:
        tables = page.find_tables()
        if tables and len(tables.tables) > 0:
            evidence = []
            for i, table in enumerate(tables.tables[:3]):
                evidence.append(f"Table {i + 1}: {table.row_count} rows x {table.col_count} cols")

            return PageCandidate(
                page_index=page.number,
                page_label=page_label,
                feature_type="table",
                confidence=0.8,
                evidence=evidence,
            )
    except Exception:
        pass

    return None


def detect_negative_example(page: fitz.Page, body_size: float) -> PageCandidate | None:
    """Identify pages suitable as negative examples (body text, no features)."""
    page_label = page.get_label() or str(page.number + 1)
    page_height = page.rect.height

    text = page.get_text().strip()

    # Must have substantial text
    if len(text) < 500:
        return None

    # Check for absence of features
    blocks = page.get_text("dict")["blocks"]

    has_small_bottom_text = False
    has_superscript = False

    for block in blocks:
        if block["type"] != 0:
            continue

        block_top = block["bbox"][1]

        if block_top > page_height * 0.80:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if span["size"] < body_size * 0.9:
                        has_small_bottom_text = True

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if span["flags"] & 1:
                    has_superscript = True

    # Check for citation patterns
    has_citations = any(p.search(text) for p in CITATION_PATTERNS.values())

    if not has_small_bottom_text and not has_superscript and not has_citations:
        return PageCandidate(
            page_index=page.number,
            page_label=page_label,
            feature_type="negative",
            confidence=0.7,
            evidence=[
                "Body text present",
                "No footnote region",
                "No superscripts",
                "No citation patterns",
            ],
        )

    return None


def find_endnote_section(doc: fitz.Document) -> dict | None:
    """Find endnote/notes section in document."""
    # Search from back of document
    for page_num in range(max(0, doc.page_count - 150), doc.page_count):
        page = doc[page_num]
        text = page.get_text()[:500].upper()

        if any(marker in text for marker in ["NOTES", "ENDNOTES", "NOTES TO"]):
            # Find where it ends
            end_page = page_num
            for check_page in range(page_num + 1, min(page_num + 100, doc.page_count)):
                check_text = doc[check_page].get_text()[:300].upper()
                if any(
                    marker in check_text
                    for marker in ["BIBLIOGRAPHY", "WORKS CITED", "REFERENCES", "INDEX"]
                ):
                    end_page = check_page - 1
                    break
                end_page = check_page

            return {
                "start_page": page_num,
                "end_page": end_page,
                "start_label": page.get_label() or str(page_num + 1),
            }

    return None


def find_bibliography_section(doc: fitz.Document) -> dict | None:
    """Find bibliography/works cited section."""
    for page_num in range(max(0, doc.page_count - 100), doc.page_count):
        page = doc[page_num]
        text = page.get_text()[:500].upper()

        if any(marker in text for marker in ["BIBLIOGRAPHY", "WORKS CITED", "REFERENCES"]):
            # Find where it ends
            end_page = page_num
            for check_page in range(page_num + 1, min(page_num + 50, doc.page_count)):
                check_text = doc[check_page].get_text()[:300].upper()
                if "INDEX" in check_text:
                    end_page = check_page - 1
                    break
                end_page = check_page

            return {
                "start_page": page_num,
                "end_page": end_page,
                "start_label": page.get_label() or str(page_num + 1),
            }

    return None


def analyze_document(pdf_path: str, features: set[str] | None = None) -> DocumentReport:
    """Analyze a PDF and find candidate pages for ground truth."""
    if features is None:
        features = {"footnotes", "citations", "tables", "negatives"}

    doc = fitz.open(pdf_path)
    body_size = get_body_font_size(doc)

    report = DocumentReport(
        pdf_path=str(pdf_path),
        total_pages=doc.page_count,
        body_font_size=body_size,
    )

    # Find special sections
    report.endnote_section = find_endnote_section(doc)
    report.bibliography_section = find_bibliography_section(doc)

    # Analyze each page
    for page_num in range(doc.page_count):
        page = doc[page_num]

        if "footnotes" in features:
            candidate = detect_footnotes(page, body_size)
            if candidate:
                report.footnote_candidates.append(candidate)

        if "citations" in features:
            candidate = detect_citations(page)
            if candidate:
                report.citation_candidates.append(candidate)

        if "tables" in features:
            candidate = detect_tables(page)
            if candidate:
                report.table_candidates.append(candidate)

        if "negatives" in features:
            candidate = detect_negative_example(page, body_size)
            if candidate:
                report.negative_candidates.append(candidate)

    doc.close()
    return report


def print_report(report: DocumentReport, verbose: bool = False):
    """Print a human-readable summary of the report."""
    print(f"\n{'=' * 70}")
    print(f"CANDIDATE PAGE REPORT: {Path(report.pdf_path).name}")
    print(f"{'=' * 70}")
    print(f"Total pages: {report.total_pages}")
    print(f"Body font size: {report.body_font_size}pt")

    if report.endnote_section:
        s = report.endnote_section
        print(
            f"Endnote section: pages {s['start_page']}-{s['end_page']} (label: {s['start_label']})"
        )

    if report.bibliography_section:
        s = report.bibliography_section
        print(f"Bibliography: pages {s['start_page']}-{s['end_page']} (label: {s['start_label']})")

    print(f"\n{'─' * 70}")
    print(f"FOOTNOTE CANDIDATES: {len(report.footnote_candidates)} pages")
    print(f"{'─' * 70}")

    # Sort by confidence
    for c in sorted(report.footnote_candidates, key=lambda x: -x.confidence)[:15]:
        markers = c.markers_found
        print(f"  Page {c.page_index:3d} ({c.page_label:>6}) conf={c.confidence:.2f} {markers}")
        if verbose:
            for e in c.evidence:
                print(f"    - {e}")

    if len(report.footnote_candidates) > 15:
        print(f"  ... and {len(report.footnote_candidates) - 15} more")

    print(f"\n{'─' * 70}")
    print(f"CITATION CANDIDATES: {len(report.citation_candidates)} pages")
    print(f"{'─' * 70}")

    for c in sorted(report.citation_candidates, key=lambda x: -x.confidence)[:10]:
        print(f"  Page {c.page_index:3d} ({c.page_label:>6}) conf={c.confidence:.2f}")
        if verbose:
            for e in c.evidence[:3]:
                print(f"    - {e}")

    if len(report.citation_candidates) > 10:
        print(f"  ... and {len(report.citation_candidates) - 10} more")

    print(f"\n{'─' * 70}")
    print(f"TABLE CANDIDATES: {len(report.table_candidates)} pages")
    print(f"{'─' * 70}")

    for c in report.table_candidates[:10]:
        print(f"  Page {c.page_index:3d} ({c.page_label:>6}) {c.evidence}")

    print(f"\n{'─' * 70}")
    print(f"NEGATIVE EXAMPLES: {len(report.negative_candidates)} pages (no features)")
    print(f"{'─' * 70}")

    # Sample some negatives
    import random

    sample = random.sample(report.negative_candidates, min(10, len(report.negative_candidates)))
    for c in sorted(sample, key=lambda x: x.page_index):
        print(f"  Page {c.page_index:3d} ({c.page_label:>6})")

    print()


def main():
    parser = argparse.ArgumentParser(description="Find candidate pages for ground truth labeling")
    parser.add_argument("pdfs", nargs="+", help="PDF files to analyze")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument(
        "--features",
        "-f",
        help="Features to detect (comma-separated: footnotes,citations,tables,negatives)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed evidence")

    args = parser.parse_args()

    features = None
    if args.features:
        features = set(args.features.split(","))

    all_reports = []

    for pdf_path in args.pdfs:
        if not Path(pdf_path).exists():
            print(f"Warning: {pdf_path} not found, skipping")
            continue

        report = analyze_document(pdf_path, features)
        all_reports.append(report)
        print_report(report, verbose=args.verbose)

    if args.output:
        # Convert to JSON-serializable format
        output_data = []
        for report in all_reports:
            report_dict = {
                "pdf_path": report.pdf_path,
                "total_pages": report.total_pages,
                "body_font_size": report.body_font_size,
                "endnote_section": report.endnote_section,
                "bibliography_section": report.bibliography_section,
                "footnote_candidates": [asdict(c) for c in report.footnote_candidates],
                "citation_candidates": [asdict(c) for c in report.citation_candidates],
                "table_candidates": [asdict(c) for c in report.table_candidates],
                "negative_candidates": [asdict(c) for c in report.negative_candidates],
            }
            output_data.append(report_dict)

        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"\nReport saved to {args.output}")


if __name__ == "__main__":
    main()
