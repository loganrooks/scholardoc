# ScholarDoc

## Quick Start
1. Read this file
2. Check ROADMAP.md for current phase
3. If implementing: Read SPEC.md relevant sections
4. If exploring: Check spikes/ for prior work
5. Run `/project:plan` before coding
6. Use Serena memories: `ocr_pipeline_architecture`, `session_handoff`

## Vision
ScholarDoc extracts structured knowledge from scholarly PDFs into `ScholarDocument` for RAG pipelines, Anki generation, citation management, and research organization.

**Core insight**: Separate *extraction* from *presentation*. ScholarDocument is the intermediate representation; Markdown is one output format.

See [docs/VISION.md](docs/VISION.md) for full vision and applications.

## Current Phase
**Phase 1: Core Implementation** - PDF reader and OCR pipeline
- **Current**: Integrate validated OCR pipeline into main module
- **Completed**: PDF reader, cascading extractor, OCR pipeline design
- See ROADMAP.md for full plan

## Stack
Python 3.11+ | PyMuPDF (fitz) | Pydantic | pytest + hypothesis | ruff | uv

## Quick Commands
```bash
uv sync && uv run pytest && uv run ruff check .
```
See [docs/COMMANDS.md](docs/COMMANDS.md) for full reference.

## Workflow
1. **Explore first** - Run spikes before implementing
2. **Check ROADMAP.md** for current phase
3. **Read SPEC.md** before writing code
4. **Check QUESTIONS.md** - don't implement unresolved decisions
5. **Write tests first** (TDD) - use `/project:tdd`

See [docs/RULES.md](docs/RULES.md) for complete guidelines.

## Git Workflow
**CRITICAL**: Use feature branches, never commit to main.
See [docs/GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md) for branching strategy.

## Architecture
Key decisions in docs/adr/:
- ADR-001: PDF library choice (PyMuPDF)
- ADR-002: OCR pipeline architecture (spellcheck as selector)
- ADR-003: Line-break detection (block-based filtering)

## Validation & Testing
Follow systematic methodology. Use FULL validation set, not subsets.
See [docs/TESTING_METHODOLOGY.md](docs/TESTING_METHODOLOGY.md) for complete guide.

## Automation
This project uses automated hooks. See [docs/AUTOMATION_SETUP.md](docs/AUTOMATION_SETUP.md).

**Pre-approved**: Read files, edit scholardoc/tests/spikes/docs, run uv/pytest/ruff/git
**Blocked**: rm -rf, sudo, git push --force, pip install

## MCP Servers
| Server | Purpose |
|--------|---------|
| **Serena** | Project memory, symbol operations |
| **Context7** | Library docs when needed |
| **Sequential** | Complex analysis when requested |
