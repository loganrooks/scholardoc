"""Semantic element models for ScholarGT ground truth annotation.

Contains all 9 semantic element types as Pydantic models inheriting from GTElement,
supporting models (MarkerInfo, ContentSpan, ParsedCitation, ToCEntry), and the
SemanticElement discriminated union for polymorphic JSON deserialization.

Semantic elements capture WHAT something means in a scholarly document -- footnotes,
citations, sections, cross-references, and philosophy-specific constructs like
sous rature and marginal reference systems (Stephanus, Bekker, Akademie).
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from scholargt.schema.base import GTElement
from scholargt.schema.labels import CitationType, MarginalRefType

# ---------- Supporting models (not elements themselves) ----------


class MarkerInfo(BaseModel):
    """Information about a footnote/endnote marker in the source text."""

    text: str = Field(description="Marker text as displayed (e.g., '1', '*', 'a')")
    page: int = Field(description="0-based page index where marker appears")
    region_id: str | None = Field(
        default=None, description="Region ID containing the marker"
    )
    char_offset: int | None = Field(
        default=None, description="Character offset of marker within region text"
    )


class ContentSpan(BaseModel):
    """A span of content text, potentially spanning multiple pages.

    Used for footnote/endnote content that may continue across page boundaries.
    The is_continuation flag marks spans after the first page.
    """

    page: int = Field(description="0-based page index for this span")
    region_id: str | None = Field(
        default=None, description="Region ID containing this span"
    )
    text: str = Field(description="Text content of this span")
    is_continuation: bool = Field(
        default=False,
        description="True if this span continues from a previous page",
    )


class ParsedCitation(BaseModel):
    """Structured citation data extracted from raw citation text."""

    author: str | None = Field(default=None, description="Author name(s)")
    year: str | None = Field(default=None, description="Publication year")
    page_ref: str | None = Field(
        default=None, description="Page reference within cited work"
    )
    work: str | None = Field(
        default=None, description="Work title or abbreviation (e.g., 'SZ', 'KrV')"
    )


class ToCEntry(BaseModel):
    """A single entry in a table of contents."""

    title: str = Field(description="Section/chapter title")
    level: int = Field(description="Nesting level (0 = top-level)")
    page_label: str | None = Field(
        default=None, description="Printed page number (e.g., '127', 'xiv')"
    )
    page_index: int | None = Field(
        default=None, description="0-based PDF page index"
    )


# ---------- Element models (each with discriminated element_type) ----------


class Footnote(GTElement):
    """A footnote with marker location and content spans.

    Supports multi-page footnotes via ContentSpan list with is_continuation flags.
    """

    element_type: Literal["footnote"] = "footnote"
    marker: MarkerInfo = Field(description="Marker location in source text")
    content: list[ContentSpan] = Field(description="Content spans (may cross pages)")
    note_source: Literal["author", "translator", "editor"] | None = Field(
        default=None, description="Who wrote the note"
    )
    location: Literal["page_bottom", "endnote", "margin"] = Field(
        description="Where the note content appears"
    )


class Endnote(GTElement):
    """An endnote with marker location and content spans.

    Similar to Footnote but collected at end of chapter/book rather than page bottom.
    """

    element_type: Literal["endnote"] = "endnote"
    marker: MarkerInfo = Field(description="Marker location in source text")
    content: list[ContentSpan] = Field(description="Content spans (may cross pages)")
    note_source: Literal["author", "translator", "editor"] | None = Field(
        default=None, description="Who wrote the note"
    )
    section_title: str | None = Field(
        default=None, description="Title of the endnote section"
    )


class Citation(GTElement):
    """An in-text citation reference.

    Supports 7 citation types including philosophy-specific Stephanus, Bekker,
    and Akademie reference systems.
    """

    element_type: Literal["citation"] = "citation"
    raw_text: str = Field(description="Citation text as it appears in source")
    citation_type: CitationType = Field(description="Classification of citation style")
    parsed: ParsedCitation | None = Field(
        default=None, description="Structured parsed citation data"
    )
    bib_entry_id: str | None = Field(
        default=None, description="Link to bibliography entry element ID"
    )
    page: int | None = Field(
        default=None, description="Page where citation appears"
    )
    region_id: str | None = Field(
        default=None, description="Region containing the citation"
    )


class BibEntry(GTElement):
    """A bibliography/references list entry."""

    element_type: Literal["bibliography_entry"] = "bibliography_entry"
    raw_text: str = Field(description="Full bibliography entry text")
    parsed: ParsedCitation | None = Field(
        default=None, description="Structured parsed citation data"
    )
    entry_index: int | None = Field(
        default=None, description="Position in bibliography list (0-based)"
    )


class Section(GTElement):
    """A document section/chapter with hierarchical structure."""

    element_type: Literal["section"] = "section"
    title: str = Field(description="Section title text")
    level: int = Field(description="Nesting level (0 = top-level)")
    page_start: int | None = Field(
        default=None, description="First page of section (0-based)"
    )
    page_end: int | None = Field(
        default=None, description="Last page of section (0-based)"
    )
    children: list[str] = Field(
        default_factory=list, description="Child section element IDs"
    )


class SousRature(GTElement):
    """Text written 'under erasure' (sous rature) -- a Derridean philosophical concept.

    Represents text that is simultaneously present and crossed out, indicating
    a term that is inadequate yet necessary. Common in continental philosophy.
    """

    element_type: Literal["sous_rature"] = "sous_rature"
    text: str = Field(description="The text under erasure")
    page: int = Field(description="Page where it appears (0-based)")
    region_id: str | None = Field(
        default=None, description="Region containing the text"
    )
    char_offset: int | None = Field(
        default=None, description="Character offset within region text"
    )
    char_length: int | None = Field(
        default=None, description="Length of crossed-out text in characters"
    )


class CrossReference(GTElement):
    """An internal cross-reference within the document (e.g., 'see section 3')."""

    element_type: Literal["cross_reference"] = "cross_reference"
    raw_text: str = Field(description="Cross-reference text as displayed")
    target_page: int | None = Field(
        default=None, description="Target page index (0-based)"
    )
    target_section_id: str | None = Field(
        default=None, description="Target section element ID"
    )
    page: int = Field(description="Page where reference appears (0-based)")
    region_id: str | None = Field(
        default=None, description="Region containing the reference"
    )


class MarginalReference(GTElement):
    """A marginal reference system annotation (Stephanus, Bekker, Akademie, custom).

    Philosophy texts use standard reference systems in margins: Stephanus pagination
    for Plato, Bekker numbers for Aristotle, Akademie edition numbers for Kant.
    """

    element_type: Literal["marginal_reference"] = "marginal_reference"
    raw_text: str = Field(description="Reference text as displayed in margin")
    ref_type: MarginalRefType = Field(description="Type of marginal reference system")
    page: int = Field(description="Page where reference appears (0-based)")
    region_id: str | None = Field(
        default=None, description="Region containing the reference"
    )


class PageNumberAnnotation(GTElement):
    """A page number annotation capturing the display format and mapping.

    Maps between printed page labels (roman, arabic) and PDF page indices.
    """

    element_type: Literal["page_number_annotation"] = "page_number_annotation"
    display_text: str = Field(description="Page number as displayed (e.g., 'xiv', '127')")
    number_type: Literal["arabic", "roman", "mixed"] = Field(
        description="Type of page numbering system"
    )
    page_index: int = Field(description="0-based PDF page index")


# ---------- Discriminated union ----------

SemanticElement = Annotated[
    Footnote
    | Endnote
    | Citation
    | BibEntry
    | Section
    | SousRature
    | CrossReference
    | MarginalReference
    | PageNumberAnnotation,
    Field(discriminator="element_type"),
]
"""Discriminated union of all semantic element types.

Uses Pydantic's discriminated union on the `element_type` field to enable
polymorphic JSON deserialization: a list of mixed element dicts can be
deserialized into the correct Python types based on element_type value.
"""
