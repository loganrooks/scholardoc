# Spike Findings

> **Purpose:** Document what we learn from exploration before committing to designs  
> **Status:** Not started - need sample PDFs

---

## Sample PDFs Needed

Before running spikes, acquire 3-5 diverse philosophy PDFs:

1. **Classic scholarly edition** - e.g., Cambridge Kant (two-column, A/B pagination)
2. **Modern monograph** - single-column academic book
3. **Article/chapter** - shorter piece with standard footnotes
4. **Public domain scan** - OCR'd older text (stress test)
5. **EPUB-originated PDF** - reflowable source converted to PDF

**Sources:**
- Project Gutenberg (public domain)
- PhilPapers (academic articles)
- Publisher sample chapters
- Open access journals

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

### Results: [PDF Name]

_Run spike on each sample PDF and record findings_

**Structure observations:**
- 

**Font patterns:**
- Body font:
- Heading fonts:

**Layout:**
- Multi-column:
- Footnote regions:

**Quality:**
- Born-digital:
- Text extraction quality:

---

## Spike 02: Library Comparison

**Run:** `uv run python spikes/02_library_comparison.py <pdf>`

### Results: [PDF Name]

| Library | Time | Chars | Quality Notes |
|---------|------|-------|---------------|
| pymupdf | | | |
| pdfplumber | | | |
| pypdf | | | |
| pymupdf4llm | | | |

**Best text quality:**

**Best speed:**

**Best for our needs:**

**Recommendation for ADR-001:**

---

## Spike 03: Heading Detection

**Run:** `uv run python spikes/03_heading_detection.py <pdf>`

### Results: [PDF Name]

| Method | Headings Found | True Positives | False Positives |
|--------|---------------|----------------|-----------------|
| font_size | | | |
| bold | | | |
| isolation | | | |
| combined | | | |
| pymupdf4llm | | | |

**Most accurate method:**

**Recommended approach:**

**Confidence threshold:**

---

## Spike 04: Footnote Detection

**Run:** `uv run python spikes/04_footnote_detection.py <pdf>`

### Results: [PDF Name]

**Footnote style in this document:** (footnotes per page / endnotes / mixed)

**Detection results:**
- Page-region method accuracy:
- Font-size method accuracy:
- Marker matching success rate:

**Feasibility assessment:**
- [ ] Include in Phase 1
- [ ] Defer to Phase 2
- [ ] Needs different approach
- [ ] Not worth the complexity

---

## Spike 05: OCR Quality Survey

**Run:** `uv run python spikes/05_ocr_quality_survey.py <pdf> [--detailed] [--compare-image]`

### Survey Results by Source

Track quality across different PDF sources to determine if custom OCR is needed.

| Source | PDFs Tested | Acceptable | Degraded | Poor | Notes |
|--------|-------------|------------|----------|------|-------|
| Internet Archive | | | | | |
| Google Books | | | | | |
| JSTOR | | | | | |
| Project Gutenberg | | | | | |
| HathiTrust | | | | | |
| Publisher PDFs | | | | | |
| Other | | | | | |

### Individual Document Results

#### [Document 1 Name]
- **Source:** 
- **Recommendation:** ACCEPTABLE / DEGRADED / POOR
- **Garbage ratio:**
- **Valid word ratio:**
- **Key issues:**

#### [Document 2 Name]
...

### Conclusions for Phase 4 OCR

Based on survey:
- What % of target documents have acceptable text layers?
- What % need correction?
- What % need full re-OCR from images?
- Is custom structure-aware OCR worth the investment?

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
| Q1: Page number format | | |
| Q2: Multi-column handling | | |
| Q3: Born-digital detection | | |
| Q4: Heading detection strategy | | |
| Q5: Footnote accuracy threshold | | |
| Q6: GROBID integration | | |

### Validated Assumptions

- [ ] _List assumptions confirmed by spikes_

### Invalidated Assumptions

- [ ] _List assumptions disproven by spikes_

### Surprises

- _What didn't we expect?_

---

## Design Changes Required

Based on spike findings:

### ADR-001 (Library Choice)
- [ ] Confirm PyMuPDF recommendation
- [ ] Or change to: ___
- [ ] Rationale:

### SPEC.md Updates
- [ ] _List specific sections to revise_

### REQUIREMENTS.md Updates
- [ ] _List acceptance criteria changes_

### Scope Changes
- [ ] Move footnotes to Phase 2?
- [ ] Simplify heading detection?
- [ ] Other:

---

## Next Steps

After completing all spikes:

1. [ ] Update ADR-001 with empirical decision
2. [ ] Revise SPEC.md based on findings
3. [ ] Update QUESTIONS.md with answers
4. [ ] Adjust ROADMAP.md if scope changes
5. [ ] Create test fixtures from sample PDFs
6. [ ] Begin Phase 1 implementation
