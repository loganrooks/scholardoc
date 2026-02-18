"""PageGT model for page-level ground truth files.

Each page in a GT corpus has a PageGT JSON file containing spatial regions,
reading order, quality metadata, and page-level verification records.
Schema version is embedded in every file for migration support.
"""

from __future__ import annotations

import warnings
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scholargt.schema.base import VerificationRecord
from scholargt.schema.spatial import Region
from scholargt.schema.version import SCHEMA_VERSION


class PageQuality(BaseModel):
    """Page-level quality assessment metadata."""

    scan_quality: Literal["low", "medium", "high"] | None = Field(
        default=None, description="Scan quality assessment"
    )
    difficulty: Literal["easy", "medium", "hard"] | None = Field(
        default=None, description="Annotation difficulty for test stratification"
    )


class PageGT(BaseModel):
    """Page-level ground truth containing spatial annotations.

    Each page file captures regions (spatial + semantic annotations),
    reading order, quality metadata, and page-level verifications.
    Forward-compatible via extra="allow".
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
