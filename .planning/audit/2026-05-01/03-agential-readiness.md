# Agential Development Readiness Audit — ScholarDoc

**Date:** 2026-05-01
**Auditor:** Claude (deep audit subagent)
**Scope:** Repo-wide AI-agent setup — MCP, hooks, agents, settings, memory, automation

---

## Top-line verdict: **5/10 — Adequate but mismatched**

The repo has substantial GSD infrastructure (20 agents, 36 commands, 4 hook scripts, rich `.planning/` artifacts) but three structural problems:

1. **Stale advertising vs reality.** `CLAUDE.md` claims "Phase 1: PDF reader/OCR"; reality is Phase 1.1 done, Phase 1.2 pending. Lists three MCP servers; only `serena` is configured, and the project's `disabledMcpServers` list disables most.
2. **No domain specialization.** All 20 agents and 36 commands are stock GSD. Logan's domain (PDF extraction, OCR, GT schema, philosophy tagging) gets zero specialized affordance.
3. **Memory fragmentation.** Three memory systems (`.serena/memories/`, `~/.claude/projects/.../memory/`, `.planning/knowledge/`) with no convention; several stale; `.planning/knowledge/` sub-dirs are empty.

---

## MCP servers (configured / running / actually used)

| Server | Configured at | Status for this project | Used? |
|---|---|---|---|
| `serena` | `.mcp.json` (project) | Disabled in project (per `~/.claude.json`: `disabledMcpServers`) | No |
| `sequential-thinking` | `~/.claude.json` (global) | Running (multiple `npx` processes via `ps -ef`) | Yes |
| `context7` | Not in `.mcp.json`; project `disabledMcpServers` | Disabled | No |
| `philpapers` | `~/.claude/settings.json` allowlist only | Disabled | No |
| `tavily` | Project `disabledMcpServers` | Disabled | No |
| `morphllm-fast-apply` | Project `disabledMcpServers` | Disabled | No |
| `zlibrary` | `~/.claude/settings.json` `enabledMcpjsonServers` | Not in project `.mcp.json` — not loaded | No |

Evidence: `/home/rookslog/.claude.json` (paths `.mcpServers` top-level and `.projects."/home/rookslog/workspace/projects/scholardoc".disabledMcpServers`); `/home/rookslog/workspace/projects/scholardoc/.mcp.json` (only serena).

**Practical effect:** Only `sequential-thinking` is reliably available. `CLAUDE.md` table is misleading.

---

## Hooks audit

**Project hooks** (`.claude/settings.json`): three SessionStart hooks (`gsd-check-update`, `gsd-version-check`, `gsd-ci-status`) — all background fire-and-forget — plus a statusline.

**User-level hooks** (`~/.claude/settings.json`): much heavier — 5 SessionStart, Notification, Stop, PostToolUse on Bash/Edit/Write/Task, PreToolUse on Write/Edit/Bash. Includes `gsd-prompt-guard.js` (advisory prompt-injection detector for `.planning/` writes), `gsd-validate-commit.sh` (Conventional Commits — **opt-in via `hooks.community: true` in config.json, currently disabled**), `gsd-workflow-guard.js`, `gsdr-context-monitor.js`.

**Verdict:** Stack is reasonable. `pip install` is *not* actually blocked anywhere (`Bash(pip:*)` is in user `allow`) despite CLAUDE.md claiming it is. Conventional-Commits hook is inert; commits already follow the convention so flipping the flag is free.

**Missing:** PreToolUse hook for `Bash` enforcing pytest timeouts (long-running OCR tests will drain budget); hook preventing edits to generated `scholargt/generated/schema.json`.

---

## Custom agent gap analysis

All 20 agents in `.claude/agents/` are stock GSD. `grep "scholardoc|scholargt|GTElement|extractor|OCR"` across them returns **zero hits**.

Five domain agents would pay off across months:

1. **`scholargt-schema-validator`** — given a YAML profile + GTElement, verifies enabled label categories cover the element and runs `jsonschema` against generated `schema.json`. Logan does this manually after every Phase 1.x plan.
2. **`scholargt-ocr-bench`** — runs an extractor against `ground_truth/ocr_quality/`, computes WER/CER vs `ground_truth/baselines/`, writes a signal. Currently no closed-loop regression detection across the 32 spikes.
3. **`gt-corpus-curator`** — diffs `spikes/sample_pdfs/MANIFEST.md` (20 PDFs listed) against the gitignored disk contents; flags missing files before tests assume they exist.
4. **`extractor-protocol-checker`** — for Phase 2 (pluggable extractors): statically verifies a new implementation matches the contract once defined.
5. **`scholargt-decision-archivist`** — reads conversation for a `[##-##]:` decision tag (STATE.md convention) and appends to `PROJECT.md`/`STATE.md`. Manual today; missed entries lead to drift.

---

## CLAUDE.md grade: **D**

Root `CLAUDE.md` (last touched Jan 6):

- **Stale phase claim** (line 19): "Phase 1: PDF reader and OCR pipeline" — actual: Phase 1.1 ScholarGT schema complete, Phase 1.2 repo reset pending.
- **Misleading MCP table** (lines 62-67): lists Serena, Context7, Sequential — Context7 not configured at all in `.mcp.json`; Serena configured but project-disabled.
- **Wrong workflow** (line 8): "Run `/project:plan`" — no such command exists. Repo uses `/gsd:plan-phase`.
- **Stale memory hints** (line 9): points at Serena memories that pre-date Phase 1.1 completion.
- **No mention of ScholarGT** — the dual-package nature (currently the focus per STATE.md) is invisible to an agent reading CLAUDE.md.
- **No active-branch note.** Branch is `feature/01.1-01-foundation-types`; an agent reading only CLAUDE.md could miss it.

What works: stack line, security boundary section, ADR pointer.

**Fix priority:** Highest. CLAUDE.md is the first file every agent reads.

---

## Memory system map

| System | Path | Purpose | Currency | Usage |
|---|---|---|---|---|
| Serena memories | `.serena/memories/` (15 files) | Symbol-indexed project knowledge | Stale — newest Jan 8, pre-Phase 1.1 | Unused (serena project-disabled) |
| Claude Code project memory | `~/.claude/projects/.../memory/` (5 files + MEMORY.md) | Auto-injected per CLAUDE.md prompt | Mar 19 (42 days, flagged stale by system reminders) | Auto-loaded |
| GSD planning state | `.planning/STATE.md`, `PROJECT.md`, `ROADMAP.md` | Authoritative state | Current (Feb 19) | Live |
| GSD knowledge base | `.planning/knowledge/{reflections,signals,spikes}/` | Phase signals/lessons | **Empty** — sub-dirs exist, no files | Unused |

**Convention gap:** No documented rule for which system holds what. After 12 completed plans, `.planning/knowledge/` has zero signals — GSD's signal-collection design intent is unused.

---

## Top 5 specific gaps + interventions

### 1. CLAUDE.md is stale by 4+ months
**Concrete intervention:** Rewrite CLAUDE.md "Current Phase" and "MCP Servers" sections. Replace `/project:plan` with `/gsd:plan-phase`. Add: "Active branch: `feature/01.1-01-foundation-types` (Phase 1.1 complete, Phase 1.2 pending merge)". Add: "ScholarGT package is the current focus — see `scholargt/` not `scholardoc/`."

### 2. No agent for OCR validation against `ground_truth/ocr_quality/`
**Concrete intervention:** Build `.claude/agents/scholargt-ocr-bench.md` that takes an extractor name and runs `ground_truth/scripts/eval_ocr.py` (or similar — verify path) against the validation corpus, comparing to `ground_truth/baselines/`. Output: WER/CER deltas committed as `.planning/codebase/signals/ocr-bench-{date}.md`.

### 3. Test corpus is gitignored but not reproducibly fetched
**Concrete intervention:** Add `tests/conftest.py` skip-marker `@pytest.mark.requires_corpus` for tests needing `spikes/sample_pdfs/`. CI (`.github/workflows/ci.yml`) currently runs all tests — when these tests exist they will fail silently in CI. Either gate them or add a fetch script. The `MANIFEST.md` lists 20 files but no script downloads them.

### 4. Empty `.planning/knowledge/` defeats GSD's signal capture
**Concrete intervention:** Run `/gsd:collect-signals` for completed Phase 1.1 to backfill signals. Then enable `hooks.community: true` in `.planning/config.json` so commit-message validation activates and post-phase signal collection becomes habit.

### 5. Memory system has no orientation file
**Concrete intervention:** Add `.planning/MEMORY_MAP.md` documenting: where decisions live (`PROJECT.md`), where signals live (`.planning/knowledge/signals/`), where session handoffs live (`STATE.md` "Session Continuity"), and that Serena memories are deprecated/stale and should not be re-read without verification. This becomes the orientation read for any new agent.

Bonus: 116 modified `.claude/` files indicate `gsd:update` ran but didn't commit. Either commit them or revert — `git status` noise costs cognitive overhead in every session.

---

## What's working well

- **`.planning/` structure is solid.** STATE.md, ROADMAP.md, PROJECT.md, phase artifacts (PLAN/SUMMARY/CONTEXT/RESEARCH/VERIFICATION) are comprehensive and current.
- **Decision logging** (STATE.md's 65-line decision table tagged by plan ID) is the strongest evidence-trail in the repo.
- **`spikes/`** with 32 numbered experiments + `FINDINGS.md` + 4 ADRs is exemplary scientific practice.
- **CI works** (`.github/workflows/ci.yml`): Python 3.11/3.12 matrix, ruff, pytest. Lean but functional.
- **Prompt-injection hook** for `.planning/` writes is a quiet but real defense.
- **Sub-package separation** is clean: `scholargt/` imports nothing from `scholardoc/`.
- **Worktree-ready:** repo isn't large enough to need it yet, but Phase 1.2 docs-reset parallel to Phase 2 design exploration would be a natural pair.

---

## Bottom line

The framework is heavier than the current usage justifies. Trim the cargo (delete or fix CLAUDE.md MCP table; commit or revert the 116 GSD update files; populate `.planning/knowledge/`), then add 2-3 domain agents (`scholargt-schema-validator`, `scholargt-ocr-bench`, `gt-corpus-curator`). After that, this becomes a 7-8/10 setup. Until then it's adequate but not differentiated for Logan's specific work.
