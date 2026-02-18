#!/usr/bin/env python3
"""
Compare Two Evaluation Results

Compare metrics between two evaluation runs (e.g., baseline vs candidate).
Useful for A/B testing extraction configurations or detecting regressions.

Usage:
    # Compare two result files
    uv run python -m ground_truth.scripts.compare \\
        --baseline ground_truth/baselines/current.json \\
        --candidate results/new_eval.json

    # Fail if regression detected
    uv run python -m ground_truth.scripts.compare \\
        --baseline ground_truth/baselines/current.json \\
        --candidate results/new_eval.json \\
        --fail-on-regression

    # Output detailed HTML report
    uv run python -m ground_truth.scripts.compare \\
        --baseline ground_truth/baselines/current.json \\
        --candidate results/new_eval.json \\
        --output comparison_report.html
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class MetricDelta:
    """Change in a metric value."""

    metric_name: str
    baseline_value: float
    candidate_value: float

    @property
    def delta(self) -> float:
        return self.candidate_value - self.baseline_value

    @property
    def delta_percent(self) -> float:
        if self.baseline_value == 0:
            return 0.0 if self.candidate_value == 0 else float("inf")
        return (self.delta / self.baseline_value) * 100

    @property
    def is_improvement(self) -> bool:
        return self.delta > 0

    @property
    def is_regression(self) -> bool:
        return self.delta < 0

    def __str__(self) -> str:
        sign = "+" if self.delta >= 0 else ""
        return (
            f"{self.metric_name}: {self.baseline_value:.4f} → {self.candidate_value:.4f} "
            f"({sign}{self.delta:.4f}, {sign}{self.delta_percent:.1f}%)"
        )


@dataclass
class ComparisonResult:
    """Result of comparing two evaluation runs."""

    baseline_path: str
    candidate_path: str
    overall: dict[str, MetricDelta]
    by_type: dict[str, dict[str, MetricDelta]]
    regressions: list[MetricDelta]
    improvements: list[MetricDelta]

    @property
    def has_regressions(self) -> bool:
        return len(self.regressions) > 0


def load_metrics(path: Path) -> dict:
    """Load metrics from JSON file."""
    with open(path) as f:
        data = json.load(f)

    # Handle both direct metrics and nested format
    if "aggregate_metrics" in data:
        return data["aggregate_metrics"]
    return data


def compare_metrics(baseline: dict, candidate: dict) -> ComparisonResult:
    """Compare two sets of metrics."""
    # Compare overall metrics
    overall = {}
    for metric in ["micro_f1", "macro_precision", "macro_recall", "macro_f1"]:
        baseline_val = baseline.get(metric, 0.0)
        candidate_val = candidate.get(metric, 0.0)
        overall[metric] = MetricDelta(metric, baseline_val, candidate_val)

    # Compare per-type metrics
    by_type = {}
    baseline_types = baseline.get("by_type", {})
    candidate_types = candidate.get("by_type", {})

    all_types = set(baseline_types.keys()) | set(candidate_types.keys())
    for element_type in all_types:
        bt = baseline_types.get(element_type, {})
        ct = candidate_types.get(element_type, {})

        type_deltas = {}
        for metric in ["precision", "recall", "f1"]:
            baseline_val = bt.get(metric, 0.0)
            candidate_val = ct.get(metric, 0.0)
            type_deltas[metric] = MetricDelta(
                f"{element_type}.{metric}", baseline_val, candidate_val
            )

        by_type[element_type] = type_deltas

    # Collect regressions and improvements
    regressions = []
    improvements = []

    for delta in overall.values():
        if delta.is_regression:
            regressions.append(delta)
        elif delta.is_improvement:
            improvements.append(delta)

    for type_deltas in by_type.values():
        for delta in type_deltas.values():
            if delta.is_regression:
                regressions.append(delta)
            elif delta.is_improvement:
                improvements.append(delta)

    return ComparisonResult(
        baseline_path="",
        candidate_path="",
        overall=overall,
        by_type=by_type,
        regressions=regressions,
        improvements=improvements,
    )


def generate_cli_comparison(result: ComparisonResult) -> str:
    """Generate CLI comparison report."""
    lines = [
        "=" * 60,
        "Evaluation Comparison Report",
        "=" * 60,
        "",
        "Overall Metrics:",
        "-" * 40,
    ]

    for _metric, delta in result.overall.items():
        status = "✅" if delta.is_improvement else ("❌" if delta.is_regression else "→")
        lines.append(f"  {status} {delta}")

    lines.append("")
    lines.append("Per-Element Type:")
    lines.append("-" * 40)

    for element_type, deltas in result.by_type.items():
        lines.append(f"\n  {element_type}:")
        for metric, delta in deltas.items():
            status = "✅" if delta.is_improvement else ("❌" if delta.is_regression else "→")
            # Show shorter format for per-type
            sign = "+" if delta.delta >= 0 else ""
            lines.append(
                f"    {status} {metric}: {delta.baseline_value:.3f} → "
                f"{delta.candidate_value:.3f} ({sign}{delta.delta:.3f})"
            )

    lines.append("")
    lines.append("-" * 40)

    if result.improvements:
        lines.append(f"✅ {len(result.improvements)} improvements")
    if result.regressions:
        lines.append(f"❌ {len(result.regressions)} regressions")

    if not result.improvements and not result.regressions:
        lines.append("→ No significant changes")

    return "\n".join(lines)


def generate_html_comparison(
    result: ComparisonResult,
    baseline_path: str,
    candidate_path: str,
) -> str:
    """Generate HTML comparison report."""
    rows = []
    for metric, delta in result.overall.items():
        color = (
            "#28a745" if delta.is_improvement else ("#dc3545" if delta.is_regression else "#6c757d")
        )
        sign = "+" if delta.delta >= 0 else ""
        rows.append(
            f"<tr><td><strong>{metric}</strong></td>"
            f"<td>{delta.baseline_value:.4f}</td>"
            f"<td>{delta.candidate_value:.4f}</td>"
            f'<td style="color:{color}">{sign}{delta.delta:.4f}</td></tr>'
        )

    overall_table = "\n".join(rows)

    type_sections = []
    for element_type, deltas in result.by_type.items():
        type_rows = []
        for metric, delta in deltas.items():
            color = (
                "#28a745"
                if delta.is_improvement
                else ("#dc3545" if delta.is_regression else "#6c757d")
            )
            sign = "+" if delta.delta >= 0 else ""
            type_rows.append(
                f"<tr><td>{metric}</td>"
                f"<td>{delta.baseline_value:.3f}</td>"
                f"<td>{delta.candidate_value:.3f}</td>"
                f'<td style="color:{color}">{sign}{delta.delta:.3f}</td></tr>'
            )
        type_sections.append(f"""
        <h3>{element_type}</h3>
        <table class="table">
            <thead><tr><th>Metric</th><th>Baseline</th><th>Candidate</th><th>Delta</th></tr></thead>
            <tbody>{"".join(type_rows)}</tbody>
        </table>
        """)

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Evaluation Comparison Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 40px; }}
        .table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        .table th, .table td {{ border: 1px solid #dee2e6; padding: 8px 12px; text-align: left; }}
        .table th {{ background-color: #f8f9fa; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; margin-top: 20px; }}
        .summary {{ padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .summary.good {{ background-color: #d4edda; border: 1px solid #c3e6cb; }}
        .summary.bad {{ background-color: #f8d7da; border: 1px solid #f5c6cb; }}
        .summary.neutral {{ background-color: #e2e3e5; border: 1px solid #d6d8db; }}
    </style>
</head>
<body>
    <h1>Evaluation Comparison Report</h1>
    <p><strong>Baseline:</strong> {baseline_path}</p>
    <p><strong>Candidate:</strong> {candidate_path}</p>

    <div class="summary {"good" if not result.has_regressions else "bad"}">
        {"✅ " + str(len(result.improvements)) + " improvements" if result.improvements else ""}
        {" | " if result.improvements and result.regressions else ""}
        {"❌ " + str(len(result.regressions)) + " regressions" if result.regressions else ""}
        {"→ No significant changes" if not result.improvements and not result.regressions else ""}
    </div>

    <h2>Overall Metrics</h2>
    <table class="table">
        <thead><tr><th>Metric</th><th>Baseline</th><th>Candidate</th><th>Delta</th></tr></thead>
        <tbody>{overall_table}</tbody>
    </table>

    <h2>Per-Element Type</h2>
    {"".join(type_sections)}
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(
        description="Compare two evaluation results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        required=True,
        help="Path to baseline evaluation JSON",
    )
    parser.add_argument(
        "--candidate",
        type=Path,
        required=True,
        help="Path to candidate evaluation JSON",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output path (.html for HTML report)",
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with error if any regression detected",
    )
    parser.add_argument(
        "--regression-threshold",
        type=float,
        default=0.01,
        help="Minimum delta to consider a regression (default: 0.01)",
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.baseline.exists():
        print(f"Error: Baseline file not found: {args.baseline}")
        sys.exit(1)
    if not args.candidate.exists():
        print(f"Error: Candidate file not found: {args.candidate}")
        sys.exit(1)

    # Load and compare
    baseline = load_metrics(args.baseline)
    candidate = load_metrics(args.candidate)
    result = compare_metrics(baseline, candidate)
    result.baseline_path = str(args.baseline)
    result.candidate_path = str(args.candidate)

    # Generate output
    if args.output and args.output.suffix == ".html":
        html = generate_html_comparison(result, str(args.baseline), str(args.candidate))
        args.output.write_text(html)
        print(f"Report saved to: {args.output}")
    else:
        print(generate_cli_comparison(result))

    # Check for regressions
    if args.fail_on_regression:
        significant_regressions = [
            r for r in result.regressions if abs(r.delta) >= args.regression_threshold
        ]
        if significant_regressions:
            print(f"\n❌ REGRESSION DETECTED: {len(significant_regressions)} metrics regressed")
            for r in significant_regressions:
                print(f"   {r}")
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
