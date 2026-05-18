# Version Migration Specification

Reference specification for GSD Reflect version migration behavior. Enables projects initialized under older versions to catch up to new features without re-initialization.

## Overview

Projects evolve alongside the GSD Reflect framework. When new versions introduce configurable features, existing projects need a way to adopt those features without starting over.

**Two mechanisms:**
1. **Auto-detect (primary):** A SessionStart hook (`hooks/gsd-version-check.js`) compares the installed version against the project version on every session start, caching the result. Commands like `/gsd:health-check` read this cache and trigger migration when needed.
2. **Explicit (secondary):** The `/gsd:upgrade-project` command provides a direct escape hatch for users who want to migrate on demand.

**Core principle:** Migrations are ALWAYS additive. New config fields are added with sensible defaults. New directories are created if needed. Templates are updated. Nothing is removed. Nothing existing is modified. This guarantees backward compatibility -- a migrated project behaves identically to before unless the user explicitly changes a new setting.

**Fork constraint compliance:** The version check is a new hook file (additive). Config changes are new fields only. No existing files are modified in ways that change behavior.

## Version Detection

**Installed version** is read from the VERSION file:
1. Check project-local install first: `{project}/.claude/get-shit-done/VERSION`
2. Fall back to global install: `./.claude/get-shit-done/VERSION`
3. If neither exists: skip migration check (cannot determine installed version)

**Project version** is read from `.planning/config.json`:
- Field: `gsd_reflect_version`
- If the field is absent: project is "pre-tracking" (treat as version `0.0.0`)
- If `.planning/config.json` does not exist: project is not initialized (not a migration issue)

**Version comparison** uses simple numeric dot-separated comparison:

```bash
# Compare installed version vs project version
INSTALLED=$(cat ./.claude/get-shit-done/VERSION 2>/dev/null || echo "0.0.0")
PROJECT=$(cat .planning/config.json 2>/dev/null | grep -o '"gsd_reflect_version"[[:space:]]*:[[:space:]]*"[^"]*"' | grep -o '[0-9][0-9.]*' || echo "0.0.0")

# Simple numeric comparison (split on dots)
IFS='.' read -r inst_major inst_minor inst_patch <<< "$INSTALLED"
IFS='.' read -r proj_major proj_minor proj_patch <<< "$PROJECT"

NEEDS_MIGRATION=false
if [ "$inst_major" -gt "$proj_major" ] 2>/dev/null || \
   ([ "$inst_major" -eq "$proj_major" ] && [ "$inst_minor" -gt "$proj_minor" ]) 2>/dev/null || \
   ([ "$inst_major" -eq "$proj_major" ] && [ "$inst_minor" -eq "$proj_minor" ] && [ "$inst_patch" -gt "$proj_patch" ]) 2>/dev/null; then
  NEEDS_MIGRATION=true
fi
```

## Migration Rules

**Additive only:** Every migration action adds something new without touching existing values.

| Action | Allowed | Not Allowed |
|--------|---------|-------------|
| Add new config field with default | Yes | Change existing field values |
| Add new directory | Yes | Remove existing directories |
| Add new template sections | Yes | Restructure existing templates |
| Update `gsd_reflect_version` | Yes | Remove any existing field |
| Add new files | Yes | Delete existing files |

**Default values:** Every new field has a sensible default that preserves existing behavior. A project that migrates without changing any setting behaves identically to before.

### Migration Actions

Migration actions are now manifest-driven. Running `manifest apply-migration` reads `feature-manifest.json`, detects config gaps, fills missing features/fields with schema defaults, and coerces mismatched types.

**To see what would change:** `node ./.claude/get-shit-done/bin/gsd-tools.js manifest diff-config --raw`
**To apply changes:** `node ./.claude/get-shit-done/bin/gsd-tools.js manifest apply-migration --raw`

Adding a new feature requires only adding it to `feature-manifest.json`. The migration commands automatically handle existing projects.

### Future Migrations

Adding new features follows the same pattern: add the feature schema to `feature-manifest.json`. The `apply-migration` command automatically detects and fills gaps.

## Mini-Onboarding

When migration introduces new configurable features, the user may be prompted for preferences.

**YOLO mode:** Apply all defaults silently. Log what was added. No questions asked.

**Interactive mode:** Use `AskUserQuestion` for each new feature section. Keep questions minimal (2-3 max per migration).

### Onboarding Questions

Questions and options for each feature are declared in `feature-manifest.json` via `init_prompts`. Use `manifest get-prompts <feature>` to retrieve them.

**YOLO mode:** Apply all defaults silently. Log what was added. No questions asked.

**Interactive mode:** Use `AskUserQuestion` for each feature's prompts. Features with `_gate` prompts allow the user to skip configuration entirely (accepting all defaults).

## Migration Log

Each migration is recorded in `.planning/migration-log.md` for audit trail.

**Location:** `.planning/migration-log.md`
**Format:** Append-only markdown. New entries are prepended (most recent first).

### Migration Log Template

```markdown
# Migration Log

Tracks version upgrades applied to this project.

## {source_version} -> {target_version} ({ISO_timestamp})

### Changes Applied
- {description of each field/section added}

### User Choices
- {setting}: {chosen value}

---

*Log is append-only. Each migration is recorded when applied.*
```

### Example Entry

```markdown
## 0.0.0 -> 1.12.0 (2026-02-10T14:30:00Z)

### Changes Applied
- Added `gsd_reflect_version: "1.12.0"` to config.json
- Added `health_check` section to config.json
- Added `devops` section to config.json

### User Choices
- Health check frequency: milestone-only (default)
- Health check blocking: false (default)
- DevOps context: skipped (defaults applied)

---
```

## Auto-Detect Mechanism

The SessionStart hook (`hooks/gsd-version-check.js`) runs on every session start. It performs version detection only -- it does NOT execute migrations.

**Hook behavior:**
1. Read installed VERSION file (project-local first, then global)
2. Read `.planning/config.json` field `gsd_reflect_version`
3. Compare versions numerically
4. Write result to `./.claude/cache/gsd-version-check.json`

**Cache format:**
```json
{
  "project_needs_migration": true,
  "installed": "1.12.0",
  "project": "0.0.0",
  "project_config": "/absolute/path/to/.planning/config.json",
  "checked": 1707580200
}
```

**Cache consumers:**
- `/gsd:upgrade-project` reads cache to skip redundant version detection
- `/gsd:health-check` reads cache to report version mismatch as a finding
- Neither consumer trusts stale cache -- they re-verify if cache is older than current session

**Hook constraints:**
- Local file reads ONLY (no npm registry calls -- that is `/gsd:update`'s job)
- Sub-millisecond execution target
- Background spawn pattern (non-blocking)
- If `.planning/config.json` does not exist: `project_needs_migration: false` (not initialized)
- If `gsd_reflect_version` field is absent: `project: "0.0.0"`, `project_needs_migration: true`

## Error Handling

| Scenario | Behavior | Severity |
|----------|----------|----------|
| Missing `.planning/config.json` | Not a migration issue (project not initialized). Skip. | Silent |
| Missing VERSION file | Cannot determine installed version. Skip migration check. | Silent |
| JSON parse failure on config.json | Report as health check issue. Skip migration. | Warning |
| Field write failure during migration | Log failure. Continue with partial migration. Report what succeeded/failed. | Warning |
| Missing `.planning/` directory | Project not initialized. Skip. | Silent |

**Blocking behavior:**
- Critical failures that should block: none for migration (migration is best-effort)
- All migration issues are warnings, not blockers
- The `blocking_checks` config field applies to health check findings, not migration itself

**Partial migration recovery:**
- If migration fails partway through, the fields that were added remain
- Next migration attempt detects which fields exist and only adds missing ones
- The `gsd_reflect_version` field is updated LAST (only after all other changes succeed)
- This ensures a partial migration is retried on next run
