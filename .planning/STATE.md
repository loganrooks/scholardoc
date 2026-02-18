# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-18)

**Core value:** You cannot improve what you cannot measure. ScholarGT provides the measurement foundation.
**Current focus:** Phase 1: Universal GT Schema -- COMPLETE (all 4 plans done)

## Current Position

Phase: 1 of 5 (Universal GT Schema) -- COMPLETE
Plan: 4 of 4 in current phase -- ALL COMPLETE
Status: Phase complete, ready for Phase 2 planning
Last activity: 2026-02-18 -- Completed 01-04 (validation, examples, documentation)

Progress: [████████░░] 40%

## Performance Metrics

**Velocity:**
- Total plans completed: 7
- Average duration: 3.0 min
- Total execution time: 0.35 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 00 | 3 | 5 min | 1.7 min |
| 01 | 4 | 19 min | 4.75 min |

**Recent Trend:**
- Last 5 plans: 01-04 (6min), 01-03 (4min), 01-02 (4min), 01-01 (5min), 00-03 (2min)
- Trend: Consistent ~5min for schema plans, 01-04 slightly longer due to examples + documentation

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

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

### Pending Todos

None yet.

### Blockers/Concerns

- Zero verified GT documents exist. Phase 5 validates the design by producing a small corpus.
- ~~Two existing GT schemas (ScholarDoc v3/v4, CryptOfCogito v0.3.1) need unification~~ -- RESOLVED: Phase 1 complete, unified schema with 17 spatial + 9 semantic labels, config-driven profiles.
- Annotation tool (Cogito) needs design review before deciding rewrite vs adapt — Phase 4 task.
- Repo location for ScholarGT code undecided — deferred to after design phases.

## Session Continuity

Last session: 2026-02-18
Stopped at: Completed 01-04-PLAN.md (validation, examples, documentation) -- Phase 1 COMPLETE
Resume file: .planning/phases/01-universal-gt-schema/01-04-SUMMARY.md
