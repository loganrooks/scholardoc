# Phase 1: Universal GT Schema - Context

**Gathered:** 2026-02-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Design a universal, extensible ground truth annotation schema that unifies ScholarDoc (v3/v4 spatial/extraction focus) and CryptOfCogito (v0.3.1 semantic/philosophical focus) capabilities. Projects select annotation types via configuration. Per-element verification tracking with multi-reviewer support. Schema must accommodate both page-level and document-level ground truth.

</domain>

<decisions>
## Implementation Decisions

### Schema format
- JSON for GT data files (schema-validated, machine-readable, diffable)
- YAML for project config files (human-editable, supports comments)
- Semantic versioning on the schema itself; every GT file references its schema version
- Pydantic models as source of truth, generating JSON Schema for external validation

### Label taxonomy organization
- Multi-dimensional: elements have both spatial (where on page) and semantic (what it means) properties
- A region can be spatially "text_block" and semantically "footnote" — these are independent dimensions
- Labels organized by category with flat leaf names (COCO-style): `layout: [text_block, figure, table, ...]`, `semantic: [footnote, heading, citation, ...]`
- Document-level annotation types alongside page-level types — ToC, metadata, cross-page references are their own category
- Actual label unification (specific ScholarDoc + CryptOfCogito labels) is a research task — this context locks the organizational principle

### GT file scope
- **Deferred to research** — needs analysis of cross-page requirements before deciding
- Known cross-page elements that must be supported: multi-page footnotes, table of contents, document metadata, bibliography spanning pages, footnote-to-endnote linking
- Options under consideration: per-page files with cross-page linking, per-document files, or hybrid (page-level + document-level companion files)
- Researcher should analyze both existing schemas' approaches and recommend

### Configuration profiles
- Layered YAML: base profile + project-level overrides
- Three default profiles per success criteria: `extraction-eval`, `layout-annotation`, `full-scholarly`
- Projects toggle labels at category level or individual label level
- Config drives both validation (what's required) and UI adaptation (what's shown in annotation tool)

### Verification model
- Multi-verifier: array of verification records per element (supports inter-annotator agreement)
- Each record contains: reviewer ID, timestamp, confidence (0.0-1.0), optional notes
- "Verified" = has at least one verification record above a configurable confidence threshold
- Multi-state workflows (draft/reviewed/verified/disputed) are Phase 4 annotation tool UI concerns, not schema concerns — schema records verification events, tool manages workflow
- Multi-verifier chosen because the corpus will include genuinely ambiguous elements (cross-page footnotes, ToC parsing) where inter-annotator agreement matters

### Claude's Discretion
- Pydantic model structure and inheritance patterns
- JSON Schema generation approach
- Config file parsing implementation
- Directory/file naming conventions for GT data
- Test fixtures and example schema structure
- Documentation format and depth

</decisions>

<specifics>
## Specific Ideas

- GT corpus should include strategically selected difficult examples: metadata extraction from front-material, front-material identification, ToC parsing, bibliography parsing, footnote/endnote linking
- Also include representative "normal" examples to prevent regression and overfitting to difficult cases
- Difficulty selection should be measurable through metrics, not just subjective — this informs how evaluation metrics (Phase 3) and corpus creation (Phase 5) are designed
- The user envisions a corpus larger than the Phase 5 minimum of 10-20 pages, with stratified difficulty

</specifics>

<deferred>
## Deferred Ideas

- **Difficulty-based page selection metrics** — metrics that identify which pages are hard *before* GT creation, feeding into corpus selection strategy. Relates to Phase 3 (Experimentation & Evaluation) and Phase 5 (Validation).
- **Corpus expansion beyond Phase 5 minimum** — user envisions a production-scale corpus; Phase 5's 10-20 pages is a design validation starting point, not the end state.
- **Cross-phase linking strategy** — how elements that span pages (footnotes, sections, tables) link across GT files. Depends on file scope decision (deferred to research).

</deferred>

---

*Phase: 01-universal-gt-schema*
*Context gathered: 2026-02-18*
