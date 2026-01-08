#!/usr/bin/env python3
"""
Spike 33: Batched Docling Layout Detection

Demonstrates batched layout detection using Docling RT-DETR for
optimal throughput on GPU.

Optimal batch sizes (GTX 1080Ti 11GB):
- Batch 16: 47.6ms/page, 2.2GB VRAM (recommended)
- Batch 32: 48.3ms/page, 4.2GB VRAM
- Batch 8:  51.1ms/page, 1.2GB VRAM (conservative)

Usage:
    uv run python spikes/33_docling_batched.py <pdf_path>
    uv run python spikes/33_docling_batched.py <pdf_path> --batch-size 16
    uv run python spikes/33_docling_batched.py <pdf_path> --pages 0-50
"""

from __future__ import annotations

import argparse
import io
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import fitz
import torch
from PIL import Image
from transformers import RTDetrImageProcessor, RTDetrV2ForObjectDetection


@dataclass
class LayoutBox:
    """A detected layout region."""

    label: str
    confidence: float
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2
    page_num: int


@dataclass
class PageLayout:
    """Layout detection results for a single page."""

    page_num: int
    boxes: list[LayoutBox]
    image_size: tuple[int, int]

    @property
    def footnotes(self) -> list[LayoutBox]:
        return [b for b in self.boxes if b.label == "Footnote"]

    @property
    def text_regions(self) -> list[LayoutBox]:
        return [b for b in self.boxes if b.label == "Text"]

    @property
    def tables(self) -> list[LayoutBox]:
        return [b for b in self.boxes if b.label == "Table"]

    def by_type(self) -> dict[str, list[LayoutBox]]:
        result: dict[str, list[LayoutBox]] = {}
        for box in self.boxes:
            if box.label not in result:
                result[box.label] = []
            result[box.label].append(box)
        return result


class DoclingLayoutDetector:
    """Batched layout detection using Docling RT-DETR."""

    MODEL_ID = "ds4sd/docling-layout-heron"

    # Docling label mapping
    LABELS = {
        0: "Caption",
        1: "Footnote",
        2: "Formula",
        3: "List-item",
        4: "Page-footer",
        5: "Page-header",
        6: "Picture",
        7: "Section-header",
        8: "Table",
        9: "Text",
        10: "Title",
        11: "Document-Index",
        12: "Code",
        13: "Checkbox-Selected",
        14: "Checkbox-Unselected",
        15: "Form",
        16: "Key-Value-Region",
    }

    def __init__(
        self,
        device: str = "cuda",
        batch_size: int = 16,
        confidence_threshold: float = 0.3,
        dpi: int = 150,
    ):
        self.device = device
        self.batch_size = batch_size
        self.confidence_threshold = confidence_threshold
        self.dpi = dpi

        print(f"Loading Docling RT-DETR on {device}...")
        self.processor = RTDetrImageProcessor.from_pretrained(self.MODEL_ID)
        self.model = RTDetrV2ForObjectDetection.from_pretrained(self.MODEL_ID)
        self.model = self.model.to(device)
        self.model.eval()
        print(f"Model loaded. Batch size: {batch_size}")

    def _pdf_to_images(
        self, pdf_path: Path, page_range: tuple[int, int] | None = None
    ) -> Iterator[tuple[int, Image.Image]]:
        """Convert PDF pages to PIL Images."""
        doc = fitz.open(pdf_path)

        if page_range:
            start, end = page_range
            pages = range(start, min(end, len(doc)))
        else:
            pages = range(len(doc))

        mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)

        for i in pages:
            page = doc[i]
            pix = page.get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            yield i, img

        doc.close()

    def _process_batch(
        self,
        images: list[Image.Image],
        page_nums: list[int],
    ) -> list[PageLayout]:
        """Process a batch of images."""
        inputs = self.processor(images=images, return_tensors="pt").to(self.device)

        with torch.inference_mode():
            outputs = self.model(**inputs)

        # Post-process each image
        target_sizes = torch.tensor([img.size[::-1] for img in images]).to(self.device)
        results = self.processor.post_process_object_detection(
            outputs, threshold=self.confidence_threshold, target_sizes=target_sizes
        )

        page_layouts = []
        for page_num, img, detections in zip(page_nums, images, results, strict=True):
            boxes = []
            for score, label, box in zip(
                detections["scores"].cpu(),
                detections["labels"].cpu(),
                detections["boxes"].cpu(),
                strict=True,
            ):
                label_name = self.model.config.id2label.get(label.item(), f"Unknown-{label.item()}")
                boxes.append(
                    LayoutBox(
                        label=label_name,
                        confidence=score.item(),
                        bbox=tuple(box.tolist()),
                        page_num=page_num,
                    )
                )

            page_layouts.append(
                PageLayout(
                    page_num=page_num,
                    boxes=boxes,
                    image_size=img.size,
                )
            )

        return page_layouts

    def detect_pdf(
        self,
        pdf_path: Path | str,
        page_range: tuple[int, int] | None = None,
        progress: bool = True,
    ) -> list[PageLayout]:
        """Detect layout for all pages in a PDF."""
        pdf_path = Path(pdf_path)

        # Collect pages into batches
        all_results: list[PageLayout] = []
        batch_images: list[Image.Image] = []
        batch_page_nums: list[int] = []

        total_pages = 0
        start_time = time.time()

        for page_num, img in self._pdf_to_images(pdf_path, page_range):
            batch_images.append(img)
            batch_page_nums.append(page_num)

            if len(batch_images) >= self.batch_size:
                results = self._process_batch(batch_images, batch_page_nums)
                all_results.extend(results)
                total_pages += len(batch_images)

                if progress:
                    elapsed = time.time() - start_time
                    rate = total_pages / elapsed
                    print(f"  Processed {total_pages} pages ({elapsed:.1f}s, {rate:.1f} pages/s)")

                batch_images = []
                batch_page_nums = []

        # Process remaining pages
        if batch_images:
            results = self._process_batch(batch_images, batch_page_nums)
            all_results.extend(results)
            total_pages += len(batch_images)

        elapsed = time.time() - start_time
        if progress:
            rate = total_pages / elapsed
            print(f"Completed {total_pages} pages in {elapsed:.1f}s ({rate:.1f} pages/s)")

        return all_results

    def detect_images(
        self,
        images: list[Image.Image],
        page_nums: list[int] | None = None,
    ) -> list[PageLayout]:
        """Detect layout for a list of images."""
        if page_nums is None:
            page_nums = list(range(len(images)))

        all_results: list[PageLayout] = []

        for i in range(0, len(images), self.batch_size):
            batch_images = images[i : i + self.batch_size]
            batch_page_nums = page_nums[i : i + self.batch_size]
            results = self._process_batch(batch_images, batch_page_nums)
            all_results.extend(results)

        return all_results


def main():
    parser = argparse.ArgumentParser(description="Batched Docling layout detection")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size (default: 16)")
    parser.add_argument("--pages", help="Page range (e.g., '0-50', '10-20')")
    parser.add_argument("--dpi", type=int, default=150, help="Render DPI (default: 150)")
    parser.add_argument(
        "--threshold", type=float, default=0.3, help="Confidence threshold (default: 0.3)"
    )
    parser.add_argument("--show-footnotes", action="store_true", help="Show only footnote regions")

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        return

    # Parse page range
    page_range = None
    if args.pages:
        start, end = args.pages.split("-")
        page_range = (int(start), int(end))

    # Create detector
    detector = DoclingLayoutDetector(
        batch_size=args.batch_size,
        confidence_threshold=args.threshold,
        dpi=args.dpi,
    )

    # Run detection
    print(f"\nProcessing: {pdf_path}")
    results = detector.detect_pdf(pdf_path, page_range=page_range)

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")

    total_by_type: dict[str, int] = {}
    for page in results:
        for label, boxes in page.by_type().items():
            if label not in total_by_type:
                total_by_type[label] = 0
            total_by_type[label] += len(boxes)

    print("\nTotal regions by type:")
    for label, count in sorted(total_by_type.items(), key=lambda x: -x[1]):
        print(f"  {label}: {count}")

    # Show footnotes if requested
    if args.show_footnotes:
        print(f"\n{'=' * 60}")
        print("FOOTNOTES")
        print(f"{'=' * 60}")

        for page in results:
            if page.footnotes:
                print(f"\nPage {page.page_num}:")
                for fn in page.footnotes:
                    print(f"  Footnote (conf={fn.confidence:.2f}): bbox={fn.bbox}")


if __name__ == "__main__":
    main()
