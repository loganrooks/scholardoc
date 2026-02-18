#!/usr/bin/env python3
"""
Generate Draft Ground Truth

Auto-generates a draft ground truth YAML file from a PDF using:
1. Docling RT-DETR for layout detection (bboxes)
2. PyMuPDF for text extraction per region
3. Heuristic parsers for footnotes, citations, page numbers

Usage:
    uv run python ground_truth/scripts/generate_draft.py <pdf_path> --pages 150-170
    uv run python ground_truth/scripts/generate_draft.py <pdf_path> --pages 150-170 -o out.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import fitz
import yaml

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from spikes.docling_batched import DoclingLayoutDetector, PageLayout  # noqa: E402


@dataclass
class RegionData:
    """Extracted data for a single region."""

    id: str
    type: str
    bbox: list[float]  # Normalized [x0, y0, x1, y1]
    text: str
    special_chars: list[dict[str, str]] = field(default_factory=list)


@dataclass
class PageData:
    """Extracted data for a single page."""

    index: int
    label: str | None
    dimensions: dict[str, float]
    regions: list[RegionData]
    quality: dict[str, Any]


# Mapping from Docling labels to our schema region types
DOCLING_TO_SCHEMA = {
    "Text": "body",
    "Footnote": "footnote_region",
    "Page-header": "header",
    "Page-footer": "footer",
    "Section-header": "heading",
    "Title": "heading",
    "Caption": "caption",
    "Table": "table",
    "Picture": "figure",
    "Formula": "formula",
    "List-item": "body",  # Treat as body for now
    "Document-Index": "index",
    "Code": "code",
}

# Regex patterns for element detection
FOOTNOTE_MARKER_PATTERN = re.compile(r"[¹²³⁴⁵⁶⁷⁸⁹⁰]+|\[(\d+)\]|(?<!\d)(\d{1,2})(?=[.\s])")
CITATION_PATTERN = re.compile(
    r"\(([A-Z][a-z]+(?:\s+(?:and|&)\s+[A-Z][a-z]+)*)"
    r"(?:\s+et\s+al\.?)?"
    r"[\s,]+(\d{4})"
    r"(?:[\s,]+(?:p\.?\s*)?(\d+(?:-\d+)?))?\)"
)
PAGE_NUMBER_PATTERN = re.compile(r"^\s*(\d+|[ivxlcdm]+)\s*$", re.IGNORECASE)

# Language detection patterns
GREEK_PATTERN = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]+")
GERMAN_PATTERN = re.compile(r"\b[A-ZÄÖÜ][a-zäöüß]*(?:heit|keit|ung|sein|dasein)\b", re.IGNORECASE)
LATIN_PATTERN = re.compile(
    r"\b(?:et\s+al|ibid|op\.\s*cit|loc\.\s*cit|cf|viz|e\.g|i\.e)\b", re.IGNORECASE
)


def normalize_bbox(bbox: tuple[float, ...], page_width: float, page_height: float) -> list[float]:
    """Convert pixel bbox to normalized 0-1 coordinates."""
    x0, y0, x1, y1 = bbox
    return [
        round(x0 / page_width, 4),
        round(y0 / page_height, 4),
        round(x1 / page_width, 4),
        round(y1 / page_height, 4),
    ]


def extract_text_from_bbox(
    page: fitz.Page,
    bbox: tuple[float, ...],
    page_width: float,
    page_height: float,
) -> str:
    """Extract text from a bounding box region using PyMuPDF."""
    # Docling bbox is in pixel coords at render DPI, need to convert to PDF points
    # The detector uses 150 DPI, PDF is 72 DPI
    scale = 72 / 150
    pdf_bbox = fitz.Rect(
        bbox[0] * scale,
        bbox[1] * scale,
        bbox[2] * scale,
        bbox[3] * scale,
    )

    # Extract text from rect
    text = page.get_text("text", clip=pdf_bbox)
    return text.strip()


def detect_special_chars(text: str) -> list[dict[str, str]]:
    """Detect special characters (Greek, German, Latin) in text."""
    special = []

    for match in GREEK_PATTERN.finditer(text):
        special.append({"lang": "el", "text": match.group()})

    for match in GERMAN_PATTERN.finditer(text):
        # Filter out common English words
        word = match.group()
        if word.lower() not in {"being", "thing", "nothing", "something"}:
            special.append({"lang": "de", "text": word})

    # Don't include Latin abbreviations as "special" - they're common
    return special


def detect_footnote_markers(text: str) -> list[dict[str, Any]]:
    """Detect footnote markers in body text."""
    markers = []
    for match in FOOTNOTE_MARKER_PATTERN.finditer(text):
        marker_text = match.group(1) or match.group(2) or match.group()
        markers.append(
            {
                "text": marker_text,
                "char_offset": match.start(),
            }
        )
    return markers


def detect_citations(text: str) -> list[dict[str, Any]]:
    """Detect author-date citations in text."""
    citations = []
    for match in CITATION_PATTERN.finditer(text):
        citations.append(
            {
                "raw": match.group(),
                "char_offset": match.start(),
                "parsed": {
                    "style": "author_date",
                    "authors": [match.group(1)],
                    "year": int(match.group(2)),
                    "pages": match.group(3),
                },
            }
        )
    return citations


def detect_page_number(text: str) -> dict[str, Any] | None:
    """Detect if text is a page number."""
    match = PAGE_NUMBER_PATTERN.match(text)
    if match:
        value = match.group(1)
        try:
            normalized = int(value)
            fmt = "arabic"
        except ValueError:
            # Roman numeral
            normalized = roman_to_int(value.lower())
            fmt = "roman_lower" if value.islower() else "roman_upper"
        return {
            "displayed": value,
            "normalized": normalized,
            "format": fmt,
        }
    return None


def roman_to_int(s: str) -> int:
    """Convert roman numeral to integer."""
    values = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
    result = 0
    prev = 0
    for char in reversed(s.lower()):
        curr = values.get(char, 0)
        if curr < prev:
            result -= curr
        else:
            result += curr
        prev = curr
    return result


def process_page(
    page_layout: PageLayout,
    pdf_page: fitz.Page,
    page_index: int,
) -> PageData:
    """Process a single page, combining layout detection with text extraction."""
    page_width = pdf_page.rect.width
    page_height = pdf_page.rect.height

    # Get render dimensions for bbox conversion
    render_width = page_layout.image_size[0]
    render_height = page_layout.image_size[1]

    regions: list[RegionData] = []
    region_counts: dict[str, int] = {}

    for box in page_layout.boxes:
        # Map Docling label to our schema type
        region_type = DOCLING_TO_SCHEMA.get(box.label, "unknown")

        # Generate unique region ID
        region_counts[region_type] = region_counts.get(region_type, 0) + 1
        region_id = f"{region_type}_{region_counts[region_type]}"

        # Normalize bbox
        norm_bbox = normalize_bbox(box.bbox, render_width, render_height)

        # Extract text from region
        text = extract_text_from_bbox(pdf_page, box.bbox, page_width, page_height)

        # Detect special characters
        special_chars = detect_special_chars(text)

        regions.append(
            RegionData(
                id=region_id,
                type=region_type,
                bbox=norm_bbox,
                text=text,
                special_chars=special_chars,
            )
        )

    # Try to extract page label from header/footer regions
    page_label = None
    for region in regions:
        if region.type in ("header", "footer") and region.text:
            pn = detect_page_number(region.text.strip())
            if pn:
                page_label = pn["displayed"]
                break

    return PageData(
        index=page_index,
        label=page_label,
        dimensions={"width": page_width, "height": page_height},
        regions=regions,
        quality={"scan_quality": "high", "difficulty": "medium"},  # Human assesses later
    )


def extract_footnotes_from_pages(pages: list[PageData]) -> list[dict[str, Any]]:
    """Extract footnotes from processed pages."""
    footnotes = []
    footnote_id = 0

    for page in pages:
        # Find body regions and footnote regions
        body_regions = [r for r in page.regions if r.type == "body"]
        fn_regions = [r for r in page.regions if r.type == "footnote_region"]

        if not fn_regions:
            continue

        # Detect markers in body text
        all_markers = []
        for region in body_regions:
            markers = detect_footnote_markers(region.text)
            for m in markers:
                m["page"] = page.index
                m["region_id"] = region.id
            all_markers.extend(markers)

        # Extract footnote content from footnote regions
        for fn_region in fn_regions:
            # Simple heuristic: split by newline + number pattern
            fn_text = fn_region.text
            if not fn_text:
                continue

            # For now, treat each footnote region as one note
            # More sophisticated parsing would split by markers
            footnote_id += 1
            footnotes.append(
                {
                    "id": f"fn_{footnote_id}",
                    "marker": {
                        "text": str(footnote_id),
                        "page": page.index,
                        "region_id": "unknown",  # Would need matching logic
                        "char_offset": 0,
                    },
                    "content": [
                        {
                            "page": page.index,
                            "region_id": fn_region.id,
                            "text": fn_text,
                            "is_continuation": False,
                        }
                    ],
                    "pages": [page.index],
                    "note_type": "author",
                    "tags": [],
                }
            )

    return footnotes


def extract_citations_from_pages(pages: list[PageData]) -> list[dict[str, Any]]:
    """Extract citations from processed pages."""
    citations = []
    cite_id = 0

    for page in pages:
        for region in page.regions:
            if region.type != "body":
                continue

            detected = detect_citations(region.text)
            for cite in detected:
                cite_id += 1
                citations.append(
                    {
                        "id": f"cite_{cite_id}",
                        "raw": cite["raw"],
                        "page": page.index,
                        "region_id": region.id,
                        "char_offset": cite["char_offset"],
                        "parsed": cite["parsed"],
                        "bib_entry_id": None,
                        "tags": [],
                    }
                )

    return citations


def extract_page_numbers(pages: list[PageData]) -> list[dict[str, Any]]:
    """Extract page number information from pages."""
    page_numbers = []

    for page in pages:
        for region in page.regions:
            if region.type in ("header", "footer"):
                pn = detect_page_number(region.text.strip())
                if pn:
                    page_numbers.append(
                        {
                            "page": page.index,
                            "displayed": pn["displayed"],
                            "normalized": pn["normalized"],
                            "format": pn["format"],
                            "position": region.type,
                        }
                    )
                    break  # One page number per page

    return page_numbers


def generate_draft(
    pdf_path: Path,
    page_range: tuple[int, int],
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Generate a draft ground truth YAML from a PDF."""
    print(f"Processing: {pdf_path}")
    print(f"Page range: {page_range[0]}-{page_range[1]}")

    # Initialize layout detector
    detector = DoclingLayoutDetector(
        device="cuda",
        batch_size=16,
        confidence_threshold=0.3,
        dpi=150,
    )

    # Run layout detection
    print("\nRunning layout detection...")
    layouts = detector.detect_pdf(pdf_path, page_range=page_range)

    # Open PDF for text extraction
    doc = fitz.open(pdf_path)

    # Process each page
    print("\nExtracting text from regions...")
    pages: list[PageData] = []
    for layout in layouts:
        pdf_page = doc[layout.page_num]
        page_data = process_page(layout, pdf_page, layout.page_num)
        pages.append(page_data)

    doc.close()

    # Extract semantic elements
    print("\nDetecting semantic elements...")
    footnotes = extract_footnotes_from_pages(pages)
    citations = extract_citations_from_pages(pages)
    page_numbers = extract_page_numbers(pages)

    print(f"  Found {len(footnotes)} footnotes")
    print(f"  Found {len(citations)} citations")
    print(f"  Found {len(page_numbers)} page numbers")

    # Build document structure
    document = {
        "schema_version": "1.1.0",
        "source": {
            "pdf": pdf_path.name,
            "page_range": list(page_range),
            "document_type": "unknown",  # To be filled by human
        },
        "annotation_status": {
            "footnotes": {
                "state": "auto_generated",
                "count": len(footnotes),
                "annotator": "auto",
                "verified_by": None,
            },
            "endnotes": {
                "state": "auto_generated",
                "count": 0,
                "annotator": "auto",
                "verified_by": None,
            },
            "citations": {
                "state": "auto_generated",
                "count": len(citations),
                "annotator": "auto",
                "verified_by": None,
            },
            "marginal_refs": {
                "state": "pending",
                "count": None,
                "annotator": None,
            },
            "sous_rature": {
                "state": "pending",
                "count": None,
                "annotator": None,
            },
        },
        "pages": [
            {
                "index": p.index,
                "label": p.label,
                "dimensions": p.dimensions,
                "tags": [],
                "quality": p.quality,
                "regions": [
                    {
                        "id": r.id,
                        "type": r.type,
                        "bbox": r.bbox,
                        "text": r.text,
                        **({"special_chars": r.special_chars} if r.special_chars else {}),
                    }
                    for r in p.regions
                ],
            }
            for p in pages
        ],
        "elements": {
            "footnotes": footnotes,
            "endnotes": [],
            "citations": citations,
            "marginal_refs": [],
            "sections": [],
            "page_numbers": page_numbers,
            "bib_entries": [],
            "sous_rature": [],  # Requires visual inspection - not auto-detected
        },
        "relationships": {
            "footnote_links": [],
            "citation_bib_links": [],
            "cross_refs": [],
        },
        "structure": {
            "toc": [],
            "front_matter": {"pages": [], "elements": []},
            "back_matter": {"pages": [], "elements": []},
        },
        "metadata": {
            "tags": [],
            "created": str(date.today()),
            "last_modified": str(date.today()),
            "notes": "Auto-generated draft. Requires human review.",
        },
    }

    # Write output
    if output_path is None:
        stem = pdf_path.stem.lower().replace(" ", "_").replace("-", "_")
        output_path = Path("ground_truth/documents") / f"{stem}_draft.yaml"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        yaml.dump(document, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"\nDraft written to: {output_path}")
    return document


def main():
    parser = argparse.ArgumentParser(description="Generate draft ground truth from PDF")
    parser.add_argument("pdf_path", type=Path, help="Path to PDF file")
    parser.add_argument(
        "--pages",
        required=True,
        help="Page range (e.g., '150-170')",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output YAML path (default: ground_truth/documents/<pdf_name>_draft.yaml)",
    )

    args = parser.parse_args()

    if not args.pdf_path.exists():
        print(f"ERROR: PDF not found: {args.pdf_path}")
        sys.exit(1)

    # Parse page range
    start, end = args.pages.split("-")
    page_range = (int(start), int(end))

    generate_draft(args.pdf_path, page_range, args.output)


if __name__ == "__main__":
    main()
