<purpose>
Migrate the current project's GSD Reflect configuration to match the installed version. Adds new config fields with sensible defaults, prompts for preferences on new features (in interactive mode), and logs the migration.

This workflow does NOT spawn subagents -- it executes migration logic directly (mechanical config patching + optional questions).
</purpose>

<core_principle>
Upgrades are additive and non-destructive. Existing settings are preserved exactly as they are. Only new fields are added. The version stamp is updated last, ensuring partial migrations are retried on the next run.
</core_principle>

<required_reading>
Read version-migration.md for migration principles and log format. Feature-specific migration actions come from the manifest via `manifest apply-migration`.
Read ui-brand.md for output formatting conventions.
Read .planning/config.json for current project configuration.
</required_reading>

<process>

<step name="detect_versions">
## 1. Detect Versions

Read the installed version:
1. Check `{project}/.claude/get-shit-done/VERSION` first (local install)
2. Fall back to `./.claude/get-shit-done/VERSION` (global install)
3. If neither exists: report "Cannot determine installed version. Run `/gsd:update` first." and exit.

Read the project version:
1. Read `.planning/config.json`
2. If file does not exist: report "Project not initialized. Run `/gsd:new-project` first." and exit.
3. Extract `gsd_reflect_version` field
4. If field is absent: project version is `0.0.0` (pre-tracking)
</step>

<step name="compare_versions">
## 2. Compare Versions

Compare installed vs project using numeric dot-separated comparison (split on dots, compare major.minor.patch).

**If versions match:** Report "Project is up to date (version {version})" and exit.

**If installed version is BEHIND project version:** Report "Installed GSD Reflect version ({installed}) is older than project version ({project}). Run `/gsd:update` to get the latest version." and exit.

**If installed version is AHEAD of project version:** Proceed with migration.
</step>

<step name="display_banner">
## 3. Display Migration Banner

```
## Project Migration: {old_version} -> {new_version}

Migrating project configuration to match installed GSD Reflect version.
All changes are additive -- existing settings are preserved.
```
</step>

<step name="determine_mode">
## 4. Determine Mode

Check if `--auto` flag was passed in arguments OR if `.planning/config.json` has `"mode": "yolo"`:
- If `--auto` or YOLO mode: apply all defaults silently (no questions)
- If interactive mode (no `--auto`): run mini-onboarding questions for new features
</step>

<step name="apply_patches">
## 5. Apply Additive Config Patches

Run manifest diff to detect config gaps:
```bash
DIFF=$(node ./.claude/get-shit-done/bin/gsd-tools.js manifest diff-config --raw)
```

Parse the JSON result. Extract `missing_features`, `missing_fields`, and `type_mismatches`.

**If no gaps found** (all arrays empty and `manifest_version` matches `config_manifest_version`):
Report "Config is up to date" and skip to Step 6.

**In YOLO/auto mode:** Apply all defaults without prompting:
```bash
RESULT=$(node ./.claude/get-shit-done/bin/gsd-tools.js manifest apply-migration --raw)
```

**In interactive mode:** For each missing feature:
1. Get prompts: `node ./.claude/get-shit-done/bin/gsd-tools.js manifest get-prompts <feature> --raw`
2. Check for `_gate` prompt (field === "_gate"):
   - If present: ask the gate question first via AskUserQuestion
   - If user selects `skip_value`: skip remaining prompts, feature gets all defaults
   - If user selects other value: continue with remaining prompts
3. For each non-gate prompt: present question and options via AskUserQuestion
4. Write user choices: `node ./.claude/get-shit-done/bin/gsd-tools.js config-set <config_key>.<field> <value>`
5. After all user choices, fill remaining defaults and coerce types:
   ```bash
   node ./.claude/get-shit-done/bin/gsd-tools.js manifest apply-migration --raw
   ```

Update version stamps LAST (only after all changes succeed):
```bash
node ./.claude/get-shit-done/bin/gsd-tools.js config-set gsd_reflect_version "<installed_version>"
```

This ensures partial migrations are retried on next run.
</step>

<step name="log_migration">
## 6. Log Migration

Log the migration using the changes from Step 5:
```bash
node ./.claude/get-shit-done/bin/gsd-tools.js manifest log-migration --from "<old_version>" --to "<new_version>" --changes '<changes_json_from_step_5>' --raw
```

The `--changes` argument is the `changes` array from the `manifest apply-migration` output in Step 5. If interactive mode added user choices via `config-set`, include those as additional `field_added` entries in the changes array.
</step>

<step name="report_results">
## 7. Report Results

Display a summary of what changed:

```
### Migration Complete: {old} -> {new}

**Changes applied:**
- {list of fields/sections added}

**User choices:**
- {setting}: {value}

Migration logged to `.planning/migration-log.md`
```
</step>

</process>

<error_handling>
**No VERSION file found:** Direct user to run `/gsd:update` first.
**No config.json:** Direct user to run `/gsd:new-project` first.
**Versions already match:** Report up-to-date status and exit cleanly.
**Installed behind project:** Warn user and suggest `/gsd:update`.
**Config write failure:** Report error, do NOT update version stamp (ensures retry on next run).
</error_handling>
