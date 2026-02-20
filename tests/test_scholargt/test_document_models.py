"""Tests for DocumentGT and related document-level models.

Covers DocumentGT creation, cross-page semantic elements via discriminated union,
document structure (ToC, sections), LayoutRegister (SFP-1), NoteSchema,
CitationStyle, round-trip JSON serialization, extra field compatibility,
and a realistic Heidegger Being and Time example using v2.0.0 models.

v2.0.0 changes:
- Note replaces Footnote/Endnote in elements
- Citation uses CitationFormat/ReferenceSystem (not CitationType)
- DocumentRelationships/FootnoteLink/CitationBibLink removed
- LayoutRegister (SFP-1) for multi-register documents
- NoteSchema for note numbering conventions
- citation_style at document level
"""

from datetime import UTC, datetime

import pytest

from scholargt.schema import (
    SCHEMA_VERSION,
    BibEntry,
    BibliographicRecord,
    Citation,
    ContentSpan,
    DocumentGT,
    DocumentSource,
    DocumentStructure,
    FormattingAnnotation,
    LayoutRegister,
    Note,
    NoteSchema,
    PageNumberAnnotation,
    ParsedCitation,
    Section,
    SemanticElement,
    ToCEntry,
)
from scholargt.schema.base import LocationRef, VerificationRecord
from scholargt.schema.labels import (
    CitationFormat,
    CitationStyle,
    FormattingType,
    ReferenceSystem,
)

# ---------- DocumentSource tests ----------


class TestDocumentSource:
    def test_minimal_source(self):
        src = DocumentSource(pdf="test.pdf")
        assert src.pdf == "test.pdf"
        assert src.title is None
        assert src.author is None
        assert src.document_type is None

    def test_full_source(self):
        src = DocumentSource(
            pdf="heidegger_sz.pdf",
            title="Being and Time",
            author="Martin Heidegger",
            translator="John Macquarrie",
            year=1962,
            publisher="Harper & Row",
            isbn="978-0-06-063850-0",
            doi=None,
            document_type="translation",
        )
        assert src.title == "Being and Time"
        assert src.year == 1962
        assert src.document_type == "translation"


# ---------- DocumentStructure tests ----------


class TestDocumentStructure:
    def test_empty_structure(self):
        ds = DocumentStructure()
        assert ds.toc == []
        assert ds.sections == []
        assert ds.front_matter is None
        assert ds.back_matter is None

    def test_structure_with_toc(self):
        ds = DocumentStructure(
            toc=[
                ToCEntry(title="Introduction", level=0, page_label="1"),
                ToCEntry(
                    title="Division One",
                    level=0,
                    page_label="41",
                    page_index=65,
                ),
                ToCEntry(
                    title="Being-in-the-World",
                    level=1,
                    page_label="53",
                ),
            ],
            sections=["sec_intro", "sec_div1", "sec_biw"],
        )
        assert len(ds.toc) == 3
        assert ds.toc[1].page_index == 65
        assert len(ds.sections) == 3

    def test_structure_with_front_back_matter(self):
        ds = DocumentStructure(
            front_matter={"preface": True, "dedication": "To Husserl"},
            back_matter={"index": True, "bibliography": True},
        )
        assert ds.front_matter["preface"] is True
        assert ds.back_matter["bibliography"] is True


# ---------- LayoutRegister tests (SFP-1) ----------


class TestLayoutRegister:
    def test_create_layout_register(self):
        reg = LayoutRegister(
            register_id="main_text",
            name="Main Text",
        )
        assert reg.register_id == "main_text"
        assert reg.name == "Main Text"
        assert reg.author is None
        assert reg.language is None

    def test_layout_register_full(self):
        reg = LayoutRegister(
            register_id="rashi",
            name="Rashi Commentary",
            author="Rashi",
            language="he",
            text_direction="rtl",
            position_convention="inner_margin",
            typeface_convention="rashi_script",
        )
        assert reg.register_id == "rashi"
        assert reg.author == "Rashi"
        assert reg.language == "he"
        assert reg.text_direction == "rtl"
        assert reg.position_convention == "inner_margin"
        assert reg.typeface_convention == "rashi_script"

    def test_layout_register_bilingual(self):
        """Bilingual edition: Hebrew + English registers."""
        he_reg = LayoutRegister(
            register_id="hebrew_text",
            name="Hebrew Original",
            language="he",
            text_direction="rtl",
            position_convention="right_column",
        )
        en_reg = LayoutRegister(
            register_id="english_text",
            name="English Translation",
            language="en",
            text_direction="ltr",
            position_convention="left_column",
        )
        assert he_reg.text_direction == "rtl"
        assert en_reg.text_direction == "ltr"

    def test_layout_register_talmud(self):
        """Talmud page layout: Gemara + Rashi + Tosafot registers."""
        registers = [
            LayoutRegister(
                register_id="gemara",
                name="Gemara",
                language="he-arc",
                text_direction="rtl",
                position_convention="central",
                typeface_convention="square_hebrew",
            ),
            LayoutRegister(
                register_id="rashi",
                name="Rashi",
                author="Rashi",
                language="he",
                text_direction="rtl",
                position_convention="inner_margin",
                typeface_convention="rashi_script",
            ),
            LayoutRegister(
                register_id="tosafot",
                name="Tosafot",
                author="Tosafot",
                language="he",
                text_direction="rtl",
                position_convention="outer_margin",
                typeface_convention="square_hebrew",
            ),
        ]
        assert len(registers) == 3
        assert registers[1].typeface_convention == "rashi_script"

    def test_layout_register_json_round_trip(self):
        reg = LayoutRegister(
            register_id="hegel",
            name="Hegel Text",
            author="Hegel",
            language="de",
            text_direction="ltr",
            position_convention="left_column",
        )
        json_str = reg.model_dump_json()
        restored = LayoutRegister.model_validate_json(json_str)
        assert restored.register_id == "hegel"
        assert restored.author == "Hegel"


# ---------- DocumentGT tests ----------


class TestDocumentGT:
    def test_minimal_document(self):
        doc = DocumentGT(
            document_id="test_doc",
            source=DocumentSource(pdf="test.pdf"),
        )
        assert doc.document_id == "test_doc"
        assert doc.source.pdf == "test.pdf"
        assert doc.elements == []
        assert doc.formatting == []
        assert doc.structure is None
        assert doc.registers == []
        assert doc.note_schemas == []
        assert doc.citation_style is None
        assert doc.config_profile is None
        assert doc.verifications == []

    def test_schema_version_defaults(self):
        doc = DocumentGT(
            document_id="d1",
            source=DocumentSource(pdf="test.pdf"),
        )
        assert doc.schema_version == SCHEMA_VERSION

    def test_document_with_source_metadata(self):
        doc = DocumentGT(
            document_id="sz_1962",
            source=DocumentSource(
                pdf="being_and_time.pdf",
                title="Being and Time",
                author="Martin Heidegger",
                translator="John Macquarrie",
                year=1962,
                document_type="translation",
            ),
        )
        assert doc.source.author == "Martin Heidegger"
        assert doc.source.translator == "John Macquarrie"

    def test_document_with_mixed_elements(self):
        """DocumentGT.elements accepts mixed SemanticElement types (v2.0.0)."""
        doc = DocumentGT(
            document_id="d1",
            source=DocumentSource(pdf="test.pdf"),
            elements=[
                Note(
                    id="n1",
                    body_marker=LocationRef(page=0, region_id="r1"),
                    content=[ContentSpan(page=0, text="Note")],
                    placement="page_bottom",
                ),
                Citation(
                    id="ct1",
                    raw_text="(Heidegger 1927)",
                    citation_format=CitationFormat.PARENTHETICAL,
                ),
                Section(
                    id="sec1",
                    title="Introduction",
                    level=0,
                ),
            ],
        )
        assert len(doc.elements) == 3
        assert isinstance(doc.elements[0], Note)
        assert isinstance(doc.elements[1], Citation)
        assert isinstance(doc.elements[2], Section)

    def test_document_elements_discriminated_union_from_json(self):
        """Elements deserialize correctly via discriminated union (v2.0.0)."""
        json_str = """{
            "document_id": "d1",
            "source": {"pdf": "test.pdf"},
            "elements": [
                {
                    "id": "n1",
                    "element_type": "note",
                    "body_marker": {"page": 0, "region_id": "r1"},
                    "content": [{"page": 0, "text": "Note"}],
                    "placement": "page_bottom"
                },
                {
                    "id": "ct1",
                    "element_type": "citation",
                    "raw_text": "(Heidegger 1927)",
                    "citation_format": "parenthetical"
                }
            ]
        }"""
        doc = DocumentGT.model_validate_json(json_str)
        assert len(doc.elements) == 2
        assert isinstance(doc.elements[0], Note)
        assert isinstance(doc.elements[1], Citation)

    def test_document_with_structure(self):
        doc = DocumentGT(
            document_id="d1",
            source=DocumentSource(pdf="test.pdf"),
            structure=DocumentStructure(
                toc=[
                    ToCEntry(title="Intro", level=0, page_index=0),
                ],
                sections=["sec_intro"],
            ),
        )
        assert doc.structure is not None
        assert len(doc.structure.toc) == 1
        assert doc.structure.sections == ["sec_intro"]

    def test_document_with_registers(self):
        """SFP-1: DocumentGT with LayoutRegister list."""
        doc = DocumentGT(
            document_id="talmud_1",
            source=DocumentSource(pdf="talmud.pdf"),
            registers=[
                LayoutRegister(
                    register_id="gemara",
                    name="Gemara",
                    language="he-arc",
                    text_direction="rtl",
                ),
                LayoutRegister(
                    register_id="rashi",
                    name="Rashi",
                    author="Rashi",
                    language="he",
                    text_direction="rtl",
                ),
            ],
        )
        assert len(doc.registers) == 2
        assert doc.registers[0].register_id == "gemara"
        assert doc.registers[1].author == "Rashi"

    def test_document_with_note_schemas(self):
        doc = DocumentGT(
            document_id="d1",
            source=DocumentSource(pdf="test.pdf"),
            note_schemas=[
                NoteSchema(
                    schema_id="translator_footnotes",
                    marker_type="arabic",
                    reset_boundary="page",
                    placement="page_bottom",
                    note_source="translator",
                ),
                NoteSchema(
                    schema_id="author_footnotes",
                    marker_type="symbolic",
                    symbol_sequence=["*", "dagger"],
                    reset_boundary="page",
                    placement="page_bottom",
                    note_source="author",
                ),
            ],
        )
        assert len(doc.note_schemas) == 2
        assert doc.note_schemas[0].schema_id == "translator_footnotes"

    def test_document_note_schema_duplicate_warns(self):
        """NoteSchema uniqueness validator warns on duplicate schema_id."""
        with pytest.warns(UserWarning, match="duplicate schema_id"):
            DocumentGT(
                document_id="d1",
                source=DocumentSource(pdf="test.pdf"),
                note_schemas=[
                    NoteSchema(schema_id="dup", marker_type="arabic"),
                    NoteSchema(schema_id="dup", marker_type="roman_lower"),
                ],
            )

    def test_document_with_citation_style(self):
        doc = DocumentGT(
            document_id="d1",
            source=DocumentSource(pdf="test.pdf"),
            citation_style=CitationStyle.CHICAGO_NB,
        )
        assert doc.citation_style == CitationStyle.CHICAGO_NB

    def test_document_with_formatting(self):
        doc = DocumentGT(
            document_id="d1",
            source=DocumentSource(pdf="test.pdf"),
            formatting=[
                FormattingAnnotation(
                    id="fmt1",
                    formatting_type=FormattingType.ITALIC,
                    page=5,
                    char_offset=10,
                    char_length=13,
                    text="Sein und Zeit",
                ),
            ],
        )
        assert len(doc.formatting) == 1
        assert doc.formatting[0].text == "Sein und Zeit"

    def test_document_with_page_range(self):
        doc = DocumentGT(
            document_id="d1",
            source=DocumentSource(pdf="test.pdf"),
            page_range=(0, 437),
        )
        assert doc.page_range == (0, 437)

    def test_document_with_verifications(self):
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        doc = DocumentGT(
            document_id="d1",
            source=DocumentSource(pdf="test.pdf"),
            verifications=[
                VerificationRecord(
                    reviewer_id="annotator_1",
                    timestamp=ts,
                    confidence=0.95,
                    notes="Document-level review complete",
                ),
            ],
        )
        assert len(doc.verifications) == 1
        assert doc.verifications[0].confidence == 0.95

    def test_document_extra_fields(self):
        """DocumentGT accepts unknown fields for forward compat."""
        doc = DocumentGT(
            document_id="d1",
            source=DocumentSource(pdf="test.pdf"),
            future_field="v2_data",
        )
        assert doc.future_field == "v2_data"  # type: ignore[attr-defined]

    def test_document_json_round_trip(self):
        """Full DocumentGT round-trip serialization (v2.0.0)."""
        doc = DocumentGT(
            document_id="d1",
            source=DocumentSource(
                pdf="test.pdf",
                title="Test",
                author="Author",
            ),
            elements=[
                Note(
                    id="n1",
                    body_marker=LocationRef(page=0, region_id="r1"),
                    content=[ContentSpan(page=0, text="Note")],
                    placement="page_bottom",
                ),
                Citation(
                    id="ct1",
                    raw_text="(Author 2024)",
                    citation_format=CitationFormat.PARENTHETICAL,
                ),
            ],
            structure=DocumentStructure(
                toc=[ToCEntry(title="Ch 1", level=0)],
                sections=["sec1"],
            ),
            registers=[
                LayoutRegister(register_id="main", name="Main Text"),
            ],
            note_schemas=[
                NoteSchema(schema_id="default", marker_type="arabic"),
            ],
            citation_style=CitationStyle.CHICAGO_NB,
        )
        json_str = doc.model_dump_json(indent=2)
        restored = DocumentGT.model_validate_json(json_str)

        assert restored.document_id == "d1"
        assert restored.schema_version == SCHEMA_VERSION
        assert restored.source.title == "Test"
        assert len(restored.elements) == 2
        assert isinstance(restored.elements[0], Note)
        assert isinstance(restored.elements[1], Citation)
        assert restored.structure is not None
        assert len(restored.structure.toc) == 1
        assert len(restored.registers) == 1
        assert len(restored.note_schemas) == 1
        assert restored.citation_style == CitationStyle.CHICAGO_NB

    def test_document_extra_fields_round_trip(self):
        """Extra fields survive JSON round-trip."""
        doc = DocumentGT(
            document_id="d1",
            source=DocumentSource(pdf="test.pdf"),
            annotation_tool="cogito_v2",
        )
        json_str = doc.model_dump_json()
        restored = DocumentGT.model_validate_json(json_str)
        assert restored.annotation_tool == "cogito_v2"  # type: ignore[attr-defined]

    def test_document_config_profile(self):
        doc = DocumentGT(
            document_id="d1",
            source=DocumentSource(pdf="test.pdf"),
            config_profile="philosophy_german_translation",
        )
        assert doc.config_profile == "philosophy_german_translation"


# ---------- Realistic example ----------


class TestHeideggerExample:
    """Full realistic example: Heidegger Being and Time snippet (v2.0.0)."""

    def test_heidegger_being_and_time(self):
        """A realistic DocumentGT for Being and Time with Note (not Footnote),
        Citation with CitationFormat/ReferenceSystem, Commentary, LayoutRegister,
        NoteSchema, and no DocumentRelationships."""
        doc = DocumentGT(
            document_id="heidegger_sz_1962",
            source=DocumentSource(
                pdf="being_and_time_macquarrie_1962.pdf",
                title="Being and Time",
                author="Martin Heidegger",
                translator="John Macquarrie & Edward Robinson",
                year=1962,
                publisher="Harper & Row",
                document_type="translation",
            ),
            page_range=(0, 524),
            note_schemas=[
                NoteSchema(
                    schema_id="translator_notes",
                    marker_type="arabic",
                    reset_boundary="page",
                    placement="page_bottom",
                    note_source="translator",
                ),
            ],
            citation_style=CitationStyle.CHICAGO_NB,
            elements=[
                # Cross-page note (was footnote in v1.0.0)
                Note(
                    id="n_p41_1",
                    body_marker=LocationRef(
                        page=65,
                        region_id="r_text_main",
                        char_offset=312,
                    ),
                    content=[
                        ContentSpan(
                            page=65,
                            region_id="r_fn_area",
                            text="See the analysis of care in",
                        ),
                        ContentSpan(
                            page=66,
                            region_id="r_fn_cont",
                            text="section 41 below.",
                            is_continuation=True,
                        ),
                    ],
                    placement="page_bottom",
                    note_source="translator",
                    marker_text="1",
                    note_schema_id="translator_notes",
                ),
                # Citation using SZ abbreviation
                Citation(
                    id="ct_sz_41",
                    raw_text="(SZ, 41)",
                    citation_format=CitationFormat.PARENTHETICAL,
                    reference_system=ReferenceSystem.SZ_PAGINATION,
                    parsed=ParsedCitation(
                        author="Heidegger",
                        work="SZ",
                        page_ref="41",
                    ),
                    bib_entry_id="bib_sz",
                    page=65,
                ),
                # Bibliography entry
                BibEntry(
                    id="bib_sz",
                    raw_text=(
                        "Heidegger, M. (1927). Sein und Zeit. "
                        "Halle: Max Niemeyer."
                    ),
                    record=BibliographicRecord(
                        author="Heidegger, M.",
                        title="Sein und Zeit",
                        year="1927",
                        publisher="Max Niemeyer",
                        work_abbreviation="SZ",
                    ),
                    entry_index=0,
                ),
                # Section
                Section(
                    id="sec_div1",
                    title="Division One: The Preparatory Fundamental "
                    "Analysis of Dasein",
                    level=0,
                    page_start=65,
                    page_end=274,
                    children=["sec_ch1", "sec_ch2", "sec_ch3"],
                ),
                # Page number annotation
                PageNumberAnnotation(
                    id="pn_41",
                    display_text="41",
                    number_type="arabic",
                    page_index=65,
                ),
            ],
            formatting=[
                FormattingAnnotation(
                    id="fmt_sz",
                    formatting_type=FormattingType.ITALIC,
                    page=65,
                    region_id="r_text_main",
                    char_offset=100,
                    char_length=13,
                    text="Sein und Zeit",
                    language="de",
                ),
            ],
            structure=DocumentStructure(
                toc=[
                    ToCEntry(
                        title="Division One",
                        level=0,
                        page_label="41",
                        page_index=65,
                    ),
                    ToCEntry(
                        title="Being-in-the-World in General",
                        level=1,
                        page_label="53",
                    ),
                ],
                sections=["sec_div1"],
            ),
        )

        # Verify structure
        assert doc.document_id == "heidegger_sz_1962"
        assert doc.source.translator is not None
        assert "Macquarrie" in doc.source.translator
        assert doc.page_range == (0, 524)
        assert len(doc.elements) == 5
        assert doc.citation_style == CitationStyle.CHICAGO_NB
        assert len(doc.note_schemas) == 1

        # Verify discriminated union types
        assert isinstance(doc.elements[0], Note)
        assert isinstance(doc.elements[1], Citation)
        assert isinstance(doc.elements[2], BibEntry)
        assert isinstance(doc.elements[3], Section)
        assert isinstance(doc.elements[4], PageNumberAnnotation)

        # Verify cross-page note
        note = doc.elements[0]
        assert isinstance(note, Note)
        assert len(note.content) == 2
        assert note.content[1].is_continuation is True
        assert note.placement == "page_bottom"
        assert note.note_schema_id == "translator_notes"

        # Verify no relationships attribute (v2.0.0 removed it)
        assert not hasattr(doc, "relationships") or doc.model_fields.get("relationships") is None

        # Round-trip
        json_str = doc.model_dump_json(indent=2)
        restored = DocumentGT.model_validate_json(json_str)
        assert restored.document_id == doc.document_id
        assert len(restored.elements) == 5
        assert isinstance(restored.elements[0], Note)
        assert restored.formatting[0].text == "Sein und Zeit"
        assert restored.formatting[0].language == "de"


# ---------- Import from scholargt.schema tests ----------


class TestSchemaPackageExports:
    """Verify all public models are importable from scholargt.schema."""

    def test_base_models_importable(self):
        from scholargt.schema import BBox, GTElement, LocationRef, VerificationRecord

        assert BBox is not None
        assert GTElement is not None
        assert VerificationRecord is not None
        assert LocationRef is not None

    def test_page_models_importable(self):
        from scholargt.schema import (
            PageDependency,
            PageGT,
            PageQuality,
            Region,
            SectionContextEntry,
        )

        assert PageGT is not None
        assert PageQuality is not None
        assert Region is not None
        assert PageDependency is not None
        assert SectionContextEntry is not None

    def test_semantic_models_importable(self):
        from scholargt.schema import Commentary as Comm
        from scholargt.schema import Note as Note_
        from scholargt.schema import NoteSchema as NS
        from scholargt.schema import ToCEntry as ToC

        assert Note_ is not None
        assert Comm is not None
        assert SemanticElement is not None
        assert ToC is not None
        assert NS is not None

    def test_document_models_importable(self):
        from scholargt.schema import (
            DocumentGT,
            LayoutRegister,
        )

        assert DocumentGT is not None
        assert LayoutRegister is not None

    def test_formatting_importable(self):
        from scholargt.schema import FormattingAnnotation

        assert FormattingAnnotation is not None

    def test_labels_importable(self):
        from scholargt.schema import (
            CitationFormat,
            CitationStyle,
            DocumentSectionType,
            ReferenceSystem,
            ScriptVariant,
            SpatialLabel,
        )

        assert len(CitationFormat) == 5
        assert len(ReferenceSystem) == 13
        assert len(CitationStyle) == 7
        assert len(ScriptVariant) == 6
        assert len(DocumentSectionType) == 5
        assert len(SpatialLabel) == 21

    def test_version_importable(self):
        from scholargt.schema import SCHEMA_VERSION

        assert SCHEMA_VERSION == "2.0.0"
