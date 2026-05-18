---
name: gsd-signal-collector
description: "SUPERSEDED by multi-sensor orchestrator. See gsd-artifact-sensor.md and gsd-signal-synthesizer.md."
tools: Read, Write, Bash, Glob, Grep
color: yellow
---

<role>
**This agent has been superseded by the multi-sensor architecture (Phase 32).**

The detection logic now lives in `gsd-artifact-sensor.md` and KB writing in `gsd-signal-synthesizer.md`. The orchestrator workflow `collect-signals.md` coordinates them.
</role>

<deprecation_notice>

## Architecture Split

What was one agent is now three:

1. **gsd-artifact-sensor** -- Detection: Analyzes execution artifacts (PLAN.md, SUMMARY.md, VERIFICATION.md) and returns raw signal candidates as structured JSON
2. **gsd-signal-synthesizer** -- KB writes: Validates, deduplicates, filters, and persists signals to the knowledge base
3. **collect-signals.md workflow** -- Coordination: Orchestrates sensor spawning and synthesizer invocation

## Why the Split

The original signal-collector combined detection logic and KB write logic in a single agent. The multi-sensor architecture separates concerns so that:
- Multiple sensors can run in parallel (artifact sensor, git sensor, future log sensor)
- A single synthesizer enforces quality gates (trace filtering, dedup, rigor, caps) consistently
- New sensors can be added without modifying existing agents

## Backward Compatibility

If referenced directly, this agent will perform the same detection as `gsd-artifact-sensor` but without the orchestrator's deduplication, rigor enforcement, trace filtering, or cap management benefits. For full signal collection, use the `/gsd:collect-signals` command which invokes the orchestrator workflow.

## Migration

- Detection logic: see `agents/gsd-artifact-sensor.md`
- KB write logic: see `agents/gsd-signal-synthesizer.md` (Phase 32 Plan 03)
- Orchestration: see `get-shit-done/workflows/collect-signals.md` (Phase 32 Plan 04)
- Sensor configuration: see `signal_collection` in `get-shit-done/feature-manifest.json`

</deprecation_notice>

<required_reading>
@~/get-shit-done/references/agent-protocol.md
</required_reading>
