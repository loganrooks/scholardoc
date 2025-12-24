---
description: Release preparation and changelog generation
allowed-tools: Read, Glob, Grep, Bash(git:*), Bash(ls:*), Bash(uv run pytest:*), Bash(uv run ruff:*)
argument-hint: [version]
---

# Release: $ARGUMENTS

**MODE: RELEASE PREPARATION**

## Pre-Release Checklist

### 1. Branch Status
```bash
git status
git log --oneline main..HEAD
```

- [ ] On correct branch (feature branch or release branch)
- [ ] All changes committed
- [ ] Branch is up to date with main

### 2. Quality Gates

Run all quality checks:
```bash
uv run ruff check .
uv run pytest
```

- [ ] All tests pass
- [ ] No linting errors
- [ ] No type errors (if applicable)

### 3. Documentation Review

- [ ] README is up to date
- [ ] API changes documented
- [ ] Breaking changes noted
- [ ] Examples work with new code

## Changelog Generation

### Gather Changes
Review commits since last release:
```bash
git log --oneline $(git describe --tags --abbrev=0 2>/dev/null || echo "main")..HEAD
```

### Categorize Changes

**Added**: New features
**Changed**: Changes to existing functionality
**Deprecated**: Features to be removed in future
**Removed**: Features removed in this release
**Fixed**: Bug fixes
**Security**: Security-related changes

### Format

```markdown
## [version] - YYYY-MM-DD

### Added
- Feature description (#PR)

### Changed
- Change description (#PR)

### Fixed
- Bug fix description (#PR)
```

## Version Bump

Semantic versioning:
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

Check current version in:
- pyproject.toml
- __init__.py (if applicable)
- Other version references

## Final Checks

Before merging:
- [ ] Version number updated
- [ ] Changelog updated
- [ ] All CI checks pass
- [ ] PR description complete
- [ ] Reviewed by human (if required)

## Post-Release

After merge:
- [ ] Tag the release: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- [ ] Push tags: `git push --tags`
- [ ] Update any deployment/release documentation

## Important

- Don't rush releases - quality over speed
- When in doubt, get human review
- Document breaking changes clearly
