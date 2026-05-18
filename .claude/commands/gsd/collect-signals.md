---
name: gsd:collect-signals
description: Analyze execution artifacts for a phase using parallel sensors (artifact, git) and synthesize signals into the knowledge base (v1.16.0+dev)
argument-hint: "<phase-number>"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - Task
---

<objective>
Collect signals from a completed phase's execution artifacts.

After running `/gsd:execute-phase`, run this command to analyze what happened — detect deviations from plans, debugging struggles, and configuration mismatches. Qualifying signals are persisted to the knowledge base for future surfacing.

This is a retrospective analysis pass. It reads artifacts without modifying them.
</objective>

<execution_context>
@./.claude/get-shit-done/references/ui-brand.md
@./.claude/get-shit-done/workflows/collect-signals.md
</execution_context>

<context>
Phase: $ARGUMENTS

@.planning/STATE.md
@.planning/config.json
</context>

<process>
1. **Parse phase number** from arguments
2. **Delegate to workflow** at `get-shit-done/workflows/collect-signals.md` -- workflow reads sensor config, spawns enabled sensors in parallel (artifact sensor, git sensor), collects their output, and passes to the signal synthesizer for deduplication, rigor enforcement, and KB persistence
3. **Report completion** with signal counts and files written
</process>
