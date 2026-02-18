"""Label enums for the ScholarGT universal annotation taxonomy.

All enums use the (str, Enum) pattern so they serialize as strings in JSON.
Labels are organized by dimension (spatial, semantic, formatting, document, quality)
following the multi-dimensional principle: spatial and semantic are independent axes.

Spatial labels: WHERE on the page (17 values)
Semantic types: WHAT it means (9 values)
Formatting types: HOW text is decorated (6 values)
Document types: Document-level annotation categories (5 values)
Quality labels: Page quality assessment (scan_quality, difficulty)
Citation types: Sublabels for citation classification (7 values)
Marginal reference types: Sublabels for marginal reference systems (4 values)
"""

from enum import Enum


class SpatialLabel(str, Enum):
    """Spatial layout region types -- WHERE on the page.

    Unified from ScholarDoc region types and CryptOfCogito region labels.
    """

    TEXT_BLOCK = "text_block"
    FOOTNOTE_AREA = "footnote_area"
    ENDNOTE_AREA = "endnote_area"
    PAGE_HEADER = "page_header"
    PAGE_FOOTER = "page_footer"
    PAGE_NUMBER = "page_number"
    SECTION_HEADER = "section_header"
    TITLE = "title"
    BLOCK_QUOTE = "block_quote"
    LIST_ITEM = "list_item"
    TABLE = "table"
    FIGURE = "figure"
    CAPTION = "caption"
    FORMULA = "formula"
    MARGINAL_NOTE = "marginal_note"
    BIBLIOGRAPHY_AREA = "bibliography_area"
    FOOTNOTE_CONTINUATION = "footnote_continuation"


class SemanticType(str, Enum):
    """Semantic element types -- WHAT it means.

    Independent dimension from spatial labels. A region can be spatially
    'text_block' and semantically 'footnote'.
    """

    FOOTNOTE = "footnote"
    ENDNOTE = "endnote"
    CITATION = "citation"
    BIBLIOGRAPHY_ENTRY = "bibliography_entry"
    SECTION = "section"
    SOUS_RATURE = "sous_rature"
    CROSS_REFERENCE = "cross_reference"
    MARGINAL_REFERENCE = "marginal_reference"
    PAGE_NUMBER_ANNOTATION = "page_number_annotation"


class FormattingType(str, Enum):
    """Text formatting/decoration types."""

    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    STRIKETHROUGH = "strikethrough"
    SMALL_CAPS = "small_caps"
    SUPERSCRIPT = "superscript"


class DocumentType(str, Enum):
    """Document-level annotation categories."""

    METADATA = "metadata"
    TOC = "toc"
    FRONT_MATTER = "front_matter"
    BACK_MATTER = "back_matter"
    NOTE_SCHEMA = "note_schema"


class ScanQuality(str, Enum):
    """Page scan quality assessment."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Difficulty(str, Enum):
    """Page annotation difficulty for test stratification."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class CitationType(str, Enum):
    """Citation style sublabels."""

    AUTHOR_DATE = "author_date"
    NUMERIC = "numeric"
    ABBREVIATED = "abbreviated"
    FOOTNOTE_STYLE = "footnote_style"
    STEPHANUS = "stephanus"
    BEKKER = "bekker"
    AK_REFERENCE = "ak_reference"


class MarginalRefType(str, Enum):
    """Marginal reference system sublabels."""

    STEPHANUS = "stephanus"
    BEKKER = "bekker"
    AKADEMIE = "akademie"
    CUSTOM = "custom"
