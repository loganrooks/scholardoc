#!/usr/bin/env python3
"""
Spike 32: Document Layout Segmentation Evaluation

Evaluates three layout segmentation libraries for scholarly PDF processing:
1. Surya - All-around scholarly documents (footnotes, reading order, tables)
2. DETR-DocLayNet - Best footnote accuracy (78% F1)
3. DocLayout-YOLO - Fastest (85 FPS)

Hardware: GTX 1080Ti (11GB VRAM, compute capability 6.1)
Requires: PyTorch with CUDA 12.4 or 12.6 (cu124/cu126) - NOT cu128+

Usage:
    # First, install dependencies (see install_dependencies())
    uv run python spikes/32_layout_segmentation.py --install

    # Then run evaluation
    uv run python spikes/32_layout_segmentation.py <pdf_path> [--page N]
    uv run python spikes/32_layout_segmentation.py spikes/sample_pdfs/heidegger_pages_22-23.pdf

    # Run all three models
    uv run python spikes/32_layout_segmentation.py <pdf_path> --all

    # Run specific model
    uv run python spikes/32_layout_segmentation.py <pdf_path> --model surya
    uv run python spikes/32_layout_segmentation.py <pdf_path> --model detr
    uv run python spikes/32_layout_segmentation.py <pdf_path> --model yolo
"""

from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

# Check if we're in the right directory
PROJECT_ROOT = Path(__file__).parent.parent
SPIKE_DIR = Path(__file__).parent
OUTPUT_DIR = SPIKE_DIR / "output" / "32_layout_segmentation"


def check_cuda_compatibility():
    """Check CUDA/PyTorch compatibility with GTX 1080Ti."""
    print("\n" + "=" * 60)
    print("CUDA Compatibility Check (GTX 1080Ti = compute capability 6.1)")
    print("=" * 60)

    try:
        import torch

        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"GPU: {torch.cuda.get_device_name(0)}")

            # Check compute capability
            capability = torch.cuda.get_device_capability(0)
            print(f"Compute capability: {capability[0]}.{capability[1]}")

            if capability[0] < 6 or (capability[0] == 6 and capability[1] < 1):
                print("WARNING: GPU compute capability too low!")
                return False

            # Check if sm_61 is supported
            # This is tricky - newer PyTorch+CUDA might not include sm_61
            print(f"cuDNN version: {torch.backends.cudnn.version()}")

            # Test tensor creation on GPU
            try:
                x = torch.tensor([1.0, 2.0, 3.0], device="cuda")
                y = x * 2
                print(f"GPU tensor test: PASSED ({y.device})")
                return True
            except Exception as e:
                print(f"GPU tensor test: FAILED - {e}")
                return False
        else:
            print("CUDA not available - will use CPU")
            return False

    except ImportError:
        print("PyTorch not installed")
        return False


def install_dependencies():
    """Install required dependencies for layout segmentation."""
    print("\n" + "=" * 60)
    print("Installing Dependencies")
    print("=" * 60)

    # GTX 1080Ti requires CUDA 12.4 or lower for Pascal support
    # CUDA 12.8+ dropped sm_61 support
    print("""
NOTE: GTX 1080Ti (Pascal, sm_61) compatibility:
- PyTorch 2.4+ with CUDA 12.4 or 12.6 works
- PyTorch with CUDA 12.8+ does NOT support GTX 1080Ti
- We'll use cu124 wheels for best compatibility

Installing PyTorch with CUDA 12.4...
""")

    # Install PyTorch with CUDA 12.4 (supports sm_61)
    pytorch_cmd = [
        "uv",
        "pip",
        "install",
        "--index-url",
        "https://download.pytorch.org/whl/cu124",
        "torch",
        "torchvision",
    ]
    print(f"Running: {' '.join(pytorch_cmd)}")
    result = subprocess.run(pytorch_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"PyTorch install failed: {result.stderr}")
        # Try cu118 as fallback
        print("\nTrying CUDA 11.8 as fallback...")
        pytorch_cmd = [
            "uv",
            "pip",
            "install",
            "--index-url",
            "https://download.pytorch.org/whl/cu118",
            "torch",
            "torchvision",
        ]
        result = subprocess.run(pytorch_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Fallback also failed: {result.stderr}")
            return False

    print("PyTorch installed successfully!")

    # Check CUDA works
    if not check_cuda_compatibility():
        print("\nWARNING: CUDA test failed. Models will run on CPU.")

    # Install layout segmentation libraries
    libraries = [
        # Surya - all-around scholarly documents
        ("surya-ocr", "Surya (layout + OCR)"),
        # DETR-DocLayNet - best footnote accuracy
        ("transformers", "Transformers (for DETR)"),
        # DocLayout-YOLO - fastest
        ("doclayout-yolo", "DocLayout-YOLO"),
        # Common dependencies
        ("huggingface-hub", "Hugging Face Hub"),
        ("pillow", "Pillow"),
    ]

    for package, desc in libraries:
        print(f"\nInstalling {desc}...")
        result = subprocess.run(["uv", "pip", "install", package], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  WARNING: {package} install failed: {result.stderr[:200]}")
        else:
            print(f"  {package} installed")

    print("\n" + "=" * 60)
    print("Installation complete! Run without --install to evaluate models.")
    print("=" * 60)
    return True


def pdf_to_images(pdf_path: Path, page_num: int | None = None) -> list[tuple[int, Image]]:
    """Convert PDF pages to PIL Images."""
    import io

    import fitz
    from PIL import Image

    doc = fitz.open(pdf_path)
    images = []

    pages = [page_num] if page_num is not None else range(len(doc))

    for i in pages:
        if i >= len(doc):
            print(f"Warning: Page {i} does not exist (PDF has {len(doc)} pages)")
            continue
        page = doc[i]
        # Render at 150 DPI for good quality without excessive memory
        mat = fitz.Matrix(150 / 72, 150 / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        images.append((i, img))

    doc.close()
    return images


def evaluate_surya(images: list[tuple[int, Image]], output_dir: Path) -> dict:
    """Evaluate Surya layout detection."""
    print("\n" + "-" * 40)
    print("Evaluating: Surya")
    print("-" * 40)

    results = {"model": "surya", "pages": [], "total_time": 0, "error": None}

    try:
        # Surya v0.9+ uses LayoutPredictor with FoundationPredictor
        from surya.foundation import FoundationPredictor
        from surya.layout import LayoutPredictor

        print("Loading Surya FoundationPredictor + LayoutPredictor...")
        start_load = time.time()
        foundation = FoundationPredictor(device="cuda")
        predictor = LayoutPredictor(foundation)
        load_time = time.time() - start_load
        print(f"Model loaded in {load_time:.2f}s")

        # Process each page
        pil_images = [img for _, img in images]
        page_nums = [num for num, _ in images]

        print(f"Processing {len(pil_images)} page(s)...")
        start_infer = time.time()
        layout_results = list(predictor(pil_images))
        infer_time = time.time() - start_infer

        results["total_time"] = infer_time
        results["time_per_page"] = infer_time / len(pil_images)

        # Process results
        for page_num, layout in zip(page_nums, layout_results, strict=True):
            page_result = {"page": page_num, "regions": [], "by_type": {}}

            for bbox in layout.bboxes:
                region = {
                    "type": bbox.label,
                    "confidence": getattr(bbox, "confidence", 1.0),
                    "bbox": bbox.bbox,  # [x1, y1, x2, y2]
                }
                page_result["regions"].append(region)

                # Count by type
                if bbox.label not in page_result["by_type"]:
                    page_result["by_type"][bbox.label] = 0
                page_result["by_type"][bbox.label] += 1

            results["pages"].append(page_result)

            print(f"\nPage {page_num}:")
            print(f"  Total regions: {len(page_result['regions'])}")
            for label, count in sorted(page_result["by_type"].items()):
                print(f"  - {label}: {count}")

        # Save visualization
        try:
            from PIL import ImageDraw

            for (page_num, img), layout in zip(images, layout_results, strict=True):
                vis_img = img.copy()
                draw = ImageDraw.Draw(vis_img)

                colors = {
                    "Footnote": "red",
                    "Text": "blue",
                    "SectionHeader": "green",
                    "PageHeader": "orange",
                    "PageFooter": "orange",
                    "Table": "purple",
                    "Picture": "cyan",
                    "Caption": "magenta",
                    "Formula": "yellow",
                }

                for bbox in layout.bboxes:
                    color = colors.get(bbox.label, "gray")
                    draw.rectangle(bbox.bbox, outline=color, width=2)
                    conf = getattr(bbox, "confidence", 1.0)
                    draw.text(
                        (bbox.bbox[0], bbox.bbox[1] - 15),
                        f"{bbox.label} ({conf:.2f})",
                        fill=color,
                    )

                vis_path = output_dir / f"surya_page_{page_num}.png"
                vis_img.save(vis_path)
                print(f"  Saved: {vis_path}")
        except Exception as e:
            print(f"  Visualization failed: {e}")

        print(f"\nSurya total time: {infer_time:.2f}s ({results['time_per_page']:.2f}s/page)")

    except ImportError as e:
        results["error"] = f"Import error: {e}. Run with --install first."
        print(f"ERROR: {results['error']}")
    except Exception as e:
        results["error"] = str(e)
        print(f"ERROR: {e}")

    return results


def evaluate_detr(images: list[tuple[int, Image]], output_dir: Path) -> dict:
    """Evaluate DETR-DocLayNet model."""
    print("\n" + "-" * 40)
    print("Evaluating: DETR-DocLayNet")
    print("-" * 40)

    results = {"model": "detr-doclaynet", "pages": [], "total_time": 0, "error": None}

    try:
        import torch
        from transformers import AutoImageProcessor, DetrForObjectDetection

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")

        print("Loading DETR-DocLayNet model...")
        start_load = time.time()
        processor = AutoImageProcessor.from_pretrained("cmarkea/detr-layout-detection")
        model = DetrForObjectDetection.from_pretrained("cmarkea/detr-layout-detection")
        model = model.to(device)
        model.eval()
        load_time = time.time() - start_load
        print(f"Model loaded in {load_time:.2f}s")

        labels = {
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
        }

        total_infer_time = 0

        for page_num, img in images:
            print(f"\nProcessing page {page_num}...")

            start_infer = time.time()
            with torch.inference_mode():
                inputs = processor(img, return_tensors="pt").to(device)
                outputs = model(**inputs)

            # Post-process
            target_sizes = torch.tensor([img.size[::-1]]).to(device)
            detections = processor.post_process_object_detection(
                outputs, threshold=0.3, target_sizes=target_sizes
            )[0]

            infer_time = time.time() - start_infer
            total_infer_time += infer_time

            page_result = {"page": page_num, "regions": [], "by_type": {}, "time": infer_time}

            for score, label, box in zip(
                detections["scores"].cpu(),
                detections["labels"].cpu(),
                detections["boxes"].cpu(),
                strict=True,
            ):
                label_name = labels[label.item()]
                region = {"type": label_name, "confidence": score.item(), "bbox": box.tolist()}
                page_result["regions"].append(region)

                if label_name not in page_result["by_type"]:
                    page_result["by_type"][label_name] = 0
                page_result["by_type"][label_name] += 1

            results["pages"].append(page_result)

            print(f"  Time: {infer_time:.3f}s")
            print(f"  Total regions: {len(page_result['regions'])}")
            for label, count in sorted(page_result["by_type"].items()):
                print(f"  - {label}: {count}")

            # Visualization
            try:
                from PIL import ImageDraw

                vis_img = img.copy()
                draw = ImageDraw.Draw(vis_img)

                colors = {
                    "Footnote": "red",
                    "Text": "blue",
                    "Section-header": "green",
                    "Page-header": "orange",
                    "Page-footer": "orange",
                    "Table": "purple",
                    "Picture": "cyan",
                    "Caption": "magenta",
                    "Title": "darkgreen",
                }

                for region in page_result["regions"]:
                    color = colors.get(region["type"], "gray")
                    draw.rectangle(region["bbox"], outline=color, width=2)
                    draw.text(
                        (region["bbox"][0], region["bbox"][1] - 15),
                        f"{region['type']} ({region['confidence']:.2f})",
                        fill=color,
                    )

                vis_path = output_dir / f"detr_page_{page_num}.png"
                vis_img.save(vis_path)
                print(f"  Saved: {vis_path}")
            except Exception as e:
                print(f"  Visualization failed: {e}")

        results["total_time"] = total_infer_time
        results["time_per_page"] = total_infer_time / len(images)
        print(f"\nDETR total time: {total_infer_time:.2f}s ({results['time_per_page']:.3f}s/page)")

    except ImportError as e:
        results["error"] = f"Import error: {e}. Run with --install first."
        print(f"ERROR: {results['error']}")
    except Exception as e:
        results["error"] = str(e)
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()

    return results


def evaluate_yolo(images: list[tuple[int, Image]], output_dir: Path) -> dict:
    """Evaluate DocLayout-YOLO model."""
    print("\n" + "-" * 40)
    print("Evaluating: DocLayout-YOLO")
    print("-" * 40)

    results = {"model": "doclayout-yolo", "pages": [], "total_time": 0, "error": None}

    try:
        import torch
        from doclayout_yolo import YOLOv10
        from huggingface_hub import hf_hub_download

        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")

        print("Downloading DocLayout-YOLO model...")
        start_load = time.time()
        model_path = hf_hub_download(
            repo_id="juliozhao/DocLayout-YOLO-DocStructBench",
            filename="doclayout_yolo_docstructbench_imgsz1024.pt",
        )
        model = YOLOv10(model_path)
        load_time = time.time() - start_load
        print(f"Model loaded in {load_time:.2f}s")

        total_infer_time = 0

        for page_num, img in images:
            print(f"\nProcessing page {page_num}...")

            # Save temp image for YOLO
            temp_path = output_dir / f"temp_page_{page_num}.png"
            img.save(temp_path)

            start_infer = time.time()
            yolo_results = model.predict(str(temp_path), imgsz=1024, conf=0.2, device=device)
            infer_time = time.time() - start_infer
            total_infer_time += infer_time

            page_result = {"page": page_num, "regions": [], "by_type": {}, "time": infer_time}

            for r in yolo_results:
                for box in r.boxes:
                    label_name = r.names[int(box.cls)]
                    region = {
                        "type": label_name,
                        "confidence": box.conf.item(),
                        "bbox": box.xyxy[0].tolist(),
                    }
                    page_result["regions"].append(region)

                    if label_name not in page_result["by_type"]:
                        page_result["by_type"][label_name] = 0
                    page_result["by_type"][label_name] += 1

            results["pages"].append(page_result)

            print(f"  Time: {infer_time:.3f}s")
            print(f"  Total regions: {len(page_result['regions'])}")
            for label, count in sorted(page_result["by_type"].items()):
                print(f"  - {label}: {count}")

            # Save YOLO's built-in visualization
            try:
                from PIL import Image as PILImage

                for r in yolo_results:
                    vis_arr = r.plot(line_width=2)  # Returns numpy array
                    vis_img = PILImage.fromarray(vis_arr)
                    vis_path = output_dir / f"yolo_page_{page_num}.png"
                    vis_img.save(vis_path)
                    print(f"  Saved: {vis_path}")
            except Exception as e:
                print(f"  Visualization failed: {e}")

            # Clean up temp file
            temp_path.unlink()

        results["total_time"] = total_infer_time
        results["time_per_page"] = total_infer_time / len(images)
        print(f"\nYOLO total time: {total_infer_time:.2f}s ({results['time_per_page']:.3f}s/page)")

    except ImportError as e:
        results["error"] = f"Import error: {e}. Run with --install first."
        print(f"ERROR: {results['error']}")
    except Exception as e:
        results["error"] = str(e)
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()

    return results


def evaluate_docling(images: list[tuple[int, Image]], output_dir: Path) -> dict:
    """Evaluate Docling RT-DETR model - BEST FOR FOOTNOTES."""
    print("\n" + "-" * 40)
    print("Evaluating: Docling RT-DETR (ds4sd/docling-layout-heron)")
    print("-" * 40)

    results = {"model": "docling-rtdetr", "pages": [], "total_time": 0, "error": None}

    try:
        import torch
        from transformers import RTDetrImageProcessor, RTDetrV2ForObjectDetection

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")

        print("Loading Docling RT-DETR model...")
        start_load = time.time()
        processor = RTDetrImageProcessor.from_pretrained("ds4sd/docling-layout-heron")
        model = RTDetrV2ForObjectDetection.from_pretrained("ds4sd/docling-layout-heron")
        model = model.to(device)
        model.eval()
        load_time = time.time() - start_load
        print(f"Model loaded in {load_time:.2f}s")
        print(f"Classes: {model.config.id2label}")

        total_infer_time = 0

        for page_num, img in images:
            print(f"\nProcessing page {page_num}...")

            start_infer = time.time()
            inputs = processor(images=[img], return_tensors="pt").to(device)
            with torch.inference_mode():
                outputs = model(**inputs)

            target_sizes = torch.tensor([img.size[::-1]]).to(device)
            detections = processor.post_process_object_detection(
                outputs, threshold=0.3, target_sizes=target_sizes
            )[0]

            infer_time = time.time() - start_infer
            total_infer_time += infer_time

            page_result = {"page": page_num, "regions": [], "by_type": {}, "time": infer_time}

            for score, label, box in zip(
                detections["scores"].cpu(),
                detections["labels"].cpu(),
                detections["boxes"].cpu(),
                strict=True,
            ):
                label_name = model.config.id2label[label.item()]
                region = {"type": label_name, "confidence": score.item(), "bbox": box.tolist()}
                page_result["regions"].append(region)

                if label_name not in page_result["by_type"]:
                    page_result["by_type"][label_name] = 0
                page_result["by_type"][label_name] += 1

            results["pages"].append(page_result)

            print(f"  Time: {infer_time:.3f}s")
            print(f"  Total regions: {len(page_result['regions'])}")
            for label, count in sorted(page_result["by_type"].items()):
                print(f"  - {label}: {count}")

            # Visualization
            try:
                from PIL import ImageDraw

                vis_img = img.copy()
                draw = ImageDraw.Draw(vis_img)

                colors = {
                    "Footnote": "red",
                    "Text": "blue",
                    "Section-header": "green",
                    "Page-header": "orange",
                    "Page-footer": "orange",
                    "Table": "purple",
                    "Picture": "cyan",
                    "Caption": "magenta",
                    "Title": "darkgreen",
                }

                for region in page_result["regions"]:
                    color = colors.get(region["type"], "gray")
                    draw.rectangle(region["bbox"], outline=color, width=2)
                    draw.text(
                        (region["bbox"][0], region["bbox"][1] - 15),
                        f"{region['type']} ({region['confidence']:.2f})",
                        fill=color,
                    )

                vis_path = output_dir / f"docling_page_{page_num}.png"
                vis_img.save(vis_path)
                print(f"  Saved: {vis_path}")
            except Exception as e:
                print(f"  Visualization failed: {e}")

        results["total_time"] = total_infer_time
        results["time_per_page"] = total_infer_time / len(images)
        print(
            f"\nDocling total time: {total_infer_time:.2f}s ({results['time_per_page']:.3f}s/page)"
        )

    except ImportError as e:
        results["error"] = f"Import error: {e}. Run with --install first."
        print(f"ERROR: {results['error']}")
    except Exception as e:
        results["error"] = str(e)
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()

    return results


def print_summary(all_results: list[dict]):
    """Print comparison summary."""
    print("\n" + "=" * 60)
    print("SUMMARY: Layout Segmentation Comparison")
    print("=" * 60)

    # Speed comparison
    print("\n### Speed (per page)")
    for result in all_results:
        if result.get("error"):
            print(f"  {result['model']}: FAILED - {result['error'][:50]}...")
        elif result.get("time_per_page"):
            print(f"  {result['model']}: {result['time_per_page']:.3f}s/page")

    # Footnote detection
    print("\n### Footnote Detection")
    for result in all_results:
        if result.get("error"):
            continue

        total_footnotes = 0
        for page in result.get("pages", []):
            total_footnotes += page.get("by_type", {}).get("Footnote", 0)

        print(f"  {result['model']}: {total_footnotes} footnote(s) detected")

    # All detected types
    print("\n### Region Types Detected")
    for result in all_results:
        if result.get("error"):
            continue

        all_types = set()
        for page in result.get("pages", []):
            all_types.update(page.get("by_type", {}).keys())

        print(f"  {result['model']}: {', '.join(sorted(all_types))}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate layout segmentation models on scholarly PDFs"
    )
    parser.add_argument("pdf_path", nargs="?", help="Path to PDF file")
    parser.add_argument("--page", type=int, help="Specific page number (0-indexed)")
    parser.add_argument("--install", action="store_true", help="Install dependencies")
    parser.add_argument("--check", action="store_true", help="Check CUDA compatibility only")
    parser.add_argument("--all", action="store_true", help="Run all models (default)")
    parser.add_argument(
        "--model",
        choices=["surya", "detr", "yolo", "docling"],
        help="Run specific model only (docling recommended for footnotes)",
    )

    args = parser.parse_args()

    if args.install:
        install_dependencies()
        return

    if args.check:
        check_cuda_compatibility()
        return

    if not args.pdf_path:
        parser.print_help()
        print("\nExample:")
        print("  uv run python spikes/32_layout_segmentation.py --install")
        print("  uv run python spikes/32_layout_segmentation.py sample.pdf")
        return

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        return

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Processing: {pdf_path}")
    print(f"Output dir: {OUTPUT_DIR}")

    # Convert PDF to images
    images = pdf_to_images(pdf_path, args.page)
    print(f"Converted {len(images)} page(s) to images")

    # Determine which models to run
    all_results = []

    if args.model:
        models = [args.model]
    else:
        models = ["docling", "yolo"]  # Default to working models only

    for model in models:
        if model == "surya":
            all_results.append(evaluate_surya(images, OUTPUT_DIR))
        elif model == "detr":
            all_results.append(evaluate_detr(images, OUTPUT_DIR))
        elif model == "yolo":
            all_results.append(evaluate_yolo(images, OUTPUT_DIR))
        elif model == "docling":
            all_results.append(evaluate_docling(images, OUTPUT_DIR))

    # Print summary
    print_summary(all_results)

    # Save results as JSON
    import json

    results_path = OUTPUT_DIR / "results.json"
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to: {results_path}")


if __name__ == "__main__":
    main()
