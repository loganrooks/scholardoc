# Signal Format Specification

Standard format for correction signals captured via `/signal` command.

## Location

Signals are appended to: `.claude/signals/corrections.jsonl`

One JSON object per line (JSONL format).

## Schema

```json
{
  "ts": "ISO8601 timestamp",
  "type": "correction",
  "user_feedback": "string - what the user said, verbatim or summarized",
  "context": {
    "task": "string - what Claude was working on",
    "action": "string - the specific action that triggered the signal",
    "approach": "string - the overall approach being taken"
  },
  "diagnosis": {
    "what_happened": "string - concrete description of the issue",
    "why": "string - root cause hypothesis",
    "should_have": "string - what should have happened instead"
  },
  "improvement_hint": "string - what should change to prevent recurrence",
  "level": "1 or 2 - systemic (1) or project-specific (2)"
}
```

## Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `ts` | Yes | ISO8601 timestamp when signal was captured |
| `type` | Yes | Always "correction" for user-initiated signals |
| `user_feedback` | Yes | The user's words - what they said was wrong |
| `context.task` | Yes | High-level task being worked on |
| `context.action` | Yes | Specific action that caused the issue |
| `context.approach` | No | Broader approach/strategy if relevant |
| `diagnosis.what_happened` | Yes | Factual description of what occurred |
| `diagnosis.why` | Yes | Hypothesis about root cause |
| `diagnosis.should_have` | Yes | Better alternative that should have been taken |
| `improvement_hint` | Yes | Actionable suggestion for preventing recurrence |
| `level` | Yes | 1 = systemic (affects other projects), 2 = project-specific |

## Level Classification

| Level | When to Use | Example |
|-------|-------------|---------|
| 1 | Issue would occur in other projects using claude-enhanced | "Should check for existing libraries before building custom" |
| 2 | Issue is specific to this project's context | "Should use our existing UserService class" |

Level 1 signals may be escalated to claude-enhanced during weekly review.

## Example: Good Signal

```json
{
  "ts": "2026-01-08T15:30:00Z",
  "type": "correction",
  "user_feedback": "wrong approach",
  "context": {
    "task": "implementing user authentication",
    "action": "created a custom JWT library",
    "approach": "building auth from scratch"
  },
  "diagnosis": {
    "what_happened": "started implementing custom JWT handling instead of using existing solution",
    "why": "assumed we needed custom solution, didn't check for existing libraries",
    "should_have": "checked npm for existing auth libraries like next-auth"
  },
  "improvement_hint": "Always check for existing solutions before building custom implementations",
  "level": 1
}
```

## Example: Minimal Valid Signal

```json
{
  "ts": "2026-01-08T16:00:00Z",
  "type": "correction",
  "user_feedback": "no, stop",
  "context": {
    "task": "refactoring database queries",
    "action": "started rewriting the entire data layer"
  },
  "diagnosis": {
    "what_happened": "began large refactor when small fix was needed",
    "why": "over-scoped the solution",
    "should_have": "asked about scope before starting major changes"
  },
  "improvement_hint": "Confirm scope on refactoring tasks",
  "level": 2
}
```

## Anti-patterns

**Too vague:**
```json
{
  "ts": "...",
  "type": "correction",
  "user_feedback": "wrong",
  "context": {"task": "coding"},
  "diagnosis": {"what_happened": "made mistake"}
}
```

**Missing diagnosis:**
```json
{
  "ts": "...",
  "user_feedback": "should have asked first",
  "context": {"task": "deleting files", "action": "deleted config.old"}
}
```

## Usage

The `/signal` command reads this format specification and produces signals conforming to it.

The review workflow (`guides/review-workflow.md`) reads signals in this format during analysis.
