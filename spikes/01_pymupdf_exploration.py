#!/usr/bin/env python3
"""
Spike 01: Explore PyMuPDF Output Structure

PURPOSE: Understand what PyMuPDF actually gives us before designing data models.

RUN:
  uv run python spikes/01_pymupdf_exploration.py <pdf_path>           # Basic structure
  uv run python spikes/01_pymupdf_exploration.py <pdf_path> --fonts   # Font analysis
  uv run python spikes/01_pymupdf_exploration.py <pdf_path> --layout  # Layout analysis
  uv run python spikes/01_pymupdf_exploration.py <pdf_path> --all     # Everything

QUESTIONS TO ANSWER:
1. What does get_text("dict") return? (block → line → span hierarchy)
2. Can we distinguish headings by font size/weight?
3. Where do footnotes appear? (page bottom? smaller font?)
4. Are page labels (printed page numbers) available?
5. How does multi-column text appear in block structure?
6. Can we detect if a PDF is born-digital vs scanned?
"""

import sys
from pathlib import Path
from collections import defaultdict

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Install PyMuPDF: uv add pymupdf")
    sys.exit(1)


def explore_structure(pdf_path: str, max_pages: int = 3):
    """Show raw PyMuPDF block/line/span structure."""
    doc = fitz.open(pdf_path)
    
    print(f"{'='*60}")
    print(f"STRUCTURE ANALYSIS: {pdf_path}")
    print(f"{'='*60}")
    print(f"Pages: {doc.page_count}")
    print(f"Metadata: {doc.metadata}")
    print()
    
    # Page labels
    print("--- Page Labels (printed page numbers) ---")
    has_labels = False
    for i in range(min(10, doc.page_count)):
        label = doc[i].get_label()
        if label and label != str(i + 1):  # Non-trivial label
            has_labels = True
        print(f"  Index {i} → Label: {label!r}")
    
    if not has_labels:
        print("  ⚠ No custom page labels found (all match index+1)")
    print()
    
    # Detailed page exploration
    for page_num in range(min(max_pages, doc.page_count)):
        page = doc[page_num]
        data = page.get_text("dict")
        
        print(f"\n--- Page {page_num} (label: {page.get_label()!r}) ---")
        print(f"Page size: {page.rect.width:.0f} x {page.rect.height:.0f}")
        print(f"Text blocks: {len([b for b in data['blocks'] if b['type'] == 0])}")
        print(f"Image blocks: {len([b for b in data['blocks'] if b['type'] == 1])}")
        
        for block_idx, block in enumerate(data["blocks"]):
            if block["type"] == 1:  # Image
                print(f"\n  Block {block_idx} [IMAGE]: bbox={_fmt_bbox(block['bbox'])}")
                continue
                
            # Text block
            lines = block.get("lines", [])
            print(f"\n  Block {block_idx} [TEXT]: bbox={_fmt_bbox(block['bbox'])}, {len(lines)} lines")
            
            for line_idx, line in enumerate(lines[:5]):  # First 5 lines
                spans = line.get("spans", [])
                for span in spans:
                    text = span["text"][:60] + "..." if len(span["text"]) > 60 else span["text"]
                    flags_str = _decode_flags(span["flags"])
                    print(f"    L{line_idx}: {span['font'][:20]:20} sz={span['size']:5.1f} "
                          f"{flags_str:10} | {text!r}")
            
            if len(lines) > 5:
                print(f"    ... ({len(lines) - 5} more lines)")
    
    doc.close()


def analyze_fonts(pdf_path: str):
    """Analyze font patterns to identify body vs heading text."""
    doc = fitz.open(pdf_path)
    
    print(f"{'='*60}")
    print(f"FONT ANALYSIS: {pdf_path}")
    print(f"{'='*60}")
    
    font_stats = defaultdict(lambda: {"count": 0, "samples": [], "pages": set()})
    
    for page_num, page in enumerate(doc):
        data = page.get_text("dict")
        for block in data["blocks"]:
            if block["type"] != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    key = (span["font"], round(span["size"], 1), span["flags"])
                    font_stats[key]["count"] += 1
                    font_stats[key]["pages"].add(page_num)
                    if len(font_stats[key]["samples"]) < 3:
                        text = span["text"].strip()[:50]
                        if text:
                            font_stats[key]["samples"].append(text)
    
    doc.close()
    
    # Sort by frequency
    sorted_fonts = sorted(font_stats.items(), key=lambda x: -x[1]["count"])
    
    print("\nFont usage (most frequent = likely body text):\n")
    
    total_spans = sum(s["count"] for s in font_stats.values())
    
    for (font, size, flags), stats in sorted_fonts[:15]:
        pct = (stats["count"] / total_spans) * 100
        flags_str = _decode_flags(flags)
        pages_str = f"{len(stats['pages'])} pages" if len(stats['pages']) > 5 else str(sorted(stats['pages']))
        
        print(f"{font[:25]:25} sz={size:5.1f} {flags_str:10} | {stats['count']:5} ({pct:5.1f}%) | {pages_str}")
        for sample in stats["samples"][:2]:
            print(f"    Sample: {sample!r}")
        print()
    
    # Interpretation hints
    print("--- Interpretation ---")
    if sorted_fonts:
        body_font = sorted_fonts[0]
        print(f"Likely body text: {body_font[0][0]}, size {body_font[0][1]}")
        
        larger_fonts = [(k, v) for k, v in sorted_fonts if k[1] > body_font[0][1] + 1]
        if larger_fonts:
            print(f"Possible headings (larger than body):")
            for (font, size, flags), stats in larger_fonts[:5]:
                print(f"  - {font}, size {size}: {stats['samples'][0]!r}" if stats['samples'] else f"  - {font}, size {size}")


def analyze_layout(pdf_path: str):
    """Analyze page layout for multi-column detection and footnote regions."""
    doc = fitz.open(pdf_path)
    
    print(f"{'='*60}")
    print(f"LAYOUT ANALYSIS: {pdf_path}")
    print(f"{'='*60}")
    
    for page_num in range(min(5, doc.page_count)):
        page = doc[page_num]
        data = page.get_text("dict")
        
        page_width = page.rect.width
        page_height = page.rect.height
        
        print(f"\n--- Page {page_num} ({page_width:.0f} x {page_height:.0f}) ---")
        
        # Collect text block positions
        text_blocks = [b for b in data["blocks"] if b["type"] == 0]
        
        if not text_blocks:
            print("  No text blocks")
            continue
        
        # Analyze horizontal distribution (multi-column detection)
        x_centers = [(b["bbox"][0] + b["bbox"][2]) / 2 for b in text_blocks]
        left_blocks = sum(1 for x in x_centers if x < page_width / 2)
        right_blocks = sum(1 for x in x_centers if x >= page_width / 2)
        
        if left_blocks > 2 and right_blocks > 2 and abs(left_blocks - right_blocks) < max(left_blocks, right_blocks) * 0.5:
            print(f"  ⚠ POSSIBLE MULTI-COLUMN: {left_blocks} blocks left, {right_blocks} blocks right")
        else:
            print(f"  Single column likely: {left_blocks} left, {right_blocks} right")
        
        # Analyze vertical distribution (footnote detection)
        bottom_third_y = page_height * 0.7
        bottom_blocks = [b for b in text_blocks if b["bbox"][1] > bottom_third_y]
        
        if bottom_blocks:
            # Check if bottom blocks have smaller font
            bottom_fonts = []
            other_fonts = []
            
            for block in text_blocks:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if block["bbox"][1] > bottom_third_y:
                            bottom_fonts.append(span["size"])
                        else:
                            other_fonts.append(span["size"])
            
            if bottom_fonts and other_fonts:
                avg_bottom = sum(bottom_fonts) / len(bottom_fonts)
                avg_other = sum(other_fonts) / len(other_fonts)
                
                if avg_bottom < avg_other - 1:
                    print(f"  ⚠ POSSIBLE FOOTNOTES: Bottom text avg size {avg_bottom:.1f} vs body {avg_other:.1f}")
                    for block in bottom_blocks[:2]:
                        first_line = block.get("lines", [{}])[0]
                        first_span = first_line.get("spans", [{}])[0]
                        text = first_span.get("text", "")[:60]
                        print(f"    → {text!r}")
    
    doc.close()


def check_quality(pdf_path: str):
    """Check if PDF appears to be born-digital or scanned."""
    doc = fitz.open(pdf_path)
    
    print(f"{'='*60}")
    print(f"QUALITY CHECK: {pdf_path}")
    print(f"{'='*60}")
    
    total_pages = doc.page_count
    pages_with_text = 0
    pages_with_images = 0
    total_text_len = 0
    embedded_fonts = set()
    
    for page in doc:
        data = page.get_text("dict")
        
        has_text = any(b["type"] == 0 for b in data["blocks"])
        has_images = any(b["type"] == 1 for b in data["blocks"])
        
        if has_text:
            pages_with_text += 1
        if has_images:
            pages_with_images += 1
        
        for block in data["blocks"]:
            if block["type"] == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        total_text_len += len(span.get("text", ""))
                        embedded_fonts.add(span.get("font", ""))
    
    doc.close()
    
    print(f"\nPages: {total_pages}")
    print(f"Pages with text: {pages_with_text} ({pages_with_text/total_pages*100:.0f}%)")
    print(f"Pages with images: {pages_with_images} ({pages_with_images/total_pages*100:.0f}%)")
    print(f"Total text extracted: {total_text_len:,} characters")
    print(f"Avg chars/page: {total_text_len/total_pages:,.0f}")
    print(f"Embedded fonts: {len(embedded_fonts)}")
    
    # Heuristics
    print("\n--- Assessment ---")
    
    if pages_with_text < total_pages * 0.5:
        print("⚠ WARNING: Less than 50% of pages have extractable text")
        print("  This may be a scanned document or image-heavy PDF")
    
    if total_text_len / total_pages < 500:
        print("⚠ WARNING: Very little text per page (< 500 chars avg)")
        print("  This may be scanned, or have text as images")
    
    if len(embedded_fonts) < 2:
        print("⚠ WARNING: Very few embedded fonts")
        print("  May indicate OCR'd text or simple layout")
    
    if pages_with_text >= total_pages * 0.9 and total_text_len / total_pages > 1000:
        print("✓ Appears to be born-digital with good text extraction")


def _fmt_bbox(bbox):
    """Format bounding box for display."""
    return f"({bbox[0]:.0f},{bbox[1]:.0f})-({bbox[2]:.0f},{bbox[3]:.0f})"


def _decode_flags(flags):
    """Decode PyMuPDF font flags to readable string."""
    parts = []
    if flags & 2**0:  # superscript
        parts.append("super")
    if flags & 2**1:  # italic
        parts.append("ital")
    if flags & 2**2:  # serifed
        parts.append("serif")
    if flags & 2**3:  # monospaced
        parts.append("mono")
    if flags & 2**4:  # bold
        parts.append("bold")
    return ",".join(parts) if parts else "-"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUsage:")
        print("  uv run python spikes/01_pymupdf_exploration.py <pdf_path> [options]")
        print("\nOptions:")
        print("  --fonts   Analyze font usage patterns")
        print("  --layout  Analyze page layout (columns, footnotes)")
        print("  --quality Check if born-digital vs scanned")
        print("  --all     Run all analyses")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)
    
    args = set(sys.argv[2:])
    
    if "--all" in args:
        explore_structure(pdf_path)
        print("\n" + "="*60 + "\n")
        analyze_fonts(pdf_path)
        print("\n" + "="*60 + "\n")
        analyze_layout(pdf_path)
        print("\n" + "="*60 + "\n")
        check_quality(pdf_path)
    elif "--fonts" in args:
        analyze_fonts(pdf_path)
    elif "--layout" in args:
        analyze_layout(pdf_path)
    elif "--quality" in args:
        check_quality(pdf_path)
    else:
        explore_structure(pdf_path)


if __name__ == "__main__":
    main()
