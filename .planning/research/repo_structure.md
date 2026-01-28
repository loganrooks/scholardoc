# Repository Structure Research

**Domain:** Python monorepo vs multi-repo patterns for related scholarly packages
**Researched:** 2026-01-28
**Overall confidence:** MEDIUM-HIGH

## Context

Three related packages need a home:
- **ScholarDoc** — PDF extraction library (uv-managed, 395 tests)
- **CryptOfCogito** — Philosophy corpus app with annotation tool (FastAPI, SQLAlchemy, 20 ADRs)
- **scholarly_annotate** (proposed) — Shared annotation functionality

The question: monorepo, multi-repo with shared packages, or hybrid?

---

## 1. Monorepo vs Multi-Repo Trade-offs

### Monorepo Advantages
- **Atomic changes**: A schema change in the shared annotation library + consumers can land in one commit
- **Single lockfile**: uv workspaces produce one `uv.lock` — no dependency version drift between packages
- **Easier refactoring**: Move code between packages without cross-repo PRs
- **Shared CI**: One pipeline tests everything; changes to shared code automatically trigger downstream tests
- **Discoverability**: New contributors see the whole ecosystem in one clone

### Monorepo Disadvantages
- **Coupled release cycles**: Harder to version/release packages independently (solvable with tooling but adds complexity)
- **Docker build bloat**: Every Dockerfile must COPY the whole workspace or maintain precise COPY lines matching the dependency graph
- **IDE issues**: VSCode/Pylance can struggle with uv workspace imports — false lint errors on cross-package imports
- **Permission granularity**: Can't restrict write access per-package via GitHub (CODEOWNERS helps but isn't the same)
- **Git history noise**: `git log` for one package shows all commits unless you use path filters

### Multi-Repo Advantages
- **Independent lifecycles**: ScholarDoc can have a 1.0 release while CryptOfCogito is still 0.3
- **Clean boundaries enforced by default**: No accidental tight coupling
- **Simpler CI per repo**: Each repo's CI only runs its own tests
- **Existing structure**: Both repos already exist with their own histories

### Multi-Repo Disadvantages
- **Cross-repo changes are painful**: Shared schema change requires coordinated PRs across repos
- **Dependency version drift**: CryptOfCogito might pin scholardoc==0.4 while scholarly_annotate needs ==0.5
- **Code sharing requires publishing**: Must publish to PyPI (or private index) or use `pip install git+https://...`

### Recommendation: **Monorepo with uv workspaces**

**Why:** The packages are tightly coupled by domain (scholarly documents, annotations, ground truth schemas). The primary developer is a single person or small team. The Docker and IDE disadvantages are manageable. The cross-repo coordination cost of multi-repo would be the dominant friction for a project at this scale.

---

## 2. Python Code-Sharing Mechanisms

### Option A: uv Workspaces (Recommended)

```toml
# Root pyproject.toml
[tool.uv.workspace]
members = ["packages/*"]

# packages/scholardoc/pyproject.toml
[project]
dependencies = ["scholarly-annotate"]

[tool.uv.sources]
scholarly-annotate = { workspace = true }
```

- Single `uv.lock` at root, shared across all packages
- Each package has its own `pyproject.toml` with standard metadata
- `workspace = true` tells uv to resolve the dependency from the workspace, not PyPI
- Packages can still be published to PyPI independently
- **Confidence: HIGH** — Official uv documentation, Apache Airflow uses this at scale (120 pyproject.toml files)

### Option B: Namespace Packages

Use `scholarly.*` namespace (no `__init__.py` in the `scholarly` directory):
```
scholarly/
    doc/        # ScholarDoc
    annotate/   # scholarly_annotate
    corpus/     # CryptOfCogito
```

- Works with multi-repo or monorepo
- Native Python 3.3+ support (PEP 420 implicit namespace packages)
- **Caveat**: mypy has known issues with namespace packages; requires careful configuration
- **Caveat**: All sub-packages must consistently omit `__init__.py` at the namespace level — mixing breaks everything
- **Confidence: MEDIUM** — Well-documented pattern but adds complexity for marginal benefit at this scale

### Option C: pip install from git (Multi-repo fallback)

```toml
dependencies = ["scholardoc @ git+https://github.com/user/scholardoc.git@v1.0"]
```

- No publishing infrastructure needed
- Version pinning via git tags
- Slow installs (clones entire repo each time)
- No lock file coordination across repos
- **Confidence: HIGH** — Standard pip feature, well-understood

### Option D: git submodules

- Generally considered an anti-pattern for Python packages
- Adds cognitive overhead for every contributor
- Does not integrate with Python packaging tools
- **Recommendation: Avoid**

### Verdict

Use **uv workspaces** (Option A). Namespace packages (Option B) are orthogonal — you could adopt them later for the import paths if you want `scholarly.doc` instead of `scholardoc`, but this is cosmetic and not needed initially.

---

## 3. Monorepo Tooling Landscape

| Tool | Type | Python Support | Setup Effort | Best For |
|------|------|---------------|-------------|----------|
| **uv workspaces** | Package manager | Native | Low | Small-medium monorepos, single-team |
| **Pants** | Build system | Excellent | Medium | Medium-large monorepos, CI optimization |
| **Bazel** | Build system | Adequate | High | Very large polyglot repos (Google-scale) |
| **Hatch** | Package manager | Native | Low | Single-package or simple multi-package |
| **PDM** | Package manager | Native | Low | Similar to Hatch, less monorepo-focused |

### Recommendation: **uv workspaces now, Pants later if needed**

**Rationale:**
- ScholarDoc already uses uv — zero migration cost
- uv workspaces handle the core need: shared lockfile, cross-package dependencies, independent publishing
- Pants becomes worthwhile when CI time matters (10+ packages, 1000+ tests) — not needed yet with ~400 tests
- Bazel is overkill for a Python-only project of this size

### uv Workspaces: What You Get
- `uv lock` locks the entire workspace
- `uv run --package scholardoc pytest` runs tests for one package
- `uv sync --package scholardoc` installs only one package's deps
- Each package independently publishable to PyPI
- Single virtual environment at workspace root

### uv Workspaces: What You Don't Get
- No build caching (Pants/Bazel territory)
- No automatic "only test affected packages" (must script this yourself)
- No remote execution
- IDE support can be finicky (Pylance especially)

---

## 4. Migration Patterns: Merging Repos

### Recommended Approach: git subtree merge

ScholarDoc is the more active repo with 395 tests. Use it as the monorepo base and merge CryptOfCogito into it.

**Steps:**

```bash
# 1. In ScholarDoc repo, reorganize into packages/ subdirectory
mkdir -p packages/scholardoc
git mv src/ tests/ pyproject.toml packages/scholardoc/
git commit -m "chore: reorganize scholardoc into packages/ subdirectory"

# 2. Add CryptOfCogito as a remote
git remote add cogito ~/workspace/writings/PHL410_CryptOfCogito
git fetch cogito

# 3. Merge with history preservation
git merge cogito/main --allow-unrelated-histories --no-commit
# Move files into packages/crypt_of_cogito/
git mv [cogito files] packages/crypt_of_cogito/
git commit -m "chore: merge CryptOfCogito into monorepo"

# 4. Create root workspace pyproject.toml
# 5. Create packages/scholarly_annotate/ (new package)
# 6. Archive old CryptOfCogito repo
```

**Key points:**
- `--allow-unrelated-histories` preserves full commit history from both repos
- `git log --follow packages/crypt_of_cogito/somefile.py` will track history across the move
- Do the migration during a quiet period — warn collaborators
- Archive (don't delete) the old CryptOfCogito repo with a README pointing to the monorepo

### Alternative: Keep CryptOfCogito separate, extract shared code

If CryptOfCogito has a fundamentally different lifecycle (it's a writing/philosophy project, not a software product), consider:
1. Keep CryptOfCogito where it is
2. Extract `scholarly_annotate` as a package in the ScholarDoc monorepo
3. CryptOfCogito depends on `scholarly_annotate` via pip install from git or PyPI

**This is viable if** CryptOfCogito is more "consumer" than "co-developer" of the shared code.

---

## 5. Shared Ground Truth Data and Schemas

### The Problem

Ground truth (GT) data — annotated PDFs, expected extraction outputs, evaluation metrics — needs to be accessible to:
- ScholarDoc (for extraction quality testing)
- scholarly_annotate (for annotation validation)
- CryptOfCogito (for corpus-specific GT)

### Pattern A: Shared GT Package (Recommended for monorepo)

```
packages/
    scholardoc/
    scholarly_annotate/
    crypt_of_cogito/
    scholarly_testdata/          # Shared GT package
        pyproject.toml
        src/scholarly_testdata/
            schemas/             # Pydantic models for GT format
            fixtures/            # Sample PDFs, expected outputs
            conftest_plugin.py   # pytest plugin exposing fixtures
```

- Other packages declare `scholarly_testdata` as a dev dependency
- Pydantic schemas define the GT format — shared across all packages
- pytest fixtures exposed via plugin: `pytest_plugins = ["scholarly_testdata.conftest_plugin"]`

### Pattern B: Root-level conftest.py (Simpler)

```
conftest.py                     # Root conftest with shared fixtures
ground_truth/                   # GT data at repo root
    schemas/
    sample_pdfs/
    annotations/
packages/
    scholardoc/
    ...
```

- Root `conftest.py` defines fixtures that load from `ground_truth/`
- All packages automatically have access when tests run from root
- Simpler but less explicit about dependencies

### Pattern C: Git LFS for Large GT Files

If GT data includes large PDFs or binary files:
```bash
git lfs track "ground_truth/**/*.pdf"
git lfs track "ground_truth/**/*.png"
```

- Keeps repo clone fast
- PDF samples and scanned images don't bloat git history
- **Already relevant**: ScholarDoc has sample PDFs in `spikes/sample_pdfs/`

### Recommendation

Use **Pattern A** (shared GT package) for schemas and fixtures, combined with **Pattern C** (Git LFS) for binary test data. The GT package gives you:
- Explicit dependency declaration
- Version-controlled schema evolution
- Reusable pytest fixtures
- Clean separation of test infrastructure from production code

---

## Proposed Monorepo Structure

```
scholarly-workspace/                    # or just keep as "scholardoc"
    pyproject.toml                      # Workspace root
    uv.lock                            # Single lockfile
    README.md
    .planning/                         # Planning docs (existing)
    ground_truth/                      # GT data (existing, move here)
        sample_pdfs/
        annotations/
    packages/
        scholardoc/
            pyproject.toml
            src/scholardoc/
            tests/
        scholarly_annotate/
            pyproject.toml
            src/scholarly_annotate/
            tests/
        crypt_of_cogito/
            pyproject.toml
            src/crypt_of_cogito/
            tests/
        scholarly_testdata/             # Shared test fixtures
            pyproject.toml
            src/scholarly_testdata/
                schemas/
                fixtures/
```

Root `pyproject.toml`:
```toml
[project]
name = "scholarly-workspace"
version = "0.1.0"
requires-python = ">=3.11"

[tool.uv.workspace]
members = ["packages/*"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| uv workspaces | HIGH | Official docs, major adopters (Airflow), well-documented |
| Monorepo vs multi-repo trade-offs | HIGH | Well-established patterns, extensive community discussion |
| Git migration | HIGH | Multiple verified approaches, standard git features |
| Shared GT patterns | MEDIUM | Assembled from multiple patterns; no single authoritative source |
| Pants/Bazel comparison | MEDIUM | Based on community reports, not hands-on verification |

## Sources

- [uv Workspaces — Official Documentation](https://docs.astral.sh/uv/concepts/projects/workspaces/)
- [FOSDEM 2026 — Modern Python monorepo with uv (Apache Airflow)](https://fosdem.org/2026/schedule/event/WE7NHM-modern-python-monorepo-apache-airflow/)
- [JasperHG90/uv-monorepo — Example repo](https://github.com/JasperHG90/uv-monorepo)
- [Python Workspaces (Monorepos) — Tomas Repcik](https://tomasrepcik.dev/blog/2025/2025-10-26-python-workspaces/)
- [Releasing a Monorepo using uv Workspace — Medium](https://medium.com/@asafshakarzy/releasing-a-monorepo-using-uv-workspace-and-python-semantic-release-0dafc889f4cc)
- [Packaging namespace packages — Python Packaging User Guide](https://packaging.python.org/en/latest/guides/packaging-namespace-packages/)
- [Our Python Monorepo — Opendoor Engineering](https://medium.com/opendoor-labs/our-python-monorepo-d34028f2b6fa)
- [Migrating Git from multirepo to monorepo — Netlify](https://developers.netlify.com/guides/migrating-git-from-multirepo-to-monorepo-without-losing-history/)
- [Moving to a monorepo — Alex Harri](https://alexharri.com/blog/move-to-monorepo)
- [Using Pants to Manage a Python Monorepo — Earthly](https://earthly.dev/blog/pants-python-monorepo/)
- [Comparing Bazel, Lerna, Nx, and Pants — Graphite](https://graphite.com/guides/monorepo-tooling-comparison)
- [Sharing data between test fixtures — pytest issue #1571](https://github.com/pytest-dev/pytest/issues/1571)
- [Python Monorepo: an Example — Tweag](https://www.tweag.io/blog/2023-04-04-python-monorepo-1/)
