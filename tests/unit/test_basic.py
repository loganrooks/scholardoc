"""
Basic tests for ScholarDoc package structure.

These tests verify the public API is importable and
basic configuration works correctly.
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

    def test_import_core_types(self):
        """Can import core data types."""
        from scholardoc import (
            ChunkStrategy,
            DocumentType,
        )

        assert DocumentType.BOOK.value == "book"
        assert ChunkStrategy.SEMANTIC.value == "semantic"

    def test_import_annotation_types(self):
        """Can import annotation types."""
        from scholardoc import (
            FootnoteRef,
        )

        fn = FootnoteRef(position=10, marker="1", target_id="fn1")
        assert fn.position == 10

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
