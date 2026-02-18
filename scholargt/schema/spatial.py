"""Region model for page-level spatial annotations.

A Region represents a visually identifiable area on a page with:
- A spatial label (WHERE on the page: text_block, footnote_area, etc.)
- Optional semantic labels (WHAT it means: footnote, citation, etc.)
- A normalized bounding box
- Optional transcribed text content

The multi-dimensional label principle is enforced here: `label` (spatial)
and `semantic_labels` (semantic) are independent axes. A region can be
label="text_block" with semantic_labels=["footnote"].
"""

from __future__ import annotations

from pydantic import Field

from scholargt.schema.base import BBox, GTElement
from scholargt.schema.labels import SemanticType, SpatialLabel


class Region(GTElement):
    """A spatial region on a page with optional semantic annotations.

    Inherits GTElement's id, verifications, tags, and extra="allow".
    """

    label: SpatialLabel = Field(description="Spatial layout type (where on page)")
    bbox: BBox = Field(description="Normalized bounding box [x0, y0, x1, y1]")
    text: str | None = Field(default=None, description="Transcribed text content (optional)")
    text_anchors: list[str] = Field(
        default_factory=list, description="Notable text spans within region"
    )
    semantic_labels: list[SemanticType] = Field(
        default_factory=list,
        description="Semantic meaning (independent dimension from spatial label)",
    )
    reading_order_index: int | None = Field(
        default=None, description="Position in reading order (optional)"
    )
