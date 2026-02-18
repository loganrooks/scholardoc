# Ground Truth Evaluation Framework

Tools for creating, validating, and evaluating ground truth annotations against ScholarDoc extraction results.

## Quick Start

```bash
# Install dependencies
uv sync --extra ground-truth

# Run annotation UI
uv run streamlit run ground_truth/scripts/annotate_ui.py

# Evaluate extraction against ground truth
uv run python -m ground_truth.scripts.evaluate \
    --ground-truth ground_truth/documents/test.yaml

# Validate a ground truth file
uv run python ground_truth/scripts/validate.py ground_truth/documents/test.yaml

# Generate HTML visualization
uv run python ground_truth/scripts/visualize.py ground_truth/documents/test.yaml
```

## Components

### Annotation UI (`annotate_ui.py`)

Streamlit-based interface for viewing and editing ground truth YAML files.

Features:
- PDF viewer with region overlays
- YAML editor with syntax highlighting
- Validation against schema
- Save functionality

### Evaluation Library (`lib/`)

Python library for comparing extraction results to ground truth.

```python
from ground_truth.lib import (
    load_ground_truth_elements,
    match_elements,
    compute_metrics,
    aggregate_metrics,
)

# Load ground truth
gt_elements = load_ground_truth_elements("ground_truth/documents/test.yaml")

# Match against predictions
matches = match_elements(gt_elements, pred_elements, "footnote")

# Compute metrics
metrics = compute_metrics(matches)
print(f"F1: {metrics.f1:.3f}")
```

### CLI Evaluation (`evaluate.py`)

Command-line tool for running evaluations.

```bash
# Basic evaluation
uv run python -m ground_truth.scripts.evaluate \
    --ground-truth ground_truth/documents/test.yaml

# With PDF extraction
uv run python -m ground_truth.scripts.evaluate \
    --pdf spikes/sample_pdfs/test.pdf \
    --ground-truth ground_truth/documents/test.yaml

# Output to JSON
uv run python -m ground_truth.scripts.evaluate \
    --ground-truth ground_truth/documents/test.yaml \
    --output results.json

# Compare to baseline
uv run python -m ground_truth.scripts.evaluate \
    --ground-truth ground_truth/documents/test.yaml \
    --baseline ground_truth/baselines/current.json \
    --fail-on-regression
```

### Validation (`validate.py`)

Schema validation for ground truth YAML files.

```bash
# Validate single file
uv run python ground_truth/scripts/validate.py ground_truth/documents/test.yaml

# Validate multiple files
uv run python ground_truth/scripts/validate.py ground_truth/documents/*.yaml

# Strict mode (treat warnings as errors)
uv run python ground_truth/scripts/validate.py --strict ground_truth/documents/test.yaml
```

### Visualization (`visualize.py`)

Generate HTML visualizations of ground truth annotations.

```bash
uv run python ground_truth/scripts/visualize.py ground_truth/documents/test.yaml
```

## Directory Structure

```
ground_truth/
├── README.md                  # This file
├── SCHEMA.md                  # Ground truth schema specification
├── ANNOTATION_UI_DESIGN.md    # UI design document
├── PIPELINE_INTEGRATION.md    # Integration architecture
├── TESTING_METHODOLOGY.md     # Evaluation methodology
├── documents/                 # Ground truth YAML files
├── baselines/                 # Baseline metrics for regression
├── lib/                       # Evaluation library
│   ├── normalize.py          # Element normalization
│   ├── matching.py           # Element matching
│   ├── metrics.py            # Metric computation
│   └── reports.py            # Report generation
└── scripts/
    ├── annotate_ui.py        # Streamlit annotation UI
    ├── evaluate.py           # CLI evaluation tool
    ├── generate_draft.py     # Auto-generate draft YAML
    ├── validate.py           # Schema validation
    └── visualize.py          # HTML visualization
```

## Schema

See [SCHEMA.md](SCHEMA.md) for the full ground truth schema specification.

Key concepts:
- **Document-scoped elements**: Footnotes, citations, etc. at document level
- **Multi-page support**: Elements can span pages
- **Three-state verification**: pending → annotated → verified
- **Normalized bboxes**: 0-1 coordinates, resolution-independent

## Metrics

The evaluation framework computes:

| Metric | Description |
|--------|-------------|
| Precision | TP / (TP + FP) - how many predictions are correct |
| Recall | TP / (TP + FN) - how many ground truth elements found |
| F1 | Harmonic mean of precision and recall |
| Micro F1 | F1 computed from total counts across all types |
| Macro F1 | Average F1 across element types |
| Text Similarity | Average text match score for matched elements |

## Development

```bash
# Run tests
uv run pytest tests/unit/ground_truth/ -v

# Check lint
uv run ruff check ground_truth/
```
