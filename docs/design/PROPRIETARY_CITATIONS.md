# Proprietary Citation Systems Design

> **Status:** DRAFT - Needs planning approval
> **Phase:** Phase 2.4 (Citation Detection) - requires dedicated design
> **Author:** Planning session 2026-01-06
> **Problem:** Current roadmap mentions "Multiple styles (Chicago, MLA)" but doesn't address proprietary scholarly citation systems

---

## Problem Statement

Scholarly editions of classical and modern philosophy texts use **proprietary reference systems** that appear in the margins or inline. These are fundamentally different from standard citation styles:

| System | Works | Format | Location | Example |
|--------|-------|--------|----------|---------|
| **Stephanus** | Plato | number + letter | Margin | "514a", "Republic 514a-b" |
| **Bekker** | Aristotle | number + letter + line | Margin | "1003a15", "Met. 1003a" |
| **Akademie (Ak.)** | Kant | volume:page | Inline/Margin | "Ak. 167", "Ak. IV:421" |
| **A/B** | Kant CPR | letter + number | Margin | "A23", "B47", "A23/B47" |
| **Heidegger** | Sein und Zeit | H. + page | Margin | "H. 42" |

### Why This Matters

1. **Scholarly citation standards**: Proper citations to Plato, Aristotle, Kant require these reference numbers
2. **RAG applications**: Need to extract and index these for retrieval
3. **Citation linking**: In-text references like "see 514a" need to link to marginal markers
4. **Anki generation**: Flashcards need proper source citations

### Current Gap

- Schema v4 has `citation_type` enum with `stephanus`, `bekker`, `ak_reference`
- No implementation plan for detecting marginal markers
- No registry of known works and their citation systems
- No layout analysis for margin detection
- ROADMAP Phase 2.4 only mentions "Chicago, MLA" styles

---

## Research Questions

### Q1: Where do proprietary citations appear?

| Location | % of Cases | Detection Difficulty | Examples |
|----------|------------|---------------------|----------|
| **Margin (outer)** | ~70% | Medium - layout analysis | Stephanus, Bekker, A/B |
| **Margin (inner)** | ~15% | Medium - layout analysis | Some Kant editions |
| **Inline bracketed** | ~10% | Easy - regex | "(Ak. 167)", "[H. 42]" |
| **Running header** | ~5% | Easy - position | Page-level markers |

**Answer needed**: Examine our sample PDFs to verify these percentages.

### Q2: Are there cases where proprietary citations are NOT in margins?

Yes:
- Inline parenthetical: "(see Ak. 167)" - common in modern editions
- Footnote apparatus: Notes citing specific passages
- Bibliography entries: "Kant, Critique of Pure Reason, A23/B47"
- Running headers: Section markers

**Implication**: Can't rely solely on margin detection.

### Q3: Can we identify the citation system from document metadata?

**Approach 1: Registry matching**
```python
CITATION_REGISTRY = {
    "Plato": {"system": "stephanus", "pattern": r"\d+[a-e]"},
    "Aristotle": {"system": "bekker", "pattern": r"\d{3,4}[ab]\d*"},
    "Kant": {
        "Critique of Pure Reason": {"system": "ab_pagination", "pattern": r"[AB]\d+"},
        "default": {"system": "akademie", "pattern": r"Ak\.?\s*\d+"}
    },
    "Heidegger": {
        "Being and Time": {"system": "marginal_h", "pattern": r"H\.?\s*\d+"}
    }
}
```

**Approach 2: Heuristic detection**
- Detect margin text regions
- Apply pattern matching to margin content
- Infer system from patterns found

**Recommendation**: Hybrid - use registry when author/title match, fallback to heuristic.

### Q4: What about unknown works with proprietary systems?

Philosophy dissertations, commentaries, and translations sometimes create their own marginal reference systems. Need a **default marginal marker detector** that:
1. Identifies margin regions (spatial analysis)
2. Extracts text from margins
3. Detects reference-like patterns (numbers, letters, abbreviations)
4. Flags as "unknown_proprietary" for manual classification

---

## Detection Strategy Options

### Option A: Layout Segmentation First (GPU-accelerated)

```
Page Image → Layout Model (YOLO/LayoutLM) → Regions → Text Extraction → Pattern Matching
```

**Pros:**
- Robust margin detection
- Works on any document layout
- Can detect unknown systems

**Cons:**
- Requires GPU for reasonable speed
- Additional dependency (PyTorch, etc.)
- Overkill for born-digital PDFs

### Option B: PyMuPDF Block Analysis (CPU)

```
PDF → PyMuPDF blocks → Position analysis → Margin detection → Pattern matching
```

**Pros:**
- No additional dependencies
- Fast on born-digital PDFs
- Leverages existing infrastructure

**Cons:**
- May miss margins in scanned PDFs
- Depends on block boundary accuracy

### Option C: Hybrid (Recommended)

```
1. Check registry for author/title match
2. If match: Apply known pattern to entire page text + margin regions
3. If no match:
   a. Born-digital: Use PyMuPDF block analysis for margins
   b. Scanned: Fall back to layout model (if available)
4. Pattern matching on detected margins
5. Link inline references to marginal markers
```

**Performance profile:**
- Registry lookup: O(1) - instant
- PyMuPDF block analysis: ~10ms/page
- Layout model: ~100-500ms/page (GPU), ~2-5s/page (CPU)

---

## Proposed Architecture

### Component 1: Citation Registry

```python
@dataclass
class CitationSystem:
    """Definition of a proprietary citation system."""
    name: str  # "stephanus", "bekker", "akademie", "ab_pagination"
    pattern: str  # Regex pattern
    location: Literal["margin", "inline", "both"]
    format_description: str
    example: str

@dataclass
class WorkCitationConfig:
    """Citation configuration for a specific work."""
    author: str
    title_pattern: str  # Regex to match title variations
    system: CitationSystem
    volume_format: str | None  # For multi-volume works

# Registry populated from YAML/JSON config
CITATION_REGISTRY: dict[str, list[WorkCitationConfig]]
```

### Component 2: Margin Detector

```python
class MarginDetector(Protocol):
    """Abstract interface for margin detection."""

    def detect_margins(self, page: RawPage) -> list[MarginRegion]:
        """Detect margin regions on a page."""
        ...

@dataclass
class MarginRegion:
    bbox: tuple[float, float, float, float]
    side: Literal["left", "right", "top", "bottom"]
    text: str
    confidence: float

# Implementations
class PyMuPDFMarginDetector(MarginDetector):
    """CPU-based margin detection using block positions."""

class LayoutModelMarginDetector(MarginDetector):
    """GPU-accelerated margin detection using YOLO/LayoutLM."""
```

### Component 3: Citation Extractor

```python
class ProprietaryCitationExtractor:
    """Extract proprietary citations from documents."""

    def __init__(
        self,
        registry: CitationRegistry,
        margin_detector: MarginDetector,
        fallback_to_heuristic: bool = True,
    ):
        ...

    def extract(self, doc: RawDocument) -> list[ProprietaryCitation]:
        """Extract all proprietary citations from document."""
        # 1. Identify citation system from metadata
        system = self._identify_system(doc.metadata)

        # 2. Detect margins on each page
        for page in doc.pages:
            margins = self.margin_detector.detect_margins(page)

            # 3. Extract citations from margins
            for region in margins:
                citations = self._extract_from_region(region, system)

            # 4. Also check inline text if system allows
            if system.location in ("inline", "both"):
                inline_citations = self._extract_inline(page, system)

        # 5. Link inline references to marginal markers
        self._link_references(citations)

        return citations

@dataclass
class ProprietaryCitation:
    """A detected proprietary citation."""
    system: str  # "stephanus", "bekker", etc.
    reference: str  # "514a", "Ak. 167"
    parsed: dict  # {"section": 514, "subsection": "a"}
    page_index: int
    location: Literal["margin", "inline"]
    bbox: tuple[float, float, float, float] | None
    confidence: float
```

---

## Performance Considerations

### Budget

For a 500-page philosophy book:
- **Target**: < 30 seconds total for citation extraction
- **Per-page budget**: ~60ms

### Parallelization Opportunities

| Component | Parallelizable | Method |
|-----------|---------------|--------|
| Page margin detection | ✅ Yes | multiprocessing.Pool |
| Pattern matching | ✅ Yes | Per-page parallel |
| Layout model inference | ✅ Yes (batch) | GPU batching |
| Reference linking | ❌ No | Sequential (needs all pages) |

### GPU Acceleration

**YOLO for layout detection:**
- YOLOv8/v9 nano models: ~5-10ms/image on GPU
- Can batch multiple pages
- Pre-trained on document layouts available

**LayoutLM/DiT:**
- More accurate but slower
- ~50-100ms/page on GPU
- Better for complex layouts

**Recommendation**:
- Default: CPU-based PyMuPDF analysis (good enough for 90% of cases)
- Optional: GPU layout model for scanned documents or complex layouts
- Make GPU acceleration opt-in via config

---

## Ground Truth Requirements

### New test cases needed:

| Test Case | Document | Pages | Features |
|-----------|----------|-------|----------|
| Stephanus margins | Plato Republic | TBD | Margin numbers |
| Bekker margins | Aristotle | TBD | Margin + line numbers |
| Ak. inline | Kant Critique of Judgement | Various | Inline Ak. references |
| A/B margins | Kant CPR | Need sample | Dual pagination |
| H. margins | Heidegger B&T | 21-30 | H. page markers |
| Inline references | Various | Various | "see 514a" patterns |
| No margins (negative) | Modern commentary | Various | No proprietary system |

### Labels needed per page:

```json
{
  "page_index": 42,
  "has_marginal_citations": true,
  "marginal_citations": [
    {
      "system": "akademie",
      "reference": "167",
      "bbox": [50, 100, 70, 120],
      "side": "left"
    }
  ],
  "inline_citations": [
    {
      "system": "akademie",
      "reference": "Ak. 167",
      "position": 1234,
      "context": "As Kant argues (Ak. 167)..."
    }
  ]
}
```

---

## Open Questions for User

1. **Sample PDFs**: Do we have any Plato or Aristotle PDFs with Stephanus/Bekker margins? If not, should we acquire them?

2. **Kant CPR**: Do we have a Critique of Pure Reason PDF with A/B pagination in margins?

3. **GPU requirement**: Is it acceptable to make GPU acceleration optional? Or must CPU-only be sufficient?

4. **Registry scope**: Should we build a comprehensive registry of all philosophical works with proprietary systems, or start with just the ones in our test corpus?

5. **Priority**: Should this be part of Phase 2.4 (Citation Detection) or split into its own phase?

6. **Multi-page footnotes**: You mentioned needing more examples - should we prioritize finding those over proprietary citation work?

---

## Recommended Next Steps

1. **Spike exploration**: Run spike on sample PDFs to identify which have marginal markers
2. **Sample acquisition**: Get Plato/Aristotle/Kant CPR samples if needed
3. **Prototype**: Build simple PyMuPDF-based margin detector
4. **Ground truth**: Create test cases for margin detection
5. **Registry**: Build initial registry for works in test corpus
6. **Evaluate GPU options**: If CPU performance insufficient, evaluate YOLO integration

---

## Decision Needed

Before proceeding with implementation, please review and decide:

1. **Scope**: Include in Phase 2.4 or separate phase?
2. **GPU**: Required or optional?
3. **Registry vs Heuristic**: How much effort on registry?
4. **Samples**: What PDFs to acquire?
