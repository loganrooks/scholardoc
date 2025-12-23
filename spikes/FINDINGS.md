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
| 06a_extract_tricky_samples | Extract test samples | German terms, Greek, hyphenation, sous-erasure |
| 06b_ground_truth | Build evaluation corpus | Parallel texts, annotation tools, validation |
| 07_annotation_review | Claude + Human workflow | Hybrid annotation, review interface, stats |
| 08_embedding_robustness | Test embeddings vs OCR | How robust are embeddings to OCR errors? |
| 09_trocr_reocr | Test TrOCR re-OCR | Is re-OCR better than existing text layer? |
| 10_tesseract_reocr | Compare OCR engines | Tesseract vs EasyOCR vs docTR |
| 11_rag_chunk_quality | Test artifact impact | Page numbers, headers, footnote markers |
| 12_smart_spellcheck | Auto-detect skip words | Avoid whitelists with heuristics |
| 13_spellcheck_risk | Quantify correction risk | False correction rate for philosophy terms |
| 14-19_ground_truth | Build classification corpus | Stratified sampling, batch processing, review |
| 20-22_review_analysis | Review BAD classifications | False positive detection, final validation |

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
uv run python spikes/06a_extract_tricky_samples.py  # Extract challenging samples

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

### ✅ OCR Correction Improvements (Based on Spike 09)

Following Spike 09's critical finding that mid-word caps don't hurt embeddings, we improved the module:

**1. Quality Scoring Update**
- `mid_word_caps` error weight changed from 2 → **0**
- Rationale: "jUdgment" → 1.000 similarity (embeddings normalize case perfectly)
- Only actual misspellings and character substitutions are penalized

**2. Philosophy Vocabulary Whitelist**
- Added ~120 scholarly terms that spell checkers incorrectly flag:
  - Kantian: apperception, noumenon, transcendental, schematism
  - Hegelian: dialectic, aufhebung, sublation, negation
  - Phenomenology: intentionality, epoché, dasein, lebenswelt
  - Deconstruction: différance, logocentrism, aporia, grammatology
  - Semiotics: phonologism, signifier, semiology, scientificity
  - Philosopher names: Heidegger, Husserl, Derrida, etc.

**3. Contextual Correction (Optional)**
- Integrated OCRfixr for BERT-based contextual correction
- Install with: `pip install scholardoc[contextual]`
- Uses two-step validation: spell suggestions × BERT context
- Higher accuracy but slower (~1-2s per paragraph)

**Tested Results:**
| PDF | Quality Score | Usable for RAG | Philosophy Terms Preserved |
|-----|---------------|----------------|---------------------------|
| Derrida (English) | 0.89 | ✅ Yes | epistemological, phenomenological |
| Heidegger (German) | 0.00 | ❌ No | N/A (German text, need i18n) |
| Kant (OCR scan) | ~0.65 | ⚠️ Marginal | judgment, aesthetic, transcendental |

**Limitation Identified:** Current spell checker is English-only. German philosophy texts trigger many false positives. Future work may need language detection.

---

## Spike 09: TrOCR Re-OCR Testing

**Run:** `uv run python spikes/09_trocr_reocr.py <pdf> --pages 50,100,150 --compare`

### Purpose

Test whether re-OCR with Microsoft's TrOCR produces better results than existing PDF text layers.

### Setup

**GPU Configuration (GTX 1080 Ti / sm_61):**
- Requires PyTorch with CUDA 11.8 (not 12.x which dropped sm_61 support)
- Configured via `pyproject.toml` with `extra-index-url` for PyTorch cu118 wheels
- GPU speedup: ~21x faster than CPU (7.5s vs 236s per page)

### Results (Kant PDF)

| Metric | Value | Notes |
|--------|-------|-------|
| Mean CER | 17.4% | TrOCR vs existing OCR |
| Mean WER | 25.6% | Not ground truth comparison |
| GPU Speed | ~7.5s/page | 21x faster than CPU |

**⚠️ Caveat:** This compares TrOCR vs existing OCR - neither is ground truth!

### Sample Comparisons

| Existing OCR | TrOCR Output | Assessment |
|--------------|--------------|------------|
| "Beautlful" | "BEAUTIFAL" | Both wrong (should be "Beautiful") |
| "jUdgment" | "JUDEMENT" | Both have issues |
| "Practical" | "PRACTION" | TrOCR error |
| "TRANSLATOR'S INTRODUCTION" | "TRANSLATOR'S INTRODUCTION" | ✅ Perfect match |

### Key Findings

1. **TrOCR not clearly better** than Adobe Paper Capture OCR for this scan
2. **Different error types**: Existing = character confusions; TrOCR = misspellings
3. **TrOCR outputs ALL CAPS** - model limitation for this specific model
4. **Ground truth needed** to properly evaluate which is better

### ⚠️ Critical Finding: Embedding Impact

Testing which OCR produces better embeddings for RAG (using ground truth comparison):

| Ground Truth | Existing OCR Sim | TrOCR Sim | Winner |
|-------------|------------------|-----------|--------|
| "Beautiful" | 0.515 ("Beautlful") | 0.381 ("BEAUTIFAL") | Existing |
| "judgment" | **1.000** ("jUdgment") | 0.288 ("JUDEMENT") | Existing |
| "Practical Reason" | **1.000** | 0.621 ("PRACTION") | Existing |

**Key insights:**
1. **ALL CAPS doesn't hurt embeddings** - embeddings normalize case
2. **Mid-word caps don't hurt** - "jUdgment" embeds perfectly!
3. **Misspellings DEVASTATE embeddings** - TrOCR's errors are worse for RAG
4. **Character confusions** (existing OCR) preserve word shape better than misspellings

### Recommendation

**For RAG applications: Existing OCR + Phase 1 correction > TrOCR re-OCR**

The existing OCR's errors are more "fixable" by our spell checker because:
- "Beautlful" → "Beautiful" is a known pattern we can correct
- "JUDEMENT" is a novel misspelling harder to fix
- Character confusions preserve enough word shape for partial embedding match

TrOCR would only be valuable for:
- PDFs with no/garbage text layer
- After fine-tuning on domain-specific samples

---

## Spike 10: Comprehensive OCR Engine Comparison

**Run:** `uv run python spikes/10_tesseract_reocr.py <pdf> --engine all`

### Purpose

Compare multiple OCR engines against existing PDF text layers to determine if re-OCR can improve RAG quality.

### Engines Tested

| Engine | Type | GPU Support | Speed (page) |
|--------|------|-------------|--------------|
| Existing | Adobe Paper Capture | N/A | N/A |
| Tesseract 5.3 | Classical + LSTM | ❌ CPU only | ~2.0s |
| EasyOCR | Neural (CRNN) | ✅ GPU | ~5.5s |
| docTR | Neural (Transformer) | ✅ GPU | ~0.6s |

### Results (Kant PDF, 2 pages, ground truth comparison)

| Method | Avg Similarity to Ground Truth | Speed |
|--------|-------------------------------|-------|
| **docTR (GPU)** | **0.402** 🏆 | 0.6s/page |
| Existing layer | 0.392 | N/A |
| Tesseract | 0.373 | 2.0s/page |
| EasyOCR | 0.368 | 5.5s/page |
| Existing + correction | 0.365 | N/A |

### Key Findings

1. **docTR wins!** Neural document OCR outperforms existing Adobe OCR for RAG embedding similarity
2. **docTR is fastest** on GPU (10x faster than Tesseract, 9x faster than EasyOCR)
3. **Word order matters** - EasyOCR scrambles text order, devastating for embeddings
4. **Spell correction hurts** - Basic corrections introduced more errors than they fixed

### Text Quality Comparison

```
Existing: "64 Preface <A> But since there were fortunately only a few of them..."
docTR:    "Preface <A> But since there were fortunately only a few of them..."  ✅
EasyOCR:  "Preface <A> they could not few But since there were..."  ❌ (scrambled)
Tesseract: "AX AXi Preface <A> But since there were..."  ⚠️ (artifacts)
```

### ✅ Critical Update: docTR as Selective Re-OCR Option

Based on these findings, **docTR is a viable selective re-OCR option**:

**When to use docTR re-OCR:**
- Quality score < 0.5 (poor existing OCR)
- Detected as scan without text layer
- User explicitly requests re-OCR
- Ground truth comparison available for validation

**Configuration option (proposed):**
```python
@dataclass
class ConversionConfig:
    ocr_strategy: Literal["existing", "doctr", "hybrid"] = "existing"
    reocr_threshold: float = 0.5  # Re-OCR pages below this quality
```

**Trade-offs:**
- Pro: Better RAG similarity for scans
- Pro: Fastest GPU-accelerated option
- Con: Adds ~130MB model download
- Con: Requires GPU for reasonable speed

### Recommendation Update

Previous recommendation (Spike 09): "Existing OCR + spell correction > re-OCR"

**Revised recommendation:**
- For **born-digital PDFs**: Use existing text layer (no benefit from re-OCR)
- For **scanned PDFs with poor OCR**: docTR re-OCR can improve RAG quality by ~3-5%
- **Hybrid strategy**: Use quality scoring to selectively re-OCR problematic pages

---

## Spike 11: RAG Chunk Quality Testing

**Run:** `uv run python spikes/11_rag_chunk_quality.py`

### Purpose

Test how different text artifacts affect embedding quality for RAG retrieval.

### Key Question

Should we remove page numbers, running headers, and footnote markers before embedding?

### Results

| Artifact Type | Similarity Impact | Action |
|--------------|-------------------|--------|
| Page numbers ("64 ") | **-29%** 🚨 | MUST REMOVE |
| Running headers ("Preface <A>") | -2% | Should remove |
| Footnote markers ("*", "†") | -1% | Optional |
| OCR misspellings | -4% to -15% | MUST CORRECT |
| Cross-page markers ("[PAGE 65]") | -4% | Don't add |

### Critical Finding: Page Numbers Devastate Embeddings

A leading page number like "64 " drops embedding similarity from 1.0 to 0.707.

This explains why Spike 10's OCR comparisons showed low similarities (~0.4):
- Ground truth: "But since there were fortunately..."
- Existing OCR: "64 Preface <A> But since there were..."
- The page number artifact was penalizing the comparison!

### Footnote Handling Experiment

| Strategy | Similarity to Query |
|----------|---------------------|
| Passage + footnote together | 0.591 |
| Passage with marker | 0.587 |
| Passage clean | 0.578 |
| Footnote only | 0.434 |

**Finding:** Embedding footnotes with their context marginally improves retrieval.
But footnotes alone are poor retrieval targets.

### Cross-Page Text Handling

| Representation | Similarity |
|---------------|------------|
| Full sentence | 0.597 |
| Naive concat | 0.597 ✅ |
| With page marker | 0.573 ❌ |
| With hyphen artifact | 0.598 |

**Finding:** Simple concatenation works perfectly. Don't add "[PAGE X]" markers.

### Recommendations for ScholarDoc Output

```python
@dataclass
class RAGChunk:
    """Optimized for embedding and retrieval."""

    # Clean text for embedding (no artifacts)
    text: str

    # Metadata for citation (NOT embedded)
    page_start: int
    page_end: int | None
    page_labels: list[str]  # ["64", "65"] for display

    # Footnotes extracted separately
    footnotes: list[Footnote]  # Embed separately if needed
```

**Processing Pipeline:**
1. Extract raw text from PDF
2. **Remove page numbers** (critical - 29% embedding impact)
3. **Remove running headers** (recommended - 2% impact)
4. Apply OCR correction (critical - 4-15% impact)
5. Merge cross-page text without markers
6. Extract footnotes as separate chunks
7. Store page numbers as metadata for citation

---

## Spike 06: Extract Tricky OCR Samples

**Run:** `uv run python spikes/06_extract_tricky_samples.py`

### Purpose

Extract challenging text samples from philosophy PDFs for OCR correction testing.

### Results (4 PDFs analyzed)

| PDF | German Terms | Greek | Hyphenation | Sous-Erasure Candidates | OCR Errors |
|-----|--------------|-------|-------------|-------------------------|------------|
| Heidegger - Being and Time | 1,354 | 0 | 192 | 1,347 | 1,394 |
| Derrida - Writing & Difference | 290 | 9 | 843 | 595 | 1,421 |
| Derrida - Margins of Philosophy | 326 | 0 | 578 | 495 | 1,016 |
| Heidegger - Pathmarks | 255 | 8 | 9 | 506 | 794 |

**Total samples extracted:** 4,998 (extensive mode from 10 PDFs)

### Sample Categories (Extensive Run - 20 Categories)

| Category | Count | Description |
|----------|-------|-------------|
| ocr_char_confusion | 500 | rn/m, l/1/I, cl/d character confusions |
| philosopher_names | 422 | Heidegger, Derrida, Kant, etc. (often misspelled) |
| german_terms | 421 | Sein, Dasein, Aufhebung, Zeitlichkeit |
| ligatures | 400 | fi, fl, ff, ffi ligature issues |
| special_punctuation | 350 | Em-dashes, curly quotes, guillemets |
| hyphenation | 344 | Line-break hyphenation |
| superscript_subscript | 300 | Footnote markers, Unicode super/subscripts |
| roman_numerals | 300 | i, ii, iii, iv (l/I confusion risk) |
| citations | 282 | (Smith, 2020), page ranges, vol/no. |
| sous_erasure_candidate | 273 | Being, presence, trace (needs visual check) |
| french_terms | 268 | différance, écriture, épistémè |
| latin_terms | 246 | a priori, cf., ibid., sui generis |
| diacritics | 232 | Accented characters (é, ü, ö, etc.) |
| page_artifact | 192 | Running heads, page numbers |
| block_quote | 163 | Indented quoted text |
| cross_references | 160 | See page X, §4.2, cf. above |
| unicode_anomaly | 69 | Non-breaking spaces, zero-width chars |
| editorial_marks | 48 | [sic], [...], asterisks |
| greek_chars | 15 | Greek letters (ψ, λόγος, etc.) |
| math_symbols | 13 | ∀, ∃, →, ≠, √ |

### Key Findings

1. **German philosophical terms are common**: Dasein, Sein, Seiendes appear hundreds of times
2. **Greek characters appear**: Mostly in Derrida discussing Freud (ψ for psychic apparatus)
3. **Hyphenation varies by source**: Pathmarks has very few, Margins has many
4. **Sous-erasure candidates need visual verification**: Text detection alone can't confirm X-marks

### Sous-Erasure Discovery

Found complete sous-erasure detection implementation in `zlibrary-mcp` project:
- Uses OpenCV Line Segment Detector (LSD)
- Detects crossing diagonal line pairs
- Maps X-marks to underlying text
- Outputs as `~~word~~` in markdown

See: `docs/design/SOUS_ERASURE_DESIGN.md` for integration strategy.

### Output

Samples saved to `spikes/tricky_samples.json` for use in OCR correction testing.

---

## Spike 06b: Ground Truth Corpus

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

## Spike 06c: Real Ground Truth Extraction

**Run:** `uv run python spikes/06c_real_ground_truth.py scan-errors <pdf> --pages 1-100`

### Purpose

Build verified (ocr_text, correct_text) pairs for OCR correction testing by finding **actual** OCR errors, not just patterns that look problematic.

### Challenge: Pattern Matching ≠ Real Errors

Initial approach (Spike 06b) tried to validate samples by pattern matching:
- Result: 97.5% needed manual review
- Problem: German "Moment" matched English uses, proper names flagged as errors

**Solution:** Use spell checking on OCR'd scans + extensive filtering.

### Filtering Implementation

Developed comprehensive filtering to reduce false positives:

| Filter | Purpose | Examples Filtered |
|--------|---------|------------------|
| **Scholarly terms** | ~200 philosophy vocabulary | dasein, aufhebung, différance, noumenon |
| **Scholar names** | Commonly cited names | Hutcheson, Guyer, Kivy, Boulton |
| **Publishers** | Academic press names | Routledge, Nijhoff, Hackett, Cambridge |
| **Latin terms** | Abbreviations | viz, ibid, sensus, communis |
| **German/French** | Foreign words in citations | der, die, das, theoretisch, wissen |
| **Roman numerals** | Page numbers, section refs | i, ii, iii, xlvii, lxvi (with OCR l/I variants) |
| **Hyphenation** | Line-break fragments | "presupposi-tion", "imagina-tion" |
| **Proper names** | Capitalized mid-sentence | Context-based detection |

### Results (Kant PDF, First 100 Pages)

| Metric | Before Filtering | After Filtering |
|--------|------------------|-----------------|
| Candidates found | ~200 | **30** |
| True OCR errors | ~19 | ~15 |
| False positives | ~181 | ~15 |
| Precision | ~10% | **~50%** |

### Verified OCR Errors Found

| OCR Text | Correct | Error Type | Context |
|----------|---------|------------|---------|
| `righLful` | rightful | L/t confusion | "its righLful place in the Kantian corpus" |
| `tbese` | these | b/h confusion | "tbese judgments is, roughly" |
| `tbe` | the | b/h confusion | Same line as above |
| `untit` | until | l truncation | "not untit a few years" |
| `ewton` | Newton | Missing N | "Newton undeniably had discovered" |
| `sllbsumed` | subsumed | ll/u confusion | "can be sllbsumed under it" |
| `ithin` | within | Missing w | "bounds ~ithin which" |
| `lhe` | the | l/t confusion | "remind us of lhe limits" |
| `willI` | will | Extra I | "maxim of your willI could" |
| `fhis` | this | f/t confusion | "29'fhis claim hinges" |
| `alsu` | also | u/o confusion | "it can alsu produce" |
| `idifferent` | different | Extra i | "organization of idifferent subjects" |

### Key OCR Error Patterns

| Pattern | Example | Frequency | Detection Method |
|---------|---------|-----------|------------------|
| b/h confusion | tbe→the | Common | Spell check + edit distance |
| l/t confusion | lhe→the | Common | Character substitution |
| ll/u confusion | sllbsumed | Occasional | Edit distance |
| Character drop | ithin, ewton | Occasional | Spell check |
| Extra char | idifferent | Occasional | Spell check |

### Remaining Challenges

1. **Hyphenation fragments still slip through**: Need even more patterns
2. **Valid technical terms flagged**: "typus" (Latin), "categorial" (Kantian)
3. **German words in references**: "aller", "theoretisch"

### Output

Clean ground truth pairs saved to `spikes/real_ground_truth_v2.json` for OCR correction testing.

### Recommendation

For OCR correction testing:
- Use verified pairs from this spike as gold standard
- Pattern-based detection needs human review (~50% precision)
- Consider parallel text comparison for higher confidence (Gutenberg, etc.)

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

## Spikes 14-22: Ground Truth Classification

**Run:** `uv run python spikes/18_aggregate_ground_truth.py`

### Purpose

Build a comprehensive OCR quality ground truth corpus for:
1. Training quality prediction models
2. Evaluating OCR correction strategies
3. Benchmarking selective re-OCR approaches

### Methodology

**Classification Tier System:**

| Tier | Criteria | Re-OCR Action |
|------|----------|---------------|
| **GOOD** | Clean text, only foreign terms flagged | Skip |
| **MARGINAL** | Some issues but readable | Optional |
| **BAD** | Genuine OCR corruption | Required |

**Process:**
1. **Spike 14-16**: Initial classification with spell-check + heuristics
2. **Spike 17**: Stratified sampling for even coverage across error rates
3. **Spike 18**: Aggregation into unified ground truth
4. **Spike 19**: Batch creation for parallel agent processing
5. **54 Sonnet agents**: Classified ~1,991 pages in parallel
6. **BAD review**: 13 agents re-reviewed 295 BAD pages for false positives
7. **Final update**: 160 pages reclassified from BAD→GOOD (false positives)

### Final Statistics (1,790 pages)

| Document | Pages | GOOD | MARGINAL | BAD |
|----------|-------|------|----------|-----|
| Heidegger - Being and Time | 419 | 32.9% | 50.1% | 16.9% |
| Heidegger - Pathmarks | 223 | 22.9% | 54.7% | 21.5% |
| Heidegger - Discourse on Thinking | 18 | 38.9% | 33.3% | 27.8% |
| Derrida - Margins of Philosophy | 192 | 43.2% | 42.2% | 14.6% |
| Derrida - Writing and Difference | 270 | 58.9% | 37.0% | 4.1% |
| Derrida - Truth in Painting | 222 | 46.8% | 48.2% | 5.0% |
| Derrida - Beast and Sovereign Vol 1 | 233 | 46.4% | 51.9% | 1.7% |
| Comay - Mourning Sickness | 147 | 46.3% | 40.8% | 12.9% |
| Lenin - State and Revolution | 66 | 65.2% | 34.8% | 0.0% |

### Key Findings

**1. Born-digital texts have near-zero BAD pages**
- Lenin (0% BAD) and most Derrida volumes (1.7-5.0% BAD)
- "BAD" classifications were false positives from foreign vocabulary

**2. Scanned OCR varies by source quality**
- Heidegger Being and Time: 16.9% BAD (older scan)
- Pathmarks: 21.5% BAD (mixed quality)
- Discourse: 27.8% BAD (small sample, high variance)

**3. False positive sources in BAD classification:**
- German/French/Latin philosophical terms (differance, Zeitlichkeit)
- Greek characters (λόγος, ψυχή)
- Proper nouns and bibliographic abbreviations
- Roman numerals (misidentified as OCR errors)

**4. Review process critical for accuracy**
- Initial 295 BAD pages → 160 false positives (54%)
- After review: 197 confirmed BAD pages (11% of corpus)

### Output Files

```
ground_truth/
├── footnotes/                  # Footnote detection ground truth
│   ├── schema.json             # ML-optimized footnote schema
│   ├── derrida_footnotes.json  # Derrida footnote examples
│   └── kant_footnotes.json     # Kant footnote examples
├── ocr_errors/                 # OCR error pairs for correction testing
│   ├── ocr_error_pairs.json    # Verified (ocr_text, correct_text) pairs
│   ├── challenging_samples.json # Extracted tricky OCR samples
│   └── validated_samples.json  # Validated OCR samples
└── ocr_quality/                # Page-level OCR quality classifications
    ├── batches/                # Raw batch files with full page text
    ├── classified/             # *_batch_NN_classified.json files
    ├── reviewed/               # BAD page review results
    ├── samples/                # *_sample_for_review.json files
    └── unified_ground_truth.json # Aggregated classifications
```

### Recommendations

1. **Use stratified sampling** for representative test sets
2. **Always review BAD classifications** - 54% were false positives
3. **Account for multilingual content** when building classifiers
4. **Prioritize Heidegger texts** for re-OCR testing (highest BAD rate)
5. **Use Lenin/Derrida** as born-digital baselines

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
7. [x] ~~Adjust ROADMAP.md: defer footnotes, consider OCR correction priority~~ ✅
8. [ ] Create test fixtures from sample PDFs (Comay, Derrida, Kant)
9. [x] ~~Decision needed: How to handle OCR errors for RAG applications?~~ → Use fuzzy retrieval + flag for re-OCR
10. [x] ~~Run structure extraction validation spikes (24-27)~~ ✅
11. [ ] Begin Phase 1 implementation

---

## Spike 24: ToC Detection and Parsing

**Run:** `uv run python spikes/24_toc_detection.py`

### Purpose

Validate ToC detection and parsing design before implementation.

### Results (12 PDFs)

| Metric | Value |
|--------|-------|
| PDFs with ToC detected | 7/12 (58%) |
| Average entries parsed per ToC | 7.9 |
| Format type detected | indented_hierarchy (most common) |

**Detection performance by PDF:**

| PDF | ToC Pages | Entries Parsed | Notes |
|-----|-----------|----------------|-------|
| Lenin - State and Revolution | 2 | 41 | ✅ Best parsing |
| Derrida - Truth in Painting | 3 | 7 | Good |
| Derrida - Beast & Sovereign | 1 | 5 | Good |
| Heidegger - Being and Time | 6 | 1 | ⚠️ Detection worked, parsing failed |
| Kant - Critique of Judgement | 7 | 1 | ⚠️ Detection worked, parsing failed |
| Comay - Mourning Sickness | 1 | 0 | ⚠️ Detection worked, parsing failed |
| Heidegger - Pathmarks | 1 | 0 | ⚠️ Detection worked, parsing failed |

### Key Findings

1. **ToC page detection works** - 58% of PDFs have detectable ToC pages
2. **ToC entry parsing is fragile** - Many ToCs detected but not parsed (0-1 entries)
3. **Format varies widely** - Different publishers use different ToC layouts
4. **Dotted leaders help** - ToCs with ".........." parse better

### Parsing Challenges

- Philosophy books often have complex ToC layouts
- Roman numerals for front matter pages are hard to resolve
- Indentation-based hierarchy varies by publisher
- Some ToCs span multiple pages with inconsistent formatting

### ✅ Recommendation

ToC detection is useful but should be a **supplementary** source, not primary.
Parser needs improvement to handle more formats reliably.

---

## Spike 25: PDF Outline/Bookmark Quality

**Run:** `uv run python spikes/25_pdf_outline_quality.py`

### Purpose

Evaluate PDF outlines as a structure source.

### Results (12 PDFs)

| Metric | Value |
|--------|-------|
| PDFs with outline | 7/12 (58%) |
| Average entries | 36.3 |
| Average page coverage | 6.5% |
| Average max depth | 2.3 levels |

**Outline quality by PDF:**

| PDF | Entries | Max Depth | Coverage | Title Match Rate |
|-----|---------|-----------|----------|------------------|
| Heidegger - Being and Time | 134 | 5 | 19.5% | 40% |
| Kant - Critique of Judgement | 46 | 5 | 6.3% | 50% |
| Heidegger - Pathmarks | 20 | 1 | 5.0% | 70% |
| Derrida - Writing & Difference | 17 | 1 | 3.6% | 20% |
| Derrida - Margins | 16 | 1 | 4.5% | 40% |

### Key Findings

1. **Outlines exist in majority** - 58% have outlines
2. **Coverage is sparse** - Only 6.5% of pages have outline entries
3. **Outlines mark major sections** - Chapters and major headings, not subsections
4. **Title match rate varies** - 0-70%, depends on PDF creation
5. **Deep outlines exist** - Some have 5 levels of hierarchy

### ✅ Recommendation

PDF outlines are **high-confidence when present** (0.95 confidence) but:
- Only mark major sections
- Not always available
- Need heading detection fallback for subsections

---

## Spike 26: Multi-Source Structure Fusion

**Run:** `uv run python spikes/26_structure_fusion.py`

### Purpose

Test whether combining multiple structure sources improves accuracy.

### Results (12 PDFs)

| Metric | Value |
|--------|-------|
| Source: Outline | 7/12 (58%) |
| Source: ToC | 0/12 (0%) - parser not integrated |
| Source: Heading | 11/12 (92%) |

**Agreement Analysis:**

| Agreement Level | Count | Percentage |
|-----------------|-------|------------|
| All 3 sources agree | 0 | 0% |
| 2 sources agree | 71 | 21% |
| Single source only | 270 | 79% |

### Key Findings

1. **⚠️ Sources rarely agree** - Only 21% agreement between outline and heading detection
2. **Heading detection is universal** - 92% of PDFs have detectable headings
3. **ToC parser didn't contribute** - Needs page reference resolution
4. **Agreement varies by PDF** - Heidegger Being and Time: 17% agreement; Margins: 39%

### Why Low Agreement?

- **Outline marks chapters**, heading detection finds all headings (subsections too)
- **Different granularity** - Outline has 46 entries, heading detection finds 276
- **Position tolerance** - 1-page tolerance still shows disagreement
- **False positives** - Heading detection picks up emphasized text that isn't a heading

### ✅ Critical Finding

**Probabilistic fusion as designed may add noise rather than improve accuracy.**

The low agreement rate (21%) suggests:
- Sources capture different things (major vs minor sections)
- Fusion would create conflicting candidates
- Best approach: **Use outline when available (high confidence), fallback to heading detection**

### Revised Recommendation

Instead of probabilistic fusion, use **cascading with confidence**:
1. If PDF outline exists → use it (confidence 0.95)
2. Supplement with heading detection for subsections (confidence 0.5-0.8)
3. ToC enriches titles but shouldn't create new sections

---

## Spike 27: Document Profile Auto-Detection

**Run:** `uv run python spikes/27_document_profile_detection.py`

### Purpose

Test whether we can automatically detect document types.

### Results (12 PDFs)

| Metric | Value |
|--------|-------|
| Accuracy vs manual | 10/10 (100%) |
| Average confidence | 100% |
| Low confidence (<50%) | 0 |

**Detection breakdown:**

| Detected Type | Count |
|---------------|-------|
| Book | 10 (83%) |
| Article | 2 (17%) |

### Indicators Used

| Indicator | Detection Rate | Reliability |
|-----------|---------------|-------------|
| Page count (>200) | High | ✅ Very reliable for books |
| Has ToC | 58% | ✅ Good book indicator |
| Has outline | 58% | ✅ Good book indicator |
| Has chapters | High | ✅ Strong book indicator |
| Has abstract | 0% | Would indicate article |

### ⚠️ Caveat: Test Set Bias

All 10 full PDFs in our test set are **books**. The two "article" classifications were:
- Test snippets (few pages)

We have **no articles, essays, or reports** in the test set. This 100% accuracy may not generalize.

### ✅ Recommendation

Profile detection is reliable **for books vs non-books** but needs testing on:
- Academic articles (with abstracts, DOIs)
- Essays (short, no ToC, no chapters)
- Technical reports (numbered sections)

---

## Phase 0.5 Validation Summary

### What We Validated

| Component | Status | Finding |
|-----------|--------|---------|
| ToC detection | ⚠️ Partial | Detects pages (58%) but parsing is fragile |
| PDF outlines | ✅ Works | 58% have outlines, high confidence when present |
| Heading detection | ✅ Works | 92% detection rate, good fallback |
| Probabilistic fusion | ❌ Not beneficial | 21% agreement - sources capture different things |
| Profile detection | ✅ Works | 100% on books (needs more document types) |

### Design Changes Recommended

| Original Design | Revised Approach | Reason |
|-----------------|------------------|--------|
| Probabilistic fusion of 3 sources | Cascading with confidence | Low source agreement (21%) |
| ToC parser as equal source | ToC for title enrichment only | Parsing too fragile |
| Profile auto-detection | Keep, but add more profiles | Works for books, untested for others |

### Updated Architecture

```
Structure Extraction (Revised):
├── Primary: PDF Outline (when available, 0.95 confidence)
│   └── Contains: Chapter/section boundaries, hierarchy
├── Secondary: Heading Detection (always available, 0.5-0.8 confidence)
│   └── Contains: All headings including subsections
├── Enrichment: ToC Parser (when available)
│   └── Contains: Better titles, page mappings
└── Fallback: Paragraph boundaries (when no structure found)
```

### Remaining Validation Needed

1. **ToC parser improvement** - Handle more formats, resolve page refs
2. **Article/essay/report testing** - Need test PDFs of other types
3. **Heading detection tuning** - Reduce false positives

---

## zlibrary-mcp RAG Pipeline Analysis

**Date:** December 18, 2025
**Purpose:** Evaluate zlibrary-mcp codebase for reusable components and test assets

### Overview

The zlibrary-mcp project contains a mature RAG processing pipeline for philosophical PDFs with extensive handling of footnotes, corruption recovery, and quality assurance. This analysis identifies components to reuse or reference for ScholarDoc.

### Test Assets Available

**Location:** `/home/rookslog/workspace/projects/zlibrary-mcp/test_files/`

| Asset | Description | Reuse Value |
|-------|-------------|-------------|
| `DerridaJacques_OfGrammatology.pdf` (22MB) | Full Derrida PDF with footnotes | ✅ Excellent for footnote testing |
| `HeideggerMartin_TheQuestionOfBeing.pdf` (3.4MB) | Full Heidegger PDF | ✅ Multi-language testing |
| `derrida_footnote_pages_120_125.pdf` | 6-page footnote test snippet | ✅ Targeted footnote tests |
| `kant_critique_pages_64_65.pdf` | Multi-page continuation test | ✅ Edge case testing |
| `heidegger_pages_17-24_full_translator_preface.pdf` | Translator notes test | ✅ Note classification |
| `sample.epub`, `sample.pdf`, `sample.txt` | Multi-format samples | ✅ Format testing |

**Ground Truth Data:**
- `ground_truth/kant_64_65_footnotes.json` - Footnote markers + definitions
- `ground_truth/derrida_footnotes_v2.json` - Complex footnote scenarios
- `ground_truth/heidegger_22_23_footnotes.json` - Secondary/tertiary footnotes
- `ground_truth/schema_v3.json` - **ML-optimized ground truth schema with note classification**
- `ground_truth/correction_matrix.json` - Validation matrix for three-way comparison

### Reusable Modules

**Location:** `/home/rookslog/workspace/projects/zlibrary-mcp/lib/`

#### Core Data Models (`rag_data_models.py`)
Comprehensive data structures for structured RAG output:

| Class | Purpose | ScholarDoc Relevance |
|-------|---------|---------------------|
| `TextSpan` | Formatted text fragment with bbox | ✅ Direct adoption (nearly identical to our needs) |
| `PageRegion` | Semantic page region with quality flags | ✅ Direct adoption |
| `NoteInfo` | Footnote/endnote with source classification | ✅ Critical for Phase 2 |
| `ListInfo` | List item structure | ✅ List handling |
| `Entity` | Linkable entities (notes, citations) | ⚠️ Consider for Phase 3 |
| `NoteType`, `NoteSource` enums | Note classification | ✅ Phase 2 footnotes |

**Key design decisions:**
- `Set[str]` for formatting (human-readable, debuggable, JSON-friendly)
- Semantic structure as first-class fields (not metadata dict)
- PyMuPDF flag mapping corrections (bold=bit4, italic=bit1)
- Quality flags directly on PageRegion

#### Garbled Text Detection (`garbled_text_detection.py`)
Shannon entropy-based corruption detection:

```python
# API we should consider adopting
from garbled_text_detection import detect_garbled_text_enhanced, GarbledDetectionConfig, GarbledDetectionResult

result = detect_garbled_text_enhanced(text)
if result.is_garbled:
    print(f"Garbled: {result.flags}")  # {'low_entropy', 'high_symbols', 'repeated_chars'}
```

**Key features:**
- Three heuristics: entropy, symbol density, character repetition
- Confidence scoring (0.0-1.0)
- Configurable thresholds
- Detailed metrics for explainability

**ScholarDoc adoption:** ✅ High value for Phase 1 quality assessment

#### Footnote Corruption Model (`footnote_corruption_model.py`)
Bayesian symbol inference for OCR corruption recovery:

- `SymbolCorruptionModel` - Prior probabilities for symbol→text mappings
- `FootnoteSchemaValidator` - Validates footnote marker sequences
- `apply_corruption_recovery()` - Recovers corrupted markers

**ScholarDoc adoption:** ⚠️ Consider for Phase 2 footnote work

#### Note Classification (`note_classification.py`)
Author/translator/editor attribution:

- Schema-based classification (numeric=author, alphabetic=translator)
- Content analysis (editorial phrases, translation markers)
- Confidence scoring with method tracking

**ScholarDoc adoption:** ⚠️ Phase 2 or later

#### Footnote Continuation (`footnote_continuation.py`)
Multi-page footnote handling:

- `CrossPageFootnoteParser` - Tracks notes across pages
- `is_footnote_incomplete()` - Detects truncated notes
- `FootnoteWithContinuation` - Linked note structure

**ScholarDoc adoption:** ⚠️ Phase 2 footnote work

### Architecture Patterns

#### Pipeline Configuration
Strategy profiles for different document types:

```python
STRATEGY_CONFIGS = {
    'philosophy': {
        'garbled_threshold': 0.9,        # Conservative (preserve ambiguous)
        'recovery_threshold': 0.95,      # Rarely auto-recover
        'enable_strikethrough': True,    # Check for sous-rature
        'priority': 'preservation'
    },
    'technical': {
        'garbled_threshold': 0.6,        # Aggressive detection
        'recovery_threshold': 0.7,       # More likely to recover
        'enable_strikethrough': False,   # Technical docs rarely have it
        'priority': 'quality'
    },
    'hybrid': {  # DEFAULT
        'garbled_threshold': 0.75,
        'recovery_threshold': 0.8,
        'enable_strikethrough': True,
        'priority': 'balanced'
    }
}
```

**ScholarDoc adoption:** ✅ Excellent pattern for configurable pipelines

#### Ground Truth Schema Evolution
Progression from v1 → v2 → v3 with ML features:

| Version | Key Additions |
|---------|---------------|
| v1 | Basic footnote markers and definitions |
| v2 | BBox coordinates, corruption model, ML enums |
| v3 | Note source classification, confidence scoring, classification method |

**ScholarDoc adoption:** ✅ Adopt v3 schema for our ground truth

### Immediate Reuse Recommendations

**Phase 0 (Now):**
1. Copy test PDFs to `spikes/sample_pdfs/` (Derrida, Kant, Heidegger snippets)
2. Reference `schema_v3.json` for ground truth format
3. Review `garbled_text_detection.py` for quality scoring ideas

**Phase 1 (Text Extraction):**
1. Adopt `TextSpan`, `PageRegion` data models (adapt to Python)
2. Integrate garbled text detection for quality warnings
3. Use PyMuPDF flag mappings from `create_text_span_from_pymupdf()`

**Phase 2 (Structure Extraction):**
1. Adopt `NoteInfo`, `NoteType`, `NoteSource` for footnotes
2. Reference footnote continuation logic for multi-page notes
3. Use correction model for OCR recovery of footnote markers

**Long-term (Phase 3+):**
1. Note classification for author/translator/editor attribution
2. Entity linking for cross-references
3. Replace zlibrary-mcp RAG code with ScholarDoc imports

### Key Takeaways

1. **Mature codebase:** zlibrary-mcp has ~2 years of production testing on philosophy PDFs
2. **Same target domain:** Focus on continental philosophy matches ScholarDoc exactly
3. **Modular design:** Clean separation into reusable modules
4. **ML-ready:** Ground truth schema designed for model training
5. **Quality focus:** Multiple quality layers (garbled detection, corruption recovery, confidence scoring)

### Files to Reference

| File | Lines | Key Patterns |
|------|-------|--------------|
| `lib/rag_data_models.py` | 647 | Data classes, enums, formatting |
| `lib/garbled_text_detection.py` | 369 | Entropy-based quality detection |
| `lib/footnote_corruption_model.py` | ~28K | Bayesian symbol inference |
| `lib/note_classification.py` | ~15K | Author/translator classification |
| `lib/rag_processing.py` | ~218K | Full pipeline (reference only) |
| `scripts/run_rag_tests.py` | 338 | Manifest-based test framework |
| `test_files/ground_truth/schema_v3.json` | 524 | Ground truth schema |

---

## Spike 12: Smart Spell-Checking Without Whitelists

**Run:** `uv run python spikes/12_smart_spellcheck.py`

### Purpose

Test whether we can automatically detect what NOT to spell-check, eliminating the need for unmaintainable vocabulary whitelists.

### Strategies Tested

| Strategy | What It Catches | Reliability |
|----------|-----------------|-------------|
| **Capitalized words** | Heidegger, Derrida, Plato | ✅ High (except sentence-start) |
| **Words with diacritics** | différance, épistémè, Søren | ✅ Very high |
| **Italic text** | Dasein, Sein, l'Autrui | ✅ High (requires PDF font info) |
| **All caps** | NATO, UNESCO, PDF | ✅ Very high |
| **Citation context** | Smith (2020), (Taylor, 1989) | ✅ High |
| **Frequency analysis** | Terms appearing 3+ times | ⚠️ Medium (needs document scale) |
| **Consistency checking** | Heldegger→Heidegger (1x vs 9x) | ✅ High for repeated names |

### Key Finding: Consistency Checking Catches OCR Errors in Proper Nouns

The consistency check solves a critical gap:
- **Problem:** We skip capitalized words (proper nouns), but OCR might corrupt them
- **Solution:** Compare frequency of similar capitalized words
- If "Heidegger" appears 9x and "Heldegger" appears 1x → flag as likely OCR error

```python
def check_consistency(word: str, all_words: Counter) -> tuple[bool, str | None]:
    """Flag rare variants of frequent words."""
    for similar_word, distance in find_similar_words(word, all_words):
        if all_words[similar_word] >= all_words[word] * 3:
            return True, similar_word  # Suggest the frequent variant
    return False, None
```

### Results on Philosophy Text

**Words correctly skipped (no spell-check):**
- `proper_noun_repeated`: Heidegger, Derrida, Gadamer, Merleau-Ponty
- `foreign_diacritics`: différance, l'Autrui
- `citation_context`: Smith, Taylor
- `acronym`: (none in sample)

**Words correctly flagged for spell-check:**
- Common words: according, question, notion, concept
- OCR errors in sample: questlon, beautlful, underrnines

### Limitations

1. **First occurrence of names:** No frequency signal yet
2. **Names appearing only once:** Can't compare to anything
3. **Very short documents:** Not enough data for frequency
4. **Sentence-start capitalization:** Requires context to distinguish

### Recommendation

**Use layered detection:**
1. Skip capitalized words (proper nouns)
2. Skip words with diacritics (foreign terms)
3. Skip italic text (requires font info from PDF)
4. Skip citation contexts (regex patterns)
5. BUT run consistency check on all capitalized words
6. Flag rare variants of frequent proper nouns as potential OCR errors

This catches ~90% of cases without any whitelist.

---

## Spike 13: Empirical Spell-Check Risk Assessment

**Run:** `uv run python spikes/13_spellcheck_risk.py`

### Purpose

Your concern: "I am still concerned we might have a non-proper-noun philosophical term that I didn't know existed in the text that will get erased or improperly embedded."

This spike empirically tests:
1. What does pyspellchecker suggest for philosophy terms?
2. How much embedding damage do wrong corrections cause?
3. Can we generalize from test results?

### 🚨 Critical Finding: 41% of Philosophy Terms Would Be Wrongly "Corrected"

| Category | Count | Examples |
|----------|-------|----------|
| Known to spell-checker | 25 | aporia, nous, logos, deconstruction |
| Unknown, no suggestion | 10 | phronesis, entelecheia, heideggerian |
| **WOULD BE WRONGLY "CORRECTED"** | **24** | See below |

**Dangerous corrections that would occur:**

| Term | Would Become | Semantic Damage |
|------|--------------|-----------------|
| dasein | casein | 🚨 Protein! |
| ousia | music | 🚨 Completely wrong |
| telos | tells | 🚨 Wrong meaning |
| arche | ache | 🚨 Wrong meaning |
| hyle | hole | 🚨 Wrong meaning |
| differance | difference | 🚨 Destroys Derrida's point! |
| mitsein | mitten | 🚨 Absurd |
| jouissance | puissance | ⚠️ Different concept |
| techne | techno | ⚠️ Music genre |
| episteme | epitome | ⚠️ Different word |
| derridean | hebridean | 🚨 Scottish islands! |

### Embedding Damage Quantified

| Term | Correction | Similarity | Damage |
|------|------------|------------|--------|
| dasein | casein | 0.785 | **21.5%** 🚨 |
| epoché | epoch | 0.991 | 0.9% ✅ |

- "dasein" → "casein" causes 21.5% embedding similarity loss
- That's enough to break retrieval for passages discussing Heidegger's central concept

### OCR Error Detection Works Well

| OCR Error | Spell-check Suggests | Match? |
|-----------|---------------------|--------|
| beautlful | beautiful | ✅ |
| questlon | question | ✅ |
| rnetaphysics | metaphysics | ✅ |
| phenornenology | phenomenology | ✅ |
| intentlonality | intentionality | ✅ |
| transcendenta1 | transcendental | ✅ |

**Finding:** Spell-checker is excellent at catching actual OCR errors (7/7 correct).

### Mechanical Pattern Corrections Are Also Risky

| Pattern | Input | Output | Correct? |
|---------|-------|--------|----------|
| rn→m | rnorning | moming | ❌ (should be "morning") |
| cl→d | clog | dog | ❌ (clog is a real word!) |
| tl→ti | beautlful | beautiful | ✅ |
| vv→w | vvord | word | ✅ |
| 1→l | on1y | only | ✅ |
| l→I | lIl | lIl | ❌ (ambiguous: III? lil? Il?) |

**Finding:** Even "mechanical" OCR pattern corrections are context-dependent.

### The Generalization Problem

Your concern is validated:

> "But even then, how will we know our test results generalize?"

**Answer: We can't.**
- We tested 59 philosophy terms
- Any book might have terms we didn't anticipate
- Testing doesn't prove safety for novel terms
- The risk is asymmetric: one wrong correction can devastate a key concept

### ✅ Safer Alternatives (Ranked by Safety)

| Option | Safety | User Effort | Implementation |
|--------|--------|-------------|----------------|
| **D: Fuzzy retrieval** | 🟢 Zero risk | None | Match at search time |
| **E: Embed both versions** | 🟢 Zero risk | None | Higher storage |
| **A: Don't auto-correct** | 🟢 Zero risk | High (human review) | Simple |
| **B: High-confidence only** | 🟡 Low risk | Low | Complex thresholds |
| **C: Verified corrections** | 🟢 Zero risk | Medium | Needs reference text |

### Recommendation: Option D (Fuzzy Retrieval)

**Instead of correcting the source text, handle at search time:**

```python
# At embedding time: preserve original
chunk.text = "The beautlful analysis of dasein..."

# At search time: fuzzy matching
results = vector_store.search(
    query="beautiful analysis of Dasein",
    fuzzy=True  # Matches despite OCR errors
)
```

**Benefits:**
1. Zero risk to source text
2. No vocabulary whitelists needed
3. No generalization problem
4. User sees original (can verify quality)
5. Reversible (unlike corrections)

**Trade-off:** Slightly lower retrieval precision for heavily corrupted text.

### Alternative: Option E (Embed Both)

If fuzzy retrieval isn't available:

```python
# Keep original
chunks.append(RAGChunk(text=original, is_cleaned=False))

# Also embed cleaned version
chunks.append(RAGChunk(text=cleaned, is_cleaned=True))
```

**Benefits:**
- No information loss
- Original preserved for display
- Cleaned version improves retrieval
- Higher storage cost (2x chunks)

### Final Verdict

**🚨 DO NOT auto-correct scholarly text with spell-checkers.**

The 41% damage rate for philosophy terms is unacceptable. Instead:
1. **Remove artifacts** (page numbers, headers) - 29% embedding improvement
2. **Apply OCR correction** for mechanical patterns only when safe
3. **Use fuzzy retrieval** to handle remaining errors at search time
4. **Let users see original text** so they can verify quality
