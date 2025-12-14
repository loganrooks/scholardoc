# ScholarDoc

> **Status:** Phase 0 - Exploration (validating assumptions before implementation)  
> See [ROADMAP.md](ROADMAP.md) for development phases

Convert scholarly documents (PDF, EPUB) to structured Markdown optimized for RAG pipelines, while preserving the metadata and structure that researchers need.

## Current Status

🔬 **Phase 0: Exploration**

Before implementing, we're validating our assumptions with empirical spikes:

```bash
# Install comparison libraries
uv sync --extra comparison

# Explore what PyMuPDF gives us
uv run python spikes/01_pymupdf_exploration.py sample.pdf --all

# Compare different PDF libraries
uv run python spikes/02_library_comparison.py sample.pdf

# Test heading detection strategies
uv run python spikes/03_heading_detection.py sample.pdf

# Assess footnote detection feasibility
uv run python spikes/04_footnote_detection.py sample.pdf
```

**Why exploration first?** 

We have detailed specs (SPEC.md) but they're based on assumptions:
- "PyMuPDF is the best library" → needs validation
- "Headings can be detected by font size" → needs testing
- "Footnote detection is feasible" → needs assessment

The spikes test these assumptions on real philosophy PDFs before we commit to an architecture.

## Why ScholarDoc?

Philosophy scholars and humanities researchers need to:
- Process large bodies of philosophical texts for analysis
- Maintain page numbers for accurate citations
- Preserve document structure (chapters, sections)
- Eventually extract footnotes and references

Most PDF extraction tools are optimized for business documents or scientific papers. ScholarDoc focuses on the needs of humanities scholarship.

## What ScholarDoc Does

- **Input:** PDF files (EPUB and other formats planned)
- **Output:** Clean, structured Markdown with metadata
- **Preserves:** Page numbers, document structure, metadata

## What ScholarDoc Does NOT Do

- **Chunking:** We produce clean Markdown; chunking is a downstream concern
- **Embedding:** We output text, not vectors
- **OCR:** We handle born-digital PDFs; scanned documents may be added later

## Current Status

🚧 **Phase 1: MVP Development**

We're building the core PDF → Markdown pipeline. See:
- [REQUIREMENTS.md](REQUIREMENTS.md) - What we're building
- [SPEC.md](SPEC.md) - How we're building it
- [ROADMAP.md](ROADMAP.md) - Development phases
- [QUESTIONS.md](QUESTIONS.md) - Open design questions

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
print(doc.markdown)

# Access metadata
print(f"Title: {doc.metadata.title}")
print(f"Pages: {doc.metadata.page_count}")

# Save to file
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
```

## Contributing

This project is in early development. Before contributing:

1. Read [REQUIREMENTS.md](REQUIREMENTS.md) and [ROADMAP.md](ROADMAP.md)
2. Check [QUESTIONS.md](QUESTIONS.md) for open design questions
3. Check [SPEC.md](SPEC.md) for technical decisions
4. Open an issue to discuss before submitting PRs

## License

MIT License - see [LICENSE](LICENSE) for details.
