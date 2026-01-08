# Ground Truth Schema Specification

**Version**: 1.1.0
**Created**: 2026-01-07
**Updated**: 2026-01-07
**Status**: Draft

## Overview

This schema defines the structure for ground truth annotations used to validate ScholarDoc's extraction pipeline. The schema is hierarchical and document-centric, with elements that can span multiple pages.

**Important Distinction**: Ground truth is the *correct answer* - it contains no confidence scores or uncertainty. Confidence/probability values belong to *pipeline output*, not ground truth. Once a human verifies an annotation, it becomes truth by definition.

## Design Principles

1. **Document-scoped elements** - Footnotes, citations, sections exist at document level with page references
2. **Multi-page support** - Elements can span pages (continuation footnotes, sections)
3. **Tag-based indexing** - Documents and elements tagged for flexible querying
4. **Three-state verification** - `pending` → `annotated` → `verified`
5. **Raw text preservation** - Store text as-is, normalization is pipeline concern
6. **No confidence in ground truth** - Ground truth is truth; confidence belongs to pipeline output only

## Directory Structure

```
ground_truth/
├── SCHEMA.md                 # This file
├── index.yaml                # Quick lookup index
├── scripts/
│   ├── generate_draft.py     # Auto-generate from PDF
│   ├── visualize.py          # Render for review
│   └── validate.py           # Schema validation
└── documents/
    ├── heidegger_being_and_time.yaml
    ├── plato_republic.yaml
    └── ...
```

## Index File

`ground_truth/index.yaml` - Fast lookup without loading full documents.

```yaml
schema_version: "1.0.0"
last_updated: "2026-01-07"

documents:
  - id: heidegger_bt
    path: documents/heidegger_being_and_time.yaml
    source_pdf: Heidegger_BeingAndTime.pdf
    page_range: [150, 170]
    doc_tags: [has_footnotes, translation, has_greek]
    element_tags: [multi_page_footnote, translator_note]
    annotation_summary:
      footnotes: {state: verified, count: 23}
      citations: {state: annotated, count: 8}
      marginal_refs: {state: verified, count: 0}

  - id: plato_republic
    path: documents/plato_republic.yaml
    source_pdf: "Plato Complete Works.pdf"
    page_range: [50, 80]
    doc_tags: [has_stephanus_refs, has_footnotes]
    element_tags: [stephanus]
    annotation_summary:
      footnotes: {state: annotated, count: 15}
      marginal_refs: {state: annotated, count: 45}
```

## Document Schema

### Top-Level Structure

```yaml
# ground_truth/documents/{document_id}.yaml

schema_version: "1.0.0"

# ══════════════════════════════════════════════════════════════
# SOURCE IDENTIFICATION
# ══════════════════════════════════════════════════════════════
source:
  pdf: "Heidegger_BeingAndTime.pdf"        # Filename in sample_pdfs/
  page_range: [150, 170]                    # 0-indexed page range annotated
  document_type: translation                # monograph | edited_volume | translation | anthology

  # Optional bibliographic info
  title: "Being and Time"
  author: "Martin Heidegger"
  translator: "John Macquarrie & Edward Robinson"
  publisher: "Harper & Row"
  year: 1962

# ══════════════════════════════════════════════════════════════
# ANNOTATION STATUS (per element type)
# ══════════════════════════════════════════════════════════════
annotation_status:
  footnotes:
    state: verified              # pending | annotated | verified
    count: 23                    # Number found (null if pending)
    annotator: model_assisted    # human | model_assisted | auto
    verified_by: human           # null if not verified
    verified_date: "2026-01-07"

  endnotes:
    state: verified
    count: 0                     # Confirmed: none in this range
    annotator: human
    verified_by: human

  citations:
    state: annotated             # Done but not verified
    count: 8
    annotator: model_assisted
    verified_by: null

  marginal_refs:
    state: pending               # Not yet annotated
    count: null
    annotator: null

  sous_rature:
    state: pending               # Not yet annotated
    count: null
    annotator: null

# ══════════════════════════════════════════════════════════════
# PAGES (Layout + Raw Text)
# ══════════════════════════════════════════════════════════════
pages:
  - index: 150                   # 0-indexed PDF page
    label: "127"                 # Printed page number
    dimensions:                  # PDF points (72 per inch)
      width: 612
      height: 792
    tags: [complex_layout, has_greek]
    quality:
      scan_quality: high         # low | medium | high (human assessment of source)
      difficulty: medium         # easy | medium | hard (for test stratification)

    regions:
      - id: header_1
        type: header
        bbox: [0.10, 0.02, 0.90, 0.05]    # Normalized [x0, y0, x1, y1]
        text: "BEING AND TIME"

      - id: body_1
        type: body
        bbox: [0.10, 0.08, 0.90, 0.72]
        text: |
          The 'essence' of Dasein lies in its existence. Accordingly those
          characteristics which can be exhibited in this entity are not
          'properties' present-at-hand of some entity which 'looks' so and so...
        special_chars:
          - lang: de
            text: "Dasein"
          - lang: el
            text: "οὐσία"

      - id: fn_region_1
        type: footnote_region
        bbox: [0.10, 0.75, 0.90, 0.92]
        text: |
          1. See the analysis of care in §41 where Heidegger develops...
          2. The German 'Geworfenheit' is difficult to translate...

      - id: page_num_1
        type: page_number
        bbox: [0.48, 0.96, 0.52, 0.98]
        text: "127"

# ══════════════════════════════════════════════════════════════
# ELEMENTS (Document-Scoped Semantic Units)
# ══════════════════════════════════════════════════════════════
elements:

  # ─────────────────────────────────────────────────────────────
  # FOOTNOTES
  # ─────────────────────────────────────────────────────────────
  footnotes:
    - id: fn_1
      marker:
        text: "1"
        page: 150
        region_id: body_1
        char_offset: 234           # Character offset within region text
      content:
        - page: 150
          region_id: fn_region_1
          text: "See the analysis of care in §41 where Heidegger develops the threefold structure..."
          char_range: [0, 156]     # Within region text
          is_continuation: false
      pages: [150]                 # Quick lookup for multi-page
      note_type: author            # author | translator | editor
      tags: []

    - id: fn_2
      marker:
        text: "2"
        page: 150
        region_id: body_1
        char_offset: 567
      content:
        - page: 150
          region_id: fn_region_1
          text: "The German 'Geworfenheit' is difficult to translate..."
          char_range: [157, 298]
          is_continuation: false
        - page: 151
          region_id: fn_cont_1
          text: "...and has been variously rendered as 'thrownness' or 'facticity'."
          char_range: [0, 67]
          is_continuation: true
      pages: [150, 151]
      note_type: translator
      tags: [multi_page, de]

  # ─────────────────────────────────────────────────────────────
  # ENDNOTES
  # ─────────────────────────────────────────────────────────────
  endnotes: []   # None in this document range

  # ─────────────────────────────────────────────────────────────
  # CITATIONS
  # ─────────────────────────────────────────────────────────────
  citations:
    - id: cite_1
      raw: "(SZ, 41)"
      page: 150
      region_id: body_1
      char_offset: 789
      parsed:
        style: abbreviated         # author_date | numeric | abbreviated
        work_abbrev: "SZ"
        section: "41"
        pages: null
      bib_entry_id: sein_und_zeit  # Link to bibliography (if exists)
      tags: []

    - id: cite_2
      raw: "(Heidegger 1927, 45)"
      page: 152
      region_id: body_1
      char_offset: 123
      parsed:
        style: author_date
        authors: ["Heidegger"]
        year: 1927
        pages: "45"
      bib_entry_id: sein_und_zeit
      tags: []

  # ─────────────────────────────────────────────────────────────
  # MARGINAL REFERENCES
  # ─────────────────────────────────────────────────────────────
  marginal_refs:
    - id: marg_1
      system: custom               # stephanus | bekker | akademie | custom
      markers:
        - text: "SZ 127"
          page: 150
          region_id: margin_1      # If separate margin region
          bbox: [0.02, 0.08, 0.08, 0.10]  # Or direct bbox
      body_range:
        start: {page: 150, region_id: body_1, char_offset: 0}
        end: {page: 150, region_id: body_1, char_offset: 1200}
      tags: []

  # ─────────────────────────────────────────────────────────────
  # SECTIONS
  # ─────────────────────────────────────────────────────────────
  sections:
    - id: sec_41
      title: "§41. Dasein's Being as Care"
      level: 2                     # 1=part, 2=chapter, 3=section, 4=subsection
      page_start: 148
      page_end: 165
      parent_id: null              # For nested sections
      tags: []

  # ─────────────────────────────────────────────────────────────
  # PAGE NUMBERS
  # ─────────────────────────────────────────────────────────────
  page_numbers:
    - page: 150
      displayed: "127"
      normalized: 127
      format: arabic               # arabic | roman_lower | roman_upper
      position: header             # header | footer | margin

    - page: 151
      displayed: "128"
      normalized: 128
      format: arabic
      position: header
      alternate:                   # For A/B pagination (Kant CPR)
        - system: akademie
          value: "A64"
        - system: akademie
          value: "B89"

  # ─────────────────────────────────────────────────────────────
  # BIBLIOGRAPHY ENTRIES
  # ─────────────────────────────────────────────────────────────
  bib_entries:
    - id: sein_und_zeit
      raw: "Heidegger, M. Sein und Zeit. Tübingen: Niemeyer, 1927."
      page: null                   # If from abbreviations list, not bibliography
      parsed:
        authors: ["Heidegger, Martin"]
        title: "Sein und Zeit"
        year: 1927
        publisher: "Niemeyer"
        place: "Tübingen"
      tags: []

  # ─────────────────────────────────────────────────────────────
  # SOUS RATURE (Under Erasure)
  # ─────────────────────────────────────────────────────────────
  # Words crossed out but still legible - a key convention in
  # continental philosophy (Derrida, Heidegger). Visually appears
  # as strikethrough: B̶e̶i̶n̶g̶, p̶r̶e̶s̶e̶n̶c̶e̶
  # Semantically significant - it's a philosophical move, not an error.
  sous_rature:
    - id: sr_1
      text: "Being"                # The word under erasure
      page: 150
      region_id: body_1
      char_offset: 45              # Position in region text
      char_length: 5               # Length of crossed-out text
      display_form: "B̶e̶i̶n̶g̶"       # How it appears with strikethrough (optional)
      context: "the question of B̶e̶i̶n̶g̶ must be posed anew"  # Surrounding text
      tags: []

    - id: sr_2
      text: "presence"
      page: 152
      region_id: body_1
      char_offset: 234
      char_length: 8
      display_form: "p̶r̶e̶s̶e̶n̶c̶e̶"
      context: "the metaphysics of p̶r̶e̶s̶e̶n̶c̶e̶"
      tags: [derrida_convention]

# ══════════════════════════════════════════════════════════════
# RELATIONSHIPS (Cross-Element Links)
# ══════════════════════════════════════════════════════════════
relationships:
  # Footnote marker → content (implicit in footnote structure, but explicit here for validation)
  footnote_links:
    - marker_id: fn_1.marker
      content_ids: [fn_1.content.0]
    - marker_id: fn_2.marker
      content_ids: [fn_2.content.0, fn_2.content.1]  # Multi-page

  # Citation → bibliography entry
  citation_bib_links:
    - citation_id: cite_1
      bib_entry_id: sein_und_zeit
    - citation_id: cite_2
      bib_entry_id: sein_und_zeit

  # Cross-references within text
  cross_refs:
    - id: xref_1
      source:
        page: 155
        region_id: body_1
        text: "see §12 above"
        char_offset: 890
      target:
        type: section
        section_id: sec_12
        page: 78

# ══════════════════════════════════════════════════════════════
# DOCUMENT STRUCTURE
# ══════════════════════════════════════════════════════════════
structure:
  toc:
    - title: "Division One: Preparatory Fundamental Analysis of Dasein"
      page: 41
      section_id: div_1
      children:
        - title: "§12. A Preliminary Sketch of Being-in-the-World"
          page: 78
          section_id: sec_12
        - title: "§41. Dasein's Being as Care"
          page: 148
          section_id: sec_41

  front_matter:
    pages: [0, 1, 2, 3, 4, 5]
    elements:
      - type: title_page
        page: 0
      - type: copyright
        page: 1
      - type: dedication
        page: 2
      - type: toc
        pages: [3, 4, 5]
      - type: preface
        pages: [6, 7, 8]

  back_matter:
    pages: [450, 451, 452, 453, 454, 455]
    elements:
      - type: index
        pages: [450, 451, 452, 453, 454, 455]
      - type: bibliography
        pages: []  # Uses abbreviations, no formal bibliography

# ══════════════════════════════════════════════════════════════
# METADATA
# ══════════════════════════════════════════════════════════════
metadata:
  tags: [has_footnotes, translation, has_greek, has_german, complex_notes]
  created: "2026-01-07"
  last_modified: "2026-01-07"
  notes: |
    Macquarrie & Robinson translation. German terms preserved throughout.
    Marginal references use SZ page numbers from original German edition.
```

## Field Definitions

### Region Types

| Type | Description |
|------|-------------|
| `header` | Running header (book title, chapter title) |
| `footer` | Running footer |
| `body` | Main text content |
| `footnote_region` | Area containing footnotes |
| `footnote_continuation` | Footnote continued from previous page |
| `margin` | Marginal notes or references |
| `page_number` | Page number display |
| `figure` | Image or diagram |
| `caption` | Figure/table caption |
| `table` | Tabular content |
| `block_quote` | Extended quotation |
| `heading` | Section/chapter heading |

### Note Types

| Type | Description |
|------|-------------|
| `author` | Original author's note |
| `translator` | Translator's note (often marked [TN]) |
| `editor` | Editor's note (often marked [Ed.]) |

### Citation Styles

| Style | Example |
|-------|---------|
| `author_date` | (Heidegger 1927, 45) |
| `numeric` | [1], [23] |
| `abbreviated` | (SZ, 41), (CPR A64/B89) |
| `footnote_style` | Superscript linking to bibliographic footnote |

### Marginal Reference Systems

| System | Description | Example |
|--------|-------------|---------|
| `stephanus` | Plato editions | 245a, 245b |
| `bekker` | Aristotle editions | 1094a1, 1094b15 |
| `akademie` | Kant editions | A64/B89, Ak. 4:421 |
| `custom` | Other systems | SZ 127 |

### Sous Rature (Under Erasure)

A typographical convention in continental philosophy where a word is crossed out but remains legible. This is a deliberate philosophical gesture, not a correction.

| Field | Description |
|-------|-------------|
| `text` | The underlying word without strikethrough |
| `display_form` | The word with strikethrough characters (optional) |
| `char_offset` | Position in region text |
| `char_length` | Length of crossed-out text |
| `context` | Surrounding text for disambiguation |

Common in works by Derrida and Heidegger. Examples: B̶e̶i̶n̶g̶, p̶r̶e̶s̶e̶n̶c̶e̶, s̶i̶g̶n̶

### Page Quality

| Field | Description |
|-------|-------------|
| `scan_quality` | Human assessment of source scan: `low` \| `medium` \| `high` |
| `difficulty` | Extraction difficulty for test stratification: `easy` \| `medium` \| `hard` |

**Note**: Ground truth contains NO confidence scores. Confidence belongs to pipeline output only.

### Language Codes (ISO 639-1)

| Code | Language |
|------|----------|
| `el` | Greek |
| `de` | German |
| `la` | Latin |
| `fr` | French |
| `he` | Hebrew |

### Annotation States

| State | Meaning |
|-------|---------|
| `pending` | Not yet annotated; count is null |
| `annotated` | Annotated but not human-verified |
| `verified` | Human-verified as correct |

### Annotator Types

| Type | Meaning |
|------|---------|
| `auto` | Fully automated (no human review) |
| `model_assisted` | Auto-generated, human-corrected |
| `human` | Manually annotated |

## Bounding Box Format

Coordinates are normalized to 0-1 range:
- `[x0, y0, x1, y1]` where (x0, y0) is top-left, (x1, y1) is bottom-right
- Origin is top-left of page
- Convert to pixels: `pixel_x = norm_x * page_width_points * dpi / 72`

## Validation Rules

1. **Referential integrity**
   - Every `region_id` reference must exist in `pages[].regions`
   - Every `section_id` in relationships must exist in `elements.sections`
   - Every `bib_entry_id` must exist in `elements.bib_entries`

2. **Consistency**
   - `footnotes[].pages` must match pages referenced in `content[]`
   - `annotation_status.*.count` must match actual element count

3. **Completeness**
   - If `state: verified`, all required fields must be populated
   - Multi-page elements must have `is_continuation: true` on subsequent parts

4. **Coordinates**
   - All bbox values must be in [0, 1] range
   - x0 < x1 and y0 < y1

## Changelog

- **1.1.0** (2026-01-07): Added sous_rature element, clarified ground truth vs pipeline output
  - Added `sous_rature` element type for under-erasure text (Derrida/Heidegger convention)
  - Removed `ocr_confidence` from page quality (confidence belongs to pipeline, not ground truth)
  - Added `difficulty` field for test stratification
  - Renamed `scan` to `scan_quality` for clarity
  - Added design principle #6: No confidence in ground truth
- **1.0.0** (2026-01-07): Initial schema specification
