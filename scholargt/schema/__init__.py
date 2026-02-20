"""ScholarGT schema models for ground truth annotation.

Re-exports all public models for convenient imports:

    from scholargt.schema import PageGT, DocumentGT, SemanticElement, Region

v2.0.0: Note replaces Footnote+Endnote, Commentary added, LayoutRegister (SFP-1),
LocationRef standardizes position references, label enums reorganized.
"""

from scholargt.schema.base import BBox, GTElement, LocationRef, VerificationRecord
from scholargt.schema.document import (
    DocumentGT,
    DocumentSource,
    DocumentStructure,
    LayoutRegister,
)
from scholargt.schema.formatting import FormattingAnnotation
from scholargt.schema.labels import (
    CitationFormat,
    CitationStyle,
    DocumentSectionType,
    FormattingType,
    ReferenceSystem,
    ScriptVariant,
    SemanticType,
    SpatialLabel,
)
from scholargt.schema.page import PageDependency, PageGT, PageQuality, SectionContextEntry
from scholargt.schema.semantic import (
    BibEntry,
    BibliographicRecord,
    Citation,
    Commentary,
    ContentSpan,
    CrossReference,
    MarginalReference,
    Note,
    NoteSchema,
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
    "LocationRef",
    # Spatial
    "Region",
    # Page-level
    "PageGT",
    "PageQuality",
    "PageDependency",
    "SectionContextEntry",
    # Semantic elements
    "Note",
    "Commentary",
    "Citation",
    "BibEntry",
    "Section",
    "SousRature",
    "CrossReference",
    "MarginalReference",
    "PageNumberAnnotation",
    "SemanticElement",
    # Supporting models
    "ContentSpan",
    "ParsedCitation",
    "BibliographicRecord",
    "ToCEntry",
    "NoteSchema",
    # Formatting
    "FormattingAnnotation",
    # Document-level
    "DocumentGT",
    "DocumentSource",
    "DocumentStructure",
    "LayoutRegister",
    # Label enums
    "SpatialLabel",
    "SemanticType",
    "FormattingType",
    "ScriptVariant",
    "CitationFormat",
    "ReferenceSystem",
    "CitationStyle",
    "DocumentSectionType",
]
