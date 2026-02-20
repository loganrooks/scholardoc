"""Formatting annotation model for ScholarGT.

Captures text decoration (bold, italic, underline, etc.) with character-level
offsets for precise annotation of formatted text spans within regions.

v2.0.0 additions:
- language: BCP 47 language tag for mixed-language text annotation
- script_variant: Script variant beyond BCP 47 (SFP-3, e.g., Rashi vs square Hebrew)
- color_value: CSS color value when formatting_type is COLOR (SFP-4)
- color_semantic: Semantic meaning of the color (SFP-4, e.g., 'gemara_text')
"""

from __future__ import annotations

import warnings

from pydantic import Field, model_validator

from scholargt.schema.base import GTElement
from scholargt.schema.labels import FormattingType, ScriptVariant


class FormattingAnnotation(GTElement):
    """A text formatting/decoration annotation with character-level positioning.

    Tracks formatting at character granularity within a page region, enabling
    precise reconstruction of bold, italic, small caps, and other decorations.

    Supports language tagging (BCP 47), script variant identification (SFP-3),
    and color annotation with semantic meaning (SFP-4).
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

    # BCP 47 language tag
    language: str | None = Field(
        default=None,
        description="BCP 47 language tag for this span (e.g., 'de', 'el', 'la', 'he')",
    )

    # SFP-3: Script variant
    script_variant: ScriptVariant | None = Field(
        default=None,
        description="Script variant when BCP 47 script subtag is insufficient (SFP-3, e.g., Rashi vs square Hebrew)",
    )

    # SFP-4: Color fields
    color_value: str | None = Field(
        default=None,
        description="CSS color value when formatting_type is COLOR (e.g., '#FF0000', 'red')",
    )
    color_semantic: str | None = Field(
        default=None,
        description="Semantic meaning of the color (e.g., 'gemara_text', 'mishnah_text')",
    )

    @model_validator(mode="after")
    def _check_color_consistency(self) -> FormattingAnnotation:
        """Warn about inconsistent COLOR / color_value usage.

        Warnings (not errors) because annotation may be incremental --
        color_value might be added in a later annotation pass.
        """
        if self.formatting_type == FormattingType.COLOR and self.color_value is None:
            warnings.warn(
                "FormattingAnnotation has formatting_type=COLOR but color_value is None; "
                "consider setting color_value for complete color annotation",
                UserWarning,
                stacklevel=2,
            )
        if self.color_value is not None and self.formatting_type != FormattingType.COLOR:
            warnings.warn(
                f"FormattingAnnotation has color_value='{self.color_value}' but "
                f"formatting_type={self.formatting_type.value} (not COLOR); "
                "color_value is typically used with formatting_type=COLOR",
                UserWarning,
                stacklevel=2,
            )
        return self
