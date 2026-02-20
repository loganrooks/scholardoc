"""Tests for semantic element models, discriminated union, and formatting annotations.

Covers all 9 semantic element types (v2.0.0: Note, Commentary replace Footnote/Endnote),
SemanticElement discriminated union routing, round-trip JSON serialization,
philosophy-specific elements, and FormattingAnnotation with SFP features.

v2.0.0 changes:
- Note replaces Footnote + Endnote (unified model with LocationRef markers)
- Commentary added for philosophical/rabbinic commentary apparatus
- Citation uses CitationFormat + ReferenceSystem (replaces CitationType)
- MarginalReference uses ReferenceSystem (replaces MarginalRefType)
- BibEntry uses BibliographicRecord (replaces ParsedCitation for bibliography)
- NoteSchema added for document-level note numbering conventions
- ContentSpan gains char_offset/char_length for endnote positioning
- FormattingAnnotation gains language, script_variant (SFP-3), color_value/color_semantic (SFP-4)
"""

from datetime import UTC, datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from scholargt.schema.base import LocationRef
from scholargt.schema.formatting import FormattingAnnotation
from scholargt.schema.labels import (
    CitationFormat,
    FormattingType,
    ReferenceSystem,
    ScriptVariant,
)
from scholargt.schema.semantic import (
    BibEntry,
    BibliographicRecord,
    Citation,
    Commentary,
    ContentSpan,
    CrossReference,
    MarginalReference,
    Note,
    NoteSchema,
    PageNumberAnnotation,
    ParsedCitation,
    Section,
    SemanticElement,
    SousRature,
    ToCEntry,
)

# ---------- Supporting model tests ----------


class TestSupportingModels:
    def test_location_ref_required_fields(self):
        loc = LocationRef(page=0, region_id="r1")
        assert loc.page == 0
        assert loc.region_id == "r1"
        assert loc.char_offset is None

    def test_location_ref_all_fields(self):
        loc = LocationRef(page=5, region_id="r3", char_offset=42, char_length=10)
        assert loc.region_id == "r3"
        assert loc.char_offset == 42
        assert loc.char_length == 10

    def test_content_span_default(self):
        cs = ContentSpan(page=0, text="Note text")
        assert cs.is_continuation is False
        assert cs.region_id is None
        assert cs.char_offset is None
        assert cs.char_length is None

    def test_content_span_continuation(self):
        cs = ContentSpan(page=1, text="continued text", is_continuation=True)
        assert cs.is_continuation is True

    def test_content_span_with_char_offset(self):
        """char_offset/char_length for endnote positioning in shared regions."""
        cs = ContentSpan(
            page=200, text="Endnote text", region_id="r_endnotes",
            char_offset=512, char_length=100,
        )
        assert cs.char_offset == 512
        assert cs.char_length == 100

    def test_parsed_citation_all_none(self):
        pc = ParsedCitation()
        assert pc.author is None
        assert pc.year is None
        assert pc.page_ref is None
        assert pc.work is None

    def test_parsed_citation_with_values(self):
        pc = ParsedCitation(author="Heidegger", year="1927", work="SZ", page_ref="41")
        assert pc.author == "Heidegger"
        assert pc.work == "SZ"

    def test_bibliographic_record_all_fields(self):
        rec = BibliographicRecord(
            author="Heidegger, Martin",
            title="Sein und Zeit",
            year="1927",
            publisher="Max Niemeyer",
            edition="7th",
            translator="Macquarrie & Robinson",
            work_abbreviation="SZ",
        )
        assert rec.author == "Heidegger, Martin"
        assert rec.title == "Sein und Zeit"
        assert rec.work_abbreviation == "SZ"

    def test_bibliographic_record_minimal(self):
        rec = BibliographicRecord()
        assert rec.author is None
        assert rec.title is None

    def test_toc_entry(self):
        entry = ToCEntry(title="Division One", level=0, page_label="21", page_index=45)
        assert entry.title == "Division One"
        assert entry.level == 0
        assert entry.page_label == "21"
        assert entry.page_index == 45

    def test_note_schema_full(self):
        ns = NoteSchema(
            schema_id="translator_footnotes",
            marker_type="arabic",
            symbol_sequence=None,
            reset_boundary="page",
            placement="page_bottom",
            note_source="translator",
        )
        assert ns.schema_id == "translator_footnotes"
        assert ns.marker_type == "arabic"
        assert ns.reset_boundary == "page"
        assert ns.placement == "page_bottom"
        assert ns.note_source == "translator"

    def test_note_schema_symbolic(self):
        ns = NoteSchema(
            schema_id="author_notes",
            marker_type="symbolic",
            symbol_sequence=["*", "dagger", "double_dagger"],
            reset_boundary="page",
            placement="page_bottom",
            note_source="author",
        )
        assert ns.marker_type == "symbolic"
        assert len(ns.symbol_sequence) == 3

    def test_note_schema_minimal(self):
        ns = NoteSchema(schema_id="default", marker_type="arabic")
        assert ns.schema_id == "default"
        assert ns.symbol_sequence is None
        assert ns.reset_boundary is None


# ---------- Note tests (replaces Footnote + Endnote) ----------


class TestNote:
    def test_create_note_footnote_style(self):
        """Note with placement='page_bottom' acts as a footnote."""
        note = Note(
            id="n1",
            body_marker=LocationRef(page=0, region_id="r_text"),
            content=[ContentSpan(page=0, text="See the analysis of care.")],
            placement="page_bottom",
        )
        assert note.element_type == "note"
        assert note.body_marker.page == 0
        assert note.body_marker.region_id == "r_text"
        assert len(note.content) == 1
        assert note.placement == "page_bottom"
        assert note.note_source is None

    def test_create_note_endnote_style(self):
        """Note with placement='end_of_book' acts as an endnote."""
        note = Note(
            id="n2",
            body_marker=LocationRef(page=10, region_id="r_text", char_offset=342),
            content=[ContentSpan(page=200, text="Endnote text at back of book")],
            placement="end_of_book",
            scope="chapter",
        )
        assert note.placement == "end_of_book"
        assert note.scope == "chapter"

    def test_note_with_all_fields(self):
        note = Note(
            id="n3",
            body_marker=LocationRef(page=5, region_id="r_main", char_offset=100, char_length=1),
            content_marker=LocationRef(page=5, region_id="r_fn_area"),
            content=[ContentSpan(page=5, text="Note content here.")],
            placement="page_bottom",
            scope="page",
            note_source="translator",
            marker_text="1",
            note_schema_id="translator_footnotes",
        )
        assert note.content_marker is not None
        assert note.content_marker.region_id == "r_fn_area"
        assert note.note_source == "translator"
        assert note.marker_text == "1"
        assert note.note_schema_id == "translator_footnotes"

    def test_note_multi_page_content(self):
        """Note content spanning two pages with continuation flag."""
        note = Note(
            id="n4",
            body_marker=LocationRef(page=5, region_id="r_text"),
            content=[
                ContentSpan(page=5, text="This note begins here"),
                ContentSpan(page=6, text="and continues on the next page", is_continuation=True),
            ],
            placement="page_bottom",
            note_source="author",
        )
        assert len(note.content) == 2
        assert note.content[0].is_continuation is False
        assert note.content[1].is_continuation is True
        assert note.note_source == "author"

    def test_note_inherits_gtelement(self):
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        note = Note(
            id="n5",
            body_marker=LocationRef(page=0, region_id="r1"),
            content=[ContentSpan(page=0, text="Note")],
            placement="page_bottom",
            verifications=[
                {"reviewer_id": "r1", "timestamp": ts.isoformat(), "confidence": 0.95}
            ],
            tags=["philosophy"],
        )
        assert note.is_verified(threshold=0.9) is True
        assert note.tags == ["philosophy"]

    def test_note_margin_placement(self):
        """Note with margin placement for marginal notes."""
        note = Note(
            id="n6",
            body_marker=LocationRef(page=42, region_id="r_text"),
            content=[ContentSpan(page=42, text="Marginal annotation")],
            placement="margin",
        )
        assert note.placement == "margin"


# ---------- Commentary tests ----------


class TestCommentary:
    def test_create_commentary(self):
        comm = Commentary(
            id="comm1",
            source="Rashi",
            passage_ref="Gen 1:1",
            reference_system=ReferenceSystem.CHAPTER_VERSE,
            content=[ContentSpan(page=10, text="In the beginning -- for the sake of Torah")],
        )
        assert comm.element_type == "commentary"
        assert comm.source == "Rashi"
        assert comm.passage_ref == "Gen 1:1"
        assert comm.reference_system == ReferenceSystem.CHAPTER_VERSE

    def test_commentary_with_catchword(self):
        """SFP-6: Commentary using CATCHWORD reference system (dibbur ha-matchil)."""
        comm = Commentary(
            id="comm2",
            source="Rashi",
            passage_ref="In the beginning",
            reference_system=ReferenceSystem.CATCHWORD,
            content=[ContentSpan(page=10, text="d\"h: In the beginning -- the commentary text")],
            layer="rashi",
        )
        assert comm.reference_system == ReferenceSystem.CATCHWORD
        assert comm.layer == "rashi"

    def test_commentary_with_target_location(self):
        comm = Commentary(
            id="comm3",
            source="editor",
            passage_ref="p. 42",
            reference_system=ReferenceSystem.STANDARD,
            target_location=LocationRef(page=42, region_id="r_main", char_offset=0, char_length=50),
            content=[ContentSpan(page=300, text="Editor's commentary on this passage")],
        )
        assert comm.target_location is not None
        assert comm.target_location.page == 42

    def test_commentary_multi_layer(self):
        """Multi-layer commentary: Rashi and Tosafot on same passage."""
        rashi = Commentary(
            id="comm_rashi",
            source="Rashi",
            passage_ref="264a",
            reference_system=ReferenceSystem.CATCHWORD,
            content=[ContentSpan(page=5, text="Rashi's interpretation")],
            layer="rashi",
        )
        tosafot = Commentary(
            id="comm_tosafot",
            source="Tosafot",
            passage_ref="264a",
            reference_system=ReferenceSystem.CATCHWORD,
            content=[ContentSpan(page=5, text="Tosafot's analysis")],
            layer="tosafot",
        )
        assert rashi.layer == "rashi"
        assert tosafot.layer == "tosafot"


# ---------- Citation tests ----------


class TestCitation:
    def test_create_citation_parenthetical(self):
        ct = Citation(
            id="ct1",
            raw_text="(Heidegger, 1927)",
            citation_format=CitationFormat.PARENTHETICAL,
            reference_system=ReferenceSystem.STANDARD,
        )
        assert ct.element_type == "citation"
        assert ct.citation_format == CitationFormat.PARENTHETICAL
        assert ct.reference_system == ReferenceSystem.STANDARD

    def test_citation_with_parsed(self):
        ct = Citation(
            id="ct2",
            raw_text="(SZ, 41)",
            citation_format=CitationFormat.PARENTHETICAL,
            reference_system=ReferenceSystem.SZ_PAGINATION,
            parsed=ParsedCitation(author="Heidegger", work="SZ", page_ref="41"),
            bib_entry_id="bib1",
            page=5,
            region_id="r3",
        )
        assert ct.parsed is not None
        assert ct.parsed.work == "SZ"
        assert ct.bib_entry_id == "bib1"

    def test_all_five_citation_formats(self):
        """Verify all 5 CitationFormat enum values exist and work in Citation model."""
        expected = {
            "parenthetical",
            "numeric",
            "inline_author",
            "note_based",
            "author_title",
        }
        actual = {cf.value for cf in CitationFormat}
        assert actual == expected

        for cf in CitationFormat:
            c = Citation(
                id=f"ct_{cf.value}",
                raw_text=f"test-{cf.value}",
                citation_format=cf,
            )
            assert c.citation_format == cf

    def test_citation_stephanus(self):
        """Stephanus pagination for Plato references."""
        ct = Citation(
            id="ct_plato",
            raw_text="Republic 514a",
            citation_format=CitationFormat.PARENTHETICAL,
            reference_system=ReferenceSystem.STEPHANUS,
            parsed=ParsedCitation(author="Plato", work="Republic", page_ref="514a"),
        )
        assert ct.reference_system == ReferenceSystem.STEPHANUS

    def test_citation_bekker(self):
        """Bekker numbering for Aristotle references."""
        ct = Citation(
            id="ct_aristotle",
            raw_text="Met. 1003a21",
            citation_format=CitationFormat.PARENTHETICAL,
            reference_system=ReferenceSystem.BEKKER,
            parsed=ParsedCitation(author="Aristotle", work="Metaphysics", page_ref="1003a21"),
        )
        assert ct.reference_system == ReferenceSystem.BEKKER

    def test_citation_numeric_format(self):
        ct = Citation(
            id="ct_num",
            raw_text="[42]",
            citation_format=CitationFormat.NUMERIC,
        )
        assert ct.citation_format == CitationFormat.NUMERIC

    def test_citation_no_reference_system(self):
        """Citation without reference_system (optional)."""
        ct = Citation(
            id="ct_simple",
            raw_text="(Author 2024)",
            citation_format=CitationFormat.PARENTHETICAL,
        )
        assert ct.reference_system is None


# ---------- BibEntry tests ----------


class TestBibEntry:
    def test_create_bib_entry_with_record(self):
        be = BibEntry(
            id="bib1",
            raw_text="Heidegger, M. (1927). Sein und Zeit. Halle: Niemeyer.",
            record=BibliographicRecord(
                author="Heidegger, M.",
                title="Sein und Zeit",
                year="1927",
                publisher="Niemeyer",
                work_abbreviation="SZ",
            ),
            entry_index=0,
        )
        assert be.element_type == "bibliography_entry"
        assert be.entry_index == 0
        assert be.record is not None
        assert be.record.work_abbreviation == "SZ"

    def test_bib_entry_minimal(self):
        be = BibEntry(
            id="bib2",
            raw_text="Plato. Republic.",
        )
        assert be.record is None
        assert be.entry_index is None


# ---------- Section tests ----------


class TestSection:
    def test_create_section(self):
        s = Section(
            id="sec1",
            title="Division One: The Preparatory Fundamental Analysis of Dasein",
            level=0,
            page_start=41,
            page_end=230,
            children=["sec1.1", "sec1.2", "sec1.3"],
        )
        assert s.element_type == "section"
        assert s.level == 0
        assert s.children == ["sec1.1", "sec1.2", "sec1.3"]

    def test_section_defaults(self):
        s = Section(id="sec2", title="Introduction", level=0)
        assert s.page_start is None
        assert s.page_end is None
        assert s.children == []


# ---------- SousRature tests ----------


class TestSousRature:
    def test_create_sous_rature(self):
        """Sous rature (under erasure) -- Derrida's philosophical device."""
        sr = SousRature(
            id="sr1",
            text="Being",
            page=15,
            region_id="r5",
            char_offset=10,
            char_length=5,
        )
        assert sr.element_type == "sous_rature"
        assert sr.text == "Being"
        assert sr.char_length == 5

    def test_sous_rature_minimal(self):
        sr = SousRature(id="sr2", text="is", page=20)
        assert sr.region_id is None
        assert sr.char_offset is None
        assert sr.char_length is None


# ---------- CrossReference tests ----------


class TestCrossReference:
    def test_create_cross_reference(self):
        cr = CrossReference(
            id="xref1",
            raw_text="see section 41",
            target_page=205,
            target_section_id="sec41",
            page=15,
            region_id="r7",
        )
        assert cr.element_type == "cross_reference"
        assert cr.target_section_id == "sec41"


# ---------- MarginalReference tests ----------


class TestMarginalReference:
    def test_stephanus_reference(self):
        mr = MarginalReference(
            id="mr1",
            raw_text="514a",
            reference_system=ReferenceSystem.STEPHANUS,
            page=42,
        )
        assert mr.element_type == "marginal_reference"
        assert mr.reference_system == ReferenceSystem.STEPHANUS

    def test_bekker_reference(self):
        mr = MarginalReference(
            id="mr2",
            raw_text="1003a",
            reference_system=ReferenceSystem.BEKKER,
            page=55,
        )
        assert mr.reference_system == ReferenceSystem.BEKKER

    def test_akademie_reference(self):
        mr = MarginalReference(
            id="mr3",
            raw_text="A 51 / B 75",
            reference_system=ReferenceSystem.AKADEMIE,
            page=100,
        )
        assert mr.reference_system == ReferenceSystem.AKADEMIE

    def test_custom_reference(self):
        mr = MarginalReference(
            id="mr4",
            raw_text="GA 2, 27",
            reference_system=ReferenceSystem.CUSTOM,
            page=30,
            region_id="r_margin",
        )
        assert mr.reference_system == ReferenceSystem.CUSTOM
        assert mr.region_id == "r_margin"

    def test_catchword_reference(self):
        """SFP-6: CATCHWORD reference system for pre-modern books."""
        mr = MarginalReference(
            id="mr5",
            raw_text="In the beginning",
            reference_system=ReferenceSystem.CATCHWORD,
            page=10,
        )
        assert mr.reference_system == ReferenceSystem.CATCHWORD


# ---------- PageNumberAnnotation tests ----------


class TestPageNumberAnnotation:
    def test_arabic_page_number(self):
        pn = PageNumberAnnotation(
            id="pn1", display_text="127", number_type="arabic", page_index=150
        )
        assert pn.element_type == "page_number_annotation"
        assert pn.number_type == "arabic"

    def test_roman_page_number(self):
        pn = PageNumberAnnotation(
            id="pn2", display_text="xiv", number_type="roman", page_index=14
        )
        assert pn.number_type == "roman"


# ---------- Discriminated union tests ----------


class TestSemanticElementUnion:
    def test_discriminated_union_note(self):
        """TypeAdapter correctly deserializes Note from dict."""
        ta = TypeAdapter(SemanticElement)
        data = {
            "id": "n1",
            "element_type": "note",
            "body_marker": {"page": 0, "region_id": "r1"},
            "content": [{"page": 0, "text": "Note text"}],
            "placement": "page_bottom",
        }
        elem = ta.validate_python(data)
        assert isinstance(elem, Note)

    def test_discriminated_union_commentary(self):
        """TypeAdapter correctly deserializes Commentary from dict."""
        ta = TypeAdapter(SemanticElement)
        data = {
            "id": "comm1",
            "element_type": "commentary",
            "source": "Rashi",
            "passage_ref": "Gen 1:1",
            "reference_system": "chapter_verse",
            "content": [{"page": 10, "text": "Commentary text"}],
        }
        elem = ta.validate_python(data)
        assert isinstance(elem, Commentary)

    def test_discriminated_union_citation(self):
        ta = TypeAdapter(SemanticElement)
        data = {
            "id": "ct1",
            "element_type": "citation",
            "raw_text": "(Heidegger 1927)",
            "citation_format": "parenthetical",
        }
        elem = ta.validate_python(data)
        assert isinstance(elem, Citation)

    def test_discriminated_union_mixed_list(self):
        """Deserialize a list of mixed SemanticElement types by element_type."""
        ta = TypeAdapter(list[SemanticElement])
        data = [
            {
                "id": "n1",
                "element_type": "note",
                "body_marker": {"page": 0, "region_id": "r1"},
                "content": [{"page": 0, "text": "Note"}],
                "placement": "page_bottom",
            },
            {
                "id": "ct1",
                "element_type": "citation",
                "raw_text": "(Heidegger 1927)",
                "citation_format": "parenthetical",
            },
            {
                "id": "sec1",
                "element_type": "section",
                "title": "Introduction",
                "level": 0,
            },
            {
                "id": "sr1",
                "element_type": "sous_rature",
                "text": "Being",
                "page": 15,
            },
        ]
        elements = ta.validate_python(data)
        assert len(elements) == 4
        assert isinstance(elements[0], Note)
        assert isinstance(elements[1], Citation)
        assert isinstance(elements[2], Section)
        assert isinstance(elements[3], SousRature)

    def test_discriminated_union_all_nine_types(self):
        """Every element type can be deserialized through the union."""
        ta = TypeAdapter(SemanticElement)
        type_data = [
            {
                "id": "n1",
                "element_type": "note",
                "body_marker": {"page": 0, "region_id": "r1"},
                "content": [{"page": 0, "text": "N"}],
                "placement": "page_bottom",
            },
            {
                "id": "comm1",
                "element_type": "commentary",
                "source": "Rashi",
                "passage_ref": "Gen 1:1",
                "reference_system": "chapter_verse",
                "content": [{"page": 0, "text": "C"}],
            },
            {
                "id": "ct1",
                "element_type": "citation",
                "raw_text": "x",
                "citation_format": "parenthetical",
            },
            {
                "id": "be1",
                "element_type": "bibliography_entry",
                "raw_text": "Heidegger 1927",
            },
            {
                "id": "s1",
                "element_type": "section",
                "title": "Intro",
                "level": 0,
            },
            {
                "id": "sr1",
                "element_type": "sous_rature",
                "text": "Being",
                "page": 0,
            },
            {
                "id": "xr1",
                "element_type": "cross_reference",
                "raw_text": "see ch 3",
                "page": 5,
            },
            {
                "id": "mr1",
                "element_type": "marginal_reference",
                "raw_text": "514a",
                "reference_system": "stephanus",
                "page": 10,
            },
            {
                "id": "pn1",
                "element_type": "page_number_annotation",
                "display_text": "127",
                "number_type": "arabic",
                "page_index": 150,
            },
        ]
        expected_types = [
            Note, Commentary, Citation, BibEntry, Section,
            SousRature, CrossReference, MarginalReference,
            PageNumberAnnotation,
        ]
        for data, expected in zip(
            type_data, expected_types, strict=True
        ):
            elem = ta.validate_python(data)
            assert isinstance(elem, expected), (
                f"Expected {expected.__name__}, "
                f"got {type(elem).__name__}"
            )

    def test_unknown_element_type_raises_validation_error(self):
        """Discriminator enforcement: unknown element_type is rejected."""
        ta = TypeAdapter(SemanticElement)
        data = {"id": "x1", "element_type": "unknown_type", "text": "hello"}
        with pytest.raises(ValidationError):
            ta.validate_python(data)

    def test_round_trip_json_list(self):
        """model_dump_json() list of SemanticElement -> model_validate_json()."""
        ta = TypeAdapter(list[SemanticElement])
        elements: list[SemanticElement] = [
            Note(
                id="n1",
                body_marker=LocationRef(page=0, region_id="r1"),
                content=[ContentSpan(page=0, text="Note text")],
                placement="page_bottom",
            ),
            Citation(
                id="ct1",
                raw_text="(Heidegger 1927)",
                citation_format=CitationFormat.PARENTHETICAL,
                parsed=ParsedCitation(author="Heidegger", year="1927"),
            ),
            Section(id="sec1", title="Introduction", level=0, children=["sec1.1"]),
        ]
        json_bytes = ta.dump_json(elements, indent=2)
        restored = ta.validate_json(json_bytes)

        assert len(restored) == 3
        assert isinstance(restored[0], Note)
        assert isinstance(restored[1], Citation)
        assert isinstance(restored[2], Section)
        assert restored[0].body_marker.region_id == "r1"
        assert restored[1].parsed is not None
        assert restored[1].parsed.author == "Heidegger"
        assert restored[2].children == ["sec1.1"]


# ---------- FormattingAnnotation tests ----------


class TestFormattingAnnotation:
    def test_create_formatting_annotation(self):
        fa = FormattingAnnotation(
            id="fmt1",
            formatting_type=FormattingType.ITALIC,
            page=5,
            region_id="r2",
            char_offset=10,
            char_length=15,
            text="Sein und Zeit",
        )
        assert fa.formatting_type == FormattingType.ITALIC
        assert fa.char_offset == 10
        assert fa.char_length == 15
        assert fa.text == "Sein und Zeit"

    def test_formatting_annotation_no_text(self):
        fa = FormattingAnnotation(
            id="fmt2",
            formatting_type=FormattingType.BOLD,
            page=0,
            char_offset=0,
            char_length=5,
        )
        assert fa.text is None
        assert fa.region_id is None

    def test_formatting_all_types(self):
        """All FormattingType values work in FormattingAnnotation."""
        for ft in FormattingType:
            if ft == FormattingType.COLOR:
                # COLOR triggers a warning if no color_value, test separately
                continue
            fa = FormattingAnnotation(
                id=f"fmt_{ft.value}",
                formatting_type=ft,
                page=0,
                char_offset=0,
                char_length=1,
            )
            assert fa.formatting_type == ft

    def test_formatting_inherits_gtelement(self):
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        fa = FormattingAnnotation(
            id="fmt3",
            formatting_type=FormattingType.SMALL_CAPS,
            page=0,
            char_offset=0,
            char_length=10,
            verifications=[
                {"reviewer_id": "r1", "timestamp": ts.isoformat(), "confidence": 0.9}
            ],
        )
        assert fa.is_verified() is True

    def test_formatting_json_round_trip(self):
        fa = FormattingAnnotation(
            id="fmt4",
            formatting_type=FormattingType.SUPERSCRIPT,
            page=3,
            region_id="r1",
            char_offset=42,
            char_length=1,
            text="2",
        )
        json_str = fa.model_dump_json()
        restored = FormattingAnnotation.model_validate_json(json_str)
        assert restored.formatting_type == FormattingType.SUPERSCRIPT
        assert restored.char_offset == 42
        assert restored.text == "2"

    def test_formatting_with_language(self):
        """BCP 47 language tag for mixed-language annotation."""
        fa = FormattingAnnotation(
            id="fmt_de",
            formatting_type=FormattingType.ITALIC,
            page=5,
            char_offset=10,
            char_length=13,
            text="Sein und Zeit",
            language="de",
        )
        assert fa.language == "de"

    def test_formatting_with_script_variant(self):
        """SFP-3: Script variant annotation for Rashi script."""
        fa = FormattingAnnotation(
            id="fmt_rashi",
            formatting_type=FormattingType.ITALIC,
            page=10,
            char_offset=0,
            char_length=50,
            script_variant=ScriptVariant.RASHI_SCRIPT,
        )
        assert fa.script_variant == ScriptVariant.RASHI_SCRIPT

    def test_formatting_color_with_semantic(self):
        """SFP-4: COLOR formatting with color_value and color_semantic."""
        fa = FormattingAnnotation(
            id="fmt_color",
            formatting_type=FormattingType.COLOR,
            page=5,
            char_offset=0,
            char_length=100,
            color_value="#FF0000",
            color_semantic="gemara_text",
        )
        assert fa.formatting_type == FormattingType.COLOR
        assert fa.color_value == "#FF0000"
        assert fa.color_semantic == "gemara_text"

    def test_formatting_color_warns_without_value(self):
        """SFP-4: COLOR without color_value emits warning."""
        with pytest.warns(UserWarning, match="color_value is None"):
            FormattingAnnotation(
                id="fmt_color_warn",
                formatting_type=FormattingType.COLOR,
                page=5,
                char_offset=0,
                char_length=10,
            )

    def test_formatting_color_value_without_color_type_warns(self):
        """SFP-4: color_value set but formatting_type is not COLOR emits warning."""
        with pytest.warns(UserWarning, match="not COLOR"):
            FormattingAnnotation(
                id="fmt_mismatched",
                formatting_type=FormattingType.BOLD,
                page=5,
                char_offset=0,
                char_length=10,
                color_value="#0000FF",
            )
