"""ScholarGT: Universal ground truth annotation schema for scholarly documents.

ScholarGT provides a config-driven, extensible schema for annotating scholarly
PDFs with spatial layout, semantic elements, and per-element verification tracking.
Independent of ScholarDoc -- usable by any extraction pipeline.

Usage:
    from scholargt import PageGT, DocumentGT, GTProfile, load_profile, validate_gt_file
"""

__version__ = "0.1.0"

# Config models
from scholargt.config import (
    GTProfile,
    ProjectConfig,
    ValidationConfig,
    get_profiles_dir,
    list_profiles,
    load_profile,
)

# Schema models
from scholargt.schema import (
    SCHEMA_VERSION,
    BBox,
    BibEntry,
    BibliographicRecord,
    Citation,
    CitationFormat,
    CitationStyle,
    Commentary,
    ContentSpan,
    CrossReference,
    DocumentGT,
    DocumentSectionType,
    DocumentSource,
    DocumentStructure,
    FormattingAnnotation,
    FormattingType,
    GTElement,
    LayoutRegister,
    LocationRef,
    MarginalReference,
    Note,
    NoteSchema,
    PageDependency,
    PageGT,
    PageNumberAnnotation,
    PageQuality,
    ParsedCitation,
    ReferenceSystem,
    Region,
    ScriptVariant,
    Section,
    SectionContextEntry,
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
    "BibEntry",
    "BibliographicRecord",
    "Citation",
    "ContentSpan",
    "CrossReference",
    "MarginalReference",
    "NoteSchema",
    "PageNumberAnnotation",
    "ParsedCitation",
    "Section",
    "SemanticElement",
    "SousRature",
    "ToCEntry",
    # Formatting
    "FormattingAnnotation",
    # Document-level
    "DocumentGT",
    "DocumentSource",
    "DocumentStructure",
    "LayoutRegister",
    # Label enums
    "CitationFormat",
    "CitationStyle",
    "DocumentSectionType",
    "FormattingType",
    "ReferenceSystem",
    "ScriptVariant",
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
