# Open Questions

> **Purpose:** Track questions requiring research or decisions before implementation
> **Status:** Phase 0 exploration complete - most questions resolved empirically
> **Last Updated:** December 18, 2025

---

## High Priority (Blocks Phase 1)

### Q1: Page Number Output Format ✅ RESOLVED
**Question:** How should page numbers appear in the Markdown output?

**Options:**
1. **Inline markers:** `The argument proceeds... <!-- page: 42 -->`
2. **Heading markers:** `## [Page 42]` as separate blocks
3. **Metadata only:** Page info in frontmatter/sidecar, not in text
4. **Configurable:** Let user choose

**Resolution:** **Option 4 (Configurable)** with inline markers as default.

**Evidence (Spike 01-02):**
- PyMuPDF provides PDF page labels (Roman numerals, Arabic, mixed)
- Derrida PDF has proper labels: "Cover", "i", "ii", "iii"... "1", "2", etc.
- Kant PDF has labels even for OCR'd scans
- Page labels are critical for scholarly citations

**Implementation:**
- Default: Inline HTML comments `<!-- page: 42 -->`
- Option: Heading markers for visual documents
- Always: Page mapping in metadata frontmatter
- Use PDF page labels when available, fall back to 1-indexed

**See:** spikes/FINDINGS.md § Spike 01, § Spike 02

---

### Q2: Multi-Column Layout Handling ✅ RESOLVED
**Question:** How should we handle multi-column PDFs (common in academic papers)?

**Resolution:** **Defer to Phase 2** - not needed for Phase 1.

**Evidence (Spike 01):**
- **All tested philosophy PDFs are single-column**
- Comay: Single column throughout
- Derrida: Single column
- Kant: Single column
- Heidegger volumes: Single column

**Decision:** Philosophy/humanities texts are primarily single-column. Multi-column handling can be added in Phase 2 if scientific paper support is requested.

**See:** spikes/FINDINGS.md § Spike 01

---

### Q3: What Constitutes "Born-Digital" PDF? ✅ RESOLVED
**Question:** How do we detect if a PDF is born-digital vs. scanned?

**Resolution:** Use multiple heuristics - no single indicator is definitive.

**Evidence (Spike 01, Spike 05):**

| Indicator | Born-Digital | Scanned/OCR'd |
|-----------|--------------|---------------|
| Creator metadata | InDesign, Word, LaTeX | "Adobe Paper Capture", ABBYY |
| Font count | Reasonable (5-20) | Many (Kant: 243 fonts!) |
| Image blocks | Few/none | Every page has image |
| Text quality | Perfect spelling | OCR errors present |
| Font embedding | Subset fonts | OCR-generated fonts |

**Implementation:**
```python
def is_likely_scanned(doc):
    # Check for OCR creator tools
    if "Paper Capture" in doc.metadata.get("creator", ""):
        return True
    # Check for image + text overlay pattern
    if page_has_image_with_text_overlay(page):
        return True
    # Check font count (OCR creates many fonts)
    if len(doc.fonts) > 100:
        return True
    return False
```

**Warning behavior:** Issue quality warning for scanned docs, don't fail.

**See:** spikes/FINDINGS.md § Spike 01, § Spike 05

---

### Q4: Heading Detection Strategy ✅ RESOLVED
**Question:** How do we reliably detect headings in PDFs?

**Resolution:** **Combined method with confidence threshold ≥0.6**

**Evidence (Spike 03):**

| Method | Comay | Derrida | Assessment |
|--------|-------|---------|------------|
| Font size only | 0 headings | 30 headings | Varies by doc |
| Bold only | 0 headings | **36 headings** | Best for Derrida |
| Isolation only | 180 headings | 33 headings | Too many false positives |
| **Combined** | **21 headings** | 46 headings | ✅ Best overall |

**Implementation:**
1. Score each candidate using multiple signals (size, bold, isolation, position)
2. Sum signals into confidence score (0.0-1.0)
3. Accept headings with confidence ≥0.6
4. Use font size ratio: heading font / body font ≥ 1.2

**Detected accurately:**
- Chapter titles: "Introduction", "Mourning Sickness", "FORCE AND SIGNIFICATION"
- Section headings within chapters
- "Contents", "Acknowledgments", "Abbreviations"

**See:** spikes/FINDINGS.md § Spike 03

---

## Medium Priority (Blocks Phase 2)

### Q5: Footnote Extraction Accuracy Threshold ✅ RESOLVED
**Question:** What accuracy is acceptable for footnote extraction?

**Resolution:** **Defer footnote linking to Phase 2** - philosophy texts use ENDNOTES.

**Critical Finding (Spike 04):**
- **Both tested philosophy books use ENDNOTES, not footnotes!**
- Notes are collected at the back of the book
- Superscript markers in body text don't have matching content on same page
- Page-region detection finds publisher info, not footnotes

**Evidence:**
| Document | Footnote Style | Detection Results |
|----------|----------------|-------------------|
| Comay | Endnotes | 0/5 markers matched (notes at back) |
| Derrida | Endnotes | Notes section found at page 378 |

**Phase 1 approach:** Just preserve superscript markers in text.
**Phase 2 approach:** Detect endnote sections and link markers. Use confidence scores (option 3).

**See:** spikes/FINDINGS.md § Spike 04

---

### Q6: GROBID Integration Strategy ✅ RESOLVED
**Question:** How should we integrate with GROBID for scientific papers?

**Resolution:** **Option 4 - No integration for Phase 1**

**Evidence (Spike 01-02):**
- PyMuPDF provides everything needed for Phase 1
- Our focus is philosophy/humanities texts (single-column, endnotes)
- GROBID is specialized for scientific papers (multi-column, citations)
- No overlap with current target corpus

**Future consideration:** May add GROBID adapter in Phase 3 if scientific paper support is requested.

**See:** spikes/FINDINGS.md § Consolidated Findings

---

### Q7: EPUB Note Handling
**Question:** EPUB3 has semantic footnote markup (`epub:type="footnote"`). EPUB2 doesn't. How do we handle both?

**EPUB3:** Use semantic markup (reliable)
**EPUB2:** Heuristics based on link patterns, class names, position

**Decision:** _Pending - research EPUB landscape_

---

## Low Priority (Future Phases)

### Q8: Should We Support PDF Annotations?
Some PDFs have highlighting, comments, sticky notes. Should we extract these?

### Q9: Image Handling
Should we extract/reference images? Convert to alt-text descriptions? Ignore?

### Q10: Language Support
What languages should we prioritize? Philosophy texts exist in German, French, Greek, Latin, etc.

---

## Phase 4 Questions (OCR Research)

### Q11: Base OCR Engine Selection
**Question:** Which OCR engine should we build on?

**Options:**
1. **Tesseract** - Mature, widely used, LSTM models
2. **EasyOCR** - Neural network based, easier API
3. **TrOCR/Donut** - Transformer-based, state of the art
4. **Cloud APIs** - Google Vision, AWS Textract (adds cost/dependency)

**Considerations:**
- Per-character confidence scores needed for our approach
- Training/fine-tuning capabilities
- Speed and resource requirements
- License compatibility

**Decision:** _Pending - needs evaluation in Phase 4_

---

### Q12: Sequence Model Architecture
**Question:** What type of model for sequence correction?

**Options:**
1. **Markov chains** - Simple, interpretable, fast
2. **CRF (Conditional Random Fields)** - Good for sequence labeling
3. **BiLSTM** - Neural, flexible, needs more data
4. **Transformer** - Most powerful, needs most data/compute
5. **Hybrid** - Markov for simple sequences, neural for complex

**Considerations:**
- Amount of training data available
- Interpretability requirements
- Runtime performance
- Maintenance complexity

**Decision:** _Pending - needs research_

---

### Q13: Training Data Strategy
**Question:** How do we get ground truth for training sequence models?

**Options:**
1. **Manual annotation** - Accurate but expensive
2. **Synthetic corruption** - Generate errors from clean text
3. **Parallel texts** - Born-digital + scanned versions
4. **Crowdsourced correction** - Users correct errors
5. **Semi-supervised** - Use high-confidence OCR as pseudo-labels

**Considerations:**
- Philosophy text availability
- Error pattern realism
- Scale needed

**Decision:** _Pending_

---

### Q14: Scanned Document Prevalence ✅ PARTIALLY RESOLVED
**Question:** What portion of our target documents are scanned vs. born-digital?

**Evidence (Spike 05, zlibrary-mcp analysis):**

| Source | Born-Digital | Scanned | Notes |
|--------|--------------|---------|-------|
| Comay (Stanford Press, 2011) | ✅ | | Modern academic press |
| Derrida (Routledge, 1978) | ✅ | | Re-released digital |
| Kant (Hackett, 1987) | | ✅ | Adobe Paper Capture |
| Heidegger (Harper, various) | Mixed | Mixed | Varies by edition |

**Preliminary findings:**
- ~70% of target documents have acceptable text layers (born-digital)
- ~30% need correction (scans with various issues)
- <5% need full re-OCR (truly poor quality)

**Resolution:** Custom structure-aware OCR (Phase 4) is **valuable but not critical** for Phase 1. Focus on:
1. Born-digital PDFs work great out of the box
2. OCR'd scans work with spell-check correction
3. Phase 4 OCR is for optimization, not necessity

**Still needed:** Larger corpus survey to validate percentages

---

### Q15: Human-in-the-Loop Interface
**Question:** How should we handle OCR uncertainty?

**Options:**
1. **Silent best-effort** - Always output something, may be wrong
2. **Confidence markers** - Mark uncertain regions in output
3. **Review queue** - Separate file of items needing human review
4. **Interactive correction** - UI for reviewing/correcting during processing

**Considerations:**
- Use case (batch processing vs. interactive)
- Acceptable error rates
- User expertise

**Decision:** _Pending_

---

### Q16: Text Layer vs Image Extraction Decision ✅ RESOLVED
**Question:** How do we decide when to use the existing text layer vs. re-extracting from images?

**Resolution:** **Option 3 (Quality threshold) + spell-check correction** - existing OCR + correction beats re-OCR.

**Critical Findings (Spike 08-09):**

1. **Existing OCR + spell correction > TrOCR re-OCR**
   - Existing OCR errors are "fixable" by spell checker
   - TrOCR produces different errors that are harder to fix
   - Example: "Beautlful" → correctable; "JUDEMENT" → novel misspelling

2. **Embedding impact comparison:**
   | Ground Truth | Existing OCR Similarity | TrOCR Similarity | Winner |
   |--------------|-------------------------|------------------|--------|
   | "Beautiful" | 0.515 ("Beautlful") | 0.381 ("BEAUTIFAL") | Existing |
   | "judgment" | **1.000** ("jUdgment") | 0.288 ("JUDEMENT") | Existing |
   | "Practical" | **1.000** | 0.621 ("PRACTION") | Existing |

3. **Mid-word caps don't hurt embeddings:** "jUdgment" → 1.000 similarity
4. **Character errors DO hurt:** Even 1-2% error rate degrades RAG significantly

**Implementation:**
1. Always use existing text layer first
2. Run quality assessment (entropy, word validity, garbage ratio)
3. Apply spell-check correction for character errors
4. Only re-OCR if text layer is truly garbage (<50% valid words)
5. Warn users about quality issues

**OCR Correction Module:** `scholardoc/normalizers/ocr_correction.py`
- Quality scoring with `is_usable_for_rag` threshold
- Pattern-based correction for known OCR errors
- Philosophy vocabulary whitelist (~120 terms)

**See:** spikes/FINDINGS.md § Spike 08, § Spike 09, § OCR Correction Improvements

---

### Q17: Ground Truth Corpus Strategy
**Question:** How do we build a reliable ground truth corpus for evaluating ALL components (not just OCR)?

**Scope:** Ground truth needed for:
- Page number detection (Phase 1)
- Heading detection (Phase 1)
- Footnote/endnote detection (Phase 2)
- Table detection (Phase 2)
- Region classification (Phase 4)
- OCR accuracy (Phase 4)

**Approach: Claude + Human Hybrid**
1. Claude analyzes PDF, proposes annotations with confidence scores
2. Human reviews low-confidence items + random sample
3. Corrections improve future annotations
4. Verified corpus grows incrementally

**Key resources:**
- `docs/design/GROUND_TRUTH_STRATEGY.md` - Full strategy document
- `.claude/agents/ground-truth-annotator.md` - Claude annotation agent
- `spikes/07_annotation_review.py` - Human review interface
- `.claude/commands/annotate.md` - Workflow command

**Open questions:**
- How much annotation per document? (full vs sampled)
- What's the minimum viable corpus size?
- How do we handle inter-annotator disagreement?

**Decision:** _In progress - piloting workflow_

---

## Resolved Questions

The following questions were resolved through Phase 0 spike exploration (December 2025):

| Question | Resolution | Evidence |
|----------|------------|----------|
| Q1: Page number format | Configurable, default inline markers | Spike 01-02 |
| Q2: Multi-column handling | Defer to Phase 2 (philosophy is single-column) | Spike 01 |
| Q3: Born-digital detection | Multiple heuristics (creator, fonts, images) | Spike 01, 05 |
| Q4: Heading detection | Combined method, confidence ≥0.6 | Spike 03 |
| Q5: Footnote accuracy | Defer to Phase 2 (philosophy uses endnotes) | Spike 04 |
| Q6: GROBID integration | No integration for Phase 1 | Spike 01-02 |
| Q14: Scanned prevalence | ~70% born-digital, ~30% need correction | Spike 05 |
| Q16: Text layer vs re-OCR | Use existing + spell correction | Spike 08-09 |

### Key Insights from Exploration

1. **OCR quality matters for RAG** - Character errors devastate embedding similarity (0.5-0.65)
2. **Existing OCR + correction > re-OCR** - Spell-check fixes more errors than TrOCR introduces
3. **Philosophy texts use endnotes** - Defer footnote linking to Phase 2
4. **PyMuPDF is the right choice** - 32-57x faster, page labels, font info
5. **Mid-word caps don't hurt** - "jUdgment" embeds perfectly, only real misspellings matter

### Still Open

- Q7: EPUB note handling (Phase 3)
- Q8-Q10: Low priority features
- Q11-Q13, Q15: Phase 4 OCR research
- Q17: Ground truth strategy (in progress)
