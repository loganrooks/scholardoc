<purpose>
Automate the full release cycle: version bump, changelog update, git tag, push, and GitHub Release creation. This workflow handles safety checks, version computation, changelog formatting, and publishing. If the project has a CI workflow triggered by GitHub Releases (e.g., publish.yml), it will be triggered automatically.
</purpose>

<required_reading>
Read `package.json` and `CHANGELOG.md` from the project root before starting. These are the two files that will be modified during the release.
</required_reading>

<process>

<step name="pre-flight-checks">
**Step 1: Pre-flight checks**

Verify the repository is in a safe state before making any mutations.

Run these three checks and abort immediately if any fail:

1. **Clean working tree:**
   Run `git status --porcelain` and check the output is empty.
   If dirty, tell the user: "Working tree is dirty. Commit or stash changes first." and STOP.

2. **On main branch:**
   Run `git branch --show-current` and verify it returns `main`.
   If not on main, tell the user: "Must be on main branch to release. Current branch: {branch}" and STOP.

3. **Remote is up to date:**
   Run `git fetch origin main` then `git diff HEAD origin/main --quiet`.
   If the diff is non-empty (exit code non-zero), tell the user: "Local main is behind origin. Pull first." and STOP.

All three must pass before continuing.
</step>

<step name="determine-bump-type">
**Step 2: Determine bump type**

Read the current version from package.json:
```bash
node -p "require('./package.json').version"
```

Store as `CURRENT_VERSION`.

Check if `$ARGUMENTS` was provided by the invoking command:

- If `$ARGUMENTS` is `patch`, `minor`, or `major`, use that directly as `BUMP_TYPE`. Skip to Step 3.
- If `$ARGUMENTS` is empty or not one of the above, analyze commits to recommend a bump type.

**Auto-detection (when no argument provided):**

Get commits since last tag:
```bash
git log $(git describe --tags --abbrev=0)..HEAD --oneline
```

Categorize the commits:
- Commits starting with `fix:` or `fix(` count toward **patch**
- Commits starting with `feat:` or `feat(` count toward **minor**
- Commits containing `BREAKING CHANGE` or starting with `feat!:` or `fix!:` count toward **major**
- If no conventional commits found, default to **patch**

Determine recommendation: major > minor > patch (highest severity wins).

Present the analysis to the user using AskUserQuestion:
```
Header: "Release Bump Recommendation"
Question: "Recommended bump: {BUMP_TYPE}\n\nCommits since last tag:\n{commit list}\n\nProceed with {BUMP_TYPE}? (yes/patch/minor/major/abort)"
```

Handle the user response:
- "yes" or empty: use the recommended BUMP_TYPE
- "patch", "minor", or "major": override with that bump type
- "abort": STOP immediately, do not proceed
</step>

<step name="compute-new-version">
**Step 3: Compute new version**

Parse `CURRENT_VERSION` as X.Y.Z (split on dots into MAJOR, MINOR, PATCH integers).

Apply the bump:
- **patch**: increment Z (MAJOR.MINOR.PATCH+1)
- **minor**: increment Y, reset Z to 0 (MAJOR.MINOR+1.0)
- **major**: increment X, reset Y and Z to 0 (MAJOR+1.0.0)

Store the result as `NEW_VERSION`.
</step>

<step name="dry-run-summary">
**Step 4: Dry-run summary**

Display the release plan to the user (output directly, not via AskUserQuestion):

```
Release Summary:
  Current version: {CURRENT_VERSION}
  New version:     {NEW_VERSION}
  Bump type:       {BUMP_TYPE}
  Tag:             reflect-v{NEW_VERSION}
  Branch:          main
```

Then confirm with the user using AskUserQuestion:
```
Header: "Confirm Release"
Question: "Proceed with release v{NEW_VERSION}? (yes/abort)"
```

If the user says "abort" or anything other than "yes", STOP immediately.
</step>

<step name="bump-version">
**Step 5: Bump version in package.json**

Update the version field in package.json:
```bash
node -e "const p=require('./package.json'); p.version='${NEW_VERSION}'; require('fs').writeFileSync('package.json', JSON.stringify(p, null, 2) + '\n')"
```

Verify the update took effect:
```bash
node -p "require('./package.json').version"
```

The output must match `NEW_VERSION`. If it does not, abort with an error.

Then stamp the version into the config template:
```bash
node scripts/stamp-version.js
```

This ensures the template's `gsd_reflect_version` matches the new version before the release commit.
</step>

<step name="update-changelog">
**Step 6: Update CHANGELOG.md**

Read `CHANGELOG.md` using the Read tool.

Find the `## [Unreleased]` line. Find the content between `## [Unreleased]` and the next `## [` line -- this is the unreleased content.

Use the Edit tool to replace the `## [Unreleased]` section. The result should look like:

```markdown
## [Unreleased]

## [{NEW_VERSION}] - {TODAY}
```

Where `{TODAY}` is today's date in YYYY-MM-DD format.

The unreleased content (everything that was between `## [Unreleased]` and the next version header) goes under the new `## [{NEW_VERSION}]` header.

If the unreleased content is empty (no changes listed between `[Unreleased]` and the previous version), generate placeholder content by extracting key commits from `git log $(git describe --tags --abbrev=0)..HEAD --oneline` and organizing them into appropriate `### Added`, `### Changed`, or `### Fixed` sections based on commit prefixes.
</step>

<step name="commit-tag-push">
**Step 7: Commit, tag, and push**

Stage the modified files:
```bash
git add package.json CHANGELOG.md get-shit-done/templates/config.json
```

Create the release commit:
```bash
git commit -m "release: v${NEW_VERSION}"
```

Create an annotated tag:
```bash
git tag -a "reflect-v${NEW_VERSION}" -m "reflect-v${NEW_VERSION}"
```

Push the commit and tag to origin:
```bash
git push origin main
git push origin "reflect-v${NEW_VERSION}"
```
</step>

<step name="create-github-release">
**Step 8: Create GitHub Release**

Extract the changelog section for this version. Read CHANGELOG.md and extract the content between `## [{NEW_VERSION}]` and the next `## [` header. Write this content to a temporary file:
```bash
# Write extracted notes to temp file
cat > /tmp/release-notes-${NEW_VERSION}.md << 'NOTES_EOF'
{extracted changelog content}
NOTES_EOF
```

Create the GitHub Release:
```bash
gh release create "reflect-v${NEW_VERSION}" --title "reflect-v${NEW_VERSION}" --notes-file /tmp/release-notes-${NEW_VERSION}.md
```

This triggers the `publish.yml` workflow which handles npm publish automatically.
</step>

<step name="completion">
**Step 9: Completion output**

Display the final summary:

First, get the repo URL dynamically:
```bash
REPO_URL=$(gh repo view --json url -q .url 2>/dev/null || git remote get-url origin | sed 's/\.git$//' | sed 's|git@github.com:|https://github.com/|')
```

Then display:
```
---
Release v{NEW_VERSION} complete!

  package.json: {NEW_VERSION}
  CHANGELOG.md: updated
  Git tag:      reflect-v{NEW_VERSION}
  GitHub Release: {REPO_URL}/releases/tag/reflect-v{NEW_VERSION}

  If this repo has CI triggered by releases (e.g., npm publish), it will run automatically.
  Monitor: {REPO_URL}/actions
---
```
</step>

</process>

<success_criteria>
- [ ] Pre-flight checks pass (clean tree, main branch, up to date)
- [ ] Version bumped in package.json
- [ ] CHANGELOG.md updated with new version section and today's date
- [ ] Git commit created with message "release: vX.Y.Z"
- [ ] Annotated git tag reflect-vX.Y.Z created
- [ ] Commit and tag pushed to origin
- [ ] GitHub Release created (triggers npm publish via publish.yml)
</success_criteria>
