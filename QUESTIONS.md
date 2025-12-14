# Open Questions

> **Purpose:** Track questions requiring research or decisions before implementation  
> **Status:** Active - gathering input

---

## High Priority (Blocks Phase 1)

### Q1: Page Number Output Format
**Question:** How should page numbers appear in the Markdown output?

**Options:**
1. **Inline markers:** `The argument proceeds... <!-- page: 42 -->` 
2. **Heading markers:** `## [Page 42]` as separate blocks
3. **Metadata only:** Page info in frontmatter/sidecar, not in text
4. **Configurable:** Let user choose

**Considerations:**
- RAG systems typically ignore HTML comments
- Heading markers create artificial structure
- Metadata-only loses position information
- Configurable adds complexity but maximizes flexibility

**Decision:** _Pending_

---

### Q2: Multi-Column Layout Handling  
**Question:** How should we handle multi-column PDFs (common in academic papers)?

**Options:**
1. **Merge to single column:** Reading order detection, merge columns
2. **Preserve columns:** Mark column boundaries, keep separate
3. **Configurable:** Let user choose based on use case

**Considerations:**
- Most RAG use cases want merged, readable text
- Column detection is imperfect
- Some documents mix single and multi-column pages

**Decision:** _Pending - default to merge, option to preserve_

---

### Q3: What Constitutes "Born-Digital" PDF?
**Question:** How do we detect if a PDF is born-digital vs. scanned?

**Approach ideas:**
- Check for embedded fonts (born-digital usually has them)
- Check text layer quality (scanned OCR is often poor)
- Sample text extraction and check for garbage characters
- Check for image-only pages

**Follow-up:** Should we warn users or fail silently when encountering scanned pages?

**Decision:** _Pending_

---

### Q4: Heading Detection Strategy
**Question:** How do we reliably detect headings in PDFs?

**Signals available:**
- Font size (larger = heading)
- Font weight (bold = heading)
- Position on page (top, standalone line)
- Whitespace (more space above = heading)
- Style consistency (same formatting = same level)

**Challenges:**
- Philosophy texts often have unusual formatting
- Some books use font changes for emphasis, not structure
- No universal heading conventions

**Approach:** _Research needed - see PyMuPDF4LLM capabilities_

---

## Medium Priority (Blocks Phase 2)

### Q5: Footnote Extraction Accuracy Threshold
**Question:** What accuracy is acceptable for footnote extraction?

**Context:** Footnote detection in PDFs is heuristic-based. We will have false positives (text marked as footnote that isn't) and false negatives (missed footnotes).

**Options:**
1. **High precision, low recall:** Only mark footnotes when very confident
2. **High recall, low precision:** Mark anything that might be a footnote
3. **Confidence scores:** Mark all candidates with confidence, let user filter
4. **Manual verification mode:** Suggest footnotes for human review

**Considerations:**
- Scholars need accuracy for citation
- RAG systems may tolerate some noise
- Different use cases have different tolerances

**Decision:** _Pending - needs user research_

---

### Q6: GROBID Integration Strategy
**Question:** How should we integrate with GROBID for scientific papers?

**Options:**
1. **Optional dependency:** Check for GROBID server, use if available
2. **Separate module:** `scholardoc.scientific` that requires GROBID
3. **Adapter pattern:** GROBID as one of several extraction backends
4. **No integration:** Recommend GROBID for scientific papers, stay focused

**Considerations:**
- GROBID is excellent for scientific papers
- Adds complexity (Docker/server dependency)
- Our focus is philosophy/humanities texts
- Could be complementary, not overlapping

**Decision:** _Pending_

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

### Q14: Scanned Document Prevalence
**Question:** What portion of our target documents are scanned vs. born-digital?

**Why it matters:** If 90% of philosophy PDFs are born-digital, custom OCR may not be worth the investment. If 50% are scanned, it's essential.

**Research needed:**
- Survey academic PDF sources
- Sample from Project Gutenberg, Internet Archive, JSTOR
- Ask target users about their corpora

**Decision:** _Pending - needs user research_

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

### Q16: Text Layer vs Image Extraction Decision
**Question:** How do we decide when to use the existing text layer vs. re-extracting from images?

**Context:** Many philosophy PDFs have text layers, but they may be poor quality (bad OCR from years ago). We need to detect this and fall back to image extraction when necessary.

**Options:**
1. **Always use text layer** - Fast, but accepts errors
2. **Always re-OCR** - Consistent, but slow and wasteful for good text layers
3. **Quality threshold** - Detect garbage ratio, word validity, use text layer if above threshold
4. **Hybrid spot-check** - Use text layer, but verify sample regions against images
5. **User choice** - Let user specify per document or globally

**Considerations:**
- False positive cost: Re-OCR when text layer was fine (wasted compute)
- False negative cost: Use bad text layer (garbage output)
- Different sources have different quality patterns

**Related:** See `spikes/05_ocr_quality_survey.py` for detection approaches

**Decision:** _Pending - needs survey results_

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

_None yet - project is in requirements phase_

<!-- Template for resolved:
### Q#: [Question]
**Resolution:** [Decision made]
**Date:** [Date]
**Rationale:** [Why we decided this]
**See:** [Link to ADR if applicable]
-->
