"""
Integration tests for the convert() orchestrator.

These tests use real PDF files to verify end-to-end conversion.
"""

from pathlib import Path

import pytest

from scholardoc import (
    ChunkStrategy,
    ConversionConfig,
    QualityLevel,
    ScholarDocument,
    convert,
)

# Path to sample PDFs in the spikes directory
SAMPLE_PDFS = Path(__file__).parent.parent.parent / "spikes" / "sample_pdfs"


def has_sample_pdfs() -> bool:
    """Check if sample PDFs are available."""
    return SAMPLE_PDFS.exists() and any(SAMPLE_PDFS.glob("*.pdf"))


# Skip all tests if no sample PDFs available
pytestmark = pytest.mark.skipif(
    not has_sample_pdfs(),
    reason="Sample PDFs not available in spikes/sample_pdfs/",
)


@pytest.fixture
def small_pdf() -> Path:
    """Get a small PDF for quick tests."""
    # Use a smaller excerpt if available
    excerpts = list(SAMPLE_PDFS.glob("*pages*.pdf"))
    if excerpts:
        return excerpts[0]
    # Fall back to any PDF
    pdfs = list(SAMPLE_PDFS.glob("*.pdf"))
    if pdfs:
        return sorted(pdfs, key=lambda p: p.stat().st_size)[0]
    pytest.skip("No PDF files found")


@pytest.fixture
def philosophy_pdf() -> Path:
    """Get a philosophy book PDF."""
    candidates = [
        SAMPLE_PDFS / "Heidegger_DiscourseOnThinking.pdf",
        SAMPLE_PDFS / "Derrida_WritingAndDifference.pdf",
        SAMPLE_PDFS / "Kant_CritiqueOfJudgement.pdf",
    ]
    for pdf in candidates:
        if pdf.exists():
            return pdf
    # Fall back to any PDF
    pdfs = list(SAMPLE_PDFS.glob("*.pdf"))
    if pdfs:
        return pdfs[0]
    pytest.skip("No philosophy PDFs found")


class TestConvertBasic:
    """Basic conversion tests."""

    def test_convert_returns_scholar_document(self, small_pdf):
        """convert() returns a ScholarDocument."""
        doc = convert(small_pdf)
        assert isinstance(doc, ScholarDocument)

    def test_convert_has_text(self, small_pdf):
        """Converted document has text content."""
        doc = convert(small_pdf)
        assert len(doc.text) > 0

    def test_convert_has_pages(self, small_pdf):
        """Converted document has page spans."""
        doc = convert(small_pdf)
        assert len(doc.pages) > 0

    def test_convert_pages_are_ordered(self, small_pdf):
        """Page spans are in order by position."""
        doc = convert(small_pdf)
        for i in range(1, len(doc.pages)):
            assert doc.pages[i].start >= doc.pages[i - 1].end

    def test_convert_has_paragraphs(self, small_pdf):
        """Converted document has paragraph spans."""
        doc = convert(small_pdf)
        assert len(doc.paragraphs) > 0

    def test_convert_has_metadata(self, small_pdf):
        """Converted document has metadata."""
        doc = convert(small_pdf)
        assert doc.metadata is not None
        assert doc.metadata.page_count > 0

    def test_convert_has_quality_info(self, small_pdf):
        """Converted document has quality info."""
        doc = convert(small_pdf)
        assert doc.quality is not None
        assert doc.quality.overall in [
            QualityLevel.GOOD,
            QualityLevel.MARGINAL,
            QualityLevel.BAD,
        ]

    def test_convert_has_processing_log(self, small_pdf):
        """Converted document has processing log."""
        doc = convert(small_pdf)
        assert len(doc.processing_log) > 0

    def test_convert_source_path_set(self, small_pdf):
        """Converted document has source_path set."""
        doc = convert(small_pdf)
        assert doc.source_path is not None
        assert Path(doc.source_path).name == small_pdf.name


class TestConvertWithConfig:
    """Test conversion with custom configuration."""

    def test_config_is_respected(self, small_pdf):
        """Custom config is used during conversion."""
        config = ConversionConfig(
            include_page_markers=True,
            detect_headings=True,
        )
        doc = convert(small_pdf, config)
        assert isinstance(doc, ScholarDocument)

    def test_error_handling_warn(self, tmp_path):
        """Config on_extraction_error='warn' returns minimal document."""
        # Create an invalid PDF
        fake_pdf = tmp_path / "invalid.pdf"
        fake_pdf.write_text("Not a real PDF")

        config = ConversionConfig(on_extraction_error="warn")
        doc = convert(fake_pdf, config)

        # Should return minimal document with error in log
        assert doc.text == ""
        assert any("failed" in entry.lower() for entry in doc.processing_log)


class TestConvertStructure:
    """Test structure extraction in converted documents."""

    def test_sections_detected(self, philosophy_pdf):
        """Sections are detected from PDF outline or headings."""
        doc = convert(philosophy_pdf)
        # May or may not have sections depending on the PDF
        # Just verify the structure is valid
        for section in doc.sections:
            assert section.start >= 0
            # end can be 0 for placeholder sections from structure extraction
            assert section.end >= section.start
            assert section.level >= 1

    def test_sections_dont_overlap(self, philosophy_pdf):
        """Section spans at the same level don't overlap."""
        doc = convert(philosophy_pdf)

        # Group by level
        by_level: dict[int, list] = {}
        for section in doc.sections:
            by_level.setdefault(section.level, []).append(section)

        # Check non-overlapping at each level
        for level, sections in by_level.items():
            sections_sorted = sorted(sections, key=lambda s: s.start)
            for i in range(1, len(sections_sorted)):
                assert sections_sorted[i].start >= sections_sorted[i - 1].end, (
                    f"Level {level} sections overlap: "
                    f"{sections_sorted[i - 1]} and {sections_sorted[i]}"
                )


class TestConvertOutput:
    """Test output generation from converted documents."""

    def test_to_plain_text(self, small_pdf):
        """to_plain_text() works on converted document."""
        doc = convert(small_pdf)
        text = doc.to_plain_text()
        assert len(text) > 0
        assert text == doc.text

    def test_to_markdown(self, small_pdf):
        """to_markdown() works on converted document."""
        doc = convert(small_pdf)
        md = doc.to_markdown()
        assert len(md) > 0
        # Should have content (frontmatter is optional based on config)

    def test_to_rag_chunks_page(self, small_pdf):
        """to_rag_chunks() with PAGE strategy works."""
        doc = convert(small_pdf)
        chunks = list(doc.to_rag_chunks(strategy=ChunkStrategy.PAGE))
        assert len(chunks) > 0
        assert all(len(c.text) > 0 for c in chunks)
        assert all(c.doc_title or c.source_path for c in chunks)

    def test_to_rag_chunks_semantic(self, small_pdf):
        """to_rag_chunks() with SEMANTIC strategy works."""
        doc = convert(small_pdf)
        chunks = list(doc.to_rag_chunks(strategy=ChunkStrategy.SEMANTIC, max_tokens=500))
        assert len(chunks) > 0

    def test_chunk_has_citation(self, small_pdf):
        """RAG chunks have usable citation strings."""
        doc = convert(small_pdf)
        chunks = list(doc.to_rag_chunks(strategy=ChunkStrategy.PAGE))
        for chunk in chunks:
            citation = chunk.citation
            assert len(citation) > 0
            # Citation should mention page
            assert "p." in citation or "page" in citation.lower() or len(citation) > 5


class TestConvertPersistence:
    """Test save/load of converted documents."""

    def test_save_and_load_json(self, small_pdf, tmp_path):
        """Converted document survives JSON save/load."""
        doc = convert(small_pdf)
        save_path = tmp_path / "test.scholardoc"

        doc.save(save_path)
        loaded = ScholarDocument.load(save_path)

        assert loaded.text == doc.text
        assert len(loaded.pages) == len(doc.pages)
        assert len(loaded.paragraphs) == len(doc.paragraphs)

    def test_save_and_load_sqlite(self, small_pdf, tmp_path):
        """Converted document survives SQLite save/load."""
        doc = convert(small_pdf)
        save_path = tmp_path / "test.scholardb"

        doc.save_sqlite(save_path)
        loaded = ScholarDocument.load_sqlite(save_path)

        assert loaded.text == doc.text
        assert len(loaded.pages) == len(doc.pages)


class TestConvertQuery:
    """Test query methods on converted documents."""

    def test_page_for_position(self, small_pdf):
        """page_for_position() works on converted document."""
        doc = convert(small_pdf)
        if len(doc.pages) > 0:
            mid = len(doc.text) // 2
            page = doc.page_for_position(mid)
            assert page is not None
            assert page.start <= mid < page.end

    def test_text_range(self, small_pdf):
        """text_range() works on converted document."""
        doc = convert(small_pdf)
        first_100 = doc.text_range(0, 100)
        assert first_100 == doc.text[:100]

    def test_pages_in_range(self, small_pdf):
        """pages_in_range() works on converted document."""
        doc = convert(small_pdf)
        if len(doc.pages) >= 2:
            # Get pages overlapping middle third
            third = len(doc.text) // 3
            pages = doc.pages_in_range(third, 2 * third)
            assert len(pages) >= 1


class TestConvertPhilosophyBooks:
    """Specific tests for philosophy book conversion."""

    @pytest.mark.slow
    def test_heidegger_discourse(self):
        """Convert Heidegger's Discourse on Thinking."""
        pdf = SAMPLE_PDFS / "Heidegger_DiscourseOnThinking.pdf"
        if not pdf.exists():
            pytest.skip("Heidegger PDF not available")

        doc = convert(pdf)

        # Should have substantial content
        assert len(doc.text) > 10000

        # Should have multiple pages
        assert len(doc.pages) > 10

        # Should have detected structure (may or may not have sections)
        assert len(doc.paragraphs) > 40  # Flexible - depends on paragraph detection

    @pytest.mark.slow
    def test_kant_critique(self):
        """Convert Kant's Critique of Judgement (scanned PDF)."""
        pdf = SAMPLE_PDFS / "Kant_CritiqueOfJudgement.pdf"
        if not pdf.exists():
            pytest.skip("Kant PDF not available")

        doc = convert(pdf)

        # Should have content despite being scanned
        assert len(doc.text) > 10000

        # Should have quality info
        # Kant is a scanned PDF, may have some OCR issues
        assert doc.quality is not None


class TestProfileBasedExtraction:
    """Test profile-based structure extraction."""

    def test_extractor_for_document_works(self, philosophy_pdf):
        """CascadingExtractor.for_document() works with real PDFs."""
        from scholardoc.extractors import CascadingExtractor
        from scholardoc.readers import PDFReader

        reader = PDFReader()
        raw = reader.read(philosophy_pdf)

        # Create extractor with auto-detected profile
        extractor = CascadingExtractor.for_document(raw)
        result = extractor.extract(raw)

        # Should have a profile
        assert result.profile_used is not None

        # Should still produce valid results
        assert isinstance(result.sections, list)
        assert result.confidence >= 0.0

    def test_book_profile_on_philosophy_text(self):
        """Book profile works on philosophy PDFs."""
        from scholardoc.extractors import BOOK_PROFILE, CascadingExtractor
        from scholardoc.readers import PDFReader

        pdf = SAMPLE_PDFS / "heidegger_pages_17-24_full_translator_preface.pdf"
        if not pdf.exists():
            pytest.skip("Heidegger PDF not available")

        reader = PDFReader()
        raw = reader.read(pdf)

        # Use book profile explicitly
        extractor = CascadingExtractor(profile=BOOK_PROFILE)
        result = extractor.extract(raw)

        assert result.profile_used == "book"
        assert len(result.processing_log) > 0

    def test_article_profile_disables_toc(self):
        """Article profile doesn't use ToC enrichment."""
        from scholardoc.extractors import ARTICLE_PROFILE, CascadingExtractor
        from scholardoc.readers import PDFReader

        pdf = SAMPLE_PDFS / "kant_critique_pages_64_65.pdf"
        if not pdf.exists():
            pytest.skip("Kant PDF not available")

        reader = PDFReader()
        raw = reader.read(pdf)

        extractor = CascadingExtractor(profile=ARTICLE_PROFILE)
        result = extractor.extract(raw)

        assert result.profile_used == "article"
        # ToC entries should not appear in log
        assert not any("ToC entries" in entry for entry in result.processing_log)
