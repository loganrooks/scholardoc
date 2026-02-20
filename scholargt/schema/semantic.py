"""Semantic element models for ScholarGT ground truth annotation.

Contains 9 semantic element types as Pydantic models inheriting from GTElement,
supporting models (ContentSpan, ParsedCitation, BibliographicRecord, ToCEntry,
NoteSchema), and the SemanticElement discriminated union for polymorphic JSON
deserialization.

Semantic elements capture WHAT something means in a scholarly document -- notes,
citations, commentary apparatus, sections, cross-references, and philosophy-specific
constructs like sous rature and marginal reference systems (Stephanus, Bekker, Akademie).

v2.0.0 changes from v1.0.0:
- Note replaces Footnote + Endnote (unified model with LocationRef markers)
- Commentary added for philosophical/rabbinic running commentary apparatus
- Citation decomposed: CitationFormat (appearance) + ReferenceSystem (coordinates)
- BibEntry uses BibliographicRecord for full bibliography fields
- MarginalReference uses shared ReferenceSystem (eliminating MarginalRefType)
- MarkerInfo removed (replaced by LocationRef from base.py)
- NoteSchema added for document-level note numbering conventions
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from scholargt.schema.base import GTElement, LocationRef
from scholargt.schema.labels import CitationFormat, ReferenceSystem

# ---------- Supporting models (not elements themselves) ----------


class ContentSpan(BaseModel):
    """A span of content text, potentially spanning multiple pages.

    Used for note/commentary content that may continue across page boundaries.
    The is_continuation flag marks spans after the first page.
    char_offset and char_length support endnote positioning within shared regions.
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
    char_offset: int | None = Field(
        default=None,
        description="Character offset within region text (for endnote positioning in shared regions)",
    )
    char_length: int | None = Field(
        default=None,
        description="Length of this span within region text (for endnote positioning in shared regions)",
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


class BibliographicRecord(BaseModel):
    """Full bibliography entry data for BibEntry.

    Provides richer bibliographic fields than ParsedCitation, which is designed
    for in-text citation parsing. BibliographicRecord captures complete reference
    list entries with all standard bibliographic metadata.
    """

    author: str | None = Field(default=None, description="Author name(s)")
    title: str | None = Field(default=None, description="Work title")
    year: str | None = Field(default=None, description="Publication year")
    journal: str | None = Field(default=None, description="Journal name")
    volume: str | None = Field(default=None, description="Volume number")
    issue: str | None = Field(default=None, description="Issue number")
    pages: str | None = Field(default=None, description="Page range (e.g., '1-25')")
    publisher: str | None = Field(default=None, description="Publisher name")
    doi: str | None = Field(default=None, description="Digital Object Identifier")
    isbn: str | None = Field(default=None, description="ISBN number")
    url: str | None = Field(default=None, description="URL for online resources")
    edition: str | None = Field(default=None, description="Edition (e.g., '2nd')")
    editor: str | None = Field(default=None, description="Editor name(s)")
    translator: str | None = Field(default=None, description="Translator name(s)")
    work_abbreviation: str | None = Field(
        default=None,
        description="Standard abbreviation (e.g., 'SZ' for Sein und Zeit, 'KrV' for Kritik der reinen Vernunft)",
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


class NoteSchema(BaseModel):
    """Document-level note numbering convention.

    Describes how notes are numbered/marked throughout a document or section.
    Multiple NoteSchemas can coexist (e.g., author footnotes use symbols,
    translator footnotes use arabic numerals). Referenced by Note.note_schema_id.
    """

    schema_id: str = Field(description="Unique identifier for this note schema")
    marker_type: Literal[
        "arabic",
        "roman_lower",
        "roman_upper",
        "alphabetical_lower",
        "alphabetical_upper",
        "symbolic",
        "custom",
    ] = Field(description="Type of marker used for notes")
    symbol_sequence: list[str] | None = Field(
        default=None,
        description="For symbolic markers: sequence of symbols (e.g., ['*', 'dagger', 'double_dagger', 'section', 'parallel', 'pilcrow'])",
    )
    reset_boundary: Literal["page", "chapter", "section", "essay", "document"] | None = Field(
        default=None,
        description="Where note numbering resets (e.g., per-page, per-chapter)",
    )
    placement: Literal["page_bottom", "end_of_chapter", "end_of_book", "margin"] | None = Field(
        default=None,
        description="Where note content is placed in the document",
    )
    note_source: Literal["author", "translator", "editor"] | None = Field(
        default=None,
        description="Who wrote the notes using this schema",
    )


# ---------- Element models (each with discriminated element_type) ----------


class Note(GTElement):
    """A note (unified model replacing Footnote + Endnote).

    Uses LocationRef for precise marker positioning instead of the old MarkerInfo.
    Supports multi-page notes via ContentSpan list with is_continuation flags.
    Placement distinguishes footnotes (page_bottom) from endnotes (end_of_chapter,
    end_of_book) and marginal notes (margin).
    """

    element_type: Literal["note"] = "note"
    body_marker: LocationRef = Field(
        description="Where reference marker appears in body text"
    )
    content_marker: LocationRef | None = Field(
        default=None,
        description="Where note content begins (important for endnotes where content is distant from marker)",
    )
    content: list[ContentSpan] = Field(
        description="Content spans (may cross pages)"
    )
    placement: Literal["page_bottom", "end_of_chapter", "end_of_book", "margin"] = Field(
        description="Where the note content appears in the document"
    )
    scope: Literal["page", "chapter", "section", "essay", "document"] | None = Field(
        default=None,
        description="Scope of the numbering reset boundary for this note",
    )
    note_source: Literal["author", "translator", "editor"] | None = Field(
        default=None, description="Who wrote the note"
    )
    marker_text: str | None = Field(
        default=None,
        description="Marker display text (e.g., '1', '*', 'a')",
    )
    note_schema_id: str | None = Field(
        default=None,
        description="Reference to NoteSchema in DocumentGT for numbering convention",
    )


class Commentary(GTElement):
    """A running commentary annotation (philosophical/rabbinic commentary apparatus).

    Represents structured commentary that references a specific passage using
    a reference system. Supports multi-layer commentary (e.g., Rashi + Tosafot
    on the same Talmudic passage, or editor + translator commentary).
    """

    element_type: Literal["commentary"] = "commentary"
    source: str = Field(
        description="Who wrote the commentary (e.g., 'Rashi', 'editor', 'translator')"
    )
    passage_ref: str = Field(
        description="What passage it comments on (canonical coordinates, e.g., 'Gen 1:1', '264a')"
    )
    reference_system: ReferenceSystem = Field(
        description="How it locates the passage (e.g., CATCHWORD, CHAPTER_VERSE)"
    )
    target_location: LocationRef | None = Field(
        default=None,
        description="Optional precise location of the referenced passage in the GT corpus",
    )
    content: list[ContentSpan] = Field(
        description="Commentary content spans (may cross pages)"
    )
    layer: str | None = Field(
        default=None,
        description="Commentary layer identifier for multi-layer commentary (e.g., 'rashi', 'tosafot')",
    )


class Citation(GTElement):
    """An in-text citation reference.

    v2.0.0: Decomposes the old CitationType into two dimensions:
    - citation_format: How it appears in text (parenthetical, numeric, etc.)
    - reference_system: What coordinates locate the passage (Stephanus, Bekker, etc.)
    """

    element_type: Literal["citation"] = "citation"
    raw_text: str = Field(description="Citation text as it appears in source")
    citation_format: CitationFormat = Field(
        description="How the citation appears in text (e.g., parenthetical, numeric)"
    )
    reference_system: ReferenceSystem | None = Field(
        default=None,
        description="What coordinates locate the referenced passage (e.g., Stephanus, Bekker)",
    )
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
    """A bibliography/references list entry.

    v2.0.0: Uses BibliographicRecord for full bibliography fields instead of
    ParsedCitation which is designed for in-text citation parsing.
    """

    element_type: Literal["bibliography_entry"] = "bibliography_entry"
    raw_text: str = Field(description="Full bibliography entry text")
    record: BibliographicRecord | None = Field(
        default=None, description="Structured bibliographic record data"
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

    v2.0.0: Uses shared ReferenceSystem enum instead of the old MarginalRefType,
    eliminating duplication between Citation and MarginalReference.
    """

    element_type: Literal["marginal_reference"] = "marginal_reference"
    raw_text: str = Field(description="Reference text as displayed in margin")
    reference_system: ReferenceSystem = Field(
        description="Type of marginal reference system (e.g., Stephanus, Bekker)"
    )
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
    Note
    | Commentary
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

v2.0.0: Includes Note and Commentary; excludes old Footnote and Endnote.
"""
