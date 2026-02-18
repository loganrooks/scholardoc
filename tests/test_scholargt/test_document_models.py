"""Tests for DocumentGT and related document-level models.

Covers DocumentGT creation, cross-page semantic elements via discriminated union,
document structure (ToC, sections), relationships (footnote/citation links),
round-trip JSON serialization, extra field compatibility, and a realistic
Heidegger Being and Time example.
"""

from datetime import UTC, datetime

from scholargt.schema import (
    SCHEMA_VERSION,
    BibEntry,
    Citation,
    CitationBibLink,
    ContentSpan,
    DocumentGT,
    DocumentRelationships,
    DocumentSource,
    DocumentStructure,
    Footnote,
    FootnoteLink,
    FormattingAnnotation,
    MarkerInfo,
    PageNumberAnnotation,
    ParsedCitation,
    Section,
    SemanticElement,
    ToCEntry,
)
from scholargt.schema.base import VerificationRecord
from scholargt.schema.labels import CitationType, FormattingType

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


# ---------- Relationship model tests ----------


class TestRelationshipModels:
    def test_footnote_link(self):
        fl = FootnoteLink(
            marker_id="fn1_marker",
            content_id="fn1_content",
            link_type="footnote",
        )
        assert fl.marker_id == "fn1_marker"
        assert fl.link_type == "footnote"

    def test_footnote_link_default_type(self):
        fl = FootnoteLink(marker_id="m1", content_id="c1")
        assert fl.link_type == "footnote"

    def test_endnote_link(self):
        fl = FootnoteLink(
            marker_id="en1_marker",
            content_id="en1_content",
            link_type="endnote",
        )
        assert fl.link_type == "endnote"

    def test_citation_bib_link(self):
        cbl = CitationBibLink(
            citation_id="ct1", bib_entry_id="bib1"
        )
        assert cbl.citation_id == "ct1"
        assert cbl.bib_entry_id == "bib1"

    def test_document_relationships(self):
        rels = DocumentRelationships(
            footnote_links=[
                FootnoteLink(marker_id="m1", content_id="c1"),
            ],
            citation_bib_links=[
                CitationBibLink(
                    citation_id="ct1", bib_entry_id="bib1"
                ),
            ],
            cross_refs=["xref1", "xref2"],
        )
        assert len(rels.footnote_links) == 1
        assert len(rels.citation_bib_links) == 1
        assert rels.cross_refs == ["xref1", "xref2"]

    def test_document_relationships_defaults(self):
        rels = DocumentRelationships()
        assert rels.footnote_links == []
        assert rels.citation_bib_links == []
        assert rels.cross_refs == []


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
        assert doc.relationships is None
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
        """DocumentGT.elements accepts mixed SemanticElement types."""
        doc = DocumentGT(
            document_id="d1",
            source=DocumentSource(pdf="test.pdf"),
            elements=[
                Footnote(
                    id="fn1",
                    marker=MarkerInfo(text="1", page=0),
                    content=[ContentSpan(page=0, text="Note")],
                    location="page_bottom",
                ),
                Citation(
                    id="ct1",
                    raw_text="(Heidegger 1927)",
                    citation_type=CitationType.AUTHOR_DATE,
                ),
                Section(
                    id="sec1",
                    title="Introduction",
                    level=0,
                ),
            ],
        )
        assert len(doc.elements) == 3
        assert isinstance(doc.elements[0], Footnote)
        assert isinstance(doc.elements[1], Citation)
        assert isinstance(doc.elements[2], Section)

    def test_document_elements_discriminated_union_from_json(self):
        """Elements deserialize correctly via discriminated union."""
        json_str = """{
            "document_id": "d1",
            "source": {"pdf": "test.pdf"},
            "elements": [
                {
                    "id": "fn1",
                    "element_type": "footnote",
                    "marker": {"text": "1", "page": 0},
                    "content": [{"page": 0, "text": "Note"}],
                    "location": "page_bottom"
                },
                {
                    "id": "ct1",
                    "element_type": "citation",
                    "raw_text": "(Heidegger 1927)",
                    "citation_type": "author_date"
                }
            ]
        }"""
        doc = DocumentGT.model_validate_json(json_str)
        assert len(doc.elements) == 2
        assert isinstance(doc.elements[0], Footnote)
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

    def test_document_with_relationships(self):
        doc = DocumentGT(
            document_id="d1",
            source=DocumentSource(pdf="test.pdf"),
            relationships=DocumentRelationships(
                footnote_links=[
                    FootnoteLink(marker_id="m1", content_id="c1"),
                ],
                citation_bib_links=[
                    CitationBibLink(
                        citation_id="ct1",
                        bib_entry_id="bib1",
                    ),
                ],
            ),
        )
        assert doc.relationships is not None
        assert len(doc.relationships.footnote_links) == 1
        assert len(doc.relationships.citation_bib_links) == 1

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
        """Full DocumentGT round-trip serialization."""
        doc = DocumentGT(
            document_id="d1",
            source=DocumentSource(
                pdf="test.pdf",
                title="Test",
                author="Author",
            ),
            elements=[
                Footnote(
                    id="fn1",
                    marker=MarkerInfo(text="1", page=0),
                    content=[ContentSpan(page=0, text="Note")],
                    location="page_bottom",
                ),
                Citation(
                    id="ct1",
                    raw_text="(Author 2024)",
                    citation_type=CitationType.AUTHOR_DATE,
                ),
            ],
            structure=DocumentStructure(
                toc=[ToCEntry(title="Ch 1", level=0)],
                sections=["sec1"],
            ),
            relationships=DocumentRelationships(
                footnote_links=[
                    FootnoteLink(marker_id="m1", content_id="fn1"),
                ],
            ),
        )
        json_str = doc.model_dump_json(indent=2)
        restored = DocumentGT.model_validate_json(json_str)

        assert restored.document_id == "d1"
        assert restored.schema_version == SCHEMA_VERSION
        assert restored.source.title == "Test"
        assert len(restored.elements) == 2
        assert isinstance(restored.elements[0], Footnote)
        assert isinstance(restored.elements[1], Citation)
        assert restored.structure is not None
        assert len(restored.structure.toc) == 1
        assert restored.relationships is not None
        assert len(restored.relationships.footnote_links) == 1

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
    """Full realistic example: Heidegger Being and Time snippet."""

    def test_heidegger_being_and_time(self):
        """A realistic DocumentGT for Being and Time with cross-page
        footnote, citation, section structure, and relationships."""
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
            elements=[
                # Cross-page footnote
                Footnote(
                    id="fn_p41_1",
                    marker=MarkerInfo(
                        text="1",
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
                    location="page_bottom",
                    note_source="translator",
                ),
                # Citation using SZ abbreviation
                Citation(
                    id="ct_sz_41",
                    raw_text="(SZ, 41)",
                    citation_type=CitationType.ABBREVIATED,
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
                    parsed=ParsedCitation(
                        author="Heidegger",
                        year="1927",
                        work="Sein und Zeit",
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
            relationships=DocumentRelationships(
                footnote_links=[
                    FootnoteLink(
                        marker_id="fn_p41_1",
                        content_id="fn_p41_1",
                    ),
                ],
                citation_bib_links=[
                    CitationBibLink(
                        citation_id="ct_sz_41",
                        bib_entry_id="bib_sz",
                    ),
                ],
            ),
        )

        # Verify structure
        assert doc.document_id == "heidegger_sz_1962"
        assert doc.source.translator is not None
        assert "Macquarrie" in doc.source.translator
        assert doc.page_range == (0, 524)
        assert len(doc.elements) == 5

        # Verify discriminated union types
        assert isinstance(doc.elements[0], Footnote)
        assert isinstance(doc.elements[1], Citation)
        assert isinstance(doc.elements[2], BibEntry)
        assert isinstance(doc.elements[3], Section)
        assert isinstance(doc.elements[4], PageNumberAnnotation)

        # Verify cross-page footnote
        fn = doc.elements[0]
        assert isinstance(fn, Footnote)
        assert len(fn.content) == 2
        assert fn.content[1].is_continuation is True

        # Verify relationships
        assert doc.relationships is not None
        assert len(doc.relationships.footnote_links) == 1
        assert len(doc.relationships.citation_bib_links) == 1

        # Round-trip
        json_str = doc.model_dump_json(indent=2)
        restored = DocumentGT.model_validate_json(json_str)
        assert restored.document_id == doc.document_id
        assert len(restored.elements) == 5
        assert isinstance(restored.elements[0], Footnote)
        assert restored.formatting[0].text == "Sein und Zeit"


# ---------- Import from scholargt.schema tests ----------


class TestSchemaPackageExports:
    """Verify all public models are importable from scholargt.schema."""

    def test_base_models_importable(self):
        from scholargt.schema import BBox, GTElement, VerificationRecord

        assert BBox is not None
        assert GTElement is not None
        assert VerificationRecord is not None

    def test_page_models_importable(self):
        from scholargt.schema import PageGT, PageQuality, Region

        assert PageGT is not None
        assert PageQuality is not None
        assert Region is not None

    def test_semantic_models_importable(self):
        from scholargt.schema import (
            Footnote,
            ToCEntry,
        )

        assert Footnote is not None
        assert SemanticElement is not None
        assert ToCEntry is not None

    def test_document_models_importable(self):
        from scholargt.schema import (
            DocumentGT,
            FootnoteLink,
        )

        assert DocumentGT is not None
        assert FootnoteLink is not None

    def test_formatting_importable(self):
        from scholargt.schema import FormattingAnnotation

        assert FormattingAnnotation is not None

    def test_labels_importable(self):
        from scholargt.schema import (
            CitationType,
            SpatialLabel,
        )

        assert len(CitationType) == 7
        assert len(SpatialLabel) == 17

    def test_version_importable(self):
        from scholargt.schema import SCHEMA_VERSION

        assert SCHEMA_VERSION == "1.0.0"
