"""Tests for document profiles.

DocumentProfile enables document-type-specific structure extraction settings.
"""

import pytest

from scholardoc.extractors.profiles import (
    ARTICLE_PROFILE,
    BOOK_PROFILE,
    DEFAULT_PROFILE,
    ESSAY_PROFILE,
    PROFILES,
    REPORT_PROFILE,
    DocumentProfile,
    get_profile,
)


class TestDocumentProfile:
    """Test DocumentProfile dataclass."""

    def test_profile_creation(self):
        """Can create a profile with required fields."""
        profile = DocumentProfile(
            name="test",
            description="A test profile",
        )
        assert profile.name == "test"
        assert profile.description == "A test profile"

    def test_default_values(self):
        """Profile has sensible defaults."""
        profile = DocumentProfile(name="test", description="test")

        assert profile.use_outline is True
        assert profile.use_heading_detection is True
        assert profile.use_toc_enrichment is True
        assert profile.min_confidence == 0.5
        assert profile.title_similarity_threshold == 0.8
        assert "overlap" in profile.validators

    def test_custom_values(self):
        """Can override default values."""
        profile = DocumentProfile(
            name="custom",
            description="Custom profile",
            use_outline=False,
            use_toc_enrichment=False,
            min_confidence=0.3,
            validators=("overlap",),
        )

        assert profile.use_outline is False
        assert profile.use_toc_enrichment is False
        assert profile.min_confidence == 0.3
        assert profile.validators == ("overlap",)


class TestStandardProfiles:
    """Test standard profile constants."""

    def test_book_profile_exists(self):
        """BOOK_PROFILE is defined."""
        assert BOOK_PROFILE is not None
        assert BOOK_PROFILE.name == "book"

    def test_article_profile_exists(self):
        """ARTICLE_PROFILE is defined."""
        assert ARTICLE_PROFILE is not None
        assert ARTICLE_PROFILE.name == "article"

    def test_essay_profile_exists(self):
        """ESSAY_PROFILE is defined."""
        assert ESSAY_PROFILE is not None
        assert ESSAY_PROFILE.name == "essay"

    def test_report_profile_exists(self):
        """REPORT_PROFILE is defined."""
        assert REPORT_PROFILE is not None
        assert REPORT_PROFILE.name == "report"

    def test_default_profile_exists(self):
        """DEFAULT_PROFILE is defined."""
        assert DEFAULT_PROFILE is not None
        assert DEFAULT_PROFILE.name == "generic"

    def test_profiles_dict_contains_all(self):
        """PROFILES dict contains all standard profiles."""
        assert "book" in PROFILES
        assert "article" in PROFILES
        assert "essay" in PROFILES
        assert "report" in PROFILES
        assert "generic" in PROFILES

    def test_book_profile_configuration(self):
        """Book profile has appropriate settings."""
        assert BOOK_PROFILE.use_outline is True
        assert BOOK_PROFILE.use_heading_detection is True
        assert BOOK_PROFILE.use_toc_enrichment is True
        assert BOOK_PROFILE.min_confidence == 0.5
        assert "overlap" in BOOK_PROFILE.validators
        assert "hierarchy" in BOOK_PROFILE.validators

    def test_article_profile_configuration(self):
        """Article profile has appropriate settings."""
        assert ARTICLE_PROFILE.use_toc_enrichment is False  # Articles rarely have ToC
        assert ARTICLE_PROFILE.min_confidence == 0.4  # More lenient

    def test_essay_profile_configuration(self):
        """Essay profile has appropriate settings."""
        assert ESSAY_PROFILE.use_toc_enrichment is False
        assert ESSAY_PROFILE.min_confidence == 0.4


class TestGetProfile:
    """Test get_profile() function."""

    def test_returns_profile_for_book_type(self, monkeypatch):
        """get_profile returns BOOK_PROFILE for book document type."""
        from unittest.mock import MagicMock

        monkeypatch.setattr(
            "scholardoc.extractors.profiles.estimate_document_type",
            lambda _: "book",
        )
        doc = MagicMock()

        profile = get_profile(doc)

        assert profile.name == "book"
        assert profile is BOOK_PROFILE

    def test_returns_profile_for_article_type(self, monkeypatch):
        """get_profile returns ARTICLE_PROFILE for article document type."""
        from unittest.mock import MagicMock

        monkeypatch.setattr(
            "scholardoc.extractors.profiles.estimate_document_type",
            lambda _: "article",
        )
        doc = MagicMock()

        profile = get_profile(doc)

        assert profile.name == "article"
        assert profile is ARTICLE_PROFILE

    def test_returns_profile_for_essay_type(self, monkeypatch):
        """get_profile returns ESSAY_PROFILE for essay document type."""
        from unittest.mock import MagicMock

        monkeypatch.setattr(
            "scholardoc.extractors.profiles.estimate_document_type",
            lambda _: "essay",
        )
        doc = MagicMock()

        profile = get_profile(doc)

        assert profile.name == "essay"
        assert profile is ESSAY_PROFILE

    def test_returns_profile_for_report_type(self, monkeypatch):
        """get_profile returns REPORT_PROFILE for report document type."""
        from unittest.mock import MagicMock

        monkeypatch.setattr(
            "scholardoc.extractors.profiles.estimate_document_type",
            lambda _: "report",
        )
        doc = MagicMock()

        profile = get_profile(doc)

        assert profile.name == "report"
        assert profile is REPORT_PROFILE

    def test_returns_default_profile_for_generic(self, monkeypatch):
        """get_profile returns DEFAULT_PROFILE for generic document type."""
        from unittest.mock import MagicMock

        monkeypatch.setattr(
            "scholardoc.extractors.profiles.estimate_document_type",
            lambda _: "generic",
        )
        doc = MagicMock()

        profile = get_profile(doc)

        assert profile.name == "generic"
        assert profile is DEFAULT_PROFILE

    def test_returns_default_for_unknown_type(self, monkeypatch):
        """get_profile returns DEFAULT_PROFILE for unknown document type."""
        from unittest.mock import MagicMock

        monkeypatch.setattr(
            "scholardoc.extractors.profiles.estimate_document_type",
            lambda _: "unknown_type",
        )
        doc = MagicMock()

        profile = get_profile(doc)

        assert profile.name == "generic"


class TestProfileImmutability:
    """Test that profile constants are safe to use."""

    def test_profiles_are_frozen(self):
        """Standard profiles should be frozen (immutable)."""
        from dataclasses import FrozenInstanceError

        # Try to modify - should raise FrozenInstanceError
        with pytest.raises(FrozenInstanceError):
            BOOK_PROFILE.name = "modified"
