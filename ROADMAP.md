# ScholarDoc Roadmap

> **Status:** Planning  
> **Last Updated:** December 2025

---

## Phase Overview

```
Phase 0 (Current)    Phase 1 (MVP)        Phase 2 (Enhanced)    Phase 3 (Formats)     Phase 4 (OCR)
────────────────     ─────────────        ──────────────────    ─────────────────     ─────────────
Exploration          PDF → Markdown       Footnote extraction   EPUB support          Structure-aware OCR
Spike validation     Basic structure      Table extraction      MOBI support          Sequence models
Sample PDFs          Page numbers         Bibliography detect   Markdown passthrough  Domain-specific
Answer QUESTIONS.md  Metadata             Citation linking      Format plugins        training

[Current Focus]      [Next]               [Planned]             [Planned]             [Research]
```

---

## Phase 0: Exploration (Current)

**Goal:** Validate assumptions before committing to detailed designs.

### Why Phase 0?

We have detailed specs but haven't:
- Processed a single real PDF
- Validated PyMuPDF capabilities
- Tested heading detection approaches
- Seen what footnotes look like in practice

This phase prevents building the wrong thing.

### Deliverables

- [ ] 3-5 sample philosophy PDFs acquired
- [ ] spikes/01_pymupdf_exploration.py run on all samples
- [ ] spikes/02_library_comparison.py validates ADR-001
- [ ] spikes/03_heading_detection.py determines strategy
- [ ] spikes/04_footnote_detection.py assesses feasibility
- [ ] spikes/FINDINGS.md populated with observations
- [ ] QUESTIONS.md Q1-Q4 answered empirically
- [ ] SPEC.md updated based on findings

### Success Criteria

- We can articulate what PyMuPDF does/doesn't give us
- ADR-001 is validated (or changed) based on evidence
- We have specific examples of heading patterns in philosophy texts
- Footnote detection feasibility is determined (Phase 1 vs Phase 2)

---

## Phase 1: MVP - PDF to Markdown (Current)

**Goal:** Reliable PDF → Markdown conversion with structure and page preservation.

### Milestones

#### 1.1 Core Infrastructure
- [ ] Project setup (pyproject.toml, uv, ruff, pytest)
- [ ] Data models defined (Pydantic or dataclasses)
- [ ] Exception hierarchy
- [ ] Configuration system
- [ ] Basic test harness

#### 1.2 PDF Reader
- [ ] PyMuPDF integration
- [ ] Text block extraction with position
- [ ] Font/style information capture
- [ ] Page boundary tracking
- [ ] Multi-column handling (basic)

#### 1.3 Structure Normalization
- [ ] Heading detection (font-size based)
- [ ] Paragraph merging (across line breaks)
- [ ] Reading order detection
- [ ] Page number mapping (index ↔ label)

#### 1.4 Markdown Writer
- [ ] Basic Markdown output
- [ ] Heading hierarchy
- [ ] Page markers (configurable style)
- [ ] Metadata frontmatter (YAML)

#### 1.5 Public API
- [ ] `convert()` function
- [ ] `convert_batch()` with progress
- [ ] Configuration validation
- [ ] Warning collection

#### 1.6 Testing & Documentation
- [ ] Unit tests for each component
- [ ] Integration tests with sample PDFs
- [ ] Test corpus (philosophy texts)
- [ ] API documentation
- [ ] Usage examples

### Phase 1 Success Criteria
- Process 10 sample philosophy PDFs with >95% text accuracy
- Page numbers correct in all test documents
- Heading detection working for 80%+ of documents
- API is clean and documented
- CI/CD passing

### Open Questions for Phase 1
See QUESTIONS.md: Q1 (page format), Q2 (multi-column), Q3 (born-digital detection), Q4 (heading strategy)

---

## Phase 2: Enhanced Extraction

**Goal:** Extract scholarly apparatus (footnotes, tables, citations).

### Planned Features

#### 2.1 Footnote Extraction
- Footnote region detection (page bottom)
- Superscript marker detection
- Marker ↔ content linking
- Output options: inline, endnotes, linked

**Challenges:**
- No semantic markup in PDFs
- Requires layout analysis
- Accuracy vs. coverage tradeoff

#### 2.2 Table Extraction
- Table boundary detection
- Cell extraction and structure
- Markdown table output
- Fallback: preserve as text

#### 2.3 Bibliography Detection
- Bibliography section identification
- Reference entry parsing (best effort)
- Structured output (optional)

#### 2.4 Citation Detection
- In-text citation patterns
- Link to bibliography entries
- Multiple styles (Chicago, MLA, etc.)

### Phase 2 Dependencies
- Phase 1 complete
- PyMuPDF4LLM evaluation
- Accuracy requirements defined (see Q5)

---

## Phase 3: Format Expansion

**Goal:** Support EPUB, MOBI, and other formats.

### Planned Features

#### 3.1 EPUB Reader
- ebooklib integration
- EPUB2 and EPUB3 support
- Semantic footnotes (EPUB3 epub:type)
- Heuristic footnotes (EPUB2)
- NCX/NAV navigation preservation

#### 3.2 MOBI/AZW Support
- KindleUnpack or similar
- Conversion to EPUB internally
- DRM-free only (legal requirement)

#### 3.3 Markdown Passthrough
- Parse existing Markdown
- Apply same normalization
- Consistent output format

#### 3.4 Plugin Architecture
- Custom reader registration
- Format detection hooks
- Community contributions

### Phase 3 Dependencies
- Phase 1 complete
- EPUB landscape research (Q7)

---

## Phase 4: Structure-Aware OCR

**Goal:** Build a custom OCR system designed for scholarly documents that maintains structural context and uses sequence models for improved accuracy.

### Why Custom OCR?

Standard OCR (Tesseract, EasyOCR) treats each page as an independent image. This throws away valuable context:

- **Page numbers follow sequences** - If page 42 is followed by "4B" that's probably "43"
- **Footnote markers are sequential** - Footnote 7 followed by "B" is probably "8"
- **Chapter headings have patterns** - "Chapter I" → "Chapter II" not "Chapter 11"
- **Names recur throughout** - "Heidegger" recognized once should inform future occurrences
- **Roman numerals in front matter** - "iv" → "v" → "vi" is predictable

A structure-aware OCR can use this context to improve accuracy significantly on scholarly documents.

### Architecture Vision

```
┌─────────────────────────────────────────────────────────────────┐
│                    Structure-Aware OCR Pipeline                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ Base OCR     │───▶│ Confidence   │───▶│ Structure        │  │
│  │ (per-char)   │    │ Scores       │    │ Context          │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│                                                  │               │
│                                                  ▼               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Sequence Models                        │  │
│  │  • Page number Markov chain (Roman/Arabic/Mixed)         │  │
│  │  • Footnote marker sequence                               │  │
│  │  • Chapter/section numbering                              │  │
│  │  • Recurring proper nouns (names, places, terms)          │  │
│  │  • Language-specific patterns (Greek, German, Latin)      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 Correction & Confidence                   │  │
│  │  • Apply sequence priors to low-confidence chars          │  │
│  │  • Flag remaining uncertainty for human review            │  │
│  │  • Learn from corrections (optional feedback loop)        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Planned Features

#### 4.1 Base OCR Layer
- Tesseract or EasyOCR as foundation
- Per-character confidence scores
- Position/bounding box preservation
- Multi-column and rotation handling

#### 4.2 Page Number Sequence Model
- Detect page number regions (headers/footers)
- Model: `P(page_n | page_n-1, page_n-2, ...)`
- Handle mixed Roman/Arabic (front matter → body)
- Handle A/B scholarly pagination (Kant's Critique style)
- Correct OCR errors using sequence predictions

#### 4.3 Footnote Sequence Model
- Track footnote markers through document
- Model: `P(marker_n | marker_n-1, region_type)`
- Per-page reset vs. continuous numbering
- Superscript vs. inline detection
- Link markers to footnote content

#### 4.4 Structural Element Models
- Chapter/section numbering sequences
- List item sequences (a, b, c or i, ii, iii)
- Reference/citation numbering
- Table of contents alignment

#### 4.5 Vocabulary Priors
- Build per-document vocabulary from high-confidence OCR
- Apply vocabulary priors to low-confidence words
- Domain-specific dictionaries (philosophy, classics, theology)
- Name/proper noun persistence

#### 4.6 Multi-Language Support
- Greek character sequences (philosophy texts)
- German quotations (common in philosophy)
- Latin phrases
- Mixed-language handling

### Research Questions

These need investigation before implementation:

1. **What's the right base OCR?** Tesseract vs EasyOCR vs cloud APIs vs training custom
2. **How much does structure context actually help?** Need quantitative evaluation
3. **What confidence threshold triggers sequence correction?**
4. **How to handle documents that don't follow conventions?**
5. **Training data for scholarly document patterns?**

### Phase 4 Milestones

#### 4.1 Foundation (Research)
- [ ] Evaluate base OCR options on scanned philosophy texts
- [ ] Quantify baseline accuracy on test corpus
- [ ] Design sequence model architecture
- [ ] Create training/evaluation datasets

#### 4.2 Page Number Model (First Implementation)
- [ ] Implement page number region detection
- [ ] Build Markov chain for page sequences
- [ ] Evaluate improvement over baseline
- [ ] Handle Roman/Arabic transitions

#### 4.3 Footnote Model
- [ ] Implement footnote marker tracking
- [ ] Build footnote sequence model
- [ ] Integrate with Phase 2 footnote extraction
- [ ] Evaluate on documents with extensive footnotes

#### 4.4 Full Integration
- [ ] Vocabulary prior system
- [ ] Multi-language support
- [ ] Confidence-based human review flagging
- [ ] Performance optimization

### Dependencies

- Phase 1 complete (basic PDF pipeline)
- Phase 2 helpful (footnote extraction patterns inform model)
- Training corpus of scanned scholarly documents with ground truth
- Evaluation methodology defined

### Open Design Questions

See `docs/design/CUSTOM_OCR_DESIGN.md` (to be created) for detailed design discussion:

- Neural vs. probabilistic sequence models?
- Per-document learning vs. pre-trained models?
- How to handle confidence propagation?
- Integration with born-digital pipeline?

---

## Future Considerations (Not Planned)

These features may be considered based on user feedback:

- **Chunking strategies** - Currently out of scope; may add chunk hints
- **Vector embedding** - Not our domain
- **Web interface** - CLI only planned
- **PDF annotation extraction** - Q8
- **Image extraction/description** - Q9
- **Non-Latin script optimization** - Partially addressed in Phase 4
- **PDF editing/modification** - Different tool
- **GROBID Integration** - May add for scientific papers if demand exists
- **Scientific Paper Support** - May add specialized handling if demand exists

---

## Version Numbering

```
0.1.x - Phase 1 development
0.2.x - Phase 2 development
0.3.x - Phase 3 development
0.x.x - Pre-1.0 (API may change)
1.0.0 - Stable API, Phase 1-2 complete
```

---

## Decision Log

| Date | Decision | Rationale | ADR |
|------|----------|-----------|-----|
| Dec 2025 | Start with PDF only | Most common scholarly format, hardest to do well | - |
| Dec 2025 | Output Markdown, not JSON | Markdown is human-readable and RAG-compatible | - |
| Dec 2025 | No chunking in scope | Chunking strategies vary; downstream concern; added chunk_hints | - |
| Dec 2025 | Defer footnotes to Phase 2 | Complex feature requiring careful design | - |
| Dec 2025 | PyMuPDF as primary PDF lib | Mature, fast, well-documented | ADR-001 (pending validation) |
| Dec 2025 | Custom structure-aware OCR | Standard OCR loses sequence context; scholarly docs have predictable patterns | - |
| Dec 2025 | Exploration before implementation | Validate assumptions empirically with spikes | - |

---

## Resources

- **Test Corpus:** TBD - need sample philosophy PDFs (public domain)
- **Benchmarks:** TBD - define accuracy metrics
- **Similar Projects:** marker-pdf, pypdf, unstructured, docling
