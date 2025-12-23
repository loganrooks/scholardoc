# Sous-Erasure (Under Erasure) Detection Design

**Status**: Design Draft
**Created**: 2024-12-18
**Related**: OCR correction pipeline, formatting preservation

## Overview

"Sous rature" (under erasure) is a typographical convention from Continental philosophy where words are printed with an X through them, indicating the word is necessary but inadequate. This is common in:
- Heidegger translations (Being, presence, truth crossed out)
- Derrida's deconstructive texts (is, meaning, origin crossed out)

Unlike strikethrough (horizontal line), sous-erasure uses two diagonal crossing lines forming an X over the text.

## Problem Statement

Current PDF extraction libraries:
1. **Ignore visual overlays**: Text layer extraction misses X-mark annotations
2. **Corrupt the text**: OCR may misread X-marks as characters
3. **Lose semantic meaning**: The philosophical significance is lost

For scholarly RAG pipelines, preserving sous-erasure is critical for:
- Accurate philosophical text retrieval
- Maintaining author's intended meaning
- Proper citation and quotation

## Technical Analysis

### How X-Marks Appear in PDFs

Based on analysis of `zlibrary-mcp`'s implementation:

1. **Vector drawings**: X-marks are often PDF path objects (lines) overlaying text
2. **Image-based**: In scanned PDFs, X-marks are part of the raster image
3. **Font glyphs**: Rare - some fonts include crossed-out characters

### Detection Approaches

#### Approach A: OpenCV Line Segment Detection (zlibrary-mcp method)

```
Render page → Detect lines (LSD) → Filter diagonals → Find crossing pairs → Map to text
```

**Pros**:
- Works on both scanned and digital PDFs
- High accuracy when tuned properly
- Can detect partial/faint X-marks

**Cons**:
- Requires image rendering (slow)
- May have false positives (decorative elements)
- Needs ground truth calibration

**Implementation details from zlibrary-mcp**:
```python
# Line detection using OpenCV's Line Segment Detector
lsd = cv2.createLineSegmentDetector(0)
lines = lsd.detect(gray_image)[0]

# Filter for diagonal lines (30-60° and -60 to -30°)
# Find crossing pairs within max_distance threshold
# Calculate confidence based on:
#   - Center proximity
#   - Length similarity
#   - Angle perpendicularity (ideal: 90°)
```

#### Approach B: PDF Path Analysis (digital PDFs only)

```
Parse PDF structure → Find path objects → Identify X-pattern lines → Map to underlying text
```

**Pros**:
- Fast (no rendering)
- Precise positioning
- Works well for digital-origin PDFs

**Cons**:
- Doesn't work for scanned PDFs
- PDF structure varies by creator
- May miss image-embedded X-marks

#### Approach C: Hybrid Detection

1. First pass: PDF path analysis (fast check for digital X-marks)
2. If inconclusive or scanned PDF: Fall back to CV-based detection
3. Use text-layer hints (common sous-erasure terms) to focus detection

## Recommended Integration

### Phase 1: Metadata Flagging (Minimal Effort)

Add detection hints without full implementation:

```python
@dataclass
class ExtractionResult:
    text: str
    page_num: int
    # New field
    potential_sous_erasure: list[str] = field(default_factory=list)
```

When extracting text containing known sous-erasure terms, flag for manual review:
- "Being" in Heidegger contexts
- "presence", "trace", "origin" in Derrida contexts

### Phase 2: Visual Detection (Optional Module)

Create `scholardoc.detectors.sous_erasure` module:

```python
class SousErasureDetector:
    """Detect sous-erasure (X-marked) text in PDF pages."""

    def __init__(self, method: Literal["cv", "paths", "hybrid"] = "hybrid"):
        self.method = method

    def detect_page(self, page: fitz.Page, dpi: int = 150) -> list[SousErasureMarking]:
        """Detect X-marks on a page and map to underlying text."""
        ...

    def detect_document(self, doc: fitz.Document) -> dict[int, list[SousErasureMarking]]:
        """Detect X-marks across all pages."""
        ...

@dataclass
class SousErasureMarking:
    """A detected sous-erasure marking."""
    page_num: int
    text: str  # The word under erasure
    bbox: tuple[float, float, float, float]
    confidence: float
    detection_method: str
```

### Phase 3: Output Formatting

Output sous-erasure in Markdown using extended strikethrough or custom syntax:

**Option A**: Standard Strikethrough (Limited)
```markdown
~~Being~~ is always already withdrawn.
```

**Option B**: Custom Marker (Preserves Distinction)
```markdown
<sous-erasure>Being</sous-erasure> is always already withdrawn.
```

**Option C**: Unicode Combining (Experimental)
```markdown
B̶e̶i̶n̶g̶ is always already withdrawn.  # Uses combining strikethrough
```

**Recommendation**: Use Option B (custom HTML-like tags) for scholarly accuracy, with fallback to Option A for standard Markdown compatibility.

## Dependencies

For CV-based detection:
```toml
[project.optional-dependencies]
sous_erasure = [
    "opencv-python-headless>=4.8.0",  # ~50MB, no GUI
]
```

## Ground Truth Validation

Following zlibrary-mcp's approach, create ground truth files:

```json
{
  "test_name": "heidegger_being_and_time",
  "pdf_file": "test_files/heidegger_sample.pdf",
  "features": {
    "xmarks": [
      {
        "page": 79,
        "word_under_erasure": "Being",
        "bbox": [91.68, 138.93, 379.99, 150.0],
        "expected_output": "<sous-erasure>Being</sous-erasure>",
        "expected_recovery": "Being"
      }
    ]
  }
}
```

## Integration Points

### With OCR Correction

Sous-erasure detection should run **before** OCR correction:
1. Detect X-marks and extract underlying text
2. Mark these regions as "protected" from correction
3. Output with appropriate formatting

### With Normalizer Pipeline

```python
class SousErasureNormalizer:
    """Normalize sous-erasure markings in extracted text."""

    def __init__(self, output_format: str = "html_tag"):
        self.output_format = output_format

    def normalize(self, text: str, markings: list[SousErasureMarking]) -> str:
        """Apply sous-erasure formatting to text."""
        ...
```

## Performance Considerations

| Method | Speed | Accuracy | Scanned PDFs |
|--------|-------|----------|--------------|
| Path analysis | Fast (~10ms/page) | High (digital) | No |
| CV detection | Slow (~200ms/page) | Medium | Yes |
| Hybrid | Medium | High | Yes |

For batch processing, consider:
- Lazy detection (only when flagged terms present)
- Page-level caching of detection results
- Parallel processing across pages

## Open Questions

1. **Strikethrough vs X-mark**: How to distinguish regular strikethrough from philosophical sous-erasure?
   - Context: Strikethrough is usually editorial deletion; X-mark is philosophical technique
   - Solution: Angle detection (X = diagonal, strikethrough = horizontal)

2. **Partial X-marks**: What if only one diagonal line is visible?
   - Some older printings may have degraded X-marks
   - May need lower confidence threshold with term-based validation

3. **Multiple X-marks**: Can a phrase be under erasure, not just a word?
   - Example: "the meaning of" might be crossed out together
   - Need bounding box merging logic

## References

- zlibrary-mcp implementation: `scripts/validation/xmark_detector.py`
- Ground truth format: `test_files/ground_truth/`
- OpenCV LSD documentation
- Derrida, J. (1967). "Of Grammatology" - Original sous-erasure examples
- Heidegger, M. (1927). "Being and Time" - Sein under erasure in translations
