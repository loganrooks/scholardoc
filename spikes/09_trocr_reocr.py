#!/usr/bin/env python3
"""
Spike 09: Re-OCR with TrOCR

PURPOSE: Test whether re-OCR with TrOCR produces better results than existing
         PDF text layers (especially for scanned documents like Kant).

RUN:
  # Basic test on a single page
  CUDA_VISIBLE_DEVICES="" uv run python spikes/09_trocr_reocr.py sample.pdf --page 50

  # Compare multiple pages
  CUDA_VISIBLE_DEVICES="" uv run python spikes/09_trocr_reocr.py sample.pdf --pages 50,100,150

  # Full analysis with quality comparison
  CUDA_VISIBLE_DEVICES="" uv run python spikes/09_trocr_reocr.py sample.pdf --compare

NOTES:
- TrOCR is designed for line-level OCR, not full pages
- We extract text blocks from the page, crop them as images, and OCR each
- This lets us compare TrOCR output vs existing text layer
- Use CUDA_VISIBLE_DEVICES="" to force CPU if GPU issues occur

MODELS:
- microsoft/trocr-base-printed: General printed text (fast, good quality)
- microsoft/trocr-large-printed: Better quality, slower
- microsoft/trocr-base-handwritten: For handwritten text
"""

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF required: uv add pymupdf")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Pillow required: uv add pillow")
    sys.exit(1)

try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    import torch
except ImportError:
    print("Transformers and torch required: uv sync --extra ocr")
    sys.exit(1)


# ============================================================================
# TrOCR Engine
# ============================================================================


class TrOCREngine:
    """TrOCR-based OCR engine for printed text."""

    def __init__(
        self,
        model_name: str = "microsoft/trocr-base-printed",
        device: str | None = None,
    ):
        """
        Initialize TrOCR engine.

        Args:
            model_name: HuggingFace model name
            device: "cuda", "cpu", or None (auto-detect)
        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        print(f"Loading TrOCR model: {model_name}")
        print(f"Device: {self.device}")

        self.processor = TrOCRProcessor.from_pretrained(model_name)
        self.model = VisionEncoderDecoderModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

        print("Model loaded successfully")

    def ocr_image(self, image: Image.Image) -> str:
        """
        Perform OCR on a PIL Image.

        Args:
            image: PIL Image (should be a text line or small region)

        Returns:
            Recognized text
        """
        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Process image
        pixel_values = self.processor(image, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(self.device)

        # Generate text
        with torch.no_grad():
            generated_ids = self.model.generate(pixel_values)

        # Decode
        text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return text.strip()

    def ocr_images_batch(self, images: list[Image.Image], batch_size: int = 8) -> list[str]:
        """
        Perform OCR on multiple images in batches.

        Args:
            images: List of PIL Images
            batch_size: Batch size for processing

        Returns:
            List of recognized texts
        """
        results = []

        for i in range(0, len(images), batch_size):
            batch = images[i : i + batch_size]

            # Convert to RGB
            batch_rgb = [img.convert("RGB") if img.mode != "RGB" else img for img in batch]

            # Process batch
            pixel_values = self.processor(batch_rgb, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)

            # Generate
            with torch.no_grad():
                generated_ids = self.model.generate(pixel_values)

            # Decode
            texts = self.processor.batch_decode(generated_ids, skip_special_tokens=True)
            results.extend([t.strip() for t in texts])

        return results


# ============================================================================
# PDF Processing
# ============================================================================


@dataclass
class TextRegion:
    """A text region from a PDF page."""

    bbox: tuple[float, float, float, float]  # x0, y0, x1, y1
    original_text: str
    trocr_text: str | None = None
    image: Image.Image | None = None


def extract_page_image(doc: fitz.Document, page_num: int, dpi: int = 300) -> Image.Image:
    """Extract a page as a PIL Image."""
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72 is default PDF DPI
    pix = page.get_pixmap(matrix=mat)

    # Convert to PIL Image
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img


def extract_text_regions(
    doc: fitz.Document,
    page_num: int,
    min_height: int = 10,
    min_width: int = 50,
    line_level: bool = False,
) -> list[TextRegion]:
    """
    Extract text regions from a PDF page.

    Args:
        doc: PyMuPDF document
        page_num: Page number (0-indexed)
        min_height: Minimum region height
        min_width: Minimum region width
        line_level: If True, extract individual lines (better for TrOCR)
                   If False, extract whole text blocks

    Returns list of TextRegion with bounding boxes and original text.
    """
    page = doc[page_num]
    blocks = page.get_text("dict")["blocks"]

    regions = []
    for block in blocks:
        if block.get("type") != 0:  # 0 = text block
            continue

        if line_level:
            # Extract each line as a separate region (better for TrOCR)
            for line in block.get("lines", []):
                bbox = line["bbox"]
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]

                if height < min_height or width < min_width:
                    continue

                # Get text from all spans in this line
                text_parts = []
                for span in line.get("spans", []):
                    text_parts.append(span.get("text", ""))

                text = "".join(text_parts).strip()
                if not text:
                    continue

                regions.append(TextRegion(bbox=tuple(bbox), original_text=text))
        else:
            # Extract whole block (original behavior)
            bbox = block["bbox"]
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]

            if height < min_height or width < min_width:
                continue

            text_parts = []
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text_parts.append(span.get("text", ""))

            text = " ".join(text_parts).strip()
            if not text:
                continue

            regions.append(TextRegion(bbox=tuple(bbox), original_text=text))

    return regions


def crop_region(
    page_image: Image.Image,
    bbox: tuple[float, float, float, float],
    page_size: tuple[float, float],
    dpi: int = 300,
    padding: int = 5,
) -> Image.Image:
    """
    Crop a region from the page image.

    Args:
        page_image: Full page PIL Image
        bbox: Region bounding box in PDF coordinates
        page_size: PDF page size (width, height)
        dpi: DPI of the page image
        padding: Extra pixels to add around region
    """
    # Scale factor from PDF points to image pixels
    scale = dpi / 72

    # Convert PDF coordinates to image coordinates
    x0 = int(bbox[0] * scale) - padding
    y0 = int(bbox[1] * scale) - padding
    x1 = int(bbox[2] * scale) + padding
    y1 = int(bbox[3] * scale) + padding

    # Clamp to image bounds
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(page_image.width, x1)
    y1 = min(page_image.height, y1)

    return page_image.crop((x0, y0, x1, y1))


# ============================================================================
# Quality Comparison
# ============================================================================


def word_error_rate(reference: str, hypothesis: str) -> float:
    """
    Calculate Word Error Rate (WER) between reference and hypothesis.

    WER = (S + D + I) / N
    where S=substitutions, D=deletions, I=insertions, N=words in reference
    """
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()

    if not ref_words:
        return 1.0 if hyp_words else 0.0

    # Dynamic programming for edit distance
    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]

    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j

    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min(
                    d[i - 1][j] + 1,  # deletion
                    d[i][j - 1] + 1,  # insertion
                    d[i - 1][j - 1] + 1,  # substitution
                )

    return d[len(ref_words)][len(hyp_words)] / len(ref_words)


def char_error_rate(reference: str, hypothesis: str) -> float:
    """Calculate Character Error Rate (CER)."""
    if not reference:
        return 1.0 if hypothesis else 0.0

    # Simple character-level comparison
    ref = reference.lower()
    hyp = hypothesis.lower()

    # Use same edit distance approach but for characters
    d = [[0] * (len(hyp) + 1) for _ in range(len(ref) + 1)]

    for i in range(len(ref) + 1):
        d[i][0] = i
    for j in range(len(hyp) + 1):
        d[0][j] = j

    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            if ref[i - 1] == hyp[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min(
                    d[i - 1][j] + 1,
                    d[i][j - 1] + 1,
                    d[i - 1][j - 1] + 1,
                )

    return d[len(ref)][len(hyp)] / len(ref)


# ============================================================================
# Main
# ============================================================================


def process_page(
    doc: fitz.Document,
    page_num: int,
    engine: TrOCREngine,
    dpi: int = 300,
    line_level: bool = True,
    verbose: bool = True,
) -> list[TextRegion]:
    """
    Process a single page: extract regions, run TrOCR, compare.
    """
    if verbose:
        print(f"\n--- Page {page_num} ---")

    # Get page image
    page_image = extract_page_image(doc, page_num, dpi=dpi)
    page = doc[page_num]
    page_size = (page.rect.width, page.rect.height)

    if verbose:
        print(f"Page size: {page_size[0]:.0f}x{page_size[1]:.0f} pts")
        print(f"Image size: {page_image.width}x{page_image.height} px")

    # Extract text regions (line-level is better for TrOCR)
    regions = extract_text_regions(doc, page_num, line_level=line_level)
    if verbose:
        mode = "lines" if line_level else "blocks"
        print(f"Text regions ({mode}): {len(regions)}")

    # Process each region with TrOCR
    for i, region in enumerate(regions):
        # Crop region from image
        region.image = crop_region(page_image, region.bbox, page_size, dpi=dpi)

        # Run TrOCR
        try:
            region.trocr_text = engine.ocr_image(region.image)
        except Exception as e:
            if verbose:
                print(f"  Region {i}: TrOCR error - {e}")
            region.trocr_text = ""

    return regions


def main():
    parser = argparse.ArgumentParser(description="Test TrOCR re-OCR on PDF pages")
    parser.add_argument("pdf", help="PDF file to process")
    parser.add_argument("--page", type=int, help="Single page to process (0-indexed)")
    parser.add_argument("--pages", type=str, help="Comma-separated page numbers")
    parser.add_argument("--compare", action="store_true", help="Run quality comparison")
    parser.add_argument("--dpi", type=int, default=300, help="Image DPI (default: 300)")
    parser.add_argument(
        "--model",
        type=str,
        default="microsoft/trocr-base-printed",
        help="TrOCR model name",
    )
    parser.add_argument("--limit", type=int, default=10, help="Max regions per page")
    parser.add_argument(
        "--blocks",
        action="store_true",
        help="Extract text blocks instead of lines (lines are better for TrOCR)",
    )
    args = parser.parse_args()

    # Open PDF
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    doc = fitz.open(pdf_path)
    print(f"Opened: {pdf_path.name}")
    print(f"Pages: {len(doc)}")

    # Determine pages to process
    if args.page is not None:
        pages = [args.page]
    elif args.pages:
        pages = [int(p) for p in args.pages.split(",")]
    else:
        # Default: sample pages from different parts of the document
        total = len(doc)
        pages = [
            min(50, total - 1),
            min(100, total - 1),
            min(150, total - 1),
        ]
        pages = list(set(pages))  # Remove duplicates

    print(f"Processing pages: {pages}")

    # Initialize TrOCR
    print()
    engine = TrOCREngine(model_name=args.model)

    # Process each page
    all_regions = []
    total_time = 0

    for page_num in pages:
        if page_num >= len(doc):
            print(f"Skipping page {page_num} (out of range)")
            continue

        start = time.time()
        regions = process_page(
            doc, page_num, engine, dpi=args.dpi, line_level=not args.blocks
        )
        elapsed = time.time() - start
        total_time += elapsed

        # Limit regions for display
        regions = regions[: args.limit]
        all_regions.extend(regions)

        print(f"\nProcessed {len(regions)} regions in {elapsed:.1f}s")

        # Show sample comparisons
        print("\nSample comparisons:")
        for i, region in enumerate(regions[:5]):
            orig = region.original_text[:60] + "..." if len(region.original_text) > 60 else region.original_text
            trocr = (region.trocr_text or "")[:60]
            if len(region.trocr_text or "") > 60:
                trocr += "..."

            # Calculate similarity
            if region.original_text and region.trocr_text:
                wer = word_error_rate(region.original_text, region.trocr_text)
                cer = char_error_rate(region.original_text, region.trocr_text)
                print(f"\n  [{i}] Original: {orig}")
                print(f"      TrOCR:    {trocr}")
                print(f"      WER: {wer:.1%}, CER: {cer:.1%}")
            else:
                print(f"\n  [{i}] Original: {orig}")
                print(f"      TrOCR:    {trocr}")

    # Summary statistics
    if args.compare and all_regions:
        print("\n" + "=" * 70)
        print("QUALITY COMPARISON SUMMARY")
        print("=" * 70)

        wers = []
        cers = []
        for region in all_regions:
            if region.original_text and region.trocr_text:
                wers.append(word_error_rate(region.original_text, region.trocr_text))
                cers.append(char_error_rate(region.original_text, region.trocr_text))

        if wers:
            import statistics

            print(f"\nRegions compared: {len(wers)}")
            print(f"\nWord Error Rate (WER):")
            print(f"  Mean:   {statistics.mean(wers):.1%}")
            print(f"  Median: {statistics.median(wers):.1%}")
            print(f"  Min:    {min(wers):.1%}")
            print(f"  Max:    {max(wers):.1%}")

            print(f"\nCharacter Error Rate (CER):")
            print(f"  Mean:   {statistics.mean(cers):.1%}")
            print(f"  Median: {statistics.median(cers):.1%}")
            print(f"  Min:    {min(cers):.1%}")
            print(f"  Max:    {max(cers):.1%}")

            # Interpretation
            mean_cer = statistics.mean(cers)
            print("\nInterpretation:")
            if mean_cer < 0.02:
                print("  ✅ Excellent: TrOCR matches existing OCR well")
            elif mean_cer < 0.05:
                print("  ⚠️ Moderate: Some differences, review needed")
            else:
                print("  ❌ Poor: Significant differences, investigate")

            print(f"\nTotal processing time: {total_time:.1f}s")
            print(f"Avg time per page: {total_time / len(pages):.1f}s")

    print("\n" + "=" * 70)
    print("NOTES")
    print("=" * 70)
    print("""
TrOCR is designed for line-level OCR, not full text blocks.
High error rates may indicate:
1. Text blocks need to be segmented into lines
2. Image quality/resolution needs adjustment
3. Font or language not well-supported by model

For scanned documents like Kant, TrOCR may produce DIFFERENT text
than the existing OCR layer - this doesn't necessarily mean worse.
Manual spot-checking is recommended.

Next steps:
- Try line-level segmentation for better TrOCR performance
- Compare with ground truth if available
- Test microsoft/trocr-large-printed for better accuracy
""")


if __name__ == "__main__":
    main()
