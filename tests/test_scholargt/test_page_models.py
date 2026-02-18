"""Tests for Region and PageGT models.

Covers region creation, multi-dimensional labeling, GTElement inheritance,
PageGT construction, schema version defaults, JSON round-trips, extra field
compatibility, and reading order validation.
"""

from datetime import UTC, datetime

import pytest

from scholargt.schema.base import BBox, VerificationRecord
from scholargt.schema.labels import SemanticType, SpatialLabel
from scholargt.schema.page import PageGT, PageQuality
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
            label=SpatialLabel.FOOTNOTE_AREA,
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
            semantic_labels=[SemanticType.FOOTNOTE],
        )
        # Spatial: text_block, Semantic: footnote -- independent
        assert r.label == SpatialLabel.TEXT_BLOCK
        assert r.semantic_labels == [SemanticType.FOOTNOTE]

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
            semantic_labels=[SemanticType.FOOTNOTE],
            reading_order_index=0,
        )
        json_str = r.model_dump_json()
        restored = Region.model_validate_json(json_str)
        assert restored.id == r.id
        assert restored.label == SpatialLabel.TEXT_BLOCK
        assert restored.bbox == r.bbox
        assert restored.text == "Sample text"
        assert restored.semantic_labels == [SemanticType.FOOTNOTE]
        assert restored.reading_order_index == 0

    def test_region_label_serializes_as_string_in_json(self):
        r = Region(
            id="r1",
            label=SpatialLabel.FOOTNOTE_AREA,
            bbox=BBox(x0=0.1, y0=0.7, x1=0.9, y1=0.9),
        )
        json_str = r.model_dump_json()
        assert '"footnote_area"' in json_str


# ---------- PageQuality tests ----------


class TestPageQuality:
    def test_create_page_quality(self):
        q = PageQuality(scan_quality="high", difficulty="medium")
        assert q.scan_quality == "high"
        assert q.difficulty == "medium"

    def test_page_quality_defaults_to_none(self):
        q = PageQuality()
        assert q.scan_quality is None
        assert q.difficulty is None


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
            label=SpatialLabel.FOOTNOTE_AREA,
            bbox=BBox(x0=0.1, y0=0.75, x1=0.9, y1=0.92),
        )
        page = PageGT(page_index=0, regions=[r1, r2], reading_order=["r1", "r2"])
        assert len(page.regions) == 2
        assert page.reading_order == ["r1", "r2"]

    def test_page_with_quality(self):
        page = PageGT(
            page_index=0,
            quality=PageQuality(scan_quality="high", difficulty="easy"),
        )
        assert page.quality is not None
        assert page.quality.scan_quality == "high"

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
            semantic_labels=[SemanticType.FOOTNOTE],
        )
        page = PageGT(
            page_index=150,
            page_label="127",
            dimensions={"width": 612.0, "height": 792.0},
            regions=[r],
            reading_order=["r1"],
            quality=PageQuality(scan_quality="high", difficulty="medium"),
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
        assert restored.regions[0].semantic_labels == [SemanticType.FOOTNOTE]
        assert restored.reading_order == ["r1"]
        assert restored.quality is not None
        assert restored.quality.scan_quality == "high"
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
