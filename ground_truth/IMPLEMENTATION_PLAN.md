# Ground Truth Tooling Implementation Plan

**Created**: 2026-01-08
**Status**: Active
**Scope**: Annotation UI Phase 1 + Evaluation Library Full Phase

## Overview

Implement two components in parallel:
1. **Annotation UI** - Streamlit app for viewing/editing ground truth YAML
2. **Evaluation Library** - Python modules for pipeline comparison

## Dependencies to Add

```toml
# pyproject.toml [project.optional-dependencies]
ground-truth = [
    "streamlit>=1.30.0",
    "streamlit-ace>=0.1.0",
    "rapidfuzz>=3.0.0",    # Fast string matching
    "tabulate>=0.9.0",     # CLI table output
]
```

## Component 1: Annotation UI

### File Structure
```
ground_truth/scripts/
├── annotate_ui.py         # NEW - Main Streamlit app
├── ui_components.py       # NEW - Reusable UI components
├── visualize.py           # MODIFY - Extract render_page_image()
├── validate.py            # REUSE as-is
└── generate_draft.py      # REUSE as-is
```

### Tasks

#### Task 1.1: Refactor visualize.py for Streamlit
**Given** visualize.py has render_page_with_annotations() that outputs bytes
**When** I extract a render_page_image() function
**Then** It returns PIL Image instead of HTML, accepts highlight_region_id param

```python
def render_page_image(
    pdf_path: Path,
    page_idx: int,
    regions: list[dict],
    dpi: int = 150,
    highlight_region_id: str | None = None
) -> Image.Image:
    """Render PDF page with bbox overlays."""
```

#### Task 1.2: Create UI skeleton (annotate_ui.py)
**Given** Streamlit is installed
**When** I run `streamlit run ground_truth/scripts/annotate_ui.py`
**Then** App launches with sidebar + main area layout

Components:
- Sidebar: mode selection, PDF/YAML picker, page nav
- Main: placeholder columns for PDF viewer and YAML editor

#### Task 1.3: Implement PDF viewer
**Given** A ground truth YAML is loaded
**When** User navigates pages
**Then** Rendered page with bboxes displays in left column

#### Task 1.4: Implement YAML editor
**Given** streamlit-ace is available
**When** User views a document
**Then** YAML appears in syntax-highlighted editor, editable

#### Task 1.5: Implement validation display
**Given** User clicks Validate
**When** Validation runs via validate.py
**Then** Errors/warnings display in expandable section

#### Task 1.6: Implement save functionality
**Given** User clicks Save
**When** Validation passes
**Then** YAML writes to ground_truth/documents/, index.yaml updates

#### Task 1.7: Add annotation status management
**Given** Status selectors in sidebar
**When** User changes element status (pending→annotated→verified)
**Then** annotation_status section updates in YAML

## Component 2: Evaluation Library

### File Structure
```
ground_truth/
├── lib/
│   ├── __init__.py        # NEW
│   ├── normalize.py       # NEW - GT/predicted normalization
│   ├── matching.py        # NEW - Element matching
│   ├── metrics.py         # NEW - Metric computation
│   └── reports.py         # NEW - Report generation
└── scripts/
    └── evaluate.py        # NEW - CLI interface
```

### Tasks

#### Task 2.1: Create normalize.py
**Given** Ground truth YAML and ScholarDocument
**When** I call normalize functions
**Then** Both convert to list[GroundTruthElement] for comparison

```python
@dataclass
class GroundTruthElement:
    element_type: str      # "footnote", "citation", etc.
    element_id: str
    page: int
    text: str
    char_offset: int | None
    char_length: int | None
    attributes: dict
    tags: list[str]

def load_ground_truth_elements(yaml_path: Path) -> list[GroundTruthElement]
def scholar_doc_to_elements(doc: ScholarDocument) -> list[GroundTruthElement]
```

#### Task 2.2: Create matching.py
**Given** Two lists of normalized elements
**When** I call match_elements()
**Then** Returns list of ElementMatch with match_type and similarity

```python
@dataclass
class ElementMatch:
    ground_truth: GroundTruthElement | None
    predicted: GroundTruthElement | None
    match_type: Literal['exact', 'partial', 'missed', 'spurious']
    similarity_score: float
    error_details: dict | None

def match_elements(
    ground_truth: list[GroundTruthElement],
    predicted: list[GroundTruthElement],
    element_type: str,
    config: MatchConfig
) -> list[ElementMatch]
```

#### Task 2.3: Create metrics.py
**Given** List of ElementMatch
**When** I call compute_metrics()
**Then** Returns ElementMetrics with precision, recall, F1

```python
@dataclass
class ElementMetrics:
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float  # computed property
    recall: float     # computed property
    f1: float         # computed property
    mean_text_similarity: float

def compute_metrics(matches: list[ElementMatch]) -> ElementMetrics
def aggregate_metrics(by_type: dict[str, ElementMetrics]) -> AggregateMetrics
```

#### Task 2.4: Create reports.py
**Given** Evaluation results
**When** I call generate_report()
**Then** Outputs CLI table, JSON, or HTML report

```python
def generate_cli_report(metrics: AggregateMetrics) -> str
def generate_json_report(metrics: AggregateMetrics) -> dict
def generate_html_report(metrics: AggregateMetrics, output_path: Path) -> None
```

#### Task 2.5: Create evaluate.py CLI
**Given** PDF path and ground truth YAML
**When** I run `python -m ground_truth.scripts.evaluate`
**Then** Runs extraction, compares, outputs report

```bash
uv run python -m ground_truth.scripts.evaluate \
    --pdf spikes/sample_pdfs/foo.pdf \
    --ground-truth ground_truth/documents/foo.yaml \
    --output results.json
```

## Testing Strategy

### Unit Tests
```
tests/unit/ground_truth/
├── test_normalize.py      # Test normalization functions
├── test_matching.py       # Test element matching
├── test_metrics.py        # Test metric computation
└── test_validate.py       # Test validation (existing)
```

### Integration Tests
```
tests/integration/
└── test_evaluation_pipeline.py  # End-to-end evaluation
```

### Test Data
- Create minimal test YAML in tests/fixtures/ground_truth/
- Mock ScholarDocument for matching tests

## Task Dependencies

```
[Add deps to pyproject.toml]
        ↓
   ┌────┴────┐
   ↓         ↓
[Task 1.1]  [Task 2.1]
Refactor    normalize.py
visualize
   ↓         ↓
[Task 1.2]  [Task 2.2]
UI skeleton matching.py
   ↓         ↓
[Task 1.3]  [Task 2.3]
PDF viewer  metrics.py
   ↓         ↓
[Task 1.4]  [Task 2.4]
YAML editor reports.py
   ↓         ↓
[Task 1.5]  [Task 2.5]
Validation  evaluate.py
   ↓         ↓
[Task 1.6]  [Tests]
Save
   ↓
[Task 1.7]
Status mgmt
   ↓
[Tests]
```

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Streamlit state management complexity | Medium | Medium | Use session_state carefully, test edge cases |
| Large PDF slow rendering | Medium | Low | Cache rendered pages with @st.cache_resource |
| YAML sync issues | Medium | Medium | YAML editor as source of truth, validate before save |
| No test PDFs available | Low | High | Create minimal test fixtures |

## Success Criteria

1. `streamlit run ground_truth/scripts/annotate_ui.py` launches without error
2. Can load existing YAML, view pages, edit YAML, validate, save
3. `uv run python -m ground_truth.scripts.evaluate --help` shows options
4. Can evaluate mock ground truth against mock extraction
5. All tests pass, ruff clean
6. README updated with usage instructions

## Estimated Complexity

- **Annotation UI**: ~400-500 lines across 2 files
- **Evaluation Library**: ~600-700 lines across 5 files
- **Tests**: ~300-400 lines
- **Total**: ~1300-1600 lines new code
