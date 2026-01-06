# ADR-004: OCR Source Tracking and Engine Validation

## Status

Accepted

## Context

ScholarDoc processes PDFs with embedded OCR text layers. These text layers are produced by various OCR engines, and the quality/error patterns can vary significantly by engine. Understanding the OCR source helps with:

1. **Traceability**: Knowing what produced the text layer
2. **Analysis**: Comparing error patterns across OCR engines
3. **Debugging**: Identifying engine-specific issues
4. **Validation**: Ensuring our error detection works across different OCR sources

### Current Validation Set Coverage

Analysis of our sample PDFs (December 2025):

| Document | OCR Engine | Version | Date |
|----------|-----------|---------|------|
| Lenin_StateAndRevolution | Adobe Paper Capture | Acrobat Pro DC 15 | 2020 |
| Kant_CritiqueOfJudgement | Adobe Paper Capture | Acrobat 9.0 | 2010 |
| Derrida_TheTruthInPainting | Adobe Paper Capture + ClearScan | Acrobat 9.0 | 2009 |
| Heidegger_Pathmarks | Adobe Paper Capture | Acrobat Pro 24 | 2023 |
| Heidegger_BeingAndTime | Unknown | (empty metadata) | 2023 |

**Findings:**
- All identified sources use **Adobe Acrobat Paper Capture** (single vendor)
- Version span: Acrobat 9.0 (2009) to Acrobat Pro 24 (2023) - 14 years of versions
- No samples from: Tesseract, ABBYY FineReader, Google Vision, AWS Textract, docTR

### Why Single-Vendor Coverage May Be Acceptable

Our OCR error detection is **engine-agnostic** by design:

1. **Dictionary-based validation**: Checks against English dictionary + scholarly vocabulary
2. **Pattern-based detection**: Identifies impossible letter combinations (triple letters, no vowels)
3. **Morphological analysis**: Validates word stems and affixes

These techniques detect universal OCR problems (character substitution, ligature errors) that occur across all OCR engines, not Adobe-specific patterns.

## Decision

### 1. Track OCR Source in QualityInfo

Add `OCRSourceInfo` to capture:
- Engine name (normalized: `adobe_paper_capture`, `tesseract`, `abbyy_finereader`, etc.)
- Engine version
- Raw producer/creator strings
- Detection confidence

```python
@dataclass
class OCRSourceInfo:
    engine: str = "unknown"
    engine_version: str = ""
    producer: str = ""
    creator: str = ""
    creation_date: str = ""
    confidence: float = 0.0
```

### 2. Extract from PDF Metadata

Parse `producer` and `creator` fields to identify known OCR engines:
- Adobe: `"Paper Capture"` in producer
- ABBYY: `"ABBYY"` in producer/creator
- Tesseract: `"Tesseract"` in producer/creator

### 3. Future Multi-Engine Validation (Not Blocking)

Create samples processed by different OCR engines when available, but don't block Phase 1 completion on this. The current Adobe-only validation is acceptable because:

- 14-year version span provides temporal diversity
- Error detection is algorithm-based, not pattern-matched to specific engines
- False positive rate (20.8%) and detection rate (96.9%) are acceptable across versions

## Consequences

### Positive
- Full traceability of OCR sources in processed documents
- Foundation for future multi-engine analysis
- Processing logs show OCR engine when detected
- Can correlate error patterns with OCR sources

### Negative
- Some PDFs have empty metadata (undetectable source)
- Detection heuristics may need updates for new OCR engines

### Future Work

When multi-engine samples become available:

1. **Create test samples**: Process same source image with Tesseract, docTR, ABBYY
2. **Compare error patterns**: Document engine-specific error tendencies
3. **Validate detection rates**: Ensure ≥95% detection across all engines
4. **Update heuristics**: Add detection patterns for new engines

## References

- PDF Metadata fields: `producer`, `creator` contain OCR engine info
- Adobe Paper Capture: Adobe's built-in OCR technology in Acrobat
- Validation set: `ground_truth/validation_set.json` (130 error pairs, 77 correct words)
