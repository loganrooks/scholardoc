# Testing Methodology

**Version**: 1.0.0
**Created**: 2026-01-07
**Status**: Planning

## Overview

This document defines the testing methodology for evaluating ScholarDoc's extraction pipeline against ground truth annotations. It covers metrics, baseline establishment, comparison workflows, and continuous improvement.

## Evaluation Levels

### Level 1: Element Detection (Did we find it?)

Binary detection - was the element detected at all?

| Element Type | Detection Criteria |
|--------------|-------------------|
| Footnote | Marker found within 50 chars of ground truth position |
| Citation | Citation text found with ≥80% text match |
| Marginal Ref | Marker found on correct page |
| Page Number | Number detected on correct page |
| Section | Heading detected with ≥70% title match |

### Level 2: Localization (Where is it?)

Position accuracy for detected elements:

| Metric | Definition |
|--------|------------|
| Position Error | \|predicted_offset - ground_truth_offset\| |
| Position Accuracy | 1 - (error / tolerance), clamped to [0, 1] |
| BBox IoU | Intersection over Union for region boxes |

### Level 3: Content Accuracy (What does it say?)

Text and attribute accuracy for detected elements:

| Metric | Definition |
|--------|------------|
| Text Similarity | Levenshtein ratio of normalized text |
| Attribute Match | % of attributes correctly extracted |
| Parse Accuracy | For citations: authors, year, pages correct |

## Metrics Definition

### Primary Metrics

```python
@dataclass
class ElementMetrics:
    """Metrics for a single element type."""

    # Detection metrics (Level 1)
    true_positives: int       # Correctly detected
    false_positives: int      # Spurious detections
    false_negatives: int      # Missed elements

    # Derived detection metrics
    @property
    def precision(self) -> float:
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)

    @property
    def recall(self) -> float:
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)

    @property
    def f1(self) -> float:
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)

    # Localization metrics (Level 2)
    mean_position_error: float    # Average char offset error
    position_accuracy: float      # % within tolerance
    mean_bbox_iou: float | None   # For region-based elements

    # Content metrics (Level 3)
    mean_text_similarity: float   # Average text match score
    attribute_accuracy: float     # % of attributes correct
```

### Aggregate Metrics

```python
@dataclass
class AggregateMetrics:
    """Aggregate metrics across all element types."""

    # Per-type metrics
    by_type: dict[str, ElementMetrics]

    # Weighted averages (by ground truth count)
    @property
    def macro_precision(self) -> float:
        """Unweighted average precision across types."""
        return sum(m.precision for m in self.by_type.values()) / len(self.by_type)

    @property
    def macro_recall(self) -> float:
        """Unweighted average recall across types."""
        return sum(m.recall for m in self.by_type.values()) / len(self.by_type)

    @property
    def micro_f1(self) -> float:
        """F1 computed from total TP/FP/FN across all types."""
        total_tp = sum(m.true_positives for m in self.by_type.values())
        total_fp = sum(m.false_positives for m in self.by_type.values())
        total_fn = sum(m.false_negatives for m in self.by_type.values())

        precision = total_tp / (total_tp + total_fp) if total_tp + total_fp > 0 else 0
        recall = total_tp / (total_tp + total_fn) if total_tp + total_fn > 0 else 0

        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
```

## Baseline Establishment

### Process

1. **Initial Extraction**: Run current pipeline on all ground truth documents
2. **Manual Review**: Sample 10% of results for quality check
3. **Metric Computation**: Calculate all metrics
4. **Baseline Recording**: Store as `baseline_results.json`
5. **Threshold Setting**: Set minimum acceptable thresholds

### Baseline Format

```json
{
  "version": "1.0.0",
  "timestamp": "2026-01-07T12:00:00Z",
  "extraction_config": {
    "extractor": "cascading",
    "ocr_enabled": true,
    "dpi": 150
  },
  "ground_truth_version": "1.1.0",
  "documents_evaluated": 6,
  "pages_evaluated": 42,

  "aggregate_metrics": {
    "micro_f1": 0.82,
    "macro_precision": 0.85,
    "macro_recall": 0.79
  },

  "by_element_type": {
    "footnote": {
      "true_positives": 45,
      "false_positives": 8,
      "false_negatives": 12,
      "precision": 0.849,
      "recall": 0.789,
      "f1": 0.818,
      "mean_text_similarity": 0.92,
      "mean_position_error": 12.5
    },
    "citation": {
      "true_positives": 23,
      "false_positives": 5,
      "false_negatives": 7,
      "precision": 0.821,
      "recall": 0.767,
      "f1": 0.793,
      "mean_text_similarity": 0.88,
      "attribute_accuracy": 0.72
    }
  },

  "by_difficulty": {
    "easy": { "f1": 0.91 },
    "medium": { "f1": 0.82 },
    "hard": { "f1": 0.68 }
  },

  "thresholds": {
    "footnote_recall_min": 0.75,
    "citation_recall_min": 0.70,
    "overall_f1_min": 0.75
  }
}
```

### Threshold Guidelines

| Element Type | Precision Min | Recall Min | F1 Min |
|--------------|---------------|------------|--------|
| Footnotes | 0.80 | 0.75 | 0.77 |
| Citations | 0.75 | 0.70 | 0.72 |
| Marginal Refs | 0.80 | 0.80 | 0.80 |
| Page Numbers | 0.95 | 0.95 | 0.95 |
| Sections | 0.85 | 0.80 | 0.82 |

## Comparison Workflows

### 1. Regression Testing (CI/CD)

Run on every PR that touches extraction code:

```yaml
# .github/workflows/ground_truth_regression.yml
name: Ground Truth Regression

on:
  pull_request:
    paths:
      - 'scholardoc/extractors/**'
      - 'scholardoc/readers/**'
      - 'scholardoc/ocr/**'

jobs:
  regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Run ground truth evaluation
        run: |
          uv run python -m ground_truth.scripts.evaluate \
            --batch ground_truth/documents/ \
            --output results/pr_eval.json

      - name: Compare to baseline
        run: |
          uv run python -m ground_truth.scripts.compare \
            --baseline ground_truth/baseline_results.json \
            --candidate results/pr_eval.json \
            --fail-on-regression
```

### 2. A/B Comparison

Compare two extraction configurations:

```python
def compare_configs(
    config_a: dict,
    config_b: dict,
    ground_truth_dir: Path
) -> ComparisonReport:
    """Compare two extraction configurations."""

    results_a = evaluate_batch(ground_truth_dir, config_a)
    results_b = evaluate_batch(ground_truth_dir, config_b)

    comparison = {
        'config_a': config_a,
        'config_b': config_b,
        'metrics_a': results_a.aggregate_metrics,
        'metrics_b': results_b.aggregate_metrics,
        'deltas': compute_deltas(results_a, results_b),
        'significant_changes': find_significant_changes(results_a, results_b),
        'recommendation': 'a' if results_a.micro_f1 > results_b.micro_f1 else 'b'
    }

    return ComparisonReport(**comparison)
```

### 3. Error Analysis

Deep dive into failures:

```python
@dataclass
class ErrorAnalysis:
    """Detailed analysis of extraction errors."""

    # Categorized errors
    missed_by_reason: dict[str, list[ElementMatch]]  # Why missed?
    spurious_by_reason: dict[str, list[ElementMatch]]  # Why false positive?
    partial_by_issue: dict[str, list[ElementMatch]]  # What's wrong?

    # Common patterns
    most_common_miss_reasons: list[tuple[str, int]]
    most_common_spurious_reasons: list[tuple[str, int]]

    # Recommendations
    recommendations: list[str]

def analyze_errors(matches: list[ElementMatch]) -> ErrorAnalysis:
    """Analyze error patterns in element matches."""

    missed = [m for m in matches if m.match_type == 'missed']
    spurious = [m for m in matches if m.match_type == 'spurious']
    partial = [m for m in matches if m.match_type == 'partial']

    # Categorize missed elements
    missed_by_reason = defaultdict(list)
    for m in missed:
        reason = classify_miss_reason(m)
        missed_by_reason[reason].append(m)

    # Categorize spurious detections
    spurious_by_reason = defaultdict(list)
    for m in spurious:
        reason = classify_spurious_reason(m)
        spurious_by_reason[reason].append(m)

    # Categorize partial matches
    partial_by_issue = defaultdict(list)
    for m in partial:
        issue = classify_partial_issue(m)
        partial_by_issue[issue].append(m)

    return ErrorAnalysis(
        missed_by_reason=dict(missed_by_reason),
        spurious_by_reason=dict(spurious_by_reason),
        partial_by_issue=dict(partial_by_issue),
        most_common_miss_reasons=Counter(m for m in missed_by_reason).most_common(5),
        most_common_spurious_reasons=Counter(m for m in spurious_by_reason).most_common(5),
        recommendations=generate_recommendations(missed_by_reason, spurious_by_reason)
    )

def classify_miss_reason(match: ElementMatch) -> str:
    """Classify why an element was missed."""
    gt = match.ground_truth

    # Check common reasons
    if 'multi_page' in gt.tags:
        return 'multi_page_element'
    if any(lang in gt.tags for lang in ['el', 'de', 'la', 'fr']):
        return 'foreign_language'
    if gt.attributes.get('note_type') == 'translator':
        return 'translator_note'
    if gt.char_length and gt.char_length > 500:
        return 'long_element'

    return 'unknown'
```

## Test Stratification

### By Difficulty

Ground truth pages have a `difficulty` field:

```yaml
quality:
  scan_quality: high
  difficulty: medium  # easy | medium | hard
```

**Difficulty Criteria:**

| Difficulty | Criteria |
|------------|----------|
| Easy | Clean scan, simple layout, common fonts, no special chars |
| Medium | Good scan, moderate layout, some footnotes, occasional foreign text |
| Hard | Complex layout, multi-page elements, dense annotations, OCR challenges |

### By Element Type

Report metrics separately for each element type to identify weak areas.

### By Document Type

```yaml
source:
  document_type: translation  # monograph | edited_volume | translation | anthology
```

Different document types have different extraction challenges.

## Continuous Improvement Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                    Improvement Cycle                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────┐ │
│  │ Baseline │────▶│ Evaluate │────▶│ Analyze  │────▶│ Fix    │ │
│  │ (v1.0)   │     │ Current  │     │ Errors   │     │ Issues │ │
│  └──────────┘     └──────────┘     └──────────┘     └────┬───┘ │
│       ▲                                                   │     │
│       │                                                   ▼     │
│  ┌────┴─────┐     ┌──────────┐     ┌──────────┐     ┌────────┐ │
│  │ New      │◀────│ Pass     │◀────│ Re-eval  │◀────│ PR     │ │
│  │ Baseline │     │ Thresh?  │     │ Changes  │     │ Ready  │ │
│  └──────────┘     └──────────┘     └──────────┘     └────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Improvement Process

1. **Identify Weak Area**: Error analysis shows footnote recall drops on multi-page elements
2. **Create Targeted Tests**: Add more multi-page footnote examples to ground truth
3. **Implement Fix**: Modify extraction to handle continuations
4. **Evaluate**: Run against ground truth, verify improvement
5. **Check Regression**: Ensure no degradation on other element types
6. **Update Baseline**: If all thresholds pass, update baseline

### Baseline Versioning

```
ground_truth/
├── baselines/
│   ├── v1.0.0_2026-01-07.json    # Initial baseline
│   ├── v1.1.0_2026-01-15.json    # After footnote improvements
│   └── current.json              # Symlink to latest
```

## Reporting

### CLI Report

```
$ uv run python -m ground_truth.scripts.evaluate --batch ground_truth/documents/

Ground Truth Evaluation Report
==============================
Documents: 6 | Pages: 42 | Elements: 156

Element Type    Precision  Recall    F1      Δ Baseline
-----------     ---------  ------    --      ----------
Footnotes       0.849      0.789     0.818   +0.02
Citations       0.821      0.767     0.793   -0.01
Marginal Refs   0.900      0.857     0.878   +0.05
Page Numbers    0.976      0.952     0.964   +0.00

Overall Micro-F1: 0.837 (baseline: 0.820, Δ +0.017)

⚠ 3 elements below threshold:
  - footnote recall (0.789) < min (0.80) on hard pages
```

### HTML Report

Generate detailed HTML report with:
- Summary metrics dashboard
- Per-document breakdown
- Error visualization (side-by-side GT vs predicted)
- Trend charts (if historical data available)

### JSON Report

Machine-readable format for CI/CD integration (see Baseline Format above).

## Open Questions

1. **Confidence thresholds**: Should we track pipeline confidence and correlate with accuracy?
   - Recommendation: Yes, useful for calibration and selective human review

2. **Partial match scoring**: How much credit for partial matches?
   - Recommendation: Scale by similarity (0.5 * similarity_score for partials)

3. **Cross-element relationships**: How to evaluate footnote-marker linkage?
   - Recommendation: Separate metric for relationship accuracy

4. **OCR-specific metrics**: Track OCR quality separately?
   - Recommendation: Yes, especially for pages with `scan_quality: low`

## Implementation Priority

1. [ ] **Core metrics module** (`metrics.py`) - precision/recall/F1 computation
2. [ ] **Matching algorithm** (`matching.py`) - element pairing
3. [ ] **Evaluation script** (`evaluate.py`) - CLI interface
4. [ ] **Baseline recording** - Store first baseline
5. [ ] **Comparison script** (`compare.py`) - A/B comparison
6. [ ] **Error analysis** - Pattern identification
7. [ ] **CI integration** - GitHub Actions workflow
8. [ ] **HTML reporting** - Visual reports
