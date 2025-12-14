"""
Basic tests for ScholarDoc package structure.

These tests verify the public API is importable and
basic data models work correctly.
"""

import pytest


class TestImports:
    """Test that the public API is importable."""

    def test_import_package(self):
        """Can import the main package."""
        import scholardoc

        assert scholardoc.__version__ == "0.1.0"

    def test_import_convert_function(self):
        """Can import the main convert function."""
        from scholardoc import convert

        assert callable(convert)

    def test_import_config(self):
        """Can import configuration class."""
        from scholardoc import ConversionConfig

        config = ConversionConfig()
        assert config.include_page_markers is True

    def test_import_models(self):
        """Can import data models."""
        from scholardoc import DocumentMetadata, DocumentStructure, ScholarDocument

        assert DocumentMetadata is not None
        assert DocumentStructure is not None
        assert ScholarDocument is not None

    def test_import_exceptions(self):
        """Can import exception classes."""
        from scholardoc import (
            ConfigurationError,
            ExtractionError,
            ScholarDocError,
            UnsupportedFormatError,
        )

        # Verify inheritance
        assert issubclass(UnsupportedFormatError, ScholarDocError)
        assert issubclass(ExtractionError, ScholarDocError)
        assert issubclass(ConfigurationError, ScholarDocError)


class TestConversionConfig:
    """Test ConversionConfig behavior."""

    def test_default_config(self):
        """Default config has expected values."""
        from scholardoc import ConversionConfig

        config = ConversionConfig()

        assert config.include_metadata_frontmatter is True
        assert config.include_page_markers is True
        assert config.page_marker_style == "comment"
        assert config.detect_headings is True
        assert config.on_extraction_error == "warn"

    def test_custom_config(self):
        """Can create config with custom values."""
        from scholardoc import ConversionConfig

        config = ConversionConfig(
            include_page_markers=False,
            page_marker_style="heading",
            on_extraction_error="raise",
        )

        assert config.include_page_markers is False
        assert config.page_marker_style == "heading"
        assert config.on_extraction_error == "raise"

    def test_invalid_page_marker_style(self):
        """Invalid page_marker_style raises error."""
        from scholardoc import ConversionConfig

        with pytest.raises(ValueError, match="page_marker_style"):
            ConversionConfig(page_marker_style="invalid")

    def test_invalid_heading_strategy(self):
        """Invalid heading_detection_strategy raises error."""
        from scholardoc import ConversionConfig

        with pytest.raises(ValueError, match="heading_detection_strategy"):
            ConversionConfig(heading_detection_strategy="invalid")


class TestDocumentMetadata:
    """Test DocumentMetadata model."""

    def test_default_metadata(self):
        """Can create metadata with defaults."""
        from scholardoc.models import DocumentMetadata

        meta = DocumentMetadata()

        assert meta.title is None
        assert meta.authors == []
        assert meta.page_count == 0

    def test_metadata_with_values(self):
        """Can create metadata with values."""
        from scholardoc.models import DocumentMetadata

        meta = DocumentMetadata(
            title="Critique of Pure Reason",
            authors=["Immanuel Kant"],
            page_count=856,
        )

        assert meta.title == "Critique of Pure Reason"
        assert meta.authors == ["Immanuel Kant"]
        assert meta.page_count == 856


class TestScholarDocument:
    """Test ScholarDocument model."""

    def test_document_creation(self):
        """Can create a ScholarDocument."""
        from scholardoc.models import DocumentMetadata, DocumentStructure, ScholarDocument

        doc = ScholarDocument(
            markdown="# Test\n\nContent here.",
            metadata=DocumentMetadata(title="Test"),
            structure=DocumentStructure(),
            source_path="/path/to/doc.pdf",
        )

        assert doc.markdown == "# Test\n\nContent here."
        assert doc.metadata.title == "Test"
        assert doc.warnings == []

    def test_document_to_dict(self):
        """Can convert document to dictionary."""
        from scholardoc.models import DocumentMetadata, DocumentStructure, ScholarDocument

        doc = ScholarDocument(
            markdown="# Test",
            metadata=DocumentMetadata(title="Test", page_count=10),
            structure=DocumentStructure(),
            source_path="/path/to/doc.pdf",
            warnings=["Some warning"],
        )

        d = doc.to_dict()

        assert d["markdown"] == "# Test"
        assert d["metadata"]["title"] == "Test"
        assert d["metadata"]["page_count"] == 10
        assert d["warnings"] == ["Some warning"]

    def test_document_save(self, tmp_path):
        """Can save document to file."""
        from scholardoc.models import DocumentMetadata, DocumentStructure, ScholarDocument

        doc = ScholarDocument(
            markdown="# Test\n\nContent.",
            metadata=DocumentMetadata(),
            structure=DocumentStructure(),
            source_path="/path/to/doc.pdf",
        )

        output_path = tmp_path / "output.md"
        doc.save(output_path)

        assert output_path.exists()
        assert output_path.read_text() == "# Test\n\nContent."


class TestSupportedFormats:
    """Test format support."""

    def test_supported_formats(self):
        """supported_formats returns current formats."""
        from scholardoc import supported_formats

        formats = supported_formats()

        assert "pdf" in formats
        # Phase 1: PDF only
        assert len(formats) == 1


class TestNotImplemented:
    """Test that unimplemented features raise NotImplementedError."""

    def test_convert_not_implemented(self):
        """convert() raises NotImplementedError in Phase 1."""
        from scholardoc import convert

        with pytest.raises(NotImplementedError, match="Phase 1"):
            convert("test.pdf")

    def test_convert_batch_not_implemented(self):
        """convert_batch() raises NotImplementedError in Phase 1."""
        from scholardoc import convert_batch

        with pytest.raises(NotImplementedError, match="Phase 1"):
            list(convert_batch(["test.pdf"]))

    def test_detect_format_not_implemented(self):
        """detect_format() raises NotImplementedError in Phase 1."""
        from scholardoc import detect_format

        with pytest.raises(NotImplementedError, match="Phase 1"):
            detect_format("test.pdf")
