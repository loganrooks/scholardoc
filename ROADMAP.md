# ScholarDoc Roadmap

> **Status:** Phase 1 In Progress
> **Last Updated:** December 23, 2025

---

## Phase Overview

```
Phase 0 ✅ DONE      Phase 0.5 ✅ DONE         Phase 1 (Next)          Phase 2 (Enhanced)
────────────────     ──────────────────────    ─────────────────────   ──────────────────
Exploration          ToC detection spike       Core representation     Footnote extraction
Spike validation     PDF outline evaluation    Structure extraction    Table extraction
Sample PDFs          Structure fusion test     Quality filtering       Bibliography detect
Answer QUESTIONS.md  Profile detection test    Document profiles       Citation linking
OCR quality study    Design validation         Cascading extraction    Feedback system
Design decisions     Architecture revision     Position annotations    Cross-doc learning

[Complete ✅]        [Complete ✅]             [Build Core]            [Enhance]


Phase 3 (Formats)     Phase 4 (OCR)
─────────────────     ─────────────
EPUB support          Structure-aware OCR
MOBI support          Sequence models
Markdown passthrough  Domain-specific
Format plugins        training

[Planned]             [Research]
```

---

## Phase 0: Exploration ✅ COMPLETE

**Goal:** Validate assumptions before committing to detailed designs.
**Status:** ✅ Complete (December 18, 2025)
**Summary:** All exploration spikes completed. Key assumptions validated. Ready for Phase 1.

### Deliverables

- [x] 3-5 sample philosophy PDFs acquired (10+ PDFs: Comay, Derrida, Kant, Heidegger, Lenin)
- [x] spikes/01_pymupdf_exploration.py run on all samples
- [x] spikes/02_library_comparison.py validates ADR-001 (PyMuPDF 32-57x faster)
- [x] spikes/03_heading_detection.py determines strategy (combined method, conf ≥0.6)
- [x] spikes/04_footnote_detection.py assesses feasibility (defer to Phase 2 - endnotes)
- [x] spikes/05_ocr_quality_survey.py evaluates text layers
- [x] spikes/08_embedding_robustness.py tests RAG impact (CRITICAL: OCR errors hurt)
- [x] spikes/09_trocr_reocr.py compares re-OCR vs correction (correction wins)
- [x] spikes/06c_real_ground_truth.py extracts verified OCR error pairs
- [x] spikes/10_tesseract_reocr.py compares OCR engines (docTR best for scans)
- [x] spikes/11_rag_chunk_quality.py tests artifact impact (page numbers -29%)
- [x] spikes/12_smart_spellcheck.py tests auto-detection of skip words
- [x] spikes/13_spellcheck_risk.py quantifies correction risks (41% damage rate)
- [x] spikes/14-19_ground_truth_collection.py builds OCR quality ground truth
- [x] spikes/FINDINGS.md populated with observations
- [x] QUESTIONS.md Q1-Q6, Q14, Q16 answered empirically
- [x] SPEC.md updated based on findings
- [x] zlibrary-mcp RAG pipeline analyzed for reusable components
- [x] Test PDFs and ground truth copied from zlibrary-mcp

### Success Criteria ✅ All Met

- ✅ We can articulate what PyMuPDF does/doesn't give us
- ✅ ADR-001 is validated based on evidence (PyMuPDF confirmed)
- ✅ We have specific examples of heading patterns in philosophy texts
- ✅ Footnote detection feasibility determined (Phase 2 - philosophy uses endnotes)
- ✅ OCR quality impact on RAG understood (character errors are devastating)
- ✅ OCR correction module implemented (`scholardoc/normalizers/ocr_correction.py`)

### Key Findings Summary

| Finding | Impact |
|---------|--------|
| Philosophy texts use endnotes | Defer footnote linking to Phase 2 |
| OCR character errors hurt RAG | Add quality assessment + correction |
| Existing OCR + correction > re-OCR | Use spell-check, not TrOCR |
| Mid-word caps don't hurt embeddings | Only real misspellings matter |
| PyMuPDF provides page labels | Use labels, not indices |
| Combined heading detection works | Confidence threshold ≥0.6 |
| docTR best for scanned PDFs | 3-5% RAG improvement over existing OCR |
| Page numbers devastate embeddings | -29% similarity; must remove before embedding |
| Auto spell-check damages 41% of terms | Use fuzzy retrieval instead of correction |
| Ground truth: 1,991 pages classified | 10 philosophy texts with GOOD/MARGINAL/BAD labels |

### Assets Acquired

- **Test PDFs:** 14 files (10 full books + 4 targeted snippets)
- **Ground Truth:** schema_v3.json, footnote JSON files from zlibrary-mcp
- **OCR Quality Ground Truth:** 1,991 pages classified (GOOD/MARGINAL/BAD) across 10 philosophy texts
- **OCR Correction Module:** Implemented with philosophy vocabulary whitelist
- **Reusable Patterns:** Data models, quality detection from zlibrary-mcp

---

## Phase 0.5: Structure Validation ✅ COMPLETE

**Goal:** Validate structure extraction design before full implementation.
**Status:** ✅ Complete (December 22, 2025)
**Summary:** Critical finding - probabilistic fusion invalidated. Architecture revised to cascading with confidence.

### Spike Results

#### 24_toc_detection.py ✅
- ToC pages detected in 58% of PDFs (7/12)
- Parsing fragile: many ToCs detected but not parsed (0-7 entries typical)
- Exception: Lenin text had 41 entries (well-structured ToC)
- Format breakdown: 4 dotted_leaders, 1 simple_list, 2 none

**Findings:**
- ToC detection works but parsing needs improvement
- Format diversity requires multiple parsing strategies
- ToC useful for title enrichment, not primary structure source

#### 25_pdf_outline_quality.py ✅
- PDF outlines present in 58% of PDFs (7/12)
- Average 36.3 entries when present
- Low page coverage: 6.5% average (major sections only)
- Title match rate: 75-100% (high accuracy when present)

**Findings:**
- PDF outlines are high confidence (0.95) when available
- Cover chapter-level structure, not subsections
- Use as primary source, supplement with heading detection

#### 26_structure_fusion.py ✅ CRITICAL
- **Only 21% agreement between sources** (outline vs heading detection)
- Outline tends to capture major chapters
- Heading detection captures visual outliers (may be false positives)
- ToC rarely agrees with either

**Findings:**
- ❌ Probabilistic fusion as designed would NOT help
- Sources capture different things, not same structure differently
- Recommendation: **Cascading with confidence, not fusion**

#### 27_document_profile_detection.py ✅
- 100% accuracy on test set (10/10 books correctly identified)
- Strong indicators: page count >100, ToC, PDF outline, chapter markers
- Auto-detection reliable for books

**Limitations:**
- Test set is all books - no articles/essays/reports to validate
- Need diverse test corpus for full validation

### Success Criteria Results

- [x] ToC parsing evaluated (works on 58%, but parsing fragile)
- [x] PDF outline extraction documented (58% have outlines, 6.5% coverage)
- [x] Source agreement measured: **21% - fusion does NOT help**
- [x] Profile detection accuracy: 100% on books (needs diverse test set)
- [x] Design docs updated: **Architecture revised**

### Architecture Revision

**Original Design (Invalidated):**
```
Probabilistic Fusion: weight(outline)*0.9 + weight(toc)*0.7 + weight(heading)*0.5
```

**Revised Design (Spike-Validated):**
```
Structure Extraction (Cascading with Confidence):
├── Primary: PDF Outline (when available, 0.95 confidence)
├── Secondary: Heading Detection (always available, 0.5-0.8 confidence)
├── Enrichment: ToC Parser (title correction only)
└── Fallback: Paragraph boundaries (when no structure found)
```

**Key Changes:**
1. No probabilistic fusion - sources don't agree enough (21%)
2. PDF outline is primary when present (high confidence)
3. Heading detection supplements for subsections only
4. ToC used for title enrichment, not section creation

---

## Phase 1: Core Representation & Structure (Current)

**Goal:** Build the canonical data representation and structure extraction system.
**Status:** In progress - PDF reader done, OCR pipeline validated, structure extraction in progress

**Design Documents:**
- [CORE_REPRESENTATION.md](docs/design/CORE_REPRESENTATION.md) - Data structures
- [STRUCTURE_EXTRACTION.md](docs/design/STRUCTURE_EXTRACTION.md) - Probabilistic extraction
- [QUALITY_FILTERING.md](docs/design/QUALITY_FILTERING.md) - OCR quality assessment

**Architecture Decision Records:**
- [ADR-002](docs/adr/ADR-002-ocr-pipeline-architecture.md) - OCR pipeline (spellcheck as selector)
- [ADR-003](docs/adr/ADR-003-line-break-detection.md) - Line-break detection (block filtering)

### Milestones

#### 1.1 Core Infrastructure ✅ COMPLETE
- [x] Project setup (pyproject.toml, uv, ruff, pytest)
- [x] Exception hierarchy (basic)
- [x] Configuration system (basic)
- [x] Basic test harness (199 tests passing)

#### 1.2 Core Data Model (Partial)
- [x] `RawDocument`, `RawPage`, `TextBlock` dataclasses
- [x] `PageLabel` for scholarly pagination (roman, arabic)
- [x] `DocumentMetadata` with basic fields
- [ ] `ScholarDocument` with clean text + position annotations
- [ ] `FootnoteRef`, `CitationRef`, `CrossRef` annotation types
- [ ] `PageSpan`, `SectionSpan`, `ParagraphSpan` structural spans
- [ ] `Note`, `ToCEntry`, `TableOfContents` content types
- [ ] JSON serialization (.scholardoc format)
- [ ] SQLite serialization (.scholardb for large docs)

#### 1.3 PDF Reader ✅ COMPLETE
- [x] PyMuPDF integration (`scholardoc/readers/pdf_reader.py`)
- [x] Text block extraction with position
- [x] Font/style information capture
- [x] Page boundary tracking with labels
- [x] PDF outline/bookmark extraction
- [x] Document type detection (book, article, essay)
- [ ] Multi-column handling (basic) - deferred

#### 1.4 Structure Extraction (Partial)
- [x] `CandidateSource` abstract interface
- [x] `PDFOutlineSource` - extract from PDF bookmarks (PRIMARY, conf=0.95)
- [x] `HeadingDetectionSource` - statistical outlier detection (SECONDARY)
- [x] `CascadingExtractor` strategy (validated: fusion invalidated by 21% agreement)
- [ ] `ToCParserSource` - detect and parse ToC (ENRICHMENT - title correction only)
- [ ] `NoOverlapValidator`, `HierarchyValidator` rules
- [ ] `StructureExtractor` orchestrator with fallback chain

#### 1.5 Document Profiles (Partial)
- [x] Document type detection (100% accuracy on books)
- [x] `estimate_document_type()` method on PDF reader
- [ ] `DocumentProfile` configuration dataclass
- [ ] Profile-specific extraction settings
- [ ] Auto-detection with confidence scores

#### 1.6 Quality Filtering ✅ VALIDATED (ADR-002, ADR-003)
- [x] OCR quality assessment - 99.2% detection rate validated
- [x] Page quality scoring (GOOD/MARGINAL/BAD) - ground truth complete
- [x] Spellcheck as selector for re-OCR (not auto-correct) - ADR-002
- [x] Line-break rejoining with block filtering - ADR-003
- [x] Adaptive dictionary with morphological validation
- [x] Pipeline design validated (`spikes/29_ocr_pipeline_design.py`)
- [ ] Integration into main module (next step)

#### 1.7 Query Methods
- [ ] `text_range()`, `annotations_in_range()`
- [ ] `page_for_position()`, `section_for_position()`
- [ ] `footnotes_in_range()`, `citations_in_range()`
- [ ] `to_markdown()`, `to_plain_text()`
- [ ] `to_rag_chunks()` with `ChunkStrategy`

#### 1.8 Testing & Documentation
- [ ] Unit tests for each component
- [ ] Integration tests with sample PDFs
- [ ] Test corpus (philosophy texts)
- [ ] API documentation
- [ ] Usage examples

### Phase 1 Success Criteria
- `ScholarDocument` correctly represents all annotation types
- Structure extraction works on books, articles, and essays
- Document profiles auto-detected with >80% accuracy
- Quality filtering identifies pages needing re-OCR
- Process 10 sample philosophy PDFs with >95% structure accuracy
- API is clean and documented

### Key Decisions for Phase 1
- **Clean text + position annotations** (not artifacts in text)
- **Cascading extraction** (outline → heading → fallback; fusion invalidated by 21% agreement)
- **Flag for re-OCR, don't auto-correct** (41% damage rate from auto-correction)
- **Document profiles** (extensible to all PDF types, 100% accuracy on books)

---

## Phase 2: Enhanced Extraction & Learning

**Goal:** Extract scholarly apparatus and implement feedback-driven learning.

**Design Documents:**
- [FEEDBACK_SYSTEM.md](docs/design/FEEDBACK_SYSTEM.md) - Correction logging and learning

### Planned Features

#### 2.1 Footnote/Endnote Extraction
- Footnote region detection (page bottom)
- Endnote section identification (philosophy uses endnotes)
- Superscript marker detection
- Marker ↔ content linking via position annotations
- Output options: inline, collected, linked

**Challenges:**
- No semantic markup in PDFs
- Requires layout analysis
- Accuracy vs. coverage tradeoff

#### 2.2 Table Extraction
- Table boundary detection
- Cell extraction and structure
- Position annotations for table spans
- Fallback: preserve as text

#### 2.3 Bibliography Detection
- Bibliography section identification
- Reference entry parsing (best effort)
- `BibEntry` structured output
- Link to `CitationRef` annotations

#### 2.4 Citation Detection
- In-text citation patterns
- `CitationRef` with parsed structure
- Link to bibliography entries
- Multiple styles (Chicago, MLA, etc.)

#### 2.5 Feedback System (NEW)
- `FeedbackLog` - persistent correction storage
- `StructureCorrection` - track structure mistakes
- `AnnotationCorrection` - track footnote/citation mistakes
- `QualityCorrection` - track quality assessment mistakes
- JSON Lines storage format

#### 2.6 Pattern Library (NEW)
- `PatternLibrary` - learn from corrections
- `LearnedPattern` - regex + formatting hints
- Cross-document pattern generalization
- Confidence scoring for learned patterns

#### 2.7 Cross-Document Learning (NEW)
- `CrossDocumentLearner` - find common patterns
- Cluster similar corrections
- Generalize to new documents
- Privacy-safe export (patterns without content)

#### 2.8 Human Review Integration
- `FeedbackCollector` - UI integration helper
- Pending corrections queue
- Batch commit workflow
- Correction audit trail

### Phase 2 Success Criteria
- Footnote/endnote linking works on 80%+ of test documents
- Citations parsed and linked to bibliography
- Feedback system captures human corrections
- Pattern library improves accuracy over time
- Cross-document learning demonstrates improvement

### Phase 2 Dependencies
- Phase 1 complete (core representation, structure extraction)
- Ground truth dataset for footnote/citation testing
- Human review workflow defined

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
| Dec 2025 | PyMuPDF as primary PDF lib | Mature, fast, well-documented | ADR-001 ✅ validated |
| Dec 2025 | Custom structure-aware OCR | Standard OCR loses sequence context; scholarly docs have predictable patterns | - |
| Dec 2025 | Exploration before implementation | Validate assumptions empirically with spikes | - |
| Dec 18, 2025 | Use existing OCR + spell correction over re-OCR | Spike 08-09: spell-check correction produces better embeddings than TrOCR | - |
| Dec 18, 2025 | Add quality assessment to pipeline | Spike 08: OCR character errors devastate RAG similarity (0.5-0.6) | - |
| Dec 18, 2025 | Philosophy uses endnotes, not footnotes | Spike 04: tested books have notes at back; defer linking to Phase 2 | - |
| Dec 18, 2025 | Combined heading detection with conf ≥0.6 | Spike 03: best accuracy across different document styles | - |
| Dec 18, 2025 | Reuse zlibrary-mcp patterns | Analysis: mature codebase with same domain focus; adopt data models | - |
| Dec 21, 2025 | Remove artifacts before embedding | Spike 11: page numbers cause -29% embedding similarity loss | - |
| Dec 21, 2025 | Use fuzzy retrieval, not spell-correction | Spike 13: auto-correction damages 41% of philosophy terms | - |
| Dec 21, 2025 | OCR quality ground truth complete | Spikes 14-19: 1,991 pages classified for training/evaluation | - |
| Dec 22, 2025 | Clean text + position annotations | Artifacts removed from text, positions recorded; ready for embedding | CORE_REPRESENTATION.md |
| Dec 22, 2025 | Common methods on class, niche exports external | Balance utility vs bloat; to_markdown, to_rag_chunks on class | CORE_REPRESENTATION.md |
| Dec 22, 2025 | Probabilistic structure extraction | Multiple sources (outline, ToC, heading detection) with confidence fusion | STRUCTURE_EXTRACTION.md |
| Dec 22, 2025 | Document profiles for extensibility | Handle books, articles, essays, reports with different source configs | STRUCTURE_EXTRACTION.md |
| Dec 22, 2025 | Unsupervised heading detection | Statistical outlier analysis (font size, bold, whitespace) | STRUCTURE_EXTRACTION.md |
| Dec 22, 2025 | Feedback logging for learning | Track human corrections, learn patterns, improve over time | FEEDBACK_SYSTEM.md |
| Dec 22, 2025 | Cross-document pattern library | Generalize heading patterns across documents | FEEDBACK_SYSTEM.md |
| Dec 22, 2025 | Flag for re-OCR, don't auto-correct | 41% damage rate from auto-correction; use neural re-OCR on flagged pages | QUALITY_FILTERING.md |
| Dec 22, 2025 | Support all PDF document types | Extensible profiles, graceful degradation, not just scholarly | STRUCTURE_EXTRACTION.md |
| Dec 22, 2025 | Cascading extraction over fusion | Spike 26: only 21% source agreement - fusion adds noise not signal | ROADMAP Phase 0.5 |
| Dec 22, 2025 | PDF outline as primary source | Spike 25: 58% availability, 0.95 confidence when present, high title match | ROADMAP Phase 0.5 |
| Dec 22, 2025 | ToC for enrichment only | Spike 24: detection works (58%) but parsing fragile; use for title correction | ROADMAP Phase 0.5 |
| Dec 22, 2025 | Heading detection as secondary | Spike 26: captures subsections that outline misses, 0.5-0.8 confidence | ROADMAP Phase 0.5 |
| Dec 22, 2025 | Book profile detection validated | Spike 27: 100% accuracy on books; need diverse test set for other types | ROADMAP Phase 0.5 |
| Dec 23, 2025 | Spellcheck as selector, not corrector | Spikes 28-30: 99.2% detection, flags for re-OCR instead of auto-correct | ADR-002 |
| Dec 23, 2025 | Line-level re-OCR, not word-level | Neural OCR needs visual context; word crops fail | ADR-002 |
| Dec 23, 2025 | Block-based line-break filtering | PyMuPDF blocks distinguish margins from text; prevents false matches | ADR-003 |
| Dec 23, 2025 | Adaptive dictionary with safeguards | Learn vocabulary with frequency thresholds, morphological validation | ADR-002 |
| Dec 23, 2025 | Validation framework established | 130 error pairs, 77 correct words; test before optimizing | Spike 30 |

---

## Resources

- **Test Corpus:** TBD - need sample philosophy PDFs (public domain)
- **Benchmarks:** TBD - define accuracy metrics
- **Similar Projects:** marker-pdf, pypdf, unstructured, docling
