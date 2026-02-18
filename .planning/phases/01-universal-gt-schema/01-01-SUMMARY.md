---
phase: 01-universal-gt-schema
plan: 01
subsystem: schema
tags: [pydantic, gt-schema, spatial-labels, semantic-labels, verification, bbox]

# Dependency graph
requires:
  - phase: 00-workspace-cleanup
    provides: Clean workspace and git state
provides:
  - GTElement base model with per-element verification tracking
  - BBox normalized bounding box with corners format and to_xywh() helper
  - VerificationRecord with reviewer_id, timestamp, confidence, notes
  - 17 spatial labels, 9 semantic types, 6 formatting, 5 document type enums
  - Citation (7) and marginal reference (4) sublabel enums
  - Region model with independent spatial and semantic label dimensions
  - PageGT model with regions, reading order, quality, schema version
affects: [01-02, 01-03, 01-04, 02-01, 02-02]

# Tech tracking
tech-stack:
  added: [pydantic 2.12.5]
  patterns: [str-Enum for JSON-serializable labels, model_config extra=allow for forward compat, model_validator for constraint checking]

key-files:
  created:
    - scholargt/__init__.py
    - scholargt/py.typed
    - scholargt/schema/__init__.py
    - scholargt/schema/version.py
    - scholargt/schema/labels.py
    - scholargt/schema/base.py
    - scholargt/schema/spatial.py
    - scholargt/schema/page.py
    - tests/test_scholargt/__init__.py
    - tests/test_scholargt/test_schema_base.py
    - tests/test_scholargt/test_page_models.py
  modified:
    - pyproject.toml

key-decisions:
  - "BBox uses [x0,y0,x1,y1] corners format (ScholarDoc convention) with to_xywh() helper for CryptOfCogito compat"
  - "GTElement uses extra=allow for forward compatibility per user decision"
  - "is_verified() takes configurable threshold parameter (default 0.8)"
  - "Reading order validation warns rather than errors (annotation may be in progress)"
  - "scholargt created as independent top-level package, imports nothing from scholardoc"

patterns-established:
  - "str,Enum pattern: all label enums inherit (str, Enum) so they serialize as strings in JSON"
  - "Multi-dimensional labeling: Region.label (spatial) and Region.semantic_labels (semantic) are independent"
  - "Verification tracking: VerificationRecord per element, not per document/page"
  - "Schema versioning: every PageGT file embeds schema_version for migration"

requirements-completed: [SCH-01, SCH-03]

# Metrics
duration: 5min
completed: 2026-02-18
---

# Phase 1 Plan 01: Schema Foundation Summary

**Pydantic-based scholargt package with GTElement verification tracking, 17 spatial + 9 semantic label taxonomy, BBox corners format, and PageGT page-level ground truth model**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-18T20:18:34Z
- **Completed:** 2026-02-18T20:23:27Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- Created scholargt as independent top-level package with PEP 561 type marker
- Built GTElement, BBox, VerificationRecord base models with full Pydantic validation
- Defined complete unified label taxonomy: 17 spatial, 9 semantic, 6 formatting, 5 document type enums plus citation and marginal reference sublabels
- Implemented Region model proving multi-dimensional labeling (spatial + semantic independent)
- Built PageGT model with schema version, regions, reading order, quality metadata

## Task Commits

Each task was committed atomically:

1. **Task 1: Create scholargt package with base models, label enums, and version** - `f0c4e6c` (feat)
2. **Task 2: Create Region and PageGT models with page-level spatial annotations** - `cd59fba` (feat)

## Files Created/Modified
- `scholargt/__init__.py` - Package root with version
- `scholargt/py.typed` - PEP 561 type marker
- `scholargt/schema/__init__.py` - Schema subpackage
- `scholargt/schema/version.py` - SCHEMA_VERSION = "1.0.0" constants
- `scholargt/schema/labels.py` - All label enums (SpatialLabel, SemanticType, FormattingType, DocumentType, ScanQuality, Difficulty, CitationType, MarginalRefType)
- `scholargt/schema/base.py` - GTElement, BBox, VerificationRecord base models
- `scholargt/schema/spatial.py` - Region model with multi-dimensional labels
- `scholargt/schema/page.py` - PageGT and PageQuality models
- `tests/test_scholargt/test_schema_base.py` - 35 tests for base models and enums
- `tests/test_scholargt/test_page_models.py` - 24 tests for Region and PageGT
- `pyproject.toml` - Added pydantic dependency, scholargt to build packages

## Decisions Made
- BBox uses [x0,y0,x1,y1] corners format per research recommendation, with to_xywh() helper for CryptOfCogito compatibility
- GTElement uses `extra="allow"` for forward compatibility (new fields in schema v1.1 won't break v1.0 loaders)
- `is_verified()` takes a configurable threshold parameter (default 0.8) so project profiles can set different thresholds
- PageGT reading order validator uses warnings rather than errors since annotation may be in progress
- scholargt is an independent top-level package that imports nothing from scholardoc

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test assertions for str(Enum) behavior in Python 3.11+**
- **Found during:** Task 1 (test execution)
- **Issue:** `str(SpatialLabel.TEXT_BLOCK)` returns `"SpatialLabel.TEXT_BLOCK"` in Python 3.11+, not `"text_block"`. The `(str, Enum)` pattern makes `==` comparison work but `str()` uses the class-qualified representation.
- **Fix:** Changed test assertions to use `.value` property and `isinstance(enum, str)` instead of `str()` comparison
- **Files modified:** tests/test_scholargt/test_schema_base.py
- **Verification:** All 35 tests pass
- **Committed in:** f0c4e6c (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Minor test assertion fix. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Base models (GTElement, BBox, VerificationRecord) ready for Plan 02's semantic element hierarchy
- Label enums ready for Plan 02's discriminated union element types
- Region and PageGT models ready for Plan 02's document-level GT companion
- Schema version constants ready for Plan 04's JSON Schema generation
- 59 tests provide regression safety for subsequent plans

## Self-Check: PASSED

- All 11 created files verified on disk
- Both task commits verified: f0c4e6c, cd59fba
- 59 tests pass across 2 test files
- Lint clean (ruff check passes)

---
*Phase: 01-universal-gt-schema*
*Completed: 2026-02-18*
