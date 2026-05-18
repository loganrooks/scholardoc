---
name: gsd:signal
description: Log a manual signal observation to the knowledge base with context from the current conversation (v1.16.0+dev)
argument-hint: '"description" [--severity critical|notable] [--type deviation|struggle|config-mismatch|custom]'
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

<objective>
Create a manual signal entry in the knowledge base capturing an observation from the current conversation. Write a signal file to ~/.gsd/knowledge/signals/{project}/ and rebuild the index.
</objective>

<context>
Arguments: $ARGUMENTS

@.planning/STATE.md
@.planning/config.json
</context>

<signal_rules>

## Signal Schema

File path: `~/.gsd/knowledge/signals/{project}/{YYYY-MM-DD}-{slug}.md`
ID pattern: `sig-{YYYY-MM-DD}-{slug}`
Slug: kebab-case, max 50 chars, derived from description.

Frontmatter fields:
  id, type: signal, project, tags: [], created (ISO-8601), updated (ISO-8601),
  durability: {workaround|convention|principle}, status: active,
  severity: {critical|notable},
  signal_type: {deviation|struggle|config-mismatch|capability-gap|custom},
  phase, plan, polarity: {positive|negative|neutral}, source: manual,
  occurrence_count: {N}, related_signals: [],
  runtime: {detected}, model: {detected}, gsd_version: {detected}

Body sections: ## What Happened / ## Context / ## Potential Cause

## Severity Auto-Assignment (SGNL-04)

| Condition | Severity |
|-----------|----------|
| Verification failed, config mismatch | critical |
| Multiple issues, non-trivial problems, unexpected improvements | notable |

Manual signals are always persisted regardless of severity (user explicitly chose to record).

## Frustration Patterns (SGNL-06)

Scan recent conversation messages for these patterns:
- "still not working", "this is broken", "tried everything"
- "keeps failing", "doesn't work", "same error"
- "frustrated", "why won't", "makes no sense", "wasting time"

Threshold: 2+ patterns detected. Detection is suggestive -- mention to user and let them decide whether to include frustration context. Do not auto-create signals from frustration alone.

## Dedup Logic (SGNL-05)

1. Read index at `~/.gsd/knowledge/index.md` (if exists)
2. For each existing active signal, check match criteria:
   - Same `signal_type` AND same `project` AND 2+ shared tags
3. If match found: add matched IDs to `related_signals`, set `occurrence_count` = max(matched counts) + 1
4. Do NOT modify existing signals (immutable)
5. If no matches: `related_signals: []`, `occurrence_count: 1`

## Cap Enforcement (SGNL-09)

Max 10 active signals per phase per project.
- If count < 10: write normally
- If count >= 10: compare new signal severity against lowest-severity existing signal
  - new >= lowest: archive lowest (set status: archived), write new signal
  - new < lowest: inform user, offer override
Severity ordering: critical > notable.

## KB Paths

KB root: `~/.gsd/knowledge/`
Index: `~/.gsd/knowledge/index.md`
Rebuild: `bash ~/.gsd/bin/kb-rebuild-index.sh`

</signal_rules>

<process>

## Step 1: Parse Arguments

Extract from inline arguments if provided:
- **description** -- quoted string (required, can be asked for if missing)
- **--severity** -- `critical` or `notable` (optional, auto-assigned if missing)
- **--type** -- `deviation`, `struggle`, `config-mismatch`, or `custom` (optional, inferred if missing)

## Step 2: Extract Conversation Context

1. **Phase and plan**: Check conversation for current phase/plan. If not evident, read `.planning/STATE.md`.
2. **Project name**: Derive from working directory basename, kebab-case.
3. **Frustration detection**: Scan recent messages using inlined patterns above (SGNL-06). If 2+ patterns found, mention to user and offer to include frustration context.
4. **Runtime detection**: Examine path prefix of this command file.
   - ~/.claude/ -> runtime: claude-code
   - ~/.config/opencode/ -> runtime: opencode
   - ~/.gemini/ -> runtime: gemini-cli
   - ~/.codex/ -> runtime: codex-cli
5. **Model detection**: Use self-knowledge of current model name. If uncertain, omit.

## Step 3: Fill Missing Information (Max 1 Follow-up)

Combine all missing fields into a single follow-up if needed. Zero follow-ups if everything was inline.

- **No description**: Ask "What did you observe?"
- **No severity**: Auto-assign using SGNL-04 table above. Show assignment, allow override.
- **No type**: Infer from description keywords:
  - "deviat", "unexpected", "changed", "different from plan" -> `deviation`
  - "struggle", "stuck", "debug", "retry", "failing" -> `struggle`
  - "config", "environment", "model", "setting" -> `config-mismatch`
  - Otherwise -> `custom`
- **Polarity**: Auto-assign:
  - Negative indicators (problems, failures, struggles, frustration) -> `negative`
  - Positive indicators (improvements, faster, cleaner, better) -> `positive`
  - Otherwise -> `neutral`

## Step 4: Preview Before Writing

Display signal preview for confirmation:
```
## Signal Preview
**Description:** {description}
**Severity:** {severity}
**Type:** {type}
**Polarity:** {polarity}
**Phase:** {phase} | **Plan:** {plan}
**Runtime:** {runtime} | **Model:** {model}
**Source:** manual
Save this signal? (y/n)
```

## Step 5: Dedup Check

Apply SGNL-05 dedup logic above. Show related signals if matches found.

## Step 6: Cap Check

Apply SGNL-09 cap enforcement above. Handle cap exceeded scenario.

## Step 7: Write Signal File

Write to `~/.gsd/knowledge/signals/{project}/{YYYY-MM-DD}-{slug}.md` using schema above. Create parent directories with `mkdir -p`. Include all frontmatter fields and body sections (What Happened, Context, Potential Cause).

## Step 8: Rebuild Index

```bash
bash ~/.gsd/bin/kb-rebuild-index.sh
```

## Step 9: Git Commit (Conditional)

```bash
COMMIT_DOCS=$(cat .planning/config.json 2>/dev/null | grep -o '"commit_docs"[[:space:]]*:[[:space:]]*[^,}]*' | grep -o 'true\|false' || echo "true")
git check-ignore -q .planning 2>/dev/null && COMMIT_DOCS=false
```
If true: `git add -f {signal-file} && git commit -m "docs(signal): {slug}"`
If false: skip git, inform user signal saved but not committed.

## Step 10: Confirm

```
Signal created: {id}
File: ~/.gsd/knowledge/signals/{project}/{filename}
Index rebuilt.
```

</process>

<design_notes>
- Max 2 interaction rounds: arguments + one follow-up if needed
- Frustration detection is suggestive, not automatic
- Git follows commit_docs setting from .planning/config.json
- All manual signals persisted regardless of severity
- Source always "manual" (vs "auto" from gsd-signal-collector)
- Runtime/model fields are best-effort; omit if uncertain
</design_notes>
