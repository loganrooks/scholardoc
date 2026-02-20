# ScholarGT Schema Guide v2.0.0

## Overview

ScholarGT is a universal ground truth annotation schema for scholarly documents. It provides a structured, config-driven format for describing the spatial layout, semantic elements, and textual content of scholarly PDFs -- enabling evaluation of extraction pipelines, training of layout detection models, and comprehensive document annotation.

The schema is independent of any specific extraction tool. It serves as the measurement foundation: you cannot improve what you cannot measure.

**Schema version: 2.0.0** -- This is a major breaking change from v1.0.0. See [Migration Notes](#migration-from-v100) below.

## What's New in v2.0.0

### Major Changes

1. **Note consolidation**: `Footnote` + `Endnote` replaced by unified `Note` model with `placement` field (page_bottom, end_of_chapter, end_of_book, margin)
2. **Commentary apparatus**: New `Commentary` model for philosophical/rabbinic running commentary
3. **Citation decomposition**: Old `CitationType` replaced by `CitationFormat` (how it appears) x `ReferenceSystem` (what coordinates) x `CitationStyle` (document convention)
4. **Hybrid PageQuality**: `ScanQuality`/`Difficulty` enums replaced by categorical + numeric + artifact-list hybrid model
5. **Cross-page relationships**: `PageDependency` and `Region` continuation flags for multi-page content
6. **Self-describing pages**: `SectionContextEntry` provides hierarchical section path per page
7. **Embedded relationships**: `DocumentRelationships` removed; links embedded in elements (Note.body_marker, Citation.bib_entry_id)
8. **LocationRef**: Standardized position reference model (page + region_id + optional char_offset/char_length)

### SFP (Structural Fix Proposal) Features

9. **LayoutRegister (SFP-1)**: Named reading streams for multi-register documents (Talmud, bilingual editions, critical editions)
10. **Text direction (SFP-2)**: Explicit `text_direction` on Region, `base_direction` on PageGT
11. **ScriptVariant (SFP-3)**: Rashi script vs square Hebrew distinction (BCP 47 insufficient)
12. **COLOR formatting (SFP-4)**: Color annotation with `color_value` and `color_semantic` meaning
13. **INDEX_AREA (SFP-5)**: New spatial label for index/concordance regions
14. **CATCHWORD (SFP-6)**: New reference system for pre-modern printed book navigation

## Schema Architecture

ScholarGT uses a **hybrid file scope** with two complementary file types:

### PageGT (Page-level)

One JSON file per page. Contains:

- **Regions**: Spatial annotations with bounding boxes, text, labels, register identity, and text direction
- **Reading order**: Ordered list of region IDs for sequential reading
- **Quality metadata**: Hybrid categorical + numeric + artifact model
- **Section context**: Hierarchical section path for self-describing pages
- **Page dependency**: Cross-page continuation metadata
- **Base direction**: Default text direction for the page (SFP-2)
- **Verification records**: Who verified this page and their confidence

PageGT files capture WHERE things are on the page.

### DocumentGT (Document-level)

One JSON file per document. Contains:

- **Semantic elements**: Notes, commentary, citations, sections, bibliography entries
- **Formatting annotations**: Bold, italic, underline, color, script variant with character offsets
- **Document structure**: Table of contents, section hierarchy
- **Registers**: Named reading streams for multi-register layouts (SFP-1)
- **Note schemas**: Document-level note numbering conventions
- **Citation style**: Document-level citation convention
- **Source metadata**: Title, author, publisher, ISBN/DOI

DocumentGT files capture WHAT things mean across the whole document.

### Why Hybrid?

Spatial data is inherently per-page (bounding boxes are page-relative). Semantic data often spans pages (notes, sections, commentary). The hybrid approach keeps each file focused and enables:

- Independent page-level annotation workflows
- Cross-page semantic analysis
- Partial annotation (annotate layout first, semantics later)

## Label Taxonomy

ScholarGT v2.0.0 organizes labels into 8 independent dimensions:

### Spatial Labels (21)

WHERE on the page. Applied to regions in PageGT files.

| Label | Description |
|-------|-------------|
| `text_block` | Main body text paragraph |
| `note_area` | Note content area (footnotes, endnotes -- unified) |
| `note_continuation` | Note content continued from a previous page |
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
| `toc_area` | Table of contents area |
| `abstract` | Abstract or summary area |
| `code_block` | Code or monospaced text block |
| `index_area` | Index or concordance region (SFP-5) |
| `unknown` | Unclassified region |

### Semantic Types (9)

WHAT it means. Applied to elements in DocumentGT files.

| Type | Description |
|------|-------------|
| `note` | Unified note model (footnotes, endnotes, marginal notes via `placement`) |
| `citation` | In-text citation reference |
| `bibliography_entry` | Bibliography/references list entry |
| `section` | Document section with hierarchy |
| `sous_rature` | Text under erasure (Derridean concept) |
| `cross_reference` | Internal cross-reference ("see section 3") |
| `marginal_reference` | Marginal reference system (Stephanus, Bekker) |
| `page_number_annotation` | Page number mapping (display to PDF index) |
| `commentary` | Running commentary apparatus (Rashi, Tosafot, editor notes) |

### Formatting Types (9)

HOW text is decorated. Applied to formatting annotations in DocumentGT.

| Type | Description |
|------|-------------|
| `bold` | Bold text |
| `italic` | Italic text |
| `underline` | Underlined text |
| `strikethrough` | Strikethrough text |
| `small_caps` | Small capitals |
| `superscript` | Superscript text |
| `subscript` | Subscript text |
| `monospace` | Monospaced/code text |
| `color` | Colored/highlighted text (SFP-4) |

### Script Variants (6) -- SFP-3

Script distinctions beyond BCP 47. Applied to formatting annotations.

| Variant | Description |
|---------|-------------|
| `square_hebrew` | Standard square Hebrew script |
| `rashi_script` | Rashi (semi-cursive) Hebrew script |
| `nastaliq` | Nastaliq Arabic calligraphic style |
| `naskh` | Naskh Arabic calligraphic style |
| `fraktur` | Fraktur (Blackletter) European script |
| `custom` | Project-specific script variant |

### Citation Formats (5)

How a citation appears in the text.

| Format | Description |
|--------|-------------|
| `parenthetical` | Author-date or abbreviated in parentheses |
| `numeric` | Numbered reference (e.g., [42]) |
| `inline_author` | Author name woven into text |
| `note_based` | Superscript number referencing a footnote/endnote |
| `author_title` | Author and title shorthand |

### Reference Systems (13)

What coordinates locate the referenced passage. Shared by Citation and MarginalReference.

| System | Description |
|--------|-------------|
| `standard` | Standard page/volume reference |
| `stephanus` | Stephanus pagination for Plato |
| `bekker` | Bekker numbers for Aristotle |
| `akademie` | Akademie edition for Kant (A/B pages) |
| `ab_edition` | Generic A/B edition pagination |
| `paragraph` | Paragraph-level reference |
| `sz_pagination` | Sein und Zeit original pagination |
| `diels_kranz` | Diels-Kranz for pre-Socratics |
| `line_number` | Line-level reference |
| `chapter_verse` | Chapter:verse (biblical, Talmudic) |
| `legal` | Legal citation format |
| `catchword` | Catchword/dibbur ha-matchil navigation (SFP-6) |
| `custom` | Project-specific reference system |

### Citation Styles (7)

Document-level citation convention.

| Style | Description |
|-------|-------------|
| `apa` | APA style |
| `chicago_nb` | Chicago Notes-Bibliography |
| `chicago_ad` | Chicago Author-Date |
| `mla` | MLA style |
| `vancouver` | Vancouver (medical/scientific) |
| `turabian` | Turabian style |
| `custom` | Project-specific convention |

### Document Section Types (5)

Document-level annotation categories.

| Type | Description |
|------|-------------|
| `metadata` | Document metadata annotations |
| `toc` | Table of contents structure |
| `front_matter` | Preface, dedication, etc. |
| `back_matter` | Index, appendices, etc. |
| `note_schema` | Note numbering scheme |

### PageQuality (Hybrid Model)

Page-level quality assessment for test stratification. Replaces the old `ScanQuality` and `Difficulty` enums with a richer hybrid model:

- **Categorical**: `overall` (low/medium/high), `is_scan` (boolean)
- **Artifact list**: Specific quality issues (bleed_through, foxing, skew, margin_cropping, water_damage, faded_ink, etc.)
- **Difficulty factors**: Signals affecting annotation difficulty (dense_footnotes, multi_column, mixed_language, complex_typography, etc.)
- **Numeric metrics**: Optional `dpi_estimate`, `contrast_ratio`, `skew_angle`, `noise_level`, `ocr_confidence`

```json
{
  "quality": {
    "overall": "high",
    "is_scan": true,
    "artifacts": ["binding_shadow", "foxing"],
    "difficulty_factors": ["dense_footnotes", "mixed_language"],
    "dpi_estimate": 300,
    "ocr_confidence": 0.92
  }
}
```

## Note Model

The unified `Note` model replaces the old `Footnote` and `Endnote` models. A single Note can represent any type of note by varying its `placement` field:

| Placement | Equivalent to |
|-----------|---------------|
| `page_bottom` | Footnote |
| `end_of_chapter` | Chapter endnote |
| `end_of_book` | Book endnote |
| `margin` | Marginal note |

### Key Fields

- **body_marker** (`LocationRef`): Where the reference marker appears in the body text
- **content_marker** (`LocationRef`, optional): Where the note content begins (important for endnotes where content is distant)
- **content** (`list[ContentSpan]`): Note text spans (may cross pages via `is_continuation`)
- **placement**: Where the note content appears in the document
- **scope**: Numbering reset boundary (page, chapter, section, essay, document)
- **note_source**: Who wrote the note (author, translator, editor)
- **marker_text**: Display text of the marker (e.g., "1", "*", "a")
- **note_schema_id**: Reference to NoteSchema for numbering convention

### NoteSchema

Document-level note numbering conventions. Multiple NoteSchemas can coexist (e.g., translator uses arabic numerals, author uses symbols):

```json
{
  "note_schemas": [
    {
      "schema_id": "translator_footnotes",
      "marker_type": "arabic",
      "reset_boundary": "page",
      "placement": "page_bottom",
      "note_source": "translator"
    },
    {
      "schema_id": "author_footnotes",
      "marker_type": "symbolic",
      "symbol_sequence": ["*", "dagger", "double_dagger"],
      "reset_boundary": "page",
      "placement": "page_bottom",
      "note_source": "author"
    }
  ]
}
```

## Commentary Model

The `Commentary` model represents running commentary apparatus -- philosophical, rabbinic, or editorial commentary that references a specific passage.

### Key Fields

- **source**: Who wrote the commentary (e.g., "Rashi", "editor", "translator")
- **passage_ref**: What passage it comments on (canonical coordinates, e.g., "Gen 1:1", "264a")
- **reference_system**: How it locates the passage (e.g., CATCHWORD, CHAPTER_VERSE, STANDARD)
- **target_location** (`LocationRef`, optional): Precise location in the GT corpus
- **content** (`list[ContentSpan]`): Commentary text (may cross pages)
- **layer**: Commentary layer for multi-layer commentary (e.g., "rashi", "tosafot")

### Example: Talmudic Commentary

```json
{
  "element_type": "commentary",
  "source": "Rashi",
  "passage_ref": "In the beginning",
  "reference_system": "catchword",
  "content": [{"page": 10, "text": "d\"h: In the beginning -- for the sake of Torah"}],
  "layer": "rashi"
}
```

## Layout Registers (SFP-1)

Multi-register documents (Talmud pages, bilingual editions, critical editions, Derrida's *Glas*) have multiple parallel reading streams. `LayoutRegister` provides first-class identity for each stream.

### How It Works

1. Define registers at the document level in `DocumentGT.registers`
2. Link regions to registers via `Region.register_id`
3. Validate cross-references with `validate_page_registers()`

### Fields

- **register_id**: Unique identifier (e.g., "rashi", "main_text", "hegel")
- **name**: Human-readable name
- **author**: Attributed source (optional)
- **language**: BCP 47 language tag (optional)
- **text_direction**: Base direction for this register (ltr/rtl)
- **position_convention**: Layout position (e.g., "left_column", "inner_margin", "central")
- **typeface_convention**: Expected typeface family (e.g., "rashi_script", "square_hebrew")

### Example: Talmud Page

```json
{
  "registers": [
    {
      "register_id": "gemara",
      "name": "Gemara",
      "language": "he-arc",
      "text_direction": "rtl",
      "position_convention": "central",
      "typeface_convention": "square_hebrew"
    },
    {
      "register_id": "rashi",
      "name": "Rashi",
      "author": "Rashi",
      "language": "he",
      "text_direction": "rtl",
      "position_convention": "inner_margin",
      "typeface_convention": "rashi_script"
    },
    {
      "register_id": "tosafot",
      "name": "Tosafot",
      "author": "Tosafot",
      "language": "he",
      "text_direction": "rtl",
      "position_convention": "outer_margin",
      "typeface_convention": "square_hebrew"
    }
  ]
}
```

### Example: Bilingual Edition

```json
{
  "registers": [
    {
      "register_id": "hebrew_original",
      "name": "Hebrew Original",
      "language": "he",
      "text_direction": "rtl",
      "position_convention": "right_column"
    },
    {
      "register_id": "english_translation",
      "name": "English Translation",
      "language": "en",
      "text_direction": "ltr",
      "position_convention": "left_column"
    }
  ]
}
```

## Text Direction (SFP-2)

Explicit text direction at two levels:

- **Region.text_direction**: Direction for a specific region (`ltr`, `rtl`, `bidi`)
- **PageGT.base_direction**: Default direction for the entire page (`ltr`, `rtl`)

### When to Use

- Set `base_direction` on pages that are predominantly RTL or LTR
- Override with `text_direction` on regions that differ from the page default
- Use `bidi` for regions containing both LTR and RTL content
- Derivation from BCP 47 language tags is insufficient because a Hebrew-language page may contain substantial English quotations

## Script Variants (SFP-3)

BCP 47 script subtags cannot distinguish between Rashi script and square Hebrew -- both are "he-Hebr". Similarly, Nastaliq and Naskh are both "ar-Arab". The `ScriptVariant` enum fills this gap.

### When to Use

- Use `script_variant` when two visually distinct scripts share the same BCP 47 code
- Use `language` (BCP 47) for language identification
- They are independent: a span can have `language="he"` and `script_variant="rashi_script"`

### Example

```json
{
  "formatting_type": "italic",
  "page": 10,
  "char_offset": 0,
  "char_length": 50,
  "language": "he",
  "script_variant": "rashi_script"
}
```

## Color Annotation (SFP-4)

The `color` formatting type enables annotation of colored/highlighted text spans with semantic meaning.

### Fields

- **formatting_type**: Set to `"color"`
- **color_value**: CSS color value (e.g., `"#FF0000"`, `"red"`)
- **color_semantic**: Domain-specific meaning (e.g., `"gemara_text"`, `"mishnah_text"`, `"emphasis"`)

### Validation

- `color_value` is recommended but not required when `formatting_type=color` (warns if missing)
- `color_value` on a non-COLOR formatting type also warns (likely misconfigured)
- This supports incremental annotation where color values may be added in a later pass

### Example: Koren Talmud Color Coding

```json
{
  "formatting_type": "color",
  "page": 5,
  "char_offset": 0,
  "char_length": 200,
  "color_value": "#0000FF",
  "color_semantic": "mishnah_text"
}
```

## Cross-Page Relationships

### Region Continuation

Regions can mark content that continues across page boundaries:

```json
{
  "id": "r_fn_cont",
  "label": "note_continuation",
  "is_continuation": true,
  "continues_to_next": false
}
```

### PageDependency

Page-level metadata about cross-page relationships:

```json
{
  "page_dependency": {
    "continues_from_previous": true,
    "continues_to_next": false,
    "unresolved_markers": ["fn_3"],
    "orphan_continuations": ["fn_2_cont"]
  }
}
```

### SectionContextEntry

Makes each page self-describing with its section hierarchy:

```json
{
  "section_context": [
    {
      "section_id": "sec_div1",
      "title": "Division One",
      "level": 0,
      "starts_on_this_page": true,
      "ends_on_this_page": false
    }
  ]
}
```

## Multi-dimensional Labeling

A key design principle: spatial and semantic labels are independent axes. A single region can have BOTH:

```json
{
  "id": "r1",
  "label": "text_block",
  "semantic_labels": ["note"],
  "bbox": {"x0": 0.1, "y0": 0.8, "x1": 0.9, "y1": 0.95},
  "text": "1. This is a note appearing in the text block area."
}
```

This region is spatially a `text_block` (its visual appearance) and semantically a `note` (its meaning). This separation enables:

- Layout detection models to focus on spatial labels
- Semantic extraction pipelines to focus on semantic types
- Joint evaluation of both dimensions

## Configuration Profiles

Not every project needs all 21 spatial labels and 9 semantic types. ScholarGT uses **config-driven profiles** to select which labels are active for a given use case.

### Default Profiles

| Profile | Spatial | Semantic | Formatting | DocSection | CitFmt | RefSys | NotePlc | Script |
|---------|---------|----------|------------|------------|--------|--------|---------|--------|
| `base` | 6 | 2 | 0 | 1 | 0 | 0 | 0 | 0 |
| `extraction-eval` | 21 | 9 | 9 | 5 | 5 | 13 | 4 | 6 |
| `layout-annotation` | 21 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `full-scholarly` | 21 | 9 | 9 | 5 | 5 | 13 | 4 | 6 |

### Using Profiles

```python
from scholargt import load_profile, validate_gt_file
from pathlib import Path

# Load a built-in profile
profile = load_profile("full-scholarly")

# Check if a label is active (8 categories)
if profile.is_label_enabled("spatial", "text_block"):
    print("text_block is active")
if profile.is_label_enabled("reference_system", "stephanus"):
    print("Stephanus references enabled")

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
additional_reference_systems:
  - custom_reference
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
    }
  ]
}
```

Key properties:

- **Per-element**: Each region, element, or page carries its own verification records
- **Multi-reviewer**: Multiple verification records support inter-annotator agreement
- **Confidence is reviewer property**: Confidence reflects how sure the reviewer is, not element quality
- **Agreement score**: Mean confidence across reviewers (future: Cohen's kappa)

An element is considered verified when at least one reviewer's confidence exceeds the profile's threshold (default 0.8, configurable).

## Extensibility

ScholarGT is designed for forward compatibility:

### Extra Fields

All core models use `extra="allow"` in Pydantic configuration. This means:

- New fields in schema v2.1 won't break v2.0 loaders
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

- **4 regions**: section header, two body text blocks, note area (v2.0.0: `note_area` not `footnote_area`)
- **All regions have text**: Required by the extraction-eval profile for CER/WER computation
- **Reading order specified**: Enables reading order accuracy evaluation
- **Hybrid PageQuality**: `overall: "high"`, `ocr_confidence: 0.97`
- **Section context**: Self-describing page with chapter reference
- **Register/direction**: Main text block has `register_id` and `text_direction` (SFP-1, SFP-2)

### layout-annotation-page.json

A dense page with 9 regions demonstrating diverse spatial label types.

- **9 regions**: page header, section header, two text blocks, block quote, note area, page footer, page number, **index area** (SFP-5)
- **All regions have bounding boxes**: Required by layout-annotation for IoU/mAP metrics
- **Hybrid PageQuality**: `overall: "medium"`, `is_scan: true`, `artifacts: ["binding_shadow"]`
- **base_direction**: Page-level text direction set

### full-scholarly-document.json

A DocumentGT file for Heidegger's "Being and Time" showing comprehensive v2.0.0 scholarly annotation.

- **9 semantic elements**: 3 sections (with hierarchy), 1 cross-page note (not footnote), 1 citation (Stephanus), 1 sous rature, 1 bibliography entry, 1 **commentary** (SFP-6 catchword), 1 marginal reference
- **Note model**: Uses `body_marker` (LocationRef), `placement: "page_bottom"`, `note_schema_id` linking to NoteSchema
- **Commentary**: Editor commentary using `reference_system: "catchword"` (SFP-6)
- **LayoutRegister (SFP-1)**: Two registers defined (main_text, marginal_refs)
- **NoteSchema**: Translator footnotes with arabic markers, page-level reset
- **Citation style**: `chicago_nb` at document level
- **Formatting annotations**: Italic, bold, German-language italic (`language: "de"`), COLOR with semantic meaning (SFP-4), Rashi script variant (SFP-3)
- **No relationships section**: Relationships embedded in elements (v2.0.0)
- **Inter-annotator verification**: Two reviewers

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
    PageGT, DocumentGT, Region, BBox, GTElement, LocationRef,
    # Semantic elements
    Note, Commentary, Citation, Section, BibEntry, SousRature,
    # Supporting models
    NoteSchema, BibliographicRecord, ContentSpan, ParsedCitation,
    # Page models
    PageQuality, PageDependency, SectionContextEntry,
    # Document models
    LayoutRegister, DocumentSource, DocumentStructure,
    # Config
    GTProfile, load_profile, list_profiles,
    # Validation
    validate_gt_file, validate_page_gt, validate_document_gt,
    ValidationResult, generate_schema, write_schema,
    # Labels
    SpatialLabel, SemanticType, FormattingType,
    ScriptVariant, CitationFormat, ReferenceSystem,
    CitationStyle, DocumentSectionType,
)
```

## Migration from v1.0.0

v1.0.0 files are **NOT** compatible with v2.0.0. Key changes:

### Removed Models

| v1.0.0 | v2.0.0 Replacement |
|--------|-------------------|
| `Footnote` | `Note` with `placement="page_bottom"` |
| `Endnote` | `Note` with `placement="end_of_book"` |
| `MarkerInfo` | `LocationRef` |
| `FootnoteLink` | `Note.body_marker` (embedded) |
| `CitationBibLink` | `Citation.bib_entry_id` (embedded) |
| `DocumentRelationships` | Removed entirely |
| `CitationType` | `CitationFormat` + `ReferenceSystem` |
| `MarginalRefType` | `ReferenceSystem` |
| `ScanQuality` | `PageQuality.overall` |
| `Difficulty` | `PageQuality.difficulty_factors` |
| `DocumentType` | `DocumentSectionType` |

### Renamed Labels

| v1.0.0 | v2.0.0 |
|--------|--------|
| `footnote_area` | `note_area` |
| `endnote_area` | (removed -- use `note_area`) |
| `footnote_continuation` | `note_continuation` |
| `footnote` (semantic) | `note` |
| `endnote` (semantic) | (removed -- use `note`) |

### Added Models

`Note`, `Commentary`, `NoteSchema`, `BibliographicRecord`, `LocationRef`, `LayoutRegister`, `PageDependency`, `SectionContextEntry`, `ScriptVariant`, `CitationFormat`, `ReferenceSystem`, `CitationStyle`, `DocumentSectionType`

### Field Changes

| Model | v1.0.0 | v2.0.0 |
|-------|--------|--------|
| `Citation` | `citation_type` | `citation_format` + `reference_system` |
| `MarginalReference` | `ref_type` | `reference_system` |
| `BibEntry` | `parsed` (ParsedCitation) | `record` (BibliographicRecord) |
| `PageQuality` | `scan_quality`, `difficulty` | `overall`, `is_scan`, `artifacts`, etc. |
| `DocumentGT` | `relationships` | (removed) |
| `Region` | -- | `register_id`, `text_direction`, `children` |
| `PageGT` | -- | `section_context`, `page_dependency`, `base_direction` |
| `FormattingAnnotation` | -- | `language`, `script_variant`, `color_value`, `color_semantic` |
