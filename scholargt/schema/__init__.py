"""ScholarGT schema models for ground truth annotation.

Re-exports all public models for convenient imports:

    from scholargt.schema import PageGT, DocumentGT, SemanticElement, Region
"""

from scholargt.schema.base import BBox, GTElement, VerificationRecord
from scholargt.schema.document import (
    CitationBibLink,
    DocumentGT,
    DocumentRelationships,
    DocumentSource,
    DocumentStructure,
    FootnoteLink,
)
from scholargt.schema.formatting import FormattingAnnotation
from scholargt.schema.labels import (
    CitationType,
    Difficulty,
    DocumentType,
    FormattingType,
    MarginalRefType,
    ScanQuality,
    SemanticType,
    SpatialLabel,
)
from scholargt.schema.page import PageGT, PageQuality
from scholargt.schema.semantic import (
    BibEntry,
    Citation,
    ContentSpan,
    CrossReference,
    Endnote,
    Footnote,
    MarginalReference,
    MarkerInfo,
    PageNumberAnnotation,
    ParsedCitation,
    Section,
    SemanticElement,
    SousRature,
    ToCEntry,
)
from scholargt.schema.spatial import Region
from scholargt.schema.version import SCHEMA_VERSION

__all__ = [
    # Version
    "SCHEMA_VERSION",
    # Base models
    "BBox",
    "GTElement",
    "VerificationRecord",
    # Spatial
    "Region",
    # Page-level
    "PageGT",
    "PageQuality",
    # Semantic elements
    "BibEntry",
    "Citation",
    "ContentSpan",
    "CrossReference",
    "Endnote",
    "Footnote",
    "MarginalReference",
    "MarkerInfo",
    "PageNumberAnnotation",
    "ParsedCitation",
    "Section",
    "SemanticElement",
    "SousRature",
    "ToCEntry",
    # Formatting
    "FormattingAnnotation",
    # Document-level
    "CitationBibLink",
    "DocumentGT",
    "DocumentRelationships",
    "DocumentSource",
    "DocumentStructure",
    "FootnoteLink",
    # Label enums
    "CitationType",
    "Difficulty",
    "DocumentType",
    "FormattingType",
    "MarginalRefType",
    "ScanQuality",
    "SemanticType",
    "SpatialLabel",
]
