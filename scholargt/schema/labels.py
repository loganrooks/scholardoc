"""Label enums for the ScholarGT universal annotation taxonomy.

All enums use the (str, Enum) pattern so they serialize as strings in JSON.
8 enums organized by dimension:
  - Spatial: WHERE on the page (SpatialLabel)
  - Semantic: WHAT it means (SemanticType)
  - Formatting: HOW text is decorated (FormattingType)
  - Script: Script variant beyond BCP 47 (ScriptVariant)
  - Citation format: How citation appears in text (CitationFormat)
  - Reference system: What coordinates locate a passage (ReferenceSystem)
  - Citation style: Document-level citation convention (CitationStyle)
  - Document structure: Document-level annotation categories (DocumentSectionType)
"""

from enum import Enum


class SpatialLabel(str, Enum):
    """Spatial layout region types -- WHERE on the page.

    21 values for visual layout detection. Used by the spatial label
    evaluation task to assess region classification accuracy.
    NOTE_AREA and NOTE_CONTINUATION replace the old FOOTNOTE_AREA,
    ENDNOTE_AREA, and FOOTNOTE_CONTINUATION (notes are unified).
    """

    TEXT_BLOCK = "text_block"
    NOTE_AREA = "note_area"
    NOTE_CONTINUATION = "note_continuation"
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
    TOC_AREA = "toc_area"
    ABSTRACT = "abstract"
    CODE_BLOCK = "code_block"
    INDEX_AREA = "index_area"
    UNKNOWN = "unknown"


class SemanticType(str, Enum):
    """Semantic element types -- WHAT it means.

    9 values independent from spatial labels. A region can be spatially
    'text_block' and semantically 'note'. Used by the semantic element
    evaluation task to assess element classification accuracy.
    NOTE replaces the old FOOTNOTE + ENDNOTE split; COMMENTARY added
    for philosophical/rabbinic running commentary.
    """

    NOTE = "note"
    CITATION = "citation"
    BIBLIOGRAPHY_ENTRY = "bibliography_entry"
    SECTION = "section"
    SOUS_RATURE = "sous_rature"
    CROSS_REFERENCE = "cross_reference"
    MARGINAL_REFERENCE = "marginal_reference"
    PAGE_NUMBER_ANNOTATION = "page_number_annotation"
    COMMENTARY = "commentary"


class FormattingType(str, Enum):
    """Text formatting/decoration types -- HOW text is decorated.

    9 values for inline formatting evaluation. SUBSCRIPT, MONOSPACE,
    and COLOR added per SFP-4 for mathematical notation, code samples,
    and highlighted/colored text spans.
    """

    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    STRIKETHROUGH = "strikethrough"
    SMALL_CAPS = "small_caps"
    SUPERSCRIPT = "superscript"
    SUBSCRIPT = "subscript"
    MONOSPACE = "monospace"
    COLOR = "color"


class ScriptVariant(str, Enum):
    """Script variants where BCP 47 script subtag is insufficient (SFP-3).

    6 values for script variant detection. Primary use case: Rashi script
    vs square Hebrew -- both are "he-Hebr" in BCP 47 but typographically
    distinct with different OCR models. Also covers Arabic calligraphic
    styles (Nastaliq vs Naskh) and historical European scripts (Fraktur).
    CUSTOM allows project-specific script variants beyond the built-in set.
    """

    SQUARE_HEBREW = "square_hebrew"
    RASHI_SCRIPT = "rashi_script"
    NASTALIQ = "nastaliq"
    NASKH = "naskh"
    FRAKTUR = "fraktur"
    CUSTOM = "custom"


class CitationFormat(str, Enum):
    """How a citation appears in the text -- citation format evaluation.

    5 values replacing the old CitationType enum. Decomposes the format
    dimension from the reference system dimension (now in ReferenceSystem).
    """

    PARENTHETICAL = "parenthetical"
    NUMERIC = "numeric"
    INLINE_AUTHOR = "inline_author"
    NOTE_BASED = "note_based"
    AUTHOR_TITLE = "author_title"


class ReferenceSystem(str, Enum):
    """What coordinates locate the referenced passage.

    13 values shared by Citation and MarginalReference, eliminating
    the old MarginalRefType duplication. CATCHWORD added per SFP-6
    for pre-modern printed books where page headers serve as navigation
    aids rather than standard pagination.
    """

    STANDARD = "standard"
    STEPHANUS = "stephanus"
    BEKKER = "bekker"
    AKADEMIE = "akademie"
    AB_EDITION = "ab_edition"
    PARAGRAPH = "paragraph"
    SZ_PAGINATION = "sz_pagination"
    DIELS_KRANZ = "diels_kranz"
    LINE_NUMBER = "line_number"
    CHAPTER_VERSE = "chapter_verse"
    LEGAL = "legal"
    CATCHWORD = "catchword"
    CUSTOM = "custom"


class CitationStyle(str, Enum):
    """Document-level citation convention -- citation style evaluation.

    7 values describing the overall citation style used in a document.
    Set at the document level, not per-citation.
    """

    APA = "apa"
    CHICAGO_NB = "chicago_nb"
    CHICAGO_AD = "chicago_ad"
    MLA = "mla"
    VANCOUVER = "vancouver"
    TURABIAN = "turabian"
    CUSTOM = "custom"


class DocumentSectionType(str, Enum):
    """Document-level annotation categories.

    Renamed from DocumentType to avoid collision with
    DocumentSource.document_type Literal field.
    """

    METADATA = "metadata"
    TOC = "toc"
    FRONT_MATTER = "front_matter"
    BACK_MATTER = "back_matter"
    NOTE_SCHEMA = "note_schema"
