# Signal Workflow

This workflow has been consolidated into the signal command for context efficiency.

## Redirect

The complete signal creation process (all 10 steps) is now self-contained in:

`commands/gsd/signal.md`

The command was consolidated to eliminate ~700 lines of unnecessary reference context loading. All signal rules (severity auto-assignment, frustration detection, deduplication, cap enforcement, schema) are inlined directly in the command.

## Why This Changed

The original architecture split signal logic between this workflow file and the command file, with both loading full reference documents (signal-detection.md at 258 lines, knowledge-store.md at 366 lines). The command now contains everything needed for /gsd:signal execution without external reference imports.

## Reference Documents (unchanged)

These reference docs still exist for other consumers (gsd-artifact-sensor, gsd-signal-synthesizer, gsd-spike-runner):
- `get-shit-done/references/signal-detection.md` -- detection rules for automated signal collection
- `.claude/agents/knowledge-store.md` -- KB schema for all entry types
