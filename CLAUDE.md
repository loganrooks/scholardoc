# ScholarDoc

## Quick Start for AI Assistants
1. Read this file completely
2. Check ROADMAP.md for current phase (Phase 1: OCR pipeline integration)
3. If implementing: Read SPEC.md relevant sections
4. If exploring: Check spikes/ for prior work
5. Run `/project:plan` before coding
6. Use Serena memories: `ocr_pipeline_architecture`, `session_2025-12-23_validation_framework`

## Vision
<!-- AUTHORITATIVE: All other docs should reference this section, not duplicate it -->
<!-- Last verified: 2025-12-23 -->

ScholarDoc extracts structured knowledge from scholarly PDFs into a flexible intermediate representation (`ScholarDocument`) designed for multiple downstream applications:

**Primary Applications:**
- **RAG pipelines** — Clean text with position-accurate metadata for retrieval
- **Anki/flashcard generation** — Structured content with citation tracking
- **Research organization** — Metadata-rich documents for knowledge management
- **Citation management** — Page numbers, references, bibliography extraction

**Additional Applications:**
- **Knowledge graphs** — Semantic linking between documents and concepts
- **Literature review tools** — Cross-document analysis and comparison
- **Academic writing assistants** — Source material with accurate citations
- **Accessibility** — Clean text for text-to-speech, screen readers
- **Search/indexing systems** — Structured data for advanced queries
- **Custom applications** — Extensible output formats (Markdown, JSON, custom)

**Core Insight:** Separate *extraction* (getting clean, structured data) from *presentation* (formatting for specific use cases). The `ScholarDocument` is the intermediate representation; Markdown is one output format, not the goal.

## Current Phase
**Phase 1: Core Implementation** - PDF reader and OCR pipeline
**Current Task:** Integrate validated OCR pipeline into main module
**Completed:** PDF reader, cascading extractor, OCR pipeline design (validated)
See spikes/FINDINGS.md for exploration results, ROADMAP.md for full plan.

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
- docs/adr/ - Architecture Decision Records:
  - ADR-001: PDF library choice (PyMuPDF)
  - ADR-002: OCR pipeline architecture (spellcheck as selector)
  - ADR-003: Line-break detection (block-based filtering)
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

# OCR pipeline validation
uv run python spikes/29_ocr_pipeline_design.py              # OCR pipeline design/testing
uv run python spikes/30_validation_framework.py             # Build/test validation set

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
- `/project:improve [trigger]` - Self-improvement review (see protocol below)
- `/project:resume` - Restore context from previous session
- `/project:checkpoint <note>` - Save current state mid-session

### If Hooks Block You
If automated checks prevent legitimate work:
1. Explain what you're trying to do and why
2. Human can approve exception
3. Document why bypass was needed

### Self-Improvement Protocol

**Triggers** — When to run `/project:improve`:
- After PR merge (especially if it required multiple iterations)
- After repeated errors (same issue 2+ times in session)
- Weekly maintenance (during active development)
- After context loss requiring re-explanation

**Review Process:**

1. **Analyze Session Logs** (`.claude/logs/`)
   - Pattern: Same error appearing in multiple sessions?
   - Pattern: Repeated questions about same topic?
   - Pattern: Workflow steps that could be automated?

2. **Check Serena Memories** (`list_memories()`)
   - Are memories still accurate? Update or delete stale ones
   - Should recent learnings become memories?
   - Is `project_vision` still current?

3. **Review Recent Git History**
   - Commits requiring follow-up fixes → prevention rule needed?
   - PRs with extensive back-and-forth → unclear docs?
   - Reverted commits → what was missed?

**Integration Actions:**

| Finding | Action | Location |
|---------|--------|----------|
| Repeated error | Add prevention rule | CLAUDE.md rules or hook |
| Missing context | Create Serena memory | `write_memory()` |
| Unclear workflow | Update command | `.claude/commands/` |
| Doc confusion | Clarify docs | Reference CLAUDE.md#Vision |
| Tool misuse | Add usage note | AI Config section |

**Tracking:**
Improvements logged in Serena memory `improvement_log`:
- Date, trigger, finding, action taken, files modified

### Session Management

Context preservation across sessions to minimize re-explanation.

**Commands:**
- `/project:resume` — Restore context from previous session (reads `session_handoff` memory)
- `/project:checkpoint <note>` — Save current state mid-session (before risky ops)

**Key Memories:**
| Memory | Purpose |
|--------|---------|
| `session_handoff` | What was worked on, accomplished, next steps |
| `decision_log` | Architectural decisions with rationale |
| `project_vision` | Canonical project description (AUTHORITATIVE) |
| `checkpoint_*` | Mid-session state snapshots |

**Session Lifecycle:**
1. **Start**: Run `/project:resume` to restore context
2. **During**: Use `/project:checkpoint` before major changes
3. **End**: Update `session_handoff` memory (prompted by stop-verify hook)

**Decision Log Format:**
When making architectural decisions, add to `decision_log` memory:
```
## YYYY-MM-DD: [Decision Title]
**Decision**: [What was decided]
**Rationale**: [Why this choice]
**Trade-offs**: [Downsides and mitigations]
```

---

## AI Assistant Configuration

### MCP Servers
| Server | Purpose |
|--------|---------|
| **Serena** | Project memory, symbol operations. Use `project_vision` memory for canonical description. |
| **Context7** | Library docs (PyMuPDF, Pydantic, pytest) when needed. |
| **Sequential** | Complex analysis when explicitly requested. |

### Code Exploration
For OCR-related code understanding, prefer precision over speed:
- Use Serena's `find_symbol`, `get_symbols_overview` (main model, precise)
- Read files directly when understanding algorithm decisions
- Reserve Task/Explore agents for broad "where is X" questions only

### Hooks (Advisory Only)
All hooks inject context, never block operations:
- Quality checks → warnings, not hard stops
- Pre-commit → checklists, not prevention
- Only catastrophic operations are blocked (rm -rf /, fork bombs)

### Version Control Workflow

**🔴 CRITICAL: Use feature branches for ALL work, never commit directly to main.**

```bash
# Start new work
git checkout -b feature/<name>    # e.g., feature/ocr-pipeline

# During work
git add -A && git commit -m "feat: description"

# Ready for review
git push -u origin feature/<name>
gh pr create --title "feat: <name>" --body "## Summary\n..."

# After PR approval
git checkout main && git pull
git branch -d feature/<name>
```

**Branch Naming:**
- `feature/<name>` - New functionality
- `fix/<issue>` - Bug fixes
- `refactor/<area>` - Code improvements
- `docs/<topic>` - Documentation only

**Commit Message Format:** `type: description`
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `test:` tests
- `refactor:` code improvement
- `chore:` maintenance

---

## OCR Pipeline Architecture

See ADR-002 and ADR-003 for full details. Key decisions:

### Spellcheck as Selector
- Spellcheck FLAGS suspicious words, does NOT auto-correct
- Flagged words go to neural re-OCR for verification
- Detection rate: 99.2%, False positive rate: 23.4%

### Line-Level Re-OCR
- Neural OCR needs visual context (word-level crops fail)
- Crop the LINE from page image, not just the word
- Replace only the flagged words after re-OCR

### Block-Based Line-Break Detection
- PyMuPDF block numbers distinguish text regions from margins
- Only rejoin hyphenations within the SAME block
- Prevents matching margin content (page markers, headers)

### Adaptive Dictionary
- Learn specialized vocabulary with safeguards
- Morphological validation (plurals, verb forms, prefixes)
- Frequency thresholds to avoid learning OCR errors

---

## Validation & Testing Methodology

**CRITICAL: Follow these rules to avoid procedural mistakes.**

### Ground Truth Data
- **Location:** `ground_truth/` directory
- **Validation set:** `ground_truth/validation_set.json` (generated by spike 30)
- **Use the FULL validation set**, not just a subset (e.g., 130 pairs, not 30)

### Before Optimizing Anything
1. **Inventory your data** - Know what ground truth exists
2. **Build a proper validation set** - Use `spikes/30_validation_framework.py`
3. **Establish baseline metrics** - Measure BEFORE changing anything
4. **Define success criteria** - What detection rate is acceptable?

### Metrics to Track
- **Detection rate** - % of OCR errors caught (target: >99%)
- **False positive rate** - % of correct words flagged (target: <10%)
- **Re-OCR volume** - % of words sent to expensive neural re-OCR
- **Processing time** - ms per page (for performance optimization)

### Testing Rules
- **Test on the FULL validation set**, not cherry-picked examples
- **Report false negatives** - These are critical failures
- **Report false positives** - These waste resources but aren't critical
- **Measure timing** - We're optimizing for speed too

### Common Mistakes to Avoid
1. ❌ Testing on tiny subsets (30 examples) when thousands exist
2. ❌ Proposing pipelines without actually testing them
3. ❌ Ignoring edge cases found during testing
4. ❌ Not measuring performance/timing impact
5. ❌ Optimizing accuracy without considering resource cost

### Ground Truth Organization
```
ground_truth/
├── ocr_errors/
│   ├── ocr_error_pairs.json    # 30 verified pairs (high quality)
│   ├── validated_samples.json   # Additional validated samples
│   └── challenging_samples.json # Edge cases
├── ocr_quality/
│   ├── classified/             # 172 pages, 17k evidence entries
│   ├── samples/                # Per-document sample reviews
│   └── reviewed/               # Human-reviewed batches
├── footnotes/                   # Footnote ground truth
└── validation_set.json         # COMBINED validation set (use this!)
```
