"""Validation system for ScholarGT ground truth files.

Provides JSON Schema generation from Pydantic models and config-aware
validation of GT files against profile requirements.

Usage:
    from scholargt.validation import generate_schema, validate_gt_file
    from scholargt.config import load_profile

    # Generate/write JSON Schema
    schema = generate_schema()
    write_schema()  # writes to scholargt/generated/schema.json

    # Validate a GT file against a profile
    result = validate_gt_file(Path("page.json"), load_profile("extraction-eval"))
    assert result.valid
"""

from scholargt.validation.schema_gen import generate_schema, write_schema
from scholargt.validation.validator import (
    ValidationResult,
    validate_document_gt,
    validate_gt_file,
    validate_page_gt,
)

__all__ = [
    "ValidationResult",
    "generate_schema",
    "validate_document_gt",
    "validate_gt_file",
    "validate_page_gt",
    "write_schema",
]
