"""
PDF Reader using PyMuPDF (fitz).

Extracts text, positions, fonts, and structure from PDFs.
Based on ADR-001 findings: PyMuPDF is 32-57x faster than alternatives.

This module provides raw extraction - structure detection is handled
by the extractors module (CascadingExtractor).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import fitz  # PyMuPDF

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(frozen=True)
class TextBlock:
    """A block of text with position and font information.

    Extracted from PyMuPDF's get_text("dict") output.
    Used for heading detection and layout analysis.
    """

    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    font_name: str
    font_size: float
    is_bold: bool
    is_italic: bool
    color: int  # RGB packed as int
    page_index: int

    @property
    def width(self) -> float:
        """Block width."""
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        """Block height."""
        return self.y1 - self.y0


@dataclass
class PageData:
    """Raw data extracted from a single PDF page."""

    index: int  # 0-based page index
    label: str  # Page label (e.g., "42", "xiv", "A64")
    width: float
    height: float
    text: str  # Full text of page
    blocks: list[TextBlock]  # Text blocks with positions
    has_images: bool


@dataclass
class OutlineEntry:
    """An entry from the PDF outline/bookmarks.

    From PyMuPDF's doc.get_toc() which returns [level, title, page_num].
    """

    level: int  # 1=chapter, 2=section, etc.
    title: str
    page_index: int  # 0-based page index


@dataclass
class RawDocument:
    """Raw extracted data from a PDF, before structure detection.

    This intermediate representation contains everything needed
    for structure extraction and document building.
    """

    source_path: Path
    page_count: int
    pages: list[PageData]
    outline: list[OutlineEntry]
    metadata: dict[str, str | None]

    # Derived properties for quick access
    _text_cache: str | None = field(default=None, repr=False)
    _page_positions: list[tuple[int, int]] | None = field(default=None, repr=False)

    @property
    def text(self) -> str:
        """Full document text (cached)."""
        if self._text_cache is None:
            parts = []
            for page in self.pages:
                if page.text:
                    parts.append(page.text)
            self._text_cache = "\n\n".join(parts)
        return self._text_cache

    @property
    def page_positions(self) -> list[tuple[int, int]]:
        """Start and end positions for each page in the full text.

        Returns list of (start, end) tuples.
        """
        if self._page_positions is None:
            positions = []
            current_pos = 0
            for page in self.pages:
                page_len = len(page.text) if page.text else 0
                positions.append((current_pos, current_pos + page_len))
                # Add 2 for the \n\n separator
                current_pos += page_len + 2
            self._page_positions = positions
        return self._page_positions

    def page_for_position(self, pos: int) -> int | None:
        """Find page index containing a text position."""
        for i, (start, end) in enumerate(self.page_positions):
            if start <= pos < end:
                return i
        return None

    def position_to_page(self, page_index: int) -> int:
        """Get the text position where a page starts."""
        if 0 <= page_index < len(self.page_positions):
            return self.page_positions[page_index][0]
        return 0

    @property
    def has_outline(self) -> bool:
        """Whether the PDF has an outline/bookmarks."""
        return len(self.outline) > 0

    @property
    def first_pages_text(self) -> str:
        """Text from first 20 pages (for profile detection)."""
        return "\n\n".join(p.text for p in self.pages[:20] if p.text)


class PDFReader:
    """Extracts raw data from PDFs using PyMuPDF.

    Usage:
        reader = PDFReader()
        raw = reader.read("/path/to/file.pdf")
        # raw.pages, raw.outline, raw.text, etc.
    """

    def __init__(
        self,
        *,
        extract_images: bool = False,
        merge_blocks: bool = True,
    ):
        """Initialize the PDF reader.

        Args:
            extract_images: Whether to mark pages with images.
            merge_blocks: Whether to merge adjacent text blocks.
        """
        self.extract_images = extract_images
        self.merge_blocks = merge_blocks

    def read(self, path: str | Path) -> RawDocument:
        """Read a PDF file and extract raw data.

        Args:
            path: Path to PDF file.

        Returns:
            RawDocument with pages, outline, metadata.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file is not a valid PDF.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")

        try:
            doc = fitz.open(path)
        except Exception as e:
            raise ValueError(f"Failed to open PDF: {e}") from e

        try:
            # Extract pages
            pages = list(self._extract_pages(doc))

            # Extract outline
            outline = self._extract_outline(doc)

            # Extract metadata
            metadata = self._extract_metadata(doc)

            return RawDocument(
                source_path=path,
                page_count=len(doc),
                pages=pages,
                outline=outline,
                metadata=metadata,
            )
        finally:
            doc.close()

    def _extract_pages(self, doc: fitz.Document) -> Iterator[PageData]:
        """Extract data from each page."""
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            yield self._extract_page(page, page_idx)

    def _extract_page(self, page: fitz.Page, page_idx: int) -> PageData:
        """Extract data from a single page."""
        # Get page label (e.g., "42", "xiv")
        label = page.get_label() or str(page_idx + 1)

        # Get dimensions
        rect = page.rect
        width = rect.width
        height = rect.height

        # Extract text blocks with positions and fonts
        blocks = self._extract_blocks(page, page_idx)

        # Get plain text (for the full document text)
        text = page.get_text("text").strip()

        # Check for images
        has_images = self.extract_images and bool(page.get_images())

        return PageData(
            index=page_idx,
            label=label,
            width=width,
            height=height,
            text=text,
            blocks=blocks,
            has_images=has_images,
        )

    def _extract_blocks(self, page: fitz.Page, page_idx: int) -> list[TextBlock]:
        """Extract text blocks with position and font info."""
        blocks = []

        # Get detailed text extraction with font info
        page_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        for block in page_dict.get("blocks", []):
            # Skip image blocks
            if block.get("type") != 0:
                continue

            # Process text blocks
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue

                    font = span.get("font", "")
                    flags = span.get("flags", 0)

                    blocks.append(
                        TextBlock(
                            text=text,
                            x0=span.get("bbox", [0, 0, 0, 0])[0],
                            y0=span.get("bbox", [0, 0, 0, 0])[1],
                            x1=span.get("bbox", [0, 0, 0, 0])[2],
                            y1=span.get("bbox", [0, 0, 0, 0])[3],
                            font_name=font,
                            font_size=span.get("size", 0),
                            is_bold=bool(flags & 2**4),  # Bold flag
                            is_italic=bool(flags & 2**1),  # Italic flag
                            color=span.get("color", 0),
                            page_index=page_idx,
                        )
                    )

        if self.merge_blocks:
            blocks = self._merge_adjacent_blocks(blocks)

        return blocks

    def _merge_adjacent_blocks(self, blocks: list[TextBlock]) -> list[TextBlock]:
        """Merge adjacent text blocks with same formatting.

        Adjacent blocks on the same line with matching fonts are merged
        to form complete lines/paragraphs.
        """
        if not blocks:
            return []

        merged = []
        current = blocks[0]

        for block in blocks[1:]:
            # Check if blocks are adjacent and have same formatting
            same_line = abs(block.y0 - current.y0) < 2
            same_font = (
                block.font_name == current.font_name
                and abs(block.font_size - current.font_size) < 0.5
                and block.is_bold == current.is_bold
            )
            adjacent = block.x0 - current.x1 < 20  # Small gap

            if same_line and same_font and adjacent:
                # Merge blocks
                current = TextBlock(
                    text=current.text + " " + block.text,
                    x0=current.x0,
                    y0=min(current.y0, block.y0),
                    x1=block.x1,
                    y1=max(current.y1, block.y1),
                    font_name=current.font_name,
                    font_size=current.font_size,
                    is_bold=current.is_bold,
                    is_italic=current.is_italic,
                    color=current.color,
                    page_index=current.page_index,
                )
            else:
                merged.append(current)
                current = block

        merged.append(current)
        return merged

    def _extract_outline(self, doc: fitz.Document) -> list[OutlineEntry]:
        """Extract PDF outline/bookmarks."""
        outline = []

        try:
            toc = doc.get_toc()
            for level, title, page_num in toc:
                # page_num is 1-based, convert to 0-based
                outline.append(
                    OutlineEntry(
                        level=level,
                        title=title.strip(),
                        page_index=max(0, page_num - 1),
                    )
                )
        except Exception:
            # Some PDFs have malformed outlines
            pass

        return outline

    def _extract_metadata(self, doc: fitz.Document) -> dict[str, str | None]:
        """Extract PDF metadata."""
        meta = doc.metadata
        return {
            "title": meta.get("title") or None,
            "author": meta.get("author") or None,
            "subject": meta.get("subject") or None,
            "creator": meta.get("creator") or None,
            "producer": meta.get("producer") or None,
            "creation_date": meta.get("creationDate") or None,
            "mod_date": meta.get("modDate") or None,
        }


# ============================================================
# Utility functions for analyzing extracted data
# ============================================================


def get_font_statistics(raw: RawDocument) -> dict[str, float]:
    """Analyze font size distribution across document.

    Returns stats useful for heading detection.
    """
    sizes = []
    for page in raw.pages:
        for block in page.blocks:
            sizes.append(block.font_size)

    if not sizes:
        return {}

    sizes.sort()
    n = len(sizes)

    return {
        "min": min(sizes),
        "max": max(sizes),
        "median": sizes[n // 2],
        "mean": sum(sizes) / n,
        "p25": sizes[n // 4],
        "p75": sizes[3 * n // 4],
    }


def detect_body_font_size(raw: RawDocument) -> float:
    """Detect the most common (body text) font size."""
    from collections import Counter

    sizes = []
    for page in raw.pages:
        for block in page.blocks:
            # Round to 0.5pt for grouping
            sizes.append(round(block.font_size * 2) / 2)

    if not sizes:
        return 12.0  # Default

    counter = Counter(sizes)
    return counter.most_common(1)[0][0]


def has_toc_indicators(raw: RawDocument) -> bool:
    """Check if document likely has a table of contents."""
    first_text = raw.first_pages_text.lower()
    indicators = [
        "table of contents",
        "contents",
        "inhalt",  # German
        "sommaire",  # French
    ]
    return any(ind in first_text for ind in indicators)


def has_abstract(raw: RawDocument) -> bool:
    """Check if document has an abstract (article indicator)."""
    first_text = raw.first_pages_text.lower()
    return "abstract" in first_text


def estimate_document_type(raw: RawDocument) -> str:
    """Estimate document type from indicators.

    Returns one of: book, article, essay, report, generic
    """
    page_count = raw.page_count
    has_toc = has_toc_indicators(raw)
    has_outline = raw.has_outline

    # Score each type
    scores = {
        "book": 0.0,
        "article": 0.0,
        "essay": 0.0,
        "report": 0.0,
    }

    # Page count indicators
    if page_count > 100:
        scores["book"] += 0.4
    elif page_count < 30:
        scores["article"] += 0.3
        scores["essay"] += 0.2
    elif page_count < 60:
        scores["essay"] += 0.2
        scores["report"] += 0.2

    # ToC presence
    if has_toc:
        scores["book"] += 0.3
        scores["report"] += 0.2

    # Outline presence
    if has_outline:
        scores["book"] += 0.2
        scores["report"] += 0.1

    # Abstract (article indicator)
    if has_abstract(raw):
        scores["article"] += 0.4

    # Check for numbered sections (report indicator)
    if re.search(r"\d+\.\d+", raw.first_pages_text):
        scores["report"] += 0.3

    # Pick best
    best_type = max(scores, key=lambda k: scores[k])
    if scores[best_type] < 0.3:
        return "generic"
    return best_type
