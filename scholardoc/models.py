"""
Data models for ScholarDoc.

Core representation using clean text with position-based annotations.
See docs/design/CORE_REPRESENTATION.md for full design documentation.

Key insight: The `text` field contains semantic content (what the author wrote).
Artifacts like footnote markers and page numbers are REMOVED but their positions
are RECORDED as annotations.

Example:
    Original PDF: "The beautiful¹ morning. 64 The sublime..."
                             ↑              ↑
                        footnote        page number

    Our representation:
        text = "The beautiful morning. The sublime..."
        footnote_refs = [FootnoteRef(position=13, marker="¹", target_id="fn1")]
        pages = [PageSpan(start=0, end=22, label="63"), PageSpan(start=23, ..., label="64")]
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# Enumerations
# ═══════════════════════════════════════════════════════════════════════════════


class DocumentType(Enum):
    """Classification of document types for profile-based processing."""

    BOOK = "book"  # Multi-chapter with ToC
    ARTICLE = "article"  # Academic article with abstract
    ESSAY = "essay"  # Essay with subheadings
    REPORT = "report"  # Technical report with sections
    GENERIC = "generic"  # Unclassified


class NoteType(Enum):
    """Type of note."""

    FOOTNOTE = "footnote"  # Page-bottom notes
    ENDNOTE = "endnote"  # End-of-section/book notes
    TRANSLATOR = "translator"  # Translator's notes
    EDITOR = "editor"  # Editor's notes


class NoteSource(Enum):
    """Who wrote the note."""

    AUTHOR = "author"
    TRANSLATOR = "translator"
    EDITOR = "editor"
    UNKNOWN = "unknown"


class ChunkStrategy(Enum):
    """Strategy for generating RAG chunks."""

    SEMANTIC = "semantic"  # By paragraph/section boundaries
    FIXED_SIZE = "fixed_size"  # Fixed token count
    PAGE = "page"  # One chunk per page
    SECTION = "section"  # One chunk per section


class QualityLevel(Enum):
    """OCR quality classification."""

    GOOD = "good"  # Clean text, high confidence
    MARGINAL = "marginal"  # Some issues, usable
    BAD = "bad"  # Significant problems, may need re-OCR


class OCRErrorType(Enum):
    """Classification of OCR errors for analysis and validation."""

    UNKNOWN = "unknown"  # Unclassified error
    CHARACTER_SUBSTITUTION = "character_substitution"  # e.g., 'l' → 'I', 'tbe' → 'the'
    SUBSTITUTION = "substitution"  # Word-level substitution
    UMLAUT = "umlaut"  # Missing or incorrect diacritics
    HYPHENATION = "hyphenation"  # Line-break hyphenation issues
    SPACING = "spacing"  # Incorrect word spacing
    PUNCTUATION = "punctuation"  # Punctuation recognition errors


# ═══════════════════════════════════════════════════════════════════════════════
# Base Span/Annotation Types
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class Span:
    """Base class for position spans in text."""

    start: int  # Start position in text (inclusive)
    end: int  # End position in text (exclusive)

    def __post_init__(self):
        if self.start < 0:
            raise ValueError(f"start must be >= 0, got {self.start}")
        if self.end < self.start:
            raise ValueError(f"end ({self.end}) must be >= start ({self.start})")

    def __len__(self) -> int:
        return self.end - self.start

    def contains(self, position: int) -> bool:
        """Check if position is within this span."""
        return self.start <= position < self.end

    def overlaps(self, other: Span) -> bool:
        """Check if this span overlaps with another."""
        return self.start < other.end and other.start < self.end


# ═══════════════════════════════════════════════════════════════════════════════
# Position-Based Annotations (reference positions in text)
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class FootnoteRef:
    """A footnote marker that was removed from text."""

    position: int  # Where in text the marker was (between chars)
    marker: str  # The original marker ("¹", "*", "†", "1")
    target_id: str  # Reference to notes dict (e.g., "fn1")


@dataclass(frozen=True)
class EndnoteRef:
    """An endnote marker that was removed from text."""

    position: int  # Where in text the marker was
    marker: str  # The original marker
    target_id: str  # Reference to notes dict (e.g., "en1")


@dataclass(frozen=True)
class CitationRef:
    """An in-text citation."""

    start: int  # Start position in text
    end: int  # End position in text
    original: str  # "(Heidegger, 1927)" or "[1]"
    parsed: ParsedCitation | None = None  # Structured if parseable
    bib_entry_id: str | None = None  # Link to bibliography entry


@dataclass(frozen=True)
class ParsedCitation:
    """Structured citation data."""

    authors: list[str] = field(default_factory=list)
    year: str | None = None
    pages: str | None = None  # "pp. 45-67"
    style: str = "unknown"  # "chicago", "mla", "apa", "numeric"


@dataclass(frozen=True)
class CrossRef:
    """A cross-reference to another part of the document."""

    start: int  # Start position in text
    end: int  # End position in text
    original: str  # "see p. 45", "see §3.2", "see above"
    target_page: str | None = None
    target_section: str | None = None
    resolved_position: int | None = None  # If we can resolve "see above"


# ═══════════════════════════════════════════════════════════════════════════════
# Structural Spans (ranges in text)
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class PageSpan(Span):
    """A page boundary in the text."""

    label: str = ""  # "64", "xiv", "A64/B93"
    index: int = 0  # 0-based page index in source PDF


@dataclass(frozen=True)
class SectionSpan(Span):
    """A section/chapter boundary in the text."""

    title: str = ""
    level: int = 1  # 1=chapter, 2=section, 3=subsection
    confidence: float = 1.0  # Detection confidence (0.0-1.0)


@dataclass(frozen=True)
class ParagraphSpan(Span):
    """A paragraph boundary in the text."""

    pass


@dataclass(frozen=True)
class BlockQuoteSpan(Span):
    """An indented quotation in the text."""

    indentation_level: int = 1


# ═══════════════════════════════════════════════════════════════════════════════
# Referenced Content (actual footnote/endnote text)
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class Note:
    """The actual content of a footnote/endnote."""

    id: str  # "fn1", "en23"
    text: str  # The note content
    note_type: NoteType = NoteType.FOOTNOTE
    page_label: str = ""  # Where the note appears
    source: NoteSource = NoteSource.AUTHOR


@dataclass
class BibEntry:
    """A parsed bibliography entry."""

    id: str  # Internal reference id
    raw: str  # Original text
    authors: list[str] = field(default_factory=list)
    title: str | None = None
    year: str | None = None
    source: str | None = None  # Journal, book, etc.
    pages: str | None = None
    doi: str | None = None
    url: str | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# Table of Contents
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class ToCEntry:
    """An entry from the Table of Contents."""

    title: str
    page_label: str = ""  # "5", "xiv", etc.
    level: int = 1  # 1=chapter, 2=section, etc.
    children: list[ToCEntry] = field(default_factory=list)
    resolved_position: int | None = None  # Position in text if resolved


@dataclass
class TableOfContents:
    """Parsed table of contents from document."""

    entries: list[ToCEntry] = field(default_factory=list)
    page_range: tuple[int, int] = (0, 0)  # Where ToC appears (page indices)
    confidence: float = 0.0  # Parsing confidence


# ═══════════════════════════════════════════════════════════════════════════════
# Quality Information
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class OCRCorrectionRecord:
    """Record of an OCR correction (for debugging/analysis)."""

    page_index: int
    original_word: str
    corrected_word: str
    position: int  # Character position in page text
    error_type: OCRErrorType = OCRErrorType.UNKNOWN
    confidence: float = 0.0  # Detection confidence
    method: str = ""  # e.g., "reocr_doctr", "reocr_tesseract"


@dataclass
class PageQuality:
    """Quality assessment for a single page."""

    page_index: int
    page_label: str
    quality: QualityLevel
    confidence: float  # OCR confidence if available
    issues: list[str] = field(default_factory=list)  # Specific issues detected
    words_checked: int = 0  # Total words analyzed
    errors_detected: int = 0  # Errors found before correction
    corrections_made: int = 0  # Successful corrections applied


@dataclass
class OCRSourceInfo:
    """Information about the OCR engine that produced the embedded text.

    This helps with:
    - Traceability: knowing what produced the text layer
    - Analysis: comparing error patterns across OCR engines
    - Debugging: identifying engine-specific issues
    """

    engine: str = "unknown"  # e.g., "adobe_paper_capture", "tesseract", "abbyy"
    engine_version: str = ""  # e.g., "Acrobat Pro DC 15", "5.0.0"
    producer: str = ""  # Raw producer string from PDF metadata
    creator: str = ""  # Raw creator string from PDF metadata
    creation_date: str = ""  # When OCR was performed
    confidence: float = 0.0  # How confident we are in engine detection (0-1)

    @classmethod
    def from_pdf_metadata(
        cls, producer: str | None, creator: str | None, creation_date: str | None
    ) -> OCRSourceInfo:
        """Parse PDF metadata to identify OCR source.

        Known patterns:
        - Adobe: "Adobe Acrobat * Paper Capture Plug-in"
        - ABBYY: "ABBYY FineReader *"
        - Tesseract: "Tesseract *" or in creator
        """
        producer = producer or ""
        creator = creator or ""
        creation_date = creation_date or ""

        engine = "unknown"
        engine_version = ""
        confidence = 0.0

        # Adobe Paper Capture detection
        if "Paper Capture" in producer:
            engine = "adobe_paper_capture"
            confidence = 0.95
            # Extract version: "Adobe Acrobat Pro DC 15 Paper Capture"
            if "Acrobat" in producer:
                parts = producer.split("Paper Capture")[0].strip()
                engine_version = parts.replace("Adobe ", "").strip()

        # ABBYY FineReader detection
        elif "ABBYY" in producer or "ABBYY" in creator:
            engine = "abbyy_finereader"
            confidence = 0.95
            # Extract version if present
            for text in [producer, creator]:
                if "FineReader" in text:
                    parts = text.split("FineReader")
                    if len(parts) > 1:
                        engine_version = parts[1].strip().split()[0] if parts[1].strip() else ""

        # Tesseract detection
        elif "Tesseract" in producer or "Tesseract" in creator:
            engine = "tesseract"
            confidence = 0.90
            for text in [producer, creator]:
                if "Tesseract" in text:
                    parts = text.split("Tesseract")
                    if len(parts) > 1:
                        engine_version = parts[1].strip().split()[0] if parts[1].strip() else ""

        # Check for other known producers that indicate scanned docs
        elif any(x in producer.lower() for x in ["scan", "ocr", "capture"]):
            engine = "unknown_ocr"
            confidence = 0.5

        return cls(
            engine=engine,
            engine_version=engine_version,
            producer=producer,
            creator=creator,
            creation_date=creation_date,
            confidence=confidence,
        )


@dataclass
class QualityInfo:
    """OCR quality information for the document."""

    overall: QualityLevel = QualityLevel.GOOD
    overall_confidence: float = 1.0
    pages: list[PageQuality] = field(default_factory=list)
    needs_reocr: list[int] = field(default_factory=list)  # Page indices needing re-OCR
    corrections: list[OCRCorrectionRecord] = field(default_factory=list)  # Optional correction log
    ocr_source: OCRSourceInfo | None = None  # Information about embedded OCR source


# ═══════════════════════════════════════════════════════════════════════════════
# Document Metadata
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class DocumentMetadata:
    """Metadata about the source document."""

    title: str | None = None
    author: str | None = None  # Primary author
    authors: list[str] = field(default_factory=list)  # All authors
    publication_date: str | None = None
    isbn: str | None = None
    doi: str | None = None
    language: str = "en"  # ISO 639-1 code
    document_type: DocumentType = DocumentType.GENERIC
    page_count: int = 0
    source_format: str = ""  # "pdf", "epub"
    extraction_date: datetime = field(default_factory=datetime.now)
    scholardoc_version: str = ""
    raw: dict[str, Any] = field(default_factory=dict)  # Original metadata from source


# ═══════════════════════════════════════════════════════════════════════════════
# RAG Chunk Output
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class RAGChunk:
    """A chunk ready for embedding."""

    text: str  # Clean text for embedding
    chunk_id: str  # Unique identifier
    chunk_index: int  # Position in sequence

    # Location
    page_labels: list[str] = field(default_factory=list)  # ["64", "65"]
    section: str | None = None  # Current section title
    chapter: str | None = None  # Current chapter title

    # Associations (what was in this chunk's range)
    footnote_refs: list[FootnoteRef] = field(default_factory=list)
    citations: list[CitationRef] = field(default_factory=list)

    # Navigation
    prev_chunk_id: str | None = None
    next_chunk_id: str | None = None

    # Document info
    doc_title: str | None = None
    doc_author: str | None = None
    source_path: str | None = None

    @property
    def citation(self) -> str:
        """Human-readable citation string."""
        pages = "-".join(self.page_labels) if self.page_labels else "?"
        if self.doc_author and self.doc_title:
            return f"{self.doc_author}, {self.doc_title}, p. {pages}"
        if self.doc_title:
            return f"{self.doc_title}, p. {pages}"
        return f"p. {pages}"


# ═══════════════════════════════════════════════════════════════════════════════
# ScholarDocument - The Core Class
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class ScholarDocument:
    """
    The canonical representation of a scholarly document.

    The `text` field contains clean semantic content. All artifacts (footnote markers,
    page numbers) are removed but recorded as position-based annotations.

    Example:
        >>> doc = ScholarDocument.load("kant.scholardoc")
        >>> print(doc.text[:100])  # Clean text, ready for embedding
        >>> for fn in doc.footnotes_in_range(0, 1000):
        ...     print(f"Footnote at {fn.position}: {doc.notes[fn.target_id].text}")
        >>> chunk = next(doc.to_rag_chunks())
        >>> print(chunk.citation)  # "Kant, Critique of Pure Reason, p. A64-B93"
    """

    # ─────────────────────────────────────────────────
    # Core Content
    # ─────────────────────────────────────────────────
    text: str  # Clean text, artifacts removed

    # ─────────────────────────────────────────────────
    # Position-Based Annotations (reference positions in `text`)
    # ─────────────────────────────────────────────────
    footnote_refs: list[FootnoteRef] = field(default_factory=list)
    endnote_refs: list[EndnoteRef] = field(default_factory=list)
    citations: list[CitationRef] = field(default_factory=list)
    cross_refs: list[CrossRef] = field(default_factory=list)

    # ─────────────────────────────────────────────────
    # Structural Spans (ranges in `text`)
    # ─────────────────────────────────────────────────
    pages: list[PageSpan] = field(default_factory=list)
    sections: list[SectionSpan] = field(default_factory=list)
    paragraphs: list[ParagraphSpan] = field(default_factory=list)
    block_quotes: list[BlockQuoteSpan] = field(default_factory=list)

    # ─────────────────────────────────────────────────
    # Referenced Content (the actual footnote/endnote text)
    # ─────────────────────────────────────────────────
    notes: dict[str, Note] = field(default_factory=dict)
    bibliography: list[BibEntry] = field(default_factory=list)

    # ─────────────────────────────────────────────────
    # Table of Contents (if present)
    # ─────────────────────────────────────────────────
    toc: TableOfContents | None = None

    # ─────────────────────────────────────────────────
    # Document Metadata
    # ─────────────────────────────────────────────────
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)

    # ─────────────────────────────────────────────────
    # Processing Info
    # ─────────────────────────────────────────────────
    source_path: Path | str = ""
    quality: QualityInfo = field(default_factory=QualityInfo)
    processing_log: list[str] = field(default_factory=list)

    # ─────────────────────────────────────────────────
    # Query Methods (essential for working with doc)
    # ─────────────────────────────────────────────────

    def text_range(self, start: int, end: int) -> str:
        """Get text slice."""
        return self.text[start:end]

    def annotations_in_range(
        self, start: int, end: int
    ) -> list[FootnoteRef | EndnoteRef | CitationRef | CrossRef]:
        """Get all annotations overlapping a range."""
        result: list[FootnoteRef | EndnoteRef | CitationRef | CrossRef] = []

        # Point annotations (footnotes, endnotes)
        for fn in self.footnote_refs:
            if start <= fn.position < end:
                result.append(fn)
        for en in self.endnote_refs:
            if start <= en.position < end:
                result.append(en)

        # Span annotations (citations, cross-refs)
        for cit in self.citations:
            if cit.start < end and start < cit.end:
                result.append(cit)
        for cr in self.cross_refs:
            if cr.start < end and start < cr.end:
                result.append(cr)

        return result

    def page_for_position(self, pos: int) -> PageSpan | None:
        """Which page contains this position?"""
        for page in self.pages:
            if page.start <= pos < page.end:
                return page
        return None

    def pages_in_range(self, start: int, end: int) -> list[PageSpan]:
        """Get all pages overlapping a range."""
        return [p for p in self.pages if p.start < end and start < p.end]

    def section_for_position(self, pos: int) -> SectionSpan | None:
        """Which section contains this position?"""
        # Return the most specific (deepest) section containing this position
        matching = [s for s in self.sections if s.start <= pos < s.end]
        if not matching:
            return None
        # Sort by level descending (deeper = more specific)
        return max(matching, key=lambda s: s.level)

    def sections_in_range(self, start: int, end: int) -> list[SectionSpan]:
        """Get all sections overlapping a range."""
        return [s for s in self.sections if s.start < end and start < s.end]

    def footnotes_in_range(self, start: int, end: int) -> list[tuple[FootnoteRef, Note]]:
        """Get footnotes referenced in a text range with their content."""
        result = []
        for fn in self.footnote_refs:
            if start <= fn.position < end:
                note = self.notes.get(fn.target_id)
                if note:
                    result.append((fn, note))
        return result

    def citations_in_range(self, start: int, end: int) -> list[CitationRef]:
        """Get citations in a text range."""
        return [c for c in self.citations if c.start < end and start < c.end]

    # ─────────────────────────────────────────────────
    # Derived Views (lazy, commonly needed)
    # ─────────────────────────────────────────────────

    @cached_property
    def paragraph_texts(self) -> list[str]:
        """List of paragraph strings."""
        return [self.text[p.start : p.end] for p in self.paragraphs]

    @cached_property
    def section_titles(self) -> list[str]:
        """List of section titles in order."""
        return [s.title for s in sorted(self.sections, key=lambda s: s.start)]

    @cached_property
    def page_labels(self) -> list[str]:
        """List of page labels in order."""
        return [p.label for p in sorted(self.pages, key=lambda p: p.start)]

    # ─────────────────────────────────────────────────
    # Common Exports (no deps, universal need)
    # ─────────────────────────────────────────────────

    def to_markdown(
        self,
        include_footnotes: bool = True,
        include_page_markers: bool = False,
        page_marker_style: str = "comment",
    ) -> str:
        """
        Export to Markdown with optional footnotes and page markers.

        Args:
            include_footnotes: Include footnotes at end of document
            include_page_markers: Include page boundary markers
            page_marker_style: "comment" (<!-- p. 64 -->), "heading" (## [p. 64]),
                             or "inline" ([p. 64])

        Returns:
            Markdown-formatted string
        """
        lines = []

        # Add metadata frontmatter
        if self.metadata.title:
            lines.append("---")
            lines.append(f"title: {self.metadata.title}")
            if self.metadata.author:
                lines.append(f"author: {self.metadata.author}")
            lines.append("---")
            lines.append("")

        # Build text with optional page markers
        if include_page_markers and self.pages:
            # Insert page markers at appropriate positions
            current_pos = 0
            for page in sorted(self.pages, key=lambda p: p.start):
                if page.start > current_pos:
                    lines.append(self.text[current_pos : page.start])
                if page_marker_style == "comment":
                    lines.append(f"\n<!-- p. {page.label} -->\n")
                elif page_marker_style == "heading":
                    lines.append(f"\n## [p. {page.label}]\n")
                else:  # inline
                    lines.append(f" [p. {page.label}] ")
                current_pos = page.start
            if current_pos < len(self.text):
                lines.append(self.text[current_pos:])
        else:
            lines.append(self.text)

        # Add footnotes at end
        if include_footnotes and self.notes:
            lines.append("\n\n---\n\n## Notes\n")
            for note_id, note in sorted(self.notes.items()):
                marker = note_id.replace("fn", "").replace("en", "")
                lines.append(f"\n[^{marker}]: {note.text}\n")

        return "".join(lines)

    def to_plain_text(self) -> str:
        """Just the clean text."""
        return self.text

    def to_rag_chunks(
        self,
        strategy: ChunkStrategy = ChunkStrategy.SEMANTIC,
        max_tokens: int = 512,
        overlap: int = 50,
    ) -> Iterator[RAGChunk]:
        """
        Generate RAG-ready chunks with metadata.

        Args:
            strategy: Chunking strategy to use
            max_tokens: Maximum tokens per chunk (approximate, uses chars * 0.25)
            overlap: Number of characters to overlap between chunks

        Yields:
            RAGChunk objects with text and associated metadata
        """
        max_chars = int(max_tokens * 4)  # Approximate chars per token

        if strategy == ChunkStrategy.PAGE:
            yield from self._chunk_by_page()
        elif strategy == ChunkStrategy.SECTION:
            yield from self._chunk_by_section()
        elif strategy == ChunkStrategy.SEMANTIC:
            yield from self._chunk_semantic(max_chars, overlap)
        else:  # FIXED_SIZE
            yield from self._chunk_fixed_size(max_chars, overlap)

    def _chunk_by_page(self) -> Iterator[RAGChunk]:
        """Generate one chunk per page."""
        prev_id = None
        for i, page in enumerate(sorted(self.pages, key=lambda p: p.start)):
            chunk_id = f"page_{page.label}"
            chunk = RAGChunk(
                text=self.text[page.start : page.end],
                chunk_id=chunk_id,
                chunk_index=i,
                page_labels=[page.label],
                section=self._section_for_range(page.start, page.end),
                footnote_refs=list(self._footnotes_in_range_refs(page.start, page.end)),
                citations=self.citations_in_range(page.start, page.end),
                prev_chunk_id=prev_id,
                doc_title=self.metadata.title,
                doc_author=self.metadata.author,
                source_path=str(self.source_path),
            )
            if prev_id:
                # Update previous chunk's next pointer (if we had it)
                pass
            prev_id = chunk_id
            yield chunk

    def _chunk_by_section(self) -> Iterator[RAGChunk]:
        """Generate one chunk per section."""
        prev_id = None
        for i, section in enumerate(sorted(self.sections, key=lambda s: s.start)):
            chunk_id = f"section_{i}_{section.title[:20].replace(' ', '_')}"
            pages = self.pages_in_range(section.start, section.end)
            chunk = RAGChunk(
                text=self.text[section.start : section.end],
                chunk_id=chunk_id,
                chunk_index=i,
                page_labels=[p.label for p in pages],
                section=section.title,
                footnote_refs=list(self._footnotes_in_range_refs(section.start, section.end)),
                citations=self.citations_in_range(section.start, section.end),
                prev_chunk_id=prev_id,
                doc_title=self.metadata.title,
                doc_author=self.metadata.author,
                source_path=str(self.source_path),
            )
            prev_id = chunk_id
            yield chunk

    def _chunk_semantic(self, max_chars: int, overlap: int) -> Iterator[RAGChunk]:
        """Chunk by paragraph boundaries, respecting max size."""
        if not self.paragraphs:
            # Fall back to fixed size if no paragraphs
            yield from self._chunk_fixed_size(max_chars, overlap)
            return

        current_start = 0
        current_text = ""
        chunk_index = 0
        prev_id = None

        for para in sorted(self.paragraphs, key=lambda p: p.start):
            para_text = self.text[para.start : para.end]

            # Would adding this paragraph exceed max?
            if len(current_text) + len(para_text) > max_chars and current_text:
                # Emit current chunk
                chunk_id = f"chunk_{chunk_index}"
                current_end = para.start
                yield self._make_chunk(
                    chunk_id, chunk_index, current_start, current_end, current_text, prev_id
                )
                prev_id = chunk_id
                chunk_index += 1

                # Start new chunk with overlap
                overlap_start = max(0, current_end - overlap)
                current_start = overlap_start
                current_text = self.text[overlap_start:current_end]

            current_text += para_text

        # Emit final chunk
        if current_text:
            chunk_id = f"chunk_{chunk_index}"
            yield self._make_chunk(
                chunk_id, chunk_index, current_start, len(self.text), current_text, prev_id
            )

    def _chunk_fixed_size(self, max_chars: int, overlap: int) -> Iterator[RAGChunk]:
        """Chunk by fixed character size."""
        chunk_index = 0
        prev_id = None
        start = 0

        while start < len(self.text):
            end = min(start + max_chars, len(self.text))
            chunk_id = f"chunk_{chunk_index}"
            chunk_text = self.text[start:end]

            yield self._make_chunk(chunk_id, chunk_index, start, end, chunk_text, prev_id)

            prev_id = chunk_id
            chunk_index += 1
            start = end - overlap if end < len(self.text) else end

    def _make_chunk(
        self,
        chunk_id: str,
        chunk_index: int,
        start: int,
        end: int,
        text: str,
        prev_id: str | None,
    ) -> RAGChunk:
        """Helper to create a RAGChunk with all metadata."""
        pages = self.pages_in_range(start, end)
        return RAGChunk(
            text=text,
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            page_labels=[p.label for p in pages],
            section=self._section_for_range(start, end),
            footnote_refs=list(self._footnotes_in_range_refs(start, end)),
            citations=self.citations_in_range(start, end),
            prev_chunk_id=prev_id,
            doc_title=self.metadata.title,
            doc_author=self.metadata.author,
            source_path=str(self.source_path),
        )

    def _section_for_range(self, start: int, end: int) -> str | None:
        """Get the primary section title for a range."""
        sections = self.sections_in_range(start, end)
        if sections:
            # Return the first (highest-level) section
            return min(sections, key=lambda s: s.level).title
        return None

    def _footnotes_in_range_refs(self, start: int, end: int) -> Iterator[FootnoteRef]:
        """Get footnote refs in range."""
        for fn in self.footnote_refs:
            if start <= fn.position < end:
                yield fn

    # ─────────────────────────────────────────────────
    # Persistence
    # ─────────────────────────────────────────────────

    def save(self, path: Path | str) -> None:
        """
        Save to .scholardoc (JSON) format.

        For documents >1MB, consider using save_sqlite() for better performance.

        Args:
            path: Output file path
        """
        path = Path(path)
        if not path.suffix:
            path = path.with_suffix(".scholardoc")

        data = self._to_dict()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    @classmethod
    def load(cls, path: Path | str) -> ScholarDocument:
        """
        Load from .scholardoc (JSON) format.

        Args:
            path: Input file path

        Returns:
            ScholarDocument instance
        """
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        return cls._from_dict(data)

    def _to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": "1.0",
            "text": self.text,
            "source_path": str(self.source_path),
            # Annotations
            "footnote_refs": [
                {"position": fn.position, "marker": fn.marker, "target_id": fn.target_id}
                for fn in self.footnote_refs
            ],
            "endnote_refs": [
                {"position": en.position, "marker": en.marker, "target_id": en.target_id}
                for en in self.endnote_refs
            ],
            "citations": [
                {
                    "start": c.start,
                    "end": c.end,
                    "original": c.original,
                    "bib_entry_id": c.bib_entry_id,
                }
                for c in self.citations
            ],
            "cross_refs": [
                {
                    "start": cr.start,
                    "end": cr.end,
                    "original": cr.original,
                    "target_page": cr.target_page,
                    "target_section": cr.target_section,
                }
                for cr in self.cross_refs
            ],
            # Structural spans
            "pages": [
                {"start": p.start, "end": p.end, "label": p.label, "index": p.index}
                for p in self.pages
            ],
            "sections": [
                {
                    "start": s.start,
                    "end": s.end,
                    "title": s.title,
                    "level": s.level,
                    "confidence": s.confidence,
                }
                for s in self.sections
            ],
            "paragraphs": [{"start": p.start, "end": p.end} for p in self.paragraphs],
            "block_quotes": [
                {"start": b.start, "end": b.end, "indentation_level": b.indentation_level}
                for b in self.block_quotes
            ],
            # Content
            "notes": {
                note_id: {
                    "id": note.id,
                    "text": note.text,
                    "note_type": note.note_type.value,
                    "page_label": note.page_label,
                    "source": note.source.value,
                }
                for note_id, note in self.notes.items()
            },
            "bibliography": [
                {
                    "id": b.id,
                    "raw": b.raw,
                    "authors": b.authors,
                    "title": b.title,
                    "year": b.year,
                }
                for b in self.bibliography
            ],
            # ToC
            "toc": self._toc_to_dict() if self.toc else None,
            # Metadata
            "metadata": {
                "title": self.metadata.title,
                "author": self.metadata.author,
                "authors": self.metadata.authors,
                "publication_date": self.metadata.publication_date,
                "document_type": self.metadata.document_type.value,
                "language": self.metadata.language,
                "page_count": self.metadata.page_count,
            },
            # Quality
            "quality": {
                "overall": self.quality.overall.value,
                "overall_confidence": self.quality.overall_confidence,
                "needs_reocr": self.quality.needs_reocr,
            },
            # Processing
            "processing_log": self.processing_log,
        }

    def _toc_to_dict(self) -> dict[str, Any]:
        """Convert ToC to dict recursively."""

        def entry_to_dict(entry: ToCEntry) -> dict:
            return {
                "title": entry.title,
                "page_label": entry.page_label,
                "level": entry.level,
                "children": [entry_to_dict(c) for c in entry.children],
            }

        return {
            "entries": [entry_to_dict(e) for e in self.toc.entries] if self.toc else [],
            "page_range": list(self.toc.page_range) if self.toc else [0, 0],
            "confidence": self.toc.confidence if self.toc else 0.0,
        }

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> ScholarDocument:
        """Create ScholarDocument from dictionary."""
        # Parse annotations
        footnote_refs = [
            FootnoteRef(position=fn["position"], marker=fn["marker"], target_id=fn["target_id"])
            for fn in data.get("footnote_refs", [])
        ]
        endnote_refs = [
            EndnoteRef(position=en["position"], marker=en["marker"], target_id=en["target_id"])
            for en in data.get("endnote_refs", [])
        ]
        citations = [
            CitationRef(
                start=c["start"],
                end=c["end"],
                original=c["original"],
                bib_entry_id=c.get("bib_entry_id"),
            )
            for c in data.get("citations", [])
        ]
        cross_refs = [
            CrossRef(
                start=cr["start"],
                end=cr["end"],
                original=cr["original"],
                target_page=cr.get("target_page"),
                target_section=cr.get("target_section"),
            )
            for cr in data.get("cross_refs", [])
        ]

        # Parse structural spans
        pages = [
            PageSpan(start=p["start"], end=p["end"], label=p["label"], index=p.get("index", 0))
            for p in data.get("pages", [])
        ]
        sections = [
            SectionSpan(
                start=s["start"],
                end=s["end"],
                title=s["title"],
                level=s["level"],
                confidence=s.get("confidence", 1.0),
            )
            for s in data.get("sections", [])
        ]
        paragraphs = [
            ParagraphSpan(start=p["start"], end=p["end"]) for p in data.get("paragraphs", [])
        ]
        block_quotes = [
            BlockQuoteSpan(
                start=b["start"],
                end=b["end"],
                indentation_level=b.get("indentation_level", 1),
            )
            for b in data.get("block_quotes", [])
        ]

        # Parse notes
        notes = {}
        for note_id, note_data in data.get("notes", {}).items():
            notes[note_id] = Note(
                id=note_data["id"],
                text=note_data["text"],
                note_type=NoteType(note_data.get("note_type", "footnote")),
                page_label=note_data.get("page_label", ""),
                source=NoteSource(note_data.get("source", "author")),
            )

        # Parse bibliography
        bibliography = [
            BibEntry(
                id=b["id"],
                raw=b["raw"],
                authors=b.get("authors", []),
                title=b.get("title"),
                year=b.get("year"),
            )
            for b in data.get("bibliography", [])
        ]

        # Parse ToC
        toc = None
        if data.get("toc"):
            toc_data = data["toc"]

            def parse_entry(e: dict) -> ToCEntry:
                return ToCEntry(
                    title=e["title"],
                    page_label=e.get("page_label", ""),
                    level=e.get("level", 1),
                    children=[parse_entry(c) for c in e.get("children", [])],
                )

            toc = TableOfContents(
                entries=[parse_entry(e) for e in toc_data.get("entries", [])],
                page_range=tuple(toc_data.get("page_range", [0, 0])),
                confidence=toc_data.get("confidence", 0.0),
            )

        # Parse metadata
        meta_data = data.get("metadata", {})
        metadata = DocumentMetadata(
            title=meta_data.get("title"),
            author=meta_data.get("author"),
            authors=meta_data.get("authors", []),
            publication_date=meta_data.get("publication_date"),
            document_type=DocumentType(meta_data.get("document_type", "generic")),
            language=meta_data.get("language", "en"),
            page_count=meta_data.get("page_count", 0),
        )

        # Parse quality
        quality_data = data.get("quality", {})
        quality = QualityInfo(
            overall=QualityLevel(quality_data.get("overall", "good")),
            overall_confidence=quality_data.get("overall_confidence", 1.0),
            needs_reocr=quality_data.get("needs_reocr", []),
        )

        return cls(
            text=data.get("text", ""),
            footnote_refs=footnote_refs,
            endnote_refs=endnote_refs,
            citations=citations,
            cross_refs=cross_refs,
            pages=pages,
            sections=sections,
            paragraphs=paragraphs,
            block_quotes=block_quotes,
            notes=notes,
            bibliography=bibliography,
            toc=toc,
            metadata=metadata,
            source_path=data.get("source_path", ""),
            quality=quality,
            processing_log=data.get("processing_log", []),
        )

    # ─────────────────────────────────────────────────
    # SQLite Persistence (for large documents)
    # ─────────────────────────────────────────────────

    def save_sqlite(self, path: Path | str) -> None:
        """
        Save to .scholardb (SQLite) format.

        Recommended for documents with >1MB of text for better performance
        and random access capabilities.

        Args:
            path: Output file path
        """
        import sqlite3

        path = Path(path)
        if not path.suffix:
            path = path.with_suffix(".scholardb")

        # Remove existing file if present
        if path.exists():
            path.unlink()

        conn = sqlite3.connect(path)
        try:
            self._create_sqlite_schema(conn)
            self._write_sqlite_data(conn)
            conn.commit()
        finally:
            conn.close()

    def _create_sqlite_schema(self, conn) -> None:
        """Create SQLite tables for document storage."""
        # Schema split across multiple statements for readability
        conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("CREATE TABLE content (text TEXT)")
        conn.execute("CREATE TABLE footnote_refs (position INTEGER, marker TEXT, target_id TEXT)")
        conn.execute("CREATE TABLE endnote_refs (position INTEGER, marker TEXT, target_id TEXT)")
        conn.execute(
            "CREATE TABLE citations "
            "(start INTEGER, end_pos INTEGER, original TEXT, bib_entry_id TEXT)"
        )
        conn.execute(
            "CREATE TABLE cross_refs "
            "(start INTEGER, end_pos INTEGER, original TEXT, "
            "target_page TEXT, target_section TEXT)"
        )
        conn.execute("CREATE TABLE pages (start INTEGER, end_pos INTEGER, label TEXT, idx INTEGER)")
        conn.execute(
            "CREATE TABLE sections "
            "(start INTEGER, end_pos INTEGER, title TEXT, level INTEGER, confidence REAL)"
        )
        conn.execute("CREATE TABLE paragraphs (start INTEGER, end_pos INTEGER)")
        conn.execute(
            "CREATE TABLE block_quotes (start INTEGER, end_pos INTEGER, indentation_level INTEGER)"
        )
        conn.execute(
            "CREATE TABLE notes "
            "(id TEXT PRIMARY KEY, text TEXT, note_type TEXT, page_label TEXT, source TEXT)"
        )
        conn.execute(
            "CREATE TABLE bibliography "
            "(id TEXT PRIMARY KEY, raw TEXT, authors TEXT, title TEXT, year TEXT)"
        )
        conn.execute(
            "CREATE TABLE toc_entries "
            "(id INTEGER PRIMARY KEY, title TEXT, page_label TEXT, "
            "level INTEGER, parent_id INTEGER)"
        )
        conn.execute("CREATE TABLE processing_log (idx INTEGER PRIMARY KEY, entry TEXT)")

        # Indexes for common queries
        conn.execute("CREATE INDEX idx_pages_start ON pages(start)")
        conn.execute("CREATE INDEX idx_sections_start ON sections(start)")
        conn.execute("CREATE INDEX idx_footnotes_pos ON footnote_refs(position)")

    def _write_sqlite_data(self, conn) -> None:
        """Write document data to SQLite tables."""
        # Metadata
        meta_items = [
            ("version", "1.0"),
            ("source_path", str(self.source_path)),
            ("title", self.metadata.title or ""),
            ("author", self.metadata.author or ""),
            ("document_type", self.metadata.document_type.value),
            ("language", self.metadata.language),
            ("page_count", str(self.metadata.page_count)),
            ("quality_overall", self.quality.overall.value),
            ("quality_confidence", str(self.quality.overall_confidence)),
        ]
        conn.executemany("INSERT INTO metadata VALUES (?, ?)", meta_items)

        # Content
        conn.execute("INSERT INTO content VALUES (?)", (self.text,))

        # Annotations
        conn.executemany(
            "INSERT INTO footnote_refs VALUES (?, ?, ?)",
            [(fn.position, fn.marker, fn.target_id) for fn in self.footnote_refs],
        )
        conn.executemany(
            "INSERT INTO endnote_refs VALUES (?, ?, ?)",
            [(en.position, en.marker, en.target_id) for en in self.endnote_refs],
        )
        conn.executemany(
            "INSERT INTO citations VALUES (?, ?, ?, ?)",
            [(c.start, c.end, c.original, c.bib_entry_id) for c in self.citations],
        )
        conn.executemany(
            "INSERT INTO cross_refs VALUES (?, ?, ?, ?, ?)",
            [
                (cr.start, cr.end, cr.original, cr.target_page, cr.target_section)
                for cr in self.cross_refs
            ],
        )

        # Structural spans
        conn.executemany(
            "INSERT INTO pages VALUES (?, ?, ?, ?)",
            [(p.start, p.end, p.label, p.index) for p in self.pages],
        )
        conn.executemany(
            "INSERT INTO sections VALUES (?, ?, ?, ?, ?)",
            [(s.start, s.end, s.title, s.level, s.confidence) for s in self.sections],
        )
        conn.executemany(
            "INSERT INTO paragraphs VALUES (?, ?)",
            [(p.start, p.end) for p in self.paragraphs],
        )
        conn.executemany(
            "INSERT INTO block_quotes VALUES (?, ?, ?)",
            [(b.start, b.end, b.indentation_level) for b in self.block_quotes],
        )

        # Notes
        conn.executemany(
            "INSERT INTO notes VALUES (?, ?, ?, ?, ?)",
            [
                (n.id, n.text, n.note_type.value, n.page_label, n.source.value)
                for n in self.notes.values()
            ],
        )

        # Bibliography
        conn.executemany(
            "INSERT INTO bibliography VALUES (?, ?, ?, ?, ?)",
            [(b.id, b.raw, json.dumps(b.authors), b.title, b.year) for b in self.bibliography],
        )

        # Processing log
        conn.executemany(
            "INSERT INTO processing_log VALUES (?, ?)",
            [(i, entry) for i, entry in enumerate(self.processing_log)],
        )

        # ToC entries (recursive structure flattened)
        if self.toc:
            self._write_toc_entries(conn, self.toc.entries, parent_id=None)

    def _write_toc_entries(self, conn, entries: list[ToCEntry], parent_id: int | None) -> None:
        """Recursively write ToC entries."""
        for entry in entries:
            cursor = conn.execute(
                "INSERT INTO toc_entries (title, page_label, level, parent_id) VALUES (?, ?, ?, ?)",
                (entry.title, entry.page_label, entry.level, parent_id),
            )
            entry_id = cursor.lastrowid
            if entry.children:
                self._write_toc_entries(conn, entry.children, entry_id)

    @classmethod
    def load_sqlite(cls, path: Path | str) -> ScholarDocument:
        """
        Load from .scholardb (SQLite) format.

        Args:
            path: Input file path

        Returns:
            ScholarDocument instance
        """
        import sqlite3

        path = Path(path)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        try:
            return cls._read_sqlite_data(conn)
        finally:
            conn.close()

    @classmethod
    def _read_sqlite_data(cls, conn) -> ScholarDocument:
        """Read document data from SQLite tables."""
        # Metadata
        meta = dict(conn.execute("SELECT key, value FROM metadata").fetchall())

        # Content
        text = conn.execute("SELECT text FROM content").fetchone()[0]

        # Annotations
        footnote_refs = [
            FootnoteRef(position=r["position"], marker=r["marker"], target_id=r["target_id"])
            for r in conn.execute("SELECT * FROM footnote_refs").fetchall()
        ]
        endnote_refs = [
            EndnoteRef(position=r["position"], marker=r["marker"], target_id=r["target_id"])
            for r in conn.execute("SELECT * FROM endnote_refs").fetchall()
        ]
        citations = [
            CitationRef(
                start=r["start"],
                end=r["end_pos"],
                original=r["original"],
                bib_entry_id=r["bib_entry_id"],
            )
            for r in conn.execute("SELECT * FROM citations").fetchall()
        ]
        cross_refs = [
            CrossRef(
                start=r["start"],
                end=r["end_pos"],
                original=r["original"],
                target_page=r["target_page"],
                target_section=r["target_section"],
            )
            for r in conn.execute("SELECT * FROM cross_refs").fetchall()
        ]

        # Structural spans
        pages = [
            PageSpan(start=r["start"], end=r["end_pos"], label=r["label"], index=r["idx"])
            for r in conn.execute("SELECT * FROM pages").fetchall()
        ]
        sections = [
            SectionSpan(
                start=r["start"],
                end=r["end_pos"],
                title=r["title"],
                level=r["level"],
                confidence=r["confidence"],
            )
            for r in conn.execute("SELECT * FROM sections").fetchall()
        ]
        paragraphs = [
            ParagraphSpan(start=r["start"], end=r["end_pos"])
            for r in conn.execute("SELECT * FROM paragraphs").fetchall()
        ]
        block_quotes = [
            BlockQuoteSpan(
                start=r["start"],
                end=r["end_pos"],
                indentation_level=r["indentation_level"],
            )
            for r in conn.execute("SELECT * FROM block_quotes").fetchall()
        ]

        # Notes
        notes = {
            r["id"]: Note(
                id=r["id"],
                text=r["text"],
                note_type=NoteType(r["note_type"]),
                page_label=r["page_label"],
                source=NoteSource(r["source"]),
            )
            for r in conn.execute("SELECT * FROM notes").fetchall()
        }

        # Bibliography
        bibliography = [
            BibEntry(
                id=r["id"],
                raw=r["raw"],
                authors=json.loads(r["authors"]) if r["authors"] else [],
                title=r["title"],
                year=r["year"],
            )
            for r in conn.execute("SELECT * FROM bibliography").fetchall()
        ]

        # ToC entries
        toc = cls._read_toc_entries(conn)

        # Processing log
        processing_log = [
            r["entry"]
            for r in conn.execute("SELECT entry FROM processing_log ORDER BY idx").fetchall()
        ]

        # Build metadata
        metadata = DocumentMetadata(
            title=meta.get("title") or None,
            author=meta.get("author") or None,
            document_type=DocumentType(meta.get("document_type", "generic")),
            language=meta.get("language", "en"),
            page_count=int(meta.get("page_count", 0)),
        )

        # Build quality
        quality = QualityInfo(
            overall=QualityLevel(meta.get("quality_overall", "good")),
            overall_confidence=float(meta.get("quality_confidence", 1.0)),
        )

        return cls(
            text=text,
            footnote_refs=footnote_refs,
            endnote_refs=endnote_refs,
            citations=citations,
            cross_refs=cross_refs,
            pages=pages,
            sections=sections,
            paragraphs=paragraphs,
            block_quotes=block_quotes,
            notes=notes,
            bibliography=bibliography,
            toc=toc,
            metadata=metadata,
            source_path=meta.get("source_path", ""),
            quality=quality,
            processing_log=processing_log,
        )

    @classmethod
    def _read_toc_entries(cls, conn) -> TableOfContents | None:
        """Read ToC entries from SQLite."""
        rows = conn.execute(
            "SELECT id, title, page_label, level, parent_id FROM toc_entries"
        ).fetchall()

        if not rows:
            return None

        # Build tree structure
        entries_by_id: dict[int, ToCEntry] = {}
        root_entries: list[ToCEntry] = []

        # First pass: create all entries
        for r in rows:
            entry = ToCEntry(
                title=r["title"],
                page_label=r["page_label"],
                level=r["level"],
                children=[],
            )
            entries_by_id[r["id"]] = entry

        # Second pass: build hierarchy
        for r in rows:
            entry = entries_by_id[r["id"]]
            if r["parent_id"] is None:
                root_entries.append(entry)
            else:
                parent = entries_by_id.get(r["parent_id"])
                if parent:
                    parent.children.append(entry)

        return TableOfContents(entries=root_entries)

    # ─────────────────────────────────────────────────
    # Convenience
    # ─────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self.text)

    def __getitem__(self, key: slice) -> str:
        return self.text[key]

    def __repr__(self) -> str:
        return (
            f"ScholarDocument("
            f"text={len(self.text)} chars, "
            f"pages={len(self.pages)}, "
            f"sections={len(self.sections)}, "
            f"footnotes={len(self.footnote_refs)})"
        )
