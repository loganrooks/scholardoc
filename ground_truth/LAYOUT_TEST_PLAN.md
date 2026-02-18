# Layout Detection Ground Truth Test Plan

## Objective

Create a representative test set for evaluating layout detection (especially footnotes) on scholarly documents. Target: ~50 annotated pages covering key variation dimensions.

## Survey Results (January 2026)

### PDFs by Footnote Density

| Category | PDF | FN/page | Text/page | Notes |
|----------|-----|---------|-----------|-------|
| **High** | Heidegger_BeingAndTime | 2.3 | 10.3 | Translator notes, margin refs |
| **High** | Derrida_MarginsOfPhilosophy | 2.2 | 8.8 | Dense philosophical footnotes |
| **High** | Heidegger_DiscourseOnThinking | 2.2 | 33.0 | Complex layout, scanned |
| **High** | Kant_CritiqueOfJudgement | 2.0 | 7.7 | 18th century style |
| **Medium** | Heidegger_Pathmarks | 1.6 | 10.3 | Mixed essay collection |
| **Medium** | Dissemination | 1.5 | 15.9 | High text density |
| **Medium** | TheTruthInPainting | 1.4 | 8.1 | Art theory |
| **Sparse** | TheBeastAndSovereign | 0.6 | 6.5 | Lecture series |
| **Sparse** | Monolingualism | 0.6 | 6.9 | Short philosophical text |
| **Control** | WritingAndDifference | 0.0 | 2.8 | Uses endnotes |
| **Control** | Lenin_StateAndRevolution | 0.0 | 11.8 | Political text, endnotes |
| **Control** | ComayRebecca | 0.0 | 7.0 | Academic monograph |

## Test Categories

### Category 1: Footnote Density (20 pages)
- **1A: Dense (>3 FN/page)** - 6 pages
  - Source: Heidegger_BeingAndTime, Derrida_Margins
- **1B: Moderate (1-3 FN/page)** - 6 pages
  - Source: Kant_Critique, Pathmarks
- **1C: Sparse (<1 FN/page)** - 4 pages
  - Source: TheBeastAndSovereign, Monolingualism
- **1D: None (control)** - 4 pages
  - Source: Lenin, ComayRebecca

### Category 2: Layout Complexity (10 pages)
- **2A: Clean single-column** - 4 pages
- **2B: With figures/images** - 3 pages
  - Source: TheTruthInPainting (art book)
- **2C: Complex multi-element** - 3 pages
  - Source: Heidegger_DiscourseOnThinking (33 text blocks/page)

### Category 3: Special Content (10 pages)
- **3A: Greek/foreign text in footnotes** - 4 pages
  - Source: Derrida_Margins (French philosophy, Greek quotes)
- **3B: Long block quotes** - 3 pages
- **3C: Continuation footnotes** - 3 pages

### Category 4: Edge Cases (10 pages)
- **4A: Very long footnotes (>10 lines)** - 3 pages
- **4B: Page footer vs footnote distinction** - 3 pages
- **4C: Multiple footnote levels** - 2 pages
- **4D: Footnotes near page bottom margin** - 2 pages

## Gaps Identified

### Missing Document Types
1. **Scientific papers** - Two-column layout, numbered references
   - Source: arXiv, JSTOR open access
2. **Classics with critical apparatus** - Plato/Aristotle editions
   - Source: Perseus Digital Library, Loeb Classical
3. **Legal documents** - Extensive footnotes, citations
4. **Math-heavy documents** - Equations in footnotes
5. **Non-Western philosophy** - Different citation conventions

### Missing Quality Variations
1. **Poor scan quality** - Degraded images, skewed text
2. **Mixed quality** - Born-digital + scanned pages
3. **Historical documents** - Pre-20th century typesetting

## Ground Truth Schema

```yaml
# ground_truth/annotations/page_001.yaml
page_id: "derrida_margins_p120"
source:
  pdf: "Derrida_MarginsOfPhilosophy.pdf"
  page: 120

categories:
  - dense_footnotes
  - greek_text
  - single_column

expected_regions:
  - type: Footnote
    count: 3
    bboxes:  # Optional detailed boxes
      - [x1, y1, x2, y2]
  - type: Text
    count: 4
  - type: Page-header
    count: 1

notes: "Contains Greek quote in footnote 2"
difficulty: medium  # easy/medium/hard
```

## Evaluation Metrics

1. **Detection Rate** (Recall)
   - % of actual footnotes detected
   - Target: >90%

2. **Precision**
   - % of detections that are correct
   - Target: >85%

3. **Boundary Accuracy** (IoU)
   - Intersection over Union of detected vs actual boxes
   - Target: >0.7

4. **Confidence Calibration**
   - Correlation between confidence scores and accuracy
   - High-confidence detections should be more accurate

## Next Steps

1. [ ] Sample specific pages from each category
2. [ ] Create annotation files for ~50 pages
3. [ ] Run Docling baseline on full test set
4. [ ] Calculate baseline metrics
5. [ ] Identify systematic failure modes
6. [ ] Source additional PDFs for gaps

## Version History

- 2026-01-07: Initial plan based on PDF survey
