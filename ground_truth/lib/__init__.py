"""Ground Truth Evaluation Library.

This package provides tools for comparing ScholarDoc extraction results
against ground truth annotations.

Modules:
    normalize: Convert ground truth and ScholarDocument to common format
    matching: Match predicted elements to ground truth
    metrics: Compute precision, recall, F1 scores
    reports: Generate evaluation reports (CLI, JSON, HTML)
"""

from ground_truth.lib.matching import (
    ElementMatch,
    MatchConfig,
    match_elements,
)
from ground_truth.lib.metrics import (
    AggregateMetrics,
    ElementMetrics,
    aggregate_metrics,
    compute_metrics,
)
from ground_truth.lib.normalize import (
    NormalizedElement,
    load_ground_truth_elements,
    scholar_doc_to_elements,
)

__all__ = [
    # normalize
    "NormalizedElement",
    "load_ground_truth_elements",
    "scholar_doc_to_elements",
    # matching
    "ElementMatch",
    "MatchConfig",
    "match_elements",
    # metrics
    "ElementMetrics",
    "AggregateMetrics",
    "compute_metrics",
    "aggregate_metrics",
]
