# Core Representation Design

> **Status:** Proposal
> **Created:** December 21, 2025
> **Context:** Defining the canonical data structure for ScholarDoc output

---

## Design Goals

1. **Preserve all scholarly information** - page numbers, footnotes, citations, cross-references
2. **Support multiple downstream uses** - RAG, Anki, export formats, analysis
3. **Enable flexible chunking** - don't lock into one strategy
4. **Keep core lean** - no bloat from niche export formats
5. **Position-accurate associations** - know exactly where footnote markers were

---

## Core Insight: Clean Text + Position Annotations

The `text` field contains the semantic content (what the author wrote). Artifacts like footnote markers and page numbers are **removed** but their positions are **recorded** as annotations.

```
Original PDF: "The beautiful¹ morning. 64 The sublime..."
                           ↑              ↑
                      footnote        page number

Our representation:
  text = "The beautiful morning. The sublime..."
  footnote_refs = [FootnoteRef(position=13, marker="¹", target="fn1")]
  pages = [PageSpan(start=0, end=22, label="63"), PageSpan(start=23, ..., label="64")]
```

**Why this approach:**
- `text` is ready for embedding (no artifacts to filter)
- Annotations augment the clean text with metadata
- Can reconstruct original appearance by inserting markers at positions
- Position lookups are simple (no mapping through transformations)

---

## Data Structures

### ScholarDocument (The Core Class)

```python
@dataclass
class ScholarDocument:
    """The canonical representation of a scholarly document."""

    # ─────────────────────────────────────────────────
    # Core Content
    # ─────────────────────────────────────────────────
    text: str  # Clean text, artifacts removed

    # ─────────────────────────────────────────────────
    # Position-Based Annotations (reference positions in `text`)
    # ─────────────────────────────────────────────────
    footnote_refs: list[FootnoteRef]   # Where footnote markers were
    endnote_refs: list[EndnoteRef]     # Where endnote markers were
    citations: list[CitationRef]        # Where citations were
    cross_refs: list[CrossRef]          # "see p. 45", "see §3.2"

    # ─────────────────────────────────────────────────
    # Structural Spans (ranges in `text`)
    # ─────────────────────────────────────────────────
    pages: list[PageSpan]              # Page boundaries
    sections: list[SectionSpan]        # Chapter/section boundaries
    paragraphs: list[ParagraphSpan]    # Paragraph boundaries
    block_quotes: list[BlockQuoteSpan] # Indented quotations

    # ─────────────────────────────────────────────────
    # Referenced Content (the actual footnote/endnote text)
    # ─────────────────────────────────────────────────
    notes: dict[str, Note]             # "fn1" -> Note(text="...", type=FOOTNOTE)
    bibliography: list[BibEntry]       # Parsed bibliography entries

    # ─────────────────────────────────────────────────
    # Table of Contents (if present)
    # ─────────────────────────────────────────────────
    toc: TableOfContents | None        # Parsed ToC, enriches section detection

    # ─────────────────────────────────────────────────
    # Document Metadata
    # ─────────────────────────────────────────────────
    metadata: DocumentMetadata         # Title, author, document type

    # ─────────────────────────────────────────────────
    # Processing Info
    # ─────────────────────────────────────────────────
    source_path: Path
    quality: QualityInfo               # OCR quality scores
    processing_log: list[str]          # What transformations were applied
```

### Annotation Types

```python
@dataclass
class FootnoteRef:
    """A footnote marker that was removed from text."""
    position: int          # Where in `text` the marker was (between chars)
    marker: str            # The original marker ("¹", "*", "†")
    target_id: str         # Reference to notes["fn1"]

@dataclass
class CitationRef:
    """An in-text citation."""
    start: int             # Start position in `text`
    end: int               # End position in `text`
    original: str          # "(Heidegger, 1927)" or "[1]"
    parsed: ParsedCitation | None  # Structured if parseable
    bib_entry_id: str | None       # Link to bibliography entry

@dataclass
class CrossRef:
    """A cross-reference to another part of the document."""
    start: int
    end: int
    original: str          # "see p. 45", "see §3.2", "see above"
    target_page: str | None
    target_section: str | None
    resolved_position: int | None  # If we can resolve "see above"

@dataclass
class PageSpan:
    """A page boundary."""
    start: int             # Start position in `text`
    end: int               # End position in `text`
    label: str             # "64", "xiv", "A64/B93"
    index: int             # 0-based page index in PDF

@dataclass
class SectionSpan:
    """A section/chapter boundary."""
    start: int
    end: int
    title: str
    level: int             # 1=chapter, 2=section, 3=subsection

@dataclass
class Note:
    """The actual content of a footnote/endnote."""
    id: str                # "fn1", "en23"
    text: str              # The note content
    type: NoteType         # FOOTNOTE, ENDNOTE, TRANSLATOR, EDITOR
    page_label: str        # Where the note appears
    source: NoteSource     # AUTHOR, TRANSLATOR, EDITOR


@dataclass
class ToCEntry:
    """An entry from the Table of Contents."""
    title: str
    page_label: str        # "5", "xiv", etc.
    level: int             # 1=chapter, 2=section, etc.
    children: list["ToCEntry"]
    resolved_position: int | None  # Position in text if resolved


@dataclass
class TableOfContents:
    """Parsed table of contents from document."""
    entries: list[ToCEntry]
    page_range: tuple[int, int]    # Where ToC appears (page indices)
    confidence: float              # Parsing confidence
```

### Document Metadata

```python
@dataclass
class DocumentMetadata:
    """Metadata about the source document."""
    title: str | None
    author: str | None
    publication_date: str | None
    isbn: str | None
    doi: str | None
    language: str                  # ISO 639-1 code
    document_type: DocumentType    # BOOK, ARTICLE, ESSAY, REPORT


class DocumentType(Enum):
    """Classification of document types."""
    BOOK = "book"                  # Multi-chapter with ToC
    ARTICLE = "article"            # Academic article with abstract
    ESSAY = "essay"                # Essay with subheadings
    REPORT = "report"              # Technical report with sections
    GENERIC = "generic"            # Unclassified
```

---

## What Stays on the Class

### Criteria for Inclusion

| Include on class | Move to external function |
|------------------|---------------------------|
| No external dependencies | Has dependencies (genanki, etc.) |
| >50% of users need it | <20% of users need it |
| Core to document interaction | Specialized export format |
| Simple implementation | Complex implementation |

### Class Methods

```python
@dataclass
class ScholarDocument:
    # ... fields above ...

    # ─────────────────────────────────────────────────
    # Query Methods (essential for working with doc)
    # ─────────────────────────────────────────────────
    def text_range(self, start: int, end: int) -> str:
        """Get text slice."""
        return self.text[start:end]

    def annotations_in_range(self, start: int, end: int) -> list[Annotation]:
        """Get all annotations overlapping a range."""
        ...

    def page_for_position(self, pos: int) -> PageSpan:
        """Which page contains this position?"""
        ...

    def section_for_position(self, pos: int) -> SectionSpan | None:
        """Which section contains this position?"""
        ...

    def footnotes_in_range(self, start: int, end: int) -> list[tuple[FootnoteRef, Note]]:
        """Get footnotes referenced in a text range."""
        ...

    # ─────────────────────────────────────────────────
    # Derived Views (lazy, commonly needed)
    # ─────────────────────────────────────────────────
    @cached_property
    def words(self) -> list[Token]:
        """Tokenized words with positions."""
        ...

    @cached_property
    def paragraph_texts(self) -> list[str]:
        """List of paragraph strings."""
        return [self.text[p.start:p.end] for p in self.paragraphs]

    def sentences(self) -> Iterator[Span]:
        """Sentence spans (generator, computed on demand)."""
        ...

    # ─────────────────────────────────────────────────
    # Common Exports (no deps, universal need)
    # ─────────────────────────────────────────────────
    def to_markdown(self, include_footnotes: bool = True) -> str:
        """Export to Markdown with footnotes."""
        ...

    def to_plain_text(self) -> str:
        """Just the text."""
        return self.text

    def to_rag_chunks(
        self,
        strategy: ChunkStrategy = ChunkStrategy.SEMANTIC,
        max_tokens: int = 512,
        overlap: int = 50,
    ) -> Iterator[RAGChunk]:
        """Generate RAG-ready chunks with metadata."""
        ...

    # ─────────────────────────────────────────────────
    # Persistence
    # ─────────────────────────────────────────────────
    def save(self, path: Path) -> None:
        """Save to .scholardoc (JSON) or .scholardb (SQLite)."""
        ...

    @classmethod
    def load(cls, path: Path) -> "ScholarDocument":
        """Load from saved format."""
        ...

    # ─────────────────────────────────────────────────
    # Convenience
    # ─────────────────────────────────────────────────
    def __len__(self) -> int:
        return len(self.text)

    def __getitem__(self, key: slice) -> str:
        return self.text[key]
```

### External Functions (in scholardoc/export/)

```python
# scholardoc/export/anki.py
def to_anki_deck(doc: ScholarDocument, config: AnkiConfig) -> AnkiDeck:
    """Requires: pip install scholardoc[anki]"""
    ...

# scholardoc/export/latex.py
def to_latex(doc: ScholarDocument, template: str = "article") -> str:
    """Export to LaTeX."""
    ...

# scholardoc/export/html.py
def to_html(doc: ScholarDocument, standalone: bool = True) -> str:
    """Export to HTML."""
    ...

# scholardoc/export/epub.py
def to_epub(doc: ScholarDocument, path: Path) -> None:
    """Export to EPUB."""
    ...

# scholardoc/export/bibliography.py
def to_bibtex(doc: ScholarDocument) -> str:
    """Export bibliography to BibTeX."""
    ...

def to_zotero(doc: ScholarDocument) -> dict:
    """Export for Zotero import."""
    ...
```

---

## Storage Format

### Decision: JSON for small docs, SQLite for large

```python
def save(self, path: Path) -> None:
    if len(self.text) > 1_000_000:  # ~1MB text
        self._save_sqlite(path.with_suffix('.scholardb'))
    else:
        self._save_json(path.with_suffix('.scholardoc'))
```

### JSON Format (.scholardoc)

```json
{
  "version": "1.0",
  "source_path": "being_and_time.pdf",
  "text": "The question of Being has today...",
  "footnote_refs": [
    {"position": 156, "marker": "¹", "target_id": "fn1"}
  ],
  "pages": [
    {"start": 0, "end": 2340, "label": "1", "index": 0}
  ],
  "sections": [
    {"start": 0, "end": 5000, "title": "Introduction", "level": 1}
  ],
  "notes": {
    "fn1": {"id": "fn1", "text": "See Aristotle...", "type": "footnote", "page_label": "1"}
  },
  "metadata": {
    "title": "Being and Time",
    "author": "Martin Heidegger"
  }
}
```

### SQLite Format (.scholardb)

For documents >1MB or when random access is needed:

```sql
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE content (text TEXT);
CREATE TABLE footnote_refs (position INTEGER, marker TEXT, target_id TEXT);
CREATE TABLE pages (start INTEGER, end INTEGER, label TEXT, idx INTEGER);
CREATE TABLE sections (start INTEGER, end INTEGER, title TEXT, level INTEGER);
CREATE TABLE notes (id TEXT PRIMARY KEY, text TEXT, type TEXT, page_label TEXT);

CREATE INDEX idx_pages_start ON pages(start);
CREATE INDEX idx_footnotes_pos ON footnote_refs(position);
```

---

## RAG Chunk Generation

The `to_rag_chunks()` method is on the class because it's the primary use case.

```python
@dataclass
class RAGChunk:
    """A chunk ready for embedding."""

    text: str                    # Clean text for embedding
    chunk_id: str                # Unique identifier
    chunk_index: int             # Position in sequence

    # Location
    page_labels: list[str]       # ["64", "65"]
    section: str | None          # Current section title
    chapter: str | None          # Current chapter title

    # Associations (what was in this chunk's range)
    footnote_refs: list[FootnoteRef]
    citations: list[CitationRef]

    # Navigation
    prev_chunk_id: str | None
    next_chunk_id: str | None

    # Document info
    doc_title: str | None
    doc_author: str | None

    @property
    def citation(self) -> str:
        """Human-readable citation string."""
        pages = "-".join(self.page_labels)
        if self.doc_author and self.doc_title:
            return f"{self.doc_author}, {self.doc_title}, p. {pages}"
        return f"p. {pages}"


class ChunkStrategy(Enum):
    SEMANTIC = "semantic"      # By paragraph/section boundaries
    FIXED_SIZE = "fixed_size"  # Fixed token count
    PAGE = "page"              # One chunk per page
    SECTION = "section"        # One chunk per section
```

### Chunking Preserves Associations

Because annotations are position-based, chunking naturally preserves them:

```python
def to_rag_chunks(self, ...) -> Iterator[RAGChunk]:
    for chunk_start, chunk_end in self._chunk_boundaries(strategy, max_tokens):
        yield RAGChunk(
            text=self.text[chunk_start:chunk_end],
            footnote_refs=self.footnotes_in_range(chunk_start, chunk_end),
            citations=self.citations_in_range(chunk_start, chunk_end),
            page_labels=[p.label for p in self.pages_in_range(chunk_start, chunk_end)],
            ...
        )
```

---

## Open Questions

1. **Sentence detection** - Compute on demand or store? (Currently: compute on demand)

2. **Original text preservation** - Do we need to store the original with artifacts? (Currently: no, can reconstruct)

3. **Cross-reference resolution** - How far do we go in resolving "see above"? (Currently: optional, may be None)

4. **Bibliography parsing** - How much structure to extract from citations? (TBD)

5. **Multi-language support** - How to handle German terms in English text? (TBD)

---

## Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Text representation | Clean text + position annotations | Ready for embedding, no filtering needed |
| Core class size | Query methods + common exports | Balance utility vs bloat |
| Niche exports | External functions | No dep bloat, extensible |
| Storage | JSON small, SQLite large | Appropriate for access patterns |
| Chunking | On-demand with position preservation | Flexible, associations maintained |

---

## Related Design Documents

- **[STRUCTURE_EXTRACTION.md](STRUCTURE_EXTRACTION.md)** - How sections are detected via probabilistic fusion
- **[FEEDBACK_SYSTEM.md](FEEDBACK_SYSTEM.md)** - Learning from human corrections
- **[QUALITY_FILTERING.md](QUALITY_FILTERING.md)** - OCR quality assessment and filtering
- **[PROCESSING_ARCHITECTURE.md](PROCESSING_ARCHITECTURE.md)** - Overall processing pipeline
