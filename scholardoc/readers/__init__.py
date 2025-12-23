"""PDF and document reading module.

See SPEC.md for design, ADR-001 for library choice (PyMuPDF).
"""

from scholardoc.readers.pdf_reader import (
    OutlineEntry,
    PageData,
    PDFReader,
    RawDocument,
    TextBlock,
    detect_body_font_size,
    estimate_document_type,
    get_font_statistics,
    has_abstract,
    has_toc_indicators,
)

__all__ = [
    # Classes
    "PDFReader",
    "RawDocument",
    "PageData",
    "TextBlock",
    "OutlineEntry",
    # Utility functions
    "get_font_statistics",
    "detect_body_font_size",
    "has_toc_indicators",
    "has_abstract",
    "estimate_document_type",
]
