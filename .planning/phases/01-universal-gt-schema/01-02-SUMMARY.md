---
phase: 01-universal-gt-schema
plan: 02
subsystem: schema
tags: [pydantic, gt-schema, semantic-elements, discriminated-union, document-gt, formatting, philosophy]

# Dependency graph
requires:
  - phase: 01-universal-gt-schema
    plan: 01
    provides: GTElement base model, BBox, VerificationRecord, label enums, Region, PageGT
provides:
  - 9 semantic element types with discriminated union (SemanticElement)
  - FormattingAnnotation for char-level text decoration tracking
  - DocumentGT model as companion to PageGT for hybrid file scope
  - Cross-page element support via ContentSpan with page references
  - Inter-element relationships (footnote links, citation-bib links)
  - Philosophy-specific elements (SousRature, MarginalReference with Stephanus/Bekker/Akademie)
  - Clean package exports from scholargt.schema (40+ public symbols)
affects: [01-03, 01-04, 02-01, 02-02]

# Tech tracking
tech-stack:
  added: []
  patterns: [discriminated union on element_type field for polymorphic JSON, ContentSpan for cross-page content, relationship models for inter-element links]

key-files:
  created:
    - scholargt/schema/semantic.py
    - scholargt/schema/formatting.py
    - scholargt/schema/document.py
    - tests/test_scholargt/test_semantic_models.py
    - tests/test_scholargt/test_document_models.py
  modified:
    - scholargt/schema/__init__.py

key-decisions:
  - "SemanticElement uses Pydantic discriminated union on element_type Literal field for type-safe polymorphic JSON deserialization"
  - "DocumentGT uses extra=allow (like GTElement/PageGT) for forward compatibility"
  - "ContentSpan.is_continuation flag tracks cross-page footnote/endnote content spanning multiple pages"
  - "DocumentRelationships model explicitly links footnote markers to content and citations to bibliography entries"

patterns-established:
  - "Discriminated union pattern: each element has element_type: Literal['...'] = '...' enabling TypeAdapter(SemanticElement) for polymorphic deserialization"
  - "Hybrid file scope: PageGT (spatial/per-page) + DocumentGT (semantic/per-document) with DocumentGT.elements referencing page indices"
  - "Relationship modeling: explicit link objects (FootnoteLink, CitationBibLink) rather than embedded foreign keys"

requirements-completed: [SCH-01]

# Metrics
duration: 6min
completed: 2026-02-18
---

# Phase 1 Plan 02: Semantic Elements and DocumentGT Summary

**9 semantic element types with discriminated union, FormattingAnnotation with char-level offsets, and DocumentGT document-level model with cross-page elements and inter-element relationships**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-18T20:26:22Z
- **Completed:** 2026-02-18T20:32:29Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Built all 9 semantic element types inheriting GTElement with philosophy-specific models (SousRature, MarginalReference)
- Created SemanticElement discriminated union enabling polymorphic JSON deserialization by element_type field
- Implemented DocumentGT as companion to PageGT for hybrid file scope with cross-page elements, structure, and relationships
- Updated scholargt.schema __init__.py with 40+ clean public exports
- 72 new tests (39 semantic + 33 document) bringing total to 187 across all scholargt tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Create semantic element models with discriminated union and formatting annotations** - `38c7f1b` (feat)
2. **Task 2: Create DocumentGT model and update schema package exports** - `3718ed6` (feat)

## Files Created/Modified
- `scholargt/schema/semantic.py` - 9 semantic element types, supporting models, SemanticElement discriminated union
- `scholargt/schema/formatting.py` - FormattingAnnotation with char-level offsets
- `scholargt/schema/document.py` - DocumentGT, DocumentSource, DocumentStructure, DocumentRelationships, FootnoteLink, CitationBibLink
- `scholargt/schema/__init__.py` - Re-exports all public models for convenient imports
- `tests/test_scholargt/test_semantic_models.py` - 39 tests for all element types, union routing, round-trip JSON
- `tests/test_scholargt/test_document_models.py` - 33 tests including realistic Heidegger Being and Time example

## Decisions Made
- SemanticElement uses Pydantic discriminated union on `element_type` Literal field -- enables TypeAdapter-based polymorphic JSON deserialization without custom deserializers
- DocumentGT uses `extra="allow"` consistent with GTElement and PageGT for forward compatibility
- ContentSpan.is_continuation flag tracks cross-page content (footnotes spanning page boundaries)
- Explicit relationship models (FootnoteLink, CitationBibLink) chosen over embedded foreign keys for cleaner graph traversal

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full schema hierarchy complete: GTElement -> Region/PageGT (spatial) + SemanticElement types/DocumentGT (semantic)
- SemanticElement discriminated union ready for Plan 03's config-driven label selection
- DocumentGT ready for Plan 04's JSON Schema generation and validation
- 187 tests provide comprehensive regression safety for subsequent plans

## Self-Check: PASSED

- All 6 created/modified files verified on disk
- Both task commits verified: 38c7f1b, 3718ed6
- 187 tests pass across all test_scholargt/ test files
- Lint clean (ruff check passes)

---
*Phase: 01-universal-gt-schema*
*Completed: 2026-02-18*
