"""
ScholarDoc: Convert scholarly documents to structured Markdown.

This library converts PDF (and eventually EPUB) documents to clean,
structured Markdown optimized for RAG pipelines, while preserving
the metadata and structure that researchers need.

Example:
    >>> import scholardoc
    >>> doc = scholardoc.convert("document.pdf")
    >>> print(doc.markdown)
    >>> doc.save("output.md")

See SPEC.md for full API documentation.
"""

from scholardoc.config import ConversionConfig
from scholardoc.exceptions import (
    ConfigurationError,
    ExtractionError,
    ScholarDocError,
    UnsupportedFormatError,
)
from scholardoc.models import (
    DocumentMetadata,
    DocumentStructure,
    ScholarDocument,
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
    # Models
    "ScholarDocument",
    "DocumentMetadata",
    "DocumentStructure",
    # Exceptions
    "ScholarDocError",
    "UnsupportedFormatError",
    "ExtractionError",
    "ConfigurationError",
]


def convert(
    source: str,
    config: ConversionConfig | None = None,
) -> ScholarDocument:
    """
    Convert a single document to structured Markdown.

    Args:
        source: Path to document file
        config: Conversion configuration (uses defaults if None)

    Returns:
        ScholarDocument with markdown and metadata

    Raises:
        FileNotFoundError: If source doesn't exist
        UnsupportedFormatError: If format not supported
        ExtractionError: If extraction fails (when on_extraction_error="raise")

    Example:
        >>> doc = scholardoc.convert("kant.pdf")
        >>> print(doc.markdown[:100])
        >>> print(f"Pages: {doc.metadata.page_count}")
    """
    # TODO: Implement in Phase 1
    raise NotImplementedError("Phase 1 implementation in progress")


def convert_batch(
    sources,
    config: ConversionConfig | None = None,
    parallel: bool = False,
    max_workers: int = 4,
):
    """
    Convert multiple documents, yielding results as completed.

    Args:
        sources: Paths to document files
        config: Conversion configuration
        parallel: Whether to process in parallel
        max_workers: Max parallel workers (if parallel=True)

    Yields:
        (path, result) tuples where result is ScholarDocument or Exception
    """
    # TODO: Implement in Phase 1
    raise NotImplementedError("Phase 1 implementation in progress")


def detect_format(path: str) -> str:
    """
    Detect document format from file extension and magic bytes.

    Returns:
        Format string: "pdf", "epub", "markdown", etc.

    Raises:
        UnsupportedFormatError: If format cannot be detected or isn't supported
    """
    # TODO: Implement in Phase 1
    raise NotImplementedError("Phase 1 implementation in progress")


def supported_formats() -> list[str]:
    """Return list of currently supported input formats."""
    return ["pdf"]  # Phase 1: PDF only
