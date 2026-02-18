# Release Guide

## Purpose

Ship reliable releases with proper versioning, documentation, and communication.

## Principles

1. **Automate everything possible** - Reduce human error
2. **Version semantically** - Communicate change impact
3. **Document changes** - Users need to know what changed
4. **Test before release** - Verify on clean environment
5. **Make rollback easy** - Plan for problems

## Release Process

### Phase 1: PREPARE

```
1. Ensure all PRs merged to main
2. Run full test suite
3. Review pending changes since last release
4. Determine version bump (major/minor/patch)
5. Create release branch if using gitflow
```

### Phase 2: VERSION

Semantic Versioning (MAJOR.MINOR.PATCH):
```
- MAJOR: Breaking changes (users must update code)
- MINOR: New features (backwards compatible)
- PATCH: Bug fixes (backwards compatible)
```

Update version in:
```
- package.json / pyproject.toml / Cargo.toml
- __version__ or VERSION constant
- Documentation references
```

### Phase 3: CHANGELOG

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New feature A
- New feature B

### Changed
- Modified behavior X

### Fixed
- Bug fix for issue #123

### Deprecated
- Feature Y (will be removed in X+1.0.0)

### Removed
- Feature Z (deprecated in X-1.0.0)

### Security
- Fixed vulnerability in dependency
```

### Phase 4: TEST

```
1. Clean install from scratch
2. Run full test suite
3. Manual smoke test of key features
4. Test upgrade path from previous version
5. Verify documentation accuracy
```

### Phase 5: RELEASE

```bash
# Tag the release
git tag -a vX.Y.Z -m "Release X.Y.Z"
git push origin vX.Y.Z

# Publish (language-specific)
npm publish           # Node
python -m build && twine upload dist/*  # Python
cargo publish         # Rust

# Create GitHub release
gh release create vX.Y.Z --notes-file RELEASE_NOTES.md
```

### Phase 6: ANNOUNCE

```
1. GitHub release notes
2. Project blog/changelog
3. Social media if appropriate
4. Notify dependent projects
```

## Versioning Guidelines

### Pre-release Versions
```
1.0.0-alpha.1   # Early testing
1.0.0-beta.1    # Feature complete, testing
1.0.0-rc.1      # Release candidate
1.0.0           # Stable release
```

### Breaking Change Checklist
Before bumping major version:
- [ ] Migration guide written
- [ ] Deprecation warnings in previous version
- [ ] Upgrade path documented
- [ ] Timeline communicated

## Quality Criteria

A good release:
- [ ] All tests pass on clean environment
- [ ] Version follows semantic versioning
- [ ] Changelog documents all notable changes
- [ ] Release notes highlight important items
- [ ] Documentation updated for new features
- [ ] Breaking changes have migration guide

## Anti-patterns

- **YOLO releases**: No testing before publish
- **Version inflation**: Major bump for minor changes
- **Silent breaking changes**: No documentation of impact
- **Missing changelog**: Users can't see what changed
- **Stale docs**: Documentation doesn't match release
- **No rollback plan**: Can't recover from bad release

## Adaptation Notes

When generating for a project:
- Use project's specific package manager commands
- Reference project's CI/CD release workflow
- Include project's changelog format
- Note project's release branch strategy
- Include any project-specific release checklist items
