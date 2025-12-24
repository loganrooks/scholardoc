"""
ScholarDoc: Convert scholarly documents to structured Markdown.

This library converts PDF (and eventually EPUB) documents to clean,
structured Markdown optimized for RAG pipelines, while preserving
the metadata and structure that researchers need.

Example:
    >>> import scholardoc
    >>> doc = scholardoc.convert("document.pdf")
    >>> print(doc.text)  # Clean text, ready for embedding
    >>> doc.save("output.scholardoc")

    >>> # Query document structure
    >>> for chunk in doc.to_rag_chunks():
    ...     print(chunk.citation)

See SPEC.md and docs/design/CORE_REPRESENTATION.md for full documentation.
"""

from scholardoc.config import ConversionConfig
from scholardoc.convert import (
    convert,
    convert_batch,
    detect_format,
    supported_formats,
)
from scholardoc.exceptions import (
    ConfigurationError,
    ExtractionError,
    ScholarDocError,
    UnsupportedFormatError,
)
from scholardoc.models import (
    # Content
    BibEntry,
    # Spans
    BlockQuoteSpan,
    # Enums
    ChunkStrategy,
    # Annotations
    CitationRef,
    CrossRef,
    # Metadata & Quality
    DocumentMetadata,
    DocumentType,
    EndnoteRef,
    FootnoteRef,
    Note,
    NoteSource,
    NoteType,
    PageQuality,
    PageSpan,
    ParagraphSpan,
    ParsedCitation,
    QualityInfo,
    QualityLevel,
    # Output
    RAGChunk,
    ScholarDocument,
    SectionSpan,
    Span,
    TableOfContents,
    ToCEntry,
)

__version__ = "0.1.0"
__all__ = [
    # Main API
    "convert",
    "convert_batch",
    "detect_format",
    "supported_formats",
    # Configuration
    "ConversionConfig",
    # Core Document
    "ScholarDocument",
    # Enums
    "DocumentType",
    "NoteType",
    "NoteSource",
    "ChunkStrategy",
    "QualityLevel",
    # Annotations
    "FootnoteRef",
    "EndnoteRef",
    "CitationRef",
    "CrossRef",
    "ParsedCitation",
    # Spans
    "Span",
    "PageSpan",
    "SectionSpan",
    "ParagraphSpan",
    "BlockQuoteSpan",
    # Content
    "Note",
    "BibEntry",
    "ToCEntry",
    "TableOfContents",
    # Metadata
    "DocumentMetadata",
    "PageQuality",
    "QualityInfo",
    # Output
    "RAGChunk",
    # Exceptions
    "ScholarDocError",
    "UnsupportedFormatError",
    "ExtractionError",
    "ConfigurationError",
]


# Public API functions are imported from scholardoc.convert:
# - convert(source, config) -> ScholarDocument
# - convert_batch(sources, config, parallel, max_workers) -> Iterator
# - detect_format(path) -> str
# - supported_formats() -> list[str]
