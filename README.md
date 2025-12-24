# ScholarDoc

> **Status:** Phase 1 - Core Implementation (OCR pipeline integration)
> See [ROADMAP.md](ROADMAP.md) for development phases

<!-- Vision reference: See CLAUDE.md#Vision for authoritative description -->

**ScholarDoc** extracts structured knowledge from scholarly PDFs into a flexible intermediate representation designed for multiple downstream applications.

## What is ScholarDoc?

> For the full vision statement, see [CLAUDE.md#Vision](CLAUDE.md#vision).

In brief: Extract structured knowledge from scholarly PDFs for RAG pipelines, Anki flashcards, research organization, citation management, knowledge graphs, and more.

**Core insight:** Separate *extraction* (structured data) from *presentation* (output format). The `ScholarDocument` is the intermediate representation; Markdown is one output, not the goal.

## Why ScholarDoc?

Philosophy scholars and humanities researchers need to:
- Process large bodies of philosophical texts for analysis
- Maintain page numbers for accurate citations
- Preserve document structure (chapters, sections)
- Extract footnotes, references, and bibliographies

Most PDF extraction tools are optimized for business documents or scientific papers. ScholarDoc focuses on the needs of humanities scholarship, producing a flexible data structure that powers multiple applications.

## What ScholarDoc Does

- **Input:** PDF files (EPUB and other formats planned)
- **Output:** `ScholarDocument` — flexible intermediate representation
- **Exports:** Markdown, JSON, RAG chunks, plain text (extensible)
- **Preserves:** Page numbers, document structure, metadata, citations

## What ScholarDoc Does NOT Do

- **Chunking:** We provide `to_rag_chunks()` but chunking strategies are configurable
- **Embedding:** We output structured text, not vectors
- **OCR:** We enhance existing OCR; full scanned document support is Phase 4

## Current Status

🔧 **Phase 1: Core Implementation**

Building the core extraction pipeline with OCR enhancement. See:
- [CLAUDE.md](CLAUDE.md) - Project context and AI assistant instructions
- [REQUIREMENTS.md](REQUIREMENTS.md) - What we're building
- [SPEC.md](SPEC.md) - How we're building it
- [ROADMAP.md](ROADMAP.md) - Development phases

## Installation

```bash
# Not yet published - install from source
git clone https://github.com/yourusername/scholardoc
cd scholardoc
uv sync
```

## Usage (Planned API)

```python
import scholardoc

# Convert a single PDF
doc = scholardoc.convert("kant_critique.pdf")

# Access the structured document
print(doc.text)  # Clean text with artifacts removed
print(doc.pages)  # Page spans with positions

# Export to different formats
markdown = doc.to_markdown()
chunks = doc.to_rag_chunks(strategy="semantic")
data = doc.to_dict()  # JSON-serializable

# Access metadata
print(f"Title: {doc.metadata.title}")
print(f"Pages: {doc.metadata.page_count}")

# Save outputs
doc.save("output.md")
```

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .

# Run exploration spikes
uv run python spikes/01_pymupdf_exploration.py sample.pdf --all
```

## Contributing

This project is in active development. Before contributing:

1. Read [CLAUDE.md](CLAUDE.md) for project vision and context
2. Check [ROADMAP.md](ROADMAP.md) for current phase
3. Review [SPEC.md](SPEC.md) for technical decisions
4. Open an issue to discuss before submitting PRs

## License

MIT License - see [LICENSE](LICENSE) for details.
