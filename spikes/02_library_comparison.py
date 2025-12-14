#!/usr/bin/env python3
"""
Spike 02: Compare PDF Extraction Libraries

PURPOSE: Empirically compare different PDF libraries on the same documents
         before committing to an architecture.

LIBRARIES TO TEST:
- PyMuPDF (fitz) - Our current assumption
- pdfplumber - Good table detection, MIT license
- pypdf - Pure Python, BSD license
- pymupdf4llm - PyMuPDF extension for LLM use cases
- marker (optional) - ML-based, good for complex layouts

RUN:
  uv run python spikes/02_library_comparison.py sample.pdf

QUESTIONS TO ANSWER:
1. Which library gives the best text extraction quality?
2. Which preserves structure best (headings, paragraphs)?
3. Which handles footnotes/page-bottom text best?
4. What are the speed differences?
5. What are the dependency/license tradeoffs?
"""

import sys
import time
from pathlib import Path
from dataclasses import dataclass

# We'll try to import each library and gracefully handle missing ones
LIBRARIES = {}

try:
    import fitz
    LIBRARIES["pymupdf"] = fitz
except ImportError:
    pass

try:
    import pdfplumber
    LIBRARIES["pdfplumber"] = pdfplumber
except ImportError:
    pass

try:
    import pypdf
    LIBRARIES["pypdf"] = pypdf
except ImportError:
    pass

try:
    import pymupdf4llm
    LIBRARIES["pymupdf4llm"] = pymupdf4llm
except ImportError:
    pass


@dataclass
class ExtractionResult:
    """Results from a single library's extraction."""
    library: str
    time_seconds: float
    total_chars: int
    total_pages: int
    sample_text: str  # First 500 chars
    has_font_info: bool
    has_position_info: bool
    has_page_labels: bool
    error: str | None = None


def extract_with_pymupdf(pdf_path: str) -> ExtractionResult:
    """Extract using PyMuPDF."""
    start = time.time()
    
    doc = fitz.open(pdf_path)
    all_text = []
    has_labels = False
    
    for page in doc:
        # Check for page labels
        if page.get_label() and page.get_label() != str(page.number + 1):
            has_labels = True
        
        # Extract text
        all_text.append(page.get_text())
    
    doc.close()
    elapsed = time.time() - start
    
    full_text = "\n".join(all_text)
    
    return ExtractionResult(
        library="pymupdf",
        time_seconds=elapsed,
        total_chars=len(full_text),
        total_pages=len(all_text),
        sample_text=full_text[:500],
        has_font_info=True,  # via get_text("dict")
        has_position_info=True,  # bbox available
        has_page_labels=has_labels,
    )


def extract_with_pdfplumber(pdf_path: str) -> ExtractionResult:
    """Extract using pdfplumber."""
    start = time.time()
    
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            all_text.append(text)
    
    elapsed = time.time() - start
    full_text = "\n".join(all_text)
    
    return ExtractionResult(
        library="pdfplumber",
        time_seconds=elapsed,
        total_chars=len(full_text),
        total_pages=len(all_text),
        sample_text=full_text[:500],
        has_font_info=True,  # via chars property
        has_position_info=True,  # bbox available
        has_page_labels=False,  # No direct support
    )


def extract_with_pypdf(pdf_path: str) -> ExtractionResult:
    """Extract using pypdf."""
    start = time.time()
    
    reader = pypdf.PdfReader(pdf_path)
    all_text = []
    
    for page in reader.pages:
        text = page.extract_text() or ""
        all_text.append(text)
    
    elapsed = time.time() - start
    full_text = "\n".join(all_text)
    
    return ExtractionResult(
        library="pypdf",
        time_seconds=elapsed,
        total_chars=len(full_text),
        total_pages=len(all_text),
        sample_text=full_text[:500],
        has_font_info=False,  # Limited
        has_position_info=False,  # Limited
        has_page_labels=False,  # Can access but complex
    )


def extract_with_pymupdf4llm(pdf_path: str) -> ExtractionResult:
    """Extract using pymupdf4llm (Markdown output)."""
    start = time.time()
    
    # pymupdf4llm returns markdown directly
    md_text = pymupdf4llm.to_markdown(pdf_path)
    
    elapsed = time.time() - start
    
    # Count pages by opening with fitz
    doc = fitz.open(pdf_path)
    page_count = doc.page_count
    doc.close()
    
    return ExtractionResult(
        library="pymupdf4llm",
        time_seconds=elapsed,
        total_chars=len(md_text),
        total_pages=page_count,
        sample_text=md_text[:500],
        has_font_info=False,  # Abstracted away
        has_position_info=False,  # Abstracted away
        has_page_labels=False,  # Not exposed
    )


def compare_libraries(pdf_path: str):
    """Run all available libraries and compare results."""
    
    print(f"{'='*70}")
    print(f"LIBRARY COMPARISON: {pdf_path}")
    print(f"{'='*70}")
    print()
    
    # Check what's available
    print("Available libraries:")
    for name in LIBRARIES:
        print(f"  ✓ {name}")
    
    missing = {"pymupdf", "pdfplumber", "pypdf", "pymupdf4llm"} - set(LIBRARIES.keys())
    if missing:
        print(f"  ✗ Not installed: {', '.join(missing)}")
        print()
        print("To install missing libraries:")
        print("  uv add pymupdf pdfplumber pypdf pymupdf4llm")
    print()
    
    # Run extractions
    results = []
    
    extractors = {
        "pymupdf": extract_with_pymupdf,
        "pdfplumber": extract_with_pdfplumber,
        "pypdf": extract_with_pypdf,
        "pymupdf4llm": extract_with_pymupdf4llm,
    }
    
    for name, extractor in extractors.items():
        if name not in LIBRARIES:
            continue
            
        print(f"Running {name}...", end=" ", flush=True)
        try:
            result = extractor(pdf_path)
            results.append(result)
            print(f"done ({result.time_seconds:.2f}s)")
        except Exception as e:
            print(f"ERROR: {e}")
            results.append(ExtractionResult(
                library=name,
                time_seconds=0,
                total_chars=0,
                total_pages=0,
                sample_text="",
                has_font_info=False,
                has_position_info=False,
                has_page_labels=False,
                error=str(e),
            ))
    
    print()
    
    # Summary table
    print(f"{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print()
    print(f"{'Library':<15} {'Time':>8} {'Chars':>10} {'Pages':>6} {'Font':>5} {'Pos':>5} {'Labels':>7}")
    print("-" * 70)
    
    for r in results:
        if r.error:
            print(f"{r.library:<15} ERROR: {r.error[:40]}")
        else:
            print(f"{r.library:<15} {r.time_seconds:>7.2f}s {r.total_chars:>10,} {r.total_pages:>6} "
                  f"{'✓' if r.has_font_info else '✗':>5} "
                  f"{'✓' if r.has_position_info else '✗':>5} "
                  f"{'✓' if r.has_page_labels else '✗':>7}")
    
    print()
    
    # Character count comparison (quality indicator)
    print(f"{'='*70}")
    print("TEXT EXTRACTION COMPARISON")
    print(f"{'='*70}")
    print()
    
    if len(results) >= 2:
        char_counts = [(r.library, r.total_chars) for r in results if not r.error]
        char_counts.sort(key=lambda x: -x[1])
        
        if char_counts:
            max_chars = char_counts[0][1]
            print("Character extraction (more = better, usually):")
            for lib, chars in char_counts:
                pct = (chars / max_chars * 100) if max_chars > 0 else 0
                bar = "█" * int(pct / 5)
                print(f"  {lib:<15} {chars:>10,} ({pct:5.1f}%) {bar}")
    
    print()
    
    # Sample text comparison
    print(f"{'='*70}")
    print("SAMPLE TEXT (first 300 chars from each)")
    print(f"{'='*70}")
    
    for r in results:
        if r.error:
            continue
        print(f"\n--- {r.library} ---")
        print(r.sample_text[:300])
        print()
    
    # Recommendations
    print(f"{'='*70}")
    print("ANALYSIS NOTES")
    print(f"{'='*70}")
    print("""
Compare the sample text above to evaluate:

1. TEXT QUALITY
   - Which has fewer garbled characters?
   - Which preserves word boundaries correctly?
   - Which handles special characters (em-dashes, quotes)?

2. STRUCTURE PRESERVATION  
   - Does pymupdf4llm's markdown look good?
   - Are paragraphs preserved or merged?
   
3. SPEED vs FEATURES
   - pypdf is usually fastest but has fewest features
   - pymupdf is fast with full features
   - pdfplumber is slower but has good table detection
   - pymupdf4llm adds overhead but gives markdown directly

4. FOR SCHOLARLY DOCUMENTS
   - Font info needed for heading detection? → pymupdf, pdfplumber
   - Position info needed for footnotes? → pymupdf, pdfplumber
   - Page labels needed for citations? → pymupdf only
   - Just need good markdown? → pymupdf4llm might be enough
""")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUsage:")
        print("  uv run python spikes/02_library_comparison.py <pdf_path>")
        print()
        print("Install libraries to compare:")
        print("  uv add pymupdf pdfplumber pypdf pymupdf4llm")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)
    
    if not LIBRARIES:
        print("No PDF libraries installed!")
        print("Run: uv add pymupdf pdfplumber pypdf pymupdf4llm")
        sys.exit(1)
    
    compare_libraries(pdf_path)


if __name__ == "__main__":
    main()
