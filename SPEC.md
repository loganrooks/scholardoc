# ScholarDoc Technical Specification

> **Status:** Draft  
> **Last Updated:** December 2025  
> **Depends On:** REQUIREMENTS.md, QUESTIONS.md

---

## Overview

ScholarDoc is a Python library for converting scholarly documents to structured Markdown. This specification defines the technical approach, data models, and interfaces.

---

## Core Design Principles

### 1. Input Agnostic, Output Consistent
Different input formats (PDF, EPUB, Markdown) should produce consistent output structure. The library provides a unified interface regardless of source format.

### 2. Metadata Preservation Over Interpretation
We preserve information from the source document rather than interpreting it. For example, we preserve font size changes rather than deciding if something is a "heading."

### 3. Graceful Degradation
When extraction fails or is uncertain, we provide the best available output with warnings rather than failing entirely.

### 4. No Hidden State
Processing is stateless and deterministic. Same input + same config = same output.

### 5. Extensibility Through Composition
New formats and extractors are added as plugins/adapters, not modifications to core.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Public API                               │
│  scholardoc.convert(path, config) → ScholarDocument             │
│  scholardoc.convert_batch(paths, config) → Iterator             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Format Detection                            │
│  Detect input format, select appropriate Reader                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Readers (Input)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ PDFReader   │  │ EPUBReader  │  │ MarkdownRdr │  (future)   │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  All readers produce: RawDocument                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Normalizers (Transform)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │StructureNorm    │  │ PageMapper      │  │ FootnoteLinker │  │
│  │(heading detect) │  │(page numbers)   │  │(Phase 2)       │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
│  Input: RawDocument → Output: NormalizedDocument               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Writers (Output)                            │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ MarkdownWriter  │  │ JSONWriter      │  (future)            │
│  └─────────────────┘  └─────────────────┘                      │
│  Input: NormalizedDocument → Output: str/file                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Models

### RawDocument
Internal representation after initial extraction, before normalization.

```python
@dataclass
class RawDocument:
    """Raw extracted content before normalization."""
    source: DocumentSource
    pages: list[RawPage]
    metadata: dict[str, Any]
    warnings: list[str]

@dataclass
class RawPage:
    """Single page of raw content."""
    page_index: int              # 0-based PDF page
    page_label: str | None       # Printed page number if detectable
    blocks: list[TextBlock]
    
@dataclass  
class TextBlock:
    """A block of text with position and style info."""
    text: str
    bbox: tuple[float, float, float, float]  # x0, y0, x1, y1
    font_name: str | None
    font_size: float | None
    is_bold: bool
    is_italic: bool
    block_type: BlockType  # PARAGRAPH, HEADING, FOOTNOTE, etc.
```

### NormalizedDocument
Clean, structured representation ready for output.

```python
@dataclass
class NormalizedDocument:
    """Normalized document ready for output."""
    source: DocumentSource
    metadata: DocumentMetadata
    content: list[ContentElement]
    structure: DocumentStructure
    warnings: list[str]

@dataclass
class ContentElement:
    """A content element in the document."""
    element_type: ElementType  # HEADING, PARAGRAPH, BLOCKQUOTE, etc.
    text: str
    level: int | None          # For headings: 1, 2, 3
    page_index: int | None
    page_label: str | None
    attributes: dict[str, Any]

@dataclass
class DocumentMetadata:
    """Document metadata."""
    title: str | None
    authors: list[str]
    date: str | None
    isbn: str | None
    doi: str | None
    language: str | None
    page_count: int
    source_format: str         # "pdf", "epub", etc.
    extraction_date: datetime
    scholardoc_version: str

@dataclass
class DocumentStructure:
    """Document structure (TOC-like)."""
    sections: list[Section]
    
@dataclass
class Section:
    """A section in the document structure."""
    title: str
    level: int
    page_label: str | None
    children: list[Section]
```

### ScholarDocument (Public Output)
The main output type returned to users.

```python
@dataclass
class ScholarDocument:
    """The main output type for users."""
    
    # Rendered output
    markdown: str
    
    # Structured data
    metadata: DocumentMetadata
    structure: DocumentStructure
    
    # Diagnostics
    source_path: str
    warnings: list[str]
    
    def save(self, path: str) -> None:
        """Save markdown to file."""
        
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
```

---

## Configuration

> **⚠️ DRAFT:** Options below depend on unresolved questions. See QUESTIONS.md Q1 (page format), Q2 (multi-column), Q4 (heading strategy).

```python
@dataclass
class ConversionConfig:
    """Configuration for document conversion."""
    
    # Output options
    include_metadata_frontmatter: bool = True
    include_page_markers: bool = True
    page_marker_style: Literal["comment", "heading", "inline"] = "comment"
    
    # Structure options
    detect_headings: bool = True
    heading_detection_strategy: Literal["font", "heuristic", "none"] = "heuristic"
    preserve_line_breaks: bool = False  # True = hard breaks, False = soft wrap
    
    # Page options
    page_label_source: Literal["auto", "index", "label"] = "auto"
    
    # Error handling
    on_extraction_error: Literal["raise", "warn", "skip"] = "warn"
    
    # Future phases (no-op for now)
    extract_footnotes: bool = False  # Phase 2
    extract_tables: bool = False     # Phase 2
```

---

## Public API

### Primary Functions

```python
def convert(
    source: str | Path,
    config: ConversionConfig | None = None,
) -> ScholarDocument:
    """
    Convert a single document to structured Markdown.
    
    Args:
        source: Path to document file
        config: Conversion configuration (uses defaults if None)
        
    Returns:
        ScholarDocument with markdown and metadata
        
    Raises:
        FileNotFoundError: If source doesn't exist
        UnsupportedFormatError: If format not supported
        ExtractionError: If extraction fails (when on_extraction_error="raise")
    """

def convert_batch(
    sources: Iterable[str | Path],
    config: ConversionConfig | None = None,
    parallel: bool = False,
    max_workers: int = 4,
) -> Iterator[tuple[Path, ScholarDocument | Exception]]:
    """
    Convert multiple documents, yielding results as completed.
    
    Args:
        sources: Paths to document files
        config: Conversion configuration
        parallel: Whether to process in parallel
        max_workers: Max parallel workers (if parallel=True)
        
    Yields:
        (path, result) tuples where result is ScholarDocument or Exception
    """
```

### Format Detection

```python
def detect_format(path: str | Path) -> str:
    """
    Detect document format from file extension and magic bytes.
    
    Returns:
        Format string: "pdf", "epub", "markdown", etc.
        
    Raises:
        UnsupportedFormatError: If format cannot be detected or isn't supported
    """

def supported_formats() -> list[str]:
    """Return list of currently supported input formats."""
```

---

## Extension Points

### Custom Readers (Phase 3+)

```python
class BaseReader(ABC):
    """Base class for document readers."""
    
    @abstractmethod
    def can_read(self, path: Path) -> bool:
        """Return True if this reader can handle the file."""
        
    @abstractmethod
    def read(self, path: Path) -> RawDocument:
        """Read the document and return raw content."""

# Registration
scholardoc.register_reader(MyCustomReader())
```

### Custom Normalizers (Phase 2+)

```python
class BaseNormalizer(ABC):
    """Base class for document normalizers."""
    
    @abstractmethod
    def normalize(self, doc: RawDocument) -> RawDocument:
        """Transform the raw document."""

# Pipeline configuration
config.normalizers = [
    StructureNormalizer(),
    PageMapper(),
    MyCustomNormalizer(),
]
```

---

## Error Handling

### Exception Hierarchy

```python
class ScholarDocError(Exception):
    """Base exception for all ScholarDoc errors."""

class UnsupportedFormatError(ScholarDocError):
    """Raised when document format is not supported."""

class ExtractionError(ScholarDocError):
    """Raised when extraction fails."""
    
class ConfigurationError(ScholarDocError):
    """Raised for invalid configuration."""
```

### Warning System

Warnings are collected during processing and included in output:

```python
doc = scholardoc.convert("book.pdf")
for warning in doc.warnings:
    print(f"Warning: {warning}")
    
# Example warnings:
# "Page 15: Could not detect page label, using index"
# "Pages 42-45: Multi-column layout detected, merged to single column"
# "Document appears to be scanned, text quality may be poor"
```

---

## Dependencies

### Core (Required)
- `pymupdf` (fitz) - PDF parsing
- `pydantic` - Data validation (if we want validation)

### Optional (Phase 2+)
- `ebooklib` - EPUB parsing
- `pymupdf4llm` - Enhanced layout analysis
- `httpx` - GROBID client (if integrated)

### Development
- `pytest` - Testing
- `ruff` - Linting/formatting
- `uv` - Package management

---

## File Structure

```
scholardoc/
├── __init__.py           # Public API exports
├── convert.py            # Main conversion logic
├── config.py             # Configuration classes
├── models.py             # Data models
├── exceptions.py         # Exception classes
├── readers/
│   ├── __init__.py
│   ├── base.py           # BaseReader ABC
│   ├── pdf.py            # PDF reader
│   └── epub.py           # EPUB reader (Phase 3)
├── normalizers/
│   ├── __init__.py
│   ├── base.py           # BaseNormalizer ABC
│   ├── structure.py      # Heading detection
│   └── pages.py          # Page number mapping
├── writers/
│   ├── __init__.py
│   ├── markdown.py       # Markdown output
│   └── json.py           # JSON output (future)
└── utils/
    ├── __init__.py
    └── detection.py      # Format detection
```
