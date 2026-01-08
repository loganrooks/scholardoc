#!/usr/bin/env python3
"""
Visualize Ground Truth Annotations

Renders a PDF with ground truth annotations overlaid for human review.
Outputs an HTML file that can be opened in a browser.

Usage:
    uv run python ground_truth/scripts/visualize.py <yaml_path>
    uv run python ground_truth/scripts/visualize.py <yaml_path> --output review.html
    uv run python ground_truth/scripts/visualize.py <yaml_path> --pdf-dir /path/to/pdfs
"""

from __future__ import annotations

import argparse
import base64
from pathlib import Path
from typing import Any

import fitz
import yaml

# Color scheme for region types (RGB)
REGION_COLORS = {
    "body": (66, 133, 244),  # Blue
    "footnote_region": (234, 67, 53),  # Red
    "footnote_continuation": (234, 67, 53),  # Red
    "header": (251, 188, 4),  # Yellow
    "footer": (251, 188, 4),  # Yellow
    "heading": (52, 168, 83),  # Green
    "page_number": (255, 109, 0),  # Orange
    "margin": (156, 39, 176),  # Purple
    "figure": (0, 188, 212),  # Cyan
    "caption": (121, 85, 72),  # Brown
    "table": (96, 125, 139),  # Gray
    "unknown": (128, 128, 128),  # Gray
}


def load_ground_truth(yaml_path: Path) -> dict[str, Any]:
    """Load ground truth YAML file."""
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def render_page_with_annotations(
    pdf_page: fitz.Page,
    page_data: dict[str, Any],
    dpi: int = 150,
) -> bytes:
    """Render a PDF page with bounding box annotations overlaid."""
    # Render page to pixmap
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = pdf_page.get_pixmap(matrix=mat)

    # Convert to PNG and then to PIL for drawing
    # We'll use fitz's shape drawing directly
    shape = pdf_page.new_shape()

    for region in page_data.get("regions", []):
        bbox = region["bbox"]
        region_type = region["type"]

        # Convert normalized coords to PDF points
        rect = fitz.Rect(
            bbox[0] * pdf_page.rect.width,
            bbox[1] * pdf_page.rect.height,
            bbox[2] * pdf_page.rect.width,
            bbox[3] * pdf_page.rect.height,
        )

        # Get color for this region type
        color = REGION_COLORS.get(region_type, REGION_COLORS["unknown"])
        # Normalize to 0-1 for fitz
        color_norm = tuple(c / 255 for c in color)

        # Draw rectangle
        shape.draw_rect(rect)
        shape.finish(color=color_norm, width=2, fill=None)

        # Draw label
        label = f"{region['id']}"
        point = fitz.Point(rect.x0 + 2, rect.y0 + 12)
        shape.insert_text(point, label, fontsize=10, color=color_norm)

    shape.commit()

    # Re-render with annotations
    pix = pdf_page.get_pixmap(matrix=mat)
    return pix.tobytes("png")


def generate_html(
    ground_truth: dict[str, Any],
    pdf_path: Path,
    output_path: Path,
    dpi: int = 150,
) -> None:
    """Generate HTML visualization of ground truth annotations."""
    doc = fitz.open(pdf_path)

    pages_html = []
    page_range = ground_truth["source"].get("page_range", [0, len(doc)])

    for page_data in ground_truth["pages"]:
        page_idx = page_data["index"]

        if page_idx >= len(doc):
            continue

        pdf_page = doc[page_idx]

        # Render page with annotations
        img_bytes = render_page_with_annotations(pdf_page, page_data, dpi)
        img_b64 = base64.b64encode(img_bytes).decode()

        # Build region info table
        regions_html = ""
        for region in page_data.get("regions", []):
            color = REGION_COLORS.get(region["type"], REGION_COLORS["unknown"])
            color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"

            # Escape text for HTML
            text = region.get("text", "")[:200]
            if len(region.get("text", "")) > 200:
                text += "..."
            text = text.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

            special = region.get("special_chars", [])
            special_html = ""
            if special:
                special_html = (
                    "<br><small>Special: "
                    + ", ".join(f"<code>{s['lang']}:{s['text']}</code>" for s in special[:3])
                    + "</small>"
                )

            regions_html += f"""
            <tr>
                <td><span style="color: {color_hex}; font-weight: bold;">{region["id"]}</span></td>
                <td>{region["type"]}</td>
                <td><small>{text}{special_html}</small></td>
            </tr>
            """

        # Build elements summary for this page
        elements_html = ""
        page_idx_val = page_data["index"]

        # Footnotes on this page
        footnotes = [
            fn
            for fn in ground_truth.get("elements", {}).get("footnotes", [])
            if page_idx_val in fn.get("pages", [])
        ]
        if footnotes:
            elements_html += f"<p><strong>Footnotes:</strong> {len(footnotes)}</p>"
            for fn in footnotes[:5]:
                content_text = fn["content"][0]["text"][:100] if fn["content"] else ""
                elements_html += f"<p><small>• {fn['id']}: {content_text}...</small></p>"

        # Citations on this page
        citations = [
            c
            for c in ground_truth.get("elements", {}).get("citations", [])
            if c.get("page") == page_idx_val
        ]
        if citations:
            elements_html += f"<p><strong>Citations:</strong> {len(citations)}</p>"
            for c in citations[:5]:
                elements_html += f"<p><small>• {c['raw']}</small></p>"

        pages_html.append(f"""
        <div class="page-container">
            <h2>Page {page_idx} (Label: {page_data.get("label", "N/A")})</h2>
            <div class="page-content">
                <div class="page-image">
                    <img src="data:image/png;base64,{img_b64}" alt="Page {page_idx}">
                </div>
                <div class="page-info">
                    <h3>Regions ({len(page_data.get("regions", []))})</h3>
                    <table class="regions-table">
                        <thead>
                            <tr><th>ID</th><th>Type</th><th>Text</th></tr>
                        </thead>
                        <tbody>
                            {regions_html}
                        </tbody>
                    </table>

                    <h3>Elements</h3>
                    {elements_html or "<p><em>No elements detected on this page</em></p>"}

                    <h3>Quality</h3>
                    <p>Scan: {page_data.get("quality", {}).get("scan_quality", "N/A")}</p>
                    <p>Difficulty: {page_data.get("quality", {}).get("difficulty", "N/A")}</p>
                </div>
            </div>
        </div>
        """)

    doc.close()

    # Build annotation status summary
    status_html = ""
    for element_type, status in ground_truth.get("annotation_status", {}).items():
        state = status.get("state", "pending")
        count = status.get("count", "?")
        state_class = {
            "verified": "status-verified",
            "annotated": "status-annotated",
            "auto_generated": "status-auto",
            "pending": "status-pending",
        }.get(state, "status-pending")
        status_html += f"""
        <tr>
            <td>{element_type}</td>
            <td class="{state_class}">{state}</td>
            <td>{count if count is not None else "?"}</td>
        </tr>
        """

    # Full HTML document
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Ground Truth Review: {ground_truth["source"]["pdf"]}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
            }}
            .header {{
                background: white;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header h1 {{
                margin: 0 0 10px 0;
            }}
            .meta-table {{
                border-collapse: collapse;
                margin-top: 10px;
            }}
            .meta-table td {{
                padding: 4px 12px 4px 0;
            }}
            .status-table {{
                border-collapse: collapse;
                margin-top: 10px;
            }}
            .status-table th, .status-table td {{
                padding: 6px 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            .status-verified {{ color: #34a853; font-weight: bold; }}
            .status-annotated {{ color: #4285f4; }}
            .status-auto {{ color: #fbbc04; }}
            .status-pending {{ color: #ea4335; }}
            .page-container {{
                background: white;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .page-content {{
                display: flex;
                gap: 20px;
            }}
            .page-image {{
                flex: 0 0 auto;
            }}
            .page-image img {{
                max-width: 600px;
                border: 1px solid #ddd;
            }}
            .page-info {{
                flex: 1;
                min-width: 300px;
            }}
            .regions-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 12px;
            }}
            .regions-table th, .regions-table td {{
                padding: 6px;
                text-align: left;
                border-bottom: 1px solid #eee;
                vertical-align: top;
            }}
            .legend {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 10px;
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                gap: 4px;
                font-size: 12px;
            }}
            .legend-color {{
                width: 16px;
                height: 16px;
                border-radius: 2px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Ground Truth Review</h1>
            <table class="meta-table">
                <tr><td><strong>PDF:</strong></td><td>{ground_truth["source"]["pdf"]}</td></tr>
                <tr><td><strong>Page Range:</strong></td><td>{page_range[0]}-{
        page_range[1]
    }</td></tr>
                <tr><td><strong>Schema:</strong></td><td>{
        ground_truth.get("schema_version", "?")
    }</td></tr>
                <tr><td><strong>Created:</strong></td><td>{
        ground_truth.get("metadata", {}).get("created", "?")
    }</td></tr>
            </table>

            <h3>Annotation Status</h3>
            <table class="status-table">
                <thead>
                    <tr><th>Element</th><th>State</th><th>Count</th></tr>
                </thead>
                <tbody>
                    {status_html}
                </tbody>
            </table>

            <h3>Color Legend</h3>
            <div class="legend">
                {
        "".join(
            f'''<div class="legend-item">
                    <div class="legend-color" style="background: rgb({c[0]},{c[1]},{c[2]})"></div>
                    <span>{t}</span>
                </div>'''
            for t, c in REGION_COLORS.items()
        )
    }
            </div>
        </div>

        {"".join(pages_html)}

        <div class="header">
            <h3>Notes</h3>
            <p>{ground_truth.get("metadata", {}).get("notes", "No notes.")}</p>
        </div>
    </body>
    </html>
    """

    with open(output_path, "w") as f:
        f.write(html)

    print(f"Visualization written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Visualize ground truth annotations")
    parser.add_argument("yaml_path", type=Path, help="Path to ground truth YAML file")
    parser.add_argument(
        "--output", "-o", type=Path, help="Output HTML path (default: <yaml_name>_review.html)"
    )
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        default=Path("spikes/sample_pdfs"),
        help="Directory containing PDFs (default: spikes/sample_pdfs)",
    )
    parser.add_argument("--dpi", type=int, default=150, help="Render DPI (default: 150)")

    args = parser.parse_args()

    if not args.yaml_path.exists():
        print(f"ERROR: YAML file not found: {args.yaml_path}")
        return

    # Load ground truth
    ground_truth = load_ground_truth(args.yaml_path)

    # Find PDF
    pdf_name = ground_truth["source"]["pdf"]
    pdf_path = args.pdf_dir / pdf_name
    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        print(f"Looked in: {args.pdf_dir}")
        return

    # Output path
    if args.output:
        output_path = args.output
    else:
        output_path = args.yaml_path.with_suffix(".html")

    generate_html(ground_truth, pdf_path, output_path, args.dpi)


if __name__ == "__main__":
    main()
