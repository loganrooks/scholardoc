# ScholarDoc Git Workflow

## Branch Strategy

**CRITICAL: Use feature branches for ALL work. Never commit directly to main.**

### Branch Naming

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feature/` | New functionality | `feature/ocr-pipeline` |
| `fix/` | Bug fixes | `fix/heading-detection` |
| `refactor/` | Code improvements | `refactor/extractor-cleanup` |
| `docs/` | Documentation only | `docs/api-reference` |

### Workflow

```bash
# Start new work
git checkout main
git pull origin main
git checkout -b feature/<name>

# During work - commit frequently
git add -A
git commit -m "feat: description"

# Ready for review
git push -u origin feature/<name>
gh pr create --title "feat: <name>" --body "## Summary\n..."

# After PR approval
git checkout main
git pull origin main
git branch -d feature/<name>
```

## Commit Message Format

Format: `type: description`

| Type | Purpose |
|------|---------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation |
| `test:` | Tests |
| `refactor:` | Code improvement |
| `chore:` | Maintenance |

### Good Examples
```
feat: add OCR confidence scoring
fix: handle empty page in extractor
docs: update API reference for ScholarDocument
test: add property tests for line break detection
refactor: simplify cascading extractor logic
```

### Bad Examples
```
update code          # Too vague
fixed stuff          # No context
WIP                  # Not descriptive
```

## Pre-Commit Checklist

Before committing:
- [ ] Tests pass (`uv run pytest`)
- [ ] Linting passes (`uv run ruff check .`)
- [ ] Code is formatted (`uv run ruff format .`)
- [ ] No secrets or credentials in code

## Protected Operations

These are blocked by hooks:
- `git push --force` to main
- `git reset --hard` on main
- Direct commits to main (without PR)
