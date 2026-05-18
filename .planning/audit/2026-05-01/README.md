# Full-Repo Audit — 2026-05-01

Multi-axis audit of ScholarDoc/ScholarGT covering current state, direction, code quality, agential development setup, GSD-2 applicability, and uplift interventions.

## Reading order

1. **`00-SYNTHESIS.md`** — orchestrator's cross-axis synthesis. Start here. Direct answers to "where are we / where are we going / set up properly / GSD-2 / how to uplift / gaps."
2. **`06-interventions.md`** — actionable registry. 29 interventions sized, typed, sequenced. The deliverable for formalization.

## Source audits (parallel agent reports)

| File | Audit | Verdict |
|---|---|---|
| `01-codebase-quality.md` | Code quality + architecture | ScholarGT well-built. ScholarDoc bit-rotted (deferred). 32 unit failures + 29 errors from one missing fixture PDF. Real test count: 694 (not 312/320/349). |
| `02-doc-drift.md` | Documentation authority drift | SEVERE and unrepaired. Every root doc Era 1. Test count claim 43–62% stale. 8 architectural decisions need ADRs. `/project:*` commands referenced but don't exist. |
| `03-agential-readiness.md` | AI-agent development setup | 5/10 — adequate but mismatched. Zero domain agents. CLAUDE.md grade D. `.planning/knowledge/` empty after 12 plans. |
| `04-gsd2-research.md` | GSD-2 evaluation | Useful eventually, not now. Architectural pivot, breaks 19 custom agents + hooks + REVIEW_STRATEGY. ~20–50h migration. Right inflection: M1 close → spike → M2 start. |
| `05-vision-roadmap-critique.md` | Adversarial review of vision/roadmap | Recovering, with two convergent risks. Schema never tested against real annotation work; "design-heavy" frame doing rhetorical work it can't support. 11 REVIEW_STRATEGY items un-phased. |

## Top findings (cross-axis)

1. **Convergent CRITICAL risk** — schema (Phase 1+1.1) has never been validated against real annotation; plan defers that until Phase 5 (after Phases 2/3/4 are built atop it). Three independent audits surface this.
2. **Documentation drift unrepaired** — REVIEW_STRATEGY.md (March 2026) named the problem; six weeks later, every root doc is still Era 1; Phase 1.2 (queued reset) is stalled at planning.
3. **Test suite cascade from one fixture** — 32 unit failures + 29 collection errors all trace to a single gitignored PDF.
4. **GSD setup is heavier than its differentiation** — 20 stock agents, zero domain specialization; `.planning/knowledge/` empty after 12 plans.
5. **GSD-2 not now** — same maintainer, full pivot, mid-stabilization. Spike at M1 close.

## Single biggest recommendation

**Insert Phase 1.5: Pilot Annotation** before Phase 2. Annotate 3–5 pages of real GT using v2.0.0 schema. Surface what works, what doesn't, what needs SFP-process additions. Dissolves the convergent schema-validity risk that three audits independently flagged. Cost: 1–2 weeks elapsed. Alternative: write the bounded-risk argument explicitly into PROJECT.md (R10), but only if Logan judges existing gap-analysis evidence sufficient.
