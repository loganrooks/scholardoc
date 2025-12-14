#!/usr/bin/env python3
"""
Spike 04: Explore Footnote Detection Approaches

PURPOSE: Test different strategies for detecting footnotes in PDFs.
         This is a hard problem - PDFs have no semantic footnote markup.

APPROACHES TO TEST:
1. Page-bottom region (text in bottom 20% of page)
2. Font size reduction (smaller than body text)
3. Superscript markers (small raised numbers)
4. Number patterns (lines starting with small numbers)
5. Combined heuristics

RUN:
  uv run python spikes/04_footnote_detection.py sample.pdf

QUESTIONS TO ANSWER:
1. Can we reliably find footnote regions?
2. Can we match footnote markers to content?
3. What's the false positive rate?
4. Is this even feasible for Phase 1, or should it be Phase 2?
"""

import sys
import re
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict

try:
    import fitz
except ImportError:
    print("Install PyMuPDF: uv add pymupdf")
    sys.exit(1)


@dataclass  
class FootnoteCandidate:
    """A potential footnote found by some method."""
    text: str
    page: int
    method: str
    confidence: float
    marker: str | None = None  # The superscript number
    y_position: float = 0  # Vertical position on page (0=top, 1=bottom)
    font_size: float | None = None


@dataclass
class MarkerCandidate:
    """A potential footnote marker (superscript number) in body text."""
    marker: str
    page: int
    context: str  # Surrounding text
    y_position: float


def get_body_font_size(doc) -> float:
    """Determine the most common (body) font size."""
    from collections import Counter
    size_counts = Counter()
    
    for page in doc:
        data = page.get_text("dict")
        for block in data["blocks"]:
            if block["type"] != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    size = round(span["size"], 1)
                    size_counts[size] += len(span["text"])
    
    return size_counts.most_common(1)[0][0] if size_counts else 10.0


def detect_by_page_region(doc, body_size: float) -> list[FootnoteCandidate]:
    """Find text in the bottom region of pages."""
    candidates = []
    
    for page_num, page in enumerate(doc):
        page_height = page.rect.height
        bottom_threshold = page_height * 0.75  # Bottom 25%
        
        data = page.get_text("dict")
        
        for block in data["blocks"]:
            if block["type"] != 0:
                continue
            
            block_top = block["bbox"][1]
            
            if block_top > bottom_threshold:
                # This block is in the bottom region
                text_parts = []
                sizes = []
                
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text_parts.append(span["text"])
                        sizes.append(span["size"])
                
                text = "".join(text_parts).strip()
                avg_size = sum(sizes) / len(sizes) if sizes else body_size
                
                if text and len(text) > 5:
                    # Check if it looks like footnote (smaller font, starts with number)
                    is_smaller = avg_size < body_size - 0.5
                    starts_with_num = bool(re.match(r'^\d+[\.\s]', text))
                    
                    conf = 0.3  # Base confidence for bottom region
                    if is_smaller:
                        conf += 0.3
                    if starts_with_num:
                        conf += 0.3
                    
                    candidates.append(FootnoteCandidate(
                        text=text[:100],
                        page=page_num,
                        method="page_region",
                        confidence=conf,
                        marker=re.match(r'^(\d+)', text).group(1) if starts_with_num else None,
                        y_position=block_top / page_height,
                        font_size=avg_size,
                    ))
    
    return candidates


def detect_by_font_size(doc, body_size: float) -> list[FootnoteCandidate]:
    """Find text blocks with smaller-than-body font."""
    candidates = []
    footnote_size_threshold = body_size * 0.85
    
    for page_num, page in enumerate(doc):
        page_height = page.rect.height
        data = page.get_text("dict")
        
        for block in data["blocks"]:
            if block["type"] != 0:
                continue
            
            text_parts = []
            sizes = []
            
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text_parts.append(span["text"])
                    sizes.append(span["size"])
            
            if not sizes:
                continue
                
            avg_size = sum(sizes) / len(sizes)
            text = "".join(text_parts).strip()
            
            if avg_size < footnote_size_threshold and text and len(text) > 10:
                # Smaller text - might be footnote
                y_pos = block["bbox"][1] / page_height
                starts_with_num = bool(re.match(r'^\d+[\.\s]', text))
                
                conf = 0.4
                if y_pos > 0.7:  # Also in bottom region
                    conf += 0.3
                if starts_with_num:
                    conf += 0.2
                
                candidates.append(FootnoteCandidate(
                    text=text[:100],
                    page=page_num,
                    method="font_size",
                    confidence=conf,
                    marker=re.match(r'^(\d+)', text).group(1) if starts_with_num else None,
                    y_position=y_pos,
                    font_size=avg_size,
                ))
    
    return candidates


def detect_superscript_markers(doc) -> list[MarkerCandidate]:
    """Find superscript numbers that might be footnote markers."""
    markers = []
    
    for page_num, page in enumerate(doc):
        page_height = page.rect.height
        data = page.get_text("dict")
        
        for block in data["blocks"]:
            if block["type"] != 0:
                continue
            
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                
                for i, span in enumerate(spans):
                    # Check for superscript flag (bit 0)
                    is_superscript = span["flags"] & 1
                    
                    # Or check for small font + number
                    text = span["text"].strip()
                    is_small_number = (
                        text.isdigit() and 
                        len(text) <= 3 and
                        span["size"] < 8
                    )
                    
                    if (is_superscript or is_small_number) and text.isdigit():
                        # Get surrounding context
                        context_before = spans[i-1]["text"][-20:] if i > 0 else ""
                        context_after = spans[i+1]["text"][:20] if i < len(spans)-1 else ""
                        context = f"...{context_before}[{text}]{context_after}..."
                        
                        markers.append(MarkerCandidate(
                            marker=text,
                            page=page_num,
                            context=context,
                            y_position=block["bbox"][1] / page_height,
                        ))
    
    return markers


def analyze_footnotes(pdf_path: str, max_pages: int = 20):
    """Run all detection methods and analyze results."""
    
    print(f"{'='*70}")
    print(f"FOOTNOTE DETECTION ANALYSIS: {pdf_path}")
    print(f"{'='*70}")
    print()
    
    doc = fitz.open(pdf_path)
    
    if doc.page_count > max_pages:
        print(f"Note: Analyzing first {max_pages} of {doc.page_count} pages")
        # Create a subset for analysis
        doc2 = fitz.open()
        for i in range(min(max_pages, doc.page_count)):
            doc2.insert_pdf(doc, from_page=i, to_page=i)
        doc.close()
        doc = doc2
    
    body_size = get_body_font_size(doc)
    print(f"Detected body font size: {body_size}")
    print()
    
    # Run detection methods
    region_candidates = detect_by_page_region(doc, body_size)
    fontsize_candidates = detect_by_font_size(doc, body_size)
    markers = detect_superscript_markers(doc)
    
    doc.close()
    
    # Summary
    print(f"{'='*70}")
    print("DETECTION SUMMARY")
    print(f"{'='*70}")
    print()
    print(f"Page-region method:  {len(region_candidates)} candidates")
    print(f"Font-size method:    {len(fontsize_candidates)} candidates")
    print(f"Superscript markers: {len(markers)} found")
    print()
    
    # Show region candidates
    print(f"{'='*70}")
    print("PAGE-REGION CANDIDATES (bottom 25% of pages)")
    print(f"{'='*70}")
    
    for c in region_candidates[:20]:
        marker_str = f"[{c.marker}]" if c.marker else "[?]"
        print(f"\nPage {c.page} {marker_str} (conf={c.confidence:.1f}, y={c.y_position:.2f}, sz={c.font_size:.1f}):")
        print(f"  {c.text}")
    
    if len(region_candidates) > 20:
        print(f"\n... ({len(region_candidates)} total)")
    
    # Show font-size candidates
    print()
    print(f"{'='*70}")
    print("FONT-SIZE CANDIDATES (smaller than body)")
    print(f"{'='*70}")
    
    for c in fontsize_candidates[:20]:
        marker_str = f"[{c.marker}]" if c.marker else "[?]"
        print(f"\nPage {c.page} {marker_str} (conf={c.confidence:.1f}, y={c.y_position:.2f}, sz={c.font_size:.1f}):")
        print(f"  {c.text}")
    
    if len(fontsize_candidates) > 20:
        print(f"\n... ({len(fontsize_candidates)} total)")
    
    # Show markers
    print()
    print(f"{'='*70}")
    print("SUPERSCRIPT MARKERS IN BODY TEXT")
    print(f"{'='*70}")
    print()
    
    # Group by page
    markers_by_page = defaultdict(list)
    for m in markers:
        markers_by_page[m.page].append(m)
    
    for page in sorted(markers_by_page.keys())[:10]:
        print(f"Page {page}:")
        for m in markers_by_page[page][:5]:
            print(f"  Marker '{m.marker}': {m.context}")
        if len(markers_by_page[page]) > 5:
            print(f"  ... ({len(markers_by_page[page])} markers on this page)")
        print()
    
    # Try to match markers to footnotes
    print(f"{'='*70}")
    print("MARKER-TO-FOOTNOTE MATCHING ATTEMPT")
    print(f"{'='*70}")
    print()
    
    # Build footnote lookup by page and marker
    footnotes_by_page_marker = {}
    for c in region_candidates + fontsize_candidates:
        if c.marker:
            key = (c.page, c.marker)
            if key not in footnotes_by_page_marker:
                footnotes_by_page_marker[key] = c
    
    matched = 0
    unmatched_markers = []
    
    for m in markers:
        key = (m.page, m.marker)
        if key in footnotes_by_page_marker:
            matched += 1
        else:
            unmatched_markers.append(m)
    
    print(f"Markers with matching footnotes: {matched}/{len(markers)}")
    print(f"Unmatched markers: {len(unmatched_markers)}")
    
    if unmatched_markers[:10]:
        print("\nSample unmatched markers:")
        for m in unmatched_markers[:10]:
            print(f"  Page {m.page}, marker '{m.marker}': {m.context}")
    
    # Analysis guidance
    print()
    print(f"{'='*70}")
    print("EVALUATION & FEASIBILITY")
    print(f"{'='*70}")
    print("""
Based on these results, consider:

1. DETECTION QUALITY
   - Are the detected footnotes actually footnotes?
   - What's the false positive rate (non-footnotes detected)?
   - What's the false negative rate (footnotes missed)?

2. MARKER MATCHING
   - Can we reliably match superscript markers to footnote text?
   - Do footnotes appear on the same page as their markers?
   - Are there endnotes (all at the end) vs footnotes (per page)?

3. FEASIBILITY ASSESSMENT
   - If detection is >80% accurate: Include in Phase 1
   - If detection is 50-80% accurate: Phase 2 with manual verification option
   - If detection is <50% accurate: May need ML/different approach

4. PHILOSOPHY TEXT SPECIFICS
   - Do these texts use standard footnote conventions?
   - Are there endnotes that need different handling?
   - Multiple footnote styles in one document?

5. RECOMMENDATION
   - Is footnote detection worth the complexity?
   - Should we just preserve page-bottom text without linking?
   - Would "footnote hints" (probable regions) be enough?
""")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUsage:")
        print("  uv run python spikes/04_footnote_detection.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)
    
    analyze_footnotes(pdf_path)


if __name__ == "__main__":
    main()
