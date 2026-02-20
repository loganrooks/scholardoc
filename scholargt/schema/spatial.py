"""Region model for page-level spatial annotations.

A Region represents a visually identifiable area on a page with:
- A spatial label (WHERE on the page: text_block, note_area, etc.)
- Optional semantic labels (WHAT it means: note, citation, etc.)
- A normalized bounding box
- Optional transcribed text content
- Cross-page continuation flags for multi-page content
- Sub-region hierarchy for nested structures (table cells, figures within figures)
- Register identity for multi-register layouts (SFP-1)
- Explicit text direction for RTL/bidi content (SFP-2)

The multi-dimensional label principle is enforced here: `label` (spatial)
and `semantic_labels` (semantic) are independent axes. A region can be
label="text_block" with semantic_labels=["note"].
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from scholargt.schema.base import BBox, GTElement
from scholargt.schema.labels import SemanticType, SpatialLabel


class Region(GTElement):
    """A spatial region on a page with optional semantic annotations.

    Inherits GTElement's id, verifications, tags, and extra="allow".

    Supports cross-page continuation (is_continuation, continues_to_next),
    sub-region hierarchy (children), register identity (register_id, SFP-1),
    and explicit text direction (text_direction, SFP-2).
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

    # Cross-page continuation
    is_continuation: bool = Field(
        default=False,
        description="True if this region continues content from a previous page",
    )
    continues_to_next: bool = Field(
        default=False,
        description="True if this region's content continues to the next page",
    )

    # Semantic element back-references
    semantic_element_ids: list[str] = Field(
        default_factory=list,
        description="IDs of DocumentGT semantic elements associated with this region",
    )

    # Sub-region hierarchy
    children: list[Region] = Field(
        default_factory=list,
        description="Sub-regions (table cells, figures within figures, block quotes within notes)",
    )

    # SFP-1: Register identity
    register_id: str | None = Field(
        default=None,
        description="LayoutRegister this region belongs to (SFP-1, e.g., 'main_text', 'commentary_rashi')",
    )

    # SFP-2: Text direction
    text_direction: Literal["ltr", "rtl", "bidi"] | None = Field(
        default=None,
        description="Base text direction for this region's content (SFP-2)",
    )
