"""PageGT model for page-level ground truth files.

Each page in a GT corpus has a PageGT JSON file containing spatial regions,
reading order, quality metadata, cross-page dependencies, section context,
and page-level verification records.

v2.0.0 changes from v1.0.0:
- PageQuality: hybrid model replacing categorical ScanQuality/Difficulty enums
  with categorical overall, is_scan flag, artifact/difficulty lists, and numeric metrics
- PageDependency: cross-page relationship metadata (continues_from/to, unresolved markers)
- SectionContextEntry: hierarchical section path per page (starts/ends flags)
- PageGT: section_context, page_dependency, and base_direction (SFP-2) added
"""

from __future__ import annotations

import warnings
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scholargt.schema.base import VerificationRecord
from scholargt.schema.spatial import Region
from scholargt.schema.version import SCHEMA_VERSION


class PageQuality(BaseModel):
    """Page-level quality assessment -- hybrid categorical + numeric model.

    Replaces the old ScanQuality and Difficulty enums with a richer model:
    - Categorical: overall quality, is_scan flag
    - Artifact list: specific quality issues (free-form, documented recommended values)
    - Difficulty factors: signals affecting annotation difficulty
    - Numeric metrics: optional DPI, contrast, skew, noise, OCR confidence

    Recommended artifact values: "bleed_through", "foxing", "skew",
    "margin_cropping", "water_damage", "faded_ink", "handwritten_overlay",
    "binding_shadow", "staining", "torn_page".

    Recommended difficulty_factors values: "dense_footnotes", "multi_column",
    "mixed_language", "complex_typography", "poor_scan", "non_latin_script",
    "overlapping_regions", "marginal_annotations", "tables_with_text".
    """

    overall: Literal["low", "medium", "high"] | None = Field(
        default=None, description="Quick categorical quality assessment for human annotation"
    )
    is_scan: bool | None = Field(
        default=None, description="True if scanned document, False if born-digital"
    )
    artifacts: list[str] = Field(
        default_factory=list,
        description="Specific quality issues (e.g., 'bleed_through', 'foxing', 'skew')",
    )
    difficulty_factors: list[str] = Field(
        default_factory=list,
        description="Specific difficulty signals (e.g., 'dense_footnotes', 'multi_column')",
    )
    dpi_estimate: int | None = Field(
        default=None, description="Estimated DPI of the page image"
    )
    contrast_ratio: float | None = Field(
        default=None, description="Estimated contrast ratio"
    )
    skew_angle: float | None = Field(
        default=None, description="Page skew angle in degrees"
    )
    noise_level: float | None = Field(
        default=None, description="Noise estimate on [0, 1] scale"
    )
    ocr_confidence: float | None = Field(
        default=None, description="Mean OCR confidence if available"
    )


class PageDependency(BaseModel):
    """Cross-page relationship metadata.

    Captures how this page relates to its neighbors: whether content continues
    across page boundaries, and whether note markers or note content are orphaned
    (body marker on one page, note content on another -- common with endnotes).
    """

    continues_from_previous: bool = Field(
        default=False, description="Some content on this page continues from the prior page"
    )
    continues_to_next: bool = Field(
        default=False, description="Some content on this page continues to the next page"
    )
    unresolved_markers: list[str] = Field(
        default_factory=list,
        description="Body markers on this page with no corresponding note on this page (endnote refs)",
    )
    orphan_continuations: list[str] = Field(
        default_factory=list,
        description="Note content on this page with no corresponding body marker on this page",
    )


class SectionContextEntry(BaseModel):
    """A single entry in the hierarchical section path for a page.

    Provides per-page section context so each page is self-describing:
    an annotator or evaluation pipeline can determine which section(s)
    a page belongs to without loading the full DocumentGT.
    """

    section_id: str = Field(description="Reference to Section element in DocumentGT")
    title: str = Field(description="Section title text")
    level: int = Field(description="Nesting level (0 = top-level)")
    starts_on_this_page: bool = Field(
        default=False, description="True if this section begins on this page"
    )
    ends_on_this_page: bool = Field(
        default=False, description="True if this section ends on this page"
    )


class PageGT(BaseModel):
    """Page-level ground truth containing spatial annotations.

    Each page file captures regions (spatial + semantic annotations),
    reading order, quality metadata, cross-page dependencies, section
    context, and page-level verifications. Forward-compatible via extra="allow".

    v2.0.0 additions:
    - section_context: hierarchical section path for self-describing pages
    - page_dependency: cross-page dependency metadata
    - base_direction: default text direction for this page (SFP-2)
    """

    model_config = ConfigDict(extra="allow")

    schema_version: str = Field(
        default=SCHEMA_VERSION, description="Schema version for migration support"
    )
    page_index: int = Field(description="0-based PDF page index")
    page_label: str | None = Field(
        default=None, description="Printed page number (e.g., '127', 'xiv')"
    )
    dimensions: dict[str, float] | None = Field(
        default=None, description="Page dimensions, e.g., {'width': 612, 'height': 792}"
    )
    regions: list[Region] = Field(default_factory=list, description="Spatial annotations")
    reading_order: list[str] = Field(
        default_factory=list, description="Ordered list of region IDs"
    )
    quality: PageQuality | None = Field(default=None, description="Page quality metadata")
    section_context: list[SectionContextEntry] = Field(
        default_factory=list,
        description="Hierarchical section path for self-describing pages",
    )
    page_dependency: PageDependency | None = Field(
        default=None, description="Cross-page dependency metadata"
    )
    base_direction: Literal["ltr", "rtl"] | None = Field(
        default=None, description="SFP-2: default text direction for this page"
    )
    verifications: list[VerificationRecord] = Field(
        default_factory=list, description="Page-level verification records"
    )

    @model_validator(mode="after")
    def _validate_reading_order(self) -> PageGT:
        """Warn if reading_order references non-existent region IDs.

        Uses warning rather than error because annotation may be in progress
        (regions added incrementally).
        """
        if self.reading_order and self.regions:
            region_ids = {r.id for r in self.regions}
            unknown = [rid for rid in self.reading_order if rid not in region_ids]
            if unknown:
                warnings.warn(
                    f"reading_order references unknown region IDs: {unknown}",
                    UserWarning,
                    stacklevel=2,
                )
        return self
