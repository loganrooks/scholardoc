# Pipeline Integration Design

**Version**: 1.0.0
**Created**: 2026-01-07
**Status**: Planning

## Overview

This document defines how ground truth YAML files integrate with the ScholarDoc extraction pipeline for evaluation, comparison, and improvement.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Evaluation Pipeline                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐    │
│  │  Source PDF  │────▶│  Extractor   │────▶│  ScholarDocument     │    │
│  └──────────────┘     │  (Pipeline)  │     │  (Predicted)         │    │
│                       └──────────────┘     └──────────┬───────────┘    │
│                                                       │                 │
│  ┌──────────────┐                                     │                 │
│  │ Ground Truth │                                     ▼                 │
│  │    YAML      │────────────────────────▶ ┌──────────────────────┐    │
│  └──────────────┘                          │     Comparator       │    │
│                                            │  (Element Matcher)   │    │
│                                            └──────────┬───────────┘    │
│                                                       │                 │
│                                                       ▼                 │
│                                            ┌──────────────────────┐    │
│                                            │   Evaluation Report  │    │
│                                            │  - Metrics per type  │    │
│                                            │  - Error analysis    │    │
│                                            │  - Recommendations   │    │
│                                            └──────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Ground Truth → Normalized Format

Ground truth YAML uses document-centric schema. For comparison, convert to element list:

```python
@dataclass
class GroundTruthElement:
    """Normalized element for comparison."""
    element_type: str          # "footnote", "citation", "marginal_ref", etc.
    element_id: str            # Original ID from ground truth
    page: int                  # 0-indexed PDF page
    bbox: tuple[float, float, float, float] | None  # Normalized [x0, y0, x1, y1]
    text: str                  # Expected text content
    char_offset: int | None    # Position in page text
    char_length: int | None    # Length in characters
    attributes: dict           # Type-specific attributes
    tags: list[str]            # Tags for filtering

def load_ground_truth_elements(yaml_path: Path) -> list[GroundTruthElement]:
    """Load and normalize ground truth for comparison."""
    gt = yaml.safe_load(yaml_path.read_text())
    elements = []

    # Footnotes
    for fn in gt.get('elements', {}).get('footnotes', []):
        elements.append(GroundTruthElement(
            element_type='footnote',
            element_id=fn['id'],
            page=fn['marker']['page'],
            bbox=None,  # Get from region if needed
            text=fn['content'][0]['text'],
            char_offset=fn['marker']['char_offset'],
            char_length=None,
            attributes={
                'marker_text': fn['marker']['text'],
                'note_type': fn.get('note_type', 'author'),
                'is_multi_page': len(fn.get('pages', [])) > 1,
            },
            tags=fn.get('tags', [])
        ))

    # Citations
    for cite in gt.get('elements', {}).get('citations', []):
        elements.append(GroundTruthElement(
            element_type='citation',
            element_id=cite['id'],
            page=cite['page'],
            bbox=None,
            text=cite['raw'],
            char_offset=cite['char_offset'],
            char_length=len(cite['raw']),
            attributes={
                'style': cite['parsed']['style'],
                'parsed': cite['parsed'],
            },
            tags=cite.get('tags', [])
        ))

    # ... similar for other element types

    return elements
```

### 2. ScholarDocument → Normalized Format

Convert extracted ScholarDocument to same normalized format:

```python
def scholar_doc_to_elements(doc: ScholarDocument) -> list[GroundTruthElement]:
    """Convert ScholarDocument to normalized elements for comparison."""
    elements = []

    # Footnotes (from footnote_refs + notes)
    for fn_ref in doc.footnote_refs:
        note = next((n for n in doc.notes if n.label == fn_ref.label), None)
        elements.append(GroundTruthElement(
            element_type='footnote',
            element_id=f"fn_{fn_ref.label}",
            page=doc.page_for_position(fn_ref.position),
            bbox=None,
            text=note.content if note else "",
            char_offset=fn_ref.position,
            char_length=len(fn_ref.label),
            attributes={
                'marker_text': fn_ref.label,
                'note_type': note.note_type.value if note else 'author',
            },
            tags=[]
        ))

    # Citations
    for cite in doc.citation_refs:
        elements.append(GroundTruthElement(
            element_type='citation',
            element_id=f"cite_{cite.position}",
            page=doc.page_for_position(cite.position),
            bbox=None,
            text=cite.raw,
            char_offset=cite.position,
            char_length=len(cite.raw),
            attributes={
                'style': cite.parsed.style if cite.parsed else 'unknown',
                'parsed': cite.parsed.__dict__ if cite.parsed else {},
            },
            tags=[]
        ))

    return elements
```

### 3. Element Matching

Match predicted elements to ground truth:

```python
@dataclass
class ElementMatch:
    """A matched pair of ground truth and predicted elements."""
    ground_truth: GroundTruthElement | None
    predicted: GroundTruthElement | None
    match_type: Literal['exact', 'partial', 'missed', 'spurious']
    similarity_score: float  # 0.0 - 1.0
    error_details: dict | None

def match_elements(
    ground_truth: list[GroundTruthElement],
    predicted: list[GroundTruthElement],
    element_type: str,
    match_config: MatchConfig
) -> list[ElementMatch]:
    """Match predicted elements to ground truth."""

    gt_elements = [e for e in ground_truth if e.element_type == element_type]
    pred_elements = [e for e in predicted if e.element_type == element_type]

    matches = []
    matched_pred_ids = set()

    for gt in gt_elements:
        best_match = None
        best_score = 0.0

        for pred in pred_elements:
            if pred.element_id in matched_pred_ids:
                continue

            score = compute_similarity(gt, pred, match_config)
            if score > best_score and score >= match_config.threshold:
                best_score = score
                best_match = pred

        if best_match:
            matched_pred_ids.add(best_match.element_id)
            matches.append(ElementMatch(
                ground_truth=gt,
                predicted=best_match,
                match_type='exact' if best_score >= 0.95 else 'partial',
                similarity_score=best_score,
                error_details=compute_errors(gt, best_match) if best_score < 0.95 else None
            ))
        else:
            matches.append(ElementMatch(
                ground_truth=gt,
                predicted=None,
                match_type='missed',
                similarity_score=0.0,
                error_details={'reason': 'not_found'}
            ))

    # Spurious detections
    for pred in pred_elements:
        if pred.element_id not in matched_pred_ids:
            matches.append(ElementMatch(
                ground_truth=None,
                predicted=pred,
                match_type='spurious',
                similarity_score=0.0,
                error_details={'reason': 'false_positive'}
            ))

    return matches
```

### 4. Similarity Computation

```python
@dataclass
class MatchConfig:
    """Configuration for element matching."""
    threshold: float = 0.5          # Minimum score to consider a match
    position_weight: float = 0.3    # Weight for position matching
    text_weight: float = 0.5        # Weight for text similarity
    attributes_weight: float = 0.2  # Weight for attribute matching
    position_tolerance: int = 50    # Character position tolerance

def compute_similarity(
    gt: GroundTruthElement,
    pred: GroundTruthElement,
    config: MatchConfig
) -> float:
    """Compute similarity between ground truth and predicted element."""

    # Must be same page
    if gt.page != pred.page:
        return 0.0

    # Position similarity (if available)
    position_sim = 0.0
    if gt.char_offset is not None and pred.char_offset is not None:
        offset_diff = abs(gt.char_offset - pred.char_offset)
        position_sim = max(0, 1 - offset_diff / config.position_tolerance)
    else:
        position_sim = 0.5  # Neutral if no position info

    # Text similarity (Levenshtein or token-based)
    text_sim = compute_text_similarity(gt.text, pred.text)

    # Attribute similarity (type-specific)
    attr_sim = compute_attribute_similarity(gt.attributes, pred.attributes)

    return (
        config.position_weight * position_sim +
        config.text_weight * text_sim +
        config.attributes_weight * attr_sim
    )

def compute_text_similarity(text1: str, text2: str) -> float:
    """Compute text similarity using multiple methods."""
    # Normalize whitespace
    t1 = ' '.join(text1.split())
    t2 = ' '.join(text2.split())

    if t1 == t2:
        return 1.0

    # Levenshtein ratio
    from difflib import SequenceMatcher
    return SequenceMatcher(None, t1, t2).ratio()
```

## Integration Points

### 1. Evaluation Script

```python
# ground_truth/scripts/evaluate.py

def evaluate_extraction(
    pdf_path: Path,
    ground_truth_path: Path,
    extraction_config: dict | None = None
) -> EvaluationReport:
    """Run extraction and compare to ground truth."""

    # Load ground truth
    gt_elements = load_ground_truth_elements(ground_truth_path)

    # Run extraction
    doc = extract_scholar_document(pdf_path, config=extraction_config)
    pred_elements = scholar_doc_to_elements(doc)

    # Match and compute metrics
    results = {}
    for element_type in ['footnote', 'citation', 'marginal_ref', 'page_number']:
        matches = match_elements(gt_elements, pred_elements, element_type, MatchConfig())
        results[element_type] = compute_metrics(matches)

    return EvaluationReport(
        pdf_path=pdf_path,
        ground_truth_path=ground_truth_path,
        results=results,
        timestamp=datetime.now()
    )
```

### 2. Batch Evaluation

```python
def evaluate_batch(
    ground_truth_dir: Path,
    output_path: Path,
    extraction_config: dict | None = None
) -> BatchReport:
    """Evaluate all ground truth documents."""

    reports = []
    for yaml_path in ground_truth_dir.glob("documents/*.yaml"):
        gt = yaml.safe_load(yaml_path.read_text())
        pdf_path = Path("spikes/sample_pdfs") / gt['source']['pdf']

        if pdf_path.exists():
            report = evaluate_extraction(pdf_path, yaml_path, extraction_config)
            reports.append(report)

    # Aggregate metrics
    return BatchReport(
        reports=reports,
        aggregate_metrics=aggregate_metrics(reports),
        timestamp=datetime.now()
    )
```

### 3. Regression Testing

```python
# tests/test_ground_truth_regression.py

import pytest
from ground_truth.scripts.evaluate import evaluate_extraction

@pytest.fixture
def ground_truth_docs():
    """Load all verified ground truth documents."""
    gt_dir = Path("ground_truth/documents")
    return [
        yaml.safe_load(p.read_text())
        for p in gt_dir.glob("*.yaml")
        if yaml.safe_load(p.read_text())['annotation_status'].get('footnotes', {}).get('state') == 'verified'
    ]

@pytest.mark.parametrize("gt_doc", ground_truth_docs())
def test_footnote_extraction_regression(gt_doc):
    """Ensure footnote extraction meets baseline metrics."""
    pdf_path = Path("spikes/sample_pdfs") / gt_doc['source']['pdf']
    yaml_path = Path("ground_truth/documents") / f"{gt_doc['source']['pdf'].stem}.yaml"

    report = evaluate_extraction(pdf_path, yaml_path)

    assert report.results['footnote']['recall'] >= 0.85, "Footnote recall below baseline"
    assert report.results['footnote']['precision'] >= 0.80, "Footnote precision below baseline"
```

## CLI Interface

```bash
# Evaluate single document
uv run python -m ground_truth.scripts.evaluate \
    --pdf spikes/sample_pdfs/heidegger_bt.pdf \
    --ground-truth ground_truth/documents/heidegger_bt.yaml \
    --output results/heidegger_bt_eval.json

# Batch evaluation
uv run python -m ground_truth.scripts.evaluate \
    --batch ground_truth/documents/ \
    --output results/batch_eval.json \
    --config extraction_config.yaml

# Compare two extraction configs
uv run python -m ground_truth.scripts.compare \
    --baseline results/baseline.json \
    --candidate results/candidate.json \
    --output results/comparison.html
```

## File Structure

```
ground_truth/
├── scripts/
│   ├── evaluate.py          # NEW - Run evaluation
│   ├── compare.py           # NEW - Compare results
│   ├── generate_draft.py    # Existing
│   ├── visualize.py         # Existing
│   └── validate.py          # Existing
├── lib/
│   ├── __init__.py
│   ├── normalize.py         # NEW - Normalize GT/predicted
│   ├── matching.py          # NEW - Element matching
│   ├── metrics.py           # NEW - Metric computation
│   └── reports.py           # NEW - Report generation
```

## Dependencies

```toml
# Additional dependencies for evaluation
rapidfuzz = "^3.0"        # Fast string matching
pandas = "^2.0"           # Report generation
tabulate = "^0.9"         # CLI table output
```

## Open Questions

1. **BBox matching**: Use IoU or position-based matching?
   - Recommendation: Position-based (char_offset) for text elements, IoU for regions

2. **Multi-page element handling**: How to match continuations?
   - Recommendation: Match by marker, then verify content spans pages

3. **Partial credit scoring**: How to weight partial matches?
   - Recommendation: Tiered scoring - exact=1.0, partial=0.5, missed=0.0

## Next Steps

1. [ ] Implement `normalize.py` - GT/predicted normalization
2. [ ] Implement `matching.py` - Element matching algorithm
3. [ ] Implement `metrics.py` - Precision/recall/F1 computation
4. [ ] Implement `evaluate.py` - Main evaluation script
5. [ ] Add regression tests to pytest suite
6. [ ] Document baseline metrics for each element type
