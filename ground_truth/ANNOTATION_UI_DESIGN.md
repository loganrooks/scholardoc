# Annotation UI Design

**Version**: 1.1.0
**Created**: 2026-01-07
**Updated**: 2026-01-07
**Status**: Planning

## Overview

Streamlit-based annotation UI for creating and correcting ground truth YAML files. Single annotator workflow with live editing and validation.

## Quick Start

```bash
# Launch the annotation UI
cd ground_truth
streamlit run scripts/annotate_ui.py

# Or from project root
uv run streamlit run ground_truth/scripts/annotate_ui.py
```

## Requirements

### Confirmed Decisions
- Single annotator (not multi-user)
- All element types supported (footnotes, citations, marginal refs, sous_rature, etc.)
- Extraction config tunable in UI
- Basic bbox adjustment + live edit capability
- Validation before save

## File Paths

```
spikes/sample_pdfs/           # Source PDFs
ground_truth/documents/       # Output YAML files (one per document)
ground_truth/index.yaml       # Document index (auto-updated on save)
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Streamlit App                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌─────────────────────────────────────────────┐  │
│  │   Sidebar    │  │              Main Area                      │  │
│  │              │  │                                             │  │
│  │ - PDF select │  │  ┌─────────────────┐  ┌──────────────────┐  │  │
│  │ - Page nav   │  │  │   PDF Viewer    │  │  YAML Editor     │  │  │
│  │ - Extraction │  │  │   + BBoxes      │  │  (Live Edit)     │  │  │
│  │   Config     │  │  │                 │  │                  │  │  │
│  │ - Element    │  │  │  [Rendered      │  │  schema_version: │  │  │
│  │   Filter     │  │  │   page with     │  │  source:         │  │  │
│  │              │  │  │   overlays]     │  │    pdf: ...      │  │  │
│  │              │  │  │                 │  │                  │  │  │
│  └──────────────┘  │  └─────────────────┘  └──────────────────┘  │  │
│                    │                                             │  │
│                    │  ┌─────────────────────────────────────────┐  │
│                    │  │         Element Panel                    │  │
│                    │  │  - List of elements on current page     │  │
│                    │  │  - Click to highlight in viewer         │  │
│                    │  │  - Edit/Delete buttons                  │  │
│                    │  └─────────────────────────────────────────┘  │
│                    └─────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  [Validate] [Save] [Re-extract Page] [Undo]    Status: 2 warnings  │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Sidebar

#### Mode Selection (Top)
```python
mode = st.radio("Mode", ["New Document", "Edit Existing"], horizontal=True)

if mode == "New Document":
    pdf_file = st.selectbox("PDF", list_pdfs("spikes/sample_pdfs/"))
    page_range = st.slider("Page Range", 0, total_pages, (0, min(20, total_pages)))
    if st.button("Generate Draft"):
        ground_truth = generate_draft(pdf_file, page_range)
        st.session_state.ground_truth = ground_truth
        st.session_state.is_modified = False
else:  # Edit Existing
    yaml_files = list_yamls("ground_truth/documents/")
    yaml_file = st.selectbox("Document", yaml_files)
    if yaml_file:
        ground_truth = load_ground_truth(yaml_file)
        pdf_file = ground_truth['source']['pdf']  # Auto-resolve
        st.session_state.ground_truth = ground_truth
```

#### Page Navigation
```python
current_page = st.number_input("Page", min=0, max=len(pages))
col1, col2 = st.columns(2)
with col1:
    st.button("◀ Prev", on_click=lambda: prev_page())
with col2:
    st.button("Next ▶", on_click=lambda: next_page())
```

#### Annotation Status (per element type)
```python
st.subheader("Status")
for elem_type in ["footnotes", "citations", "marginal_refs", "sous_rature"]:
    status = ground_truth['annotation_status'][elem_type]['state']
    new_status = st.selectbox(
        elem_type,
        ["pending", "annotated", "verified"],
        index=["pending", "annotated", "verified"].index(status),
        key=f"status_{elem_type}"
    )
```

#### Extraction Config
```python
st.subheader("Extraction Settings")
dpi = st.slider("DPI", 72, 300, 150)
extraction_method = st.selectbox("Method", ["pymupdf", "docling", "hybrid"])
with st.expander("Advanced"):
    ocr_enabled = st.checkbox("Enable OCR", True)
    spell_threshold = st.slider("Spell Score Threshold", 0.0, 1.0, 0.8)
    confidence_display = st.checkbox("Show Confidence", True)
```

#### Element Filter
```python
show_regions = st.multiselect("Show Regions", REGION_TYPES, default=all)
show_elements = st.multiselect("Show Elements", ELEMENT_TYPES, default=all)
```

### 2. PDF Viewer (Left Main Panel)

Uses existing `visualize.py` rendering logic:
- Renders page at configured DPI
- Overlays colored bboxes for regions
- Highlights selected element
- Shows element markers (footnote numbers, etc.)

**Interaction**:
- Click region → select in Element Panel
- Shift+drag → create new region (future)
- (Future: drag corners to resize bbox)

Implementation approach:
```python
# Render page image with overlays
img = render_page_with_annotations(pdf, page_idx, ground_truth, dpi)
st.image(img, use_column_width=True)

# Or use streamlit-drawable-canvas for bbox editing
from streamlit_drawable_canvas import st_canvas
canvas_result = st_canvas(
    background_image=img,
    drawing_mode="rect",
    ...
)
```

### 3. YAML Editor (Right Main Panel)

Live YAML editing with syntax highlighting:

```python
import streamlit_ace

# For large documents, show only current page section
view_mode = st.radio("View", ["Current Page", "Full Document"], horizontal=True)

if view_mode == "Current Page":
    # Extract just the current page's data for editing
    page_data = ground_truth['pages'][current_page]
    page_elements = get_elements_for_page(ground_truth, current_page)
    editable_section = {"page": page_data, "elements": page_elements}
    yaml_content = yaml.dump(editable_section, default_flow_style=False)
else:
    yaml_content = yaml.dump(ground_truth, default_flow_style=False)

edited_yaml = streamlit_ace.st_ace(
    value=yaml_content,
    language="yaml",
    theme="monokai",
    height=500,
    key="yaml_editor"
)

# Parse and validate on change
try:
    edited_data = yaml.safe_load(edited_yaml)
    if view_mode == "Current Page":
        # Merge back into full document
        ground_truth = merge_page_edits(ground_truth, current_page, edited_data)
    else:
        ground_truth = edited_data

    errors = validate_schema(ground_truth)
    st.session_state.is_modified = True
except yaml.YAMLError as e:
    st.error(f"YAML syntax error: {e}")
```

**Sync Strategy**:
- YAML editor is source of truth
- Changes trigger re-render of PDF viewer
- Element Panel syncs from YAML state
- **Current Page view** recommended for large documents (reduces cognitive load)

### 4. Element Panel (Bottom)

List view of elements on current page:

```python
st.subheader(f"Elements on Page {current_page}")

tabs = st.tabs(["Regions", "Footnotes", "Citations", "Marginal", "Sous Rature"])

with tabs[0]:  # Regions
    for region in page_regions:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.text(f"{region['id']}: {region['type']}")
        with col2:
            if st.button("Edit", key=f"edit_{region['id']}"):
                select_region(region['id'])
        with col3:
            if st.button("Del", key=f"del_{region['id']}"):
                delete_region(region['id'])

with tabs[1]:  # Footnotes
    for fn in page_footnotes:
        with st.expander(f"fn_{fn['id']}: {fn['marker']['text']}"):
            st.text_area("Content", fn['content'][0]['text'])
            st.selectbox("Note Type", ["author", "translator", "editor"])
```

### 5. Action Bar (Bottom)

```python
# Show validation errors/warnings in dedicated area
if st.session_state.validation_errors:
    with st.expander(f"⚠️ {len(st.session_state.validation_errors)} issues", expanded=True):
        for err in st.session_state.validation_errors:
            icon = "❌" if err.level == "error" else "⚠️"
            st.markdown(f"{icon} **{err.path}**: {err.message}")
            if err.suggestion:
                st.caption(f"   → {err.suggestion}")

# Action buttons - Phase-appropriate (MVP shows only core actions)
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🔍 Validate"):
        errors = validate_ground_truth(ground_truth)
        st.session_state.validation_errors = errors

with col2:
    has_errors = any(e.level == "error" for e in st.session_state.validation_errors)
    save_label = "💾 Save" + (" *" if st.session_state.is_modified else "")
    if st.button(save_label, disabled=has_errors):
        save_ground_truth(ground_truth, output_path)
        update_index(ground_truth)
        st.session_state.is_modified = False
        st.success("Saved!")

with col3:
    # Phase 2+: Undo button
    undo_disabled = len(st.session_state.undo_stack) == 0
    if st.button("↩️ Undo", disabled=undo_disabled):
        ground_truth = st.session_state.undo_stack.pop()

with col4:
    # Status indicator
    if st.session_state.is_modified:
        st.warning("Unsaved changes")
    else:
        st.success("Saved")
```

### 6. Unsaved Changes Guard

```python
# At app start, warn about unsaved changes from previous session
if st.session_state.get('is_modified', False):
    st.warning("⚠️ You have unsaved changes from a previous session")

# Use browser beforeunload via streamlit-js-eval (optional enhancement)
# For MVP: rely on visual indicator + explicit save button
```

## State Management

```python
# Session state structure
def init_session_state():
    defaults = {
        'ground_truth': None,           # Current document data
        'original_ground_truth': None,  # For detecting changes
        'undo_stack': [],               # For undo functionality (Phase 2+)
        'current_page': 0,              # Current page index
        'selected_element': None,       # Selected element ID for highlighting
        'extraction_config': DEFAULT_CONFIG,
        'validation_errors': [],        # List of ValidationError
        'is_modified': False,           # Unsaved changes flag
        'mode': 'edit',                 # 'new' or 'edit'
        'yaml_file_path': None,         # Path to current YAML file
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

# Track modifications
def mark_modified():
    st.session_state.is_modified = True
    # Push to undo stack (Phase 2+)
    if len(st.session_state.undo_stack) < 50:  # Limit stack size
        st.session_state.undo_stack.append(
            copy.deepcopy(st.session_state.ground_truth)
        )
```

## Workflows

### New Document Workflow
1. Select PDF → Enter page range
2. Configure extraction settings
3. Click "Generate Draft" → Runs `generate_draft.py`
4. Review auto-generated annotations
5. Correct errors via YAML editor or Element Panel
6. Validate → Save

### Existing Document Workflow
1. Select existing YAML file
2. PDF auto-loads from `source.pdf`
3. Navigate pages, review annotations
4. Make corrections as needed
5. Validate → Save

### Page Re-extraction Workflow
1. Adjust extraction config (DPI, method)
2. Click "Re-extract Page"
3. Modal shows diff: "5 new regions, 2 modified"
4. Select which to accept
5. Merged into current YAML

## File Structure

```
ground_truth/
├── scripts/
│   ├── generate_draft.py      # Existing
│   ├── visualize.py           # Existing - refactor for reuse
│   ├── validate.py            # Existing
│   └── annotate_ui.py         # NEW - Streamlit app
```

## Dependencies

```toml
# pyproject.toml additions
streamlit = "^1.30"
streamlit-ace = "^0.1"           # YAML editor with syntax highlighting
streamlit-drawable-canvas = "*"  # BBox drawing (optional, phase 2)
```

## Implementation Phases

### Phase 1: Core UI (MVP)
Core viewing and YAML-based editing:
- [ ] App skeleton with sidebar + main layout
- [ ] Mode selection (New Document / Edit Existing)
- [ ] PDF viewer with bbox overlays (refactor from visualize.py)
- [ ] YAML editor with syntax highlighting (streamlit-ace)
- [ ] Current Page / Full Document view toggle
- [ ] Page navigation (prev/next)
- [ ] Validate button + error display
- [ ] Save button with unsaved changes indicator
- [ ] Element list (read-only, grouped by type)
- [ ] Annotation status selectors per element type

**Not in MVP**: Undo button disabled, Re-extract hidden, bbox drag/resize

### Phase 2: Editing Enhancements
Interactive element editing:
- [ ] Undo/redo stack (enable button)
- [ ] Edit elements via Element Panel forms
- [ ] Add new element (with auto-generated ID)
- [ ] Delete element with confirmation
- [ ] Element type tabs in panel

### Phase 3: Extraction Integration
Re-run pipeline from UI:
- [ ] Extraction config in sidebar (DPI, method, OCR toggle)
- [ ] Re-extract Page button
- [ ] Diff view: show what changed
- [ ] Selective merge: accept/reject individual changes

### Phase 4: Advanced Features
Power user features:
- [ ] Drawable canvas for bbox adjustment (streamlit-drawable-canvas)
- [ ] Keyboard shortcuts (j/k navigation, s to save)
- [ ] Annotation statistics dashboard
- [ ] Export to other formats (JSON, CSV summary)
- [ ] Session recovery (auto-save draft)

## Open Questions

1. **BBox editing**: Use streamlit-drawable-canvas or defer to YAML editor?
   - Recommendation: Start with YAML-only editing, add canvas in Phase 4

2. **Element ID generation**: Auto-generate or manual?
   - Recommendation: Auto-generate based on type + counter, allow override

3. **Multi-page element editing**: How to handle footnotes spanning pages?
   - Recommendation: Edit full element in YAML, highlight all pages it spans

## Design Notes

### Reusing visualize.py

The existing `render_page_with_annotations()` function should be refactored:
1. Extract rendering logic into reusable function
2. Return PIL Image instead of saving HTML
3. Add highlight parameter for selected element

```python
# visualize.py (refactored)
def render_page_image(
    pdf_path: Path,
    page_idx: int,
    regions: list[dict],
    dpi: int = 150,
    highlight_region_id: str | None = None
) -> Image:
    """Render page with bbox overlays, return PIL Image."""
    ...
```

### Validation Integration

Reuse `validate.py` but return structured errors:
```python
@dataclass
class ValidationError:
    level: Literal["error", "warning"]
    path: str  # JSON path, e.g., "pages[0].regions[2].bbox"
    message: str
    suggestion: str | None = None
```

### Performance

- Cache PDF page renders: `@st.cache_resource`
- Lazy load elements for large documents
- Debounce YAML parsing on edit

### BBox Color Scheme

Consistent colors for region types (reuse from visualize.py):

```python
REGION_COLORS = {
    "header": "#3498db",       # Blue
    "footer": "#3498db",       # Blue
    "body": "#2ecc71",         # Green
    "footnote_region": "#e74c3c",      # Red
    "footnote_continuation": "#c0392b", # Dark red
    "margin": "#9b59b6",       # Purple
    "page_number": "#f39c12",  # Orange
    "figure": "#1abc9c",       # Teal
    "caption": "#16a085",      # Dark teal
    "table": "#e67e22",        # Dark orange
    "block_quote": "#95a5a6",  # Gray
    "heading": "#2c3e50",      # Dark blue
}

# Selected element: add dashed border or glow effect
HIGHLIGHT_STYLE = "stroke-dasharray: 5,5; stroke-width: 3px;"
```

### Zoom Controls

```python
# In sidebar, under page navigation
zoom_level = st.slider("Zoom", 50, 200, 100, step=25, format="%d%%")
dpi = int(150 * zoom_level / 100)  # Base DPI of 150
```
