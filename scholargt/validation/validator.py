"""Config-aware GT file validation for ScholarGT.

Validates ground truth files against both the JSON Schema (structural correctness)
and profile-specific rules (e.g., extraction-eval requires text on every region,
layout-annotation requires bbox on every region).

Three levels of validation:
1. Schema validation: Does the data conform to the JSON Schema / Pydantic model?
2. Profile validation: Does the data meet the profile's requirements?
3. Structural checks: Are internal references consistent (reading_order IDs, etc.)?

Warnings are used for soft constraints (unknown labels, missing optional data).
Errors are used for hard constraints (missing required fields, schema violations).
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from scholargt.config.models import GTProfile
from scholargt.schema.document import DocumentGT
from scholargt.schema.page import PageGT
from scholargt.validation.schema_gen import DEFAULT_SCHEMA_PATH


class ValidationResult(BaseModel):
    """Result of validating a GT file or data dict."""

    valid: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def add_error(self, msg: str) -> None:
        """Add an error and mark result as invalid."""
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str) -> None:
        """Add a warning (does not affect validity)."""
        self.warnings.append(msg)


def _validate_with_jsonschema(data: dict, schema_key: str) -> list[str]:
    """Validate data against the generated JSON Schema.

    Args:
        data: The data dict to validate.
        schema_key: The $defs key to validate against (e.g., "PageGT", "DocumentGT").

    Returns:
        List of error messages (empty if valid).
    """
    try:
        import jsonschema
    except ImportError:
        return []  # jsonschema not installed, skip

    if not DEFAULT_SCHEMA_PATH.exists():
        return []  # No generated schema, skip jsonschema validation

    try:
        with open(DEFAULT_SCHEMA_PATH) as f:
            full_schema = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    # Build a schema reference pointing to the specific model def
    defs = full_schema.get("$defs", {})
    if schema_key not in defs:
        return []

    # Create a validation schema that references the specific model
    ref_schema = {
        "$ref": f"#/$defs/{schema_key}",
        "$defs": defs,
    }

    errors = []
    try:
        jsonschema.validate(data, ref_schema)
    except jsonschema.ValidationError as e:
        errors.append(f"Schema validation error: {e.message}")
    except jsonschema.SchemaError as e:
        errors.append(f"Schema error: {e.message}")

    return errors


def validate_page_gt(
    data: dict,
    profile: GTProfile | None = None,
) -> ValidationResult:
    """Validate page-level ground truth data.

    Performs three levels of validation:
    1. Schema validation (JSON Schema or Pydantic model_validate)
    2. Profile-aware validation (if profile provided)
    3. Structural consistency checks

    Args:
        data: A dict representing a PageGT JSON object.
        profile: Optional GTProfile for config-aware validation.

    Returns:
        ValidationResult with errors and warnings.
    """
    result = ValidationResult()

    # 1. Schema validation
    schema_errors = _validate_with_jsonschema(data, "PageGT")
    if schema_errors:
        for err in schema_errors:
            result.add_error(err)
    else:
        # Fallback to Pydantic model_validate if no jsonschema errors
        try:
            PageGT.model_validate(data)
        except ValidationError as e:
            for error in e.errors():
                loc = " -> ".join(str(x) for x in error["loc"])
                result.add_error(f"Pydantic validation error at {loc}: {error['msg']}")

    # 2. Profile-aware validation
    if profile is not None:
        regions = data.get("regions", [])
        reading_order = data.get("reading_order", [])

        for i, region in enumerate(regions):
            label = region.get("label", "")

            # Check spatial label against profile
            if label and label not in profile.spatial_labels:
                result.add_warning(
                    f"Region {i} label '{label}' not in profile spatial_labels"
                )

            # require_text check
            if profile.validation.require_text and region.get("text") is None:
                result.add_warning(
                    f"Region {i} ('{label}') has no text "
                    f"(profile '{profile.name}' requires text)"
                )

            # require_bbox check
            if profile.validation.require_bbox and region.get("bbox") is None:
                result.add_error(
                    f"Region {i} ('{label}') has no bbox "
                    f"(profile '{profile.name}' requires bbox)"
                )

        # require_reading_order check
        if profile.validation.require_reading_order and not reading_order:
            result.add_warning(
                f"reading_order is empty (profile '{profile.name}' requires reading order)"
            )

    # 3. Structural checks
    regions = data.get("regions", [])
    reading_order = data.get("reading_order", [])

    if regions and reading_order:
        region_ids = {r.get("id", "") for r in regions}
        for rid in reading_order:
            if rid not in region_ids:
                result.add_warning(
                    f"reading_order references unknown region ID: '{rid}'"
                )

    if "schema_version" not in data:
        result.add_warning("schema_version not present in page GT data")

    return result


def validate_document_gt(
    data: dict,
    profile: GTProfile | None = None,
) -> ValidationResult:
    """Validate document-level ground truth data.

    Performs three levels of validation:
    1. Schema validation (JSON Schema or Pydantic model_validate)
    2. Profile-aware validation (if profile provided)
    3. Structural consistency checks

    Args:
        data: A dict representing a DocumentGT JSON object.
        profile: Optional GTProfile for config-aware validation.

    Returns:
        ValidationResult with errors and warnings.
    """
    result = ValidationResult()

    # 1. Schema validation
    schema_errors = _validate_with_jsonschema(data, "DocumentGT")
    if schema_errors:
        for err in schema_errors:
            result.add_error(err)
    else:
        try:
            DocumentGT.model_validate(data)
        except ValidationError as e:
            for error in e.errors():
                loc = " -> ".join(str(x) for x in error["loc"])
                result.add_error(f"Pydantic validation error at {loc}: {error['msg']}")

    # 2. Profile-aware validation
    if profile is not None:
        elements = data.get("elements", [])

        for i, elem in enumerate(elements):
            elem_type = elem.get("element_type", "")

            # Check semantic element type against profile
            if elem_type and elem_type not in profile.semantic_types:
                result.add_warning(
                    f"Element {i} type '{elem_type}' not in profile semantic_types"
                )

        # Check formatting annotations against profile
        formatting = data.get("formatting", [])
        if formatting and not profile.formatting_types:
            result.add_warning(
                f"Document has {len(formatting)} formatting annotations "
                f"but profile '{profile.name}' has no formatting_types enabled"
            )

    # 3. Structural checks
    if "document_id" not in data:
        result.add_warning("document_id not present in document GT data")

    if "schema_version" not in data:
        result.add_warning("schema_version not present in document GT data")

    # Check for dangling relationship references
    relationships = data.get("relationships")
    if relationships:
        element_ids = {
            elem.get("id", "") for elem in data.get("elements", [])
        }

        for link in relationships.get("footnote_links", []):
            if link.get("content_id") and link["content_id"] not in element_ids:
                result.add_warning(
                    f"Footnote link references unknown content_id: '{link['content_id']}'"
                )
            if link.get("marker_id") and link["marker_id"] not in element_ids:
                result.add_warning(
                    f"Footnote link references unknown marker_id: '{link['marker_id']}'"
                )

        for link in relationships.get("citation_bib_links", []):
            if link.get("citation_id") and link["citation_id"] not in element_ids:
                result.add_warning(
                    f"Citation link references unknown citation_id: '{link['citation_id']}'"
                )
            if link.get("bib_entry_id") and link["bib_entry_id"] not in element_ids:
                result.add_warning(
                    f"Citation link references unknown bib_entry_id: '{link['bib_entry_id']}'"
                )

    return result


def validate_gt_file(
    file_path: Path,
    profile: GTProfile | None = None,
) -> ValidationResult:
    """Validate a GT JSON file, auto-detecting page vs document level.

    Detects the GT type by checking for discriminating keys:
    - "regions" -> PageGT (page-level)
    - "document_id" -> DocumentGT (document-level)

    Args:
        file_path: Path to a GT JSON file.
        profile: Optional GTProfile for config-aware validation.

    Returns:
        ValidationResult with errors and warnings.
    """
    result = ValidationResult()

    if not file_path.exists():
        result.add_error(f"File not found: {file_path}")
        return result

    try:
        with open(file_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        result.add_error(f"Invalid JSON: {e}")
        return result
    except OSError as e:
        result.add_error(f"Cannot read file: {e}")
        return result

    if not isinstance(data, dict):
        result.add_error("GT file must contain a JSON object (dict), not array or scalar")
        return result

    # Auto-detect GT type
    if "document_id" in data:
        return validate_document_gt(data, profile)
    elif "regions" in data or "page_index" in data:
        return validate_page_gt(data, profile)
    else:
        result.add_error(
            "Cannot determine GT type: file has neither 'regions'/'page_index' "
            "(PageGT) nor 'document_id' (DocumentGT)"
        )
        return result
