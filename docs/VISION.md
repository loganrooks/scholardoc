# ScholarDoc Vision

<!-- AUTHORITATIVE: All other docs should reference this section, not duplicate it -->
<!-- Last verified: 2025-12-27 -->

ScholarDoc extracts structured knowledge from scholarly PDFs into a flexible intermediate representation (`ScholarDocument`) designed for multiple downstream applications:

## Primary Applications

- **RAG pipelines** — Clean text with position-accurate metadata for retrieval
- **Anki/flashcard generation** — Structured content with citation tracking
- **Research organization** — Metadata-rich documents for knowledge management
- **Citation management** — Page numbers, references, bibliography extraction

## Additional Applications

- **Knowledge graphs** — Semantic linking between documents and concepts
- **Literature review tools** — Cross-document analysis and comparison
- **Academic writing assistants** — Source material with accurate citations
- **Accessibility** — Clean text for text-to-speech, screen readers
- **Search/indexing systems** — Structured data for advanced queries
- **Custom applications** — Extensible output formats (Markdown, JSON, custom)

## Core Insight

Separate *extraction* (getting clean, structured data) from *presentation* (formatting for specific use cases).

The `ScholarDocument` is the intermediate representation; Markdown is one output format, not the goal.

## Design Philosophy

1. **Extraction First** - Focus on getting clean, accurate, structured data from PDFs
2. **Flexible Output** - Support multiple downstream use cases through flexible intermediate representation
3. **Preserve Metadata** - Maintain page numbers, positions, citations, and document structure
4. **Quality Over Speed** - Prioritize accuracy and data quality over processing speed
5. **Graceful Degradation** - Handle imperfect OCR and varying PDF quality without hard failures
