#!/usr/bin/env python3
"""
Validate Ground Truth YAML

Validates a ground truth YAML file against the schema and checks for:
1. Required fields and structure
2. Referential integrity (all IDs resolve)
3. Consistency checks (counts match, bboxes valid)
4. Common issues

Usage:
    uv run python ground_truth/scripts/validate.py <yaml_path>
    uv run python ground_truth/scripts/validate.py ground_truth/documents/*.yaml
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

SCHEMA_VERSION = "1.1.0"

# Valid values for enums
VALID_REGION_TYPES = {
    "body",
    "footnote_region",
    "footnote_continuation",
    "header",
    "footer",
    "heading",
    "page_number",
    "margin",
    "figure",
    "caption",
    "table",
    "formula",
    "code",
    "index",
    "unknown",
}

VALID_NOTE_TYPES = {"author", "translator", "editor"}
VALID_CITATION_STYLES = {"author_date", "numeric", "abbreviated", "footnote_style"}
VALID_MARGINAL_SYSTEMS = {"stephanus", "bekker", "akademie", "custom"}
VALID_PAGE_FORMATS = {"arabic", "roman_lower", "roman_upper"}
VALID_STATES = {"pending", "annotated", "auto_generated", "verified"}
VALID_ANNOTATORS = {"human", "model_assisted", "auto", None}


@dataclass
class ValidationError:
    """A validation error."""

    path: str
    message: str
    severity: str = "error"  # error, warning, info


@dataclass
class ValidationResult:
    """Result of validation."""

    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)
    info: list[ValidationError] = field(default_factory=list)

    def add(self, error: ValidationError) -> None:
        if error.severity == "error":
            self.errors.append(error)
        elif error.severity == "warning":
            self.warnings.append(error)
        else:
            self.info.append(error)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def print_report(self) -> None:
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for e in self.errors:
                print(f"  [{e.path}] {e.message}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"  [{w.path}] {w.message}")

        if self.info:
            print(f"\nℹ️  INFO ({len(self.info)}):")
            for i in self.info:
                print(f"  [{i.path}] {i.message}")

        if self.is_valid:
            print("\n✅ Validation passed!")
        else:
            print(f"\n❌ Validation failed with {len(self.errors)} error(s)")


def validate_required_fields(
    data: dict[str, Any], required: list[str], path: str, result: ValidationResult
) -> None:
    """Check that required fields are present."""
    for field_name in required:
        if field_name not in data:
            result.add(ValidationError(path, f"Missing required field: {field_name}"))


def validate_bbox(bbox: list[float], path: str, result: ValidationResult) -> None:
    """Validate a bounding box."""
    if not isinstance(bbox, list) or len(bbox) != 4:
        result.add(ValidationError(path, "bbox must be a list of 4 floats"))
        return

    x0, y0, x1, y1 = bbox
    for val in bbox:
        if not isinstance(val, (int, float)):
            result.add(ValidationError(path, f"bbox values must be numbers, got {type(val)}"))
            return

    if not (0 <= x0 <= 1 and 0 <= y0 <= 1 and 0 <= x1 <= 1 and 0 <= y1 <= 1):
        result.add(
            ValidationError(path, f"bbox values must be in [0, 1], got {bbox}", severity="warning")
        )

    if x0 >= x1:
        result.add(ValidationError(path, f"bbox x0 ({x0}) must be < x1 ({x1})"))

    if y0 >= y1:
        result.add(ValidationError(path, f"bbox y0 ({y0}) must be < y1 ({y1})"))


def validate_source(source: dict[str, Any], result: ValidationResult) -> None:
    """Validate the source section."""
    validate_required_fields(source, ["pdf", "page_range"], "source", result)

    if "page_range" in source:
        pr = source["page_range"]
        if not isinstance(pr, list) or len(pr) != 2:
            result.add(ValidationError("source.page_range", "Must be a list of [start, end]"))
        elif pr[0] > pr[1]:
            result.add(ValidationError("source.page_range", f"start ({pr[0]}) > end ({pr[1]})"))


def validate_annotation_status(status: dict[str, Any], result: ValidationResult) -> None:
    """Validate annotation status section."""
    for element_type, s in status.items():
        path = f"annotation_status.{element_type}"

        if "state" in s:
            if s["state"] not in VALID_STATES:
                result.add(ValidationError(path, f"Invalid state: {s['state']}"))

        if "annotator" in s and s["annotator"] not in VALID_ANNOTATORS:
            result.add(ValidationError(path, f"Invalid annotator: {s['annotator']}"))


def validate_pages(pages: list[dict[str, Any]], result: ValidationResult) -> dict[str, set[str]]:
    """Validate pages section and return region IDs by page."""
    region_ids: dict[str, set[str]] = {}

    for i, page in enumerate(pages):
        path = f"pages[{i}]"
        validate_required_fields(page, ["index", "regions"], path, result)

        page_idx = page.get("index", i)
        region_ids[str(page_idx)] = set()

        for j, region in enumerate(page.get("regions", [])):
            region_path = f"{path}.regions[{j}]"
            validate_required_fields(region, ["id", "type", "bbox"], region_path, result)

            region_id = region.get("id", f"unknown_{j}")
            region_ids[str(page_idx)].add(region_id)

            if "type" in region and region["type"] not in VALID_REGION_TYPES:
                result.add(
                    ValidationError(
                        region_path, f"Unknown region type: {region['type']}", severity="warning"
                    )
                )

            if "bbox" in region:
                validate_bbox(region["bbox"], f"{region_path}.bbox", result)

    return region_ids


def validate_footnotes(
    footnotes: list[dict[str, Any]],
    region_ids: dict[str, set[str]],
    result: ValidationResult,
) -> None:
    """Validate footnotes."""
    seen_ids = set()

    for i, fn in enumerate(footnotes):
        path = f"elements.footnotes[{i}]"
        validate_required_fields(fn, ["id", "marker", "content", "pages"], path, result)

        fn_id = fn.get("id", f"fn_{i}")
        if fn_id in seen_ids:
            result.add(ValidationError(path, f"Duplicate footnote ID: {fn_id}"))
        seen_ids.add(fn_id)

        # Check note_type
        if "note_type" in fn and fn["note_type"] not in VALID_NOTE_TYPES:
            result.add(ValidationError(path, f"Invalid note_type: {fn['note_type']}"))

        # Check pages consistency
        content_pages = set()
        for content in fn.get("content", []):
            if "page" in content:
                content_pages.add(content["page"])

        declared_pages = set(fn.get("pages", []))
        if content_pages and content_pages != declared_pages:
            result.add(
                ValidationError(
                    path,
                    f"pages {declared_pages} doesn't match content pages {content_pages}",
                    severity="warning",
                )
            )


def validate_citations(citations: list[dict[str, Any]], result: ValidationResult) -> None:
    """Validate citations."""
    seen_ids = set()

    for i, cite in enumerate(citations):
        path = f"elements.citations[{i}]"
        validate_required_fields(cite, ["id", "raw", "page"], path, result)

        cite_id = cite.get("id", f"cite_{i}")
        if cite_id in seen_ids:
            result.add(ValidationError(path, f"Duplicate citation ID: {cite_id}"))
        seen_ids.add(cite_id)

        if "parsed" in cite:
            parsed = cite["parsed"]
            if "style" in parsed and parsed["style"] not in VALID_CITATION_STYLES:
                result.add(
                    ValidationError(f"{path}.parsed", f"Invalid citation style: {parsed['style']}")
                )


def validate_marginal_refs(refs: list[dict[str, Any]], result: ValidationResult) -> None:
    """Validate marginal references."""
    for i, ref in enumerate(refs):
        path = f"elements.marginal_refs[{i}]"
        validate_required_fields(ref, ["id", "system", "markers"], path, result)

        if "system" in ref and ref["system"] not in VALID_MARGINAL_SYSTEMS:
            result.add(ValidationError(path, f"Invalid system: {ref['system']}"))


def validate_page_numbers(pns: list[dict[str, Any]], result: ValidationResult) -> None:
    """Validate page numbers."""
    for i, pn in enumerate(pns):
        path = f"elements.page_numbers[{i}]"
        validate_required_fields(pn, ["page", "displayed"], path, result)

        if "format" in pn and pn["format"] not in VALID_PAGE_FORMATS:
            result.add(ValidationError(path, f"Invalid format: {pn['format']}"))


def validate_sous_rature(srs: list[dict[str, Any]], result: ValidationResult) -> None:
    """Validate sous rature (under erasure) elements."""
    seen_ids = set()

    for i, sr in enumerate(srs):
        path = f"elements.sous_rature[{i}]"
        validate_required_fields(sr, ["id", "text", "page", "char_offset"], path, result)

        sr_id = sr.get("id", f"sr_{i}")
        if sr_id in seen_ids:
            result.add(ValidationError(path, f"Duplicate sous_rature ID: {sr_id}"))
        seen_ids.add(sr_id)

        # Check char_length is present and positive
        if "char_length" in sr:
            if not isinstance(sr["char_length"], int) or sr["char_length"] <= 0:
                result.add(ValidationError(path, "char_length must be a positive integer"))


def validate_relationships(
    relationships: dict[str, Any],
    footnote_ids: set[str],
    citation_ids: set[str],
    bib_ids: set[str],
    result: ValidationResult,
) -> None:
    """Validate relationships and referential integrity."""
    # Check citation -> bib links
    for i, link in enumerate(relationships.get("citation_bib_links", [])):
        path = f"relationships.citation_bib_links[{i}]"

        cite_id = link.get("citation_id")
        if cite_id and cite_id not in citation_ids:
            result.add(ValidationError(path, f"Unknown citation_id: {cite_id}"))

        bib_id = link.get("bib_entry_id")
        if bib_id and bib_id not in bib_ids:
            result.add(ValidationError(path, f"Unknown bib_entry_id: {bib_id}", severity="warning"))


def validate_counts(ground_truth: dict[str, Any], result: ValidationResult) -> None:
    """Validate that annotation_status counts match actual counts."""
    elements = ground_truth.get("elements", {})
    status = ground_truth.get("annotation_status", {})

    for element_type in ["footnotes", "endnotes", "citations", "marginal_refs", "sous_rature"]:
        actual = len(elements.get(element_type, []))
        declared = status.get(element_type, {}).get("count")

        if declared is not None and declared != actual:
            result.add(
                ValidationError(
                    f"annotation_status.{element_type}",
                    f"Declared count ({declared}) != actual count ({actual})",
                    severity="warning",
                )
            )


def validate_ground_truth(yaml_path: Path) -> ValidationResult:
    """Validate a ground truth YAML file."""
    result = ValidationResult()

    # Load YAML
    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        result.add(ValidationError("", f"Invalid YAML: {e}"))
        return result
    except FileNotFoundError:
        result.add(ValidationError("", f"File not found: {yaml_path}"))
        return result

    if not isinstance(data, dict):
        result.add(ValidationError("", "Root must be a dictionary"))
        return result

    # Check schema version
    if "schema_version" not in data:
        result.add(ValidationError("", "Missing schema_version"))
    elif data["schema_version"] != SCHEMA_VERSION:
        result.add(
            ValidationError(
                "schema_version",
                f"Version mismatch: {data['schema_version']} != {SCHEMA_VERSION}",
                severity="warning",
            )
        )

    # Validate sections
    validate_required_fields(
        data,
        ["source", "annotation_status", "pages", "elements", "metadata"],
        "",
        result,
    )

    if "source" in data:
        validate_source(data["source"], result)

    if "annotation_status" in data:
        validate_annotation_status(data["annotation_status"], result)

    region_ids: dict[str, set[str]] = {}
    if "pages" in data:
        region_ids = validate_pages(data["pages"], result)

    elements = data.get("elements", {})

    footnote_ids: set[str] = set()
    if "footnotes" in elements:
        validate_footnotes(elements["footnotes"], region_ids, result)
        footnote_ids = {fn["id"] for fn in elements["footnotes"] if "id" in fn}

    citation_ids: set[str] = set()
    if "citations" in elements:
        validate_citations(elements["citations"], result)
        citation_ids = {c["id"] for c in elements["citations"] if "id" in c}

    if "marginal_refs" in elements:
        validate_marginal_refs(elements["marginal_refs"], result)

    if "page_numbers" in elements:
        validate_page_numbers(elements["page_numbers"], result)

    if "sous_rature" in elements:
        validate_sous_rature(elements["sous_rature"], result)

    bib_ids = {b["id"] for b in elements.get("bib_entries", []) if "id" in b}

    if "relationships" in data:
        validate_relationships(data["relationships"], footnote_ids, citation_ids, bib_ids, result)

    # Validate counts consistency
    validate_counts(data, result)

    return result


def main():
    parser = argparse.ArgumentParser(description="Validate ground truth YAML files")
    parser.add_argument("yaml_paths", type=Path, nargs="+", help="YAML file(s) to validate")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")

    args = parser.parse_args()

    all_valid = True

    for yaml_path in args.yaml_paths:
        print(f"\n{'=' * 60}")
        print(f"Validating: {yaml_path}")
        print("=" * 60)

        result = validate_ground_truth(yaml_path)
        result.print_report()

        if not result.is_valid:
            all_valid = False
        elif args.strict and result.warnings:
            all_valid = False

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
