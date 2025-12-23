"""
Unit tests for structure extraction module.

Tests the cascading extractor and individual sources.
"""

from pathlib import Path

import pytest

from scholardoc.extractors import (
    CascadingExtractor,
    HeadingDetectionSource,
    HierarchyValidator,
    MinimumContentValidator,
    NoOverlapValidator,
    PDFOutlineSource,
    SectionCandidate,
    StructureResult,
    ToCParserSource,
)
from scholardoc.models import SectionSpan
from scholardoc.readers import PDFReader, RawDocument

# Test fixtures
SAMPLE_PDFS = Path(__file__).parent.parent.parent / "spikes" / "sample_pdfs"


@pytest.fixture
def reader() -> PDFReader:
    """PDF reader instance."""
    return PDFReader()


@pytest.fixture
def small_pdf() -> Path:
    """Small 2-page Kant sample."""
    return SAMPLE_PDFS / "kant_critique_pages_64_65.pdf"


@pytest.fixture
def heidegger_pdf() -> Path:
    """8-page Heidegger with potential headings."""
    return SAMPLE_PDFS / "heidegger_pages_17-24_full_translator_preface.pdf"


@pytest.fixture
def raw_doc(reader, small_pdf) -> RawDocument:
    """Raw document for testing."""
    return reader.read(small_pdf)


@pytest.fixture
def heidegger_doc(reader, heidegger_pdf) -> RawDocument:
    """Heidegger document for testing."""
    return reader.read(heidegger_pdf)


class TestSectionCandidate:
    """Test SectionCandidate dataclass."""

    def test_candidate_creation(self):
        """Can create a section candidate."""
        candidate = SectionCandidate(
            start=0,
            end=1000,
            title="Chapter 1",
            level=1,
            confidence=0.95,
            source="pdf_outline",
            page_index=0,
        )
        assert candidate.title == "Chapter 1"
        assert candidate.confidence == 0.95
        assert candidate.source == "pdf_outline"

    def test_candidate_with_evidence(self):
        """Candidate stores evidence dict."""
        candidate = SectionCandidate(
            start=0,
            end=None,
            title="Section 1.1",
            level=2,
            confidence=0.7,
            source="heading_detection",
            page_index=5,
            evidence={"font_size": 14.0, "is_bold": True},
        )
        assert candidate.evidence["font_size"] == 14.0
        assert candidate.evidence["is_bold"] is True


class TestPDFOutlineSource:
    """Test PDF outline extraction source."""

    def test_source_name(self):
        """Source has correct name."""
        source = PDFOutlineSource()
        assert source.name == "pdf_outline"

    def test_extract_returns_list(self, raw_doc):
        """extract() returns list of candidates."""
        source = PDFOutlineSource()
        candidates = source.extract(raw_doc)
        assert isinstance(candidates, list)

    def test_extract_with_no_outline(self, raw_doc):
        """Returns empty list when no outline present."""
        source = PDFOutlineSource()
        candidates = source.extract(raw_doc)
        # May or may not have outline
        assert isinstance(candidates, list)
        for c in candidates:
            assert isinstance(c, SectionCandidate)

    def test_default_confidence(self, raw_doc):
        """Default confidence is 0.95."""
        source = PDFOutlineSource()
        candidates = source.extract(raw_doc)
        for c in candidates:
            assert c.confidence == 0.95

    def test_custom_confidence(self, raw_doc):
        """Can customize confidence level."""
        source = PDFOutlineSource(confidence=0.9)
        candidates = source.extract(raw_doc)
        for c in candidates:
            assert c.confidence == 0.9


class TestHeadingDetectionSource:
    """Test heading detection source."""

    def test_source_name(self):
        """Source has correct name."""
        source = HeadingDetectionSource()
        assert source.name == "heading_detection"

    def test_extract_returns_list(self, raw_doc):
        """extract() returns list of candidates."""
        source = HeadingDetectionSource()
        candidates = source.extract(raw_doc)
        assert isinstance(candidates, list)

    def test_confidence_in_range(self, heidegger_doc):
        """Confidence scores are within min/max range."""
        source = HeadingDetectionSource(min_confidence=0.5, max_confidence=0.8)
        candidates = source.extract(heidegger_doc)

        for c in candidates:
            assert 0.5 <= c.confidence <= 0.8

    def test_candidates_have_evidence(self, heidegger_doc):
        """Candidates include evidence dict."""
        source = HeadingDetectionSource()
        candidates = source.extract(heidegger_doc)

        for c in candidates:
            assert "font_size" in c.evidence
            assert isinstance(c.evidence["font_size"], (int, float))


class TestToCParserSource:
    """Test ToC parser source."""

    def test_source_name(self):
        """Source has correct name."""
        source = ToCParserSource()
        assert source.name == "toc_parser"

    def test_extract_returns_list(self, raw_doc):
        """extract() returns list of candidates."""
        source = ToCParserSource()
        candidates = source.extract(raw_doc)
        assert isinstance(candidates, list)


class TestNoOverlapValidator:
    """Test overlap validation."""

    def test_no_issues_for_non_overlapping(self):
        """No issues when sections don't overlap."""
        validator = NoOverlapValidator()
        sections = [
            SectionSpan(start=0, end=100, title="A", level=1),
            SectionSpan(start=100, end=200, title="B", level=1),
        ]
        issues = validator.check(sections)
        assert len(issues) == 0

    def test_detects_overlap(self):
        """Detects overlapping sections."""
        validator = NoOverlapValidator()
        sections = [
            SectionSpan(start=0, end=150, title="A", level=1),
            SectionSpan(start=100, end=200, title="B", level=1),
        ]
        issues = validator.check(sections)
        assert len(issues) == 1
        assert issues[0].type == "overlap"


class TestHierarchyValidator:
    """Test hierarchy validation."""

    def test_no_issues_for_proper_hierarchy(self):
        """No issues when hierarchy is proper."""
        validator = HierarchyValidator()
        sections = [
            SectionSpan(start=0, end=500, title="Chapter", level=1),
            SectionSpan(start=500, end=1000, title="Section", level=2),
        ]
        issues = validator.check(sections)
        assert len(issues) == 0

    def test_detects_level_skip(self):
        """Detects when levels are skipped."""
        validator = HierarchyValidator()
        sections = [
            SectionSpan(start=0, end=500, title="Chapter", level=1),
            SectionSpan(start=500, end=1000, title="SubSub", level=3),  # Skip level 2
        ]
        issues = validator.check(sections)
        assert len(issues) == 1
        assert issues[0].type == "level_skip"


class TestMinimumContentValidator:
    """Test minimum content validation."""

    def test_no_issues_for_long_sections(self):
        """No issues when sections are long enough."""
        validator = MinimumContentValidator(min_chars=100)
        sections = [
            SectionSpan(start=0, end=500, title="A", level=1),
        ]
        issues = validator.check(sections)
        assert len(issues) == 0

    def test_detects_short_section(self):
        """Detects very short sections."""
        validator = MinimumContentValidator(min_chars=100)
        sections = [
            SectionSpan(start=0, end=50, title="A", level=1),  # Only 50 chars
        ]
        issues = validator.check(sections)
        assert len(issues) == 1
        assert issues[0].type == "short_section"


class TestCascadingExtractor:
    """Test the main cascading extractor."""

    def test_extract_returns_structure_result(self, raw_doc):
        """extract() returns StructureResult."""
        extractor = CascadingExtractor()
        result = extractor.extract(raw_doc)
        assert isinstance(result, StructureResult)

    def test_result_has_sections(self, heidegger_doc):
        """Result contains section list."""
        extractor = CascadingExtractor()
        result = extractor.extract(heidegger_doc)
        assert isinstance(result.sections, list)

    def test_result_has_candidates(self, raw_doc):
        """Result includes all candidates from sources."""
        extractor = CascadingExtractor()
        result = extractor.extract(raw_doc)
        assert isinstance(result.candidates, list)

    def test_result_has_processing_log(self, raw_doc):
        """Result includes processing log."""
        extractor = CascadingExtractor()
        result = extractor.extract(raw_doc)
        assert isinstance(result.processing_log, list)
        assert len(result.processing_log) > 0

    def test_result_has_confidence(self, raw_doc):
        """Result has overall confidence score."""
        extractor = CascadingExtractor()
        result = extractor.extract(raw_doc)
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0

    def test_result_has_primary_source(self, raw_doc):
        """Result indicates primary source used."""
        extractor = CascadingExtractor()
        result = extractor.extract(raw_doc)
        assert result.primary_source in ["pdf_outline", "heading_detection"]

    def test_sections_are_sorted(self, heidegger_doc):
        """Sections are sorted by start position."""
        extractor = CascadingExtractor()
        result = extractor.extract(heidegger_doc)

        if len(result.sections) > 1:
            for i in range(len(result.sections) - 1):
                assert result.sections[i].start <= result.sections[i + 1].start

    def test_sections_have_end_positions(self, heidegger_doc):
        """All sections have end positions filled."""
        extractor = CascadingExtractor()
        result = extractor.extract(heidegger_doc)

        for section in result.sections:
            assert section.end is not None
            # End should be >= start (equal when adjacent sections at same position)
            assert section.end >= section.start

    def test_min_confidence_filtering(self, heidegger_doc):
        """Sections below min_confidence are filtered."""
        # With high threshold, fewer sections
        high_extractor = CascadingExtractor(min_confidence=0.9)
        high_result = high_extractor.extract(heidegger_doc)

        # With low threshold, more sections
        low_extractor = CascadingExtractor(min_confidence=0.3)
        low_result = low_extractor.extract(heidegger_doc)

        # Low threshold should find at least as many
        assert len(low_result.sections) >= len(high_result.sections)

    def test_custom_sources(self, raw_doc):
        """Can use custom source instances."""
        custom_outline = PDFOutlineSource(confidence=0.99)
        extractor = CascadingExtractor(outline_source=custom_outline)
        result = extractor.extract(raw_doc)
        assert isinstance(result, StructureResult)

    def test_validation_issues_collected(self, raw_doc):
        """Validation issues are collected."""
        extractor = CascadingExtractor()
        result = extractor.extract(raw_doc)
        assert isinstance(result.validation_issues, list)


class TestExtractStructureFunction:
    """Test convenience function."""

    def test_returns_sections(self, raw_doc):
        """extract_structure returns section list."""
        from scholardoc.extractors.cascading import extract_structure

        sections = extract_structure(raw_doc)
        assert isinstance(sections, list)
        for s in sections:
            assert isinstance(s, SectionSpan)


class TestIntegration:
    """Integration tests with real PDFs."""

    def test_full_extraction_pipeline(self, reader, heidegger_pdf):
        """Full pipeline from PDF to sections."""
        # Read PDF
        raw = reader.read(heidegger_pdf)
        assert raw.page_count == 8

        # Extract structure
        extractor = CascadingExtractor()
        result = extractor.extract(raw)

        # Verify result structure
        assert result.primary_source in ["pdf_outline", "heading_detection"]
        assert result.confidence >= 0.0
        assert len(result.processing_log) > 0

        # If sections found, verify they cover the document
        if result.sections:
            # First section should start early
            assert result.sections[0].start < len(raw.text) // 2

            # Last section should extend to end
            last_end = result.sections[-1].end
            assert last_end == len(raw.text)

    @pytest.mark.parametrize(
        "pdf_name",
        [
            "kant_critique_pages_64_65.pdf",
            "derrida_footnote_pages_120_125.pdf",
            "heidegger_pages_22-23_primary_footnote_test.pdf",
        ],
    )
    def test_extraction_on_multiple_pdfs(self, reader, pdf_name):
        """Extraction works on various PDF types."""
        pdf_path = SAMPLE_PDFS / pdf_name
        if not pdf_path.exists():
            pytest.skip(f"Sample PDF not found: {pdf_name}")

        raw = reader.read(pdf_path)
        extractor = CascadingExtractor()
        result = extractor.extract(raw)

        assert isinstance(result, StructureResult)
        assert result.confidence >= 0.0
        assert isinstance(result.sections, list)
