# Spike Findings

> **Purpose:** Document what we learn from exploration before committing to designs
> **Status:** ✅ Initial exploration complete (December 15, 2025)

---

## Sample PDFs Used

| Document | Type | Pages | Size | Born-Digital | Page Labels |
|----------|------|-------|------|--------------|-------------|
| Comay - Mourning Sickness | Modern monograph | 225 | 1.6MB | ✅ Yes | ❌ None |
| Derrida - Writing & Difference | Translated philosophy | 472 | 1.7MB | ✅ Yes | ✅ Roman + Arabic |
| Kant - Critique of Judgment | OCR'd scan (Hackett) | 685 | 16MB | ❌ Scanned | ✅ Roman + Arabic |
| Heidegger - Being and Time | Mixed (images + text) | 590 | 14MB | ✅ Mostly | TBD |
| Heidegger - Discourse on Thinking | Born-digital | 49 | 35MB | ✅ Yes | ❌ None |
| + 5 more Derrida/Heidegger volumes | Various | - | - | - | - |

**Collection Characteristics:**
- Continental philosophy focus (Hegel, Kant, Heidegger, Derrida)
- Mix of born-digital and OCR'd scans
- Single-column layouts
- Endnotes (not footnotes) predominate

---

## Spike Overview

| Spike | Purpose | Key Questions |
|-------|---------|---------------|
| 01_pymupdf_exploration | Understand PyMuPDF output | Block structure, font info, page labels |
| 02_library_comparison | Compare PDF libraries | Which gives best extraction? Speed? Features? |
| 03_heading_detection | Test heading strategies | Font size? Bold? Position? Combined? |
| 04_footnote_detection | Test footnote strategies | Feasible? Which approach? Phase 1 or 2? |
| 05_ocr_quality_survey | Evaluate existing OCR | How bad is it? Need custom OCR? |
| 06_ground_truth | Build evaluation corpus | Parallel texts, annotation tools, validation |
| 07_annotation_review | Claude + Human workflow | Hybrid annotation, review interface, stats |

---

## Running the Spikes

```bash
# Install all comparison libraries
uv add pymupdf pdfplumber pypdf pymupdf4llm

# PDF analysis spikes
uv run python spikes/01_pymupdf_exploration.py sample.pdf --all
uv run python spikes/02_library_comparison.py sample.pdf
uv run python spikes/03_heading_detection.py sample.pdf
uv run python spikes/04_footnote_detection.py sample.pdf
uv run python spikes/05_ocr_quality_survey.py sample.pdf --detailed

# Ground truth tools
uv run python spikes/06_ground_truth.py download-gutenberg 4280 kant.txt
uv run python spikes/06_ground_truth.py compare sample.pdf kant.txt
uv run python spikes/06_ground_truth.py annotate-pages sample.pdf

# Claude + Human annotation workflow
# Step 1: Use Claude agent to generate annotations
#   /project:annotate sample.pdf annotations.yaml
# Step 2: Human review
uv run python spikes/07_annotation_review.py review annotations.yaml --pdf sample.pdf
# Step 3: Validate
uv run python spikes/07_annotation_review.py validate annotations.yaml
# Step 4: Corpus stats
uv run python spikes/07_annotation_review.py stats ground_truth/*.yaml
```

---

## Spike 01: PyMuPDF Exploration

**Run:** `uv run python spikes/01_pymupdf_exploration.py <pdf> [--fonts|--layout|--quality|--all]`

### Results: Comay - Mourning Sickness

**Structure observations:**
- 225 pages, PDF 1.4 format
- Created with iTextSharp (born-digital)
- No embedded page labels

**Font patterns:**
- Body font: AGaramond-Regular, 11.0pt (31.2% of text)
- Heading fonts: AGaramond-Regular 14.0pt, AGaramond-Semibold 20.0pt
- Footnote markers: AGaramond-Regular 6.4pt superscript

**Layout:**
- Single column throughout
- 97% pages have text, 4% have images (mostly covers)

**Quality:**
- ✅ Born-digital with excellent text extraction
- 552K characters total, avg 2,454 chars/page

### Results: Derrida - Writing and Difference

**Structure observations:**
- 472 pages, PDF 1.6 format
- **Has proper page labels**: "Cover", "i", "ii", "iii"... "1", "2", etc.
- Full metadata (title, author, subject, keywords)

**Font patterns:**
- Body font: JoannaMT, 10.0pt (57.1%)
- Chapter headings: ScalaSans-Bold, 18.0pt (ALL CAPS)
- Footnote markers: JoannaMT 6.0pt superscript

**Layout:**
- Single column
- 100% pages have text

**Quality:**
- ✅ Born-digital with excellent extraction
- 1.1M characters total

### Results: Kant - Critique of Judgment (OCR'd Scan)

**Structure observations:**
- 685 pages, PDF 1.6 format
- **Adobe Paper Capture Plug-in** = OCR'd from scan
- Has page labels: "Cover", "iii", "iv"...
- Every page has IMAGE block (scan) + TEXT blocks (OCR overlay)

**Font patterns:**
- Mostly Times-Roman variants (from OCR recognition)
- Variable sizes due to OCR inconsistency
- 243 embedded fonts (OCR artifact)

**Layout:**
- Single column
- Pages have image + text overlay

**Quality:**
- OCR'd scan with usable text layer
- 1.66M characters total, 99% pages have text

---

## Spike 02: Library Comparison

**Run:** `uv run python spikes/02_library_comparison.py <pdf>`

### Results: Comay (Born-Digital)

| Library | Time | Chars | Font | Pos | Labels |
|---------|------|-------|------|-----|--------|
| pymupdf | **0.64s** | 560,941 | ✅ | ✅ | ❌ |
| pdfplumber | 36.27s | 554,500 | ✅ | ✅ | ❌ |
| pypdf | 9.88s | 565,476 | ❌ | ❌ | ❌ |
| pymupdf4llm | 31.50s | 559,620 | ❌ | ❌ | ❌ |

### Results: Kant (OCR'd Scan)

| Library | Time | Chars | Font | Pos | Labels |
|---------|------|-------|------|-----|--------|
| pymupdf | **3.69s** | 1,660,004 | ✅ | ✅ | ✅ |
| pdfplumber | 118.90s | 1,625,824 | ✅ | ✅ | ❌ |
| pypdf | 31.91s | 1,656,331 | ❌ | ❌ | ❌ |
| pymupdf4llm | 143.80s | 1,650,215 | ❌ | ❌ | ❌ |

### Key Findings

**Best text quality:** pypdf extracts most chars but has word boundary issues

**Best speed:** **PyMuPDF is 32-57x faster** than pdfplumber

**Best for our needs:** PyMuPDF - only library with:
- Font information (needed for heading detection)
- Position information (needed for footnotes)
- **Page labels** (critical for scholarly citations)

**✅ Recommendation for ADR-001:** PyMuPDF confirmed as best choice

---

## Spike 03: Heading Detection

**Run:** `uv run python spikes/03_heading_detection.py <pdf>`

### Results: Comay (Body font: 11.0pt)

| Method | Headings Found | Notes |
|--------|---------------|-------|
| font_size | 0 | Threshold too strict? |
| bold | 0 | Uses italics, not bold |
| isolation | 180 | Too many false positives |
| **combined** | **21** | ✅ Reasonable, confidence-scored |
| pymupdf4llm | 22 | Quirky heading levels |

**Detected headings (combined method):**
- "Mourning Sickness" (0.7 conf, 14pt)
- "Contents", "Acknowledgments", "Abbreviations" (0.7 conf, 14pt)
- "Introduction", "Missed Revolutions", "The Kantian Theater" (0.7 conf, 14pt)

### Results: Derrida (Body font: 10.0pt)

| Method | Headings Found | Notes |
|--------|---------------|-------|
| font_size | 30 | Good for chapter titles (18pt) |
| **bold** | **36** | ✅ Best - catches bold chapter headings |
| isolation | 33 | Some false positives |
| combined | 46 | Overcounting |
| pymupdf4llm | 35 | Reasonable |

**Detected headings (bold method):**
- "FORCE AND SIGNIFICATION", "COGITO AND THE HISTORY OF MADNESS"
- "VIOLENCE AND METAPHYSICS", "GENESIS AND STRUCTURE"
- Section headings within chapters also detected

### Key Findings

**Most accurate method:** Depends on document style
- **Bold text works well** when headings are bold (Derrida)
- **Font size works well** when size hierarchy is clear
- **Combined method** provides confidence scores for filtering

**Recommended approach:** Use combined method with confidence threshold ≥0.6

**Confidence threshold:** 0.6-0.7 filters most false positives

---

## Spike 04: Footnote Detection

**Run:** `uv run python spikes/04_footnote_detection.py <pdf>`

### Results: Comay

**Footnote style:** **ENDNOTES** (at back of book, not per-page)

**Detection results:**
- Page-region method: 3 candidates (publisher info, not footnotes)
- Font-size method: 10 candidates (mostly copyright page)
- Superscript markers: 5 found in body text ([1], [2], etc.)
- **Marker-to-footnote matching: 0/5** (notes not on same page)

### Results: Derrida

**Footnote style:** **ENDNOTES** (at back of book)

**Detection results:**
- Page-region method: 3 candidates
- Superscript markers: 0 found in first 20 pages
- Notes section found at page 378

### ⚠️ Critical Finding: Philosophy Uses Endnotes

**Both tested philosophy books use ENDNOTES, not footnotes!**

This means:
- Notes are collected at the back of the book
- Superscript markers in body text don't have matching content on same page
- Detection must handle endnotes vs footnotes differently

**Feasibility assessment:**
- [x] **Defer footnote linking to Phase 2**
- [ ] Phase 1: Just preserve superscript markers in text
- [ ] Future: Detect endnote sections and link markers

---

## Spike 05: OCR Quality Survey

**Run:** `uv run python spikes/05_ocr_quality_survey.py <pdf> [--detailed] [--compare-image]`

### Survey Results

| Document | Source | Recommendation | Valid Words | Issues |
|----------|--------|----------------|-------------|--------|
| Kant - Critique of Judgment | Hackett scan | **DEGRADED** | 99.76% | broken_hyphenation |
| Comay | Stanford Press | ACCEPTABLE | ~100% | N/A (born-digital) |
| Derrida | Routledge | ACCEPTABLE | ~100% | N/A (born-digital) |

### Kant OCR Analysis (Most Challenging)

- **Pages analyzed:** 685
- **Pages with text:** 666 (97%)
- **Pages with issues:** 578 (84%)
- **Garbage char ratio:** 0.05% (very low)
- **Valid word ratio:** 99.76% (excellent)

**Issue breakdown:**
| Issue | Pages Affected |
|-------|---------------|
| broken_hyphenation | 559 pages |
| no_text_layer | 19 pages |
| merged_words | 10 pages |

### Key Finding: OCR Quality is Actually Good

Despite "DEGRADED" rating:
- **99.76% valid words** = text is highly usable
- **Main issue is hyphenation** (line-end hyphens not rejoined)
- Only 19 pages (3%) lack text entirely (probably images/diagrams)

### Conclusions for Phase 4 OCR

Based on survey:
- **~70% of target documents** have acceptable text layers (born-digital)
- **~30% need correction** (scans with various issues)
- **<5% need full re-OCR** (very few are truly poor)

**⚠️ IMPORTANT CAVEAT:** See Spike 08 below - "acceptable" OCR may still hurt RAG retrieval.

---

## Spike 08: Embedding Robustness Against OCR Errors

**Run:** `CUDA_VISIBLE_DEVICES="" uv run python spikes/08_embedding_robustness.py`

### Purpose

Test whether semantic embeddings are robust to OCR errors - a key assumption for RAG pipelines.

### Simulated Error Results

| Error Type | 5% Rate | 10% Rate | Assessment |
|------------|---------|----------|------------|
| **Character errors** | 0.657 | 0.541 | ❌ DEVASTATING |
| **Combined errors** | 0.682 | 0.608 | ❌ VERY POOR |
| Hyphenation | 1.000 | 0.868 | ✅ Robust |
| Word merge | 0.980 | 0.981 | ✅ Robust |
| Real-word swap | 0.981 | 0.963 | ✅ Robust |

**Threshold interpretation:**
- \> 0.95: Excellent (identical semantic meaning)
- \> 0.90: Good (usable for RAG)
- \> 0.80: Marginal (may miss matches)
- < 0.80: Poor (unreliable)

### Real OCR Analysis (Kant PDF)

**Error counts detected:**
| Error Type | Count | Notes |
|------------|-------|-------|
| l/1/I confusion | 3,450 | Roman numerals, words |
| Mid-word caps | 597 | "PuRE", "AEsTHEnc" |
| tl→ti substitution | 381 | Character errors |
| **Total** | **4,428** | 1.61% of 274,850 words |

**Single-word embedding impact:**
| OCR | Correct | Similarity |
|-----|---------|------------|
| "Beautlful" | "Beautiful" | **0.515** ❌ |
| "Iii" | "lii" | **0.369** ❌ |
| "jUdgment" | "judgment" | 1.000 ✅ |

**Finding:** Case changes are fine, but character substitutions are devastating.

### ⚠️ Critical Finding: RAG Assumption Invalid

**What we assumed:** "OCR quality doesn't matter much for RAG"

**What we found:**
- Even 1-2 character errors per sentence can drop similarity 10-30%
- 5% character error rate → similarity drops to 0.4-0.6 (unusable)
- The Kant PDF has ~1.6% word error rate, concentrated in meaningful terms

**Implication for ScholarDoc:**
- OCR quality DOES matter for RAG applications
- Error correction is more important than previously thought
- Phase 4 OCR work may need higher priority

### ✅ Response: OCR Correction Module Implemented

Based on these findings, we implemented Phase 1 OCR correction:

**Module:** `scholardoc/normalizers/ocr_correction.py`

**Features:**
- Quality scoring with `is_usable_for_rag` threshold (<2% error rate)
- Pattern-based correction for known OCR errors (beautlful→beautiful, rnorning→morning)
- Dictionary-based spell check with pyspellchecker
- `OCRCorrectionNormalizer` for pipeline integration

**Design doc:** `docs/design/OCR_STRATEGY.md` covers full Phase 1-3 strategy

---

## Spike 06: Ground Truth Corpus

**Run:** 
- `uv run python spikes/06_ground_truth.py download-gutenberg <id> <output>`
- `uv run python spikes/06_ground_truth.py compare <pdf> <txt>`
- `uv run python spikes/06_ground_truth.py annotate-pages <pdf>`

### Parallel Text Candidates

| Work | Gutenberg ID | Archive.org ID | Alignment Quality | Notes |
|------|--------------|----------------|-------------------|-------|
| | | | | |
| | | | | |
| | | | | |

### Ground Truth Corpus Status

| Document | Pages | Page Numbers | Headings | Footnotes | Text Samples | Status |
|----------|-------|--------------|----------|-----------|--------------|--------|
| | | ❌/✅ | ❌/✅ | ❌/✅ | ❌/✅ | |
| | | | | | | |
| | | | | | | |

### Annotation Time Estimates

- Page number annotation: __ minutes per 100 pages
- Heading annotation: __ minutes per 100 pages
- Footnote annotation: __ minutes per 100 pages
- Full text verification: __ minutes per page

### Ground Truth Quality Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Inter-annotator agreement | >95% | |
| Spot-check accuracy | >99% | |
| Sequence consistency (page numbers) | 100% | |

---

## Spike 07: Claude + Human Annotation Workflow

**Purpose:** Test hybrid annotation where Claude proposes and humans verify.

### Workflow Tested

```
PDF → Claude Annotation → Human Review → Verified Ground Truth
           (agent)         (spike 07)
```

### Effectiveness Metrics

Track these across documents to measure Claude annotation quality:

| Document | Total Items | Flagged | Reviewed | Corrected | Accuracy |
|----------|-------------|---------|----------|-----------|----------|
| | | | | | |
| | | | | | |

**Accuracy = (Reviewed - Corrected) / Reviewed**

### Time Investment

| Phase | Time per 100 pages | Notes |
|-------|-------------------|-------|
| Claude annotation | | |
| Human review (flagged) | | |
| Spot-check (sample) | | |
| **Total** | | |

### Error Patterns

Track what Claude gets wrong to improve the agent:

| Error Type | Count | Example | Fix |
|------------|-------|---------|-----|
| Heading level wrong | | | |
| Missed footnote marker | | | |
| Page number format wrong | | | |
| False positive heading | | | |

### Recommendations

After running on 5+ documents:
- [ ] Is Claude annotation worth the review overhead?
- [ ] What confidence threshold minimizes review while catching errors?
- [ ] Which element types need most review?
- [ ] How should we update the annotation agent prompt?

---

## Consolidated Findings

### QUESTIONS.md Answers

| Question | Finding | Evidence |
|----------|---------|----------|
| Q1: Page number format | Use PDF page labels when available | Derrida has "i", "ii", "1", "2"... |
| Q2: Multi-column handling | Not needed - all tested PDFs are single-column | Spike 01 layout analysis |
| Q3: Born-digital detection | Check for image blocks + OCR font patterns | Kant has 243 fonts (OCR artifact) |
| Q4: Heading detection strategy | Combined method with conf ≥0.6 | Spike 03 comparison |
| Q5: Footnote accuracy threshold | N/A - defer to Phase 2 | Philosophy uses endnotes |
| Q6: GROBID integration | Not needed for Phase 1 | PyMuPDF sufficient |

### Validated Assumptions

- [x] PyMuPDF is fastest and most feature-complete library
- [x] Page labels exist in some PDFs (critical for citations)
- [x] Font size correlates with heading level
- [x] Born-digital PDFs have excellent text quality
- [x] Hyphenation errors don't hurt embeddings (robust)
- [x] Word merge errors don't hurt embeddings (robust)

### Invalidated Assumptions

- [x] ~~Footnotes appear on same page as markers~~ → Philosophy uses ENDNOTES
- [x] ~~All PDFs have consistent heading styles~~ → Varies by publisher
- [x] ~~OCR quality is a major blocker~~ → Actually character errors ARE a problem for RAG
- [x] ~~Embeddings are robust to OCR errors~~ → Character errors devastate similarity (0.5-0.65)
- [x] ~~"99% valid words" means good quality~~ → Heuristic, not accuracy measure

### Surprises

- **Endnotes dominate:** Both tested books use endnotes, not footnotes
- **Hyphenation doesn't hurt RAG:** Embeddings are robust to line-break hyphens
- **Character errors DO hurt RAG:** Even 1-2% error rate degrades similarity significantly
- **Page labels are valuable:** Derrida has proper roman/arabic numbering
- **"Valid word" metrics are misleading:** 99.76% sounds great but doesn't measure accuracy
- **Single-word errors cascade:** "Beautlful"→"Beautiful" drops similarity to 0.515

---

## Design Changes Required

Based on spike findings:

### ADR-001 (Library Choice)
- [x] **Confirm PyMuPDF recommendation** ✅
- Rationale: 32-57x faster, only library with page labels, full font/position info

### SPEC.md Updates
- [ ] Add hyphenation fixing to text processing
- [ ] Clarify page number extraction from labels vs OCR
- [ ] Document endnote vs footnote handling

### REQUIREMENTS.md Updates
- [ ] Relax footnote linking requirement (defer to Phase 2)
- [ ] Add hyphenation-fixing acceptance criteria

### Scope Changes
- [x] **Move footnote/endnote linking to Phase 2**
- [x] Keep heading detection in Phase 1 (works well)
- [x] ~~Add hyphenation post-processing to Phase 1~~ → Not needed (embeddings robust)
- [ ] **Consider: OCR error correction more important than thought**
- [ ] **Consider: Prioritize born-digital PDFs for RAG use cases**

---

## Next Steps

1. [x] ~~Run spikes 01-05~~ ✅
2. [x] ~~Run spike 08 (embedding robustness)~~ ✅
3. [x] ~~Document findings~~ ✅ (this document)
4. [ ] Update ADR-001 with empirical confirmation
5. [ ] Update SPEC.md: add OCR quality considerations
6. [ ] Update QUESTIONS.md with answers
7. [ ] Adjust ROADMAP.md: defer footnotes, consider OCR correction priority
8. [ ] Create test fixtures from sample PDFs (Comay, Derrida, Kant)
9. [ ] **Decision needed: How to handle OCR errors for RAG applications?**
   - Option A: Recommend born-digital PDFs only
   - Option B: Add error correction to pipeline
   - Option C: Accept degraded retrieval for scanned docs
   - Option D: Flag scanned docs with quality warnings
10. [ ] Begin Phase 1 implementation
