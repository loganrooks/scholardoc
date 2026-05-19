# Wave 1 /goal Prompts — 2026-05-19 Packet Framing Investigation

**Date:** 2026-05-19
**Purpose:** Three packet-blind, parallel investigations of the project, the ecosystem, and the history — independent of the v5.2-rev1 revival packet's framing. Each agent reads its assigned slice of reality directly and produces a report. Wave 2 reads all three alongside the existing audit and adoption decision to determine whether the packet's diagnosis converges with independent evidence.

**Convention:**
- Each prompt is a copy-paste /goal text for Claude Code.
- Each agent writes to `.planning/inquiry/2026-05-19/wave1-<name>.md`.
- Run in parallel sessions, ideally in separate worktrees.
- Agents are explicitly forbidden from reading `.planning/revival-packet/` or `reports/revival/` — that's the discipline that escapes the packet's framing.

**Output convergence:**
- `wave1-codebase.md` (code-anchored evidence)
- `wave1-ecosystem.md` (cross-project reality)
- `wave1-history.md` (trajectory and drift)

---

## Wave 1A — Codebase exploration

```text
Investigate the actual state of the ScholarDoc / ScholarGT code. Produce a faithful picture of what the code IS, anchored in direct file inspection, before any planning narrative frames what it SHOULD be.

VISIBILITY: read code under scholardoc/, scholargt/, ground_truth/, tests/, spikes/, and the repo's top-level docs (README.md, CLAUDE.md, pyproject.toml, VERSION). Read docs/ and docs/adr/ for context. Do NOT read anything under .planning/ — planning narratives would frame the investigation away from the code itself; that's exactly the bias this Wave is designed to escape. Use find, grep, wc, python -c, pytest --collect-only as needed.

END STATE: .planning/inquiry/2026-05-19/wave1-codebase.md exists and contains, at minimum: (1) a top-level inventory of every Python package in the repo with line counts, public-API surface, and one-sentence purpose; (2) the real coupling map between scholardoc and scholargt as observed via actual import statements, not declared independence; (3) the test suite's current state — collected, passing, failing, errored, skipped — with the top three causes of failure named with file:line citations; (4) code-quality red flags found by inspection (god modules, dead-but-imported code, unfinished interfaces, schema/code drift), each with a file:line citation; (5) at least five OBSERVED findings from read-only commands run against the live tree this session; (6) a per-package assessment: currently-working / needs-repair / needs-replacement, with the cost basis for each judgment; (7) at least one finding the agent did NOT expect going in, named explicitly as such; (8) three to five open questions the synthesis pass will need to resolve.

PROOF: in your final turn, cat .planning/inquiry/2026-05-19/wave1-codebase.md so the evaluator can verify all eight sections from the transcript.

CONSTRAINTS: read-only. No edits to source, tests, planning files, or git state. No git commit/push/reset/stash/clean. No reads of .planning/ — that includes the revival packet, audit history, phase plans, and STATE.md. The historical and narrative context lives in a sibling investigation; this one is code-anchored only. Web access is not needed.

BOUND: stop after 30 turns. If you cannot satisfy the condition, end with a structured BLOCKER turn naming what was blocked.
```

---

## Wave 1B — Ecosystem exploration

```text
Investigate the actual state of the ~/workspace/projects/ ecosystem and ScholarDoc's real position within it. Produce a faithful picture of which projects exist, which are active, and what real (not aspirational) relationships exist between them.

VISIBILITY: read every project under /home/rookslog/workspace/projects/ at the top level — each project's README.md, CLAUDE.md, pyproject.toml (or equivalent), VERSION, git log -n 20, and any cross-project references found via grep. Read source code in sibling projects where it directly shows ScholarDoc integration. Do NOT read any project's .planning/ directory, including scholardoc's. Planning narratives describe intent; this investigation needs reality.

END STATE: /home/rookslog/workspace/projects/scholardoc/.planning/inquiry/2026-05-19/wave1-ecosystem.md exists and contains, at minimum: (1) a table of every directory under ~/workspace/projects/ with status (active / maintenance / inactive / abandoned, justified by last-commit date and recent file mtimes), primary language, one-sentence purpose; (2) which projects actually import from scholardoc, reference ScholarDocument, or process scholarly documents in any form — verified via grep across the ecosystem, not asserted from any narrative; (3) for each project the user-or-narrative has called a "downstream consumer" of scholardoc (search ecosystem mentions), name what that project actually does today with documents/PDFs/extraction; (4) coordination implications: which decisions in scholardoc would block or unblock work in sibling projects, derived from actual code and config not from stated intent; (5) at least five OBSERVED findings from grep/ls/cat commands run across the ecosystem this session; (6) at least one finding the agent did NOT expect going in; (7) three to five open questions for the synthesis pass; (8) explicit handling of projects whose name suggests a relationship but where no integration exists in code (e.g., philograph, philograph-mcp, philo-rag-simple).

PROOF: in your final turn, cat .planning/inquiry/2026-05-19/wave1-ecosystem.md.

CONSTRAINTS: read-only across the entire ecosystem. No edits anywhere in any project. No reads of any .planning/ directory. No git commit/push/reset/stash/clean. Web access is not needed.

BOUND: stop after 30 turns. End with a structured BLOCKER if blocked.
```

---

## Wave 1C — Historical context

```text
Investigate ScholarDoc's actual history and decision trajectory. Produce a faithful picture of what was tried, what worked, what stalled, what drifted — derived from git history, planning docs, and the existing audit synthesis, but independent of any current proposal about what the project should do next.

VISIBILITY: read .planning/PROJECT.md, STATE.md, ROADMAP.md, REQUIREMENTS.md, .planning/audit/2026-05-01/ in full, .planning/phases/ in full, docs/adr/, git log (full history), git tag, any decision log or session-handoff artifact. Do NOT read .planning/revival-packet/ — that is a recent unaudited proposal whose framing this investigation is designed to test by independent means, not to inherit from. Do NOT read reports/revival/ — same reason. Read recent commits to characterize the actual trajectory.

END STATE: .planning/inquiry/2026-05-19/wave1-history.md exists and contains, at minimum: (1) a phase-by-phase timeline with start dates, completion dates, what each phase produced, and the state of each phase as of today (derived from .planning/phases/ + STATE.md + git log); (2) the actual velocity history — when work happened, where it accelerated, where it slowed, where it stopped — with calendar dates not just plan-minute claims; (3) every reset or scope change the project has undergone, named explicitly (Phase 0, Phase 1.2 insertion, schema rework, others to be discovered); (4) the project's original framing vs what it has drifted to — compare older PROJECT.md / ROADMAP.md / README.md commits to recent versions and name the deltas; (5) recurring patterns: deferrals, scope expansions, decisions deferred-then-forgotten, decisions made-and-later-questioned; (6) the flat decision log that any forward plan must honor, with provenance for each entry; (7) at least one finding the agent did NOT expect going in; (8) three to five open questions for the synthesis pass.

PROOF: in your final turn, cat .planning/inquiry/2026-05-19/wave1-history.md.

CONSTRAINTS: read-only. No edits to anything. No reads of .planning/revival-packet/ or reports/revival/. No git commit/push/reset/stash/clean. Web access is not needed.

BOUND: stop after 30 turns. End with a structured BLOCKER if blocked.
```

---

## How to run

1. **Three parallel sessions.** Open three terminals (or three SSH sessions, or three worktrees). Recommended: worktrees, so the agents can't accidentally collide on stash / temp files.
2. **Paste each prompt** into a `/goal` invocation in its own session.
3. **Let each run to completion.** They are read-only by design; failures are observable but not destructive.
4. **Wave 2 setup** (after all three complete): a fresh session reads `wave1-codebase.md`, `wave1-ecosystem.md`, `wave1-history.md`, plus `reports/revival/packet_audit.md` and `reports/revival/packet_adoption_decision.md`, and produces `.planning/inquiry/2026-05-19/wave2-synthesis.md` answering: do the independent investigations converge with the packet's diagnosis, or diverge? Where they diverge, which side has the better evidence? What rival framings (Lean Startup; TLA+; build-something-small-now; researcher-no-SE; engineer-no-research) does the packet not load — and would loading them change the verdict?

## Discipline notes

- The packet-blind constraint is the entire point. An agent that "just peeks" at the packet to orient itself defeats the design. If an agent needs orientation, the prompt itself is the orientation.
- The "finding I did NOT expect" section is the anti-rubber-stamp. Without it, the agent can produce a structurally-correct report that paraphrases the assigned slice of reality back. With it, the agent has to surface at least one surprise — which is the minimum evidence that real investigation happened.
- The "open questions for synthesis" section is what feeds Wave 2. If Wave 1 produces no useful open questions, Wave 2 has nothing to synthesize and the design fails earlier rather than later.
