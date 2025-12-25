---
description: Capture correction signal - mark moments when something went wrong
allowed-tools: Bash(mkdir:*), Bash(date:*), Bash(cat:*), Write, Read
argument-hint: [optional description of what went wrong]
---

# Signal: $ARGUMENTS

Capture a correction signal for self-improvement analysis.

## Purpose

Signals mark moments when:
- You interrupted Claude ("no stop", "wait", "that's wrong")
- Claude made a mistake you want remembered
- A different approach should have been taken
- Something felt off, even if you can't articulate why

The signal is just a timestamp + note. Analysis happens later via `/project:improve`.

## Step 1: Prepare Signal

### Determine Note Content
```
IF $ARGUMENTS is provided:
  note = "$ARGUMENTS"
ELSE:
  note = "(bare signal - see conversation context)"
```

### Get Timestamp
```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

## Step 2: Ensure Signals Directory

```bash
mkdir -p .claude/signals
```

## Step 3: Write Signal

Append to `.claude/signals/corrections.jsonl`:

```bash
# Format: one JSON object per line
echo '{"ts": "[TIMESTAMP]", "note": "[NOTE]", "session": "[CONVERSATION_ID_IF_AVAILABLE]"}' >> .claude/signals/corrections.jsonl
```

### Example Entries
```jsonl
{"ts": "2025-12-25T14:32:00Z", "note": "no stop", "session": "abc123"}
{"ts": "2025-12-25T14:45:00Z", "note": "wrong auth approach", "session": "abc123"}
{"ts": "2025-12-25T15:10:00Z", "note": "should use map not forEach", "session": "abc123"}
{"ts": "2025-12-25T16:00:00Z", "note": "(bare signal - see conversation context)", "session": "abc123"}
```

## Step 4: Confirm

Brief output only:

```
📍 Signal captured: "[NOTE]"
```

Then continue with whatever you were doing. Don't make a big deal of it.

## How Signals Get Used

1. `/project:improve` reads `.claude/signals/corrections.jsonl`
2. Correlates timestamps with native Claude logs (`~/.claude/projects/*/`)
3. Identifies what Claude was doing at each signal moment
4. Finds patterns across multiple signals
5. Proposes improvements to project memory or workflows

## Signal Hygiene

Signals are append-only during active development. The `/project:improve` command may:
- Mark signals as "processed" after analysis
- Archive old signals periodically
- Promote patterns to Serena memory

Don't manually edit `corrections.jsonl` - let the improvement cycle handle it.

## Examples

```bash
# Vague interruption - just mark the moment
/project:signal

# Brief note
/project:signal wrong approach

# Specific feedback
/project:signal should have checked for null before accessing .data

# Preference
/project:signal I prefer async/await over .then chains
```

All valid. The more specific, the easier to analyze - but bare signals work too.
