"""Formatting annotation model for ScholarGT.

Captures text decoration (bold, italic, underline, etc.) with character-level
offsets for precise annotation of formatted text spans within regions.
"""

from __future__ import annotations

from pydantic import Field

from scholargt.schema.base import GTElement
from scholargt.schema.labels import FormattingType


class FormattingAnnotation(GTElement):
    """A text formatting/decoration annotation with character-level positioning.

    Tracks formatting at character granularity within a page region, enabling
    precise reconstruction of bold, italic, small caps, and other decorations.
    """

    formatting_type: FormattingType = Field(
        description="Type of text formatting (bold, italic, etc.)"
    )
    page: int = Field(description="Page where formatting appears (0-based)")
    region_id: str | None = Field(
        default=None, description="Region containing the formatted text"
    )
    char_offset: int = Field(
        description="Character offset of formatting start within region text"
    )
    char_length: int = Field(
        description="Length of formatted text span in characters"
    )
    text: str | None = Field(
        default=None, description="The formatted text span (optional, for convenience)"
    )
