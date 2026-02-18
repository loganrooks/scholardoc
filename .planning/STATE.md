# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-18)

**Core value:** You cannot improve what you cannot measure. ScholarGT provides the measurement foundation.
**Current focus:** Phase 1: Universal GT Schema -- Plan 01 complete, continuing with Plan 02

## Current Position

Phase: 1 of 5 (Universal GT Schema) -- IN PROGRESS
Plan: 2 of 4 in current phase
Status: Executing
Last activity: 2026-02-18 -- Completed 01-01 (schema foundation: base models, labels, page GT)

Progress: [██░░░░░░░░] 24%

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: 2.3 min
- Total execution time: 0.15 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 00 | 3 | 5 min | 1.7 min |
| 01 | 1 | 5 min | 5.0 min |

**Recent Trend:**
- Last 5 plans: 01-01 (5min), 00-03 (2min), 00-02 (1min), 00-01 (2min)
- Trend: Slightly longer (schema models more complex than cleanup tasks)

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

### Pending Todos

None yet.

### Blockers/Concerns

- Zero verified GT documents exist. Phase 5 validates the design by producing a small corpus.
- Two existing GT schemas (ScholarDoc v3/v4, CryptOfCogito v0.3.1) need unification — Phase 1 core task.
- Annotation tool (Cogito) needs design review before deciding rewrite vs adapt — Phase 4 task.
- Repo location for ScholarGT code undecided — deferred to after design phases.

## Session Continuity

Last session: 2026-02-18
Stopped at: Completed 01-01-PLAN.md (schema foundation)
Resume file: .planning/phases/01-universal-gt-schema/01-01-SUMMARY.md
