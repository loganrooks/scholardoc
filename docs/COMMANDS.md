# ScholarDoc Commands Reference

## Development Commands

```bash
# Environment Setup
uv sync                    # Install dependencies
uv sync --extra comparison # Include comparison libraries for spikes

# Quality Checks
uv run pytest             # Run tests
uv run ruff check .       # Lint
uv run ruff format .      # Format
```

## Exploration Spikes

**Run spikes BEFORE implementing new features.**

```bash
# Core exploration
uv run python spikes/01_pymupdf_exploration.py <pdf> --all  # Explore PyMuPDF
uv run python spikes/02_library_comparison.py <pdf>         # Compare libraries
uv run python spikes/03_heading_detection.py <pdf>          # Test heading strategies
uv run python spikes/04_footnote_detection.py <pdf>         # Test footnote strategies
uv run python spikes/05_ocr_quality_survey.py <pdf>         # Evaluate OCR quality

# OCR pipeline validation
uv run python spikes/29_ocr_pipeline_design.py              # OCR pipeline design/testing
uv run python spikes/30_validation_framework.py             # Build/test validation set
```

## Ground Truth Workflow

```bash
# Step 1: Claude annotates (use /project:annotate command)
# Step 2: Human reviews flagged items
uv run python spikes/07_annotation_review.py review <annotations.yaml> --pdf <pdf>
# Step 3: Validate
uv run python spikes/07_annotation_review.py validate <annotations.yaml>
```

## Claude Code Commands

### Discovery & Planning
- `/project:explore <topic>` - Read-only investigation
- `/project:plan <feature>` - Create implementation plan
- `/project:spike <topic>` - Exploration spike

### Implementation
- `/project:implement <feature>` - TDD workflow
- `/project:tdd` - Start test-driven cycle
- `/project:refactor <code>` - Safe refactoring
- `/project:document <target>` - Generate documentation

### Quality & Review
- `/project:review` - Review recent changes
- `/project:debug <error>` - Systematic debugging

### Release & Maintenance
- `/project:release [version]` - Release preparation
- `/project:improve [trigger]` - Self-improvement review

### Session Management
- `/project:resume` - Restore context from previous session
- `/project:checkpoint <note>` - Save current state mid-session

### Specialized
- `/project:annotate <pdf>` - Ground truth annotation
- `/project:auto <feature>` - Autonomous development mode
