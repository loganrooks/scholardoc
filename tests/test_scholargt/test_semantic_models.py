"""Tests for semantic element models, discriminated union, and formatting annotations.

Covers all 9 semantic element types, SemanticElement discriminated union routing,
round-trip JSON serialization, philosophy-specific elements, and FormattingAnnotation.
"""

from datetime import UTC, datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from scholargt.schema.formatting import FormattingAnnotation
from scholargt.schema.labels import CitationType, FormattingType, MarginalRefType
from scholargt.schema.semantic import (
    BibEntry,
    Citation,
    ContentSpan,
    CrossReference,
    Endnote,
    Footnote,
    MarginalReference,
    MarkerInfo,
    PageNumberAnnotation,
    ParsedCitation,
    Section,
    SemanticElement,
    SousRature,
    ToCEntry,
)

# ---------- Supporting model tests ----------


class TestSupportingModels:
    def test_marker_info_required_fields(self):
        m = MarkerInfo(text="1", page=0)
        assert m.text == "1"
        assert m.page == 0
        assert m.region_id is None
        assert m.char_offset is None

    def test_marker_info_all_fields(self):
        m = MarkerInfo(text="*", page=5, region_id="r3", char_offset=42)
        assert m.region_id == "r3"
        assert m.char_offset == 42

    def test_content_span_default(self):
        cs = ContentSpan(page=0, text="Note text")
        assert cs.is_continuation is False
        assert cs.region_id is None

    def test_content_span_continuation(self):
        cs = ContentSpan(page=1, text="continued text", is_continuation=True)
        assert cs.is_continuation is True

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

    def test_toc_entry(self):
        entry = ToCEntry(title="Division One", level=0, page_label="21", page_index=45)
        assert entry.title == "Division One"
        assert entry.level == 0
        assert entry.page_label == "21"
        assert entry.page_index == 45


# ---------- Footnote tests ----------


class TestFootnote:
    def test_create_footnote(self):
        fn = Footnote(
            id="fn1",
            marker=MarkerInfo(text="1", page=0),
            content=[ContentSpan(page=0, text="See the analysis of care.")],
            location="page_bottom",
        )
        assert fn.element_type == "footnote"
        assert fn.marker.text == "1"
        assert len(fn.content) == 1
        assert fn.location == "page_bottom"
        assert fn.note_source is None

    def test_footnote_multi_page_content(self):
        """Footnote content spanning two pages with continuation flag."""
        fn = Footnote(
            id="fn2",
            marker=MarkerInfo(text="2", page=5),
            content=[
                ContentSpan(page=5, text="This footnote begins here"),
                ContentSpan(page=6, text="and continues on the next page", is_continuation=True),
            ],
            location="page_bottom",
            note_source="author",
        )
        assert len(fn.content) == 2
        assert fn.content[0].is_continuation is False
        assert fn.content[1].is_continuation is True
        assert fn.note_source == "author"

    def test_footnote_inherits_gtelement(self):
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        fn = Footnote(
            id="fn1",
            marker=MarkerInfo(text="1", page=0),
            content=[ContentSpan(page=0, text="Note")],
            location="page_bottom",
            verifications=[
                {"reviewer_id": "r1", "timestamp": ts.isoformat(), "confidence": 0.95}
            ],
            tags=["philosophy"],
        )
        assert fn.is_verified(threshold=0.9) is True
        assert fn.tags == ["philosophy"]


# ---------- Endnote tests ----------


class TestEndnote:
    def test_create_endnote(self):
        en = Endnote(
            id="en1",
            marker=MarkerInfo(text="1", page=10),
            content=[ContentSpan(page=200, text="Endnote text at back of book")],
            section_title="Notes to Chapter 1",
        )
        assert en.element_type == "endnote"
        assert en.section_title == "Notes to Chapter 1"
        assert en.note_source is None


# ---------- Citation tests ----------


class TestCitation:
    def test_create_citation_author_date(self):
        ct = Citation(
            id="ct1",
            raw_text="(Heidegger, 1927)",
            citation_type=CitationType.AUTHOR_DATE,
        )
        assert ct.element_type == "citation"
        assert ct.citation_type == CitationType.AUTHOR_DATE

    def test_citation_with_parsed(self):
        ct = Citation(
            id="ct2",
            raw_text="(SZ, 41)",
            citation_type=CitationType.ABBREVIATED,
            parsed=ParsedCitation(author="Heidegger", work="SZ", page_ref="41"),
            bib_entry_id="bib1",
            page=5,
            region_id="r3",
        )
        assert ct.parsed is not None
        assert ct.parsed.work == "SZ"
        assert ct.bib_entry_id == "bib1"

    def test_all_seven_citation_types(self):
        """Verify all 7 CitationType enum values exist and work in Citation model."""
        expected = {
            "author_date",
            "numeric",
            "abbreviated",
            "footnote_style",
            "stephanus",
            "bekker",
            "ak_reference",
        }
        actual = {ct.value for ct in CitationType}
        assert actual == expected

        # Create a citation with each type
        for ct_type in CitationType:
            c = Citation(
                id=f"ct_{ct_type.value}",
                raw_text=f"test-{ct_type.value}",
                citation_type=ct_type,
            )
            assert c.citation_type == ct_type

    def test_citation_stephanus(self):
        """Stephanus pagination for Plato references."""
        ct = Citation(
            id="ct_plato",
            raw_text="Republic 514a",
            citation_type=CitationType.STEPHANUS,
            parsed=ParsedCitation(author="Plato", work="Republic", page_ref="514a"),
        )
        assert ct.citation_type == CitationType.STEPHANUS

    def test_citation_bekker(self):
        """Bekker numbering for Aristotle references."""
        ct = Citation(
            id="ct_aristotle",
            raw_text="Met. 1003a21",
            citation_type=CitationType.BEKKER,
            parsed=ParsedCitation(author="Aristotle", work="Metaphysics", page_ref="1003a21"),
        )
        assert ct.citation_type == CitationType.BEKKER


# ---------- BibEntry tests ----------


class TestBibEntry:
    def test_create_bib_entry(self):
        be = BibEntry(
            id="bib1",
            raw_text="Heidegger, M. (1927). Sein und Zeit. Halle: Niemeyer.",
            parsed=ParsedCitation(author="Heidegger", year="1927", work="Sein und Zeit"),
            entry_index=0,
        )
        assert be.element_type == "bibliography_entry"
        assert be.entry_index == 0


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
            ref_type=MarginalRefType.STEPHANUS,
            page=42,
        )
        assert mr.element_type == "marginal_reference"
        assert mr.ref_type == MarginalRefType.STEPHANUS

    def test_bekker_reference(self):
        mr = MarginalReference(
            id="mr2",
            raw_text="1003a",
            ref_type=MarginalRefType.BEKKER,
            page=55,
        )
        assert mr.ref_type == MarginalRefType.BEKKER

    def test_akademie_reference(self):
        mr = MarginalReference(
            id="mr3",
            raw_text="A 51 / B 75",
            ref_type=MarginalRefType.AKADEMIE,
            page=100,
        )
        assert mr.ref_type == MarginalRefType.AKADEMIE

    def test_custom_reference(self):
        mr = MarginalReference(
            id="mr4",
            raw_text="GA 2, 27",
            ref_type=MarginalRefType.CUSTOM,
            page=30,
            region_id="r_margin",
        )
        assert mr.ref_type == MarginalRefType.CUSTOM
        assert mr.region_id == "r_margin"


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
    def test_discriminated_union_footnote(self):
        """TypeAdapter correctly deserializes Footnote from dict."""
        ta = TypeAdapter(SemanticElement)
        data = {
            "id": "fn1",
            "element_type": "footnote",
            "marker": {"text": "1", "page": 0},
            "content": [{"page": 0, "text": "Note"}],
            "location": "page_bottom",
        }
        elem = ta.validate_python(data)
        assert isinstance(elem, Footnote)

    def test_discriminated_union_citation(self):
        ta = TypeAdapter(SemanticElement)
        data = {
            "id": "ct1",
            "element_type": "citation",
            "raw_text": "(Heidegger 1927)",
            "citation_type": "author_date",
        }
        elem = ta.validate_python(data)
        assert isinstance(elem, Citation)

    def test_discriminated_union_mixed_list(self):
        """Deserialize a list of mixed SemanticElement types by element_type."""
        ta = TypeAdapter(list[SemanticElement])
        data = [
            {
                "id": "fn1",
                "element_type": "footnote",
                "marker": {"text": "1", "page": 0},
                "content": [{"page": 0, "text": "Note"}],
                "location": "page_bottom",
            },
            {
                "id": "ct1",
                "element_type": "citation",
                "raw_text": "(Heidegger 1927)",
                "citation_type": "author_date",
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
        assert isinstance(elements[0], Footnote)
        assert isinstance(elements[1], Citation)
        assert isinstance(elements[2], Section)
        assert isinstance(elements[3], SousRature)

    def test_discriminated_union_all_nine_types(self):
        """Every element type can be deserialized through the union."""
        ta = TypeAdapter(SemanticElement)
        type_data = [
            {
                "id": "fn1",
                "element_type": "footnote",
                "marker": {"text": "1", "page": 0},
                "content": [{"page": 0, "text": "N"}],
                "location": "page_bottom",
            },
            {
                "id": "en1",
                "element_type": "endnote",
                "marker": {"text": "1", "page": 0},
                "content": [{"page": 100, "text": "N"}],
            },
            {
                "id": "ct1",
                "element_type": "citation",
                "raw_text": "x",
                "citation_type": "author_date",
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
                "ref_type": "stephanus",
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
            Footnote, Endnote, Citation, BibEntry, Section,
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
            Footnote(
                id="fn1",
                marker=MarkerInfo(text="1", page=0),
                content=[ContentSpan(page=0, text="Note text")],
                location="page_bottom",
            ),
            Citation(
                id="ct1",
                raw_text="(Heidegger 1927)",
                citation_type=CitationType.AUTHOR_DATE,
                parsed=ParsedCitation(author="Heidegger", year="1927"),
            ),
            Section(id="sec1", title="Introduction", level=0, children=["sec1.1"]),
        ]
        json_bytes = ta.dump_json(elements, indent=2)
        restored = ta.validate_json(json_bytes)

        assert len(restored) == 3
        assert isinstance(restored[0], Footnote)
        assert isinstance(restored[1], Citation)
        assert isinstance(restored[2], Section)
        assert restored[0].marker.text == "1"
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
