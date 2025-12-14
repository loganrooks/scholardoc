# ScholarDoc

## About
Python library for converting scholarly documents (PDF → Markdown) optimized for RAG pipelines. Preserves structure, page numbers, and metadata that researchers need. See REQUIREMENTS.md for full scope.

## Current Phase
**Phase 0: Exploration** - Validate assumptions before detailed design  
**Current Task:** Run spikes on sample PDFs, document findings  
See spikes/FINDINGS.md for exploration status, ROADMAP.md for full plan.

## Stack
- Python 3.11+
- PyMuPDF (fitz) - PDF extraction (see docs/adr/ADR-001)
- Pydantic - data models
- pytest, hypothesis, ruff, uv - dev tooling

## Documentation
- REQUIREMENTS.md - User stories, acceptance criteria
- SPEC.md - Technical specification (DRAFT - pending spike validation)
- ROADMAP.md - Phased development plan with OCR vision
- QUESTIONS.md - Open questions needing resolution
- spikes/FINDINGS.md - Exploration results
- docs/adr/ - Architecture Decision Records
- docs/design/ - Future feature design docs (e.g., CUSTOM_OCR_DESIGN.md)

**Read relevant docs before implementing.** Don't invent requirements.

## Commands
```bash
uv sync                    # Install deps
uv sync --extra comparison # Include comparison libraries for spikes
uv run pytest             # Run tests
uv run ruff check .       # Lint
uv run ruff format .      # Format

# Exploration spikes (run before implementing!)
uv run python spikes/01_pymupdf_exploration.py <pdf> --all  # Explore PyMuPDF
uv run python spikes/02_library_comparison.py <pdf>         # Compare libraries
uv run python spikes/03_heading_detection.py <pdf>          # Test heading strategies
uv run python spikes/04_footnote_detection.py <pdf>         # Test footnote strategies
uv run python spikes/05_ocr_quality_survey.py <pdf>         # Evaluate existing OCR quality

# Ground truth workflow (Claude + Human)
# Step 1: Claude annotates (use /project:annotate command or agent)
# Step 2: Human reviews flagged items
uv run python spikes/07_annotation_review.py review <annotations.yaml> --pdf <pdf>
# Step 3: Validate
uv run python spikes/07_annotation_review.py validate <annotations.yaml>
```

## Workflow
1. **Explore first** - Run spikes before implementing (spikes/)
2. Check ROADMAP.md for current phase/milestone
3. Read SPEC.md before writing code (note DRAFT sections)
4. Check QUESTIONS.md - don't implement unresolved decisions
5. Write tests first (TDD) - use `/project:tdd`
6. Update spikes/FINDINGS.md with discoveries

## Rules
ALWAYS:
- Run exploration spikes before implementing new features
- Consult SPEC.md for data models and API design
- Write tests before implementation
- Graceful degradation over hard failures
- Preserve source information (page numbers, positions)

NEVER:
- Implement features not validated by spikes
- Trust SPEC.md over empirical findings
- Make architectural decisions without ADR
- Skip the planning documents
- Add chunking (out of scope - see REQUIREMENTS.md)

---

## Automation & Guardrails

This project uses automated hooks for quality control. See `docs/AUTOMATION_SETUP.md` for full details.

### Pre-Approved Operations (No confirmation needed)
- Read any file
- Edit files in: `scholardoc/`, `tests/`, `spikes/`, `docs/`
- Run: `uv sync/run/add`, `pytest`, `ruff`, `git status/diff/log/add/commit`
- Standard file operations: `ls`, `cat`, `grep`, `find`, `mkdir`, `cp`, `mv`

### Blocked Operations (Will be denied)
- `rm -rf`, `rm -r` (use explicit file deletion)
- `sudo` anything
- `git push --force`, `git reset --hard`
- `pip install` (use `uv add`)
- Piping to shell (`curl | sh`)

### Automatic Quality Checks
After editing Python files:
- `ruff format` runs automatically
- `ruff check --fix` runs automatically
- Related tests run (if they exist)

Before stopping:
- All tests must pass
- No linting errors
- Uncommitted changes are flagged

### Workflow Commands
Use these for structured work:
- `/project:implement <feature>` - TDD workflow (tests first)
- `/project:tdd` - Start test-driven cycle
- `/project:plan` - Create implementation plan
- `/project:review` - Review recent changes
- `/project:annotate <pdf>` - Ground truth annotation

### If Hooks Block You
If automated checks prevent legitimate work:
1. Explain what you're trying to do and why
2. Human can approve exception
3. Document why bypass was needed

### Self-Improvement
Session logs are kept in `.claude/logs/`. Periodically review for:
- Repeated errors → add rules to prevent
- Common patterns → add to CLAUDE.md
- Workflow friction → improve commands/hooks
