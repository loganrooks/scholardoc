"""
Structure extraction module.

Implements cascading structure detection per Phase 0.5 findings:
- Primary: PDF Outline (0.95 confidence when available)
- Secondary: Heading Detection (0.5-0.8 confidence)
- Enrichment: ToC Parser (title correction only)
- Fallback: Paragraph boundaries

Note: Probabilistic fusion was invalidated by 21% source agreement rate.
See spikes/FINDINGS.md for details.

Supports document profiles for type-specific configuration:
- BOOK_PROFILE: Multi-chapter books with ToC
- ARTICLE_PROFILE: Academic articles with abstract
- ESSAY_PROFILE: Essays with subheadings only
- REPORT_PROFILE: Technical reports with numbered sections
- DEFAULT_PROFILE: Fallback for unrecognized documents
"""

from scholardoc.extractors.cascading import (
    CascadingExtractor,
    StructureResult,
)
from scholardoc.extractors.profiles import (
    ARTICLE_PROFILE,
    BOOK_PROFILE,
    DEFAULT_PROFILE,
    ESSAY_PROFILE,
    PROFILES,
    REPORT_PROFILE,
    DocumentProfile,
    get_profile,
)
from scholardoc.extractors.sources import (
    CandidateSource,
    HeadingDetectionSource,
    PDFOutlineSource,
    SectionCandidate,
    ToCParserSource,
)
from scholardoc.extractors.validators import (
    HierarchyValidator,
    MinimumContentValidator,
    NoOverlapValidator,
    ValidationIssue,
    ValidationRule,
)

__all__ = [
    # Main extractor
    "CascadingExtractor",
    "StructureResult",
    # Profiles
    "DocumentProfile",
    "get_profile",
    "PROFILES",
    "BOOK_PROFILE",
    "ARTICLE_PROFILE",
    "ESSAY_PROFILE",
    "REPORT_PROFILE",
    "DEFAULT_PROFILE",
    # Sources
    "CandidateSource",
    "PDFOutlineSource",
    "HeadingDetectionSource",
    "ToCParserSource",
    "SectionCandidate",
    # Validators
    "ValidationRule",
    "NoOverlapValidator",
    "HierarchyValidator",
    "MinimumContentValidator",
    "ValidationIssue",
]
