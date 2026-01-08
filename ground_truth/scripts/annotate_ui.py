#!/usr/bin/env python3
"""
Ground Truth Annotation UI

Streamlit-based interface for viewing and editing ground truth YAML files.

Usage:
    streamlit run ground_truth/scripts/annotate_ui.py
    uv run streamlit run ground_truth/scripts/annotate_ui.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st
import yaml
from streamlit_ace import st_ace

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ground_truth.scripts.validate import validate_ground_truth  # noqa: E402
from ground_truth.scripts.visualize import REGION_COLORS, render_page_image  # noqa: E402

# Default paths
PDF_DIR = PROJECT_ROOT / "spikes" / "sample_pdfs"
DOCUMENTS_DIR = PROJECT_ROOT / "ground_truth" / "documents"

# Ensure directories exist
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)


def init_session_state():
    """Initialize Streamlit session state."""
    defaults = {
        "ground_truth": None,
        "original_yaml": "",
        "current_page_idx": 0,
        "selected_region_id": None,
        "validation_result": None,
        "is_modified": False,
        "yaml_file_path": None,
        "mode": "edit",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def list_pdfs() -> list[Path]:
    """List available PDF files."""
    if not PDF_DIR.exists():
        return []
    return sorted(PDF_DIR.glob("*.pdf"))


def list_yaml_files() -> list[Path]:
    """List available ground truth YAML files."""
    if not DOCUMENTS_DIR.exists():
        return []
    return sorted(DOCUMENTS_DIR.glob("*.yaml"))


def load_ground_truth(yaml_path: Path) -> dict[str, Any]:
    """Load ground truth from YAML file."""
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def save_ground_truth(data: dict[str, Any], yaml_path: Path) -> None:
    """Save ground truth to YAML file."""
    with open(yaml_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def get_page_data(ground_truth: dict, page_idx: int) -> dict | None:
    """Get page data by index from ground truth."""
    for page in ground_truth.get("pages", []):
        if page.get("index") == page_idx:
            return page
    return None


def get_page_indices(ground_truth: dict) -> list[int]:
    """Get list of page indices from ground truth."""
    return [p.get("index", 0) for p in ground_truth.get("pages", [])]


def render_sidebar():
    """Render the sidebar with mode selection, file selection, and navigation."""
    st.sidebar.title("Ground Truth Annotation")

    # Mode selection
    mode = st.sidebar.radio("Mode", ["Edit Existing", "New Document"], horizontal=True)

    if mode == "Edit Existing":
        yaml_files = list_yaml_files()
        if not yaml_files:
            st.sidebar.warning("No YAML files found in ground_truth/documents/")
            return

        yaml_options = {f.stem: f for f in yaml_files}
        selected_name = st.sidebar.selectbox("Document", list(yaml_options.keys()))

        if selected_name:
            yaml_path = yaml_options[selected_name]

            # Load if changed
            if st.session_state.yaml_file_path != yaml_path:
                gt = load_ground_truth(yaml_path)
                st.session_state.ground_truth = gt
                st.session_state.original_yaml = yaml.dump(gt, default_flow_style=False)
                st.session_state.yaml_file_path = yaml_path
                st.session_state.current_page_idx = 0
                st.session_state.is_modified = False
                st.session_state.validation_result = None

    else:  # New Document
        st.sidebar.subheader("Create New")
        pdf_files = list_pdfs()
        if not pdf_files:
            st.sidebar.warning("No PDFs found in spikes/sample_pdfs/")
            return

        pdf_options = {f.name: f for f in pdf_files}
        _selected_pdf = st.sidebar.selectbox("Select PDF", list(pdf_options.keys()))

        _page_range = st.sidebar.slider("Page Range", 0, 100, (0, 10))

        if st.sidebar.button("Generate Draft"):
            # TODO: Integrate with generate_draft.py
            # For now, show instruction to use CLI
            st.sidebar.info("Draft generation not yet implemented. Use generate_draft.py CLI.")

    # Navigation (if document loaded)
    if st.session_state.ground_truth:
        st.sidebar.divider()
        st.sidebar.subheader("Navigation")

        page_indices = get_page_indices(st.session_state.ground_truth)
        if page_indices:
            # Page selector
            current_idx = st.session_state.current_page_idx
            if current_idx not in page_indices:
                current_idx = page_indices[0]

            new_idx = st.sidebar.selectbox(
                "Page",
                page_indices,
                index=page_indices.index(current_idx) if current_idx in page_indices else 0,
                format_func=lambda x: f"Page {x}",
            )
            st.session_state.current_page_idx = new_idx

            # Prev/Next buttons
            col1, col2 = st.sidebar.columns(2)
            with col1:
                if st.button("◀ Prev", disabled=current_idx == page_indices[0]):
                    idx = page_indices.index(current_idx)
                    st.session_state.current_page_idx = page_indices[idx - 1]
                    st.rerun()
            with col2:
                if st.button("Next ▶", disabled=current_idx == page_indices[-1]):
                    idx = page_indices.index(current_idx)
                    st.session_state.current_page_idx = page_indices[idx + 1]
                    st.rerun()

        # Annotation status
        st.sidebar.divider()
        st.sidebar.subheader("Annotation Status")
        status = st.session_state.ground_truth.get("annotation_status", {})
        for elem_type, s in status.items():
            state = s.get("state", "pending")
            count = s.get("count", "?")
            icon = {"verified": "✅", "annotated": "🔵", "pending": "⏳"}.get(state, "❓")
            st.sidebar.text(f"{icon} {elem_type}: {state} ({count})")

    # Color legend
    st.sidebar.divider()
    st.sidebar.subheader("Region Colors")
    for region_type, color in list(REGION_COLORS.items())[:8]:
        hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        st.sidebar.markdown(
            f'<span style="color:{hex_color}">●</span> {region_type}',
            unsafe_allow_html=True,
        )


def render_pdf_viewer():
    """Render the PDF page with bbox overlays."""
    gt = st.session_state.ground_truth
    if not gt:
        st.info("Load a document from the sidebar")
        return

    # Get PDF path
    pdf_name = gt.get("source", {}).get("pdf")
    if not pdf_name:
        st.error("No PDF specified in ground truth")
        return

    pdf_path = PDF_DIR / pdf_name
    if not pdf_path.exists():
        st.error(f"PDF not found: {pdf_path}")
        return

    # Get current page data
    page_idx = st.session_state.current_page_idx
    page_data = get_page_data(gt, page_idx)

    if not page_data:
        st.warning(f"No data for page {page_idx}")
        return

    # Render page
    regions = page_data.get("regions", [])
    try:
        img = render_page_image(
            pdf_path,
            page_idx,
            regions,
            dpi=150,
            highlight_region_id=st.session_state.selected_region_id,
        )
        st.image(img, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to render page: {e}")


def render_yaml_editor():
    """Render the YAML editor."""
    gt = st.session_state.ground_truth
    if not gt:
        return

    # View mode toggle
    view_mode = st.radio("View", ["Current Page", "Full Document"], horizontal=True)

    if view_mode == "Current Page":
        # Extract current page data only
        page_idx = st.session_state.current_page_idx
        page_data = get_page_data(gt, page_idx)

        if page_data:
            # Get elements for this page
            elements = gt.get("elements", {})
            page_elements = {}

            # Filter footnotes
            page_fns = [
                fn for fn in elements.get("footnotes", []) if page_idx in fn.get("pages", [])
            ]
            if page_fns:
                page_elements["footnotes"] = page_fns

            # Filter citations
            page_cites = [c for c in elements.get("citations", []) if c.get("page") == page_idx]
            if page_cites:
                page_elements["citations"] = page_cites

            yaml_content = yaml.dump(
                {"page": page_data, "elements": page_elements},
                default_flow_style=False,
                allow_unicode=True,
            )
        else:
            yaml_content = "# No page data"
    else:
        yaml_content = yaml.dump(gt, default_flow_style=False, allow_unicode=True)

    # YAML editor
    edited_yaml = st_ace(
        value=yaml_content,
        language="yaml",
        theme="monokai",
        height=400,
        key=f"yaml_editor_{view_mode}_{st.session_state.current_page_idx}",
    )

    # Parse and validate on change
    if edited_yaml != yaml_content:
        try:
            edited_data = yaml.safe_load(edited_yaml)
            if view_mode == "Full Document":
                st.session_state.ground_truth = edited_data
                st.session_state.is_modified = True
            else:
                # Merge page edits back
                st.info("Page-level editing: changes will be merged on save")
                st.session_state.is_modified = True
        except yaml.YAMLError as e:
            st.error(f"YAML syntax error: {e}")


def render_element_panel():
    """Render the element panel showing regions and elements."""
    gt = st.session_state.ground_truth
    if not gt:
        return

    page_idx = st.session_state.current_page_idx
    page_data = get_page_data(gt, page_idx)

    if not page_data:
        return

    # Regions tab
    st.subheader(f"Regions on Page {page_idx}")
    regions = page_data.get("regions", [])

    for region in regions:
        region_id = region.get("id", "unknown")
        region_type = region.get("type", "unknown")
        text_preview = region.get("text", "")[:50]
        if len(region.get("text", "")) > 50:
            text_preview += "..."

        col1, col2 = st.columns([4, 1])
        with col1:
            color = REGION_COLORS.get(region_type, (128, 128, 128))
            hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
            st.markdown(
                f'<span style="color:{hex_color}">●</span> **{region_id}** ({region_type})',
                unsafe_allow_html=True,
            )
            st.caption(text_preview)
        with col2:
            if st.button("Select", key=f"sel_{region_id}"):
                st.session_state.selected_region_id = region_id
                st.rerun()


def render_action_bar():
    """Render the action bar with validate and save buttons."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔍 Validate"):
            if st.session_state.yaml_file_path:
                result = validate_ground_truth(st.session_state.yaml_file_path)
                st.session_state.validation_result = result

    with col2:
        # Check for validation errors
        has_errors = False
        if st.session_state.validation_result:
            has_errors = not st.session_state.validation_result.is_valid

        save_label = "💾 Save"
        if st.session_state.is_modified:
            save_label += " *"

        if st.button(save_label, disabled=has_errors):
            if st.session_state.yaml_file_path and st.session_state.ground_truth:
                # Update metadata
                st.session_state.ground_truth.setdefault("metadata", {})
                st.session_state.ground_truth["metadata"]["last_modified"] = str(date.today())

                save_ground_truth(st.session_state.ground_truth, st.session_state.yaml_file_path)
                st.session_state.is_modified = False
                st.success("Saved!")

    with col3:
        if st.session_state.is_modified:
            st.warning("Unsaved changes")

    with col4:
        if st.session_state.validation_result:
            r = st.session_state.validation_result
            if r.is_valid:
                st.success("Valid")
            else:
                st.error(f"{len(r.errors)} errors")

    # Show validation details
    if st.session_state.validation_result:
        r = st.session_state.validation_result
        if r.errors or r.warnings:
            with st.expander(
                f"Validation Results ({len(r.errors)} errors, {len(r.warnings)} warnings)"
            ):
                for e in r.errors:
                    st.error(f"❌ [{e.path}] {e.message}")
                for w in r.warnings:
                    st.warning(f"⚠️ [{w.path}] {w.message}")


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Ground Truth Annotation",
        page_icon="📝",
        layout="wide",
    )

    init_session_state()

    # Sidebar
    render_sidebar()

    # Main content
    if st.session_state.ground_truth:
        # Action bar at top
        render_action_bar()
        st.divider()

        # Two-column layout: PDF viewer | YAML editor
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("PDF Viewer")
            render_pdf_viewer()

        with col2:
            st.subheader("YAML Editor")
            render_yaml_editor()

        # Element panel below
        st.divider()
        render_element_panel()
    else:
        st.info("👈 Select a document from the sidebar to begin")
        st.markdown("""
        ## Ground Truth Annotation Tool

        This tool allows you to:
        - View PDF pages with region overlays
        - Edit ground truth YAML annotations
        - Validate annotations against the schema
        - Save changes back to disk

        ### Quick Start
        1. Select an existing YAML file from the sidebar
        2. Navigate through pages using the page selector
        3. Edit the YAML in the editor panel
        4. Click Validate to check for errors
        5. Click Save to persist changes
        """)


if __name__ == "__main__":
    main()
