# ScholarDoc Requirements

> **Status:** Active Development (Phase 1)
> **Last Updated:** December 2025
> **Vision:** See [CLAUDE.md#Vision](CLAUDE.md#vision) for authoritative project vision

---

## Vision Summary

<!-- Reference: Full vision in CLAUDE.md#Vision -->

ScholarDoc extracts structured knowledge from scholarly PDFs into a flexible intermediate representation (`ScholarDocument`) designed for multiple downstream applications.

**Core insight:** Separate *extraction* from *presentation*. `ScholarDocument` is the intermediate representation; specific output formats serve specific applications.

**What we ARE building:**
- Flexible data model (`ScholarDocument`) for structured scholarly content
- Multiple export methods: `to_markdown()`, `to_rag_chunks()`, `to_dict()`, etc.
- Clean text with position-accurate metadata (page numbers, sections, citations)
- Extensible architecture for new input formats and output writers

**What we are NOT building:**
- A single-purpose Markdown converter (we support multiple outputs)
- A full RAG pipeline (we produce optimized input for RAG)
- A chunking-only library (chunking is one feature, not the purpose)

---

## Target Applications

### RAG Pipelines
Clean text with metadata for retrieval-augmented generation systems.

### Anki / Flashcard Generation
Structured content with citation tracking for spaced repetition learning.

### Research Organization Tools
Metadata-rich documents for personal knowledge management systems.

### Citation Management
Page numbers, references, and bibliography extraction for academic writing.

### Knowledge Graphs
Semantic linking between documents, concepts, and cross-references.

### Literature Review Tools
Cross-document analysis and comparison for systematic reviews.

### Additional Applications
Academic writing assistants, accessibility tools, search/indexing systems, custom applications via extensible output formats.

---

## Target Users

### Primary: Philosophy Scholars & Researchers
Researchers who work with philosophical texts, need to process large bodies of work, and require preservation of scholarly apparatus for citation and reference.

### Secondary: Digital Humanities Projects
Teams building text analysis pipelines for literature, historical documents, and academic texts.

### Tertiary: Application Developers
Developers building RAG systems, Anki integrations, research tools, or custom applications that consume structured scholarly content.

---

## User Stories - Phase 1 (PDF → Markdown)

### US-1: Basic PDF Text Extraction
**As a** researcher  
**I want to** convert a PDF to Markdown  
**So that** I can use the text in my RAG pipeline

**Acceptance Criteria:**
- [ ] Given a born-digital PDF, output clean Markdown text
- [ ] Preserve paragraph structure (not just line breaks)
- [ ] Handle multi-column layouts appropriately
- [ ] Output valid Markdown that renders correctly

### US-2: Page Number Preservation
**As a** scholar  
**I want to** know which page each piece of text came from  
**So that** I can cite sources correctly in my research

**Acceptance Criteria:**
- [ ] Include page number metadata in output
- [ ] Support both PDF page index (0-based) and printed page number (may differ)
- [ ] Handle front matter with roman numerals (i, ii, iii, xiv)
- [ ] Allow page numbers to appear as inline markers OR separate metadata

### US-3: Document Structure Preservation  
**As a** researcher  
**I want to** preserve chapter/section hierarchy  
**So that** I can navigate and reference the document structure

**Acceptance Criteria:**
- [ ] Detect and preserve heading hierarchy (H1, H2, H3)
- [ ] Maintain chapter/section titles
- [ ] Preserve reading order (handle multi-column correctly)
- [ ] Include table of contents if present in source

### US-4: Metadata Extraction
**As a** developer  
**I want to** extract document metadata  
**So that** I can index and organize processed documents

**Acceptance Criteria:**
- [ ] Extract title, author(s), publication date when available
- [ ] Extract ISBN, DOI if present
- [ ] Preserve custom metadata from PDF
- [ ] Output metadata as frontmatter YAML or separate JSON

### US-5: Batch Processing
**As a** project lead  
**I want to** process multiple PDFs at once  
**So that** I can build a corpus efficiently

**Acceptance Criteria:**
- [ ] Process a directory of PDFs
- [ ] Report progress and errors per file
- [ ] Continue processing if one file fails
- [ ] Generate manifest of processed files

### US-6: Configurable Output
**As a** developer  
**I want to** customize the Markdown output format  
**So that** it fits my pipeline's needs

**Acceptance Criteria:**
- [ ] Option to include/exclude page markers
- [ ] Option for page marker style (inline, comment, none)
- [ ] Option to flatten or preserve heading hierarchy
- [ ] Option to include/exclude metadata frontmatter

---

## User Stories - Phase 2 (Enhanced Extraction)

### US-7: Footnote Detection (Planned)
**As a** philosophy scholar  
**I want to** have footnotes clearly marked and linked  
**So that** I can follow references in the text

**Notes:** This is complex. PDFs don't have semantic footnote markup. Requires:
- Layout analysis to detect footnote regions
- Superscript/marker detection
- Linking markers to note content

**Open Question:** How accurate can we be? What's acceptable accuracy?

### US-8: Bibliography Extraction (Planned)
**As a** researcher  
**I want to** extract the bibliography as structured data  
**So that** I can link citations to references

### US-9: Table Extraction (Planned)
**As a** researcher  
**I want to** preserve tables in a usable format  
**So that** tabular data isn't lost

---

## User Stories - Phase 3 (Format Expansion)

### US-10: EPUB Support
**As a** literature researcher  
**I want to** process EPUB files  
**So that** I can work with ebooks in my corpus

**Notes:** EPUB is easier than PDF - it's structured HTML/XML internally.

### US-11: MOBI/AZW Support (Future)
**As a** researcher  
**I want to** process Kindle format books  
**So that** I can include ebooks from my Kindle library

### US-12: Markdown Passthrough (Future)
**As a** developer  
**I want to** process Markdown files through the same pipeline  
**So that** I have consistent output regardless of input format

---

## Non-Functional Requirements

### NFR-1: Performance
- Process a 500-page PDF in under 60 seconds (born-digital)
- Memory usage should not exceed 2x file size for typical documents

### NFR-2: Error Handling
- Never crash on malformed input
- Provide meaningful error messages
- Partial extraction better than no extraction (graceful degradation)

### NFR-3: Extensibility
- Plugin architecture for new input formats
- Configurable extraction pipeline
- Hooks for custom post-processing

### NFR-4: Reliability
- Deterministic output (same input → same output)
- No external API dependencies for core functionality
- Optional integrations (GROBID, OCR) clearly separated

---

## Out of Scope (Explicit)

1. **Chunking** - This library produces clean Markdown. Chunking for RAG is a separate concern with its own strategies.

2. **Embedding generation** - We output text, not vectors.

3. **OCR for scanned PDFs** - May integrate later as optional dependency, but core library handles born-digital only.

4. **Scientific paper parsing** - GROBID handles this well. We may integrate or complement, not compete.

5. **Real-time processing** - Batch-oriented, not streaming.

---

## Success Metrics

1. **Extraction Quality:** >95% of text correctly extracted from test corpus
2. **Structure Preservation:** Headings correctly identified in >90% of documents
3. **Page Accuracy:** Page numbers correct in >99% of cases
4. **Adoption:** Library usable in 3+ internal projects
