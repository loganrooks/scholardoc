# ScholarDoc Extensibility Design

> **Status:** Proposal
> **Created:** December 19, 2025
> **Context:** How to support different domains without over-generalizing

## The Problem

ScholarDoc started with philosophy texts, but users might want:
- Linguistics (IPA, glosses, syntax trees)
- Legal (section numbering, case citations)
- Medical (terminology, drug names)
- Technical (code blocks, equations)
- Historical (archaic spellings, manuscript conventions)

How do we support this WITHOUT:
1. Abstracting everything into meaninglessness
2. Hardcoding philosophy assumptions everywhere
3. Requiring users to understand our internals

## Solution: Domain Profiles

A **Profile** bundles domain-specific behavior:

```python
from scholardoc import load
from scholardoc.profiles import philosophy, linguistics

# Use a built-in profile
doc = load("heidegger.pdf", profile=philosophy)

# Use a different profile
doc = load("phonology_paper.pdf", profile=linguistics)

# Use the generic default
doc = load("random.pdf")  # No profile = generic scholarly
```

### What's in a Profile?

```python
@dataclass
class Profile:
    """Domain-specific configuration bundle."""

    name: str  # "philosophy", "linguistics", etc.

    # ─────────────────────────────────────────────────
    # Vocabulary
    # ─────────────────────────────────────────────────

    # Terms the spell-checker should NOT flag
    vocabulary_whitelist: set[str] = field(default_factory=set)

    # Patterns to recognize as valid (regex)
    valid_patterns: list[str] = field(default_factory=list)

    # Language hints for OCR/spell-check
    expected_languages: list[str] = field(default_factory=lambda: ["en"])

    # ─────────────────────────────────────────────────
    # Element Detection
    # ─────────────────────────────────────────────────

    # Custom element detectors (plugin system)
    element_detectors: list[ElementDetector] = field(default_factory=list)

    # Custom element types this profile adds
    custom_element_types: list[str] = field(default_factory=list)

    # ─────────────────────────────────────────────────
    # Processing Options
    # ─────────────────────────────────────────────────

    # How to handle footnotes
    footnote_mode: Literal["separate", "inline", "append"] = "separate"

    # Note source detection enabled?
    detect_note_source: bool = False

    # Special formatting detection
    detect_sous_erasure: bool = False  # Philosophy-specific
    detect_interlinear_gloss: bool = False  # Linguistics-specific

    # ─────────────────────────────────────────────────
    # Output Formatting
    # ─────────────────────────────────────────────────

    # Custom formatters for special elements
    formatters: dict[str, ElementFormatter] = field(default_factory=dict)
```

### Built-in Profiles

```python
# scholardoc/profiles/philosophy.py
philosophy = Profile(
    name="philosophy",

    vocabulary_whitelist={
        # German
        "Dasein", "Sein", "Seiendes", "Zeitlichkeit", "Aufhebung",
        # Greek (transliterated)
        "logos", "physis", "aletheia", "eidos",
        # French
        "différance", "arche-writing", "sous rature",
        # Technical
        "aporia", "apophantic", "ontic", "ontological",
        # Names
        "Heidegger", "Husserl", "Derrida", "Levinas",
    },

    expected_languages=["en", "de", "fr", "el"],

    element_detectors=[
        SousErasureDetector(),
        TranslatorNoteDetector(),
    ],

    footnote_mode="separate",  # Philosophy uses endnotes
    detect_note_source=True,   # Distinguish author/translator
    detect_sous_erasure=True,
)

# scholardoc/profiles/linguistics.py
linguistics = Profile(
    name="linguistics",

    vocabulary_whitelist={
        # IPA symbols are handled by valid_patterns
        # Grammatical abbreviations
        "NOM", "ACC", "DAT", "GEN", "PL", "SG", "PST", "PRES",
    },

    valid_patterns=[
        r"/[^/]+/",        # Phonemic: /kæt/
        r"\[[^\]]+\]",     # Phonetic: [kʰæt]
        r"\w+-\w+",        # Morpheme: walk-PAST
    ],

    expected_languages=["en"],  # But with IPA

    element_detectors=[
        InterlinearGlossDetector(),
        IPABlockDetector(),
    ],

    detect_interlinear_gloss=True,
)

# scholardoc/profiles/generic.py
generic = Profile(
    name="generic",
    # Minimal assumptions, works for any scholarly text
)
```

### Creating a Custom Profile

```python
from scholardoc import Profile
from scholardoc.detectors import ElementDetector

# Custom detector for legal citations
class LegalCitationDetector(ElementDetector):
    def detect(self, text: str, context: DetectionContext) -> list[Element]:
        # Find patterns like "42 U.S.C. § 1983"
        ...

# Create custom profile
legal = Profile(
    name="legal",

    vocabulary_whitelist={
        "plaintiff", "defendant", "amicus", "certiorari",
    },

    valid_patterns=[
        r"\d+\s+U\.S\.C\.\s+§\s+\d+",  # Federal statute
        r"\d+\s+F\.\d+d\s+\d+",         # Federal reporter
    ],

    element_detectors=[
        LegalCitationDetector(),
    ],
)

# Use it
doc = load("supreme_court_case.pdf", profile=legal)
```

---

## Element Detector Plugin System

```python
from abc import ABC, abstractmethod

class ElementDetector(ABC):
    """Base class for custom element detection."""

    @property
    @abstractmethod
    def element_type(self) -> str:
        """The element type this detector produces."""
        pass

    @abstractmethod
    def detect(self,
               page: RawPage,
               context: DetectionContext) -> list[DetectedElement]:
        """
        Detect elements in a page.

        Args:
            page: The raw page to analyze
            context: Document-level context (fonts, patterns seen, etc.)

        Returns:
            List of detected elements (may be empty)
        """
        pass

    def configure(self, config: dict) -> None:
        """Optional: configure detector with custom settings."""
        pass


@dataclass
class DetectedElement:
    """An element detected by a plugin."""
    element_type: str
    text: str
    bbox: BoundingBox
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


# Example implementation
class SousErasureDetector(ElementDetector):
    """Detect text with strikethrough (sous rature / under erasure)."""

    @property
    def element_type(self) -> str:
        return "sous_erasure"

    def detect(self, page: RawPage, context: DetectionContext) -> list[DetectedElement]:
        detected = []

        # Method 1: Look for strikethrough font flags
        for block in page.blocks:
            if block.has_strikethrough:
                detected.append(DetectedElement(
                    element_type="sous_erasure",
                    text=block.text,
                    bbox=block.bbox,
                    confidence=0.95,
                    metadata={"method": "font_flag"}
                ))

        # Method 2: Visual detection (X marks over text)
        # Would use OpenCV LSD as documented in SOUS_ERASURE_DESIGN.md

        return detected
```

---

## Chunking Strategies

### The Chunking Question

Should ScholarDoc chunk at all? Arguments both ways:

**For chunking:**
- Users want ready-to-embed output
- We know the document structure best
- Convenience is a feature

**Against chunking:**
- Chunking is a separate concern (SRP)
- Different use cases need different strategies
- LangChain/LlamaIndex already do this well

**Our approach:** Provide **practical defaults** but make it easy to use external chunkers.

### Built-in Chunking Strategies

```python
from enum import Enum

class ChunkStrategy(Enum):
    # ─────────────────────────────────────────────────
    # Structure-based (use document structure)
    # ─────────────────────────────────────────────────

    ELEMENT = "element"
    # One chunk per element (paragraph, heading, etc.)
    # Respects natural document boundaries
    # Chunks may vary widely in size

    PAGE = "page"
    # One chunk per page
    # Good for page-level citation
    # May be too large for some embedding models

    SECTION = "section"
    # Group elements by section (between headings)
    # Good semantic units
    # Sizes vary based on section length

    # ─────────────────────────────────────────────────
    # Size-based (fixed sizes)
    # ─────────────────────────────────────────────────

    FIXED_CHAR = "fixed_char"
    # Fixed character count
    # Simple, predictable
    # May break mid-sentence

    FIXED_TOKEN = "fixed_token"
    # Fixed token count (estimated)
    # Better for LLM context limits
    # Requires tokenizer

    # ─────────────────────────────────────────────────
    # Hybrid (structure + size constraints)
    # ─────────────────────────────────────────────────

    PARAGRAPH_BOUNDED = "paragraph_bounded"
    # Paragraphs, but split if > max_size
    # Merge if < min_size
    # Best of both worlds

    SECTION_BOUNDED = "section_bounded"
    # Sections, but split if > max_size
    # Keeps semantic units together when possible

    # ─────────────────────────────────────────────────
    # Semantic (embedding-based)
    # ─────────────────────────────────────────────────

    SEMANTIC = "semantic"
    # Use embeddings to find natural breakpoints
    # Chunks where meaning shifts
    # Requires embedding model (slower)


def to_rag_chunks(
    self,
    strategy: ChunkStrategy = ChunkStrategy.PARAGRAPH_BOUNDED,

    # Size constraints
    min_chunk_size: int = 100,      # Chars
    max_chunk_size: int = 1500,     # Chars
    target_chunk_size: int = 800,   # Chars (for semantic)

    # Overlap
    overlap: int = 100,             # Chars
    overlap_strategy: Literal["char", "sentence"] = "sentence",

    # Semantic chunking options
    embedding_model: str | None = None,  # For SEMANTIC strategy
    similarity_threshold: float = 0.5,   # Breakpoint threshold

    # Content options
    include_headings: bool = True,  # Prepend section heading to chunks
    include_footnotes: bool = False,

) -> Iterator[RAGChunk]:
    """Generate RAG-ready chunks with specified strategy."""
    ...
```

### What Research Says About Chunking

Based on recent RAG research (2023-2024):

| Finding | Implication |
|---------|-------------|
| Semantic chunking outperforms fixed-size by 10-20% on retrieval benchmarks | Offer semantic strategy |
| Overlap of 10-20% improves retrieval | Default overlap=100 |
| Prepending context ("In Chapter 3, Kant argues...") helps | Add `include_headings` option |
| Smaller chunks for retrieval, larger for generation | Consider hierarchical strategy |
| Chunk size should match embedding model's sweet spot | Make configurable |

### Chunking Examples

```python
doc = load("critique.pdf", profile=philosophy)

# Default: paragraph-bounded hybrid
chunks = doc.to_rag_chunks()

# For long-context models (Claude, GPT-4)
chunks = doc.to_rag_chunks(
    strategy=ChunkStrategy.SECTION_BOUNDED,
    max_chunk_size=4000,
)

# For traditional embedding models
chunks = doc.to_rag_chunks(
    strategy=ChunkStrategy.PARAGRAPH_BOUNDED,
    max_chunk_size=512,
    overlap=50,
)

# Semantic (slower but better quality)
chunks = doc.to_rag_chunks(
    strategy=ChunkStrategy.SEMANTIC,
    embedding_model="all-MiniLM-L6-v2",
    target_chunk_size=800,
)

# Use external chunker on our structured output
from langchain.text_splitter import RecursiveCharacterTextSplitter

elements = list(doc.elements)
splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
# They can chunk our clean elements however they want
```

### Custom Chunking Strategy

```python
from scholardoc.chunking import ChunkingStrategy, Chunk

class MyCustomChunker(ChunkingStrategy):
    """Custom chunking logic."""

    def chunk(self,
              elements: list[Element],
              config: ChunkConfig) -> Iterator[Chunk]:
        # Your logic here
        ...

# Register and use
doc = load("paper.pdf")
chunks = doc.to_rag_chunks(strategy=MyCustomChunker())
```

---

## Summary: Extensibility Philosophy

1. **Profiles** bundle domain-specific behavior
2. **Detectors** are plugins for finding special elements
3. **Formatters** control how elements become output
4. **Chunking strategies** are swappable, with sensible defaults
5. **Everything is optional** - the generic profile works for any scholarly text

**What stays constant:**
- `ScholarDocument` structure
- `RAGChunk` output format
- Core element types (paragraph, heading, footnote)
- Quality scoring

**What's customizable:**
- Vocabulary whitelists
- Special element detection
- Output formatting
- Chunking strategy
