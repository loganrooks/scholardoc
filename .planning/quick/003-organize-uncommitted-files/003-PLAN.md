---
phase: quick
plan: 003
type: execute
wave: 1
depends_on: []
files_modified:
  - .gitignore
  - .claude/agents/*.md
  - .claude/commands/gsd/*.md
  - .claude/get-shit-done/**
  - .claude/gsd-file-manifest.json
  - .claude/gsd-local-patches/**
  - .planning/phases/01.1-schema-taxonomy-review-revision/.continue-here.md
  - .planning/phases/01.1-schema-taxonomy-review-revision/01.1-05-SUMMARY.md
autonomous: true
requirements: []
must_haves:
  truths:
    - "DifficultTexts directory and its contents are gitignored"
    - "GSD framework update files are committed as a single logical commit"
    - "Phase 01.1 completion artifacts are committed as a separate logical commit"
    - "No uncommitted tracked files remain after execution"
  artifacts:
    - path: ".gitignore"
      provides: "Entry ignoring spikes/sample_pdfs/DifficultTexts/"
      contains: "spikes/sample_pdfs/DifficultTexts/"
  key_links: []
---

<objective>
Organize all uncommitted files on branch feature/01.1-01-foundation-types into logical commits or gitignore them.

Purpose: Clean working tree so the branch is ready for PR or next phase work.
Output: Three actions — gitignore corpus files, commit GSD framework update, commit phase 01.1 completion artifacts.
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/execute-plan.md
@./.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.gitignore
</context>

<tasks>

<task type="auto">
  <name>Task 1: Gitignore DifficultTexts corpus directory</name>
  <files>.gitignore</files>
  <action>
Add a gitignore entry for the entire DifficultTexts directory. The `*.pdf` pattern already
covers individual PDFs, but the directory also contains 165 non-PDF working files (task specs,
verification reports, audit notes, working scripts) that are local corpus artifacts and should
not be committed.

Add this entry under the existing "# Project specific" section in .gitignore:

```
spikes/sample_pdfs/DifficultTexts/
```

Place it after the existing `spikes/output/` line. This ignores the entire 291MB directory
(PDFs + working notes) as local corpus data.

Verify git no longer shows `spikes/sample_pdfs/DifficultTexts/` as untracked after the change.
  </action>
  <verify>
Run `git status spikes/sample_pdfs/DifficultTexts/` — should show nothing (fully ignored).
Run `git check-ignore spikes/sample_pdfs/DifficultTexts/` — should print the path.
  </verify>
  <done>DifficultTexts directory is fully gitignored and does not appear in git status.</done>
</task>

<task type="auto">
  <name>Task 2: Commit GSD framework update and phase 01.1 completion artifacts</name>
  <files>
.gitignore
.claude/agents/*.md
.claude/commands/gsd/*.md
.claude/get-shit-done/VERSION
.claude/get-shit-done/bin/gsd-tools.cjs
.claude/get-shit-done/bin/gsd-tools.test.cjs
.claude/get-shit-done/workflows/*.md
.claude/gsd-file-manifest.json
.claude/gsd-local-patches/
.planning/phases/01.1-schema-taxonomy-review-revision/.continue-here.md
.planning/phases/01.1-schema-taxonomy-review-revision/01.1-05-SUMMARY.md
  </files>
  <action>
Create two logical commits in sequence:

**Commit 1: GSD framework update to v1.20.5**
Stage and commit all .claude/ files (modified agents, commands, workflows, VERSION, tools,
manifest, and the new gsd-local-patches/ directory). These are all from a GSD framework
version update and belong together.

Files to stage:
- All modified .claude/agents/*.md files
- All modified .claude/commands/gsd/*.md files
- .claude/get-shit-done/VERSION
- .claude/get-shit-done/bin/gsd-tools.cjs
- .claude/get-shit-done/bin/gsd-tools.test.cjs
- All modified .claude/get-shit-done/workflows/*.md files
- .claude/gsd-file-manifest.json
- .claude/gsd-local-patches/ (new directory)

Commit message: "chore: update GSD framework to v1.20.5"

**Commit 2: Phase 01.1 completion + gitignore update**
Stage and commit the phase 01.1 artifacts along with the .gitignore update from Task 1.

Files to stage:
- .gitignore
- .planning/phases/01.1-schema-taxonomy-review-revision/.continue-here.md
- .planning/phases/01.1-schema-taxonomy-review-revision/01.1-05-SUMMARY.md

Commit message: "docs(phase-1.1): add final summary and gitignore corpus files"
  </action>
  <verify>
Run `git status` — should show clean working tree (no modified, no untracked except ignored files).
Run `git log --oneline -3` — should show the two new commits with correct messages.
  </verify>
  <done>
Working tree is clean. Two commits exist: GSD framework update and phase 01.1 completion.
No uncommitted tracked files remain.
  </done>
</task>

</tasks>

<verification>
- `git status` shows clean working tree
- `git log --oneline -3` shows two new logical commits
- `git check-ignore spikes/sample_pdfs/DifficultTexts/` confirms ignored
- No binary or large files were committed
</verification>

<success_criteria>
1. DifficultTexts/ directory is gitignored (not in git status)
2. GSD framework files committed as one logical unit
3. Phase 01.1 artifacts committed as separate logical unit
4. Working tree is clean
</success_criteria>

<output>
No summary file needed for quick plans.
</output>
