"""
Ground Truth Regression Tests

Ensures extraction quality doesn't regress below baseline thresholds.
These tests require ground truth YAML files with verified annotations.

Skip these tests if:
- No verified ground truth documents exist
- Required PDFs are not available
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# Baseline thresholds (minimum acceptable metrics)
THRESHOLDS = {
    "footnote": {"precision": 0.75, "recall": 0.70, "f1": 0.72},
    "citation": {"precision": 0.70, "recall": 0.65, "f1": 0.67},
    "marginal_ref": {"precision": 0.75, "recall": 0.75, "f1": 0.75},
    "page_number": {"precision": 0.90, "recall": 0.90, "f1": 0.90},
}

# Overall threshold
OVERALL_F1_THRESHOLD = 0.70

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
GROUND_TRUTH_DIR = PROJECT_ROOT / "ground_truth" / "documents"
PDF_DIR = PROJECT_ROOT / "spikes" / "sample_pdfs"


def get_verified_ground_truth_files() -> list[tuple[Path, Path]]:
    """Get list of verified ground truth files with their PDFs.

    Returns:
        List of (yaml_path, pdf_path) tuples for verified documents
    """
    if not GROUND_TRUTH_DIR.exists():
        return []

    verified = []
    for yaml_path in GROUND_TRUTH_DIR.glob("*.yaml"):
        try:
            with open(yaml_path) as f:
                gt = yaml.safe_load(f)

            # Check if any element type is verified
            status = gt.get("annotation_status", {})
            has_verified = any(
                s.get("state") == "verified" for s in status.values() if isinstance(s, dict)
            )

            if has_verified:
                pdf_name = gt.get("source", {}).get("pdf")
                if pdf_name:
                    pdf_path = PDF_DIR / pdf_name
                    if pdf_path.exists():
                        verified.append((yaml_path, pdf_path))
        except Exception:
            continue

    return verified


# Skip if no verified documents
verified_docs = get_verified_ground_truth_files()
skip_no_verified = pytest.mark.skipif(
    len(verified_docs) == 0, reason="No verified ground truth documents with available PDFs"
)


@skip_no_verified
class TestGroundTruthRegression:
    """Regression tests against ground truth documents."""

    @pytest.fixture
    def evaluation_modules(self):
        """Import evaluation modules."""
        from ground_truth.lib.matching import MatchConfig, match_elements
        from ground_truth.lib.metrics import aggregate_metrics, compute_metrics
        from ground_truth.lib.normalize import (
            load_ground_truth_elements,
            scholar_doc_to_elements,
        )

        return {
            "load_ground_truth_elements": load_ground_truth_elements,
            "scholar_doc_to_elements": scholar_doc_to_elements,
            "match_elements": match_elements,
            "compute_metrics": compute_metrics,
            "aggregate_metrics": aggregate_metrics,
            "MatchConfig": MatchConfig,
        }

    @pytest.fixture
    def convert_pdf(self):
        """Import and return convert_pdf function."""
        try:
            from scholardoc.convert import convert_pdf

            return convert_pdf
        except ImportError:
            pytest.skip("scholardoc.convert not available")

    @pytest.mark.parametrize("yaml_path,pdf_path", verified_docs)
    def test_extraction_meets_thresholds(
        self, yaml_path: Path, pdf_path: Path, evaluation_modules, convert_pdf
    ):
        """Test that extraction meets minimum quality thresholds."""
        # Load ground truth
        gt_elements = evaluation_modules["load_ground_truth_elements"](yaml_path)

        # Run extraction
        doc = convert_pdf(pdf_path)
        pred_elements = evaluation_modules["scholar_doc_to_elements"](doc)

        # Compute metrics per element type
        match_config = evaluation_modules["MatchConfig"]()
        by_type = {}
        element_types = ["footnote", "citation", "marginal_ref", "page_number"]

        for element_type in element_types:
            matches = evaluation_modules["match_elements"](
                gt_elements, pred_elements, element_type, match_config
            )
            metrics = evaluation_modules["compute_metrics"](matches)

            # Only test if ground truth has this element type
            if metrics.support > 0:
                by_type[element_type] = metrics

                # Check against thresholds
                threshold = THRESHOLDS.get(element_type, {})

                # Allow some tolerance for small sample sizes
                min_support = 3
                if metrics.support >= min_support:
                    if "precision" in threshold:
                        assert metrics.precision >= threshold["precision"], (
                            f"{element_type} precision {metrics.precision:.3f} "
                            f"< threshold {threshold['precision']}"
                        )
                    if "recall" in threshold:
                        assert metrics.recall >= threshold["recall"], (
                            f"{element_type} recall {metrics.recall:.3f} "
                            f"< threshold {threshold['recall']}"
                        )

        # Check overall F1
        if by_type:
            agg = evaluation_modules["aggregate_metrics"](by_type)
            assert agg.micro_f1 >= OVERALL_F1_THRESHOLD, (
                f"Overall micro-F1 {agg.micro_f1:.3f} < threshold {OVERALL_F1_THRESHOLD}"
            )


class TestGroundTruthConsistency:
    """Tests for ground truth file consistency."""

    def test_all_ground_truth_files_valid(self):
        """Ensure all ground truth YAML files are valid."""
        if not GROUND_TRUTH_DIR.exists():
            pytest.skip("Ground truth directory not found")

        yaml_files = list(GROUND_TRUTH_DIR.glob("*.yaml"))
        if not yaml_files:
            pytest.skip("No ground truth files found")

        for yaml_path in yaml_files:
            with open(yaml_path) as f:
                gt = yaml.safe_load(f)

            # Basic structure checks
            assert "schema_version" in gt, f"{yaml_path.name}: missing schema_version"
            assert "source" in gt, f"{yaml_path.name}: missing source"
            assert "pages" in gt, f"{yaml_path.name}: missing pages"

            # Source must have pdf reference
            assert "pdf" in gt["source"], f"{yaml_path.name}: missing source.pdf"

    def test_ground_truth_elements_have_ids(self):
        """Ensure all elements have unique IDs."""
        if not GROUND_TRUTH_DIR.exists():
            pytest.skip("Ground truth directory not found")

        yaml_files = list(GROUND_TRUTH_DIR.glob("*.yaml"))
        if not yaml_files:
            pytest.skip("No ground truth files found")

        for yaml_path in yaml_files:
            with open(yaml_path) as f:
                gt = yaml.safe_load(f)

            all_ids = set()
            elements = gt.get("elements", {})

            # Check footnotes
            for fn in elements.get("footnotes", []):
                assert "id" in fn, f"{yaml_path.name}: footnote missing id"
                assert fn["id"] not in all_ids, f"{yaml_path.name}: duplicate id {fn['id']}"
                all_ids.add(fn["id"])

            # Check citations
            for cite in elements.get("citations", []):
                assert "id" in cite, f"{yaml_path.name}: citation missing id"
                assert cite["id"] not in all_ids, f"{yaml_path.name}: duplicate id {cite['id']}"
                all_ids.add(cite["id"])

            # Check regions (per page)
            for page in gt.get("pages", []):
                for region in page.get("regions", []):
                    assert "id" in region, f"{yaml_path.name}: region missing id"
