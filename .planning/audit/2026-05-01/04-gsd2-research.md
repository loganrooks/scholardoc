# GSD-2 Research — Is It Useful for ScholarDoc/ScholarGT?

**Date:** 2026-05-01
**Author:** research agent (gsd2-researcher)
**Sources:** `/home/rookslog/workspace/projects/gsd-2-explore` (local clone @ `phase-d-decision-trace-spike`), GitHub `gsd-build/gsd-2` README (raw), scholardoc `.planning/` and `.claude/` artifacts.

---

## Verdict (one paragraph)

**Useful eventually — NOT now.** GSD-2 is not a refactor of GSD/GSD-Reflect; it is a **complete architectural pivot** from "Claude Code prompt framework" to a **standalone TypeScript CLI** (`gsd-pi`, v2.78) on the Pi SDK. It abandons the slash-command-in-Claude-Code model entirely for its own agent runtime, state machine, TUI, MCP server, VS Code extension, and multi-provider routing. For Logan's mid-milestone scholardoc work — 80% through Phase 1.1 with deep custom agent investment, adversarial peer-review patterns, and Serena integration — migrating now means abandoning a workflow that's producing results for a tool still rapidly iterating (recent v2.78.x fixes were git-safety TOCTOU bugs, write-gate off-by-ones, crash recovery). **Right inflection point: start of milestone 2, after Phase 1.2 closes milestone 1, and after GSD-2 stabilizes.** Even then, run a spike first.

---

## What is GSD-2

GSD-2 (npm: `gsd-pi`, repo: `github.com/gsd-build/gsd-2`) is the maintainer's full pivot from "prompt-injection framework loaded into Claude Code" to "standalone coding-agent application." Same `gsd-build` org. README explicitly: GSD-2 is "the future... goal is to eventually migrate GSD-1 users."

- **GSD-1 problem (per VISION.md):** prompts in `~/.claude/commands/` — "fighting the tool, hoping the LLM would follow instructions, with no control over context windows, sessions, or execution."
- **GSD-2 architecture:** TypeScript app embedding Pi SDK. Fresh agent session per task, programmatic context injection, git worktree isolation per slice, crash recovery via lock files, cost ledger, stuck-loop detection, timeout supervision, automatic verification with auto-fix retries, HTML milestone reports.
- **Codebase shape:** npm monorepo (`packages/pi-tui`, `pi-ai`, `pi-agent-core`, `pi-coding-agent`, `mcp-server`, `native`, `rpc-client`), 23 bundled extensions, Rust N-API native engine, three bundled agents (Scout/Researcher/Worker).
- **Workflow hierarchy:** Milestone → Slice → Task ("a task must fit in one context window"). Conceptually overlaps GSD's Milestone → Phase → Plan, with squash-merge per-slice rather than atomic-commit per-plan.

The "trajectory plan" reference (`gsd-2-uplift's cheerful-forging-galaxy`) appears to be a Pi-generated milestone codename, not a user-facing uplift doc. `.plans/` contains 19 internal implementation plans (single-writer engine, parallel-milestone-orchestration, token-optimization-suite, etc.).

## Current state of `gsd-2-explore`

| Indicator | Reading |
|---|---|
| **Version** | 2.78.1 — npm-published, ~80 changelog entries since v2.0 |
| **Activity** | Currently on `phase-d-decision-trace-spike` branch, last commit hours ago |
| **Maturity** | Beta but real. Has Discord, $GSD token (sic), 5,100+ PR-numbered changelog entries, public Mintlify docs, GitBook |
| **Working** | Yes — `npm install -g gsd-pi` is the documented happy path; `/gsd auto`, `/gsd migrate`, `/gsd headless` all documented |
| **Stability signals (concerning)** | Last release v2.78.1 fixes "Windows spawn regression," catch-all auth iteration; v2.78.0 includes major git-safety pass (TOCTOU ancestry guard, atomic sync-lock, `.git/index.lock` force-removal, working-tree stash before `reset --hard`, EXDEV-safe write-gate, off-by-one max-attempts, write-gate fail-closed depth confirmation). These are the kinds of bugs that suggest the auto-mode + worktree machinery is *recently* solidified, not battle-hardened |
| **Migration tooling** | `/gsd migrate` exists, parses v1 `PROJECT.md / ROADMAP.md / REQUIREMENTS.md / phases/`, maps phases → slices, plans → tasks, shows preview before writing. Documented to handle decimal phase numbering and milestone-sectioned roadmaps with `<details>` blocks (which scholardoc uses) |
| **Scholardoc-specific test** | scholardoc's roadmap has `<details>`, decimal phases (1.1, 1.2), large knowledge base, REVIEW_STRATEGY.md and REVIEW_AUDIT_LOG.md (custom v1.20.5 GSD-Reflect artifacts). Migration tool would handle the canonical files but **the custom artifacts (REVIEW_STRATEGY, REVIEW_AUDIT_LOG, knowledge/spikes/, knowledge/reflections/, knowledge/signals/) have no defined target in `.gsd/`** |

## Comparison: scholardoc-relevant features

| Concern | Current GSD/Reflect | GSD-2 | Wins for scholardoc |
|---|---|---|---|
| **Phase/plan execution** | Phase↔Plan, atomic commits per plan. Decimal phases work | Slice↔Task, squash-merge per slice | GSD-1 — per-plan granularity supports `gsd:undo` |
| **Heavy planning artifacts** | Free-form per-phase: CONTEXT, RESEARCH, GAP-ANALYSIS-v2, VERIFICATION (4,873 lines in 1.1) | Stricter schema (M001-CONTEXT, S01-PLAN, T01-PLAN, S01-UAT). No slot for gap analysis or verification docs | GSD-1 — flexible |
| **Adversarial peer-review (REVIEW_STRATEGY/AUDIT_LOG)** | Custom Reflect feature at `.planning/` root | Not modeled. `/gsd doctor` and `/gsd forensics` are runtime checks, not peer review | GSD-1 (Reflect) |
| **Cross-tool memory (Serena + Claude + knowledge/)** | Open: knowledge memos, `.serena/memories/`, free integration | Closed system: KNOWLEDGE/DECISIONS/RUNTIME files plus DB-backed memories table (ADR-013) | GSD-1 — open |
| **Spikes (32 for ScholarDoc)** | First-class `spikes/` dir | Not first-class — would go in research/ or task plans | GSD-1 |
| **Hooks (statusline, CI status)** | Custom JS in `.claude/hooks/` | GSD-internal hook stack (Layer 0/2), incompatible | GSD-1 — porting required |
| **Custom agent set (19 agents incl sensors/synthesizers)** | `.claude/agents/*.md` tightly coupled to Reflect prompts | Scout/Researcher/Worker + skill discovery. v1 agents don't transfer | GSD-1 — significant tuning to lose |
| **Provider-agnostic** | Inherits from Claude Code | First-class: 20+ providers, capability routing (ADR-004), dynamic model selection | GSD-2 — matters when budget pressure exists |
| **Crash recovery** | Manual `gsd-pause-work`/`gsd-resume-work` | Lock files, exponential-backoff restart, recovery briefing from disk | GSD-2 by design |
| **Cost tracking / HTML reports** | None | Per-unit cost ledger, dashboard, auto-generated HTML reports | GSD-2 — nice-to-have |

Overall: GSD-2 wins on engineering (real state machine, cost control, crash recovery, multi-provider) but **loses on every scholardoc-specific customization** because those customizations live in the GSD-Reflect prompt layer that GSD-2 abandons.

## Migration assessment

**What carries over via `/gsd migrate`:** PROJECT.md, ROADMAP.md (with `<details>` and decimal phases), REQUIREMENTS.md, phases/ → slices/, plan files → tasks, completion checkboxes, summaries. Decisions register has a target (`DECISIONS.md`).

**What breaks (concrete list for scholardoc):**
1. All 19 `.claude/agents/gsd-*.md` files — no equivalent surface in GSD-2.
2. Hooks in `.claude/hooks/` (statusline, version-check, CI status, update-check) — needs porting to GSD-2's hook stack.
3. `REVIEW_STRATEGY.md` (16,717 bytes) and `REVIEW_AUDIT_LOG.md` (11,698 bytes) — bespoke files, no GSD-2 schema slot.
4. `.planning/knowledge/` substructure (signals/, reflections/, spikes/) — closest GSD-2 analogue is `KNOWLEDGE.md` flat file plus the new memories DB. Direct mapping unclear.
5. `.planning/quick/` directory (3 quick tasks) — GSD-2 has `/gsd quick` but storage shape may differ.
6. `.planning/deliberations/` — no GSD-2 analogue (this is a GSD-Reflect-specific feature).
7. `.serena/memories/` integration — Serena is not bundled in GSD-2; would coexist or be replaced by GSD-2 memory store.
8. Custom commands in `.claude/commands/gsd/` — GSD-2 ships its own command set, no carry-over.
9. `gsd:upgrade-project` analog — GSD-2 has `/gsd migrate` (one-way, v1→v2) but no "ongoing version-bump" command analogous to GSD-Reflect's upgrade-project.

**Cost (rough, single-developer hours):**
- Run `/gsd migrate` and review preview: 1-2h
- Recreate or skip 19 custom agents: 8-20h depending on which are essential
- Port 4 hooks (or accept loss): 2-6h
- Re-home `REVIEW_STRATEGY` / `REVIEW_AUDIT_LOG` / `knowledge/` substructure as research notes or extensions: 4-8h
- Learn auto-mode, dispatch pipeline, worktree git strategy: 4-8h
- Decide on Serena coexistence: 1-2h investigation
- **Total: ~20-50h, mid-milestone, with disruption to working flow**

## Recommendation: timing

**Don't migrate now.** Specifically:

- **Now (Phase 1.1 → Phase 1.2):** Stay on GSD-Reflect 1.20.5. Phase 1.1 is 80% done, Phase 1.2 is queued. The custom agent stack is *producing results* (12 plans completed at 4 min average). Switching tools mid-milestone is the classic mistake.
- **At milestone 1 close (after Phase 1.2 ships):** Run a 1-2 day spike on a fresh clone. Test `/gsd migrate` on a *copy* of `.planning/`. Verify `<details>` blocks, decimal phases, GAP-ANALYSIS-v2 files, and CONTEXT files survive. Decide if the loss of custom agents/hooks/REVIEW_STRATEGY is acceptable.
- **At milestone 2 start:** If the spike is positive AND GSD-2 has stabilized (no major git-safety regressions for 2-3 versions in a row, e.g., v2.81+), do the migration as part of milestone-2 setup. Plan agents/hooks reimplementation as a phase 2.0 of milestone 2.
- **Wait-until-X tripwires:** GSD-2 hits "stable" tag, OR Logan's workflow needs cost tracking, OR a crash recovery scenario costs >4h of rework, OR multi-provider becomes important.

## Risks

**Of NOT migrating (staying on GSD/GSD-Reflect):**
- Eventual end-of-life: README explicitly says GSD-1 is in maintenance, "active development happens in GSD-2."
- No cost tracking when Logan eventually moves to paid API (currently subscription).
- No crash recovery. Right now Logan has the discipline to handle this manually.
- Falling further behind GSD-2's worktree-isolation safety as it matures (real benefit).
- Investment in custom agents may eventually need rebuilding regardless.

**Of migrating prematurely:**
- Loss of working flow mid-milestone — Phase 1.1 took 28 minutes to execute across 5 plans, with non-trivial decision capture. Disrupting that to learn a new state machine and rewrite 19 agents could lose weeks.
- GSD-2 itself is still patching crash-recovery and git-safety bugs (v2.78.1 just fixed Windows spawn regression; v2.78.0 had a sweep of git TOCTOU/EXDEV/off-by-one fixes). Stabilization is recent.
- The $GSD-token / Discord / "viral" framing in the README signals more product/marketing investment than the careful-engineering aesthetic Logan prefers — a values mismatch worth noting.
- `.planning/REVIEW_STRATEGY.md` and the adversarial review pattern do not have a clear home in GSD-2; that custom workflow may need its own extension to survive.

## Bottom line

GSD-2 is genuinely a better engineering substrate (state machine vs prompt soup, real git isolation, real recovery, real observability). It is also a different tool with a different philosophy (auto-pilot a milestone) than what Logan currently uses (curate every plan, peer-review every decision). For scholardoc as a research project where the *thinking* is the work and the *code* is the byproduct, the prompt-framework model still serves better in the short term. Re-evaluate at milestone 1 close.
