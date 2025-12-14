#!/usr/bin/env python3
"""
Spike 03: Compare Heading Detection Approaches

PURPOSE: Test different strategies for detecting headings in PDFs
         to find what works for philosophy/scholarly texts.

APPROACHES TO TEST:
1. Font size threshold (larger than body = heading)
2. Font weight (bold = heading)
3. Line position (standalone short line = heading)
4. Combined heuristics
5. pymupdf4llm's built-in detection

RUN:
  uv run python spikes/03_heading_detection.py sample.pdf

QUESTIONS TO ANSWER:
1. Can we reliably detect headings by font size alone?
2. Do philosophy texts use consistent heading patterns?
3. What false positives/negatives do we get?
4. Is pymupdf4llm's detection good enough?
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from collections import Counter

try:
    import fitz
except ImportError:
    print("Install PyMuPDF: uv add pymupdf")
    sys.exit(1)


@dataclass
class DetectedHeading:
    """A heading detected by some method."""
    text: str
    page: int
    method: str
    confidence: float  # 0-1
    font_size: float | None = None
    is_bold: bool = False


def get_body_font_size(doc) -> float:
    """Determine the most common (body) font size."""
    size_counts = Counter()
    
    for page in doc:
        data = page.get_text("dict")
        for block in data["blocks"]:
            if block["type"] != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    size = round(span["size"], 1)
                    char_count = len(span["text"])
                    size_counts[size] += char_count
    
    if not size_counts:
        return 10.0
    
    return size_counts.most_common(1)[0][0]


def detect_by_font_size(doc, body_size: float, threshold: float = 1.5) -> list[DetectedHeading]:
    """Detect headings by font size > body size * threshold."""
    headings = []
    min_heading_size = body_size * threshold
    
    for page_num, page in enumerate(doc):
        data = page.get_text("dict")
        for block in data["blocks"]:
            if block["type"] != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if span["size"] >= min_heading_size:
                        text = span["text"].strip()
                        if text and len(text) > 2:  # Skip tiny fragments
                            # Higher confidence for larger sizes
                            conf = min(1.0, (span["size"] - body_size) / body_size)
                            headings.append(DetectedHeading(
                                text=text[:80],
                                page=page_num,
                                method="font_size",
                                confidence=conf,
                                font_size=span["size"],
                            ))
    
    return headings


def detect_by_bold(doc) -> list[DetectedHeading]:
    """Detect headings by bold font weight."""
    headings = []
    
    for page_num, page in enumerate(doc):
        data = page.get_text("dict")
        for block in data["blocks"]:
            if block["type"] != 0:
                continue
            for line in block.get("lines", []):
                line_text = ""
                is_bold_line = True
                
                for span in line.get("spans", []):
                    line_text += span["text"]
                    # Flag 2^4 = 16 indicates bold
                    if not (span["flags"] & 16):
                        is_bold_line = False
                
                line_text = line_text.strip()
                
                # Bold, short-ish line, not all caps (might be header/footer)
                if is_bold_line and line_text and 3 < len(line_text) < 100:
                    if not line_text.isupper() or len(line_text) < 30:
                        headings.append(DetectedHeading(
                            text=line_text[:80],
                            page=page_num,
                            method="bold",
                            confidence=0.7,
                            is_bold=True,
                        ))
    
    return headings


def detect_by_isolation(doc, body_size: float) -> list[DetectedHeading]:
    """Detect headings by line isolation (standalone short lines)."""
    headings = []
    
    for page_num, page in enumerate(doc):
        data = page.get_text("dict")
        blocks = [b for b in data["blocks"] if b["type"] == 0]
        
        for block in blocks:
            lines = block.get("lines", [])
            
            # Single-line block that's short = possible heading
            if len(lines) == 1:
                line = lines[0]
                text = "".join(s["text"] for s in line.get("spans", [])).strip()
                
                # Short text, not a page number, not too short
                if 5 < len(text) < 80 and not text.isdigit():
                    # Check if font is at least body size
                    sizes = [s["size"] for s in line.get("spans", [])]
                    if sizes and min(sizes) >= body_size - 1:
                        headings.append(DetectedHeading(
                            text=text[:80],
                            page=page_num,
                            method="isolation",
                            confidence=0.5,
                            font_size=sizes[0] if sizes else None,
                        ))
    
    return headings


def detect_combined(doc, body_size: float) -> list[DetectedHeading]:
    """Combine multiple signals for higher confidence detection."""
    headings = []
    
    for page_num, page in enumerate(doc):
        data = page.get_text("dict")
        blocks = [b for b in data["blocks"] if b["type"] == 0]
        
        for block in blocks:
            lines = block.get("lines", [])
            
            for line in lines:
                text = "".join(s["text"] for s in line.get("spans", [])).strip()
                if not text or len(text) < 3:
                    continue
                
                # Gather signals
                spans = line.get("spans", [])
                sizes = [s["size"] for s in spans]
                avg_size = sum(sizes) / len(sizes) if sizes else body_size
                
                is_larger = avg_size > body_size * 1.2
                is_bold = all(s["flags"] & 16 for s in spans)
                is_short = len(text) < 80
                is_isolated = len(lines) <= 2
                
                # Score based on signals
                score = 0
                if is_larger:
                    score += 0.4
                if is_bold:
                    score += 0.3
                if is_short and is_isolated:
                    score += 0.2
                if text[0].isupper():
                    score += 0.1
                
                if score >= 0.5:
                    headings.append(DetectedHeading(
                        text=text[:80],
                        page=page_num,
                        method="combined",
                        confidence=score,
                        font_size=avg_size,
                        is_bold=is_bold,
                    ))
    
    return headings


def try_pymupdf4llm(pdf_path: str) -> list[str]:
    """Try pymupdf4llm and extract its detected headings from markdown."""
    try:
        import pymupdf4llm
        md = pymupdf4llm.to_markdown(pdf_path)
        
        # Extract lines that start with #
        headings = []
        for line in md.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                # Remove # prefix and clean
                level = len(line) - len(line.lstrip("#"))
                text = line.lstrip("#").strip()
                if text:
                    headings.append(f"H{level}: {text[:60]}")
        
        return headings
    except ImportError:
        return ["(pymupdf4llm not installed)"]
    except Exception as e:
        return [f"(error: {e})"]


def analyze_headings(pdf_path: str, max_pages: int = 20):
    """Run all detection methods and compare."""
    
    print(f"{'='*70}")
    print(f"HEADING DETECTION COMPARISON: {pdf_path}")
    print(f"{'='*70}")
    print()
    
    doc = fitz.open(pdf_path)
    
    # Limit pages for speed
    if doc.page_count > max_pages:
        print(f"Note: Analyzing first {max_pages} of {doc.page_count} pages")
    
    # Determine body font size
    body_size = get_body_font_size(doc)
    print(f"Detected body font size: {body_size}")
    print()
    
    # Run each method
    methods = {
        "font_size": detect_by_font_size(doc, body_size),
        "bold": detect_by_bold(doc),
        "isolation": detect_by_isolation(doc, body_size),
        "combined": detect_combined(doc, body_size),
    }
    
    doc.close()
    
    # Also try pymupdf4llm
    p4llm_headings = try_pymupdf4llm(pdf_path)
    
    # Summary
    print(f"{'='*70}")
    print("DETECTION COUNTS")
    print(f"{'='*70}")
    print()
    
    for method, headings in methods.items():
        print(f"{method:<15}: {len(headings)} potential headings")
    print(f"{'pymupdf4llm':<15}: {len(p4llm_headings)} headings in markdown")
    print()
    
    # Show results from each method
    for method, headings in methods.items():
        print(f"{'='*70}")
        print(f"METHOD: {method.upper()}")
        print(f"{'='*70}")
        
        # Group by page
        by_page = {}
        for h in headings[:50]:  # Limit output
            by_page.setdefault(h.page, []).append(h)
        
        for page in sorted(by_page.keys())[:10]:  # First 10 pages
            print(f"\nPage {page}:")
            for h in by_page[page]:
                conf = f"[{h.confidence:.1f}]"
                size = f"sz={h.font_size:.1f}" if h.font_size else ""
                bold = "bold" if h.is_bold else ""
                print(f"  {conf} {h.text:<50} {size} {bold}")
        
        if len(by_page) > 10:
            print(f"\n  ... ({len(headings)} total across {len(by_page)} pages)")
        print()
    
    # pymupdf4llm results
    print(f"{'='*70}")
    print("PYMUPDF4LLM MARKDOWN HEADINGS")
    print(f"{'='*70}")
    print()
    for h in p4llm_headings[:30]:
        print(f"  {h}")
    if len(p4llm_headings) > 30:
        print(f"  ... ({len(p4llm_headings)} total)")
    
    # Analysis guidance
    print()
    print(f"{'='*70}")
    print("EVALUATION QUESTIONS")
    print(f"{'='*70}")
    print("""
Look at the results above and consider:

1. ACCURACY
   - Which method found the real chapter/section headings?
   - Which had the most false positives (non-headings detected)?
   - Which missed obvious headings (false negatives)?

2. CONFIDENCE CALIBRATION
   - Do high-confidence detections correspond to real headings?
   - Is there a good threshold to filter noise?

3. PHILOSOPHY TEXT PATTERNS
   - Do philosophy texts use consistent heading styles?
   - Are there unusual patterns (e.g., Greek text, special formatting)?

4. RECOMMENDATION
   - Which method (or combination) works best?
   - Should we use pymupdf4llm directly if its detection is good enough?
   - What post-processing is needed?
""")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUsage:")
        print("  uv run python spikes/03_heading_detection.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)
    
    analyze_headings(pdf_path)


if __name__ == "__main__":
    main()
