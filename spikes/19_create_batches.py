#!/usr/bin/env python3
"""Create review batches from stratified sample files."""

import json
import sys
from pathlib import Path

GROUND_TRUTH_DIR = Path(__file__).parent.parent / "ground_truth"
BATCH_SIZE = 25


def create_batches(sample_file: Path):
    """Create batches from a sample file."""
    with open(sample_file) as f:
        data = json.load(f)

    doc_name = data["document"]
    pages = data["pages"]

    # Split into batches
    batches = []
    for i in range(0, len(pages), BATCH_SIZE):
        batch_pages = pages[i:i + BATCH_SIZE]
        batches.append(batch_pages)

    # Write each batch
    for idx, batch_pages in enumerate(batches, 1):
        batch_file = GROUND_TRUTH_DIR / f"{doc_name}_batch_{idx:02d}.json"
        with open(batch_file, "w") as f:
            json.dump({
                "document": doc_name,
                "batch_number": idx,
                "total_batches": len(batches),
                "pages": batch_pages
            }, f, indent=2)
        print(f"  Created: {batch_file.name} ({len(batch_pages)} pages)")

    return len(batches)


def main():
    sample_files = [
        "Heidegger_Pathmarks_sample_for_review.json",
        "Heidegger_DiscourseOnThinking_sample_for_review.json",
        "Derrida_WritingAndDifference_sample_for_review.json",
        "Derrida_TheTruthInPainting_sample_for_review.json",
        "Derrida_TheBeastAndTheSovereignVol1_sample_for_review.json",
        "ComayRebecca_MourningSickness_HegelAndTheFrenchRevolution_sample_for_review.json",
    ]

    total_batches = 0
    for filename in sample_files:
        path = GROUND_TRUTH_DIR / filename
        if path.exists():
            print(f"\n{filename}:")
            num = create_batches(path)
            total_batches += num
        else:
            print(f"Missing: {filename}")

    print(f"\n{'='*60}")
    print(f"Total batches created: {total_batches}")


if __name__ == "__main__":
    main()
