"""Document profiles for structure extraction.

Profiles enable document-type-specific configuration for structure extraction.
Each profile specifies which sources to use, confidence thresholds, and validators.

Based on Phase 0.5 findings:
- Book detection: 100% accuracy (spike 27)
- estimate_document_type() already validated for profile selection
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from scholardoc.readers.pdf_reader import estimate_document_type

if TYPE_CHECKING:
    from scholardoc.readers.pdf_reader import RawDocument


@dataclass(frozen=True)
class DocumentProfile:
    """Configuration for document-type-specific structure extraction.

    Profiles define which sources and validators to use based on document type.
    Standard profiles are provided for common document types (book, article, etc.).

    Attributes:
        name: Profile identifier (e.g., "book", "article").
        description: Human-readable description.
        use_outline: Whether to use PDF outline/bookmarks as primary source.
        use_heading_detection: Whether to use font-based heading detection.
        use_toc_enrichment: Whether to use ToC for title enrichment.
        min_confidence: Minimum confidence threshold for including sections.
        title_similarity_threshold: Threshold for ToC title matching.
        validators: Tuple of validator names to apply ("overlap", "hierarchy", etc.).
    """

    name: str
    description: str
    use_outline: bool = True
    use_heading_detection: bool = True
    use_toc_enrichment: bool = True
    min_confidence: float = 0.5
    title_similarity_threshold: float = 0.8
    validators: tuple[str, ...] = ("overlap", "hierarchy")


# Standard profiles based on Phase 0.5 spike findings

BOOK_PROFILE = DocumentProfile(
    name="book",
    description="Multi-chapter books with ToC and/or PDF outline",
    use_outline=True,
    use_heading_detection=True,
    use_toc_enrichment=True,  # Books often have ToC for title correction
    min_confidence=0.5,
    validators=("overlap", "hierarchy", "title_quality"),
)

ARTICLE_PROFILE = DocumentProfile(
    name="article",
    description="Academic articles with abstract and sections",
    use_outline=True,
    use_heading_detection=True,
    use_toc_enrichment=False,  # Articles rarely have ToC
    min_confidence=0.4,  # More lenient - fewer sections expected
    validators=("overlap",),
)

ESSAY_PROFILE = DocumentProfile(
    name="essay",
    description="Essays and papers with subheadings only",
    use_outline=True,
    use_heading_detection=True,
    use_toc_enrichment=False,
    min_confidence=0.4,
    validators=("overlap", "min_content"),
)

REPORT_PROFILE = DocumentProfile(
    name="report",
    description="Technical reports with numbered sections",
    use_outline=True,
    use_heading_detection=True,
    use_toc_enrichment=True,
    min_confidence=0.5,
    validators=("overlap", "hierarchy"),
)

DEFAULT_PROFILE = DocumentProfile(
    name="generic",
    description="Fallback for unrecognized document types",
    use_outline=True,
    use_heading_detection=True,
    use_toc_enrichment=False,
    min_confidence=0.5,
    validators=("overlap",),
)


# Profile lookup dictionary
PROFILES: dict[str, DocumentProfile] = {
    "book": BOOK_PROFILE,
    "article": ARTICLE_PROFILE,
    "essay": ESSAY_PROFILE,
    "report": REPORT_PROFILE,
    "generic": DEFAULT_PROFILE,
}


def get_profile(doc: RawDocument) -> DocumentProfile:
    """Get the appropriate profile for a document.

    Uses estimate_document_type() to detect document type and returns
    the matching profile. Falls back to DEFAULT_PROFILE if type is unknown.

    Args:
        doc: Raw document from PDF reader.

    Returns:
        DocumentProfile appropriate for the document type.
    """
    doc_type = estimate_document_type(doc)
    return PROFILES.get(doc_type, DEFAULT_PROFILE)
