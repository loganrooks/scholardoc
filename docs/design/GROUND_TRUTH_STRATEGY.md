# Ground Truth Strategy: Unified Evaluation Corpus

> **Status:** Design  
> **Scope:** All phases of ScholarDoc, not just OCR  
> **Last Updated:** December 2025

---

## Overview

We need ground truth for evaluating and improving **every component** of ScholarDoc:

| Phase | Component | Ground Truth Needed |
|-------|-----------|---------------------|
| 1 | Text extraction | Accurate text for each page |
| 1 | Page number detection | Where are page numbers? What format? What value? |
| 1 | Heading detection | Which text is a heading? What level? |
| 1 | Document structure | Chapter/section hierarchy |
| 2 | Footnote detection | Marker locations, content locations, linkage |
| 2 | Endnote detection | Same as footnotes, document-level scope |
| 2 | Table detection | Boundaries, cell structure |
| 2 | Bibliography detection | Entry boundaries, parsed fields |
| 4 | OCR accuracy | Character/word level correctness |
| 4 | Semantic classification | Region types (heading, body, footnote, etc.) |

**Key insight:** A single well-annotated corpus can serve all these needs.

---

## Unified Annotation Schema

### Document-Level Metadata

```yaml
document:
  # Identity
  id: "kant_cpr_kemp_smith_1929"
  title: "Critique of Pure Reason"
  author: "Immanuel Kant"
  translator: "Norman Kemp Smith"
  edition: "2nd edition, 1929 translation"
  language: "en"
  
  # Sources
  scan_source: 
    url: "https://archive.org/details/xxxxx"
    quality: "good"  # good, degraded, poor
  clean_text_source:
    url: "https://gutenberg.org/ebooks/xxxxx"
    alignment_verified: true
    
  # Document characteristics
  page_count: 450
  has_front_matter: true
  has_index: true
  footnote_style: "per_page"  # per_page, continuous, endnotes
  page_number_style: "mixed"  # arabic, roman, mixed
  
  # Annotation status
  annotation_status:
    page_numbers: "complete"
    headings: "complete"
    footnotes: "partial"
    text_samples: "sparse"
    
  # Verification
  annotated_by: ["claude-assisted", "human-verified"]
  verification_date: "2025-01-15"
  verification_notes: "Spot-checked 10% of pages"
```

### Page-Level Annotations

```yaml
pages:
  - index: 0
    # Page number annotation
    page_number:
      value: null  # Title page, no number
      format: "none"
      position: null
      
    # Region annotations (normalized coordinates 0-1)
    regions:
      - type: "title"
        bbox: [0.15, 0.30, 0.85, 0.45]
        text: "CRITIQUE OF PURE REASON"
        confidence: 1.0
        
      - type: "author"
        bbox: [0.20, 0.50, 0.80, 0.55]
        text: "IMMANUEL KANT"
        confidence: 1.0
        
  - index: 5
    page_number:
      value: "iii"
      format: "roman_lower"
      position: "footer_center"
      bbox: [0.45, 0.95, 0.55, 0.98]
      
    regions:
      - type: "heading"
        level: 1
        bbox: [0.15, 0.12, 0.85, 0.18]
        text: "PREFACE TO THE FIRST EDITION"
        confidence: 1.0
        
      - type: "body"
        bbox: [0.15, 0.22, 0.85, 0.90]
        text_sample: "Human reason has this peculiar fate..."
        
  - index: 42
    page_number:
      value: "24"
      format: "arabic"
      position: "header_outer"
      bbox: [0.90, 0.03, 0.95, 0.05]
      
    regions:
      - type: "running_header"
        bbox: [0.15, 0.03, 0.60, 0.05]
        text: "TRANSCENDENTAL DOCTRINE OF ELEMENTS"
        
      - type: "heading"
        level: 2
        bbox: [0.15, 0.10, 0.85, 0.14]
        text: "Section II: The A Priori Grounds"
        
      - type: "body"
        bbox: [0.15, 0.18, 0.85, 0.75]
        
      - type: "footnote_marker"
        marker: "1"
        bbox: [0.72, 0.45, 0.74, 0.47]
        links_to: "footnote_content_0"
        
      - type: "footnote_content"
        id: "footnote_content_0"
        bbox: [0.15, 0.80, 0.85, 0.92]
        marker: "1"
        text: "This distinction was first drawn by..."
```

### Structure Annotations (Document-Level)

```yaml
structure:
  # Table of contents reconstruction
  toc:
    - title: "Preface to the First Edition"
      level: 1
      page_index: 5
      page_label: "iii"
      
    - title: "Preface to the Second Edition"
      level: 1
      page_index: 12
      page_label: "x"
      
    - title: "Introduction"
      level: 1
      page_index: 25
      page_label: "1"
      children:
        - title: "I. The Distinction between Pure and Empirical Knowledge"
          level: 2
          page_index: 25
          
  # Page number sequence (for sequence model training)
  page_sequence:
    - indices: [0, 1, 2, 3, 4]
      format: "none"
      note: "Title pages, no numbers"
      
    - indices: [5, 6, 7, 8, 9, 10, 11]
      format: "roman_lower"
      values: ["iii", "iv", "v", "vi", "vii", "viii", "ix"]
      
    - indices: [25, 26, 27]
      format: "arabic"
      values: ["1", "2", "3"]
      note: "Body begins"
      
  # Footnote sequence (for sequence model training)
  footnote_sequences:
    - scope: "per_page"
      pages:
        - page_index: 42
          markers: ["1", "2"]
        - page_index: 43
          markers: ["1", "2", "3"]  # Resets each page
```

### Text Sample Annotations (For OCR Accuracy)

```yaml
text_samples:
  # Sparse sampling for OCR accuracy measurement
  - page_index: 50
    region_bbox: [0.15, 0.20, 0.85, 0.40]
    ground_truth: |
      The transcendental doctrine of judgment will
      therefore contain two chapters. The first will
      treat of the sensuous condition under which alone
      concepts of understanding can be employed.
    ocr_extracted: |
      The transccndental doctrine of judgment will
      thcrefore contain two chapters. The first will
      treat of the sensuous condition undcr which alone
      concepts of understanding can be cmployed.
    notes: "Common e→c errors"
    
  # Greek passage sample
  - page_index: 120
    region_bbox: [0.20, 0.50, 0.80, 0.55]
    ground_truth: "τὸ τί ἦν εἶναι"
    language: "greek"
    notes: "Aristotelian technical term"
```

---

## Hybrid Claude + Human Annotation Workflow

### The Approach

Instead of either:
- Pure manual annotation (slow, expensive)
- Pure automated annotation (unreliable)

We use **Claude-assisted annotation with human verification**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                 CLAUDE + HUMAN ANNOTATION PIPELINE                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐                                                  │
│  │ PDF Document │                                                  │
│  └──────┬───────┘                                                  │
│         ↓                                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ PHASE 1: Claude Proposes Annotations                          │ │
│  │                                                                │ │
│  │  Claude analyzes each page and proposes:                      │ │
│  │  • Page number location and value                             │ │
│  │  • Heading regions and levels                                 │ │
│  │  • Footnote markers and content regions                       │ │
│  │  • Body text vs. other region types                           │ │
│  │  • Confidence scores for each annotation                      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│         ↓                                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ PHASE 2: Human Reviews High-Uncertainty Items                 │ │
│  │                                                                │ │
│  │  Human reviews:                                               │ │
│  │  • Items with confidence < 0.8                                │ │
│  │  • First few pages (establish patterns)                       │ │
│  │  • Random sample (quality check)                              │ │
│  │  • Complex pages (multi-column, heavy footnotes)              │ │
│  │                                                                │ │
│  │  Human actions:                                               │ │
│  │  • Confirm ✓                                                  │ │
│  │  • Correct (with explanation)                                 │ │
│  │  • Flag for expert review                                     │ │
│  └──────────────────────────────────────────────────────────────┘ │
│         ↓                                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ PHASE 3: Claude Learns from Corrections                       │ │
│  │                                                                │ │
│  │  • Corrections update Claude's understanding                  │ │
│  │  • Re-annotate similar items with new knowledge              │ │
│  │  • Reduce uncertainty on subsequent documents                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
│         ↓                                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ PHASE 4: Final Human Verification                             │ │
│  │                                                                │ │
│  │  • Spot-check random 5-10% of annotations                    │ │
│  │  • Verify sequence consistency (page numbers, footnotes)      │ │
│  │  • Sign off on document as "verified"                        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│         ↓                                                          │
│  ┌──────────────┐                                                  │
│  │ Ground Truth │                                                  │
│  │    Corpus    │                                                  │
│  └──────────────┘                                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Benefits of This Approach

| Aspect | Pure Manual | Pure Automated | Claude + Human |
|--------|-------------|----------------|----------------|
| Speed | Very slow | Fast | Fast (with review) |
| Accuracy | High | Variable | High |
| Consistency | Variable | Consistent | Consistent |
| Catches edge cases | Yes | No | Yes |
| Scalable | No | Yes | Yes |
| Cost | High | Low | Medium |

### Implementation: Claude Annotation Agent

```markdown
<!-- .claude/agents/ground-truth-annotator.md -->
---
name: ground-truth-annotator
description: Annotate PDF documents for ground truth corpus
tools: Read, Bash(python *), Edit(ground_truth/**)
model: sonnet
---

You are annotating scholarly PDFs to build a ground truth corpus for ScholarDoc.

## Your Task

For each page of the PDF, identify and annotate:

1. **Page Numbers**
   - Location (header/footer, left/center/right)
   - Value (the actual number/numeral)
   - Format (arabic, roman_lower, roman_upper, none)

2. **Regions** (with bounding boxes)
   - Headings (with level 1-4)
   - Body text
   - Footnote markers
   - Footnote content
   - Running headers/footers
   - Block quotes
   - Tables
   - Images/figures

3. **Confidence**
   - For each annotation, provide confidence 0.0-1.0
   - Flag anything below 0.7 for human review

## Process

1. First, examine pages 1-5 to understand document conventions
2. Note the patterns (page number style, heading conventions)
3. Apply patterns consistently through document
4. Flag departures from patterns for review

## Output Format

Output annotations in YAML format matching the schema in 
docs/design/GROUND_TRUTH_STRATEGY.md

## When Uncertain

- If confidence < 0.7, add `needs_review: true`
- Add a `notes` field explaining uncertainty
- Never guess - it's better to flag for review
```

### Implementation: Human Review Interface

```python
# spikes/07_annotation_review.py (concept)

class AnnotationReviewer:
    """Interactive tool for reviewing Claude's annotations."""
    
    def review_document(self, pdf_path: str, annotations_path: str):
        """Review and correct annotations."""
        
        annotations = load_annotations(annotations_path)
        pdf = fitz.open(pdf_path)
        
        # Items needing review
        review_queue = [
            ann for ann in annotations 
            if ann.get('needs_review') or ann.get('confidence', 1) < 0.8
        ]
        
        # Also sample random items for quality check
        random_sample = random.sample(
            [a for a in annotations if a not in review_queue],
            k=min(20, len(annotations) // 10)
        )
        
        for item in review_queue + random_sample:
            # Display page with annotation highlighted
            self.show_page_with_annotation(pdf, item)
            
            # Get human decision
            decision = self.prompt_decision(item)
            # Options: confirm, correct, flag_expert, skip
            
            if decision == 'correct':
                correction = self.get_correction(item)
                self.record_correction(item, correction)
                
        self.save_reviewed_annotations(annotations_path)
```

---

## What Ground Truth Enables

### For Each Phase

**Phase 0 (Exploration):**
- Baseline measurements on real documents
- Validate spike findings against known-correct data

**Phase 1 (MVP):**
- Evaluate heading detection accuracy
- Evaluate page number detection accuracy
- Measure text extraction quality
- Regression testing

**Phase 2 (Enhanced):**
- Train footnote detection models
- Evaluate footnote-marker linking accuracy
- Table detection benchmarks

**Phase 4 (OCR):**
- Measure OCR accuracy (CER, WER)
- Train sequence models (page numbers, footnotes)
- Train region classifiers
- Evaluate structure-aware corrections

### Cross-Phase Validation

The same annotated document serves multiple purposes:

```
Document: kant_critique_annotated.yaml
    │
    ├── Page number annotations
    │     ├── Phase 1: Evaluate page detection
    │     └── Phase 4: Train sequence model
    │
    ├── Heading annotations
    │     ├── Phase 1: Evaluate heading detection
    │     └── Phase 4: Train region classifier
    │
    ├── Footnote annotations
    │     ├── Phase 2: Evaluate footnote detection
    │     └── Phase 4: Train marker sequence model
    │
    └── Text samples
          ├── Phase 1: Evaluate extraction quality
          └── Phase 4: Measure OCR accuracy
```

---

## Corpus Building Plan

### Target Corpus Size

| Document Type | Count | Pages | Purpose |
|---------------|-------|-------|---------|
| Philosophy monographs | 10 | ~3000 | Primary test set |
| Philosophy articles | 10 | ~200 | Short-form testing |
| Multi-column academic | 5 | ~500 | Layout challenges |
| Poor OCR quality | 5 | ~1000 | OCR testing |
| Non-English | 5 | ~500 | Language handling |
| **Total** | **35** | **~5200** | |

### Phased Corpus Building

**Week 1-2: Foundation (5 documents)**
- Select 5 diverse philosophy PDFs with Gutenberg parallels
- Full Claude annotation pass
- Full human review
- Establish annotation conventions
- Create training materials for future annotation

**Week 3-4: Expansion (15 documents)**
- Apply learned conventions
- Claude annotation with targeted human review
- Less review per document (patterns established)

**Week 5-6: Completion (15 documents)**
- Include edge cases (poor OCR, non-English, complex layouts)
- Minimal human review (spot-check only)
- Quality verification

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Inter-annotator agreement | >95% | Claude vs Human on same pages |
| Sequence consistency | 100% | Automated check |
| Coverage | >90% pages | % pages with region annotations |
| Verification rate | >10% | % pages human-verified |

---

## Integration with ScholarDoc Development

### TDD with Ground Truth

```python
# tests/integration/test_against_ground_truth.py

def test_heading_detection_against_corpus():
    """Test heading detection against annotated corpus."""
    
    for doc_path in GROUND_TRUTH_CORPUS:
        annotations = load_annotations(doc_path)
        pdf_path = annotations['document']['scan_source']['local_path']
        
        # Run our detection
        detected = scholardoc.detect_headings(pdf_path)
        
        # Compare to ground truth
        ground_truth = [
            r for p in annotations['pages'] 
            for r in p['regions'] 
            if r['type'] == 'heading'
        ]
        
        precision, recall, f1 = evaluate_detection(detected, ground_truth)
        
        assert f1 > 0.80, f"F1 score {f1} below threshold for {doc_path}"
```

### Continuous Improvement Loop

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│    Ground Truth ──→ Train/Tune ──→ Evaluate ──→ Improve       │
│         ↑              │              │            │           │
│         │              ↓              ↓            │           │
│         └──── New Annotations ←── Find Errors ←───┘           │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Open Questions

1. **How much annotation per document?**
   - Full (every page): Most accurate, most expensive
   - Sampled (every 5th page): Faster, statistically valid
   - Targeted (complex pages only): Focused on hard cases

2. **Who does human review?**
   - Domain expert (philosophy scholar): Best quality, expensive
   - Trained annotator: Good quality, available
   - Crowdsourced: Scalable, needs consensus mechanism

3. **How to handle disagreements?**
   - Claude-human disagreement: Human wins, analyze why
   - Human-human disagreement: Expert tiebreaker or consensus

4. **Version control for annotations?**
   - Git for annotation files
   - Track who annotated what when
   - Enable rollback for errors

5. **Privacy/copyright?**
   - Use public domain texts where possible
   - For copyrighted: annotations only, not full text
   - Document permissions

---

## Next Steps

1. [ ] Implement annotation schema as Pydantic models
2. [ ] Create Claude annotation agent prompt
3. [ ] Build human review interface (CLI first, GUI later)
4. [ ] Select initial 5 documents for foundation corpus
5. [ ] Pilot annotation workflow on 1 document
6. [ ] Measure time and refine process
7. [ ] Scale to full corpus
