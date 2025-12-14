# ScholarDoc Requirements

> **Status:** Draft - Gathering Requirements  
> **Last Updated:** December 2025  
> **Purpose:** Define what we're building before how we build it

---

## Vision Statement

A Python library that transforms scholarly documents (PDFs, later EPUBs) into clean, structured Markdown optimized for RAG pipelines, while preserving the metadata and structure that scholars and researchers need for citation and close reading.

**What we are NOT building (yet):**
- A chunking library (downstream concern)
- A RAG pipeline (we produce input for RAG)
- A citation manager
- An OCR solution (may integrate later)

---

## Target Users

### Primary: Philosophy Scholars & Researchers
Researchers who work with philosophical texts, need to process large bodies of work, and require preservation of scholarly apparatus for citation and reference.

### Secondary: Digital Humanities Projects
Teams building text analysis pipelines for literature, historical documents, and academic texts.

### Tertiary: RAG Application Developers
Developers who need high-quality text extraction from PDFs for embedding and retrieval systems.

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
