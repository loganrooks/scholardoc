"""
Data models for ScholarDoc.

These models represent the output of document conversion.
See SPEC.md for full documentation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class DocumentSource:
    """Source document information."""

    path: str
    format: str  # "pdf", "epub", etc.
    size_bytes: int
    md5_hash: str | None = None


@dataclass
class DocumentMetadata:
    """Document metadata extracted from source."""

    title: str | None = None
    authors: list[str] = field(default_factory=list)
    date: str | None = None
    isbn: str | None = None
    doi: str | None = None
    language: str | None = None
    page_count: int = 0
    source_format: str = ""
    extraction_date: datetime = field(default_factory=datetime.now)
    scholardoc_version: str = ""
    raw: dict[str, Any] = field(default_factory=dict)  # Original metadata


@dataclass
class Section:
    """A section in the document structure."""

    title: str
    level: int  # 1 = chapter, 2 = section, etc.
    page_label: str | None = None
    children: list["Section"] = field(default_factory=list)


@dataclass
class ChunkHint:
    """
    Suggested chunk boundary for downstream RAG processing.

    Even though ScholarDoc doesn't do chunking, we can provide hints
    about where it's safe to break the document based on our structural
    understanding.
    """

    position: int  # Character offset in markdown
    hint_type: str  # "section_break", "paragraph", "page_break", "footnote_boundary"
    confidence: float  # 0.0-1.0, how confident we are this is a good break point
    context: str | None = None  # e.g., "After heading: Chapter 3"


@dataclass
class DocumentStructure:
    """Document structure (TOC-like)."""

    sections: list[Section] = field(default_factory=list)


@dataclass
class ScholarDocument:
    """
    The main output type for users.

    This contains the converted Markdown, extracted metadata,
    document structure, and any warnings from processing.

    Example:
        >>> doc = scholardoc.convert("book.pdf")
        >>> print(doc.markdown)
        >>> print(doc.metadata.title)
        >>> doc.save("output.md")
    """

    # Core output
    markdown: str

    # Structured data
    metadata: DocumentMetadata
    structure: DocumentStructure

    # Source info
    source_path: str

    # Chunk-friendly output (for downstream RAG processing)
    chunk_hints: list[ChunkHint] = field(default_factory=list)

    # Diagnostics
    warnings: list[str] = field(default_factory=list)

    def save(self, path: str | Path) -> None:
        """
        Save markdown to file.

        Args:
            path: Output file path
        """
        Path(path).write_text(self.markdown, encoding="utf-8")

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the document
        """
        return {
            "markdown": self.markdown,
            "metadata": {
                "title": self.metadata.title,
                "authors": self.metadata.authors,
                "date": self.metadata.date,
                "page_count": self.metadata.page_count,
                "source_format": self.metadata.source_format,
            },
            "source_path": self.source_path,
            "warnings": self.warnings,
        }
