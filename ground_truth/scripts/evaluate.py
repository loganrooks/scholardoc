#!/usr/bin/env python3
"""
Evaluate ScholarDoc Extraction Against Ground Truth

Compares extraction results to ground truth annotations and computes
precision, recall, and F1 metrics per element type.

Usage:
    # Evaluate single document
    uv run python -m ground_truth.scripts.evaluate \\
        --pdf spikes/sample_pdfs/test.pdf \\
        --ground-truth ground_truth/documents/test.yaml

    # Compare to baseline
    uv run python -m ground_truth.scripts.evaluate \\
        --pdf spikes/sample_pdfs/test.pdf \\
        --ground-truth ground_truth/documents/test.yaml \\
        --baseline ground_truth/baselines/current.json

    # Output to JSON
    uv run python -m ground_truth.scripts.evaluate \\
        --pdf spikes/sample_pdfs/test.pdf \\
        --ground-truth ground_truth/documents/test.yaml \\
        --output results.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ground_truth.lib.matching import MatchConfig, match_elements  # noqa: E402
from ground_truth.lib.metrics import (  # noqa: E402
    AggregateMetrics,
    aggregate_metrics,
    compute_metrics,
)
from ground_truth.lib.normalize import (  # noqa: E402
    load_ground_truth_elements,
    scholar_doc_to_elements,
)
from ground_truth.lib.reports import (  # noqa: E402
    generate_cli_report,
    generate_html_report,
    save_json_report,
)

# Element types to evaluate
ELEMENT_TYPES = ["footnote", "citation", "marginal_ref", "page_number", "sous_rature"]


def evaluate_extraction(
    pdf_path: Path,
    ground_truth_path: Path,
    match_config: MatchConfig | None = None,
) -> AggregateMetrics:
    """Run extraction and compare to ground truth.

    Args:
        pdf_path: Path to source PDF
        ground_truth_path: Path to ground truth YAML
        match_config: Optional matching configuration

    Returns:
        AggregateMetrics with per-type and overall metrics
    """
    if match_config is None:
        match_config = MatchConfig()

    # Load ground truth
    gt_elements = load_ground_truth_elements(ground_truth_path)

    # Run extraction
    try:
        from scholardoc.convert import convert_pdf

        doc = convert_pdf(pdf_path)
        pred_elements = scholar_doc_to_elements(doc)
    except ImportError:
        print("Warning: scholardoc.convert not available, using empty predictions")
        pred_elements = []
    except Exception as e:
        print(f"Warning: Extraction failed: {e}, using empty predictions")
        pred_elements = []

    # Match and compute metrics per element type
    by_type = {}
    for element_type in ELEMENT_TYPES:
        matches = match_elements(gt_elements, pred_elements, element_type, match_config)
        metrics = compute_metrics(matches)

        # Only include types that have ground truth elements
        if metrics.support > 0 or metrics.false_positives > 0:
            by_type[element_type] = metrics

    return aggregate_metrics(by_type)


def load_baseline(baseline_path: Path) -> AggregateMetrics | None:
    """Load baseline metrics from JSON file.

    Args:
        baseline_path: Path to baseline JSON

    Returns:
        AggregateMetrics or None if file doesn't exist
    """
    if not baseline_path.exists():
        return None

    with open(baseline_path) as f:
        data = json.load(f)

    # Reconstruct AggregateMetrics from JSON
    from ground_truth.lib.metrics import ElementMetrics

    by_type = {}
    for element_type, type_data in data.get("aggregate_metrics", {}).get("by_type", {}).items():
        by_type[element_type] = ElementMetrics(
            true_positives=type_data.get("true_positives", 0),
            false_positives=type_data.get("false_positives", 0),
            false_negatives=type_data.get("false_negatives", 0),
        )

    return aggregate_metrics(by_type)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate extraction against ground truth",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        help="Path to source PDF",
    )
    parser.add_argument(
        "--ground-truth",
        type=Path,
        required=True,
        help="Path to ground truth YAML file",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        help="Path to baseline JSON for comparison",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output path (.json or .html)",
    )
    parser.add_argument(
        "--format",
        choices=["cli", "json", "html"],
        default="cli",
        help="Output format (default: cli)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Match threshold (default: 0.5)",
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with error if metrics regress from baseline",
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.ground_truth.exists():
        print(f"Error: Ground truth file not found: {args.ground_truth}")
        sys.exit(1)

    # Determine PDF path from ground truth if not provided
    pdf_path = args.pdf
    if pdf_path is None:
        import yaml

        with open(args.ground_truth) as f:
            gt = yaml.safe_load(f)
        pdf_name = gt.get("source", {}).get("pdf")
        if pdf_name:
            pdf_path = Path("spikes/sample_pdfs") / pdf_name
            if not pdf_path.exists():
                print(f"Warning: PDF not found at {pdf_path}")
                pdf_path = None

    # Run evaluation
    match_config = MatchConfig(threshold=args.threshold)

    if pdf_path and pdf_path.exists():
        metrics = evaluate_extraction(pdf_path, args.ground_truth, match_config)
    else:
        # Evaluate ground truth only (no predictions)
        gt_elements = load_ground_truth_elements(args.ground_truth)
        by_type = {}
        for element_type in ELEMENT_TYPES:
            matches = match_elements(gt_elements, [], element_type, match_config)
            m = compute_metrics(matches)
            if m.support > 0:
                by_type[element_type] = m
        metrics = aggregate_metrics(by_type)

    # Load baseline if provided
    baseline = None
    if args.baseline:
        baseline = load_baseline(args.baseline)

    # Generate output
    if args.format == "json" or (args.output and args.output.suffix == ".json"):
        output_path = args.output or Path("evaluation_results.json")
        save_json_report(
            metrics,
            output_path,
            pdf_path=str(pdf_path) if pdf_path else None,
            ground_truth_path=str(args.ground_truth),
        )
        print(f"Results saved to: {output_path}")

    elif args.format == "html" or (args.output and args.output.suffix == ".html"):
        output_path = args.output or Path("evaluation_results.html")
        generate_html_report(
            metrics,
            output_path,
            pdf_path=str(pdf_path) if pdf_path else None,
            ground_truth_path=str(args.ground_truth),
        )
        print(f"Report saved to: {output_path}")

    else:
        # CLI output
        report = generate_cli_report(metrics, baseline=baseline)
        print(report)

    # Check for regression
    if args.fail_on_regression and baseline:
        if metrics.micro_f1 < baseline.micro_f1 - 0.01:  # 1% tolerance
            print(
                f"\nREGRESSION DETECTED: F1 dropped from "
                f"{baseline.micro_f1:.4f} to {metrics.micro_f1:.4f}"
            )
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
