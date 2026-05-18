---
name: gsd:release
description: Bump version, update changelog, tag, and create GitHub Release (v1.16.0+dev)
argument-hint: "[patch|minor|major]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---
<objective>
Automate the full release cycle: version bump, changelog update, git tag, and GitHub Release creation.

Usage: `/gsd:release [patch|minor|major]`

If bump type is provided, skip recommendation and use it directly.
If omitted, analyze commits since last tag and recommend a bump type.

**Executes:**
- Pre-flight safety checks (clean tree, main branch, remote sync)
- Version bump in package.json
- CHANGELOG.md update (moves [Unreleased] content under new version header)
- Git commit and annotated tag
- Push to origin
- GitHub Release creation (triggers npm publish via CI)
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/release.md
</execution_context>

<context>
@package.json
@CHANGELOG.md

Bump type: $ARGUMENTS (may be empty -- workflow handles auto-detection)
</context>

<process>
Execute the release workflow from @./.claude/get-shit-done/workflows/release.md end-to-end.
Pass $ARGUMENTS as bump type (may be empty).
</process>
