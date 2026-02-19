---
phase: quick-2
plan: 01
subsystem: schema-analysis
tags: [gap-analysis, schema-design, structural-phenomena, non-conservative]

# Dependency graph
requires:
  - phase: quick-1
    provides: "v1 gap analysis identifying 11 gaps (5 degraded, 6 nice-to-have)"
provides:
  - "Non-conservative gap analysis v2 with 7 Structural Fix Proposals"
  - "Three-tier prioritized recommendations for Phase 1.1 plan revisions"
  - "Concrete Pydantic model sketches for LayoutRegister, ScriptVariant, text_direction, color annotation"
affects: [01.1-schema-taxonomy-review-revision]

# Tech tracking
tech-stack:
  added: []
  patterns: [non-conservative-assessment, structural-fix-proposals, corpus-driven-schema-design]

key-files:
  created:
    - ".planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS-v2.md"
  modified: []

key-decisions:
  - "Register/column identity (SFP-1) is the single largest gap -- 57% of corpus uses multi-register layouts"
  - "Text direction must be explicit, not derived from BCP 47 language tags -- 33% of corpus is RTL"
  - "ScriptVariant enum needed for Rashi vs square Hebrew -- BCP 47 cannot distinguish them"
  - "CATCHWORD reference system needed for dibbur ha-matchil -- most common ref system in Hebrew texts"
  - "COLOR formatting type needed for Koren Talmud -- 449 pages (9% of corpus)"
  - "INDEX_AREA spatial label needed -- UNKNOWN is semantically wrong for a known scholarly apparatus"
  - "All SFPs can be absorbed by existing Phase 1.1 plans with ~41 lines of additional code"

patterns-established:
  - "Non-conservative analysis: treat every corpus phenomenon as a first-class use case"
  - "Corpus-driven schema design: the corpus defines requirements, schema must serve them"

requirements-completed: []

# Metrics
duration: 5min
completed: 2026-02-19
---

# Quick Task 2: Gap Analysis v2 Summary

**Non-conservative structural gap analysis: 9 Partial-Structural gaps identified with 7 Structural Fix Proposals (LayoutRegister, text_direction, ScriptVariant, COLOR, INDEX_AREA, CATCHWORD, content_layer) totaling ~41 lines of schema additions**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-19T16:59:47Z
- **Completed:** 2026-02-19T17:05:31Z
- **Tasks:** 1
- **Files created:** 1

## Accomplishments
- Produced 720-line non-conservative gap analysis reassessing all 85 structural phenomena across 9 categories
- Upgraded 6 gaps from v1 severity (degraded/nice-to-have) to Partial-Structural with concrete fix proposals
- Identified 1 new gap (G12: page-level base direction) not in v1
- Created 7 Structural Fix Proposals with Pydantic model sketches, corpus impact analysis, and Phase 1.1 plan impact assessment
- Established three-tier recommendation framework: 3 must-adopt, 3 should-adopt, 1 consider-deferring
- Demonstrated that all SFPs can be absorbed by existing Phase 1.1 plans without architectural changes

## Task Commits

Each task was committed atomically:

1. **Task 1: Produce non-conservative gap analysis v2** - `6d6bb74` (docs)

## Files Created/Modified
- `.planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS-v2.md` - 720-line non-conservative structural gap analysis with 7 SFPs, three-tier recommendations, and v1 comparison

## Decisions Made
- Treated every corpus phenomenon as a first-class use case (non-conservative stance)
- Rated register identity (G1) as the highest-priority gap at 57% corpus impact
- Separated page-level base_direction (G12) from region-level text_direction (G5) for clarity
- Classified 3 gaps as Partial-Adequate (synchronized flow, inline math, parallel enrichment) where extra fields genuinely suffice
- Kept handwritten annotation (SFP-7) as Tier 3 given 0.08% corpus occurrence
- Confirmed Note/Footnote apparatus (Category 2, all 11 phenomena) as Full coverage even under non-conservative lens

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Gap analysis v2 ready for user decision: which SFPs to adopt before executing Phase 1.1 plans
- If Tier 1 SFPs adopted, Phase 1.1 plans need minor revisions (~41 lines of additions)
- If no SFPs adopted, Phase 1.1 plans execute as-is with extra fields as workarounds
- Decision point: user should review v2 analysis and decide on SFP adoption scope

---
*Phase: quick-2*
*Completed: 2026-02-19*
