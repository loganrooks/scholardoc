"""ScholarGT: Universal ground truth annotation schema for scholarly documents.

ScholarGT provides a config-driven, extensible schema for annotating scholarly
PDFs with spatial layout, semantic elements, and per-element verification tracking.
Independent of ScholarDoc -- usable by any extraction pipeline.

Usage:
    from scholargt import PageGT, DocumentGT, GTProfile, load_profile, validate_gt_file
"""

__version__ = "0.1.0"

# Schema models
# Config models
from scholargt.config import (
    GTProfile,
    ProjectConfig,
    ValidationConfig,
    get_profiles_dir,
    list_profiles,
    load_profile,
)
from scholargt.schema import (
    SCHEMA_VERSION,
    BBox,
    BibEntry,
    Citation,
    CitationBibLink,
    CitationType,
    ContentSpan,
    CrossReference,
    Difficulty,
    DocumentGT,
    DocumentRelationships,
    DocumentSource,
    DocumentStructure,
    DocumentType,
    Endnote,
    Footnote,
    FootnoteLink,
    FormattingAnnotation,
    FormattingType,
    GTElement,
    MarginalReference,
    MarginalRefType,
    MarkerInfo,
    PageGT,
    PageNumberAnnotation,
    PageQuality,
    ParsedCitation,
    Region,
    ScanQuality,
    Section,
    SemanticElement,
    SemanticType,
    SousRature,
    SpatialLabel,
    ToCEntry,
    VerificationRecord,
)

# Validation
from scholargt.validation import (
    ValidationResult,
    generate_schema,
    validate_document_gt,
    validate_gt_file,
    validate_page_gt,
    write_schema,
)

__all__ = [
    # Version
    "__version__",
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
    # Config
    "GTProfile",
    "ProjectConfig",
    "ValidationConfig",
    "load_profile",
    "list_profiles",
    "get_profiles_dir",
    # Validation
    "ValidationResult",
    "generate_schema",
    "write_schema",
    "validate_gt_file",
    "validate_page_gt",
    "validate_document_gt",
]
