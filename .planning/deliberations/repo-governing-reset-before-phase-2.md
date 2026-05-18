## Deliberation: Repo Governing Reset Before Phase 2

**Date:** 2026-04-16
**Status:** Open
**Trigger:** Conversation observation and repo review showed that the project's governing documents, runtime architecture, and verification path have drifted apart. The immediate question is whether Phase 2 should start now or whether the repo needs a reset phase first.
**Affects:** Milestone 1 Phases 2-5; EXT-01, EXT-02, EXT-03, EXP-01, EVAL-01, ANN-01, VAL-01; deferred ARCH-01
**Related:**
- No directly related project signals found in the knowledge base
- Analogous signal: `sig-2026-03-19-stale-platform-claims-in-source`
- Analogous signal: `sig-2026-03-06-plan-verification-misses-architectural-gaps`
- Requirements: `.planning/REQUIREMENTS.md` EXT-01 through VAL-01

## Situation

The repo currently mixes four partially incompatible realities: ScholarDoc as the user-facing product, ScholarGT as the active milestone, `ground_truth/` as a legacy-but-still-runnable subsystem, and GSD planning as the authoritative execution path. That drift is no longer just documentation debt. It now affects routing, verification, packaging expectations, and the shape of the next architectural phase.

The core architectural issue is that ScholarGT has completed the schema/config/validation layer, but the next promised layers do not yet exist: extractor runtime contracts, provenance/change tracking, experiment models, and annotation workflow state. Starting Phase 2 without first restoring a single governing story risks building those layers on top of contradictory assumptions.

### Evidence Base

| Source | What it shows | Corroborated? | Signal ID |
|--------|--------------|---------------|-----------|
| `README.md`, `CLAUDE.md`, `.planning/PROJECT.md` | User-facing docs still frame ScholarDoc as the active product, while planning says ScholarGT is the primary milestone deliverable | Yes; read file comparison on 2026-04-16 | informal |
| `.planning/STATE.md`, `.planning/ROADMAP.md` | Planning state is internally inconsistent: Phase 1.1 is marked complete and still described as executing; state points to a non-existent Phase 1.2; roadmap still leaves 01.1-05 unchecked | Yes; read file comparison on 2026-04-16 | informal |
| `scholargt/__init__.py`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md` | ScholarGT's implemented public API is schema/config/validation only, while upcoming requirements depend on extractor protocols, provenance, experimentation, and annotation workflow layers | Yes; checked exports against pending requirements on 2026-04-16 | informal |
| `README.md`, `pyproject.toml`, `uv run pytest`, `uv run --extra dev --extra ground-truth pytest -q` | The documented verification path is false. Default test command fails at collection without extras; extras-enabled run still ends with 33 failures and 29 errors, mostly from missing fixture PDFs | Yes; command outputs captured on 2026-04-16 | informal |
| `ground_truth/README.md`, `tests/integration/test_ground_truth_regression.py`, `scholardoc/__init__.py`, `scholardoc/convert.py` | The legacy evaluation subsystem is stale: docs reference files that no longer exist, and the regression test expects `convert_pdf`, which is no longer exposed | Yes; symbol search and file reads on 2026-04-16 | informal |
| `README.md`, `scholardoc/models.py` | README examples are not copy-pastable: `doc.to_dict()` is not public, and `doc.save(\"output.md\")` suggests Markdown export even though `save()` writes the ScholarDoc JSON payload | Yes; compared README example to model methods on 2026-04-16 | informal |

## Framing

This is not only a documentation cleanup question. The deeper issue is whether the repo currently has the authority, boundaries, and verification baseline needed to make Phase 2 decisions without compounding drift.

**Core question:** Should this repo insert a governing reset phase before Phase 2 so that documentation authority, package boundaries, verification, and the ScholarGT runtime contract are repaired before more milestone work proceeds?

**Adjacent questions:**
- Should the reset remain intra-repo, or should it include a package/workspace split?
- Should experimentation be partially designed before extractor work, even if Phase 2 stays first?
- What parts of `ground_truth/` remain active assets versus historical reference?

## Analysis

### Option A: Proceed directly to Phase 2

- **Claim:** Start extractor-interface planning now and treat current drift as secondary cleanup work.
- **Grounds:** Phase 1 and 1.1 produced substantial schema work; the roadmap already identifies Phase 2 as next.
- **Warrant:** If the schema is stable enough, runtime work can begin and the remaining drift can be repaired incrementally.
- **Rebuttal:** The repo currently lacks a truthful verification path and a single authoritative architecture narrative. New runtime abstractions would likely inherit those contradictions.
- **Qualifier:** Unlikely to be the right move.

### Option B: Insert a short governing reset phase before Phase 2

- **Claim:** Insert a focused phase that repairs authority, verification, and runtime framing before planning or implementing Phase 2.
- **Grounds:** The repo has corroborated drift in docs, planning state, tests, examples, and legacy subsystem boundaries. Phase 2 also depends on concepts not yet modeled anywhere outside the roadmap.
- **Warrant:** Restoring one governing story and one valid verification path reduces the chance that the extractor/provenance layer gets built on false premises. This is a precondition repair, not a detour.
- **Rebuttal:** A reset phase can become a procrastination sink if it expands into repo-wide perfectionism or premature splitting.
- **Qualifier:** Probably the strongest option.

### Option C: Reorganize package structure before anything else

- **Claim:** Formalize package/workspace boundaries first, potentially splitting active packages or at least promoting a uv workspace immediately.
- **Grounds:** The repo already contains multiple products and a legacy subsystem, and packaging metadata is stale.
- **Warrant:** Structural boundaries can force clarity and prevent further conceptual bleed.
- **Rebuttal:** Structure-first changes can create churn without resolving the more basic authority and verification problems. Package splits are higher-cost and harder to reverse than a governing reset.
- **Qualifier:** Plausible later, premature as the first intervention.

## Tensions

The repo is caught between momentum and legitimacy. Moving directly into Phase 2 preserves momentum, but risks illegible architecture and unverifiable claims. Pausing for a reset improves legitimacy, but can slide into meta-work if it is not tightly scoped.

There is also a tension between serialization and runtime design in ScholarGT. The existing models are strong persistence/schema artifacts. The next milestone work needs workflow-state abstractions that are not the same thing. Treating the schema as the whole platform would be simpler, but likely wrong.

## Recommendation

The current lean is to insert a short reset phase before Phase 2. That phase should be explicitly bounded:

1. Reconcile repo authority: `README.md`, `CLAUDE.md`, root `ROADMAP.md`, `.planning/STATE.md`, and legacy status notes.
2. Repair the verification path: truthful setup commands, explicit handling of missing PDF fixtures, mark registration, and regression-harness cleanup.
3. Define the Phase 2 runtime contract boundary: extractor protocol, provenance/change event model, and the distinction between live workflow models and persisted GT artifacts.
4. Decide legacy status and package boundaries for `ground_truth/` and whether a uv workspace is needed now or later.

**Current leaning:** Option B, because it addresses the minimum load-bearing inconsistencies without prematurely committing to a repo split.

**Open questions blocking conclusion:**
1. Should the reset phase also partially design Phase 3 experiment models, or is that scope creep?
2. Is `ground_truth/` a legacy subsystem to fence off, or an active evaluation asset to rehabilitate?
3. Is a uv workspace enough for boundary clarity, or does the repo need stronger separation later?

## Predictions

**If adopted, we predict:**

| ID | Prediction | Observable by | Falsified if |
|----|-----------|---------------|-------------|
| P1 | After the reset phase, all top-level project docs point to one authoritative current milestone story | Manual repo review after phase completion | Root docs still disagree on what the active project is |
| P2 | After the reset phase, there is one documented test command that accurately reflects repo health | Running the documented command after phase completion | The documented command still fails unexpectedly or omits known failures |
| P3 | Phase 2 planning will become narrower and cleaner because the runtime contract boundary will already be explicit | Review of the resulting Phase 2 context/plan artifacts | Phase 2 planning still mixes schema cleanup, doc repair, and runtime design ambiguously |

## Decision Record

**Decision:** Not yet concluded
**Decided:** -
**Implemented via:** not yet implemented
**Signals addressed:** none formalized yet

## Evaluation

Not yet evaluated.

## Supersession

Not superseded.
