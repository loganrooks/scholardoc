---
phase: 01-universal-gt-schema
plan: 03
subsystem: config
tags: [pydantic-settings, yaml-config, profiles, label-selection, config-loader]

# Dependency graph
requires:
  - phase: 01-universal-gt-schema
    plan: 01
    provides: Label enums (SpatialLabel, SemanticType, FormattingType, DocumentType) and SCHEMA_VERSION
provides:
  - GTProfile model defining active spatial labels, semantic types, formatting types, document types
  - ValidationConfig with per-profile require_reading_order, require_text, require_bbox, confidence_threshold
  - ProjectConfig for adding custom labels and disabling existing ones
  - Layered YAML config loader (base -> profile -> project overrides)
  - Three default profiles: extraction-eval, layout-annotation, full-scholarly
  - is_label_enabled() and enabled_labels() methods for config-driven validation
affects: [01-04, 02-01, 02-02, 04-01]

# Tech tracking
tech-stack:
  added: [pydantic-settings 2.13.0, pyyaml 6.0.3 (promoted to core dep)]
  patterns: [layered YAML config with manual merge for additionals/disabled, ConfigDict extra=allow for forward compat, set[str] for label categories]

key-files:
  created:
    - scholargt/config/__init__.py
    - scholargt/config/models.py
    - scholargt/config/loader.py
    - scholargt/config/profiles/base.yaml
    - scholargt/config/profiles/extraction-eval.yaml
    - scholargt/config/profiles/layout-annotation.yaml
    - scholargt/config/profiles/full-scholarly.yaml
    - tests/test_scholargt/test_config.py
  modified:
    - pyproject.toml

key-decisions:
  - "Manual YAML loading with PyYAML instead of pydantic-settings YamlConfigSettingsSource -- custom merge logic (additionals, disabled_labels) goes beyond simple source layering"
  - "pyyaml promoted from ground-truth optional dep to core dep -- config loading is essential, not optional"
  - "GTProfile uses set[str] for label categories -- enables efficient membership testing and set operations for merge/disable"

patterns-established:
  - "Layered YAML config: base.yaml always loaded, named profile overlays, project.yaml adds/removes/overrides"
  - "Profile-driven validation: ValidationConfig varies per profile (layout needs bbox, extraction needs text)"
  - "Label cross-validation: all YAML label strings tested against label enum values to prevent typos"

requirements-completed: [SCH-02]

# Metrics
duration: 4min
completed: 2026-02-18
---

# Phase 1 Plan 03: Config-Driven Label Selection Summary

**Layered YAML config system with GTProfile model, 4 profiles (base + 3 defaults), and project-level label add/remove/override support**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-18T20:26:26Z
- **Completed:** 2026-02-18T20:30:46Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Created GTProfile, ValidationConfig, and ProjectConfig Pydantic models for config-driven annotation
- Implemented layered YAML config loader merging base -> profile -> project with custom add/disable logic
- Built 4 YAML profiles matching research spec: base (6 spatial, 2 semantic), extraction-eval (8/5), layout-annotation (17/0), full-scholarly (17/9/6/5)
- Cross-validated all YAML label strings against label enums (prevents typos from drifting)
- 56 config tests covering all profiles, layering, overrides, error handling, and round-trip serialization

## Task Commits

Each task was committed atomically:

1. **Task 1: Create config models and loader with pydantic-settings** - `6b363ad` (feat)
2. **Task 2: Create default YAML profiles and config tests** - `3b0d427` (feat)

## Files Created/Modified
- `scholargt/config/__init__.py` - Package with re-exports of GTProfile, load_profile, etc.
- `scholargt/config/models.py` - GTProfile, ValidationConfig, ProjectConfig Pydantic models
- `scholargt/config/loader.py` - Layered YAML config loader with base->profile->project merge
- `scholargt/config/profiles/base.yaml` - Base profile: 6 spatial, 2 semantic, standard validation
- `scholargt/config/profiles/extraction-eval.yaml` - Text extraction focus: require_text, require_reading_order
- `scholargt/config/profiles/layout-annotation.yaml` - Layout detection: all 17 spatial, no semantic
- `scholargt/config/profiles/full-scholarly.yaml` - Everything enabled, confidence_threshold=0.9
- `tests/test_scholargt/test_config.py` - 56 tests for profiles, loading, layering, cross-validation
- `pyproject.toml` - Added pydantic-settings and pyyaml to core dependencies

## Decisions Made
- Used manual YAML loading with PyYAML instead of pydantic-settings YamlConfigSettingsSource. The custom merge logic for additionals and disabled_labels goes beyond simple source layering. pydantic-settings is still installed as a core dep (may be useful for future env var config).
- Promoted pyyaml from ground-truth optional dependency to core dependency since config loading is essential functionality.
- GTProfile uses `set[str]` for label categories rather than direct enum references, enabling flexible project-level extension with custom labels not in the enum.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added pyyaml to core dependencies**
- **Found during:** Task 1 (config loader import)
- **Issue:** PyYAML was only in the ground-truth optional dependencies group, but config loading needs it unconditionally. Import of `yaml` failed with ModuleNotFoundError.
- **Fix:** Ran `uv add pyyaml` to add to core dependencies.
- **Files modified:** pyproject.toml, uv.lock
- **Verification:** Config loader imports and loads base.yaml successfully.
- **Committed in:** 6b363ad (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking issue)
**Impact on plan:** Necessary dependency promotion. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Config system ready for Plan 04's JSON Schema generation (GTProfile feeds into schema metadata)
- Profiles ready for Phase 2's extractor configuration (which labels to extract)
- Validation config ready for Phase 4's annotation tool (profile determines UI and validation rules)
- 56 config tests + 98 schema tests = 154 total tests providing regression safety

## Self-Check: PASSED

- All 8 created files verified on disk
- Both task commits verified: 6b363ad, 3b0d427
- 56 config tests pass
- 154 total scholargt tests pass
- Lint clean (ruff check passes)

---
*Phase: 01-universal-gt-schema*
*Completed: 2026-02-18*
