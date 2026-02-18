---
description: Stop and reflect - capture correction with full context
allowed-tools: Bash(mkdir:*), Bash(date:*), Write, Read, mcp__serena__*
argument-hint: "[optional: what went wrong]"
---

# Signal: $ARGUMENTS

**MODE: STOP, REFLECT, LEARN**

The user has indicated something went wrong. This is valuable feedback. Don't just log it - understand it, capture meaningful context, and adjust.

---

## Step 1: Pause and Acknowledge

Stop whatever you were doing. The user is giving you important feedback.

Say: "Let me stop and understand what went wrong."

---

## Step 2: Reflect on Recent Actions

Before asking the user, first reflect on what YOU were just doing:

- What task was I working on?
- What was my last action/tool call?
- What approach was I taking?
- What assumptions was I making?

Summarize this briefly (2-3 sentences) to show the user you're aware of context.

---

## Step 3: Understand the Issue

**If $ARGUMENTS provides clear feedback:**
- Acknowledge what they said
- Confirm your understanding: "So the issue was [X], and you wanted [Y] instead?"

**If $ARGUMENTS is vague or empty:**
- Ask a focused clarifying question: "Can you tell me what specifically was wrong - was it the approach, the output, something I missed?"
- Keep it to ONE question, not a list

**Wait for user response if clarification needed.**

---

## Step 4: Diagnose Root Cause

Once you understand the issue, briefly diagnose:

```
What happened: [concrete description]
Why it happened: [your hypothesis - assumption? missing context? wrong approach?]
What should have happened: [the better path]
```

Share this diagnosis with the user: "I think the issue was [X]. Does that sound right?"

---

## Step 5: Capture Rich Signal

Read the signal format specification:
- **Format spec**: `.claude/guides/signal-format.md`

Create a signal conforming to that format:

```bash
mkdir -p .claude/signals
```

Append to `.claude/signals/corrections.jsonl` using the schema from the format spec.

---

## Step 6: Decide on Immediate Action

Ask the user:

**Option A**: "Should I adjust my approach now and continue with [better approach]?"

**Option B**: "Should I undo what I just did and try again?"

**Option C**: "Should we move on - this is noted for future improvement?"

Act based on their response.

---

## Step 7: Confirm and Continue

Brief confirmation:

```
Understood. Signal captured:
- Issue: [one line summary]
- Adjustment: [what you're doing differently, if anything]

Continuing with [next action]...
```

---

## What Makes a Good Signal

See `.claude/guides/signal-format.md` for full schema and examples.

Key qualities:
- **Rich context**: Task, action, approach captured
- **Clear diagnosis**: What happened, why, what should have happened
- **Actionable hint**: Specific improvement suggestion
- **Level classified**: Systemic (1) or project-specific (2)

A good signal has enough context to be actionable during weekly review without needing to reconstruct what happened.

---

## Level Classification

While capturing, determine if this is systemic or project-specific:

| Level | Indicator | Example |
|-------|-----------|---------|
| Level 2 | Specific to this project's context | "Should use our existing auth module" |
| Level 1 | Would happen in other projects too | "Should check for existing libraries first" |

If Level 1, this signal may be escalated to claude-enhanced during review.

---

## Examples

**User runs:** `/signal`
```
Claude: "Let me stop and understand what went wrong.

I was just [modifying the database schema to add a new column].

Can you tell me what specifically was wrong - was it the approach, the output, something I missed?"

User: "You didn't create a migration file"

Claude: "Ah, I see. I directly modified the schema without creating a migration.

- What happened: Modified schema.prisma directly
- Why: I focused on the model change and forgot the migration step
- Should have: Run `prisma migrate dev` to create a proper migration

This is a workflow issue - I should always create migrations for schema changes.

Should I create the migration now, or undo my changes first?"
```

**User runs:** `/signal should have asked before deleting`
```
Claude: "Let me stop and understand.

I was just [cleaning up unused files] and deleted [config.old.json].

You're right - I should have asked before deleting files, even ones that look unused.

- What happened: Deleted file without confirmation
- Why: Assumed .old suffix meant it was safe to remove
- Should have: Asked 'Can I delete config.old.json?' before removing

This is Level 1 - I should always confirm before destructive actions.

Signal captured. I'll ask before deleting files going forward. Should I try to restore that file?"
```

---

## Anti-patterns

- **Don't just log and continue**: The old approach. Useless without context.
- **Don't be defensive**: The user is helping you improve.
- **Don't over-apologize**: Acknowledge, understand, adjust. Move on.
- **Don't ask 20 questions**: One clarifying question max, then diagnose.
