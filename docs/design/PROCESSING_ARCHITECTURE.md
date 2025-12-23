# ScholarDoc Processing Architecture

> **Status:** Proposal (informed by Spikes 1-13)
> **Created:** December 19, 2025
> **Context:** Comprehensive design for efficient, quality-preserving PDF processing

## The Core Insight

Based on spike findings:
1. **docTR re-OCR outperforms existing OCR** for scans (Spike 10)
2. **Page numbers devastate embeddings** (29% drop) - remove from text, keep as metadata (Spike 11)
3. **Spell-check is too risky** (41% damage rate) - don't auto-correct scholarly terms (Spike 13)
4. **Embeddings are robust** to hyphenation and mid-word caps (Spike 8/9)

**Conclusion:** Use quality-based hybrid OCR, remove artifacts, don't spell-correct.

---

## Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PDF INPUT                                     │
│   (book, article, selection, scan, born-digital)                    │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 1: DOCUMENT ANALYSIS                                         │
│  ─────────────────────────────                                      │
│  • Detect document type (born-digital vs scan)                      │
│  • Extract PDF metadata (title, author, page labels)                │
│  • Identify structure (ToC, front matter, body, back matter)        │
│  • Quality-score each page (entropy, symbol density, word validity) │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 2: TEXT EXTRACTION (Hybrid OCR Strategy)                     │
│  ───────────────────────────────────────────────                    │
│  For each page:                                                     │
│    IF quality_score >= threshold (0.7):                             │
│       → Use existing text layer (fast, preserves formatting)        │
│    ELSE:                                                            │
│       → Use docTR re-OCR (GPU, ~0.6s/page, higher accuracy)         │
│                                                                     │
│  Output: Raw text + bounding boxes + font info per page             │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 3: STRUCTURE DETECTION                                       │
│  ────────────────────────────                                       │
│  • Headings (font size, bold, isolation)                            │
│  • Paragraphs (text blocks)                                         │
│  • Footnotes/Endnotes (position, superscript markers)               │
│  • Block quotes (indentation)                                       │
│  • Lists (bullet patterns)                                          │
│  • Tables (grid detection)                                          │
│  • Special: sous-erasure (visual X detection)                       │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 4: ARTIFACT REMOVAL (Keep as Metadata)                       │
│  ─────────────────────────────────────────────                      │
│  • Page numbers → page_label metadata                               │
│  • Running headers → section metadata                               │
│  • Footnote markers → footnote_refs list                            │
│  • Hyphenation → rejoin words (safe, embeddings robust)             │
│                                                                     │
│  NO spell-check correction (too risky for specialized vocabulary)   │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 5: OUTPUT GENERATION                                         │
│  ──────────────────────────                                         │
│  ScholarDocument:                                                   │
│    • elements: list[Element] (paragraphs, headings, footnotes)      │
│    • pages: list[Page] (page-level grouping)                        │
│    • metadata: DocumentMetadata (title, author, type)               │
│    • structure: TableOfContents                                     │
│    • front_matter: FrontMatter (preface, acknowledgments, etc.)     │
│                                                                     │
│  RAG Export:                                                        │
│    • to_rag_chunks() → Iterator[RAGChunk]                           │
│    • Clean text + rich metadata for citation                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Structures

### Core Output: ScholarDocument

```python
@dataclass
class ScholarDocument:
    """The complete parsed document - ScholarDoc's core output."""

    # ─────────────────────────────────────────────────
    # Source Information
    # ─────────────────────────────────────────────────
    source_path: Path
    source_format: Literal["pdf", "epub"]
    document_type: DocumentType  # BOOK, ARTICLE, SELECTION, CHAPTER

    # ─────────────────────────────────────────────────
    # Content (Structured)
    # ─────────────────────────────────────────────────
    elements: list[Element]      # All content elements in order
    pages: list[Page]            # Page-level grouping

    # ─────────────────────────────────────────────────
    # Metadata (Extracted from PDF + front matter)
    # ─────────────────────────────────────────────────
    metadata: DocumentMetadata   # Title, author, publisher, year
    structure: TableOfContents   # Chapter/section hierarchy
    front_matter: FrontMatter    # Preface, acknowledgments, etc.

    # ─────────────────────────────────────────────────
    # Quality Assessment
    # ─────────────────────────────────────────────────
    quality: QualityAssessment   # Overall and per-page scores
    processing_log: list[str]    # What was done (re-OCR pages, etc.)

    # ─────────────────────────────────────────────────
    # For Selections (Student Use Case)
    # ─────────────────────────────────────────────────
    source_document: str | None  # Reference to full source if this is a selection
    page_range: tuple[int, int] | None  # Original page range
    is_complete: bool = True     # False if this is a selection/excerpt


class DocumentType(Enum):
    BOOK = "book"            # Full monograph
    ARTICLE = "article"      # Journal article, paper
    SELECTION = "selection"  # Excerpt from larger work
    CHAPTER = "chapter"      # Single chapter
    ANTHOLOGY = "anthology"  # Collection of works
```

### Element Model

```python
@dataclass
class Element:
    """A single content element in the document."""

    # ─────────────────────────────────────────────────
    # Identity
    # ─────────────────────────────────────────────────
    id: str                     # Unique ID: "doc_p064_e003"
    type: ElementType           # PARAGRAPH, HEADING, FOOTNOTE, etc.

    # ─────────────────────────────────────────────────
    # Content
    # ─────────────────────────────────────────────────
    text: str                   # Clean text (no page numbers, no headers)
    raw_text: str | None        # Original with artifacts (for debugging)

    # ─────────────────────────────────────────────────
    # Location
    # ─────────────────────────────────────────────────
    page_index: int             # 0-based page index
    page_label: str             # Printed label ("64", "xiv")
    bbox: BoundingBox | None    # Position on page

    # ─────────────────────────────────────────────────
    # Hierarchy
    # ─────────────────────────────────────────────────
    level: int | None           # For headings: 1, 2, 3
    parent_section: str | None  # Current section/chapter title
    parent_chapter: str | None  # Current chapter title

    # ─────────────────────────────────────────────────
    # Relationships
    # ─────────────────────────────────────────────────
    footnote_refs: list[str]    # Footnote marker IDs referenced here
    continues_from: str | None  # ID of previous element (if split)
    continues_to: str | None    # ID of next element (if split)

    # ─────────────────────────────────────────────────
    # Quality
    # ─────────────────────────────────────────────────
    quality_score: float        # 0.0-1.0
    ocr_method: Literal["existing", "doctr"] | None
```

### Metadata Structures

```python
@dataclass
class DocumentMetadata:
    """Document-level metadata."""
    title: str | None
    author: str | None
    authors: list[str]          # For multi-author works
    translator: str | None
    editor: str | None
    publisher: str | None
    year: int | None
    isbn: str | None
    doi: str | None

    # For citing
    citation_key: str | None    # BibTeX key if known


@dataclass
class TableOfContents:
    """Document structure."""
    entries: list[ToCEntry]

    def get_section_for_page(self, page_index: int) -> ToCEntry | None:
        """Get the current section for a given page."""
        ...


@dataclass
class ToCEntry:
    """Single ToC entry."""
    title: str
    level: int                  # 1=chapter, 2=section, 3=subsection
    page_index: int
    page_label: str
    children: list[ToCEntry]


@dataclass
class FrontMatter:
    """Extracted front matter (not embedded, used for metadata)."""
    title_page: str | None
    copyright: str | None
    dedication: str | None
    preface: str | None
    acknowledgments: str | None
    introduction: str | None    # Sometimes in front matter

    # Page ranges
    front_matter_pages: range   # Pages that are front matter
```

### RAG Output

```python
@dataclass
class RAGChunk:
    """Optimized for embedding and retrieval."""

    # ─────────────────────────────────────────────────
    # Content (CLEAN - ready to embed)
    # ─────────────────────────────────────────────────
    text: str                   # No page numbers, no headers, no artifacts

    # ─────────────────────────────────────────────────
    # Identity & Navigation
    # ─────────────────────────────────────────────────
    chunk_id: str               # "doc_chunk_042"
    chunk_index: int            # Position in document (0-based)
    total_chunks: int           # Total chunks in document
    prev_chunk_id: str | None   # For sequential reading
    next_chunk_id: str | None   # For sequential reading

    # ─────────────────────────────────────────────────
    # Location (for citation)
    # ─────────────────────────────────────────────────
    page_start: int             # First page index
    page_end: int               # Last page index
    page_labels: list[str]      # ["64", "65"] for citation

    # ─────────────────────────────────────────────────
    # Context (for retrieval enrichment)
    # ─────────────────────────────────────────────────
    section: str | None         # Current section title
    chapter: str | None         # Current chapter title
    document_type: DocumentType

    # ─────────────────────────────────────────────────
    # Document Info (for multi-doc retrieval)
    # ─────────────────────────────────────────────────
    doc_id: str                 # Hash or identifier
    doc_title: str | None
    doc_author: str | None
    doc_year: int | None

    # ─────────────────────────────────────────────────
    # Associated Content (not embedded, stored separately)
    # ─────────────────────────────────────────────────
    footnotes: list[Footnote]   # Footnotes from this chunk

    # ─────────────────────────────────────────────────
    # Quality
    # ─────────────────────────────────────────────────
    quality_score: float

    # ─────────────────────────────────────────────────
    # Convenience Properties
    # ─────────────────────────────────────────────────
    @property
    def citation(self) -> str:
        """Human-readable citation."""
        pages = "-".join(self.page_labels) if len(self.page_labels) > 1 else self.page_labels[0]
        if self.doc_author and self.doc_title:
            return f"{self.doc_author}, {self.doc_title}, p. {pages}"
        return f"p. {pages}"

    @property
    def metadata(self) -> dict:
        """Full metadata dict for vector store."""
        return {
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "page_labels": self.page_labels,
            "section": self.section,
            "chapter": self.chapter,
            "doc_id": self.doc_id,
            "doc_title": self.doc_title,
            "doc_author": self.doc_author,
            "citation": self.citation,
            "prev_chunk_id": self.prev_chunk_id,
            "next_chunk_id": self.next_chunk_id,
        }
```

---

## Use Cases

### Use Case 1: Full Book Processing

```python
from scholardoc import load

# Load entire book
doc = load("critique_of_pure_reason.pdf")

# Access metadata (extracted from PDF + front matter)
print(doc.metadata.title)      # "Critique of Pure Reason"
print(doc.metadata.author)     # "Immanuel Kant"
print(doc.metadata.translator) # "Werner S. Pluhar"

# Access table of contents
for entry in doc.structure.entries:
    print(f"{'  ' * entry.level}{entry.title} (p. {entry.page_label})")

# Export for RAG (front matter excluded by default)
for chunk in doc.to_rag_chunks():
    embed(chunk.text)
    store(chunk.metadata)
```

### Use Case 2: Article Processing

```python
# Load journal article
doc = load("derrida_signature_event.pdf")

# Articles often don't have front matter
print(doc.document_type)  # DocumentType.ARTICLE

# Simpler structure
print(doc.metadata.title)
print(doc.metadata.doi)

# Full article as chunks
chunks = list(doc.to_rag_chunks())
```

### Use Case 3: Student Selection (Page Range)

```python
# Load specific pages from a book (student use case)
doc = load(
    "being_and_time.pdf",
    page_range=(64, 120),  # Only these pages
    document_type=DocumentType.SELECTION
)

# Maintains reference to source
print(doc.source_document)  # "being_and_time.pdf"
print(doc.page_range)       # (64, 120)
print(doc.is_complete)      # False

# Chunks have context
for chunk in doc.to_rag_chunks():
    print(chunk.citation)   # "Heidegger, Being and Time, p. 64"
```

### Use Case 4: Anthology / Collected Readings

```python
# Process multiple selections into unified corpus
selections = [
    load("kant.pdf", page_range=(50, 80)),
    load("hegel.pdf", page_range=(100, 150)),
    load("heidegger.pdf", page_range=(1, 50)),
]

# Each maintains its own metadata
for sel in selections:
    for chunk in sel.to_rag_chunks():
        # Chunks know their source
        print(f"{chunk.doc_author}: {chunk.text[:50]}...")
```

---

## Configuration

```python
@dataclass
class ProcessingConfig:
    """Configuration for document processing."""

    # ─────────────────────────────────────────────────
    # OCR Strategy
    # ─────────────────────────────────────────────────
    ocr_strategy: Literal["existing", "doctr", "hybrid"] = "hybrid"
    reocr_quality_threshold: float = 0.7  # Re-OCR pages below this
    use_gpu: bool = True

    # ─────────────────────────────────────────────────
    # Structure Extraction
    # ─────────────────────────────────────────────────
    extract_toc: bool = True
    extract_front_matter: bool = True
    detect_headings: bool = True
    detect_footnotes: bool = True
    detect_blockquotes: bool = True
    detect_sous_erasure: bool = False  # Philosophy-specific

    # ─────────────────────────────────────────────────
    # Artifact Handling
    # ─────────────────────────────────────────────────
    remove_page_numbers: bool = True    # From text, keep as metadata
    remove_headers: bool = True         # From text, keep as metadata
    rejoin_hyphenation: bool = True     # Safe - embeddings robust

    # NO spell-check by default (too risky)
    spell_check: bool = False

    # ─────────────────────────────────────────────────
    # Output Control
    # ─────────────────────────────────────────────────
    include_front_matter_in_chunks: bool = False  # Usually not wanted
    include_back_matter_in_chunks: bool = False   # Notes, index, etc.

    # ─────────────────────────────────────────────────
    # Quality Thresholds
    # ─────────────────────────────────────────────────
    min_quality_for_rag: float = 0.5    # Warn below this


# Usage
doc = load("kant.pdf", config=ProcessingConfig(
    ocr_strategy="hybrid",
    reocr_quality_threshold=0.6,
    detect_sous_erasure=True,  # Enable for philosophy
))
```

---

## Key Design Decisions

### 1. No Spell-Check Correction

**Why:** 41% of philosophy terms would be wrongly "corrected" (Spike 13)

**Instead:**
- Use docTR re-OCR for low-quality pages (better than spell-check)
- Rely on fuzzy retrieval at search time
- Let users see original text to verify quality

### 2. Remove Artifacts → Keep as Metadata

| Artifact | Action | Rationale |
|----------|--------|-----------|
| Page numbers | Remove from text, store in `page_label` | 29% embedding improvement |
| Running headers | Remove from text, store in `section` | 2% improvement, cleaner |
| Footnote markers | Remove from text, store in `footnote_refs` | Keep relationship |
| Hyphenation | Rejoin words | Safe, embeddings robust |

### 3. Front Matter as Metadata, Not Embedded

**Rationale:**
- Front matter (preface, acknowledgments) is meta-content
- Not useful for semantic search about the book's *content*
- But valuable for filling document metadata

**Extraction:**
- Parse title page → `metadata.title`, `metadata.author`
- Parse copyright → `metadata.publisher`, `metadata.year`
- Store full text in `front_matter` for reference
- Exclude from `to_rag_chunks()` by default

### 4. ToC Extraction for Navigation

**Purpose:**
- Provide section/chapter context for each chunk
- Enable hierarchical navigation
- Support "what's in chapter 3?" queries

**Storage:**
- Full ToC in `structure.entries`
- Current section/chapter in each `Element` and `RAGChunk`

### 5. Hybrid OCR Strategy

```python
def process_page(page, config):
    quality = assess_quality(page)

    if quality >= config.reocr_quality_threshold:
        # Fast path: use existing text layer
        return extract_existing_text(page)
    else:
        # Slow path: re-OCR with docTR (~0.6s GPU)
        return doctr_ocr(page, use_gpu=config.use_gpu)
```

**Trade-offs:**
- Born-digital PDFs: Fast (no re-OCR needed)
- Mixed quality: Selective re-OCR only for bad pages
- Fully scanned: Full re-OCR (slower, but best quality)

---

## Summary

| Question | Answer |
|----------|--------|
| **OCR Strategy** | Hybrid: existing for good pages, docTR for bad pages |
| **Spell-Check** | No - too risky (41% damage rate) |
| **Page Numbers** | Remove from text, keep as `page_label` metadata |
| **Headers** | Remove from text, keep as `section` metadata |
| **ToC** | Yes, extract for navigation and context |
| **Front Matter** | Extract as metadata, exclude from RAG chunks |
| **Data Structure** | `ScholarDocument` → `to_rag_chunks()` → `RAGChunk` |
| **Selections** | Support `page_range` with source reference |
| **Chunk Relations** | `prev_chunk_id`, `next_chunk_id`, `chunk_index` |
