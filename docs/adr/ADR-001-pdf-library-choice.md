# ADR-001: PDF Extraction Library Choice

**Status:** PROPOSED - Pending Spike Validation  
**Date:** December 2025  
**Decision Makers:** TBD  
**Validation Required:** Run `spikes/02_library_comparison.py` on sample PDFs before finalizing

---

## Context

ScholarDoc needs a Python library for extracting text, structure, and metadata from PDF files. The choice of library affects:

- Extraction quality (text accuracy, layout preservation)
- Performance (speed, memory usage)
- Maintenance (active development, documentation)
- Features (table detection, font information, OCR support)
- Dependencies (size, licensing)

**This decision should be validated empirically before implementation begins.**

---

## Options Considered

### Option 1: PyMuPDF (fitz)

**Description:** Python bindings to MuPDF, a lightweight PDF/XPS viewer library.

**Pros:**
- Very fast (C-based core)
- Excellent text extraction with position data
- Font and style information available
- Active maintenance, good documentation
- Supports PDF, XPS, EPUB, FB2, and images
- Optional OCR integration (Tesseract)
- PyMuPDF4LLM extension for enhanced layout analysis

**Cons:**
- AGPL license (or commercial license required)
- Large binary size
- Some advanced features require Pro version

**License:** AGPL-3.0 (open source) or commercial

### Option 2: pypdf (formerly PyPDF2)

**Description:** Pure Python PDF library for reading, writing, and manipulating PDFs.

**Pros:**
- Pure Python (no binary dependencies)
- BSD license
- Simple API for basic extraction
- Good for PDF manipulation (merge, split)

**Cons:**
- Slower than PyMuPDF
- Less accurate text extraction
- Limited layout/structure detection
- No font/style information
- No table detection

**License:** BSD-3-Clause

### Option 3: pdfplumber

**Description:** Built on pdfminer.six, focused on extracting information from PDFs.

**Pros:**
- Good table detection
- Character-level positioning
- Visual debugging tools
- MIT license
- Pure Python

**Cons:**
- Slower than PyMuPDF
- Memory intensive for large documents
- Less active maintenance than PyMuPDF

**License:** MIT

### Option 4: Unstructured

**Description:** Library for preprocessing documents for ML/NLP.

**Pros:**
- Handles many formats (PDF, DOCX, HTML, etc.)
- ML-based layout analysis
- Good table extraction
- RAG-focused design

**Cons:**
- Heavy dependencies
- Requires API for best results
- Less control over extraction details
- Opinionated output format

**License:** Apache-2.0

### Option 5: docling (IBM)

**Description:** IBM's document parsing library for AI applications.

**Pros:**
- ML-based layout analysis
- Good scientific paper support
- Table and figure extraction
- Apache-2.0 license

**Cons:**
- Newer, less battle-tested
- Heavy ML dependencies
- Less control over details

**License:** Apache-2.0

---

## Decision

**Recommended:** PyMuPDF (fitz) as primary extraction library

**Rationale:**

1. **Quality:** PyMuPDF provides the most accurate text extraction with full position and style information, which is essential for heading detection and footnote extraction.

2. **Performance:** As a C-based library, PyMuPDF is significantly faster than pure Python alternatives, important for batch processing.

3. **Flexibility:** The library provides low-level access to PDF internals, allowing us to implement custom logic for scholarly document features.

4. **Ecosystem:** PyMuPDF4LLM provides additional features specifically designed for LLM/RAG use cases.

5. **EPUB support:** Built-in EPUB support aligns with Phase 3 plans.

**License consideration:** The AGPL license requires that derivative works also be AGPL. For a library intended to be integrated into other projects:
- If ScholarDoc is open source (AGPL-compatible), this is fine
- If commercial use is needed, commercial PyMuPDF license is available
- Alternative: Use pypdf for basic extraction, add PyMuPDF as optional dependency

---

## Consequences

### Positive
- High-quality text extraction from day one
- Fast processing for large corpora
- PyMuPDF4LLM available for enhanced features
- Single library covers PDF and EPUB

### Negative
- AGPL license limits proprietary distribution
- Binary dependency increases package size
- Some features require PyMuPDF Pro

### Mitigations
- Document license implications clearly
- Offer pypdf fallback for AGPL-incompatible uses (lower quality)
- Evaluate PyMuPDF Pro features if needed

---

## Implementation Notes

```python
# Basic usage
import fitz  # PyMuPDF

doc = fitz.open("document.pdf")
for page in doc:
    # Get text blocks with position
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if block["type"] == 0:  # Text block
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"]
                    font = span["font"]
                    size = span["size"]
                    bbox = span["bbox"]

# With PyMuPDF4LLM for enhanced layout
import pymupdf4llm
md_text = pymupdf4llm.to_markdown("document.pdf")
```

---

## References

- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [PyMuPDF4LLM](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/)
- [pypdf Documentation](https://pypdf.readthedocs.io/)
- [Comparative PDF Parsing Study](https://arxiv.org/html/2410.09871v1)
