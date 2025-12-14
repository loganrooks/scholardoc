# Custom OCR Design: Structure-Aware Recognition for Scholarly Documents

> **Status:** Early Design / Research Phase  
> **Target:** Phase 4  
> **Last Updated:** December 2025

---

## Problem Statement

### The Real Problem: Poor Existing OCR

Many digitized philosophy texts have **existing but unreliable OCR text layers**. This is different from "no OCR" - the PDF has a text layer, but it's garbage:

| Source | Common Issues |
|--------|---------------|
| Google Books scans | Inconsistent quality, especially older texts |
| Internet Archive | Variable OCR engines over the years |
| JSTOR older content | Early OCR technology, never re-processed |
| Library digitization projects | Budget constraints, batch processing errors |
| Publisher back-catalogs | Quick digitization, minimal QA |

**Example:** A PDF of Hegel's *Phenomenology of Spirit* might have:
- Text layer that extracts as "Phänomenologie des Geistes" → "Phanornenologie des Gcistes"
- Greek passages completely garbled
- Footnote numbers confused with body text
- Page numbers extracted as random characters

### Why Standard Approaches Fail

**"Just use the text layer"** - But the text layer is wrong.

**"Just run Tesseract"** - Tesseract treats each page independently, losing:
- Sequence context (page 42 → 43, not 42 → 4B)
- Document-level vocabulary (names, terms that recur)
- Structural classification (is this a heading? footnote? page number?)

**"Use a modern ML OCR"** - Better, but still:
- Trained on general documents, not scholarly texts
- No awareness of philosophy-specific patterns (Greek, German, Latin mixed)
- No structure-aware correction

### Our Opportunity

We can build something better by combining:

1. **Image extraction** from PDF (when text layer is unreliable)
2. **Structure-aware sequence models** (page numbers, footnotes, etc.)
3. **Semantic classification** (what TYPE of text is this?)
4. **Domain-specific vocabulary** (philosophy terms, author names)

---

## Two Intertwined Problems

### Problem 1: Text Extraction (What characters?)

Getting the right characters from image data:
- "Heidegger" not "Heideggar" or "Ileidegger"
- "Phänomenologie" not "Phanornenologie"
- "42" not "4Z" or "42." or "- 42 -"

**Aided by:**
- Vocabulary priors (seen "Heidegger" before)
- Sequence models (page 41 → probably 42)
- Language models (German/Greek character patterns)

### Problem 2: Semantic Classification (What type of text?)

Understanding what role text plays in the document:
- Is "42" a page number, footnote marker, or part of a date?
- Is this line a heading or emphasized body text?
- Is this small text at the bottom a footnote or a running footer?

**Aided by:**
- Position on page (top/bottom/margin)
- Font characteristics (size, weight, style)
- Sequence patterns (footnote 7 → 8 → 9)
- Surrounding context

### Why They're Connected

Classification helps extraction:
- If we KNOW this is a page number region, we can apply stronger sequence priors
- If we KNOW this is a footnote, we expect superscript markers

Extraction helps classification:
- If we extract "Chapter" or "§", this is probably a heading
- If we extract a superscript number, this is probably a footnote marker

**The structure-aware system does both simultaneously.**

---

## When to Use Image Data vs Text Layer

### Detection: Is the Text Layer Reliable?

```python
class TextLayerQuality(Enum):
    GOOD = "good"           # Use text layer directly
    DEGRADED = "degraded"   # Use text layer with corrections
    POOR = "poor"           # Re-extract from images
    MISSING = "missing"     # Must extract from images

def assess_text_layer(page) -> TextLayerQuality:
    """Determine if we should trust the text layer."""
    
    # Check 1: Does text layer exist?
    text = page.get_text()
    if not text.strip():
        return TextLayerQuality.MISSING
    
    # Check 2: Garbage character ratio
    garbage_ratio = count_garbage_chars(text) / len(text)
    if garbage_ratio > 0.1:  # >10% garbage
        return TextLayerQuality.POOR
    
    # Check 3: Word validity (dictionary check)
    words = tokenize(text)
    valid_ratio = sum(is_valid_word(w) for w in words) / len(words)
    if valid_ratio < 0.7:  # <70% valid words
        return TextLayerQuality.POOR
    
    # Check 4: Spot-check against image OCR
    sample_regions = select_sample_regions(page)
    agreement = compare_text_to_image_ocr(sample_regions)
    if agreement < 0.9:
        return TextLayerQuality.DEGRADED
    
    return TextLayerQuality.GOOD
```

### Hybrid Approach

For many documents, we'll want to:

1. **Use text layer where reliable** (saves compute)
2. **Fall back to image extraction** for problem regions
3. **Always use structure models** to verify/correct

```
PDF Page
    ↓
┌─────────────────────────────────────────┐
│ Text Layer Quality Assessment           │
└─────────────────────────────────────────┘
    ↓                    ↓                    ↓
  GOOD                DEGRADED              POOR/MISSING
    ↓                    ↓                    ↓
Use text layer    Use text layer +      Extract from
directly          image verification    images
    ↓                    ↓                    ↓
└─────────────────────────────────────────────┘
                    ↓
        Structure-Aware Correction
        • Sequence models
        • Vocabulary priors  
        • Semantic classification
                    ↓
            Verified Output
```

---

## Architecture: Extraction + Classification Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ScholarDoc OCR Pipeline                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐                                               │
│  │ PDF Page        │                                               │
│  │ (image + text?) │                                               │
│  └────────┬────────┘                                               │
│           ↓                                                         │
│  ┌─────────────────┐    ┌──────────────────────────────────────┐  │
│  │ Quality         │───▶│ Route: text layer / hybrid / image   │  │
│  │ Assessment      │    └──────────────────────────────────────┘  │
│  └─────────────────┘                   ↓                           │
│                                        ↓                           │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                  Region Detection                            │  │
│  │  • Page number regions (header/footer)                       │  │
│  │  • Body text regions                                         │  │
│  │  • Footnote regions (page bottom, smaller font)              │  │
│  │  • Heading regions (larger font, standalone)                 │  │
│  │  • Marginal regions (annotations, line numbers)              │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              ↓                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │            Per-Region Extraction + Classification            │  │
│  │                                                               │  │
│  │  Region Type    Extraction Strategy    Classification Aid     │  │
│  │  ───────────    ───────────────────    ──────────────────    │  │
│  │  Page Number    Strong sequence prior   Position confirms     │  │
│  │  Footnote       Marker sequence model   Size + position       │  │
│  │  Heading        Chapter/section seq     Font + isolation      │  │
│  │  Body           Vocabulary prior        Default assumption    │  │
│  │  Greek/Latin    Language-specific       Character patterns    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              ↓                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              Document-Level Consistency                       │  │
│  │  • Cross-page sequence validation                            │  │
│  │  • Vocabulary reinforcement (names seen before)              │  │
│  │  • Structure validation (TOC matches headings)               │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              ↓                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                   Structured Output                          │  │
│  │  • Extracted text with confidence                            │  │
│  │  • Semantic labels (heading, footnote, body, etc.)          │  │
│  │  • Sequence membership (page 42, footnote 7, etc.)          │  │
│  │  • Uncertainty flags for human review                        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Sequence Models (Detailed)

### Page Number Model

**Observation:** Page numbers follow predictable sequences, even complex ones.

**Types to handle:**
```
Simple Arabic:     1, 2, 3, 4, ...
Roman lowercase:   i, ii, iii, iv, v, vi, ...
Roman uppercase:   I, II, III, IV, V, VI, ...
Front matter:      i, ii, iii, ... → 1, 2, 3, ...
Scholarly A/B:     A1, A2, ... / B1, B2, ...  (Kant pagination)
Bracketed:         [1], [2], [3], ...
With prefix:       p. 1, p. 2, ... or Page 1, Page 2, ...
Missing pages:     1, 2, 4, 5 (page 3 was blank/removed)
```

**Model:**
```python
class PageNumberSequenceModel:
    """
    Markov model for page number sequences.
    
    State: (number_type, current_value, pattern)
    Transitions: Based on observed sequences in training data
    """
    
    def __init__(self):
        self.transition_probs = {}  # Learned from data
        self.format_patterns = {}   # Detected per-document
        
    def observe(self, page_index: int, extracted_text: str, confidence: float):
        """Record an observation (possibly uncertain)."""
        
    def predict_next(self) -> Distribution[str]:
        """Predict distribution over next page number."""
        
    def correct(self, ocr_output: str, ocr_confidence: float) -> tuple[str, float]:
        """
        Correct OCR output using sequence context.
        Returns (corrected_text, combined_confidence).
        """
        if ocr_confidence > 0.95:
            return ocr_output, ocr_confidence
            
        predicted = self.predict_next()
        
        # If OCR is close to prediction, boost confidence
        if edit_distance(ocr_output, predicted.mode) <= 1:
            return predicted.mode, 0.95
            
        # If OCR is very different, flag for review
        return ocr_output, ocr_confidence * 0.5  # Reduced confidence
```

### Footnote Marker Model

**Observation:** Footnote markers are sequential within their scope.

**Complexity:** Must handle:
- Per-page reset (1, 2, 3 on each page)
- Continuous through chapter (1, 2, ... 47, 48)
- Continuous through book (1, 2, ... 247, 248)
- Symbol sequences (*, †, ‡, §, ||, ¶) - rare in philosophy
- Mixed (numbers in text, symbols in tables)

**Model needs to:**
1. Detect which pattern this document uses
2. Track sequence state
3. Match markers in body to footnote content
4. Handle OCR errors in both locations

### Vocabulary Prior Model

**Observation:** Philosophy texts have recurring specialized vocabulary.

**Approach:**
```python
class DocumentVocabulary:
    """
    Per-document vocabulary built from high-confidence extractions.
    Used as prior for low-confidence regions.
    """
    
    def __init__(self):
        self.word_counts = Counter()
        self.word_contexts = defaultdict(list)  # word -> surrounding contexts
        
    def add_high_confidence(self, text: str, confidence: float):
        """Add text extracted with high confidence."""
        if confidence < 0.9:
            return
        for word in tokenize(text):
            self.word_counts[word] += 1
            
    def suggest_correction(self, uncertain_word: str) -> list[tuple[str, float]]:
        """
        Suggest corrections based on vocabulary.
        Returns list of (word, probability) pairs.
        """
        candidates = []
        for known_word, count in self.word_counts.items():
            distance = edit_distance(uncertain_word, known_word)
            if distance <= 2:  # Allow up to 2 character errors
                # Score based on frequency and edit distance
                score = count / (distance + 1)
                candidates.append((known_word, score))
        
        # Normalize to probabilities
        total = sum(s for _, s in candidates)
        return [(w, s/total) for w, s in candidates]
```

**Domain dictionaries:**
- Philosophy terms: phenomenology, hermeneutics, dialectic, transcendental, ...
- Philosopher names: Heidegger, Husserl, Wittgenstein, Derrida, ...
- Greek terms: λόγος, ἀλήθεια, οὐσία, εἶδος, ...
- German terms: Dasein, Weltanschauung, Zeitgeist, Aufhebung, ...
- Latin terms: a priori, cogito, per se, qua, ...

---

## Semantic Classification

### Region Types

```python
class RegionType(Enum):
    PAGE_NUMBER = "page_number"
    RUNNING_HEADER = "running_header"
    RUNNING_FOOTER = "running_footer"
    CHAPTER_HEADING = "chapter_heading"
    SECTION_HEADING = "section_heading"
    BODY_TEXT = "body_text"
    FOOTNOTE_MARKER = "footnote_marker"
    FOOTNOTE_CONTENT = "footnote_content"
    BLOCK_QUOTE = "block_quote"
    MARGINAL_NOTE = "marginal_note"
    FIGURE_CAPTION = "figure_caption"
    TABLE = "table"
    BIBLIOGRAPHY_ENTRY = "bibliography_entry"
    GREEK_PASSAGE = "greek_passage"
    GERMAN_QUOTE = "german_quote"
    UNKNOWN = "unknown"
```

### Classification Features

| Feature | Helps Classify |
|---------|---------------|
| Y position (top/bottom) | Page numbers, headers, footers, footnotes |
| X position (margin) | Marginal notes, line numbers |
| Font size (relative) | Headings (larger), footnotes (smaller) |
| Font weight | Headings (bold), emphasis |
| Isolation (whitespace) | Headings, block quotes |
| Line length | Headings (short), body (full width) |
| Character set | Greek passages, German quotes |
| Sequence membership | Page numbers, footnotes |
| Content patterns | "Chapter", "§", numbers |

### Classification Model

Could be:
- **Rule-based:** Fast, interpretable, brittle
- **Decision tree:** Interpretable, handles feature combinations
- **CRF:** Good for sequences of regions
- **Neural:** Most flexible, needs training data

**Recommendation:** Start rule-based, evolve to CRF/neural if needed.

---

## Research Questions (Updated)

### Fundamental Questions

1. **How bad is existing OCR on philosophy texts?**
   - Need quantitative survey
   - Sample from Internet Archive, Google Books, JSTOR
   - Measure character/word error rates
   - Categorize error types

2. **How much does structure help?**
   - Baseline: Standard OCR (Tesseract/EasyOCR)
   - +Sequence models: How much improvement?
   - +Vocabulary priors: How much more?
   - +Classification: Does it help extraction?

3. **What's the right detection threshold?**
   - When should we fall back to image extraction?
   - False positive cost (unnecessary compute)
   - False negative cost (bad text output)

### Technical Questions

4. **Base OCR engine?**
   - Need per-character confidence for our approach
   - Tesseract LSTM gives this
   - TrOCR/Donut - can we get confidences?

5. **Training data for sequence models?**
   - Need: OCR output + ground truth
   - Options: Manual annotation, synthetic corruption, parallel texts

6. **Training data for classifier?**
   - Need: Regions labeled by type
   - Could bootstrap from born-digital PDFs with structure

7. **Runtime performance?**
   - Per-page latency budget?
   - Batch vs. streaming?
   - GPU requirements?

---

## Implementation Strategy (Revised)

### Phase 4.0: Research & Evaluation

**Before building anything:**

1. [ ] Survey OCR quality across philosophy PDF sources
2. [ ] Quantify error types and rates
3. [ ] Determine: Is custom OCR worth the investment?
4. [ ] Build evaluation corpus with ground truth

**Deliverable:** Go/no-go decision with data

### Phase 4.1: Text Layer Quality Detection

**Start with detection, not correction:**

1. [ ] Implement quality assessment heuristics
2. [ ] Evaluate on test corpus
3. [ ] Determine thresholds for good/degraded/poor

**Deliverable:** Can reliably identify problem documents

### Phase 4.2: Page Number Sequence Model

**Smallest useful piece:**

1. [ ] Page number region detection
2. [ ] Sequence model implementation
3. [ ] Integration with extraction pipeline
4. [ ] Evaluate improvement

**Deliverable:** Measurable improvement on page numbers

### Phase 4.3: Semantic Classification

**Add structure awareness:**

1. [ ] Region detection (position, font features)
2. [ ] Classification model (start rule-based)
3. [ ] Integration with extraction

**Deliverable:** Regions labeled by type

### Phase 4.4: Full Pipeline

**Put it together:**

1. [ ] Vocabulary prior system
2. [ ] Footnote sequence model
3. [ ] Multi-language handling
4. [ ] Human review interface

**Deliverable:** Complete structure-aware OCR

---

## Success Metrics

| Metric | Baseline | Target |
|--------|----------|--------|
| Character Error Rate (CER) | TBD (measure) | 50% reduction |
| Word Error Rate (WER) | TBD (measure) | 50% reduction |
| Page number accuracy | TBD | >99% |
| Footnote marker accuracy | TBD | >95% |
| Region classification accuracy | N/A | >90% |
| Documents needing human review | TBD | <10% |

---

## Ground Truth Strategy

### The Problem

To evaluate OCR quality and train correction models, we need documents with verified "correct" text. This is harder than it sounds:

1. **Manual transcription is expensive** - A 300-page philosophy book = weeks of work
2. **Existing transcriptions may not match** - Different editions, different pagination
3. **Even "ground truth" has errors** - Typos in transcriptions, OCR errors propagated
4. **Alignment is hard** - Matching scanned page to transcription paragraph-by-paragraph

### Strategy 1: Parallel Text Pairs (Recommended Starting Point)

**Approach:** Find works that exist in both:
- Scanned PDF (with potentially bad OCR)
- Verified digital text (Project Gutenberg, critical editions)

**Sources for parallel texts:**

| Scanned Source | Clean Text Source | Alignment Challenge |
|----------------|-------------------|---------------------|
| Internet Archive | Project Gutenberg | Different editions, pagination |
| Google Books | Standard Ebooks | Formatting differences |
| HathiTrust | WikiSource | Section boundaries |
| Library scans | Publisher e-books | Copyright limitations |

**Workflow:**
```
1. Find work available in both forms
2. Verify same edition/translation
3. Extract text from both sources
4. Align at paragraph or page level
5. Manual verification of alignment
6. Document any discrepancies
```

**Alignment approaches:**
- **Page-level:** Match page images to page numbers in clean text
- **Paragraph-level:** Use sentence similarity to align paragraphs
- **Anchor-based:** Find unique phrases, align around them

**Example candidates (public domain philosophy):**

| Work | Scanned | Clean Text | Notes |
|------|---------|------------|-------|
| Kant, Critique of Pure Reason | archive.org | gutenberg.org | Multiple translations, need same one |
| Plato, Republic (Jowett) | Google Books | gutenberg.org | Common translation |
| Aristotle, Nicomachean Ethics | HathiTrust | Perseus Digital | Greek + English |
| Hume, Enquiry | archive.org | gutenberg.org | Good candidate |
| Mill, On Liberty | Multiple | gutenberg.org | Good candidate |
| Nietzsche, Beyond Good and Evil | archive.org | gutenberg.org | Translation matters |

### Strategy 2: Synthetic Degradation

**Approach:** Start with clean born-digital text, apply realistic degradation to simulate OCR errors.

**Why this helps:**
- Unlimited training data
- Perfect ground truth (we know what we started with)
- Can control difficulty

**Degradation types to simulate:**

```python
class OCRDegradation:
    """Simulate realistic OCR errors."""
    
    def confuse_similar_chars(self, text: str) -> str:
        """Swap visually similar characters."""
        confusions = {
            'l': ['1', 'I', '|'],
            'O': ['0', 'Q'],
            'rn': ['m'],
            'cl': ['d'],
            'vv': ['w'],
            # ... more patterns
        }
        
    def add_noise_chars(self, text: str) -> str:
        """Insert random garbage characters."""
        
    def merge_words(self, text: str) -> str:
        """Remove spaces between words."""
        
    def break_words(self, text: str) -> str:
        """Insert spurious spaces."""
        
    def garble_diacritics(self, text: str) -> str:
        """Mess up accented characters (ä → a, é → e, etc.)."""
        
    def corrupt_greek(self, text: str) -> str:
        """Simulate Greek character recognition failures."""
```

**Realism concern:** Synthetic errors may not match real OCR error patterns. Need to:
1. Study real OCR errors first
2. Build degradation model based on observed patterns
3. Validate synthetic errors look realistic

### Strategy 3: Incremental Manual Verification

**Approach:** Build ground truth incrementally through actual use.

**Workflow:**
```
1. Run OCR on document
2. Flag low-confidence regions
3. Human reviews and corrects flagged regions
4. Corrections become ground truth
5. Model learns from corrections
6. Over time, build up verified corpus
```

**Benefits:**
- Ground truth created as byproduct of real use
- Focuses effort on actual problem areas
- Continuously improves

**Challenges:**
- Need users willing to correct
- Corrections may have errors
- Takes time to accumulate

### Strategy 4: Multi-Transcription Consensus

**Approach:** Have multiple people transcribe the same passage, use agreement as ground truth.

**Workflow:**
```
1. Select passages (stratified sample)
2. 3+ independent transcribers
3. Compute agreement
4. High agreement → ground truth
5. Disagreements → expert review
```

**When to use:**
- Critical test samples
- Ambiguous/difficult passages
- Validating other strategies

**Cost:** Expensive, use sparingly for validation rather than bulk corpus building.

### Strategy 5: Structured Element Verification (Lightweight)

**Approach:** For sequence models (page numbers, footnotes), we don't need full text - just verify the structural elements.

**Page number ground truth:**
```
Document: kant_critique_1781.pdf
Page 0: [no number - title page]
Page 1: [no number - blank]
Page 2: "iii" (Roman, preface)
Page 3: "iv"
...
Page 15: "1" (Arabic, body starts)
Page 16: "2"
...
```

**Footnote ground truth:**
```
Page 42:
  - Marker "1" at position (0.7, 0.3) links to footnote at (0.1, 0.85)
  - Marker "2" at position (0.5, 0.6) links to footnote at (0.1, 0.90)
```

**Benefits:**
- Much faster than full transcription
- Can verify hundreds of pages quickly
- Directly tests what we care about

### Recommended Ground Truth Pipeline

**Phase 1: Bootstrap with Parallel Texts**
```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Select 10 philosophy works available on Gutenberg + Archive  │
│ 2. Download both versions                                       │
│ 3. Align at page/paragraph level (semi-automated)              │
│ 4. Manual spot-check alignment (sample 5%)                      │
│ 5. Document edition/translation details                         │
│                                                                 │
│ Output: 10 documents × ~200 pages = 2000 page pairs            │
└─────────────────────────────────────────────────────────────────┘
```

**Phase 2: Structured Element Annotation**
```
┌─────────────────────────────────────────────────────────────────┐
│ 1. For each document, manually record:                          │
│    - Page number sequence (type, values)                        │
│    - Heading locations and levels                               │
│    - Footnote marker locations                                  │
│    - Footnote content locations                                 │
│ 2. Create structured annotation files                           │
│                                                                 │
│ Output: Structured ground truth for sequence models             │
└─────────────────────────────────────────────────────────────────┘
```

**Phase 3: Synthetic Augmentation**
```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Analyze real OCR errors from Phase 1                         │
│ 2. Build degradation model matching observed patterns           │
│ 3. Generate synthetic training data                             │
│ 4. Validate synthetic data looks realistic                      │
│                                                                 │
│ Output: Large synthetic corpus for model training               │
└─────────────────────────────────────────────────────────────────┘
```

**Phase 4: Continuous Improvement**
```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Deploy with correction interface                             │
│ 2. Collect user corrections                                     │
│ 3. Verify corrections (sample or consensus)                     │
│ 4. Add to ground truth corpus                                   │
│ 5. Retrain models periodically                                  │
│                                                                 │
│ Output: Growing, real-world ground truth                        │
└─────────────────────────────────────────────────────────────────┘
```

### Ground Truth File Format

```yaml
# ground_truth/kant_critique_kemp_smith.yaml
document:
  title: "Critique of Pure Reason"
  author: "Immanuel Kant"
  translator: "Norman Kemp Smith"
  edition: "2nd edition, 1787"
  scan_source: "archive.org/details/xxxxx"
  clean_source: "gutenberg.org/ebooks/xxxxx"
  alignment_method: "page-level"
  verification_status: "spot-checked"
  
page_numbers:
  - page_index: 0
    label: null  # Title page
  - page_index: 1
    label: null  # Blank
  - page_index: 2
    label: "iii"
    label_type: "roman_lower"
  # ... etc
  
structure:
  - type: "heading"
    level: 1
    page_index: 5
    text: "Preface to the First Edition"
    bbox: [0.15, 0.20, 0.85, 0.25]
  # ... etc

footnotes:
  - page_index: 42
    markers:
      - marker: "1"
        marker_bbox: [0.70, 0.30, 0.72, 0.32]
        content_bbox: [0.10, 0.85, 0.90, 0.90]
        content_preview: "This distinction between..."
  # ... etc

text_samples:  # For OCR accuracy measurement
  - page_index: 50
    region_bbox: [0.10, 0.20, 0.90, 0.40]
    ground_truth_text: |
      The transcendental doctrine of judgment (or analytic
      of principles) will therefore contain two chapters...
```

### Quality Assurance for Ground Truth

**How do we know our ground truth is actually correct?**

1. **Source verification**
   - Use authoritative editions (Cambridge, Oxford, etc.)
   - Document provenance
   - Note known errata

2. **Inter-annotator agreement**
   - For manually created elements, have 2+ annotators
   - Measure agreement (Cohen's kappa for categorical, edit distance for text)
   - Resolve disagreements with expert

3. **Automated consistency checks**
   - Page numbers should be sequential
   - Footnote markers should match footnote count
   - Heading hierarchy should be valid

4. **Spot-check sampling**
   - Randomly sample N pages
   - Expert verification
   - Extrapolate error rate

5. **Version control**
   - Track all ground truth changes
   - Document who verified what
   - Enable rollback if errors found

### Open Questions for Ground Truth

1. **How much ground truth do we need?**
   - For baseline measurement: 10-20 documents, stratified sample
   - For training sequence models: Depends on model complexity
   - For statistical significance: Power analysis needed

2. **What's the minimum viable ground truth?**
   - Could start with just page number sequences (easy to verify)
   - Add footnotes and headings later
   - Full text alignment is most expensive

3. **Should ground truth be public?**
   - Open ground truth enables community contribution
   - But may also enable gaming metrics
   - Recommendation: Public after initial publication

4. **How to handle disputed readings?**
   - Philosophy texts have textual variants
   - Critical editions note alternatives
   - Document our choices, don't claim perfection

---

## Open Design Questions

1. **Joint vs. pipeline?**
   - Pipeline: Extract → Classify → Correct (simpler)
   - Joint: Simultaneous extraction + classification (potentially better)

2. **Per-document vs. pre-trained models?**
   - Per-document: Learns this document's patterns
   - Pre-trained: Faster, may miss unusual patterns
   - Hybrid: Pre-trained + per-document fine-tuning

3. **Confidence propagation?**
   - How to combine OCR confidence + sequence model confidence + vocabulary prior?
   - Bayesian combination? Learned weights?

4. **Failure modes?**
   - What happens when sequence model is wrong?
   - How to detect and recover?

---

## References

- Tesseract LSTM: Character-level confidence scores
- Post-OCR correction literature: [TODO: Add specific papers]
- CRF for document layout: [TODO: Add specific papers]
- Philosophy digitization projects: [TODO: Survey existing work]
