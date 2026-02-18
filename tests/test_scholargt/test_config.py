"""Tests for ScholarGT configuration system.

Tests profile loading, layered YAML merging, validation config,
project overrides, and cross-validation with label enums.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from scholargt.config.loader import get_profiles_dir, list_profiles, load_profile
from scholargt.config.models import GTProfile, ValidationConfig
from scholargt.schema.labels import (
    DocumentType,
    FormattingType,
    SemanticType,
    SpatialLabel,
)

# ---------------------------------------------------------------------------
# Base profile tests
# ---------------------------------------------------------------------------


class TestBaseProfile:
    """Tests for the base profile defaults."""

    def test_base_profile_loads(self):
        profile = load_profile("base")
        assert profile.name == "base"

    def test_base_has_6_spatial_labels(self):
        profile = load_profile("base")
        assert len(profile.spatial_labels) == 6

    def test_base_has_2_semantic_types(self):
        profile = load_profile("base")
        assert len(profile.semantic_types) == 2

    def test_base_has_no_formatting_types(self):
        profile = load_profile("base")
        assert len(profile.formatting_types) == 0

    def test_base_has_1_document_type(self):
        profile = load_profile("base")
        assert len(profile.document_types) == 1
        assert "metadata" in profile.document_types

    def test_base_validation_defaults(self):
        profile = load_profile("base")
        assert profile.validation.require_bbox is True
        assert profile.validation.require_text is False
        assert profile.validation.require_reading_order is False
        assert profile.validation.confidence_threshold == 0.8

    def test_base_spatial_labels_content(self):
        profile = load_profile("base")
        expected = {
            "text_block",
            "footnote_area",
            "page_header",
            "page_footer",
            "page_number",
            "section_header",
        }
        assert profile.spatial_labels == expected

    def test_base_semantic_types_content(self):
        profile = load_profile("base")
        assert profile.semantic_types == {"footnote", "citation"}


# ---------------------------------------------------------------------------
# Extraction-eval profile tests
# ---------------------------------------------------------------------------


class TestExtractionEvalProfile:
    """Tests for the extraction-eval profile."""

    def test_extraction_eval_loads(self):
        profile = load_profile("extraction-eval")
        assert profile.name == "extraction-eval"

    def test_extraction_eval_requires_text(self):
        profile = load_profile("extraction-eval")
        assert profile.validation.require_text is True

    def test_extraction_eval_requires_reading_order(self):
        profile = load_profile("extraction-eval")
        assert profile.validation.require_reading_order is True

    def test_extraction_eval_has_8_spatial_labels(self):
        profile = load_profile("extraction-eval")
        assert len(profile.spatial_labels) == 8

    def test_extraction_eval_includes_text_focused_labels(self):
        profile = load_profile("extraction-eval")
        assert "endnote_area" in profile.spatial_labels
        assert "block_quote" in profile.spatial_labels

    def test_extraction_eval_has_5_semantic_types(self):
        profile = load_profile("extraction-eval")
        assert len(profile.semantic_types) == 5
        assert "endnote" in profile.semantic_types
        assert "section" in profile.semantic_types
        assert "bibliography_entry" in profile.semantic_types

    def test_extraction_eval_inherits_base_bbox(self):
        """Extraction-eval inherits require_bbox=true from base."""
        profile = load_profile("extraction-eval")
        assert profile.validation.require_bbox is True


# ---------------------------------------------------------------------------
# Layout-annotation profile tests
# ---------------------------------------------------------------------------


class TestLayoutAnnotationProfile:
    """Tests for the layout-annotation profile."""

    def test_layout_annotation_loads(self):
        profile = load_profile("layout-annotation")
        assert profile.name == "layout-annotation"

    def test_layout_has_all_17_spatial_labels(self):
        profile = load_profile("layout-annotation")
        assert len(profile.spatial_labels) == 17

    def test_layout_has_empty_semantic_types(self):
        profile = load_profile("layout-annotation")
        assert len(profile.semantic_types) == 0

    def test_layout_requires_bbox(self):
        profile = load_profile("layout-annotation")
        assert profile.validation.require_bbox is True

    def test_layout_requires_reading_order(self):
        profile = load_profile("layout-annotation")
        assert profile.validation.require_reading_order is True

    def test_layout_does_not_require_text(self):
        profile = load_profile("layout-annotation")
        assert profile.validation.require_text is False


# ---------------------------------------------------------------------------
# Full-scholarly profile tests
# ---------------------------------------------------------------------------


class TestFullScholarlyProfile:
    """Tests for the full-scholarly profile."""

    def test_full_scholarly_loads(self):
        profile = load_profile("full-scholarly")
        assert profile.name == "full-scholarly"

    def test_full_has_all_17_spatial_labels(self):
        profile = load_profile("full-scholarly")
        assert len(profile.spatial_labels) == 17

    def test_full_has_all_9_semantic_types(self):
        profile = load_profile("full-scholarly")
        assert len(profile.semantic_types) == 9
        assert "sous_rature" in profile.semantic_types

    def test_full_has_all_6_formatting_types(self):
        profile = load_profile("full-scholarly")
        assert len(profile.formatting_types) == 6
        assert "superscript" in profile.formatting_types

    def test_full_has_all_5_document_types(self):
        profile = load_profile("full-scholarly")
        assert len(profile.document_types) == 5

    def test_full_confidence_threshold_09(self):
        profile = load_profile("full-scholarly")
        assert profile.validation.confidence_threshold == 0.9

    def test_full_requires_everything(self):
        profile = load_profile("full-scholarly")
        assert profile.validation.require_reading_order is True
        assert profile.validation.require_text is True
        assert profile.validation.require_bbox is True


# ---------------------------------------------------------------------------
# Cross-validation: YAML labels match label enums
# ---------------------------------------------------------------------------


class TestLabelEnumCrossValidation:
    """Verify all label strings in YAML profiles match label enum values."""

    def test_all_spatial_labels_match_enum(self):
        """Every spatial label in every profile must be a valid SpatialLabel value."""
        valid_values = {e.value for e in SpatialLabel}
        for profile_name in list_profiles():
            profile = load_profile(profile_name)
            for label in profile.spatial_labels:
                assert label in valid_values, (
                    f"Profile '{profile_name}' has invalid spatial label '{label}'. "
                    f"Valid values: {sorted(valid_values)}"
                )

    def test_all_semantic_types_match_enum(self):
        """Every semantic type in every profile must be a valid SemanticType value."""
        valid_values = {e.value for e in SemanticType}
        for profile_name in list_profiles():
            profile = load_profile(profile_name)
            for label in profile.semantic_types:
                assert label in valid_values, (
                    f"Profile '{profile_name}' has invalid semantic type '{label}'. "
                    f"Valid values: {sorted(valid_values)}"
                )

    def test_all_formatting_types_match_enum(self):
        """Every formatting type in every profile must be a valid FormattingType value."""
        valid_values = {e.value for e in FormattingType}
        for profile_name in list_profiles():
            profile = load_profile(profile_name)
            for label in profile.formatting_types:
                assert label in valid_values, (
                    f"Profile '{profile_name}' has invalid formatting type '{label}'. "
                    f"Valid values: {sorted(valid_values)}"
                )

    def test_all_document_types_match_enum(self):
        """Every document type in every profile must be a valid DocumentType value."""
        valid_values = {e.value for e in DocumentType}
        for profile_name in list_profiles():
            profile = load_profile(profile_name)
            for label in profile.document_types:
                assert label in valid_values, (
                    f"Profile '{profile_name}' has invalid document type '{label}'. "
                    f"Valid values: {sorted(valid_values)}"
                )


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for error cases in config loading."""

    def test_nonexistent_profile_raises(self):
        with pytest.raises(FileNotFoundError):
            load_profile("nonexistent")

    def test_nonexistent_project_config_raises(self):
        with pytest.raises(FileNotFoundError):
            load_profile("base", project_config_path=Path("/does/not/exist.yaml"))


# ---------------------------------------------------------------------------
# Project config overrides
# ---------------------------------------------------------------------------


class TestProjectConfigOverrides:
    """Tests for project-level config overrides."""

    def test_additional_semantic_types(self):
        """Project config adds custom semantic types."""
        project_yaml = {
            "profile": "base",
            "additional_semantic_types": ["custom_philosophy_label"],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(project_yaml, f)
            project_path = Path(f.name)

        try:
            profile = load_profile("base", project_config_path=project_path)
            assert "custom_philosophy_label" in profile.semantic_types
            # Original types preserved
            assert "footnote" in profile.semantic_types
            assert "citation" in profile.semantic_types
        finally:
            project_path.unlink()

    def test_disabled_labels(self):
        """Project config disables specific labels."""
        project_yaml = {
            "profile": "base",
            "disabled_labels": ["page_header", "page_footer"],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(project_yaml, f)
            project_path = Path(f.name)

        try:
            profile = load_profile("base", project_config_path=project_path)
            assert "page_header" not in profile.spatial_labels
            assert "page_footer" not in profile.spatial_labels
            # Other labels preserved
            assert "text_block" in profile.spatial_labels
        finally:
            project_path.unlink()

    def test_validation_override(self):
        """Project config overrides validation settings."""
        project_yaml = {
            "profile": "base",
            "validation": {"confidence_threshold": 0.85},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(project_yaml, f)
            project_path = Path(f.name)

        try:
            profile = load_profile("base", project_config_path=project_path)
            assert profile.validation.confidence_threshold == 0.85
            # Other validation settings preserved from base
            assert profile.validation.require_bbox is True
        finally:
            project_path.unlink()

    def test_layering_base_profile_project(self):
        """Full layering test: base -> full-scholarly -> project config."""
        project_yaml = {
            "profile": "full-scholarly",
            "additional_semantic_types": ["custom_label"],
            "disabled_labels": ["formula"],
            "validation": {"confidence_threshold": 0.95},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(project_yaml, f)
            project_path = Path(f.name)

        try:
            profile = load_profile("full-scholarly", project_config_path=project_path)
            # Custom label added
            assert "custom_label" in profile.semantic_types
            # formula disabled
            assert "formula" not in profile.spatial_labels
            # Validation overridden
            assert profile.validation.confidence_threshold == 0.95
            # Other full-scholarly labels preserved
            assert "sous_rature" in profile.semantic_types
            assert "text_block" in profile.spatial_labels
        finally:
            project_path.unlink()


# ---------------------------------------------------------------------------
# is_label_enabled tests
# ---------------------------------------------------------------------------


class TestIsLabelEnabled:
    """Tests for GTProfile.is_label_enabled()."""

    def test_enabled_spatial_label(self):
        profile = load_profile("base")
        assert profile.is_label_enabled("spatial", "text_block") is True

    def test_disabled_spatial_label(self):
        profile = load_profile("base")
        assert profile.is_label_enabled("spatial", "formula") is False

    def test_enabled_semantic_type(self):
        profile = load_profile("base")
        assert profile.is_label_enabled("semantic", "footnote") is True

    def test_disabled_semantic_type(self):
        profile = load_profile("base")
        assert profile.is_label_enabled("semantic", "sous_rature") is False

    def test_empty_formatting_category(self):
        profile = load_profile("base")
        assert profile.is_label_enabled("formatting", "bold") is False

    def test_full_scholarly_has_formatting(self):
        profile = load_profile("full-scholarly")
        assert profile.is_label_enabled("formatting", "bold") is True

    def test_invalid_category_returns_false(self):
        profile = load_profile("base")
        assert profile.is_label_enabled("nonexistent", "text_block") is False


# ---------------------------------------------------------------------------
# enabled_labels and round-trip tests
# ---------------------------------------------------------------------------


class TestEnabledLabelsAndRoundTrip:
    """Tests for enabled_labels() and model serialization round-trip."""

    def test_enabled_labels_returns_all_categories(self):
        profile = load_profile("base")
        labels = profile.enabled_labels()
        assert set(labels.keys()) == {"spatial", "semantic", "formatting", "document"}

    def test_enabled_labels_spatial_matches_profile(self):
        profile = load_profile("base")
        labels = profile.enabled_labels()
        assert labels["spatial"] == profile.spatial_labels

    def test_round_trip_preserves_label_sets(self):
        """GTProfile model_dump() -> model_validate() preserves label sets."""
        profile = load_profile("full-scholarly")
        dumped = profile.model_dump()
        restored = GTProfile.model_validate(dumped)
        assert restored.spatial_labels == profile.spatial_labels
        assert restored.semantic_types == profile.semantic_types
        assert restored.formatting_types == profile.formatting_types
        assert restored.document_types == profile.document_types
        assert restored.validation.confidence_threshold == profile.validation.confidence_threshold


# ---------------------------------------------------------------------------
# list_profiles tests
# ---------------------------------------------------------------------------


class TestListProfiles:
    """Tests for list_profiles()."""

    def test_list_profiles_returns_all_four(self):
        profiles = list_profiles()
        assert "base" in profiles
        assert "extraction-eval" in profiles
        assert "layout-annotation" in profiles
        assert "full-scholarly" in profiles

    def test_list_profiles_returns_at_least_four(self):
        profiles = list_profiles()
        assert len(profiles) >= 4

    def test_list_profiles_is_sorted(self):
        profiles = list_profiles()
        assert profiles == sorted(profiles)


# ---------------------------------------------------------------------------
# GTProfile model tests
# ---------------------------------------------------------------------------


class TestGTProfileModel:
    """Tests for GTProfile model behavior."""

    def test_default_profile_is_base(self):
        profile = GTProfile()
        assert profile.name == "base"

    def test_extra_fields_allowed(self):
        """GTProfile allows extra fields for forward compatibility."""
        profile = GTProfile(custom_field="custom_value")
        assert profile.custom_field == "custom_value"  # type: ignore[attr-defined]

    def test_validation_config_defaults(self):
        config = ValidationConfig()
        assert config.require_reading_order is False
        assert config.require_text is False
        assert config.require_bbox is True
        assert config.confidence_threshold == 0.8

    def test_validation_config_threshold_bounds(self):
        """Confidence threshold must be between 0.0 and 1.0."""
        with pytest.raises(Exception):  # noqa: B017
            ValidationConfig(confidence_threshold=1.5)

        with pytest.raises(Exception):  # noqa: B017
            ValidationConfig(confidence_threshold=-0.1)

    def test_profiles_dir_exists(self):
        profiles_dir = get_profiles_dir()
        assert profiles_dir.is_dir()
