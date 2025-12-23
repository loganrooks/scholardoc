# ADR-002: OCR Correction Pipeline Architecture

**Status:** VALIDATED - Based on spike testing
**Date:** December 2025
**Validation:** `spikes/29_ocr_pipeline_design.py`, `spikes/30_validation_framework.py`

---

## Context

ScholarDoc processes scanned scholarly documents that contain embedded OCR text of varying quality. We need a strategy for detecting and correcting OCR errors while:

- Minimizing false negatives (missed errors corrupt the output)
- Accepting some false positives (extra re-OCR wastes compute but doesn't corrupt)
- Keeping processing time reasonable for large corpora
- Handling multilingual philosophical texts (German, French, Latin, Greek terms)

**Validation data:** 130 error pairs from multiple philosophical texts, 77 correct words for false positive testing.

---

## Options Considered

### Option 1: Auto-Correct with Spellcheck

**Description:** Use spellchecker suggestions to automatically replace misspelled words.

**Pros:**
- Simple implementation
- Fast processing
- No neural models needed

**Cons:**
- High risk of wrong corrections
- Can't handle context-dependent errors
- May "correct" valid foreign terms
- No way to know if correction is right

**Verdict:** Rejected - Too risky for scholarly text

### Option 2: Neural Re-OCR Everything

**Description:** Run neural OCR (TrOCR, Tesseract) on all pages.

**Pros:**
- Consistent quality
- No detection logic needed
- Catches all errors

**Cons:**
- Very slow (seconds per page)
- Expensive compute resources
- Often worse than existing OCR (spike finding!)
- Overkill for clean pages

**Verdict:** Rejected - Testing showed existing OCR often embeds better than TrOCR

### Option 3: Spellcheck as Selector + Selective Re-OCR (Chosen)

**Description:** Use spellcheck to FLAG suspicious words, then run neural re-OCR only on flagged lines.

**Pros:**
- 99.2% detection rate (validated)
- Fast for clean pages (skip re-OCR)
- Neural re-OCR only where needed
- Acceptable false positive rate (23.4%)

**Cons:**
- More complex pipeline
- False positives waste some compute
- Requires line-level cropping

**Verdict:** Selected - Best balance of accuracy and efficiency

---

## Decision

### Core Architecture

```
┌─────────────────────────────────────────────────┐
│ STAGE 1: Line-Break Rejoining                   │
│   - Position-based detection (PyMuPDF)          │
│   - Block-filtered to avoid margins             │
│   - Removes hyphenation artifacts               │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│ STAGE 2: OCR Error Detection (Spellcheck)       │
│   - Adaptive dictionary (base + learned)        │
│   - Morphological validation                    │
│   - Flags words, does NOT auto-correct          │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│ STAGE 3: Selective Re-OCR (Line-Level)          │
│   - Crop LINE from page image (not word)        │
│   - Run TrOCR/Tesseract on crop                 │
│   - Replace only flagged words                  │
└─────────────────────────────────────────────────┘
```

### Key Decisions

#### 1. Spellcheck = Selector, Not Corrector

**Decision:** Spellcheck flags suspicious words but never auto-corrects.

**Rationale:**
- Auto-correction has high error rate for scholarly text
- "tbese" → "these" is obvious, but "Dasein" → "Design" would be wrong
- Better to flag and verify than to silently corrupt

#### 2. Line-Level Re-OCR (Not Word-Level)

**Decision:** When re-OCR is needed, crop the entire line, not just the word.

**Rationale:**
- Neural OCR needs visual context for accurate recognition
- Word-level crops lose critical information (spacing, neighboring characters)
- Line-level provides sufficient context while staying efficient
- Validated in spike testing

#### 3. Adaptive Dictionary with Safeguards

**Decision:** Learn new words during processing, but with strict safeguards.

**Rationale:**
- Philosophy texts have specialized vocabulary not in dictionaries
- Can't blindly add words (might learn OCR errors)
- Safeguards: frequency thresholds, morphological validation, confidence scoring

**Safeguards:**
- Minimum 2 occurrences before learning
- Morphological validation (check base forms exist)
- Pattern validation (has vowels, reasonable length)
- Confidence threshold (0.7+)

#### 4. No Auto-Fix for Umlauts

**Decision:** Flag `ü→ii` patterns for re-OCR instead of auto-replacing.

**Rationale:**
- Pattern `ii→ü` would break words like "skiing"
- Context needed to know if replacement is correct
- Re-OCR can see the actual character

#### 5. Block-Based Line-Break Detection

**Decision:** Only consider line breaks within the same PDF block.

**Rationale:**
- Cross-block matches catch margin content (page numbers, headers)
- PyMuPDF block numbers distinguish text regions
- Validated fix for false positives like `meta-` + `a x` (page marker)

---

## Consequences

### Positive
- 99.2% detection rate on validation set
- Fast processing for clean pages
- Neural re-OCR only where needed (~20-30% of words)
- Graceful handling of multilingual text

### Negative
- 23.4% false positive rate (German terms flagged)
- More complex than simple approaches
- Requires PyMuPDF position data for line-break detection

### Mitigations
- Scholarly vocabulary filter can reduce false positives
- Pipeline stages are independent and can be optimized separately
- Fall back to full page if line cropping fails

---

## Validation Results

**Test set:** 130 OCR error pairs, 77 correct words

| Metric | Result | Target |
|--------|--------|--------|
| Detection rate | 99.2% | >99% ✅ |
| False positive rate | 23.4% | <30% ✅ |
| False negatives | 1 ('es' fragment) | 0 ⚠️ |

**Note:** False positives are mostly German philosophical terms (Dasein, Augenblick, etc.) - expected and acceptable since they'll be verified by re-OCR.

---

## Implementation

See `spikes/29_ocr_pipeline_design.py` for:
- `AdaptiveDictionary` class with morphological validation
- `LineBreakRejoiner` class with block filtering
- `OCRErrorDetector` class with hybrid detection

See `spikes/30_validation_framework.py` for:
- `ValidationSet` class for ground truth management
- `PipelineMetrics` class for evaluation

---

## References

- Spike 28: OCR cleaner evaluation
- Spike 29: OCR pipeline design
- Spike 30: Validation framework
- Ground truth: `ground_truth/validation_set.json`
