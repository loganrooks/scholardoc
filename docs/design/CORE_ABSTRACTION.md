# ScholarDoc Core Abstraction Design

> **Status:** Proposal
> **Created:** December 19, 2025
> **Context:** Defining the "DataFrame equivalent" for ScholarDoc

## The Question

What is ScholarDoc's core output/object that other applications consume?

Like Pandas revolves around DataFrames, what does ScholarDoc revolve around?

## Design Principles

1. **Single source of truth** - One parsed document, multiple views
2. **Clean data by default** - Artifacts removed, ready for use
3. **Metadata preserved separately** - Available but not mixed with content
4. **Lazy evaluation where possible** - Don't compute until needed
5. **Composable with existing tools** - Works with LangChain, LlamaIndex, etc.

---

## Core Object: `ScholarDocument`

The main container returned by `scholardoc.load()`.

```python
from scholardoc import load

# Load a document
doc = load("kant_critique.pdf")

# Basic info
print(doc.title)          # "Critique of Pure Reason"
print(doc.page_count)     # 685
print(len(doc.elements))  # 2847 elements

# Iteration over elements
for element in doc:
    print(element.type, element.text[:50])

# Page access
page = doc.pages[64]
print(page.label)  # "64" (the printed label)
print(page.text)   # Full page text (clean)

# Export to different formats
markdown = doc.to_markdown()
json_data = doc.to_json()

# RAG-optimized export
for chunk in doc.to_rag_chunks():
    embedding = embed(chunk.text)
    store(embedding, chunk.metadata)
```

---

## Data Model

### Element (atomic unit)

```python
@dataclass
class Element:
    """A single content element in the document."""

    # Content
    text: str               # Clean text, no artifacts
    raw_text: str           # Original text with artifacts (for debugging)

    # Classification
    type: ElementType       # PARAGRAPH, HEADING, FOOTNOTE, QUOTE, etc.
    level: int | None       # For headings: 1, 2, 3

    # Location
    page_index: int         # 0-based index
    page_label: str         # Printed label ("64", "xiv")
    bbox: BoundingBox       # Position on page

    # Relationships
    footnotes: list[str]    # Footnote texts that were in this element
    continues_from: int | None  # If split across pages, previous element index
    continues_to: int | None    # If split across pages, next element index

    # Quality
    quality_score: float    # 0.0-1.0
    corrections: list[str]  # OCR corrections applied


class ElementType(Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    FOOTNOTE = "footnote"
    ENDNOTE = "endnote"
    BLOCKQUOTE = "blockquote"
    LIST_ITEM = "list_item"
    TABLE = "table"
    FIGURE_CAPTION = "figure_caption"
    PAGE_HEADER = "page_header"
    PAGE_FOOTER = "page_footer"
```

### Page (container)

```python
@dataclass
class Page:
    """A single page in the document."""

    index: int              # 0-based index
    label: str              # Printed label ("64", "xiv")
    elements: list[Element]

    @property
    def text(self) -> str:
        """Clean text for this page (no artifacts)."""
        return "\n\n".join(
            e.text for e in self.elements
            if e.type not in {ElementType.PAGE_HEADER, ElementType.PAGE_FOOTER}
        )

    @property
    def footnotes(self) -> list[Element]:
        """Footnotes on this page."""
        return [e for e in self.elements if e.type == ElementType.FOOTNOTE]
```

### ScholarDocument (main container)

```python
@dataclass
class ScholarDocument:
    """The main output type - ScholarDoc's 'DataFrame'."""

    # Source info
    source_path: Path
    source_format: str      # "pdf", "epub"

    # Content
    elements: list[Element]
    pages: list[Page]

    # Metadata
    metadata: DocumentMetadata
    structure: TableOfContents

    # Quality
    quality: QualityAssessment
    warnings: list[str]

    # ─────────────────────────────────────────────────
    # Iteration
    # ─────────────────────────────────────────────────

    def __iter__(self) -> Iterator[Element]:
        """Iterate over all elements."""
        return iter(self.elements)

    def __len__(self) -> int:
        """Number of elements."""
        return len(self.elements)

    def __getitem__(self, idx: int) -> Element:
        """Get element by index."""
        return self.elements[idx]

    # ─────────────────────────────────────────────────
    # Filtering
    # ─────────────────────────────────────────────────

    def filter(self,
               types: set[ElementType] | None = None,
               min_quality: float = 0.0,
               pages: range | None = None) -> Iterator[Element]:
        """Filter elements by criteria."""
        for e in self.elements:
            if types and e.type not in types:
                continue
            if e.quality_score < min_quality:
                continue
            if pages and e.page_index not in pages:
                continue
            yield e

    @property
    def paragraphs(self) -> list[Element]:
        """All paragraph elements."""
        return [e for e in self.elements if e.type == ElementType.PARAGRAPH]

    @property
    def headings(self) -> list[Element]:
        """All heading elements."""
        return [e for e in self.elements if e.type == ElementType.HEADING]

    @property
    def footnotes(self) -> list[Element]:
        """All footnote elements."""
        return [e for e in self.elements if e.type == ElementType.FOOTNOTE]

    # ─────────────────────────────────────────────────
    # Export Methods
    # ─────────────────────────────────────────────────

    def to_markdown(self,
                    include_page_markers: bool = True,
                    include_footnotes: bool = True) -> str:
        """Export to Markdown string."""
        ...

    def to_json(self) -> dict:
        """Export to JSON-serializable dict."""
        ...

    def to_dataframe(self) -> "pd.DataFrame":
        """Export to Pandas DataFrame for analysis."""
        import pandas as pd
        return pd.DataFrame([
            {"text": e.text, "type": e.type.value, "page": e.page_label, ...}
            for e in self.elements
        ])

    # ─────────────────────────────────────────────────
    # RAG Export (the key method!)
    # ─────────────────────────────────────────────────

    def to_rag_chunks(self,
                      strategy: ChunkStrategy = "paragraph",
                      include_footnotes: bool = False,
                      min_chunk_size: int = 100,
                      max_chunk_size: int = 2000) -> Iterator[RAGChunk]:
        """
        Export as RAG-ready chunks.

        This is the primary interface for RAG pipelines.

        Args:
            strategy: How to chunk - "paragraph", "page", "section", "semantic"
            include_footnotes: Whether to include footnotes in chunk text
            min_chunk_size: Minimum characters per chunk
            max_chunk_size: Maximum characters per chunk

        Yields:
            RAGChunk objects with clean text and metadata
        """
        ...

    # ─────────────────────────────────────────────────
    # Quality Checks
    # ─────────────────────────────────────────────────

    def is_rag_ready(self) -> bool:
        """Check if document quality is sufficient for RAG."""
        return self.quality.is_usable_for_rag

    def get_problem_pages(self, threshold: float = 0.5) -> list[int]:
        """Get page indices with quality below threshold."""
        return [p.index for p in self.pages if p.quality_score < threshold]
```

---

## RAGChunk: The RAG Interface

This is what RAG pipelines actually consume:

```python
@dataclass
class RAGChunk:
    """
    A chunk optimized for RAG embedding and retrieval.

    The text is CLEAN - no page numbers, headers, or artifacts.
    The metadata contains everything needed for citation.
    """

    # ─────────────────────────────────────────────────
    # Content (for embedding)
    # ─────────────────────────────────────────────────

    text: str               # Clean text, ready to embed
                            # NO page numbers, NO headers, NO markers

    # ─────────────────────────────────────────────────
    # Metadata (for retrieval/citation)
    # ─────────────────────────────────────────────────

    # Location
    page_start: int         # First page index
    page_end: int           # Last page index (if spans pages)
    page_labels: list[str]  # ["64", "65"] for citation

    # Context
    section: str | None     # Current section heading
    chapter: str | None     # Current chapter title

    # Document info (for multi-doc retrieval)
    doc_id: str             # Hash or path
    doc_title: str | None
    doc_author: str | None

    # Quality
    quality_score: float

    # Relationships
    chunk_index: int        # Position in document
    total_chunks: int

    # ─────────────────────────────────────────────────
    # Footnotes (embedded separately or ignored)
    # ─────────────────────────────────────────────────

    footnotes: list[str]    # Footnotes from this chunk
                            # Not included in text - handle separately

    # ─────────────────────────────────────────────────
    # Convenience
    # ─────────────────────────────────────────────────

    @property
    def citation(self) -> str:
        """Human-readable citation string."""
        pages = "-".join(self.page_labels)
        if self.doc_author and self.doc_title:
            return f"{self.doc_author}, {self.doc_title}, p. {pages}"
        return f"p. {pages}"

    @property
    def metadata(self) -> dict:
        """Dict of all metadata for vector store."""
        return {
            "page_start": self.page_start,
            "page_end": self.page_end,
            "page_labels": self.page_labels,
            "section": self.section,
            "chapter": self.chapter,
            "doc_id": self.doc_id,
            "doc_title": self.doc_title,
            "quality_score": self.quality_score,
            "citation": self.citation,
        }
```

---

## Usage Examples

### Example 1: Basic RAG Pipeline

```python
from scholardoc import load
from some_embedding_lib import embed
from some_vectordb import VectorStore

# Load document
doc = load("critique_of_pure_reason.pdf")

# Check quality
if not doc.is_rag_ready():
    print(f"Warning: Document has quality issues: {doc.warnings}")

# Create embeddings
store = VectorStore()
for chunk in doc.to_rag_chunks():
    embedding = embed(chunk.text)  # Clean text, no artifacts
    store.add(
        embedding=embedding,
        text=chunk.text,
        metadata=chunk.metadata  # Page numbers, section, etc.
    )

# Query
results = store.query("What does Kant say about the age of criticism?")
for result in results:
    print(result.text)
    print(f"  Source: {result.metadata['citation']}")
```

### Example 2: LangChain Integration

```python
from scholardoc import load
from langchain.schema import Document as LCDocument

doc = load("paper.pdf")

# Convert to LangChain documents
lc_docs = [
    LCDocument(
        page_content=chunk.text,
        metadata=chunk.metadata
    )
    for chunk in doc.to_rag_chunks()
]

# Use with LangChain
from langchain.vectorstores import Chroma
vectorstore = Chroma.from_documents(lc_docs, embedding_model)
```

### Example 3: MCP Server

```python
# In an MCP server for RAG
from scholardoc import load

@mcp.tool
async def query_document(pdf_path: str, query: str) -> str:
    doc = load(pdf_path)

    # Get chunks, embed, search...
    chunks = list(doc.to_rag_chunks())

    # Return with citation
    result = search(query, chunks)
    return f"{result.text}\n\nSource: {result.citation}"
```

### Example 4: Analysis with Pandas

```python
from scholardoc import load

doc = load("dissertation.pdf")
df = doc.to_dataframe()

# Analyze document structure
print(df.groupby('type').count())

# Find low-quality sections
low_quality = df[df['quality_score'] < 0.5]
print(f"Problem pages: {low_quality['page_label'].unique()}")
```

### Example 5: Custom Chunking

```python
doc = load("paper.pdf")

# Paragraph-level (default)
para_chunks = doc.to_rag_chunks(strategy="paragraph")

# Page-level (for longer context)
page_chunks = doc.to_rag_chunks(strategy="page")

# Section-level (follows document structure)
section_chunks = doc.to_rag_chunks(strategy="section")

# Semantic (uses headings as boundaries)
semantic_chunks = doc.to_rag_chunks(
    strategy="semantic",
    max_chunk_size=1500
)
```

---

## Chunking Strategies

```python
class ChunkStrategy(Enum):
    PARAGRAPH = "paragraph"   # One element per chunk (default)
    PAGE = "page"             # One page per chunk
    SECTION = "section"       # Group by section headings
    SEMANTIC = "semantic"     # Smart boundaries using structure
    FIXED = "fixed"           # Fixed token/char count
```

Each strategy produces the same `RAGChunk` type, just with different granularity.

---

## Integration Points

### What ScholarDoc Provides

1. **`ScholarDocument`** - The parsed document with structure
2. **`RAGChunk`** - Clean chunks ready for embedding
3. **`.to_markdown()`** - For reading/display
4. **`.to_json()`** - For serialization
5. **`.to_dataframe()`** - For analysis

### What Consumers Provide

1. **Embedding model** - Turn chunk.text into vectors
2. **Vector store** - Store and retrieve chunks
3. **LLM** - Generate answers from retrieved chunks

### ScholarDoc Does NOT

1. ❌ Chunk text (that's consumer's choice via strategy parameter)
2. ❌ Generate embeddings (use any embedding model)
3. ❌ Store vectors (use any vector database)
4. ❌ Run inference (use any LLM)

---

## Summary

**Core Abstraction:** `ScholarDocument` (like DataFrame)

**Key Methods:**
- `doc.to_rag_chunks()` - Primary RAG interface
- `doc.to_markdown()` - Human-readable output
- `doc.to_json()` - Serialization
- `doc.elements`, `doc.pages` - Structured access
- `for chunk in doc` - Iteration

**RAG Interface:** `RAGChunk`
- `chunk.text` - Clean, embeddable content
- `chunk.metadata` - Page numbers, section, citation
- `chunk.citation` - Human-readable source reference

**Philosophy:**
- One document, multiple views
- Clean content by default
- Metadata separate from content
- Works with existing tools (LangChain, LlamaIndex, etc.)
