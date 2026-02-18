# Phase 0: Workspace Cleanup - Context

**Gathered:** 2026-02-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Clean up the workspace: organize and commit uncommitted changes, resolve git backlog (stale branches), handle untracked files, and ensure a clean starting point before design work begins in Phase 1.

</domain>

<decisions>
## Implementation Decisions

### ground_truth/ prior work
- Organize and selectively commit: sort contents into appropriate categories
- Keep schema work (SCHEMA.md, schema_v4_comprehensive.json) as prior art — directly informs Phase 1
- Keep test methodology (TESTING_METHODOLOGY.md, COMPREHENSIVE_TEST_PLAN.md) — informs Phase 3
- Keep design docs (ANNOTATION_UI_DESIGN.md, PIPELINE_INTEGRATION.md) — informs Phase 4
- Keep data files (validation sets, baselines, selected pages) — useful reference
- Keep scripts/lib/data directories — may contain reusable tooling
- Planning docs superseded by the roadmap (DIAGNOSTIC_PLAN.md, IMPLEMENTATION_PLAN.md, README.md) should be noted as superseded but committed for reference

### Branch handling
- Archive stale remote branches as lightweight tags (archive/branch-name) before deleting
- Stale branches: convert-orchestrator, document-profiles, workflow-automation, workflow-commands, github-pr-integration, review-pr-smart-detection, docs/vision-overhaul
- Local feature/ocr-integration should also be evaluated for archive
- After cleanup, merge current branch (feature/ground-truth-planning) to main
- Future phases get fresh feature branches from clean main

### Sample PDFs
- Gitignore all PDFs in spikes/sample_pdfs/ (131MB — too large for git)
- Create a manifest/README documenting expected files, paths, and sources
- PDFs stay local, not version-controlled
- Also gitignore spikes/output/ (generated spike results)

### Claude's Discretion
- Commit grouping: organize into logical commits by domain (planning, GSD infra, ground truth, gitignore)
- Old .claude/ files (agents, hooks, logs, commands) — commit removal as GSD supersedes them
- New GSD files — commit as infrastructure setup
- spikes/output/ — gitignore generated output, keep spike source code
- Exact ordering of cleanup operations
- How to structure the manifest for sample PDFs

</decisions>

<specifics>
## Specific Ideas

- ground_truth/ contains substantial prior schema and methodology work (not just planning docs) — later phases should reference this as starting point
- Sample PDFs are scholarly philosophy texts (Derrida, Heidegger, Kant, Plato) that form the test corpus for Phase 5 validation
- Branch archive tags preserve commit references — no work is lost during cleanup

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 00-clean-up-workspace-and-organize-git-backlog*
*Context gathered: 2026-02-18*
