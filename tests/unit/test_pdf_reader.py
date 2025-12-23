"""
Unit tests for PDF reader module.

Uses small sample PDFs from spikes/sample_pdfs/ for fast execution.
"""

from pathlib import Path

import pytest

from scholardoc.readers import (
    OutlineEntry,
    PageData,
    PDFReader,
    RawDocument,
    detect_body_font_size,
    estimate_document_type,
    get_font_statistics,
    has_abstract,
    has_toc_indicators,
)

# Test fixtures
SAMPLE_PDFS = Path(__file__).parent.parent.parent / "spikes" / "sample_pdfs"


@pytest.fixture
def small_pdf() -> Path:
    """Small 2-page Kant sample for fast tests."""
    return SAMPLE_PDFS / "kant_critique_pages_64_65.pdf"


@pytest.fixture
def derrida_pdf() -> Path:
    """6-page Derrida sample with footnotes."""
    return SAMPLE_PDFS / "derrida_footnote_pages_120_125.pdf"


@pytest.fixture
def heidegger_pdf() -> Path:
    """8-page Heidegger translator preface."""
    return SAMPLE_PDFS / "heidegger_pages_17-24_full_translator_preface.pdf"


@pytest.fixture
def reader() -> PDFReader:
    """Default PDF reader instance."""
    return PDFReader()


class TestPDFReaderBasics:
    """Test basic PDF reader functionality."""

    def test_read_returns_raw_document(self, reader, small_pdf):
        """read() returns RawDocument."""
        raw = reader.read(small_pdf)
        assert isinstance(raw, RawDocument)

    def test_raw_document_has_pages(self, reader, small_pdf):
        """RawDocument contains page data."""
        raw = reader.read(small_pdf)
        assert raw.page_count == 2
        assert len(raw.pages) == 2

    def test_page_data_structure(self, reader, small_pdf):
        """PageData has expected fields."""
        raw = reader.read(small_pdf)
        page = raw.pages[0]

        assert isinstance(page, PageData)
        assert page.index == 0
        assert isinstance(page.label, str)
        assert page.width > 0
        assert page.height > 0
        assert isinstance(page.text, str)
        assert isinstance(page.blocks, list)

    def test_text_extraction(self, reader, small_pdf):
        """Text is extracted from pages."""
        raw = reader.read(small_pdf)
        assert len(raw.text) > 100
        assert len(raw.pages[0].text) > 50

    def test_file_not_found_raises(self, reader):
        """read() raises for missing file."""
        with pytest.raises(FileNotFoundError):
            reader.read("/nonexistent/path.pdf")

    def test_source_path_stored(self, reader, small_pdf):
        """Source path is stored in RawDocument."""
        raw = reader.read(small_pdf)
        assert raw.source_path == small_pdf


class TestTextBlocks:
    """Test text block extraction with positions and fonts."""

    def test_blocks_have_positions(self, reader, small_pdf):
        """TextBlocks have position information."""
        raw = reader.read(small_pdf)
        blocks = raw.pages[0].blocks

        assert len(blocks) > 0
        for block in blocks[:5]:
            assert block.x0 >= 0
            assert block.y0 >= 0
            assert block.x1 > block.x0
            assert block.y1 > block.y0

    def test_blocks_have_font_info(self, reader, small_pdf):
        """TextBlocks have font information."""
        raw = reader.read(small_pdf)
        blocks = raw.pages[0].blocks

        for block in blocks[:5]:
            assert isinstance(block.font_name, str)
            assert block.font_size > 0
            assert isinstance(block.is_bold, bool)
            assert isinstance(block.is_italic, bool)

    def test_blocks_have_text(self, reader, small_pdf):
        """TextBlocks have text content."""
        raw = reader.read(small_pdf)
        blocks = raw.pages[0].blocks

        texts = [b.text for b in blocks if b.text]
        assert len(texts) > 0

    def test_block_width_height(self, reader, small_pdf):
        """TextBlock width/height properties work."""
        raw = reader.read(small_pdf)
        block = raw.pages[0].blocks[0]

        assert block.width == block.x1 - block.x0
        assert block.height == block.y1 - block.y0


class TestPageLabels:
    """Test page label extraction."""

    def test_page_labels_extracted(self, reader, small_pdf):
        """Page labels are extracted."""
        raw = reader.read(small_pdf)
        labels = [p.label for p in raw.pages]

        # Should have labels for all pages
        assert len(labels) == raw.page_count
        assert all(len(label) > 0 for label in labels)

    def test_page_labels_for_derrida(self, reader, derrida_pdf):
        """Derrida sample has proper page labels."""
        raw = reader.read(derrida_pdf)

        # These pages should have meaningful labels
        assert raw.page_count == 6
        labels = [p.label for p in raw.pages]
        assert all(label for label in labels)


class TestPDFOutline:
    """Test PDF outline/bookmark extraction."""

    def test_outline_extraction(self, reader, heidegger_pdf):
        """Outline entries are extracted when present."""
        raw = reader.read(heidegger_pdf)

        # May or may not have outline
        assert isinstance(raw.outline, list)
        for entry in raw.outline:
            assert isinstance(entry, OutlineEntry)
            assert entry.level >= 1
            assert isinstance(entry.title, str)
            assert entry.page_index >= 0

    def test_has_outline_property(self, reader, small_pdf):
        """has_outline property works."""
        raw = reader.read(small_pdf)
        assert isinstance(raw.has_outline, bool)


class TestMetadata:
    """Test PDF metadata extraction."""

    def test_metadata_extracted(self, reader, small_pdf):
        """Metadata dictionary is extracted."""
        raw = reader.read(small_pdf)

        assert isinstance(raw.metadata, dict)
        assert "title" in raw.metadata
        assert "author" in raw.metadata
        assert "creator" in raw.metadata

    def test_metadata_values_or_none(self, reader, small_pdf):
        """Metadata values are strings or None."""
        raw = reader.read(small_pdf)

        for _key, value in raw.metadata.items():
            assert value is None or isinstance(value, str)


class TestRawDocumentQueries:
    """Test RawDocument query methods."""

    def test_text_property(self, reader, small_pdf):
        """text property returns full document text."""
        raw = reader.read(small_pdf)
        full_text = raw.text

        assert isinstance(full_text, str)
        assert len(full_text) > 0
        # Text should be cached
        assert raw.text is full_text

    def test_page_positions(self, reader, small_pdf):
        """page_positions returns start/end for each page."""
        raw = reader.read(small_pdf)
        positions = raw.page_positions

        assert len(positions) == raw.page_count
        for start, end in positions:
            assert start >= 0
            assert end >= start

    def test_page_for_position(self, reader, small_pdf):
        """page_for_position finds correct page."""
        raw = reader.read(small_pdf)

        # Position 0 should be page 0
        assert raw.page_for_position(0) == 0

        # Position beyond text should return None
        assert raw.page_for_position(len(raw.text) + 1000) is None

    def test_position_to_page(self, reader, small_pdf):
        """position_to_page returns page start position."""
        raw = reader.read(small_pdf)

        pos0 = raw.position_to_page(0)
        assert pos0 == 0

        if raw.page_count > 1:
            pos1 = raw.position_to_page(1)
            assert pos1 > 0

    def test_first_pages_text(self, reader, derrida_pdf):
        """first_pages_text returns text from first 20 pages."""
        raw = reader.read(derrida_pdf)
        first_text = raw.first_pages_text

        assert isinstance(first_text, str)
        assert len(first_text) > 0


class TestFontStatistics:
    """Test font analysis utilities."""

    def test_get_font_statistics(self, reader, small_pdf):
        """get_font_statistics returns size stats."""
        raw = reader.read(small_pdf)
        stats = get_font_statistics(raw)

        assert "min" in stats
        assert "max" in stats
        assert "median" in stats
        assert "mean" in stats
        assert stats["min"] <= stats["median"] <= stats["max"]

    def test_detect_body_font_size(self, reader, small_pdf):
        """detect_body_font_size returns reasonable value."""
        raw = reader.read(small_pdf)
        body_size = detect_body_font_size(raw)

        assert 8 <= body_size <= 16  # Typical body text range


class TestDocumentTypeDetection:
    """Test document type detection utilities."""

    def test_has_toc_indicators(self, reader, derrida_pdf):
        """has_toc_indicators detects ToC presence."""
        raw = reader.read(derrida_pdf)
        result = has_toc_indicators(raw)

        assert isinstance(result, bool)

    def test_has_abstract(self, reader, small_pdf):
        """has_abstract detects abstract presence."""
        raw = reader.read(small_pdf)
        result = has_abstract(raw)

        assert isinstance(result, bool)

    def test_estimate_document_type(self, reader, small_pdf):
        """estimate_document_type returns valid type."""
        raw = reader.read(small_pdf)
        doc_type = estimate_document_type(raw)

        assert doc_type in ["book", "article", "essay", "report", "generic"]


class TestReaderOptions:
    """Test reader configuration options."""

    def test_extract_images_option(self, small_pdf):
        """extract_images option marks pages with images."""
        reader = PDFReader(extract_images=True)
        raw = reader.read(small_pdf)

        # has_images should be set
        for page in raw.pages:
            assert isinstance(page.has_images, bool)

    def test_merge_blocks_option(self, small_pdf):
        """merge_blocks option affects block count."""
        reader_merged = PDFReader(merge_blocks=True)
        reader_unmerged = PDFReader(merge_blocks=False)

        raw_merged = reader_merged.read(small_pdf)
        raw_unmerged = reader_unmerged.read(small_pdf)

        # Merged should have fewer or equal blocks
        merged_count = sum(len(p.blocks) for p in raw_merged.pages)
        unmerged_count = sum(len(p.blocks) for p in raw_unmerged.pages)

        assert merged_count <= unmerged_count


class TestMultiplePages:
    """Test multi-page document handling."""

    def test_all_pages_extracted(self, reader, derrida_pdf):
        """All pages are extracted from multi-page PDF."""
        raw = reader.read(derrida_pdf)

        assert raw.page_count == len(raw.pages)
        assert raw.page_count == 6

    def test_page_indices_sequential(self, reader, derrida_pdf):
        """Page indices are sequential from 0."""
        raw = reader.read(derrida_pdf)

        for i, page in enumerate(raw.pages):
            assert page.index == i

    def test_text_spans_all_pages(self, reader, derrida_pdf):
        """Full text contains content from all pages."""
        raw = reader.read(derrida_pdf)

        for page in raw.pages:
            if page.text:
                # First non-trivial word from each page should be in full text
                words = page.text.split()[:3]
                for word in words:
                    if len(word) > 4:
                        assert word in raw.text
                        break


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_page_handling(self, reader, small_pdf):
        """Empty pages are handled gracefully."""
        raw = reader.read(small_pdf)

        # All pages should have PageData, even if empty
        for page in raw.pages:
            assert isinstance(page, PageData)
            assert isinstance(page.text, str)  # May be empty string

    def test_special_characters_in_text(self, reader, derrida_pdf):
        """Special characters are preserved in text."""
        raw = reader.read(derrida_pdf)

        # Philosophy texts often have special characters
        # Just verify text extraction doesn't crash
        assert isinstance(raw.text, str)


@pytest.mark.parametrize(
    "pdf_name",
    [
        "kant_critique_pages_64_65.pdf",
        "derrida_footnote_pages_120_125.pdf",
        "heidegger_pages_22-23_primary_footnote_test.pdf",
    ],
)
class TestMultiplePDFs:
    """Test reader works across different PDF types."""

    def test_read_succeeds(self, reader, pdf_name):
        """Reader can read the PDF without error."""
        pdf_path = SAMPLE_PDFS / pdf_name
        if not pdf_path.exists():
            pytest.skip(f"Sample PDF not found: {pdf_name}")

        raw = reader.read(pdf_path)
        assert raw.page_count > 0
        assert len(raw.text) > 0
