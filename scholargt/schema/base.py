"""Core base models for ScholarGT ground truth elements.

Provides GTElement (base for all annotatable elements with verification tracking),
BBox (normalized bounding box), and VerificationRecord (reviewer verification event).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BBox(BaseModel):
    """Normalized bounding box in [x0, y0, x1, y1] corners format.

    All coordinates are normalized to [0.0, 1.0] relative to page dimensions.
    Uses corners format (ScholarDoc convention) with a to_xywh() helper for
    CryptOfCogito compatibility.
    """

    x0: float = Field(ge=0.0, le=1.0, description="Left edge (normalized)")
    y0: float = Field(ge=0.0, le=1.0, description="Top edge (normalized)")
    x1: float = Field(ge=0.0, le=1.0, description="Right edge (normalized)")
    y1: float = Field(ge=0.0, le=1.0, description="Bottom edge (normalized)")

    @model_validator(mode="after")
    def _validate_corners(self) -> BBox:
        """Ensure x1 >= x0 and y1 >= y0 (non-degenerate box)."""
        if self.x1 < self.x0:
            msg = f"x1 ({self.x1}) must be >= x0 ({self.x0})"
            raise ValueError(msg)
        if self.y1 < self.y0:
            msg = f"y1 ({self.y1}) must be >= y0 ({self.y0})"
            raise ValueError(msg)
        return self

    def to_xywh(self) -> tuple[float, float, float, float]:
        """Convert to [x, y, width, height] format for CryptOfCogito compatibility."""
        return (self.x0, self.y0, self.x1 - self.x0, self.y1 - self.y0)

    def area(self) -> float:
        """Compute area of the bounding box (normalized units)."""
        return (self.x1 - self.x0) * (self.y1 - self.y0)


class LocationRef(BaseModel):
    """Reference to a specific location in the GT corpus.

    Standardizes the scattered page/region_id/char_offset/char_length pattern
    used across semantic elements. Use for body_marker, content_marker,
    target_location, and any element that references a position in a page region.
    """

    page: int = Field(description="0-based page index")
    region_id: str = Field(description="Region ID on the page")
    char_offset: int | None = Field(
        default=None, description="Character offset within region text"
    )
    char_length: int | None = Field(
        default=None, description="Length of referenced text span"
    )


class VerificationRecord(BaseModel):
    """A single verification event for a GT element.

    Multiple records per element support inter-annotator agreement.
    Confidence is a reviewer property, not an element property -- GT is truth
    by definition; confidence reflects how sure the reviewer is.
    """

    reviewer_id: str = Field(
        description="Unique identifier for the reviewer (e.g., 'human_alice', 'claude_opus')"
    )
    timestamp: datetime = Field(description="When the verification occurred")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Reviewer's confidence in the annotation correctness"
    )
    notes: str | None = Field(default=None, description="Optional notes about the verification")


class GTElement(BaseModel):
    """Base for all ground truth elements with verification tracking.

    All annotatable elements inherit from GTElement, gaining:
    - Unique ID for cross-referencing
    - Per-element verification records (multi-reviewer)
    - Tags for ad-hoc grouping
    - Forward compatibility via extra="allow"
    """

    model_config = ConfigDict(extra="allow")

    id: str = Field(description="Unique identifier for this element")
    verifications: list[VerificationRecord] = Field(
        default_factory=list, description="Verification records from reviewers"
    )
    tags: list[str] = Field(default_factory=list, description="Ad-hoc grouping tags")

    def is_verified(self, threshold: float = 0.8) -> bool:
        """Element is verified if at least one reviewer exceeds the confidence threshold.

        Args:
            threshold: Minimum confidence to consider verified (default 0.8,
                      configurable via project profile).

        Returns:
            True if any verification record has confidence >= threshold.
        """
        return any(v.confidence >= threshold for v in self.verifications)

    def agreement_score(self) -> float | None:
        """Inter-annotator agreement as mean confidence across reviewers.

        Returns:
            Mean confidence, or None if no verifications exist.
            Phase 4 (annotation tool) can implement Cohen's kappa or
            Fleiss' kappa for more sophisticated agreement metrics.
        """
        if not self.verifications:
            return None
        return sum(v.confidence for v in self.verifications) / len(self.verifications)
