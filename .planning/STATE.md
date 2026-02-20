# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-18)

**Core value:** You cannot improve what you cannot measure. ScholarGT provides the measurement foundation.
**Current focus:** Phase 1.1: Schema Taxonomy Review & Revision -- Executing (Plan 03 complete, 2 remaining)

## Current Position

Phase: 1.1 of 5 (Schema Taxonomy Review & Revision)
Plan: 3 of 5 in current phase
Status: Executing
Last activity: 2026-02-20 -- Plan 03 (Container Models) executed: hybrid PageQuality, PageDependency, SectionContextEntry, LayoutRegister (SFP-1), base_direction (SFP-2), DocumentRelationships removed

Progress: [██████████░] 50%

## Performance Metrics

**Velocity:**
- Total plans completed: 10
- Average duration: 2.8 min
- Total execution time: 0.47 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 00 | 3 | 5 min | 1.7 min |
| 01 | 4 | 19 min | 4.75 min |
| 01.1 | 3 | 7 min | 2.3 min |

**Recent Trend:**
- Last 5 plans: 01.1-03 (2min), 01.1-02 (3min), 01.1-01 (2min), 01-04 (6min), 01-03 (4min)
- Trend: Container model rewrites very fast (2min) -- straightforward field additions/removals with clear plan specs

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Quick-2]: Non-conservative gap analysis v2 identifies 9 Partial-Structural gaps with 7 Structural Fix Proposals
- [Quick-2]: LayoutRegister (SFP-1) is highest priority -- 57% of corpus uses multi-register layouts
- [Quick-2]: Text direction (SFP-2) must be explicit -- 33% of corpus is RTL, derivation from BCP 47 is insufficient
- [Quick-2]: ScriptVariant (SFP-3) needed for Rashi vs square Hebrew -- 1,300 pages, BCP 47 cannot distinguish
- [Quick-2]: All SFPs can be absorbed by existing Phase 1.1 plans with ~41 lines of additions
- [SFP Decision]: Adopted Tier 1+2 (SFP-1 through SFP-6): LayoutRegister, text_direction, ScriptVariant, COLOR, INDEX_AREA, CATCHWORD. Deferred SFP-7 (content_layer, 4 pages).
- [Replan]: Phase 1.1 replanned from scratch incorporating all 6 adopted SFPs. Research re-run. Verification passed all 7 dimensions.
- [Quick-1]: Phase 1.1 gap analysis confirms zero blocking gaps -- all 85 structural phenomena representable in v2.0.0 schema
- [Quick-1]: Phase 1.2 conditional -- beneficial for text_direction, script_variant, register_identity but not required
- [Quick-1]: 5 degraded gaps all covered by GTElement.extra="allow" mechanism (by design)
- [Roadmap revision]: ScholarGT is independent of ScholarDoc — GT platform serves multiple consumers
- [Roadmap revision]: Design-heavy milestone — get architecture right before producing large GT corpus
- [Roadmap revision]: Config-driven label selection from universal superset schema
- [Roadmap revision]: Pluggable extractors + built-in lightweight — extractor interface with configs for A/B comparison
- [Roadmap revision]: Experiments at both pipeline and component levels
- [Roadmap revision]: Annotation tool: review Cogito tool, possible rewrite (design during Phase 4 planning)
- [Roadmap revision]: Planning stays in ScholarDoc repo; code location decided after design
- [Roadmap revision]: ScholarDoc-specific improvements (IR, Writers, re-OCR, monorepo) deferred to milestone 2
- [00-01]: Ground truth docs committed as prior-art reference for schema, testing, and annotation phases
- [00-01]: MANIFEST.md pattern established for documenting local-only gitignored corpus files
- [00-03]: Used merge commit refs for archive tags (7 remote branches already deleted via GitHub PRs)
- [00-03]: archive/* tag convention established for preserving deleted branch history
- [00-03]: feature/ocr-integration tag preserves 8 pre-squash commits not in main's linear history
- [01-01]: BBox uses [x0,y0,x1,y1] corners format with to_xywh() helper for CryptOfCogito compat
- [01-01]: GTElement uses extra="allow" for forward compatibility
- [01-01]: scholargt created as independent top-level package (imports nothing from scholardoc)
- [01-01]: Reading order validation warns rather than errors (in-progress annotation support)
- [01-03]: Manual YAML loading with PyYAML instead of pydantic-settings YamlConfigSettingsSource (custom merge logic needed)
- [01-03]: pyyaml promoted from optional to core dep (config loading is essential)
- [01-03]: GTProfile uses set[str] for label categories (enables custom project labels beyond enum)
- [01-02]: SemanticElement uses Pydantic discriminated union on element_type Literal field for polymorphic JSON deserialization
- [01-02]: DocumentGT uses extra=allow for forward compatibility, consistent with GTElement and PageGT
- [01-02]: Explicit relationship models (FootnoteLink, CitationBibLink) for inter-element links rather than embedded foreign keys
- [01-02]: ContentSpan.is_continuation flag for cross-page footnote/endnote content spanning page boundaries
- [01-04]: jsonschema library for runtime JSON Schema validation; Pydantic model_validate as fallback
- [01-04]: Validation separates errors (invalid) from warnings (informational) for extensibility
- [01-04]: Auto-detection of page vs document GT via discriminating keys (regions vs document_id)
- [01-04]: Generated schema.json committed to repo for IDE autocompletion and CI validation
- [01.1-01]: LocationRef uses Optional[int] for char_offset/char_length (not all references need character-level precision)
- [01.1-01]: NOTE_AREA/NOTE_CONTINUATION unify footnote/endnote spatial labels (position-independent)
- [01.1-01]: ReferenceSystem shared by Citation and MarginalReference (eliminates MarginalRefType duplication)
- [01.1-01]: DocumentType renamed to DocumentSectionType (avoid collision with DocumentSource.document_type Literal)
- [01.1-02]: Note unifies Footnote+Endnote via placement field (page_bottom, end_of_chapter, end_of_book, margin)
- [01.1-02]: Commentary uses shared ReferenceSystem for passage location (consistent with Citation, MarginalReference)
- [01.1-02]: BibEntry.record (BibliographicRecord) replaces BibEntry.parsed (ParsedCitation) for richer bibliography fields
- [01.1-02]: FormattingAnnotation color validator warns rather than errors (supports incremental annotation)
- [01.1-02]: Region.children uses self-referencing list[Region] with forward reference for sub-region nesting
- [01.1-03]: PageQuality is hybrid model -- categorical overall + is_scan + artifact/difficulty lists + 5 numeric metrics (replaces ScanQuality/Difficulty enums)
- [01.1-03]: LayoutRegister (SFP-1) stores register_id, name, author, language, text_direction, position_convention, typeface_convention
- [01.1-03]: DocumentRelationships eliminated -- relationships now embedded in elements (Note.body_marker, Citation.bib_entry_id)
- [01.1-03]: NoteSchema validator warns on duplicate schema_id (not error) for incremental annotation

### Roadmap Evolution

- Phase 1.1 inserted after Phase 1: Schema Taxonomy Review & Revision (URGENT) — SpatialLabel conflates visual position with content type, CitationType mixes format/reference-system/standard, ScanQuality loses information as enum, taxonomy not organized by downstream evaluation task

### Pending Todos

None yet.

### Blockers/Concerns

- Zero verified GT documents exist. Phase 5 validates the design by producing a small corpus.
- ~~Two existing GT schemas (ScholarDoc v3/v4, CryptOfCogito v0.3.1) need unification~~ -- RESOLVED: Phase 1 complete, unified schema with 17 spatial + 9 semantic labels, config-driven profiles.
- Annotation tool (Cogito) needs design review before deciding rewrite vs adapt — Phase 4 task.
- Repo location for ScholarGT code undecided — deferred to after design phases.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 1 | Gap analysis of Phase 1.1 schema vs structural phenomena | 2026-02-19 | 358691d | [1-gap-analysis](.planning/quick/1-gap-analysis/) |
| 2 | Non-conservative gap analysis v2: structural schema review | 2026-02-19 | 08dd742 | [2-non-conservative-gap-analysis-v2-structu](.planning/quick/2-non-conservative-gap-analysis-v2-structu/) |

## Session Continuity

Last session: 2026-02-20
Stopped at: Completed 01.1-03-PLAN.md (Container Models). Continue with 01.1-04-PLAN.md.
Resume file: none -- /gsd:execute-phase 1.1
