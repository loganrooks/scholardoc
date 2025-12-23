"""
Unit tests for ScholarDoc core data models.

Tests the position-based annotation system from CORE_REPRESENTATION.md.
"""

import json

import pytest

from scholardoc.models import (
    # Content
    BibEntry,
    # Spans
    BlockQuoteSpan,
    # Enums
    ChunkStrategy,
    # Annotations
    CitationRef,
    CrossRef,
    # Metadata & Quality
    DocumentMetadata,
    DocumentType,
    EndnoteRef,
    FootnoteRef,
    Note,
    NoteSource,
    NoteType,
    PageQuality,
    PageSpan,
    ParagraphSpan,
    ParsedCitation,
    QualityInfo,
    QualityLevel,
    # Output
    ScholarDocument,
    SectionSpan,
    Span,
    TableOfContents,
    ToCEntry,
)


class TestSpanBasics:
    """Test base Span class functionality."""

    def test_span_creation(self):
        """Can create a basic span."""
        span = Span(start=10, end=20)
        assert span.start == 10
        assert span.end == 20
        assert len(span) == 10

    def test_span_validation_negative_start(self):
        """Span rejects negative start."""
        with pytest.raises(ValueError, match="start must be >= 0"):
            Span(start=-1, end=10)

    def test_span_validation_end_before_start(self):
        """Span rejects end before start."""
        with pytest.raises(ValueError, match="end .* must be >= start"):
            Span(start=20, end=10)

    def test_span_contains(self):
        """Span.contains works correctly."""
        span = Span(start=10, end=20)
        assert span.contains(10)  # Inclusive start
        assert span.contains(15)
        assert not span.contains(20)  # Exclusive end
        assert not span.contains(9)
        assert not span.contains(25)

    def test_span_overlaps(self):
        """Span.overlaps works correctly."""
        span1 = Span(start=10, end=20)
        span2 = Span(start=15, end=25)  # Overlaps
        span3 = Span(start=20, end=30)  # Adjacent, no overlap
        span4 = Span(start=0, end=5)  # No overlap

        assert span1.overlaps(span2)
        assert span2.overlaps(span1)
        assert not span1.overlaps(span3)  # Adjacent spans don't overlap
        assert not span1.overlaps(span4)

    def test_span_is_frozen(self):
        """Span is immutable (frozen)."""
        span = Span(start=10, end=20)
        with pytest.raises(AttributeError):
            span.start = 5


class TestAnnotations:
    """Test position-based annotation types."""

    def test_footnote_ref(self):
        """Can create FootnoteRef."""
        fn = FootnoteRef(position=42, marker="¹", target_id="fn1")
        assert fn.position == 42
        assert fn.marker == "¹"
        assert fn.target_id == "fn1"

    def test_endnote_ref(self):
        """Can create EndnoteRef."""
        en = EndnoteRef(position=100, marker="1", target_id="en1")
        assert en.position == 100
        assert en.marker == "1"
        assert en.target_id == "en1"

    def test_citation_ref(self):
        """Can create CitationRef."""
        cit = CitationRef(
            start=50,
            end=70,
            original="(Heidegger, 1927)",
            parsed=ParsedCitation(authors=["Heidegger"], year="1927"),
            bib_entry_id="bib1",
        )
        assert cit.start == 50
        assert cit.end == 70
        assert cit.original == "(Heidegger, 1927)"
        assert cit.parsed.authors == ["Heidegger"]
        assert cit.bib_entry_id == "bib1"

    def test_cross_ref(self):
        """Can create CrossRef."""
        cr = CrossRef(
            start=100,
            end=112,
            original="see p. 45",
            target_page="45",
        )
        assert cr.start == 100
        assert cr.original == "see p. 45"
        assert cr.target_page == "45"


class TestStructuralSpans:
    """Test structural span types."""

    def test_page_span(self):
        """Can create PageSpan with label."""
        page = PageSpan(start=0, end=1000, label="42", index=41)
        assert page.start == 0
        assert page.end == 1000
        assert page.label == "42"
        assert page.index == 41
        assert len(page) == 1000

    def test_section_span(self):
        """Can create SectionSpan with confidence."""
        section = SectionSpan(
            start=0,
            end=5000,
            title="Chapter 1: Introduction",
            level=1,
            confidence=0.95,
        )
        assert section.title == "Chapter 1: Introduction"
        assert section.level == 1
        assert section.confidence == 0.95

    def test_paragraph_span(self):
        """Can create ParagraphSpan."""
        para = ParagraphSpan(start=100, end=500)
        assert para.start == 100
        assert para.end == 500

    def test_block_quote_span(self):
        """Can create BlockQuoteSpan with indentation."""
        quote = BlockQuoteSpan(start=200, end=400, indentation_level=2)
        assert quote.indentation_level == 2


class TestContentTypes:
    """Test content storage types."""

    def test_note(self):
        """Can create Note with type and source."""
        note = Note(
            id="fn1",
            text="This is a footnote about Heidegger.",
            note_type=NoteType.FOOTNOTE,
            page_label="42",
            source=NoteSource.AUTHOR,
        )
        assert note.id == "fn1"
        assert note.text == "This is a footnote about Heidegger."
        assert note.note_type == NoteType.FOOTNOTE
        assert note.source == NoteSource.AUTHOR

    def test_bib_entry(self):
        """Can create BibEntry."""
        bib = BibEntry(
            id="heidegger1927",
            raw="Heidegger, M. (1927). Being and Time. SCM Press.",
            authors=["Martin Heidegger"],
            title="Being and Time",
            year="1927",
        )
        assert bib.id == "heidegger1927"
        assert bib.authors == ["Martin Heidegger"]

    def test_toc_entry(self):
        """Can create hierarchical ToCEntry."""
        entry = ToCEntry(
            title="Chapter 1",
            page_label="1",
            level=1,
            children=[
                ToCEntry(title="Section 1.1", page_label="5", level=2),
                ToCEntry(title="Section 1.2", page_label="15", level=2),
            ],
        )
        assert entry.title == "Chapter 1"
        assert len(entry.children) == 2
        assert entry.children[0].title == "Section 1.1"

    def test_table_of_contents(self):
        """Can create TableOfContents."""
        toc = TableOfContents(
            entries=[ToCEntry(title="Chapter 1", page_label="1", level=1)],
            page_range=(3, 5),
            confidence=0.85,
        )
        assert len(toc.entries) == 1
        assert toc.page_range == (3, 5)
        assert toc.confidence == 0.85


class TestMetadataAndQuality:
    """Test metadata and quality info types."""

    def test_document_metadata(self):
        """Can create DocumentMetadata with all fields."""
        meta = DocumentMetadata(
            title="Critique of Pure Reason",
            author="Immanuel Kant",
            authors=["Immanuel Kant"],
            document_type=DocumentType.BOOK,
            language="de",
            page_count=856,
        )
        assert meta.title == "Critique of Pure Reason"
        assert meta.document_type == DocumentType.BOOK
        assert meta.language == "de"

    def test_page_quality(self):
        """Can create PageQuality."""
        pq = PageQuality(
            page_index=5,
            page_label="vi",
            quality=QualityLevel.MARGINAL,
            confidence=0.65,
            issues=["OCR artifacts detected"],
        )
        assert pq.quality == QualityLevel.MARGINAL
        assert "OCR artifacts detected" in pq.issues

    def test_quality_info(self):
        """Can create QualityInfo with pages needing re-OCR."""
        qi = QualityInfo(
            overall=QualityLevel.GOOD,
            overall_confidence=0.92,
            needs_reocr=[5, 12, 45],
        )
        assert qi.overall == QualityLevel.GOOD
        assert 12 in qi.needs_reocr


class TestScholarDocumentCreation:
    """Test ScholarDocument creation and basic operations."""

    @pytest.fixture
    def sample_document(self) -> ScholarDocument:
        """Create a sample document for testing."""
        return ScholarDocument(
            text="The question of Being has been forgotten.",
            pages=[PageSpan(start=0, end=41, label="1", index=0)],
            sections=[
                SectionSpan(
                    start=0, end=41, title="Introduction", level=1, confidence=0.95
                )
            ],
            paragraphs=[ParagraphSpan(start=0, end=41)],
            metadata=DocumentMetadata(
                title="Being and Time",
                author="Martin Heidegger",
                document_type=DocumentType.BOOK,
            ),
            source_path="/path/to/book.pdf",
        )

    def test_basic_creation(self, sample_document):
        """Can create ScholarDocument with basic fields."""
        doc = sample_document
        assert doc.text == "The question of Being has been forgotten."
        assert len(doc.pages) == 1
        assert len(doc.sections) == 1
        assert doc.metadata.title == "Being and Time"

    def test_document_length(self, sample_document):
        """len() returns text length."""
        doc = sample_document
        assert len(doc) == 41

    def test_document_getitem(self, sample_document):
        """Can slice document text."""
        doc = sample_document
        assert doc[0:12] == "The question"
        assert doc[4:12] == "question"

    def test_document_repr(self, sample_document):
        """repr is informative."""
        doc = sample_document
        r = repr(doc)
        assert "41 chars" in r
        assert "pages=1" in r
        assert "sections=1" in r


class TestScholarDocumentQueries:
    """Test ScholarDocument query methods."""

    @pytest.fixture
    def document_with_structure(self) -> ScholarDocument:
        """Create document with multiple pages and sections."""
        text = "Page one content. " * 10 + "Page two content. " * 10
        mid = len("Page one content. " * 10)

        return ScholarDocument(
            text=text,
            pages=[
                PageSpan(start=0, end=mid, label="1", index=0),
                PageSpan(start=mid, end=len(text), label="2", index=1),
            ],
            sections=[
                SectionSpan(start=0, end=mid, title="Chapter 1", level=1),
                SectionSpan(start=mid, end=len(text), title="Chapter 2", level=1),
            ],
            paragraphs=[
                ParagraphSpan(start=0, end=mid),
                ParagraphSpan(start=mid, end=len(text)),
            ],
            footnote_refs=[
                FootnoteRef(position=10, marker="1", target_id="fn1"),
                FootnoteRef(position=mid + 10, marker="2", target_id="fn2"),
            ],
            notes={
                "fn1": Note(id="fn1", text="First footnote"),
                "fn2": Note(id="fn2", text="Second footnote"),
            },
            citations=[
                CitationRef(start=50, end=60, original="(Kant, 1781)"),
            ],
            metadata=DocumentMetadata(title="Test Doc"),
        )

    def test_text_range(self, document_with_structure):
        """text_range returns correct slice."""
        doc = document_with_structure
        assert doc.text_range(0, 4) == "Page"
        assert doc.text_range(5, 8) == "one"

    def test_page_for_position(self, document_with_structure):
        """page_for_position finds correct page."""
        doc = document_with_structure
        page1 = doc.page_for_position(10)
        assert page1 is not None
        assert page1.label == "1"

        page2 = doc.page_for_position(200)
        assert page2 is not None
        assert page2.label == "2"

    def test_page_for_position_not_found(self, document_with_structure):
        """page_for_position returns None for out of range."""
        doc = document_with_structure
        assert doc.page_for_position(10000) is None

    def test_pages_in_range(self, document_with_structure):
        """pages_in_range finds overlapping pages."""
        doc = document_with_structure
        # Range spanning both pages
        pages = doc.pages_in_range(100, 250)
        assert len(pages) == 2
        labels = [p.label for p in pages]
        assert "1" in labels
        assert "2" in labels

    def test_section_for_position(self, document_with_structure):
        """section_for_position finds correct section."""
        doc = document_with_structure
        section = doc.section_for_position(10)
        assert section is not None
        assert section.title == "Chapter 1"

    def test_footnotes_in_range(self, document_with_structure):
        """footnotes_in_range returns refs with notes."""
        doc = document_with_structure
        results = doc.footnotes_in_range(0, 50)
        assert len(results) == 1
        fn_ref, note = results[0]
        assert fn_ref.marker == "1"
        assert note.text == "First footnote"

    def test_citations_in_range(self, document_with_structure):
        """citations_in_range finds overlapping citations."""
        doc = document_with_structure
        cits = doc.citations_in_range(45, 65)
        assert len(cits) == 1
        assert cits[0].original == "(Kant, 1781)"

    def test_annotations_in_range(self, document_with_structure):
        """annotations_in_range finds all annotation types."""
        doc = document_with_structure
        anns = doc.annotations_in_range(0, 100)
        # Should find footnote and citation
        assert len(anns) >= 2


class TestScholarDocumentDerivedViews:
    """Test cached derived views."""

    @pytest.fixture
    def doc_with_sections(self) -> ScholarDocument:
        """Document with multiple sections."""
        return ScholarDocument(
            text="Intro text. Main content. Conclusion.",
            sections=[
                SectionSpan(start=0, end=12, title="Introduction", level=1),
                SectionSpan(start=12, end=26, title="Main Body", level=1),
                SectionSpan(start=26, end=37, title="Conclusion", level=1),
            ],
            paragraphs=[
                ParagraphSpan(start=0, end=12),
                ParagraphSpan(start=12, end=26),
                ParagraphSpan(start=26, end=37),
            ],
            pages=[
                PageSpan(start=0, end=20, label="1", index=0),
                PageSpan(start=20, end=37, label="2", index=1),
            ],
        )

    def test_paragraph_texts(self, doc_with_sections):
        """paragraph_texts returns paragraph strings."""
        doc = doc_with_sections
        texts = doc.paragraph_texts
        assert len(texts) == 3
        assert texts[0] == "Intro text. "

    def test_section_titles(self, doc_with_sections):
        """section_titles returns titles in order."""
        doc = doc_with_sections
        titles = doc.section_titles
        assert titles == ["Introduction", "Main Body", "Conclusion"]

    def test_page_labels(self, doc_with_sections):
        """page_labels returns labels in order."""
        doc = doc_with_sections
        labels = doc.page_labels
        assert labels == ["1", "2"]


class TestScholarDocumentExports:
    """Test export methods."""

    @pytest.fixture
    def doc_for_export(self) -> ScholarDocument:
        """Document with content for export testing."""
        return ScholarDocument(
            text="First paragraph.\n\nSecond paragraph with footnote reference.",
            footnote_refs=[FootnoteRef(position=45, marker="1", target_id="fn1")],
            notes={"fn1": Note(id="fn1", text="This is the footnote text.")},
            pages=[
                PageSpan(start=0, end=17, label="1", index=0),
                PageSpan(start=17, end=59, label="2", index=1),
            ],
            metadata=DocumentMetadata(title="Test Document", author="Test Author"),
        )

    def test_to_plain_text(self, doc_for_export):
        """to_plain_text returns clean text."""
        doc = doc_for_export
        plain = doc.to_plain_text()
        assert plain == doc.text
        assert "footnote" not in plain.lower() or "reference" in plain.lower()

    def test_to_markdown_basic(self, doc_for_export):
        """to_markdown produces valid markdown."""
        doc = doc_for_export
        md = doc.to_markdown(include_footnotes=False, include_page_markers=False)
        assert "Test Document" in md  # Title in frontmatter
        assert "First paragraph" in md

    def test_to_markdown_with_footnotes(self, doc_for_export):
        """to_markdown includes footnotes when requested."""
        doc = doc_for_export
        md = doc.to_markdown(include_footnotes=True)
        assert "[^1]:" in md
        assert "This is the footnote text" in md

    def test_to_markdown_with_page_markers(self, doc_for_export):
        """to_markdown includes page markers when requested."""
        doc = doc_for_export
        md = doc.to_markdown(include_page_markers=True, page_marker_style="comment")
        assert "<!-- p. 1 -->" in md or "<!-- p. 2 -->" in md


class TestRAGChunking:
    """Test RAG chunk generation."""

    @pytest.fixture
    def doc_for_chunking(self) -> ScholarDocument:
        """Document suitable for chunking tests."""
        # Create a longer document
        para1 = "This is the first paragraph. " * 20  # ~600 chars
        para2 = "This is the second paragraph. " * 20  # ~620 chars
        text = para1 + para2

        return ScholarDocument(
            text=text,
            paragraphs=[
                ParagraphSpan(start=0, end=len(para1)),
                ParagraphSpan(start=len(para1), end=len(text)),
            ],
            pages=[
                PageSpan(start=0, end=len(para1), label="1", index=0),
                PageSpan(start=len(para1), end=len(text), label="2", index=1),
            ],
            sections=[
                SectionSpan(start=0, end=len(text), title="Main Section", level=1)
            ],
            metadata=DocumentMetadata(title="Chunking Test", author="Test"),
            source_path="/test.pdf",
        )

    def test_chunk_by_page(self, doc_for_chunking):
        """to_rag_chunks with PAGE strategy creates page-based chunks."""
        doc = doc_for_chunking
        chunks = list(doc.to_rag_chunks(strategy=ChunkStrategy.PAGE))
        assert len(chunks) == 2
        assert chunks[0].page_labels == ["1"]
        assert chunks[1].page_labels == ["2"]

    def test_chunk_by_section(self, doc_for_chunking):
        """to_rag_chunks with SECTION strategy creates section-based chunks."""
        doc = doc_for_chunking
        chunks = list(doc.to_rag_chunks(strategy=ChunkStrategy.SECTION))
        assert len(chunks) == 1
        assert chunks[0].section == "Main Section"

    def test_chunk_semantic(self, doc_for_chunking):
        """to_rag_chunks with SEMANTIC respects paragraph boundaries."""
        doc = doc_for_chunking
        chunks = list(
            doc.to_rag_chunks(strategy=ChunkStrategy.SEMANTIC, max_tokens=100)
        )
        # Should create multiple chunks respecting paragraph boundaries
        assert len(chunks) >= 2

    def test_chunk_fixed_size(self, doc_for_chunking):
        """to_rag_chunks with FIXED_SIZE creates uniform chunks."""
        doc = doc_for_chunking
        chunks = list(
            doc.to_rag_chunks(strategy=ChunkStrategy.FIXED_SIZE, max_tokens=50)
        )
        # Should create many small chunks
        assert len(chunks) >= 3

    def test_chunk_metadata(self, doc_for_chunking):
        """RAGChunks include document metadata."""
        doc = doc_for_chunking
        chunks = list(doc.to_rag_chunks(strategy=ChunkStrategy.PAGE))
        chunk = chunks[0]

        assert chunk.doc_title == "Chunking Test"
        assert chunk.doc_author == "Test"
        assert chunk.source_path == "/test.pdf"

    def test_chunk_citation_property(self, doc_for_chunking):
        """RAGChunk.citation produces readable string."""
        doc = doc_for_chunking
        chunks = list(doc.to_rag_chunks(strategy=ChunkStrategy.PAGE))
        chunk = chunks[0]

        citation = chunk.citation
        assert "Chunking Test" in citation
        assert "p. 1" in citation


class TestScholarDocumentPersistence:
    """Test save/load functionality."""

    @pytest.fixture
    def complete_document(self) -> ScholarDocument:
        """Create a complete document with all fields populated."""
        return ScholarDocument(
            text="The beautiful morning. The sublime evening.",
            footnote_refs=[
                FootnoteRef(position=13, marker="¹", target_id="fn1"),
            ],
            endnote_refs=[
                EndnoteRef(position=35, marker="1", target_id="en1"),
            ],
            citations=[
                CitationRef(start=4, end=13, original="beautiful"),
            ],
            cross_refs=[
                CrossRef(start=24, end=31, original="sublime", target_page="42"),
            ],
            pages=[
                PageSpan(start=0, end=22, label="1", index=0),
                PageSpan(start=22, end=44, label="2", index=1),
            ],
            sections=[
                SectionSpan(start=0, end=44, title="Chapter 1", level=1, confidence=0.9),
            ],
            paragraphs=[
                ParagraphSpan(start=0, end=22),
                ParagraphSpan(start=22, end=44),
            ],
            block_quotes=[
                BlockQuoteSpan(start=4, end=13, indentation_level=1),
            ],
            notes={
                "fn1": Note(
                    id="fn1",
                    text="A footnote about beauty.",
                    note_type=NoteType.FOOTNOTE,
                    source=NoteSource.AUTHOR,
                ),
                "en1": Note(
                    id="en1",
                    text="An endnote about sublimity.",
                    note_type=NoteType.ENDNOTE,
                    source=NoteSource.TRANSLATOR,
                ),
            },
            bibliography=[
                BibEntry(
                    id="kant1790",
                    raw="Kant, I. (1790). Critique of Judgment.",
                    authors=["Immanuel Kant"],
                    title="Critique of Judgment",
                    year="1790",
                ),
            ],
            toc=TableOfContents(
                entries=[
                    ToCEntry(
                        title="Chapter 1",
                        page_label="1",
                        level=1,
                        children=[ToCEntry(title="Section 1.1", page_label="5", level=2)],
                    ),
                ],
                page_range=(0, 2),
                confidence=0.85,
            ),
            metadata=DocumentMetadata(
                title="Test Philosophy Book",
                author="Test Author",
                authors=["Test Author", "Second Author"],
                document_type=DocumentType.BOOK,
                language="en",
                page_count=100,
            ),
            source_path="/path/to/book.pdf",
            quality=QualityInfo(
                overall=QualityLevel.GOOD,
                overall_confidence=0.92,
                needs_reocr=[5, 10],
            ),
            processing_log=["Extracted with PyMuPDF", "Headings detected"],
        )

    def test_save_and_load_roundtrip(self, complete_document, tmp_path):
        """Document survives save/load roundtrip."""
        doc = complete_document
        save_path = tmp_path / "test.scholardoc"

        # Save
        doc.save(save_path)
        assert save_path.exists()

        # Load
        loaded = ScholarDocument.load(save_path)

        # Verify text
        assert loaded.text == doc.text

        # Verify annotations
        assert len(loaded.footnote_refs) == 1
        assert loaded.footnote_refs[0].position == 13
        assert loaded.footnote_refs[0].marker == "¹"

        assert len(loaded.endnote_refs) == 1
        assert len(loaded.citations) == 1
        assert len(loaded.cross_refs) == 1

        # Verify structural spans
        assert len(loaded.pages) == 2
        assert loaded.pages[0].label == "1"
        assert len(loaded.sections) == 1
        assert loaded.sections[0].confidence == 0.9
        assert len(loaded.paragraphs) == 2
        assert len(loaded.block_quotes) == 1

        # Verify notes
        assert "fn1" in loaded.notes
        assert loaded.notes["fn1"].note_type == NoteType.FOOTNOTE
        assert loaded.notes["en1"].source == NoteSource.TRANSLATOR

        # Verify bibliography
        assert len(loaded.bibliography) == 1
        assert loaded.bibliography[0].year == "1790"

        # Verify ToC
        assert loaded.toc is not None
        assert len(loaded.toc.entries) == 1
        assert len(loaded.toc.entries[0].children) == 1

        # Verify metadata
        assert loaded.metadata.title == "Test Philosophy Book"
        assert loaded.metadata.document_type == DocumentType.BOOK

        # Verify quality
        assert loaded.quality.overall == QualityLevel.GOOD
        assert 5 in loaded.quality.needs_reocr

        # Verify processing log
        assert len(loaded.processing_log) == 2

    def test_save_adds_extension(self, complete_document, tmp_path):
        """save() adds .scholardoc extension if missing."""
        doc = complete_document
        save_path = tmp_path / "test"  # No extension

        doc.save(save_path)
        assert (tmp_path / "test.scholardoc").exists()

    def test_saved_file_is_valid_json(self, complete_document, tmp_path):
        """Saved file is valid JSON."""
        doc = complete_document
        save_path = tmp_path / "test.scholardoc"

        doc.save(save_path)

        with open(save_path) as f:
            data = json.load(f)

        assert data["version"] == "1.0"
        assert "text" in data
        assert "metadata" in data


class TestEnumerations:
    """Test enum values."""

    def test_document_type_values(self):
        """DocumentType has expected values."""
        assert DocumentType.BOOK.value == "book"
        assert DocumentType.ARTICLE.value == "article"
        assert DocumentType.ESSAY.value == "essay"
        assert DocumentType.REPORT.value == "report"
        assert DocumentType.GENERIC.value == "generic"

    def test_note_type_values(self):
        """NoteType has expected values."""
        assert NoteType.FOOTNOTE.value == "footnote"
        assert NoteType.ENDNOTE.value == "endnote"
        assert NoteType.TRANSLATOR.value == "translator"
        assert NoteType.EDITOR.value == "editor"

    def test_chunk_strategy_values(self):
        """ChunkStrategy has expected values."""
        assert ChunkStrategy.SEMANTIC.value == "semantic"
        assert ChunkStrategy.FIXED_SIZE.value == "fixed_size"
        assert ChunkStrategy.PAGE.value == "page"
        assert ChunkStrategy.SECTION.value == "section"

    def test_quality_level_values(self):
        """QualityLevel has expected values."""
        assert QualityLevel.GOOD.value == "good"
        assert QualityLevel.MARGINAL.value == "marginal"
        assert QualityLevel.BAD.value == "bad"
