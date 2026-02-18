# ScholarGT Schema Guide

## Overview

ScholarGT is a universal ground truth annotation schema for scholarly documents. It provides a structured, config-driven format for describing the spatial layout, semantic elements, and textual content of scholarly PDFs -- enabling evaluation of extraction pipelines, training of layout detection models, and comprehensive document annotation.

The schema is independent of any specific extraction tool. It serves as the measurement foundation: you cannot improve what you cannot measure.

## Schema Architecture

ScholarGT uses a **hybrid file scope** with two complementary file types:

### PageGT (Page-level)

One JSON file per page. Contains:

- **Regions**: Spatial annotations with bounding boxes, text, and labels
- **Reading order**: Ordered list of region IDs for sequential reading
- **Quality metadata**: Scan quality and annotation difficulty assessments
- **Verification records**: Who verified this page and their confidence

PageGT files capture WHERE things are on the page.

### DocumentGT (Document-level)

One JSON file per document. Contains:

- **Semantic elements**: Footnotes, citations, sections, bibliography entries
- **Formatting annotations**: Bold, italic, underline with character offsets
- **Document structure**: Table of contents, section hierarchy
- **Relationships**: Footnote-to-content links, citation-to-bibliography links
- **Source metadata**: Title, author, publisher, ISBN/DOI

DocumentGT files capture WHAT things mean across the whole document.

### Why Hybrid?

Spatial data is inherently per-page (bounding boxes are page-relative). Semantic data often spans pages (footnotes, sections, relationships). The hybrid approach keeps each file focused and enables:

- Independent page-level annotation workflows
- Cross-page semantic analysis
- Partial annotation (annotate layout first, semantics later)

## Label Taxonomy

ScholarGT organizes labels into 5 independent dimensions:

### Spatial Labels (17)

WHERE on the page. Applied to regions in PageGT files.

| Label | Description |
|-------|-------------|
| `text_block` | Main body text paragraph |
| `footnote_area` | Footnote content area at page bottom |
| `endnote_area` | Endnote content area |
| `page_header` | Running header at page top |
| `page_footer` | Running footer at page bottom |
| `page_number` | Page number indicator |
| `section_header` | Section or chapter heading |
| `title` | Document or chapter title |
| `block_quote` | Extended quotation block |
| `list_item` | Enumerated or bulleted list item |
| `table` | Tabular data region |
| `figure` | Image, diagram, or illustration |
| `caption` | Figure or table caption |
| `formula` | Mathematical formula or equation |
| `marginal_note` | Marginal annotation or reference |
| `bibliography_area` | Bibliography/references section |
| `footnote_continuation` | Footnote continued from previous page |

### Semantic Types (9)

WHAT it means. Applied to elements in DocumentGT files.

| Type | Description |
|------|-------------|
| `footnote` | Footnote with marker and content spans |
| `endnote` | Endnote collected at chapter/book end |
| `citation` | In-text citation reference |
| `bibliography_entry` | Bibliography/references list entry |
| `section` | Document section with hierarchy |
| `sous_rature` | Text under erasure (Derridean concept) |
| `cross_reference` | Internal cross-reference ("see section 3") |
| `marginal_reference` | Marginal reference system (Stephanus, Bekker) |
| `page_number_annotation` | Page number mapping (display to PDF index) |

### Formatting Types (6)

HOW text is decorated. Applied to formatting annotations in DocumentGT.

| Type | Description |
|------|-------------|
| `bold` | Bold text |
| `italic` | Italic text |
| `underline` | Underlined text |
| `strikethrough` | Strikethrough text |
| `small_caps` | Small capitals |
| `superscript` | Superscript text |

### Document Types (5)

Document-level annotation categories.

| Type | Description |
|------|-------------|
| `metadata` | Document metadata annotations |
| `toc` | Table of contents structure |
| `front_matter` | Preface, dedication, etc. |
| `back_matter` | Index, appendices, etc. |
| `note_schema` | Footnote/endnote numbering scheme |

### Quality Labels

Page-level quality assessment for test stratification.

- **scan_quality**: `low`, `medium`, `high`
- **difficulty**: `easy`, `medium`, `hard`

## Multi-dimensional Labeling

A key design principle: spatial and semantic labels are independent axes. A single region can have BOTH:

```json
{
  "id": "r1",
  "label": "text_block",
  "semantic_labels": ["footnote"],
  "bbox": {"x0": 0.1, "y0": 0.8, "x1": 0.9, "y1": 0.95},
  "text": "1. This is a footnote appearing in the text block area."
}
```

This region is spatially a `text_block` (its visual appearance) and semantically a `footnote` (its meaning). This separation enables:

- Layout detection models to focus on spatial labels
- Semantic extraction pipelines to focus on semantic types
- Joint evaluation of both dimensions

## Configuration Profiles

Not every project needs all 17 spatial labels and 9 semantic types. ScholarGT uses **config-driven profiles** to select which labels are active for a given use case.

### Default Profiles

| Profile | Spatial | Semantic | Formatting | Document | Key Validation |
|---------|---------|----------|------------|----------|----------------|
| `base` | 6 | 2 | 0 | 1 | require_bbox |
| `extraction-eval` | 8 | 5 | 0 | 1 | require_text, require_reading_order |
| `layout-annotation` | 17 | 0 | 0 | 1 | require_bbox, require_reading_order |
| `full-scholarly` | 17 | 9 | 6 | 5 | All requirements, confidence_threshold=0.9 |

### Using Profiles

```python
from scholargt import load_profile, validate_gt_file
from pathlib import Path

# Load a built-in profile
profile = load_profile("extraction-eval")

# Check if a label is active
if profile.is_label_enabled("spatial", "text_block"):
    print("text_block is active")

# Validate a GT file against the profile
result = validate_gt_file(Path("page_001.json"), profile)
if result.valid:
    print("File passes validation")
else:
    print(f"Errors: {result.errors}")
```

### Layered Configuration

Profiles support layering: `base.yaml` -> `profile.yaml` -> `project.yaml`. Project-level configs can add custom labels and disable existing ones:

```yaml
# my_project.yaml
profile: full-scholarly
additional_semantic_types:
  - custom_annotation_type
disabled_labels:
  - formula
validation:
  confidence_threshold: 0.85
```

## Verification Model

Every annotatable element can carry verification records:

```json
{
  "verifications": [
    {
      "reviewer_id": "human_alice",
      "timestamp": "2026-02-15T10:30:00",
      "confidence": 0.95,
      "notes": "Verified against print edition."
    },
    {
      "reviewer_id": "human_bob",
      "timestamp": "2026-02-16T15:00:00",
      "confidence": 0.90,
      "notes": "Inter-annotator review confirmed."
    }
  ]
}
```

Key properties:

- **Per-element**: Each region, element, or page carries its own verification records
- **Multi-reviewer**: Multiple verification records support inter-annotator agreement
- **Confidence is reviewer property**: Confidence reflects how sure the reviewer is, not element quality (GT is truth by definition)
- **Agreement score**: Mean confidence across reviewers (future: Cohen's kappa)

An element is considered verified when at least one reviewer's confidence exceeds the profile's threshold (default 0.8, configurable).

## Extensibility

ScholarGT is designed for forward compatibility:

### Adding New Labels

1. Add the label string to your project's YAML config (no schema change needed)
2. The validator warns on unknown labels but does not reject them
3. Existing GT files continue to validate without modification

### Extra Fields

All core models use `extra="allow"` in Pydantic configuration. This means:

- New fields in schema v1.1 won't break v1.0 loaders
- Custom project metadata can be stored alongside standard fields
- JSON Schema validation allows additional properties

### Custom Tags

Every element has an open-ended `tags: list[str]` field for ad-hoc grouping:

```json
{
  "id": "r1",
  "label": "text_block",
  "tags": ["needs_review", "philosophy", "complex_layout"]
}
```

## GT Data Directory Structure

Recommended layout for a GT corpus:

```
gt/
  corpus-name/
    config/
      project.yaml              # Project-level config overrides
    pages/
      document-id/
        page_000.json           # PageGT for page 0
        page_001.json           # PageGT for page 1
        ...
    documents/
      document-id.json          # DocumentGT companion file
    manifests/
      MANIFEST.md               # Lists all annotated documents
```

## Example Walkthroughs

### extraction-eval-page.json

A page from Heidegger's "Being and Time" (Section 7) annotated for text extraction evaluation.

- **4 regions**: section header, two body text blocks, footnote area
- **All regions have text**: Required by the extraction-eval profile for CER/WER computation
- **Reading order specified**: Enables reading order accuracy evaluation
- **Single human reviewer**: Alice verified the transcription with 0.95 confidence

### layout-annotation-page.json

A dense page with 8 regions demonstrating diverse spatial label types.

- **8 regions**: page header, section header, two text blocks, block quote, footnote area, page footer, page number
- **All regions have bounding boxes**: Required by layout-annotation for IoU/mAP metrics
- **Text optional**: Only included on 2 of 8 regions (layout detection does not need text)
- **Layout focus**: No semantic labels applied (layout-annotation profile has empty semantic_types)

### full-scholarly-document.json

A DocumentGT file for Heidegger's "Being and Time" showing comprehensive scholarly annotation.

- **5 semantic elements**: 3 sections (with hierarchy), 1 cross-page footnote, 1 citation (Stephanus type), 1 sous rature, 1 bibliography entry
- **Cross-page footnote**: ContentSpan with `is_continuation=true` on second page
- **Philosophy-specific**: SousRature element for text under erasure, Stephanus citation for Plato reference
- **Formatting annotations**: Italic and bold with character-level offsets
- **Document structure**: Table of contents with page references, section hierarchy
- **Relationships**: Footnote marker-to-content link, citation-to-bibliography link
- **Inter-annotator verification**: Two reviewers with independent confidence scores
- **config_profile**: Set to "full-scholarly" indicating which profile was used during annotation

## JSON Schema

A generated JSON Schema is available at `scholargt/generated/schema.json` for use with:

- IDE autocompletion when editing GT files
- CI pipeline validation
- External tools (jsonschema CLI, ajv, etc.)

Generate or regenerate the schema:

```python
from scholargt import write_schema
write_schema()  # writes to scholargt/generated/schema.json
```

## API Reference

```python
from scholargt import (
    # Core models
    PageGT, DocumentGT, Region, BBox, GTElement,
    # Semantic elements
    Footnote, Citation, Section, BibEntry, SousRature,
    # Config
    GTProfile, load_profile, list_profiles,
    # Validation
    validate_gt_file, validate_page_gt, validate_document_gt,
    ValidationResult, generate_schema, write_schema,
)
```
