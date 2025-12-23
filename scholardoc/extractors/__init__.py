"""
Structure extraction module.

Implements cascading structure detection per Phase 0.5 findings:
- Primary: PDF Outline (0.95 confidence when available)
- Secondary: Heading Detection (0.5-0.8 confidence)
- Enrichment: ToC Parser (title correction only)
- Fallback: Paragraph boundaries

Note: Probabilistic fusion was invalidated by 21% source agreement rate.
See spikes/FINDINGS.md for details.
"""

from scholardoc.extractors.cascading import (
    CascadingExtractor,
    StructureResult,
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
