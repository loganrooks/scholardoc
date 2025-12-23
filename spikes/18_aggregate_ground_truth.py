#!/usr/bin/env python3
"""Aggregate all ground truth classifications into unified format."""

import json
from pathlib import Path
from collections import defaultdict

GROUND_TRUTH_DIR = Path(__file__).parent.parent / "ground_truth"
CLASSIFIED_DIR = GROUND_TRUTH_DIR / "ocr_quality" / "classified"
OUTPUT_DIR = GROUND_TRUTH_DIR / "ocr_quality"

# Document configurations: (document_name, file_prefix, num_batches)
DOCUMENT_CONFIGS = [
    ("Heidegger_BeingAndTime", "Heidegger_BeingAndTime", 18),
    ("Heidegger_Pathmarks", "Heidegger_Pathmarks", 9),
    ("Heidegger_DiscourseOnThinking", "Heidegger_DiscourseOnThinking", 1),
    ("Derrida_MarginsOfPhilosophy", "Derrida_MarginsOfPhilosophy", 8),
    ("Derrida_WritingAndDifference", "Derrida_WritingAndDifference", 11),
    ("Derrida_TheTruthInPainting", "Derrida_TheTruthInPainting", 9),
    ("Derrida_TheBeastAndTheSovereignVol1", "Derrida_TheBeastAndTheSovereignVol1", 10),
    ("ComayRebecca_MourningSickness", "ComayRebecca_MourningSickness_HegelAndTheFrenchRevolution", 6),
    ("Lenin_StateAndRevolution", "Lenin_StateAndRevolution", 3),
]


def load_batch_classifications(file_prefix: str, num_batches: int, doc_name: str):
    """Generic loader for batch-based classification files."""
    results = []
    for i in range(1, num_batches + 1):
        path = CLASSIFIED_DIR / f"{file_prefix}_batch_{i:02d}_classified.json"
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                    batch_pages = []
                    if isinstance(data, list):
                        batch_pages = data
                    elif isinstance(data, dict):
                        # Try known keys in order of preference
                        for key in ["pages", "classifications", "classified_pages"]:
                            if key in data and isinstance(data[key], list):
                                batch_pages = data[key]
                                break
                        else:
                            # Fallback: find any list in the dict
                            for key, val in data.items():
                                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                                    batch_pages = val
                                    break

                    # Filter to only include dict items with page_number
                    valid_pages = [p for p in batch_pages if isinstance(p, dict) and "page_number" in p]
                    results.extend(valid_pages)
                    print(f"  Loaded {doc_name} batch {i:02d}: {len(valid_pages)} pages ({len(results)} total)")
            except Exception as e:
                print(f"  Error loading {doc_name} batch {i:02d}: {e}")
        else:
            print(f"  Missing {doc_name} batch {i:02d}")
    return results


def load_kant_classifications():
    """Load Kant aggregated ground truth."""
    path = OUTPUT_DIR / "kant_ground_truth_aggregated.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def summarize_classifications(pages: list, document: str) -> dict:
    """Create summary statistics for a set of classifications."""
    counts = defaultdict(int)
    by_classification = defaultdict(list)

    for page in pages:
        classification = page.get("classification", "UNKNOWN")
        # Normalize classification names
        classification = classification.upper()
        if classification in ["GOOD", "MARGINAL", "BAD"]:
            counts[classification] += 1
            by_classification[classification].append(page.get("page_number"))

    return {
        "document": document,
        "total_pages": len(pages),
        "counts": dict(counts),
        "percentage": {
            k: round(v / len(pages) * 100, 1) if pages else 0
            for k, v in counts.items()
        },
        "pages_by_classification": {
            k: sorted([p for p in v if p is not None])
            for k, v in by_classification.items()
        }
    }


def main():
    print("Aggregating ground truth classifications...\n")

    # Create unified output
    unified = {
        "metadata": {
            "created": "2025-12-21",
            "classification_criteria": {
                "GOOD": "Text correct or minor issues that don't affect semantic embedding",
                "MARGINAL": "Minor OCR errors, 1-2 wrong words, still usable for RAG",
                "BAD": "OCR errors that would damage embeddings - semantic corruption"
            },
            "notes": [
                "Footnote markers (word+superscript merged) are classified as artifacts, not errors",
                "German/Greek/Latin terminology correctly OCR'd is not an error",
                "Error rate alone doesn't determine classification - semantic impact does",
                "Stratified sampling used: buckets by error rate with proportional sampling"
            ]
        },
        "documents": {}
    }

    # Load all batch-based documents
    total_pages = 0
    for doc_name, file_prefix, num_batches in DOCUMENT_CONFIGS:
        print(f"\nLoading {doc_name}...")
        pages = load_batch_classifications(file_prefix, num_batches, doc_name)
        if pages:
            unified["documents"][doc_name] = {
                "summary": summarize_classifications(pages, doc_name),
                "pages": pages
            }
            total_pages += len(pages)
            print(f"  Total {doc_name} pages: {len(pages)}")

    # Load Kant (already aggregated format)
    print("\nLoading Kant Critique of Judgement...")
    kant_data = load_kant_classifications()
    if kant_data:
        unified["documents"]["Kant_CritiqueOfJudgement"] = kant_data
        kant_count = sum(kant_data.get("aggregate_counts", {}).values())
        total_pages += kant_count
        print(f"  Total Kant pages: {kant_count}")

    # Write unified output
    output_path = OUTPUT_DIR / "unified_ground_truth.json"
    with open(output_path, "w") as f:
        json.dump(unified, f, indent=2)
    print(f"\nWritten unified ground truth to: {output_path}")
    print(f"Total pages across all documents: {total_pages}")

    # Print summary
    print("\n" + "="*60)
    print("GROUND TRUTH SUMMARY")
    print("="*60)

    for doc_name, doc_data in unified["documents"].items():
        if "summary" in doc_data:
            summary = doc_data["summary"]
            print(f"\n{doc_name}:")
            print(f"  Total pages: {summary.get('total_pages', 'N/A')}")
            print(f"  Counts: {summary.get('counts', {})}")
            print(f"  Percentages: {summary.get('percentage', {})}")
        elif "aggregate_counts" in doc_data:
            counts = doc_data["aggregate_counts"]
            total = sum(counts.values())
            print(f"\n{doc_name}:")
            print(f"  Total pages: {total}")
            print(f"  Counts: {counts}")
            pcts = {k: round(v/total*100, 1) for k, v in counts.items()}
            print(f"  Percentages: {pcts}")


if __name__ == "__main__":
    main()
