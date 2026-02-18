# Phase 1: Universal GT Schema - Research

**Researched:** 2026-02-18
**Domain:** Ground truth annotation schema design, Pydantic data modeling, config-driven label systems
**Confidence:** HIGH

## Summary

Phase 1 designs a universal, extensible ground truth annotation schema that unifies ScholarDoc's extraction-focused schemas (v3/v4) with CryptOfCogito's spatial/layout-focused schema (v0.3.1). Both existing schemas are well-documented, Pydantic-modeled, and actively used, so the unification is a design challenge rather than a greenfield build.

The key technical decisions are already locked: JSON for GT data, YAML for config, Pydantic as source of truth with JSON Schema generation, multi-dimensional label taxonomy, and multi-verifier per-element tracking. The primary research questions remaining were (a) GT file scope (per-page vs per-document vs hybrid) and (b) actual label unification. This research provides recommendations for both, plus architecture patterns and implementation guidance.

**Primary recommendation:** Use a hybrid file scope with page-level JSON files for spatial/region annotations and a document-level JSON companion file for metadata, cross-page links, ToC, and bibliography. Use Pydantic discriminated unions for the element hierarchy, `model_json_schema()` for external validation artifacts, and `pydantic-settings` with `YamlConfigSettingsSource` for layered configuration.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Schema format
- JSON for GT data files (schema-validated, machine-readable, diffable)
- YAML for project config files (human-editable, supports comments)
- Semantic versioning on the schema itself; every GT file references its schema version
- Pydantic models as source of truth, generating JSON Schema for external validation

#### Label taxonomy organization
- Multi-dimensional: elements have both spatial (where on page) and semantic (what it means) properties
- A region can be spatially "text_block" and semantically "footnote" -- these are independent dimensions
- Labels organized by category with flat leaf names (COCO-style): `layout: [text_block, figure, table, ...]`, `semantic: [footnote, heading, citation, ...]`
- Document-level annotation types alongside page-level types -- ToC, metadata, cross-page references are their own category
- Actual label unification (specific ScholarDoc + CryptOfCogito labels) is a research task -- this context locks the organizational principle

#### GT file scope
- **Deferred to research** -- needs analysis of cross-page requirements before deciding
- Known cross-page elements that must be supported: multi-page footnotes, table of contents, document metadata, bibliography spanning pages, footnote-to-endnote linking
- Options under consideration: per-page files with cross-page linking, per-document files, or hybrid (page-level + document-level companion files)
- Researcher should analyze both existing schemas' approaches and recommend

#### Configuration profiles
- Layered YAML: base profile + project-level overrides
- Three default profiles per success criteria: `extraction-eval`, `layout-annotation`, `full-scholarly`
- Projects toggle labels at category level or individual label level
- Config drives both validation (what's required) and UI adaptation (what's shown in annotation tool)

#### Verification model
- Multi-verifier: array of verification records per element (supports inter-annotator agreement)
- Each record contains: reviewer ID, timestamp, confidence (0.0-1.0), optional notes
- "Verified" = has at least one verification record above a configurable confidence threshold
- Multi-state workflows (draft/reviewed/verified/disputed) are Phase 4 annotation tool UI concerns, not schema concerns -- schema records verification events, tool manages workflow
- Multi-verifier chosen because the corpus will include genuinely ambiguous elements (cross-page footnotes, ToC parsing) where inter-annotator agreement matters

### Claude's Discretion
- Pydantic model structure and inheritance patterns
- JSON Schema generation approach
- Config file parsing implementation
- Directory/file naming conventions for GT data
- Test fixtures and example schema structure
- Documentation format and depth

### Deferred Ideas (OUT OF SCOPE)
- **Difficulty-based page selection metrics** -- metrics that identify which pages are hard *before* GT creation, feeding into corpus selection strategy. Relates to Phase 3 (Experimentation & Evaluation) and Phase 5 (Validation).
- **Corpus expansion beyond Phase 5 minimum** -- user envisions a production-scale corpus; Phase 5's 10-20 pages is a design validation starting point, not the end state.
- **Cross-phase linking strategy** -- how elements that span pages (footnotes, sections, tables) link across GT files. Depends on file scope decision (deferred to research).
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| **SCH-01** | Universal GT schema -- superset of all annotation types, combining spatial hierarchy (Cogito) with semantic richness (ScholarDoc), extensible without restructuring existing GT | Unified label taxonomy (Section: Label Unification), hybrid file scope recommendation, Pydantic model hierarchy with discriminated unions, `extra="allow"` for forward compatibility |
| **SCH-02** | Config-driven label selection -- project initialization selects needed annotation types from universal superset, with sensible defaults per use case | Layered YAML profiles (Section: Configuration Architecture), three default profiles defined, pydantic-settings with YamlConfigSettingsSource for parsing |
| **SCH-03** | Per-element verification tracking -- element-level verification status with reviewer identity, not just document/page-level | VerificationRecord model with multi-verifier array, configurable confidence threshold, verification computed property (Section: Verification Model) |
</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | 2.11.7 (installed) | Schema models, validation, JSON Schema generation | Already project standard; `model_json_schema()` generates JSON Schema from Python types |
| pydantic-settings | 2.x | Layered YAML config loading with `YamlConfigSettingsSource` | Official Pydantic companion for config management; supports file layering, env vars, deep merge |
| PyYAML | 6.0.3 (installed) | YAML parsing for config files | Already in ground-truth extras; pydantic-settings uses it internally |
| jsonschema | 4.25.1 (installed) | Runtime validation of GT data against generated schema | Already available; validates JSON files against Pydantic-generated schema |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.0.0+ (installed) | Test Pydantic models, schema generation, validation | All model and config tests |
| hypothesis | 6.100.0+ (installed) | Property-based testing of schema validation edge cases | Testing model validation boundaries, round-trip serialization |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pydantic-settings | Manual YAML loading with PyYAML | pydantic-settings provides layered sources, type validation, env var fallback out of the box |
| jsonschema for validation | Pydantic model_validate_json() | jsonschema enables validation without Python (CI pipelines, other languages) |
| JSON for GT data | YAML for GT data | JSON is machine-readable, schema-validatable, and has better tooling; YAML's comment support is unnecessary for GT data that's tool-generated |

**Installation:**
```bash
uv add pydantic-settings
```
Note: `pydantic`, `pyyaml`, and `jsonschema` are already available.

---

## Architecture Patterns

### Recommended Project Structure

```
scholargt/                       # New package (or subpackage of scholardoc)
├── __init__.py
├── schema/
│   ├── __init__.py
│   ├── base.py                  # GTElement, BBox, VerificationRecord
│   ├── spatial.py               # Region, SpatialLabel enum
│   ├── semantic.py              # Footnote, Citation, Section, SousRature, etc.
│   ├── document.py              # DocumentGT (document-level annotations)
│   ├── page.py                  # PageGT (page-level annotations)
│   ├── formatting.py            # FormattingAnnotation
│   ├── labels.py                # Label enums and registry
│   └── version.py               # Schema version constants
├── config/
│   ├── __init__.py
│   ├── models.py                # GTProfile, ProjectConfig
│   ├── profiles/                # Default YAML profiles
│   │   ├── base.yaml
│   │   ├── extraction-eval.yaml
│   │   ├── layout-annotation.yaml
│   │   └── full-scholarly.yaml
│   └── loader.py                # Config loading with pydantic-settings
├── validation/
│   ├── __init__.py
│   ├── schema_gen.py            # JSON Schema generation from Pydantic models
│   └── validator.py             # Validate GT files against schema + config
└── generated/
    └── schema.json              # Auto-generated JSON Schema (committed)
```

### GT Data Directory Structure (Recommendation)

```
gt_data/
├── config/
│   └── project.yaml             # Project-specific config (overrides base profile)
├── documents/
│   ├── heidegger_being_and_time/
│   │   ├── document.json        # Document-level: metadata, ToC, cross-page links, bibliography
│   │   └── pages/
│   │       ├── page_0150.json   # Page-level: regions, bboxes, reading order
│   │       ├── page_0151.json
│   │       └── ...
│   └── derrida_writing_and_difference/
│       ├── document.json
│       └── pages/
│           └── ...
└── index.json                   # Corpus index (document IDs, paths, summary stats)
```

### Pattern 1: Discriminated Union Element Hierarchy

**What:** Use Pydantic discriminated unions so a single `elements` array can hold different element types, each distinguished by an `element_type` literal field.

**When to use:** For the semantic elements list in both page-level and document-level GT files. Each element has common fields (id, verifications, tags) but type-specific fields (footnote has marker/content, citation has parsed/raw_text).

**Example:**
```python
from typing import Annotated, Literal, Union
from datetime import datetime
from pydantic import BaseModel, Field

class VerificationRecord(BaseModel):
    """Single verification event for an element."""
    reviewer_id: str
    timestamp: datetime
    confidence: float = Field(ge=0.0, le=1.0)
    notes: str | None = None

class GTElement(BaseModel):
    """Base for all ground truth elements."""
    id: str
    verifications: list[VerificationRecord] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @property
    def is_verified(self) -> bool:
        """Has at least one verification above threshold."""
        return any(v.confidence >= 0.8 for v in self.verifications)

class Footnote(GTElement):
    """A footnote or endnote element."""
    element_type: Literal["footnote"] = "footnote"
    marker: MarkerInfo
    content: list[ContentSpan]
    note_source: Literal["author", "translator", "editor"]
    location: Literal["page_bottom", "endnote", "margin"]

class Citation(GTElement):
    """An inline citation."""
    element_type: Literal["citation"] = "citation"
    raw_text: str
    citation_type: str  # from CitationType enum
    parsed: ParsedCitation | None = None
    bib_entry_id: str | None = None

# Discriminated union for polymorphic deserialization
SemanticElement = Annotated[
    Union[Footnote, Citation, SousRature, Section, BibEntry, CrossReference],
    Field(discriminator="element_type")
]
```

Source: [Pydantic discriminated unions docs](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions)

### Pattern 2: Hybrid File Scope (Research Recommendation)

**What:** Split GT data into page-level files (spatial annotations, regions, bboxes) and a document-level companion file (metadata, cross-page links, ToC, bibliography).

**When to use:** Always. This is the recommended GT file scope.

**Rationale from existing schema analysis:**

| Approach | Used By | Strengths | Weaknesses |
|----------|---------|-----------|------------|
| Per-page only | CryptOfCogito v0.3.1 | Simple files, parallel annotation | Cross-page elements fragile, no natural home for ToC/metadata |
| Per-document only | ScholarDoc SCHEMA.md v1.1.0 | All cross-page elements contained | Large files, poor git diffs, no parallel annotation |
| **Hybrid** | *Recommended* | Clean separation of concerns | Slightly more file management |

**Cross-page element analysis:**

| Element | Scope | Where It Lives (Hybrid) |
|---------|-------|------------------------|
| Region bboxes | Single page | `pages/page_NNNN.json` |
| Reading order | Single page | `pages/page_NNNN.json` |
| Text transcription | Single page | `pages/page_NNNN.json` |
| Footnote markers | Single page (body text) | `pages/page_NNNN.json` (as region annotation) |
| Footnote content | May span pages | `document.json` elements with page refs |
| Footnote-endnote linking | Cross-page | `document.json` relationships |
| ToC | Document-level | `document.json` structure |
| Bibliography | Document-level, multi-page | `document.json` elements |
| Section hierarchy | Document-level | `document.json` structure |
| Document metadata | Document-level | `document.json` metadata |
| Cross-references | Cross-page | `document.json` relationships |

**Example page-level file (`pages/page_0150.json`):**
```json
{
  "$schema_version": "1.0.0",
  "page_index": 150,
  "page_label": "127",
  "dimensions": {"width": 612, "height": 792},
  "regions": [
    {
      "id": "r1",
      "label": "text_block",
      "bbox": [0.10, 0.08, 0.90, 0.72],
      "text": "The 'essence' of Dasein lies in...",
      "text_anchors": ["essence of Dasein"],
      "semantic_labels": ["body_text"]
    },
    {
      "id": "r2",
      "label": "footnote_area",
      "bbox": [0.10, 0.75, 0.90, 0.92],
      "text": "1. See the analysis of care in §41...",
      "text_anchors": ["analysis of care"]
    }
  ],
  "reading_order": ["r1", "r2"],
  "quality": {
    "scan_quality": "high",
    "difficulty": "medium"
  },
  "verifications": [
    {
      "reviewer_id": "annotator_1",
      "timestamp": "2026-02-18T10:00:00Z",
      "confidence": 0.95,
      "notes": "Layout verified, all regions correct"
    }
  ]
}
```

**Example document-level file (`document.json`):**
```json
{
  "$schema_version": "1.0.0",
  "document_id": "heidegger_being_and_time",
  "source": {
    "pdf": "Heidegger_BeingAndTime.pdf",
    "title": "Being and Time",
    "author": "Martin Heidegger",
    "translator": "John Macquarrie & Edward Robinson",
    "year": 1962,
    "document_type": "translation"
  },
  "page_range": [150, 170],
  "elements": [
    {
      "element_type": "footnote",
      "id": "fn_1",
      "marker": {"text": "1", "page": 150, "region_id": "r1", "char_offset": 234},
      "content": [
        {"page": 150, "region_id": "r2", "text": "See the analysis...", "is_continuation": false},
        {"page": 151, "region_id": "r1", "text": "...continued text.", "is_continuation": true}
      ],
      "note_source": "author",
      "location": "page_bottom",
      "verifications": [
        {"reviewer_id": "annotator_1", "timestamp": "2026-02-18T10:30:00Z", "confidence": 0.9}
      ]
    }
  ],
  "structure": {
    "toc": [...],
    "sections": [...],
    "front_matter": {...},
    "back_matter": {...}
  },
  "relationships": {
    "footnote_links": [...],
    "citation_bib_links": [...],
    "cross_refs": [...]
  },
  "config_profile": "full-scholarly"
}
```

### Pattern 3: Config-Driven Validation

**What:** The project configuration profile determines which elements are required, optional, or disabled. Validation adapts accordingly.

**When to use:** When loading or validating GT files. A `layout-annotation` profile should not require semantic elements; a `full-scholarly` profile should require all tiers.

**Example:**
```python
class GTProfile(BaseModel):
    """Configuration profile for GT annotation requirements."""
    name: str
    description: str

    # Category toggles
    spatial_labels: set[str] = {"text_block", "footnote_area", "page_header", "page_footer", "page_number"}
    semantic_types: set[str] = {"footnote", "citation"}
    formatting_types: set[str] = set()
    document_types: set[str] = {"metadata", "toc"}

    # Validation behavior
    require_reading_order: bool = False
    require_text: bool = False
    require_bbox: bool = True
    confidence_threshold: float = 0.8

    def is_label_enabled(self, category: str, label: str) -> bool:
        """Check if a specific label is active in this profile."""
        category_map = {
            "spatial": self.spatial_labels,
            "semantic": self.semantic_types,
            "formatting": self.formatting_types,
            "document": self.document_types,
        }
        labels = category_map.get(category, set())
        return label in labels
```

### Anti-Patterns to Avoid

- **Monolithic schema file:** Do NOT put all GT data for a document in one massive JSON file. The hybrid approach keeps files manageable and git-diffable.
- **Confidence in ground truth:** Ground truth is truth by definition. Confidence belongs on VerificationRecord (how confident the reviewer is), not on the element itself. ScholarDoc SCHEMA.md v1.1.0 already establishes this principle.
- **Schema without version:** Every GT file MUST reference its schema version. Without this, migration is impossible when the schema evolves.
- **Hard-coded labels:** Do NOT hard-code label lists in validation logic. Labels come from the config profile. Adding a new label should require only a config change, not code changes.
- **Mixing spatial and semantic in one enum:** The user decided these are independent dimensions. A region has a spatial label (where it is) AND may have semantic labels (what it means). Do not collapse these into a single flat enum.

---

## Label Unification

### Existing Label Inventory

**ScholarDoc labels (from v3/v4 schema + SCHEMA.md v1.1.0):**

| Category | Labels |
|----------|--------|
| Region types | header, footer, body, footnote_region, footnote_continuation, margin, page_number, figure, caption, table, block_quote, heading |
| Semantic elements | footnote (author/translator/editor), endnote, citation, marginal_ref, section, page_number, bib_entry, sous_rature |
| Citation styles | author_date, numeric, abbreviated, footnote_style, stephanus, bekker, ak_reference |
| Formatting | bold, italic, underline, strikethrough, sous_erasure, small_caps |

**CryptOfCogito labels (from schema v0.3.1 + ground_truth_schema.json):**

| Category | Labels |
|----------|--------|
| Region labels | text, footnote, endnote, page_header, page_footer, page_number, section_header, title, block_quote, list_item, table, figure, caption, formula, marginal_note, bibliography |
| Validation tiers | layout, ocr, markers, citations |
| Page features | text_anchors, reading_order, continues_from/continues_to |

### Unified Taxonomy (Multi-Dimensional, COCO-Style Flat Names)

**Category: `spatial` (layout region types, page-level)**

| Label | ScholarDoc Source | CryptOfCogito Source | Notes |
|-------|-------------------|---------------------|-------|
| `text_block` | body | text | Main content regions |
| `footnote_area` | footnote_region | footnote | Area containing footnote text |
| `endnote_area` | (implicit) | endnote | Area containing endnote text |
| `page_header` | header | page_header | Running headers |
| `page_footer` | footer | page_footer | Running footers |
| `page_number` | page_number | page_number | Page number display |
| `section_header` | heading | section_header | Section/chapter headings |
| `title` | (implicit) | title | Document/chapter titles |
| `block_quote` | block_quote | block_quote | Extended quotations |
| `list_item` | -- | list_item | Numbered/bulleted items |
| `table` | table | table | Tabular content |
| `figure` | figure | figure | Images, diagrams |
| `caption` | caption | caption | Figure/table captions |
| `formula` | -- | formula | Mathematical formulas |
| `marginal_note` | margin | marginal_note | Margin annotations |
| `bibliography_area` | -- | bibliography | Bibliography sections |
| `footnote_continuation` | footnote_continuation | (via continues_from) | Continued footnote from prev page |

**Category: `semantic` (element meaning, may span pages)**

| Label | Source | Notes |
|-------|--------|-------|
| `footnote` | Both | With note_source: author/translator/editor |
| `endnote` | Both | Same structure as footnote, different location |
| `citation` | Both | With citation_type sublabel |
| `bibliography_entry` | ScholarDoc v4 | Parsed bibliography entries |
| `section` | ScholarDoc v1.1 | Hierarchical sections |
| `sous_rature` | ScholarDoc v1.1 | Under-erasure text (philosophy-specific) |
| `cross_reference` | ScholarDoc v4 | "see Chapter 3", "cf. p. 45" |
| `marginal_reference` | ScholarDoc v1.1 | Stephanus, Bekker, Akademie refs |
| `page_number_annotation` | ScholarDoc v1.1 | Semantic page number (arabic/roman/mixed) |

**Category: `formatting` (text decoration)**

| Label | Source | Notes |
|-------|--------|-------|
| `bold` | Both | Bold text |
| `italic` | Both | Italic text |
| `underline` | ScholarDoc | Underlined text |
| `strikethrough` | ScholarDoc | Struck-through text |
| `small_caps` | ScholarDoc | Small capitals |
| `superscript` | CryptOfCogito (implicit) | Superscript markers |

**Category: `document` (document-level annotations)**

| Label | Source | Notes |
|-------|--------|-------|
| `metadata` | Both | Title, author, publisher, etc. |
| `toc` | ScholarDoc v1.1 | Table of contents |
| `front_matter` | ScholarDoc v1.1 | Title page, copyright, dedication |
| `back_matter` | ScholarDoc v1.1 | Index, bibliography section |
| `note_schema` | ScholarDoc v4 | Document-wide marker conventions |

**Category: `quality` (page quality assessment)**

| Label | Source | Notes |
|-------|--------|-------|
| `scan_quality` | ScholarDoc v1.1 | low/medium/high |
| `difficulty` | ScholarDoc v1.1 | easy/medium/hard (for test stratification) |

### Citation Type Sublabels

| Sublabel | Source | Example |
|----------|--------|---------|
| `author_date` | Both | (Heidegger 1927, 45) |
| `numeric` | Both | [1], [23] |
| `abbreviated` | ScholarDoc | (SZ, 41), (CPR A64/B89) |
| `footnote_style` | ScholarDoc | Superscript linking to bibliographic footnote |
| `stephanus` | ScholarDoc | 245a, 245b (Plato) |
| `bekker` | ScholarDoc | 1094a1 (Aristotle) |
| `ak_reference` | ScholarDoc v4 | Ak. 4:421 (Kant) |

### Marginal Reference Sublabels

| Sublabel | Source | Example |
|----------|--------|---------|
| `stephanus` | ScholarDoc | 245a (Plato pagination) |
| `bekker` | ScholarDoc | 1094a1 (Aristotle pagination) |
| `akademie` | ScholarDoc | A64/B89 (Kant A/B edition) |
| `custom` | ScholarDoc | SZ 127 (custom abbreviation system) |

---

## Configuration Architecture

### Layered YAML Config

**Base profile (`profiles/base.yaml`):**
```yaml
# Base configuration -- all profiles inherit from this
schema_version: "1.0.0"

spatial_labels:
  - text_block
  - footnote_area
  - page_header
  - page_footer
  - page_number
  - section_header

semantic_types:
  - footnote
  - citation

formatting_types: []

document_types:
  - metadata

validation:
  require_reading_order: false
  require_text: false
  require_bbox: true
  confidence_threshold: 0.8
```

**Extraction eval profile (`profiles/extraction-eval.yaml`):**
```yaml
# Focused on text extraction quality evaluation
inherits: base

spatial_labels:
  - text_block
  - footnote_area
  - endnote_area
  - page_header
  - page_footer
  - page_number
  - section_header
  - block_quote

semantic_types:
  - footnote
  - endnote
  - citation
  - section
  - bibliography_entry

validation:
  require_text: true          # Need text for CER/WER computation
  require_reading_order: true  # Need reading order for text sequence
```

**Layout annotation profile (`profiles/layout-annotation.yaml`):**
```yaml
# Focused on visual layout detection (IoU, mAP)
inherits: base

spatial_labels:
  - text_block
  - footnote_area
  - endnote_area
  - page_header
  - page_footer
  - page_number
  - section_header
  - title
  - block_quote
  - list_item
  - table
  - figure
  - caption
  - formula
  - marginal_note
  - bibliography_area
  - footnote_continuation

semantic_types: []  # Not needed for layout eval

validation:
  require_bbox: true
  require_reading_order: true
  require_text: false          # Layout doesn't need transcription
```

**Full scholarly profile (`profiles/full-scholarly.yaml`):**
```yaml
# Everything enabled for comprehensive scholarly annotation
inherits: base

spatial_labels:
  - text_block
  - footnote_area
  - endnote_area
  - page_header
  - page_footer
  - page_number
  - section_header
  - title
  - block_quote
  - list_item
  - table
  - figure
  - caption
  - formula
  - marginal_note
  - bibliography_area
  - footnote_continuation

semantic_types:
  - footnote
  - endnote
  - citation
  - bibliography_entry
  - section
  - sous_rature
  - cross_reference
  - marginal_reference
  - page_number_annotation

formatting_types:
  - bold
  - italic
  - underline
  - strikethrough
  - small_caps
  - superscript

document_types:
  - metadata
  - toc
  - front_matter
  - back_matter
  - note_schema

validation:
  require_reading_order: true
  require_text: true
  require_bbox: true
  confidence_threshold: 0.9
```

**Project-level override (`config/project.yaml`):**
```yaml
# Project-specific configuration
profile: full-scholarly       # Start from this profile

# Add project-specific labels
additional_semantic_types:
  - custom_philosophy_label   # Extensibility: new types without schema change

# Disable specific labels not relevant
disabled_labels:
  - formula                   # No formulas in philosophy texts

# Override validation
validation:
  confidence_threshold: 0.85
```

### Config Loading with pydantic-settings

```python
from pydantic_settings import BaseSettings, YamlConfigSettingsSource, PydanticBaseSettingsSource, SettingsConfigDict

class ProjectConfig(BaseSettings):
    """Project-level GT configuration loaded from YAML."""
    model_config = SettingsConfigDict(
        yaml_file=['profiles/base.yaml', 'config/project.yaml'],
        yaml_file_encoding='utf-8',
    )

    profile: str = "base"
    spatial_labels: set[str] = set()
    semantic_types: set[str] = set()
    formatting_types: set[str] = set()
    document_types: set[str] = set()
    validation: ValidationConfig = ValidationConfig()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            YamlConfigSettingsSource(settings_cls),
        )
```

Source: [pydantic-settings YAML docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#yaml)

---

## Verification Model

### Multi-Verifier Design (Locked)

```python
class VerificationRecord(BaseModel):
    """A single verification event for a GT element.

    Multiple records per element support inter-annotator agreement.
    """
    reviewer_id: str = Field(
        description="Unique identifier for the reviewer (e.g., 'human_alice', 'claude_opus')"
    )
    timestamp: datetime = Field(
        description="When the verification occurred"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Reviewer's confidence in the annotation correctness"
    )
    notes: str | None = Field(
        default=None,
        description="Optional notes about the verification"
    )

class GTElement(BaseModel):
    """Base for all ground truth elements with verification tracking."""
    id: str
    verifications: list[VerificationRecord] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    # Forward compatibility
    model_config = ConfigDict(extra="allow")

    def is_verified(self, threshold: float = 0.8) -> bool:
        """Element is verified if at least one reviewer exceeds threshold."""
        return any(v.confidence >= threshold for v in self.verifications)

    def agreement_score(self) -> float | None:
        """Inter-annotator agreement (mean confidence across reviewers)."""
        if not self.verifications:
            return None
        return sum(v.confidence for v in self.verifications) / len(self.verifications)
```

**Key design decisions:**
- `threshold` is a parameter, not hardcoded -- config profile sets the default
- `agreement_score` is a simple mean; Phase 4 (annotation tool) can implement Cohen's kappa or Fleiss' kappa when needed
- `extra="allow"` on GTElement ensures forward compatibility -- new fields in schema v1.1 won't break v1.0 loaders

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON Schema from Python types | Custom JSON Schema generator | `Pydantic.model_json_schema()` | Pydantic generates draft-2020-12 JSON Schema automatically; tested against jsonschema library |
| YAML config loading with layering | Custom YAML merger | `pydantic-settings` with `YamlConfigSettingsSource` | Handles file ordering, deep merge, env var fallback, type validation |
| Schema validation of GT files | Custom validation logic | `jsonschema.validate()` against generated schema | Standard, well-tested, used in CI pipelines across languages |
| Discriminated union deserialization | Custom type dispatching | Pydantic `Field(discriminator=...)` | Handles type routing, error messages, and schema generation automatically |
| Model serialization/deserialization | Custom JSON serializer | Pydantic `model_dump_json()` / `model_validate_json()` | Handles datetime formatting, enum values, nested models, round-trip fidelity |

**Key insight:** Pydantic 2.x is the entire schema infrastructure. The Pydantic models ARE the schema -- JSON Schema, validation, serialization, and documentation all derive from them. Do not maintain a separate JSON Schema file by hand; generate it from the models.

---

## Common Pitfalls

### Pitfall 1: Schema Migration Without Versioning

**What goes wrong:** Schema changes break existing GT files. Adding a required field makes all existing files invalid.
**Why it happens:** No version tracking, no migration path, no backward compatibility strategy.
**How to avoid:**
1. Every GT file has `$schema_version` field
2. New fields are ALWAYS optional with defaults (additive changes only for minor versions)
3. Breaking changes increment major version and require a migration script
4. Pydantic's `extra="allow"` on models ignores unknown fields from newer schemas
**Warning signs:** A GT file fails validation after a code change. Required fields added to a model.

### Pitfall 2: Over-Engineering Label Hierarchy

**What goes wrong:** Deep label hierarchies (3+ levels) with complex inheritance make config profiles confusing and validation logic fragile.
**Why it happens:** Trying to capture every possible relationship in the taxonomy.
**How to avoid:** Keep labels flat within categories (COCO-style). Use tags for ad-hoc grouping. The two dimensions (spatial + semantic) already capture the primary structure. A region can have `label="text_block"` and `semantic_labels=["body_text", "philosophy"]` without needing a deep hierarchy.
**Warning signs:** More than 2 levels of label nesting. Labels that are prefixes of other labels (e.g., `footnote` and `footnote_continuation` should be separate flat labels, not parent-child).

### Pitfall 3: Coupling Schema to Annotation Tool UI

**What goes wrong:** Schema fields designed for UI display rather than data modeling. Fields like `display_order`, `color_code`, `panel_position` leaking into GT data.
**Why it happens:** Phase 1 (schema) and Phase 4 (annotation tool) designed together instead of independently.
**How to avoid:** Schema models GT truth only. UI concerns live in config profiles (which labels to show) and annotation tool code (how to render them). The config profile's `spatial_labels` list tells the UI what to show, but the schema doesn't know about the UI.
**Warning signs:** Fields in GT files that are only meaningful to the annotation tool. Schema changes driven by UI requirements.

### Pitfall 4: Ignoring Existing GT Data Migration

**What goes wrong:** The new universal schema is designed without a plan to migrate existing ScholarDoc GT data (ground_truth/documents/, ground_truth/footnotes/, ground_truth/ocr_quality/).
**Why it happens:** Treating the universal schema as greenfield when there is already GT data.
**How to avoid:** Design the new schema so existing ScholarDoc SCHEMA.md v1.1.0 YAML files can be mechanically converted to the new format. Map existing region types to new spatial labels. Map existing element types to new semantic types. Write a migration script as part of Phase 1.
**Warning signs:** Existing GT data cannot be represented in the new schema. Migration requires human re-annotation.

### Pitfall 5: JSON Schema Too Strict for Extensibility

**What goes wrong:** Generated JSON Schema rejects GT files that have extension fields for project-specific label types.
**Why it happens:** Pydantic generates `"additionalProperties": false` by default on strict models.
**How to avoid:** Use `model_config = ConfigDict(extra="allow")` on GTElement and its subclasses. This generates JSON Schema with `"additionalProperties": true`, allowing extension fields. Validation still enforces required fields and known field types.
**Warning signs:** GT files with project-specific custom fields fail schema validation. Adding a new label type requires regenerating and deploying the JSON Schema.

---

## Code Examples

### JSON Schema Generation from Pydantic Models

```python
import json
from pydantic.json_schema import models_json_schema

# Generate combined schema for all GT model types
_, schema = models_json_schema(
    [
        (PageGT, 'validation'),
        (DocumentGT, 'validation'),
        (GTProfile, 'validation'),
    ],
    title='ScholarGT Schema',
)

# Add custom metadata
schema['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
schema['version'] = '1.0.0'

# Write to generated/schema.json
with open('generated/schema.json', 'w') as f:
    json.dump(schema, f, indent=2)
```

Source: [Pydantic models_json_schema](https://docs.pydantic.dev/latest/concepts/json_schema/#generating-json-schema)

### Validating GT Files Against Generated Schema

```python
import json
import jsonschema

def validate_gt_file(gt_path: str, schema_path: str) -> list[str]:
    """Validate a GT JSON file against the generated schema."""
    with open(schema_path) as f:
        schema = json.load(f)
    with open(gt_path) as f:
        data = json.load(f)

    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(data))
    return [f"{e.json_path}: {e.message}" for e in errors]
```

### Layered Config Loading

```python
import yaml
from pathlib import Path

def load_profile(profile_name: str, project_config_path: Path | None = None) -> GTProfile:
    """Load a GT profile with optional project-level overrides."""
    # Load base profile
    base_path = Path(__file__).parent / "profiles" / "base.yaml"
    with open(base_path) as f:
        config = yaml.safe_load(f)

    # Layer profile on top
    profile_path = Path(__file__).parent / "profiles" / f"{profile_name}.yaml"
    if profile_path.exists():
        with open(profile_path) as f:
            profile_data = yaml.safe_load(f)
            config.update(profile_data)

    # Layer project config on top
    if project_config_path and project_config_path.exists():
        with open(project_config_path) as f:
            project_data = yaml.safe_load(f)
            # Handle additive fields
            if "additional_semantic_types" in project_data:
                config.setdefault("semantic_types", [])
                config["semantic_types"].extend(project_data["additional_semantic_types"])
            if "disabled_labels" in project_data:
                for label in project_data["disabled_labels"]:
                    for key in ["spatial_labels", "semantic_types", "formatting_types"]:
                        if label in config.get(key, []):
                            config[key].remove(label)
            config.update({k: v for k, v in project_data.items()
                          if k not in ("additional_semantic_types", "disabled_labels")})

    return GTProfile.model_validate(config)
```

### Creating Test Fixtures

```python
import pytest
from scholargt.schema.base import VerificationRecord
from scholargt.schema.semantic import Footnote, MarkerInfo, ContentSpan
from scholargt.schema.page import PageGT, Region

@pytest.fixture
def sample_verification():
    return VerificationRecord(
        reviewer_id="test_human",
        timestamp=datetime(2026, 2, 18, 10, 0, 0),
        confidence=0.95,
        notes="Verified by visual inspection",
    )

@pytest.fixture
def sample_page_gt():
    return PageGT(
        schema_version="1.0.0",
        page_index=150,
        page_label="127",
        dimensions={"width": 612, "height": 792},
        regions=[
            Region(
                id="r1",
                label="text_block",
                bbox=[0.10, 0.08, 0.90, 0.72],
                text="Sample body text...",
            ),
        ],
        reading_order=["r1"],
    )

@pytest.fixture
def sample_footnote(sample_verification):
    return Footnote(
        id="fn_1",
        marker=MarkerInfo(text="1", page=150, region_id="r1", char_offset=234),
        content=[ContentSpan(page=150, region_id="r2", text="See the analysis...", is_continuation=False)],
        note_source="author",
        location="page_bottom",
        verifications=[sample_verification],
    )
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| JSON Schema written by hand | Pydantic models generate JSON Schema | Pydantic 2.0 (2023) | Schema always matches validation logic |
| Single GT file per document | Hybrid: page-level + document-level companion | DocLayNet/S2ORC pattern | Better git diffs, parallel annotation |
| Confidence on GT elements | Confidence on verification records only | ScholarDoc SCHEMA.md v1.1.0 | GT is truth; confidence is a reviewer property |
| Fixed label sets in schema | Config-driven label selection | COCO supercategory pattern | Extensible without schema changes |
| pydantic v1 schema_of() | Pydantic v2 model_json_schema() | Pydantic 2.0 | Better JSON Schema output, discriminated unions |

**Deprecated/outdated:**
- `pydantic.schema_of()`: Replaced by `TypeAdapter.json_schema()` in Pydantic 2
- `pydantic.Field(schema_extra=...)`: Replaced by `Field(json_schema_extra=...)` in Pydantic 2
- CryptOfCogito v0.3 continuation format (string page ID): Being replaced by structured PageReference with `expected` flag for unresolved links

---

## Open Questions

1. **Package location: `scholargt/` subpackage or `scholardoc/gt/`?**
   - What we know: ScholarGT is designed as independent from ScholarDoc. The planning ROADMAP says "Planning in ScholarDoc repo" and "Code location decided after design phase."
   - What's unclear: Whether to create a top-level `scholargt/` package in the same repo or nest as `scholardoc/gt/`.
   - Recommendation: Create `scholargt/` as a top-level package in the same repo. It imports nothing from `scholardoc/`. This keeps independence while avoiding a multi-repo setup during design phase. Can be extracted to its own repo later.

2. **Existing GT data migration scope**
   - What we know: There are existing GT files in `ground_truth/documents/` (YAML), `ground_truth/footnotes/` (JSON v3), and `ground_truth/ocr_quality/` (JSON).
   - What's unclear: How much of this data should be migrated to the new schema in Phase 1 vs deferred.
   - Recommendation: Phase 1 should produce a migration script that can convert at least one existing GT file (e.g., `derrida_footnotes_sample.yaml`) to the new format as a proof-of-concept. Full corpus migration is Phase 5 scope.

3. **Bbox format: [x0, y0, x1, y1] vs [x, y, width, height]**
   - What we know: ScholarDoc uses `[x0, y0, x1, y1]` (corners). CryptOfCogito uses `[x, y, width, height]` (origin + size). Both are normalized 0-1.
   - What's unclear: Which to standardize on.
   - Recommendation: Use `[x0, y0, x1, y1]` (corners). It's more common in ML tooling (COCO uses it for their internal representation), avoids negative-width bugs, and is what ScholarDoc already uses. Add a `to_xywh()` helper method on the BBox model for CryptOfCogito compatibility.

---

## Sources

### Primary (HIGH confidence)
- [Pydantic JSON Schema docs](https://docs.pydantic.dev/latest/concepts/json_schema/) - model_json_schema(), models_json_schema(), GenerateJsonSchema customization
- [Pydantic discriminated unions docs](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions) - Field(discriminator=...) pattern
- [pydantic-settings YAML config](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - YamlConfigSettingsSource, layered config
- ScholarDoc v3 schema (`ground_truth/footnotes/schema.json`) - Existing footnote/citation/formatting GT schema
- ScholarDoc v4 schema (`ground_truth/schema_v4_comprehensive.json`) - Unified extraction GT schema
- ScholarDoc SCHEMA.md (`ground_truth/SCHEMA.md`) - v1.1.0 document-centric schema with design principles
- CryptOfCogito v0.3.1 schema (`preprocess/src/preprocess/ground_truth/schema.py`) - Pydantic models for spatial annotations
- CryptOfCogito ADR-007 (`docs/decisions/007-ground-truth-schema.md`) - GT schema design decisions and tier system
- CryptOfCogito ground_truth_schema.json (`preprocess/tests/fixtures/ground_truth_schema.json`) - JSON Schema for layout detection

### Secondary (MEDIUM confidence)
- [COCO annotation format](https://labelformat.com/formats/object-detection/coco/) - Flat category labels with supercategory pattern
- [DocLayNet (arXiv 2022)](https://arxiv.org/abs/2206.01062) - 11-class layout detection schema
- [S2ORC (ACL 2020)](https://aclanthology.org/2020.acl-main.447/) - Layered annotation pattern for scholarly documents
- Prior research: `.planning/research/ground_truth_evaluation.md` - Evaluation metrics and schema design patterns

### Tertiary (LOW confidence)
- None -- all findings verified against primary sources

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All libraries already installed and tested in project
- Architecture: HIGH -- Patterns derived from existing codebase analysis + Pydantic official docs
- Label unification: HIGH -- Complete inventory from both existing schemas analyzed in detail
- Pitfalls: HIGH -- Derived from actual issues in existing ScholarDoc/CryptOfCogito schemas
- File scope recommendation: MEDIUM-HIGH -- Hybrid approach is well-reasoned but novel to this project (neither existing schema uses it)

**Research date:** 2026-02-18
**Valid until:** 2026-04-18 (stable domain, Pydantic 2.x API unlikely to change)
