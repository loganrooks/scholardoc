"""Tests for scholargt base schema models: BBox, VerificationRecord, GTElement.

Covers creation, validation, helper methods, extra field compatibility,
JSON round-trip serialization, and label enum serialization.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from scholargt.schema.base import BBox, GTElement, VerificationRecord
from scholargt.schema.labels import (
    CitationType,
    Difficulty,
    DocumentType,
    FormattingType,
    MarginalRefType,
    ScanQuality,
    SemanticType,
    SpatialLabel,
)

# ---------- BBox tests ----------


class TestBBox:
    def test_create_valid_bbox(self):
        bbox = BBox(x0=0.1, y0=0.2, x1=0.9, y1=0.8)
        assert bbox.x0 == 0.1
        assert bbox.y0 == 0.2
        assert bbox.x1 == 0.9
        assert bbox.y1 == 0.8

    def test_zero_area_bbox_allowed(self):
        """A zero-area bbox (point or line) is valid."""
        bbox = BBox(x0=0.5, y0=0.5, x1=0.5, y1=0.5)
        assert bbox.area() == 0.0

    def test_invalid_x1_less_than_x0(self):
        with pytest.raises(ValidationError, match="x1.*must be >= x0"):
            BBox(x0=0.9, y0=0.1, x1=0.1, y1=0.8)

    def test_invalid_y1_less_than_y0(self):
        with pytest.raises(ValidationError, match="y1.*must be >= y0"):
            BBox(x0=0.1, y0=0.9, x1=0.5, y1=0.1)

    def test_coordinates_out_of_range(self):
        with pytest.raises(ValidationError):
            BBox(x0=-0.1, y0=0.0, x1=0.5, y1=0.5)
        with pytest.raises(ValidationError):
            BBox(x0=0.0, y0=0.0, x1=1.1, y1=0.5)

    def test_to_xywh(self):
        bbox = BBox(x0=0.1, y0=0.2, x1=0.5, y1=0.8)
        x, y, w, h = bbox.to_xywh()
        assert x == pytest.approx(0.1)
        assert y == pytest.approx(0.2)
        assert w == pytest.approx(0.4)
        assert h == pytest.approx(0.6)

    def test_area(self):
        bbox = BBox(x0=0.0, y0=0.0, x1=0.5, y1=0.5)
        assert bbox.area() == pytest.approx(0.25)

    def test_bbox_json_round_trip(self):
        bbox = BBox(x0=0.1, y0=0.2, x1=0.9, y1=0.8)
        json_str = bbox.model_dump_json()
        restored = BBox.model_validate_json(json_str)
        assert restored == bbox


# ---------- VerificationRecord tests ----------


class TestVerificationRecord:
    def test_create_verification_record(self):
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        vr = VerificationRecord(
            reviewer_id="human_alice",
            timestamp=ts,
            confidence=0.95,
            notes="Verified by visual inspection",
        )
        assert vr.reviewer_id == "human_alice"
        assert vr.timestamp == ts
        assert vr.confidence == 0.95
        assert vr.notes == "Verified by visual inspection"

    def test_verification_record_no_notes(self):
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        vr = VerificationRecord(reviewer_id="claude_opus", timestamp=ts, confidence=0.8)
        assert vr.notes is None

    def test_invalid_confidence_range(self):
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        with pytest.raises(ValidationError):
            VerificationRecord(reviewer_id="r1", timestamp=ts, confidence=1.5)
        with pytest.raises(ValidationError):
            VerificationRecord(reviewer_id="r1", timestamp=ts, confidence=-0.1)

    def test_verification_record_json_round_trip(self):
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        vr = VerificationRecord(
            reviewer_id="human_alice", timestamp=ts, confidence=0.95, notes="Good"
        )
        json_str = vr.model_dump_json()
        restored = VerificationRecord.model_validate_json(json_str)
        assert restored == vr


# ---------- GTElement tests ----------


class TestGTElement:
    def test_create_basic_element(self):
        elem = GTElement(id="e1")
        assert elem.id == "e1"
        assert elem.verifications == []
        assert elem.tags == []

    def test_create_element_with_tags(self):
        elem = GTElement(id="e1", tags=["philosophy", "heidegger"])
        assert elem.tags == ["philosophy", "heidegger"]

    def test_is_verified_no_verifications(self):
        elem = GTElement(id="e1")
        assert elem.is_verified() is False

    def test_is_verified_above_threshold(self):
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        elem = GTElement(
            id="e1",
            verifications=[
                VerificationRecord(reviewer_id="r1", timestamp=ts, confidence=0.9),
            ],
        )
        assert elem.is_verified(threshold=0.8) is True

    def test_is_verified_below_threshold(self):
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        elem = GTElement(
            id="e1",
            verifications=[
                VerificationRecord(reviewer_id="r1", timestamp=ts, confidence=0.5),
            ],
        )
        assert elem.is_verified(threshold=0.8) is False

    def test_is_verified_custom_threshold(self):
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        elem = GTElement(
            id="e1",
            verifications=[
                VerificationRecord(reviewer_id="r1", timestamp=ts, confidence=0.7),
            ],
        )
        assert elem.is_verified(threshold=0.7) is True
        assert elem.is_verified(threshold=0.8) is False

    def test_agreement_score_no_verifications(self):
        elem = GTElement(id="e1")
        assert elem.agreement_score() is None

    def test_agreement_score_single_reviewer(self):
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        elem = GTElement(
            id="e1",
            verifications=[
                VerificationRecord(reviewer_id="r1", timestamp=ts, confidence=0.9),
            ],
        )
        assert elem.agreement_score() == pytest.approx(0.9)

    def test_agreement_score_multiple_reviewers(self):
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        elem = GTElement(
            id="e1",
            verifications=[
                VerificationRecord(reviewer_id="r1", timestamp=ts, confidence=0.9),
                VerificationRecord(reviewer_id="r2", timestamp=ts, confidence=0.7),
            ],
        )
        assert elem.agreement_score() == pytest.approx(0.8)

    def test_extra_fields_allowed(self):
        """GTElement accepts unknown fields for forward compatibility."""
        elem = GTElement(id="e1", custom_field="future_value", another_field=42)
        assert elem.custom_field == "future_value"  # type: ignore[attr-defined]
        assert elem.another_field == 42  # type: ignore[attr-defined]

    def test_element_json_round_trip(self):
        ts = datetime(2026, 2, 18, 10, 0, 0, tzinfo=UTC)
        elem = GTElement(
            id="e1",
            verifications=[
                VerificationRecord(reviewer_id="r1", timestamp=ts, confidence=0.95, notes="OK"),
            ],
            tags=["test"],
        )
        json_str = elem.model_dump_json()
        restored = GTElement.model_validate_json(json_str)
        assert restored.id == elem.id
        assert len(restored.verifications) == 1
        assert restored.verifications[0].confidence == 0.95
        assert restored.tags == ["test"]

    def test_element_extra_fields_round_trip(self):
        """Extra fields survive JSON serialization round-trip."""
        elem = GTElement(id="e1", future_field="v2_data")
        json_str = elem.model_dump_json()
        restored = GTElement.model_validate_json(json_str)
        assert restored.future_field == "v2_data"  # type: ignore[attr-defined]


# ---------- Label enum tests ----------


class TestLabelEnums:
    def test_spatial_label_count(self):
        assert len(SpatialLabel) == 17

    def test_semantic_type_count(self):
        assert len(SemanticType) == 9

    def test_formatting_type_count(self):
        assert len(FormattingType) == 6

    def test_document_type_count(self):
        assert len(DocumentType) == 5

    def test_citation_type_count(self):
        assert len(CitationType) == 7

    def test_marginal_ref_type_count(self):
        assert len(MarginalRefType) == 4

    def test_scan_quality_values(self):
        assert {q.value for q in ScanQuality} == {"low", "medium", "high"}

    def test_difficulty_values(self):
        assert {d.value for d in Difficulty} == {"easy", "medium", "hard"}

    def test_spatial_label_serializes_as_string(self):
        """str, Enum pattern ensures JSON serialization as string."""
        assert SpatialLabel.TEXT_BLOCK == "text_block"
        assert SpatialLabel.TEXT_BLOCK.value == "text_block"
        # str(Enum) returns class-qualified name in Python 3.11+;
        # the .value property gives the raw string for serialization
        assert isinstance(SpatialLabel.TEXT_BLOCK, str)

    def test_semantic_type_serializes_as_string(self):
        assert SemanticType.FOOTNOTE == "footnote"
        assert SemanticType.FOOTNOTE.value == "footnote"
        assert isinstance(SemanticType.FOOTNOTE, str)

    def test_label_in_json_output(self):
        """Labels serialize as plain strings in Pydantic JSON output."""
        from pydantic import BaseModel

        class Sample(BaseModel):
            label: SpatialLabel

        s = Sample(label=SpatialLabel.TEXT_BLOCK)
        json_str = s.model_dump_json()
        assert '"text_block"' in json_str

        # Round-trip
        restored = Sample.model_validate_json(json_str)
        assert restored.label == SpatialLabel.TEXT_BLOCK
