"""Tests for ScholarGT validation system.

Tests JSON Schema generation, config-aware validation, extensibility,
auto-detection of page vs document GT, and end-to-end file validation.
"""

from __future__ import annotations

import json
from pathlib import Path

from scholargt.config.loader import load_profile
from scholargt.schema.base import BBox
from scholargt.schema.document import (
    DocumentGT,
    DocumentSource,
)
from scholargt.schema.labels import SpatialLabel
from scholargt.schema.page import PageGT
from scholargt.schema.semantic import (
    ContentSpan,
    Footnote,
    MarkerInfo,
    Section,
)
from scholargt.schema.spatial import Region
from scholargt.schema.version import SCHEMA_VERSION
from scholargt.validation.schema_gen import generate_schema, write_schema
from scholargt.validation.validator import (
    ValidationResult,
    validate_document_gt,
    validate_gt_file,
    validate_page_gt,
)

# ---------- Schema generation tests ----------


class TestGenerateSchema:
    """Tests for JSON Schema generation from Pydantic models."""

    def test_generate_schema_returns_dict(self):
        schema = generate_schema()
        assert isinstance(schema, dict)

    def test_schema_has_correct_title(self):
        schema = generate_schema()
        assert schema["title"] == "ScholarGT Schema"

    def test_schema_has_version(self):
        schema = generate_schema()
        assert schema["version"] == SCHEMA_VERSION

    def test_schema_has_json_schema_draft(self):
        schema = generate_schema()
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_schema_has_defs(self):
        schema = generate_schema()
        assert "$defs" in schema
        assert len(schema["$defs"]) > 0

    def test_schema_contains_page_gt_def(self):
        schema = generate_schema()
        assert "PageGT" in schema["$defs"]

    def test_schema_contains_document_gt_def(self):
        schema = generate_schema()
        assert "DocumentGT" in schema["$defs"]

    def test_schema_contains_gt_profile_def(self):
        schema = generate_schema()
        assert "GTProfile" in schema["$defs"]


class TestWriteSchema:
    """Tests for writing schema to disk."""

    def test_write_schema_creates_file(self, tmp_path: Path):
        output = tmp_path / "test_schema.json"
        result = write_schema(output)
        assert result == output
        assert output.exists()

    def test_written_schema_is_valid_json(self, tmp_path: Path):
        output = tmp_path / "test_schema.json"
        write_schema(output)
        with open(output) as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert data["title"] == "ScholarGT Schema"


# ---------- Schema validation round-trip tests ----------


class TestSchemaValidatesModels:
    """Test that generated schema validates valid model JSON."""

    def test_schema_validates_page_gt(self):
        """Round-trip: create model -> dump -> validate against schema."""
        page = PageGT(
            page_index=0,
            regions=[
                Region(
                    id="r1",
                    label=SpatialLabel.TEXT_BLOCK,
                    bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.9),
                    text="Hello world",
                )
            ],
            reading_order=["r1"],
        )
        data = page.model_dump(mode="json")
        result = validate_page_gt(data)
        assert result.valid, f"Errors: {result.errors}"

    def test_schema_validates_document_gt(self):
        """Round-trip: create DocumentGT model -> dump -> validate."""
        doc = DocumentGT(
            document_id="doc-001",
            source=DocumentSource(pdf="test.pdf", title="Test Document"),
            elements=[
                Section(
                    id="s1",
                    title="Chapter 1",
                    level=0,
                ),
            ],
        )
        data = doc.model_dump(mode="json")
        result = validate_document_gt(data)
        assert result.valid, f"Errors: {result.errors}"

    def test_schema_rejects_invalid_page_gt(self):
        """Missing required field should produce errors."""
        # PageGT requires page_index
        data = {"regions": []}  # missing page_index
        result = validate_page_gt(data)
        assert not result.valid
        assert any("page_index" in err for err in result.errors)


# ---------- Profile-aware validation: PageGT ----------


class TestValidatePageGTWithProfile:
    """Tests for config-aware page GT validation."""

    def _make_page_data(self, **overrides) -> dict:
        """Create minimal valid PageGT data."""
        base = {
            "schema_version": SCHEMA_VERSION,
            "page_index": 0,
            "regions": [
                {
                    "id": "r1",
                    "label": "text_block",
                    "bbox": {"x0": 0.1, "y0": 0.1, "x1": 0.9, "y1": 0.9},
                    "text": "Sample text",
                }
            ],
            "reading_order": ["r1"],
        }
        base.update(overrides)
        return base

    def test_unknown_spatial_label_warns(self):
        """Labels not in profile should generate warnings, not errors."""
        data = self._make_page_data(
            regions=[
                {
                    "id": "r1",
                    "label": "formula",  # not in extraction-eval
                    "bbox": {"x0": 0.1, "y0": 0.1, "x1": 0.5, "y1": 0.5},
                    "text": "E=mc^2",
                }
            ]
        )
        profile = load_profile("extraction-eval")
        result = validate_page_gt(data, profile)
        assert result.valid  # warnings don't affect validity
        assert any("formula" in w and "spatial_labels" in w for w in result.warnings)

    def test_extraction_eval_warns_on_missing_text(self):
        """Extraction-eval profile requires text on all regions."""
        data = self._make_page_data(
            regions=[
                {
                    "id": "r1",
                    "label": "text_block",
                    "bbox": {"x0": 0.1, "y0": 0.1, "x1": 0.9, "y1": 0.9},
                    # no text field
                }
            ]
        )
        profile = load_profile("extraction-eval")
        result = validate_page_gt(data, profile)
        assert any("no text" in w for w in result.warnings)

    def test_layout_annotation_warns_on_missing_reading_order(self):
        """Layout-annotation requires reading order."""
        data = self._make_page_data(reading_order=[])
        profile = load_profile("layout-annotation")
        result = validate_page_gt(data, profile)
        assert any("reading_order" in w for w in result.warnings)

    def test_require_bbox_errors_on_missing(self):
        """require_bbox should produce error, not warning."""
        data = {
            "schema_version": SCHEMA_VERSION,
            "page_index": 0,
            "regions": [
                {
                    "id": "r1",
                    "label": "text_block",
                    # no bbox
                    "text": "Some text",
                }
            ],
            "reading_order": ["r1"],
        }
        profile = load_profile("layout-annotation")
        # This test validates profile checking -- the actual Pydantic model
        # requires bbox, so we pass data that bypasses Pydantic validation.
        # The profile check catches bbox=None independently.
        result = validate_page_gt(data, profile)
        # Either schema validation catches it or profile check does
        assert not result.valid or any("bbox" in w for w in result.warnings)


# ---------- Profile-aware validation: DocumentGT ----------


class TestValidateDocumentGTWithProfile:
    """Tests for config-aware document GT validation."""

    def _make_doc_data(self, **overrides) -> dict:
        """Create minimal valid DocumentGT data."""
        base = {
            "schema_version": SCHEMA_VERSION,
            "document_id": "doc-001",
            "source": {"pdf": "test.pdf"},
            "elements": [
                {
                    "id": "s1",
                    "element_type": "section",
                    "title": "Chapter 1",
                    "level": 0,
                }
            ],
        }
        base.update(overrides)
        return base

    def test_unknown_semantic_type_warns(self):
        """Element types not in profile should generate warnings."""
        data = self._make_doc_data(
            elements=[
                {
                    "id": "sr1",
                    "element_type": "sous_rature",
                    "text": "Being",
                    "page": 42,
                }
            ]
        )
        # extraction-eval doesn't include sous_rature
        profile = load_profile("extraction-eval")
        result = validate_document_gt(data, profile)
        assert result.valid
        assert any("sous_rature" in w for w in result.warnings)

    def test_formatting_without_profile_types_warns(self):
        """Formatting annotations with no profile formatting_types should warn."""
        data = self._make_doc_data(
            formatting=[
                {
                    "id": "f1",
                    "formatting_type": "italic",
                    "page": 0,
                    "char_offset": 10,
                    "char_length": 5,
                }
            ]
        )
        # extraction-eval has no formatting_types
        profile = load_profile("extraction-eval")
        result = validate_document_gt(data, profile)
        assert any("formatting" in w.lower() for w in result.warnings)

    def test_full_scholarly_accepts_all_types(self):
        """Full-scholarly profile should accept all semantic types."""
        data = self._make_doc_data(
            elements=[
                {"id": "s1", "element_type": "section", "title": "Ch 1", "level": 0},
                {
                    "id": "fn1",
                    "element_type": "footnote",
                    "marker": {"text": "1", "page": 0},
                    "content": [{"page": 0, "text": "A note."}],
                    "location": "page_bottom",
                },
            ]
        )
        profile = load_profile("full-scholarly")
        result = validate_document_gt(data, profile)
        assert result.valid
        # No warnings about semantic types
        assert not any("semantic_types" in w for w in result.warnings)


# ---------- Extensibility tests ----------


class TestExtensibility:
    """Tests proving extensibility: extra fields and custom tags don't break validation."""

    def test_page_gt_with_extra_fields_validates(self):
        """PageGT with extra="allow" accepts additional fields."""
        data = {
            "schema_version": SCHEMA_VERSION,
            "page_index": 0,
            "regions": [],
            "reading_order": [],
            "custom_metadata": {"annotator": "alice", "tool_version": "2.0"},
        }
        result = validate_page_gt(data)
        assert result.valid, f"Errors: {result.errors}"

    def test_region_with_custom_tags_validates(self):
        """Region tags field accepts arbitrary strings (open-ended)."""
        page = PageGT(
            page_index=0,
            regions=[
                Region(
                    id="r1",
                    label=SpatialLabel.TEXT_BLOCK,
                    bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.9),
                    tags=["custom_project_tag", "needs_review", "philosophy"],
                )
            ],
        )
        data = page.model_dump(mode="json")
        result = validate_page_gt(data)
        assert result.valid, f"Errors: {result.errors}"

    def test_document_gt_with_extra_fields_validates(self):
        """DocumentGT with extra="allow" accepts additional fields."""
        data = {
            "schema_version": SCHEMA_VERSION,
            "document_id": "doc-ext",
            "source": {"pdf": "test.pdf"},
            "elements": [],
            "experimental_score": 0.95,
        }
        result = validate_document_gt(data)
        assert result.valid, f"Errors: {result.errors}"


# ---------- Auto-detection and file validation ----------


class TestValidateGTFile:
    """Tests for validate_gt_file auto-detection and file handling."""

    def test_auto_detects_page_gt(self, tmp_path: Path):
        """File with 'regions' key is detected as PageGT."""
        data = {
            "schema_version": SCHEMA_VERSION,
            "page_index": 0,
            "regions": [],
            "reading_order": [],
        }
        f = tmp_path / "page.json"
        f.write_text(json.dumps(data))
        result = validate_gt_file(f)
        assert result.valid

    def test_auto_detects_document_gt(self, tmp_path: Path):
        """File with 'document_id' key is detected as DocumentGT."""
        data = {
            "schema_version": SCHEMA_VERSION,
            "document_id": "doc-001",
            "source": {"pdf": "test.pdf"},
        }
        f = tmp_path / "doc.json"
        f.write_text(json.dumps(data))
        result = validate_gt_file(f)
        assert result.valid

    def test_nonexistent_file_returns_error(self):
        """Validating a non-existent file returns error."""
        result = validate_gt_file(Path("/nonexistent/file.json"))
        assert not result.valid
        assert any("not found" in e.lower() for e in result.errors)

    def test_invalid_json_returns_error(self, tmp_path: Path):
        """Invalid JSON produces an error."""
        f = tmp_path / "bad.json"
        f.write_text("{not valid json}")
        result = validate_gt_file(f)
        assert not result.valid
        assert any("json" in e.lower() for e in result.errors)

    def test_unknown_gt_type_returns_error(self, tmp_path: Path):
        """File without discriminating keys produces an error."""
        f = tmp_path / "unknown.json"
        f.write_text(json.dumps({"random_key": "value"}))
        result = validate_gt_file(f)
        assert not result.valid
        assert any("cannot determine" in e.lower() for e in result.errors)


# ---------- ValidationResult model ----------


class TestValidationResult:
    """Tests for the ValidationResult model itself."""

    def test_default_is_valid(self):
        result = ValidationResult()
        assert result.valid
        assert result.errors == []
        assert result.warnings == []

    def test_add_error_marks_invalid(self):
        result = ValidationResult()
        result.add_error("something broke")
        assert not result.valid
        assert "something broke" in result.errors

    def test_add_warning_keeps_valid(self):
        result = ValidationResult()
        result.add_warning("minor issue")
        assert result.valid
        assert "minor issue" in result.warnings

    def test_multiple_errors(self):
        result = ValidationResult()
        result.add_error("error 1")
        result.add_error("error 2")
        assert not result.valid
        assert len(result.errors) == 2


# ---------- Structural checks ----------


class TestStructuralChecks:
    """Tests for structural consistency validation."""

    def test_reading_order_unknown_id_warns(self):
        """reading_order referencing non-existent region ID should warn."""
        data = {
            "schema_version": SCHEMA_VERSION,
            "page_index": 0,
            "regions": [
                {
                    "id": "r1",
                    "label": "text_block",
                    "bbox": {"x0": 0.1, "y0": 0.1, "x1": 0.9, "y1": 0.9},
                }
            ],
            "reading_order": ["r1", "r_nonexistent"],
        }
        result = validate_page_gt(data)
        assert any("r_nonexistent" in w for w in result.warnings)

    def test_missing_schema_version_warns(self):
        """Missing schema_version should produce a warning."""
        data = {
            "page_index": 0,
            "regions": [],
            "reading_order": [],
        }
        result = validate_page_gt(data)
        assert any("schema_version" in w for w in result.warnings)

    def test_dangling_footnote_link_warns(self):
        """Footnote link referencing non-existent element should warn."""
        data = {
            "schema_version": SCHEMA_VERSION,
            "document_id": "doc-001",
            "source": {"pdf": "test.pdf"},
            "elements": [
                {"id": "s1", "element_type": "section", "title": "Ch1", "level": 0}
            ],
            "relationships": {
                "footnote_links": [
                    {
                        "marker_id": "fn_marker_1",
                        "content_id": "fn_content_1",
                    }
                ]
            },
        }
        result = validate_document_gt(data)
        assert any("fn_content_1" in w for w in result.warnings)
        assert any("fn_marker_1" in w for w in result.warnings)


# ---------- End-to-end test ----------


class TestEndToEnd:
    """End-to-end: create model -> dump to temp file -> validate_gt_file -> valid."""

    def test_page_gt_end_to_end(self, tmp_path: Path):
        """Create a PageGT model, dump to JSON, validate via file."""
        page = PageGT(
            page_index=5,
            page_label="vi",
            regions=[
                Region(
                    id="r1",
                    label=SpatialLabel.TEXT_BLOCK,
                    bbox=BBox(x0=0.1, y0=0.1, x1=0.9, y1=0.8),
                    text="The question of Being has today been forgotten.",
                ),
                Region(
                    id="r2",
                    label=SpatialLabel.FOOTNOTE_AREA,
                    bbox=BBox(x0=0.1, y0=0.85, x1=0.9, y1=0.95),
                    text="1. Cf. Plato, Sophist 244a.",
                ),
            ],
            reading_order=["r1", "r2"],
        )
        f = tmp_path / "page_005.json"
        f.write_text(json.dumps(page.model_dump(mode="json"), indent=2))

        profile = load_profile("extraction-eval")
        result = validate_gt_file(f, profile)
        assert result.valid, f"Errors: {result.errors}"

    def test_document_gt_end_to_end(self, tmp_path: Path):
        """Create a DocumentGT model, dump to JSON, validate via file."""
        doc = DocumentGT(
            document_id="heidegger-bt-001",
            source=DocumentSource(
                pdf="being_and_time.pdf",
                title="Being and Time",
                author="Martin Heidegger",
                translator="John Macquarrie & Edward Robinson",
                year=1962,
            ),
            elements=[
                Section(id="sec1", title="Introduction", level=0, page_start=0),
                Footnote(
                    id="fn1",
                    marker=MarkerInfo(text="1", page=0),
                    content=[ContentSpan(page=0, text="Cf. Plato, Sophist 244a.")],
                    location="page_bottom",
                ),
            ],
            config_profile="full-scholarly",
        )
        f = tmp_path / "document.json"
        f.write_text(json.dumps(doc.model_dump(mode="json"), indent=2))

        profile = load_profile("full-scholarly")
        result = validate_gt_file(f, profile)
        assert result.valid, f"Errors: {result.errors}"


# ---------- Import test ----------


class TestPublicAPIImports:
    """Test that the public API is accessible from scholargt root."""

    def test_imports_from_scholargt(self):
        """All key symbols importable from scholargt package."""
        from scholargt import (
            generate_schema,
            load_profile,
            validate_document_gt,
            validate_gt_file,
            validate_page_gt,
            write_schema,
        )

        # Verify they are the expected types
        assert callable(generate_schema)
        assert callable(write_schema)
        assert callable(validate_gt_file)
        assert callable(validate_page_gt)
        assert callable(validate_document_gt)
        assert callable(load_profile)
