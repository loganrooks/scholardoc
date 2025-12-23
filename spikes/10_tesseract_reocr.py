#!/usr/bin/env python3
"""Spike 10: Test Re-OCR Engines vs Existing Text Layer

Compare re-OCRing problematic PDF pages with Tesseract and EasyOCR (GPU)
against using the existing text layer + spell correction.

Hypothesis: For scanned PDFs with poor OCR, re-OCRing might produce
better results than relying on the existing text layer.

Usage:
    uv run python spikes/10_tesseract_reocr.py <pdf> [--pages 1,2,3]
    uv run python spikes/10_tesseract_reocr.py spikes/sample_pdfs/kant_critique_pages_64_65.pdf
    uv run python spikes/10_tesseract_reocr.py <pdf> --engine easyocr  # GPU-accelerated
    uv run python spikes/10_tesseract_reocr.py <pdf> --engine all      # Compare all engines
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import NamedTuple

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF required. Run: uv add pymupdf")
    sys.exit(1)

try:
    import pytesseract
    from PIL import Image
except ImportError:
    print("ERROR: pytesseract and Pillow required. Run: uv add pytesseract pillow")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    print("ERROR: sentence-transformers required. Run: uv add sentence-transformers")
    sys.exit(1)

# Optional: EasyOCR for GPU acceleration
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

# Optional: docTR for document-specific neural OCR
try:
    from doctr.io import DocumentFile
    from doctr.models import ocr_predictor
    DOCTR_AVAILABLE = True
except ImportError:
    DOCTR_AVAILABLE = False


class OCRResult(NamedTuple):
    """Result of OCR extraction."""
    text: str
    method: str
    word_count: int
    char_count: int


def extract_existing_text(doc: fitz.Document, page_num: int) -> OCRResult:
    """Extract text from existing PDF text layer."""
    page = doc[page_num]
    text = page.get_text()
    words = text.split()
    return OCRResult(
        text=text,
        method="existing_layer",
        word_count=len(words),
        char_count=len(text)
    )


def render_page_to_image(doc: fitz.Document, page_num: int, dpi: int = 300) -> Image.Image:
    """Render a PDF page to PIL Image."""
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def reocr_with_tesseract(doc: fitz.Document, page_num: int, dpi: int = 300) -> OCRResult:
    """Re-OCR a page with Tesseract (CPU only)."""
    img = render_page_to_image(doc, page_num, dpi)

    start = time.time()
    text = pytesseract.image_to_string(img, lang='eng')
    elapsed = time.time() - start

    words = text.split()
    return OCRResult(
        text=text,
        method=f"tesseract (CPU, {elapsed:.2f}s)",
        word_count=len(words),
        char_count=len(text)
    )


# Global EasyOCR reader (lazy initialization for GPU warmup)
_easyocr_reader = None


def get_easyocr_reader(gpu: bool = True):
    """Get or initialize EasyOCR reader."""
    global _easyocr_reader
    if _easyocr_reader is None and EASYOCR_AVAILABLE:
        print(f"Initializing EasyOCR (GPU={gpu})...")
        _easyocr_reader = easyocr.Reader(['en'], gpu=gpu, verbose=False)
    return _easyocr_reader


def reocr_with_easyocr(doc: fitz.Document, page_num: int, dpi: int = 300, gpu: bool = True) -> OCRResult:
    """Re-OCR a page with EasyOCR (GPU-accelerated)."""
    if not EASYOCR_AVAILABLE:
        return OCRResult(
            text="[EasyOCR not installed]",
            method="easyocr (unavailable)",
            word_count=0,
            char_count=0
        )

    img = render_page_to_image(doc, page_num, dpi)
    reader = get_easyocr_reader(gpu)

    start = time.time()
    # EasyOCR returns list of (bbox, text, confidence) tuples
    results = reader.readtext(np.array(img), detail=1)
    elapsed = time.time() - start

    # Sort by vertical position (y-coordinate) then horizontal
    results.sort(key=lambda r: (r[0][0][1], r[0][0][0]))

    # Concatenate all text
    text = " ".join(r[1] for r in results)

    words = text.split()
    device = "GPU" if gpu else "CPU"
    return OCRResult(
        text=text,
        method=f"easyocr ({device}, {elapsed:.2f}s)",
        word_count=len(words),
        char_count=len(text)
    )


# Global docTR predictor (lazy initialization)
_doctr_predictor = None


def get_doctr_predictor(gpu: bool = True):
    """Get or initialize docTR OCR predictor."""
    global _doctr_predictor
    if _doctr_predictor is None and DOCTR_AVAILABLE:
        print(f"Initializing docTR (GPU={gpu})...")
        device = "cuda" if gpu else "cpu"
        _doctr_predictor = ocr_predictor(pretrained=True).to(device)
    return _doctr_predictor


def reocr_with_doctr(doc: fitz.Document, page_num: int, dpi: int = 300, gpu: bool = True) -> OCRResult:
    """Re-OCR a page with docTR (document-specific neural OCR)."""
    if not DOCTR_AVAILABLE:
        return OCRResult(
            text="[docTR not installed]",
            method="doctr (unavailable)",
            word_count=0,
            char_count=0
        )

    img = render_page_to_image(doc, page_num, dpi)
    predictor = get_doctr_predictor(gpu)

    # Save temp image for docTR (it expects file path or bytes)
    import io
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    start = time.time()
    # docTR expects document-like input
    doc_input = DocumentFile.from_images([buf.read()])
    result = predictor(doc_input)
    elapsed = time.time() - start

    # Extract text from result
    text_parts = []
    for page in result.pages:
        for block in page.blocks:
            for line in block.lines:
                line_text = " ".join(word.value for word in line.words)
                text_parts.append(line_text)

    text = "\n".join(text_parts)
    words = text.split()
    device = "GPU" if gpu else "CPU"

    return OCRResult(
        text=text,
        method=f"doctr ({device}, {elapsed:.2f}s)",
        word_count=len(words),
        char_count=len(text)
    )


def compute_embedding_similarity(model: SentenceTransformer, text1: str, text2: str) -> float:
    """Compute cosine similarity between two texts using embeddings."""
    if not text1.strip() or not text2.strip():
        return 0.0

    embeddings = model.encode([text1, text2])
    similarity = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    return float(similarity)


def apply_basic_correction(text: str) -> str:
    """Apply basic OCR correction patterns."""
    corrections = {
        # Common OCR errors
        'rn': 'm',  # rn→m confusion
        'cl': 'd',  # cl→d confusion
        'tl': 'ti', # tl→ti substitution
        'Beautlful': 'Beautiful',
        'beautlful': 'beautiful',
        'rnorning': 'morning',
        'cloing': 'doing',
        'tbat': 'that',
        'wbich': 'which',
        'bave': 'have',
        'judgrnent': 'judgment',
        'judgrment': 'judgment',
    }

    result = text
    for old, new in corrections.items():
        result = result.replace(old, new)

    return result


def load_ground_truth(gt_path: Path) -> str | None:
    """Load ground truth text from JSON file."""
    if not gt_path.exists():
        return None

    with open(gt_path) as f:
        data = json.load(f)

    # Extract the full footnote content as ground truth
    if "features" in data and "footnotes" in data["features"]:
        footnotes = data["features"]["footnotes"]
        if footnotes and "continuation" in footnotes[0]:
            return footnotes[0]["continuation"].get("full_content", "")

    return None


def analyze_page(
    doc: fitz.Document,
    page_num: int,
    model: SentenceTransformer,
    ground_truth: str | None = None,
    engines: list[str] = None,
    gpu: bool = True,
    verbose: bool = True
) -> dict:
    """Analyze OCR quality for a single page with multiple engines."""
    if engines is None:
        engines = ["tesseract"]

    # Extract existing text
    existing = extract_existing_text(doc, page_num)
    existing_corrected = apply_basic_correction(existing.text)

    results = {
        "page": page_num,
        "existing": {
            "word_count": existing.word_count,
            "char_count": existing.char_count,
        },
    }

    # Run each OCR engine
    ocr_results = {}
    for engine in engines:
        if engine == "tesseract":
            ocr_results["tesseract"] = reocr_with_tesseract(doc, page_num)
        elif engine == "easyocr":
            ocr_results["easyocr"] = reocr_with_easyocr(doc, page_num, gpu=gpu)
        elif engine == "doctr":
            ocr_results["doctr"] = reocr_with_doctr(doc, page_num, gpu=gpu)

    # Store OCR results
    for name, result in ocr_results.items():
        results[name] = {
            "method": result.method,
            "word_count": result.word_count,
            "char_count": result.char_count,
        }

    # Compare to ground truth if available
    if ground_truth:
        existing_vs_gt = compute_embedding_similarity(model, existing.text, ground_truth)
        existing_corrected_vs_gt = compute_embedding_similarity(model, existing_corrected, ground_truth)

        gt_results = {
            "existing_similarity": existing_vs_gt,
            "existing_corrected_similarity": existing_corrected_vs_gt,
        }

        best_score = existing_corrected_vs_gt
        best_method = "existing_corrected"

        for name, result in ocr_results.items():
            sim = compute_embedding_similarity(model, result.text, ground_truth)
            gt_results[f"{name}_similarity"] = sim
            if sim > best_score:
                best_score = sim
                best_method = name

        gt_results["winner"] = best_method
        gt_results["best_score"] = best_score
        results["ground_truth"] = gt_results

    if verbose:
        print(f"\n{'='*60}")
        print(f"Page {page_num + 1}")
        print(f"{'='*60}")
        print(f"\n📊 Word counts:")
        print(f"   Existing layer: {existing.word_count:,} words ({existing.char_count:,} chars)")
        for name, result in ocr_results.items():
            print(f"   {name.capitalize():12}: {result.word_count:,} words ({result.char_count:,} chars) - {result.method}")

        if ground_truth and "ground_truth" in results:
            gt = results["ground_truth"]
            print(f"\n🎯 Ground Truth comparison (embedding similarity):")
            print(f"   Existing layer:         {gt['existing_similarity']:.3f}")
            print(f"   Existing + correction:  {gt['existing_corrected_similarity']:.3f}")
            for name in ocr_results:
                print(f"   {name.capitalize():20}: {gt[f'{name}_similarity']:.3f}")
            print(f"\n   🏆 Winner: {gt['winner']} ({gt['best_score']:.3f})")

        # Show sample differences
        print(f"\n📝 Text samples (first 200 chars):")
        print(f"\n   Existing: {existing.text[:200].replace(chr(10), ' ')!r}")
        for name, result in ocr_results.items():
            print(f"\n   {name.capitalize()}: {result.text[:200].replace(chr(10), ' ')!r}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Test OCR engines vs existing text layer")
    parser.add_argument("pdf", type=Path, help="PDF file to analyze")
    parser.add_argument("--pages", type=str, default=None,
                        help="Comma-separated page numbers (1-indexed), default: all")
    parser.add_argument("--ground-truth", "-g", type=Path, default=None,
                        help="Ground truth JSON file for comparison")
    parser.add_argument("--model", type=str, default="all-MiniLM-L6-v2",
                        help="Sentence transformer model for embeddings")
    parser.add_argument("--engine", "-e", type=str, default="tesseract",
                        choices=["tesseract", "easyocr", "doctr", "all"],
                        help="OCR engine to use (default: tesseract)")
    parser.add_argument("--no-gpu", action="store_true", help="Disable GPU for EasyOCR")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")

    args = parser.parse_args()

    # Parse engines
    if args.engine == "all":
        engines = ["tesseract"]
        if EASYOCR_AVAILABLE:
            engines.append("easyocr")
        if DOCTR_AVAILABLE:
            engines.append("doctr")
    else:
        engines = [args.engine]

    if "easyocr" in engines and not EASYOCR_AVAILABLE:
        print("WARNING: EasyOCR not available, removing from engines")
        engines = [e for e in engines if e != "easyocr"]

    if "doctr" in engines and not DOCTR_AVAILABLE:
        print("WARNING: docTR not available, removing from engines")
        engines = [e for e in engines if e != "doctr"]

    if not engines:
        engines = ["tesseract"]

    if not args.pdf.exists():
        print(f"ERROR: PDF not found: {args.pdf}")
        sys.exit(1)

    # Load PDF
    doc = fitz.open(args.pdf)
    total_pages = len(doc)

    # Parse page numbers
    if args.pages:
        pages = [int(p.strip()) - 1 for p in args.pages.split(",")]
    else:
        pages = list(range(total_pages))

    # Load model
    print(f"Loading embedding model: {args.model}...")
    model = SentenceTransformer(args.model)

    # Load ground truth if available
    ground_truth = None
    if args.ground_truth and args.ground_truth.exists():
        ground_truth = load_ground_truth(args.ground_truth)
        if ground_truth:
            print(f"Loaded ground truth: {len(ground_truth)} chars")

    # Auto-detect ground truth for known test files
    if ground_truth is None:
        pdf_name = args.pdf.name.lower()
        if "kant" in pdf_name and ("64" in pdf_name or "65" in pdf_name):
            gt_path = Path("ground_truth/footnotes/kant_footnotes.json")
            if gt_path.exists():
                ground_truth = load_ground_truth(gt_path)
                if ground_truth:
                    print(f"Auto-loaded ground truth for Kant pages 64-65")

    print(f"\nAnalyzing {args.pdf.name} ({total_pages} pages)")
    print(f"Testing pages: {[p+1 for p in pages]}")
    print(f"OCR engines: {engines}")

    all_results = []
    gpu = not args.no_gpu

    for page_num in pages:
        if page_num >= total_pages:
            print(f"WARNING: Page {page_num + 1} out of range, skipping")
            continue

        result = analyze_page(
            doc, page_num, model, ground_truth,
            engines=engines, gpu=gpu, verbose=not args.quiet
        )
        all_results.append(result)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    if ground_truth and all_results and "ground_truth" in all_results[0]:
        # Collect scores for each method
        method_scores = {}
        method_scores["existing"] = [r["ground_truth"]["existing_similarity"] for r in all_results if "ground_truth" in r]
        method_scores["existing_corrected"] = [r["ground_truth"]["existing_corrected_similarity"] for r in all_results if "ground_truth" in r]

        for engine in engines:
            key = f"{engine}_similarity"
            method_scores[engine] = [
                r["ground_truth"].get(key, 0) for r in all_results
                if "ground_truth" in r and key in r["ground_truth"]
            ]

        print(f"\n🎯 Average similarity to ground truth:")
        averages = []
        for method, scores in method_scores.items():
            if scores:
                avg = np.mean(scores)
                averages.append((method, avg))
                print(f"   {method:20}: {avg:.3f}")

        if averages:
            best = max(averages, key=lambda x: x[1])
            print(f"\n   🏆 Best method: {best[0]} ({best[1]:.3f})")
    else:
        print("\n⚠️ No ground truth available - cannot determine which is better")
        print("   Recommendation: Provide ground truth with --ground-truth flag")

    doc.close()

    return all_results


if __name__ == "__main__":
    main()
