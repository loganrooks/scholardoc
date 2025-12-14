---
description: Run exploration spike on a PDF
allowed-tools: Read, Edit, Write, Bash(uv:*), Bash(ls:*), Bash(cat:*), Glob, Grep
argument-hint: <spike-number> <pdf-path>
---

# Spike: $ARGUMENTS

## Available Spikes

| # | Script | Purpose |
|---|--------|---------|
| 01 | `01_pymupdf_exploration.py` | Explore PyMuPDF output |
| 02 | `02_library_comparison.py` | Compare PDF libraries |
| 03 | `03_heading_detection.py` | Test heading strategies |
| 04 | `04_footnote_detection.py` | Test footnote strategies |
| 05 | `05_ocr_quality_survey.py` | Evaluate OCR quality |
| 06 | `06_ground_truth.py` | Build evaluation corpus |
| 07 | `07_annotation_review.py` | Review annotations |

## Running the Spike

Based on your arguments, run the appropriate spike:

```bash
# Example: spike 01 on a PDF
uv run python spikes/01_pymupdf_exploration.py <pdf-path> --all

# Example: spike 02 comparison
uv run python spikes/02_library_comparison.py <pdf-path>
```

## After Running

1. Analyze the output
2. Document findings in `spikes/FINDINGS.md`
3. Update relevant sections based on what we learned
4. Note any surprises or assumptions invalidated

## Findings Template

Add to `spikes/FINDINGS.md`:

```markdown
## Spike XX: [Name] - [PDF Name]

**Date:** YYYY-MM-DD
**PDF:** [filename]

### Observations
- ...

### Surprises
- ...

### Implications for Design
- ...

### Questions Raised
- ...
```

## Current Phase

We're in Phase 0 (Exploration). The goal is to validate assumptions
before implementation. Document everything!
