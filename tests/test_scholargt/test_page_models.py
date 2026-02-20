"""Tests for Region and PageGT models.

Covers region creation, multi-dimensional labeling, GTElement inheritance,
PageGT construction, schema version defaults, JSON round-trips, extra field
compatibility, reading order validation, and v2.0.0 additions: PageQuality hybrid,
PageDependency, SectionContextEntry, base_direction (SFP-2), register_id (SFP-1),
text_direction (SFP-2), INDEX_AREA (SFP-5).
"""

from datetime import UTC, datetime

import pytest

from scholargt.schema.base import BBox, VerificationRecord
from scholargt.schema.labels import SemanticType, SpatialLabel
from scholargt.schema.page import (
    PageDependency,
    PageGT,
    PageQuality,
    SectionContextEntry,
)
from scholargt.schema.spatial import Region
from scholargt.schema.version import SCHEMA_VERSION

# ---------- Region tests ----------


class TestRegion:
    def test_create_region_with_spatial_label(self):
        r = Region(
            id="r1",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.7),
        )
        assert r.label == SpatialLabel.TEXT_BLOCK
        assert r.bbox.x0 == 0.1
        assert r.text is None
        assert r.semantic_labels == []
        assert r.reading_order_index is None

    def test_region_with_text_and_anchors(self):
        r = Region(
            id="r1",
            label=SpatialLabel.NOTE_AREA,
            bbox=BBox(x0=0.1, y0=0.75, x1=0.9, y1=0.92),
            text="1. See the analysis of care in section 41.",
            text_anchors=["analysis of care"],
        )
        assert r.text == "1. See the analysis of care in section 41."
        assert r.text_anchors == ["analysis of care"]

    def test_multi_dimensional_labeling(self):
        """Spatial and semantic labels are independent dimensions."""
        r = Region(
            id="r1",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.7),
            semantic_labels=[SemanticType.NOTE],
        )
        # Spatial: text_block, Semantic: note -- independent
        assert r.label == SpatialLabel.TEXT_BLOCK
        assert r.semantic_labels == [SemanticType.NOTE]

    def test_region_with_multiple_semantic_labels(self):
        r = Region(
            id="r1",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.7),
            semantic_labels=[SemanticType.CITATION, SemanticType.CROSS_REFERENCE],
        )
        assert len(r.semantic_labels) == 2

    def test_region_inherits_gtelement_verification(self):
        """Region inherits GTElement's is_verified and agreement_score."""
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        r = Region(
            id="r1",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.7),
            verifications=[
                VerificationRecord(reviewer_id="human_1", timestamp=ts, confidence=0.95),
            ],
        )
        assert r.is_verified(threshold=0.9) is True
        assert r.agreement_score() == pytest.approx(0.95)

    def test_region_inherits_tags(self):
        r = Region(
            id="r1",
            label=SpatialLabel.FIGURE,
            bbox=BBox(x0=0.2, y0=0.3, x1=0.8, y1=0.6),
            tags=["heidegger", "diagram"],
        )
        assert r.tags == ["heidegger", "diagram"]

    def test_region_extra_fields_allowed(self):
        """Region inherits GTElement's extra='allow' for forward compat."""
        r = Region(
            id="r1",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.7),
            future_v2_field="new_data",
        )
        assert r.future_v2_field == "new_data"  # type: ignore[attr-defined]

    def test_region_json_round_trip(self):
        r = Region(
            id="r1",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.7),
            text="Sample text",
            semantic_labels=[SemanticType.NOTE],
            reading_order_index=0,
        )
        json_str = r.model_dump_json()
        restored = Region.model_validate_json(json_str)
        assert restored.id == r.id
        assert restored.label == SpatialLabel.TEXT_BLOCK
        assert restored.bbox == r.bbox
        assert restored.text == "Sample text"
        assert restored.semantic_labels == [SemanticType.NOTE]
        assert restored.reading_order_index == 0

    def test_region_label_serializes_as_string_in_json(self):
        r = Region(
            id="r1",
            label=SpatialLabel.NOTE_AREA,
            bbox=BBox(x0=0.1, y0=0.7, x1=0.9, y1=0.9),
        )
        json_str = r.model_dump_json()
        assert '"note_area"' in json_str

    def test_region_with_register_id(self):
        """SFP-1: Region belongs to a named register."""
        r = Region(
            id="r_rashi",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.0, y0=0.3, x1=0.4, y1=0.9),
            register_id="rashi",
            text_direction="rtl",
        )
        assert r.register_id == "rashi"
        assert r.text_direction == "rtl"

    def test_region_with_text_direction(self):
        """SFP-2: Explicit text direction on region."""
        r = Region(
            id="r_rtl",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.5),
            text_direction="rtl",
        )
        assert r.text_direction == "rtl"

    def test_region_with_bidi_direction(self):
        """SFP-2: Bidirectional text region."""
        r = Region(
            id="r_bidi",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.5),
            text_direction="bidi",
        )
        assert r.text_direction == "bidi"

    def test_region_index_area(self):
        """SFP-5: INDEX_AREA spatial label."""
        r = Region(
            id="r_index",
            label=SpatialLabel.INDEX_AREA,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.9),
        )
        assert r.label == SpatialLabel.INDEX_AREA

    def test_region_continuation_flags(self):
        """Cross-page continuation support."""
        r = Region(
            id="r_cont",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.5),
            is_continuation=True,
            continues_to_next=False,
        )
        assert r.is_continuation is True
        assert r.continues_to_next is False

    def test_region_children(self):
        """Sub-region hierarchy via self-referencing children."""
        child = Region(
            id="r_cell",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.5, y1=0.5),
        )
        parent = Region(
            id="r_table",
            label=SpatialLabel.TABLE,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.9),
            children=[child],
        )
        assert len(parent.children) == 1
        assert parent.children[0].id == "r_cell"


# ---------- PageQuality tests ----------


class TestPageQuality:
    def test_create_page_quality_hybrid(self):
        """v2.0.0 hybrid model with categorical + numeric + artifacts."""
        q = PageQuality(
            overall="high",
            is_scan=True,
            artifacts=["binding_shadow"],
            difficulty_factors=["dense_footnotes"],
            dpi_estimate=300,
            contrast_ratio=0.85,
            skew_angle=0.5,
            noise_level=0.1,
            ocr_confidence=0.92,
        )
        assert q.overall == "high"
        assert q.is_scan is True
        assert q.artifacts == ["binding_shadow"]
        assert q.difficulty_factors == ["dense_footnotes"]
        assert q.dpi_estimate == 300
        assert q.ocr_confidence == 0.92

    def test_page_quality_defaults_to_none(self):
        q = PageQuality()
        assert q.overall is None
        assert q.is_scan is None
        assert q.artifacts == []
        assert q.difficulty_factors == []
        assert q.dpi_estimate is None

    def test_page_quality_categorical_only(self):
        """Quick human annotation with just overall and is_scan."""
        q = PageQuality(overall="medium", is_scan=False)
        assert q.overall == "medium"
        assert q.is_scan is False

    def test_page_quality_artifacts_only(self):
        """Specific quality issues without overall assessment."""
        q = PageQuality(
            artifacts=["bleed_through", "foxing", "skew"],
            difficulty_factors=["mixed_language", "complex_typography"],
        )
        assert len(q.artifacts) == 3
        assert len(q.difficulty_factors) == 2


# ---------- PageDependency tests ----------


class TestPageDependency:
    def test_create_page_dependency_defaults(self):
        pd = PageDependency()
        assert pd.continues_from_previous is False
        assert pd.continues_to_next is False
        assert pd.unresolved_markers == []
        assert pd.orphan_continuations == []

    def test_create_page_dependency_all_fields(self):
        pd = PageDependency(
            continues_from_previous=True,
            continues_to_next=False,
            unresolved_markers=["fn_3", "fn_4"],
            orphan_continuations=["fn_2_cont"],
        )
        assert pd.continues_from_previous is True
        assert pd.continues_to_next is False
        assert pd.unresolved_markers == ["fn_3", "fn_4"]
        assert pd.orphan_continuations == ["fn_2_cont"]

    def test_page_dependency_json_round_trip(self):
        pd = PageDependency(
            continues_from_previous=True,
            unresolved_markers=["fn_5"],
        )
        json_str = pd.model_dump_json()
        restored = PageDependency.model_validate_json(json_str)
        assert restored.continues_from_previous is True
        assert restored.unresolved_markers == ["fn_5"]


# ---------- SectionContextEntry tests ----------


class TestSectionContextEntry:
    def test_create_section_context_entry(self):
        sce = SectionContextEntry(
            section_id="sec_div1",
            title="Division One",
            level=0,
            starts_on_this_page=True,
            ends_on_this_page=False,
        )
        assert sce.section_id == "sec_div1"
        assert sce.title == "Division One"
        assert sce.level == 0
        assert sce.starts_on_this_page is True
        assert sce.ends_on_this_page is False

    def test_section_context_defaults(self):
        sce = SectionContextEntry(
            section_id="sec1",
            title="Introduction",
            level=0,
        )
        assert sce.starts_on_this_page is False
        assert sce.ends_on_this_page is False

    def test_section_context_json_round_trip(self):
        sce = SectionContextEntry(
            section_id="sec1",
            title="Chapter 1",
            level=1,
            starts_on_this_page=True,
        )
        json_str = sce.model_dump_json()
        restored = SectionContextEntry.model_validate_json(json_str)
        assert restored.section_id == "sec1"
        assert restored.starts_on_this_page is True


# ---------- PageGT tests ----------


class TestPageGT:
    def test_create_empty_page(self):
        page = PageGT(page_index=0)
        assert page.page_index == 0
        assert page.regions == []
        assert page.reading_order == []
        assert page.quality is None
        assert page.verifications == []

    def test_schema_version_defaults(self):
        page = PageGT(page_index=0)
        assert page.schema_version == SCHEMA_VERSION

    def test_page_with_page_label(self):
        page = PageGT(page_index=150, page_label="127")
        assert page.page_label == "127"

    def test_page_with_dimensions(self):
        page = PageGT(page_index=0, dimensions={"width": 612.0, "height": 792.0})
        assert page.dimensions == {"width": 612.0, "height": 792.0}

    def test_page_with_regions_and_reading_order(self):
        r1 = Region(
            id="r1",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.7),
        )
        r2 = Region(
            id="r2",
            label=SpatialLabel.NOTE_AREA,
            bbox=BBox(x0=0.1, y0=0.75, x1=0.9, y1=0.92),
        )
        page = PageGT(page_index=0, regions=[r1, r2], reading_order=["r1", "r2"])
        assert len(page.regions) == 2
        assert page.reading_order == ["r1", "r2"]

    def test_page_with_quality(self):
        page = PageGT(
            page_index=0,
            quality=PageQuality(overall="high", is_scan=True, artifacts=["binding_shadow"]),
        )
        assert page.quality is not None
        assert page.quality.overall == "high"

    def test_page_with_verifications(self):
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        page = PageGT(
            page_index=0,
            verifications=[
                VerificationRecord(
                    reviewer_id="annotator_1",
                    timestamp=ts,
                    confidence=0.95,
                    notes="Layout verified",
                ),
            ],
        )
        assert len(page.verifications) == 1
        assert page.verifications[0].confidence == 0.95

    def test_page_extra_fields_allowed(self):
        """PageGT accepts unknown fields for forward compat."""
        page = PageGT(page_index=0, custom_metadata="v2_feature")
        assert page.custom_metadata == "v2_feature"  # type: ignore[attr-defined]

    def test_page_with_section_context(self):
        """v2.0.0: section_context makes pages self-describing."""
        page = PageGT(
            page_index=65,
            section_context=[
                SectionContextEntry(
                    section_id="sec_div1",
                    title="Division One",
                    level=0,
                    starts_on_this_page=True,
                ),
                SectionContextEntry(
                    section_id="sec_ch1",
                    title="Chapter 1",
                    level=1,
                    starts_on_this_page=True,
                ),
            ],
        )
        assert len(page.section_context) == 2
        assert page.section_context[0].section_id == "sec_div1"

    def test_page_with_page_dependency(self):
        """v2.0.0: page_dependency for cross-page relationships."""
        page = PageGT(
            page_index=22,
            page_dependency=PageDependency(
                continues_from_previous=True,
                continues_to_next=False,
                orphan_continuations=["fn_1_cont"],
            ),
        )
        assert page.page_dependency is not None
        assert page.page_dependency.continues_from_previous is True

    def test_page_with_base_direction(self):
        """SFP-2: base_direction for default text direction."""
        page = PageGT(page_index=0, base_direction="rtl")
        assert page.base_direction == "rtl"

    def test_page_base_direction_ltr(self):
        page = PageGT(page_index=0, base_direction="ltr")
        assert page.base_direction == "ltr"

    def test_reading_order_valid_ids_no_warning(self):
        """Valid reading_order does not emit a warning."""
        r1 = Region(
            id="r1",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.7),
        )
        with pytest.warns(match="never") if False else _no_warnings():
            PageGT(page_index=0, regions=[r1], reading_order=["r1"])

    def test_reading_order_unknown_ids_warns(self):
        """reading_order referencing non-existent region IDs emits a warning."""
        r1 = Region(
            id="r1",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.7),
        )
        with pytest.warns(UserWarning, match="unknown region IDs.*r_missing"):
            PageGT(page_index=0, regions=[r1], reading_order=["r1", "r_missing"])

    def test_reading_order_empty_no_warning(self):
        """Empty reading_order should not warn."""
        r1 = Region(
            id="r1",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.7),
        )
        # Should not raise
        PageGT(page_index=0, regions=[r1], reading_order=[])

    def test_page_json_round_trip(self):
        """Full PageGT round-trip: model_dump_json -> model_validate_json."""
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        r = Region(
            id="r1",
            label=SpatialLabel.TEXT_BLOCK,
            bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.7),
            semantic_labels=[SemanticType.NOTE],
        )
        page = PageGT(
            page_index=150,
            page_label="127",
            dimensions={"width": 612.0, "height": 792.0},
            regions=[r],
            reading_order=["r1"],
            quality=PageQuality(overall="high", is_scan=True),
            base_direction="ltr",
            section_context=[
                SectionContextEntry(
                    section_id="sec1", title="Ch 1", level=0,
                    starts_on_this_page=True,
                ),
            ],
            page_dependency=PageDependency(continues_from_previous=False),
            verifications=[
                VerificationRecord(reviewer_id="ann_1", timestamp=ts, confidence=0.9),
            ],
        )
        json_str = page.model_dump_json(indent=2)
        restored = PageGT.model_validate_json(json_str)

        assert restored.schema_version == SCHEMA_VERSION
        assert restored.page_index == 150
        assert restored.page_label == "127"
        assert restored.dimensions == {"width": 612.0, "height": 792.0}
        assert len(restored.regions) == 1
        assert restored.regions[0].label == SpatialLabel.TEXT_BLOCK
        assert restored.regions[0].semantic_labels == [SemanticType.NOTE]
        assert restored.reading_order == ["r1"]
        assert restored.quality is not None
        assert restored.quality.overall == "high"
        assert restored.base_direction == "ltr"
        assert len(restored.section_context) == 1
        assert restored.page_dependency is not None
        assert len(restored.verifications) == 1

    def test_page_extra_fields_round_trip(self):
        """Extra fields survive JSON round-trip."""
        page = PageGT(page_index=0, annotation_tool="cogito_v2")
        json_str = page.model_dump_json()
        restored = PageGT.model_validate_json(json_str)
        assert restored.annotation_tool == "cogito_v2"  # type: ignore[attr-defined]


# ---------- Helpers ----------


class _no_warnings:
    """Context manager that asserts no warnings are emitted."""

    def __enter__(self):
        import warnings as w

        self._catcher = w.catch_warnings(record=True)
        self._warnings = self._catcher.__enter__()
        return self

    def __exit__(self, *args):
        self._catcher.__exit__(*args)
        user_warnings = [x for x in self._warnings if issubclass(x.category, UserWarning)]
        if user_warnings:
            msg = f"Unexpected warnings: {[str(w.message) for w in user_warnings]}"
            raise AssertionError(msg)
