# Ground Truth System: Diagnostic Analysis & Redesign Plan

**Created**: 2026-01-08
**Status**: Planning (requires approval before implementation)

## Executive Summary

The ground truth system was implemented prematurely without properly thinking through:
1. What workflows need evaluation
2. What ground truth each workflow requires
3. How to annotate each element type effectively
4. How ground truth maps to ScholarDocument representation

This document diagnoses the failures and proposes a redesign.

---

## Part 1: Diagnosis - What Went Wrong

### Failure 1: Schema-First Without Use-Case Analysis

**What happened**: Created a comprehensive YAML schema (v1.1.0) that looks complete but doesn't map to actual extraction evaluation needs.

**Evidence**:
- Schema has `regions` with flat bboxes, but no hierarchical containment
- `footnotes` have `marker` and `content` but no clear relationship to ScholarDocument's `FootnoteRef` and `Note`
- `sous_rature` is defined but there's no way to annotate it in the UI
- No clear mapping between ground truth elements and ScholarDocument fields

**Root cause**: Started with "what could ground truth contain?" instead of "what do we need to evaluate?"

### Failure 2: UI Design Without Workflow Analysis

**What happened**: Built a Streamlit UI that shows PDF + YAML editor, but:
- YAML editing is not how humans annotate documents
- No visual tools for drawing bboxes
- No text selection for spans (citations, sous-rature)
- No side-by-side comparison of PDF vs extracted text
- Navigation bugs (state not syncing)

**Evidence from testing**:
- Prev/Next buttons don't update with dropdown selection
- "Select" button does nothing visible
- Sample bboxes are arbitrary garbage
- No way to verify what was actually extracted

**Root cause**: Jumped to implementation without defining annotation workflows for each element type.

### Failure 3: Missing Link to ScholarDocument

**What happened**: Ground truth schema was designed in isolation, not as "expected output" for ScholarDocument extraction.

**Evidence**:
- ScholarDocument has `FootnoteRef` (marker position) and `Note` (content) as separate structures
- Ground truth has combined `footnotes` with nested `marker` and `content`
- No clear test: "given this ground truth, what should ScholarDocument contain?"

**Root cause**: Didn't start from ScholarDocument and work backward to "what annotation captures correct output?"

### Failure 4: Evaluation Library Without Clear Inputs

**What happened**: Built normalize.py, matching.py, metrics.py before having real ground truth to evaluate.

**Evidence**:
- `scholar_doc_to_elements()` exists but doesn't map to actual ScholarDocument fields properly
- `load_ground_truth_elements()` flattens the hierarchical schema losing information
- No integration test that runs end-to-end: PDF → extract → compare → report

**Root cause**: Built evaluation machinery without sample data to validate against.

---

## Part 2: What Should Ground Truth Enable?

### Core Question

Ground truth must answer: **"For this PDF, what should ScholarDocument contain?"**

This means ground truth is NOT:
- A general document annotation format
- A layout analysis dataset
- A "capture everything" system

Ground truth IS:
- Expected outputs for ScholarDocument extraction
- Test data for specific extraction workflows
- Validation targets with clear pass/fail criteria

### Extraction Workflows to Evaluate

| Workflow | What We Extract | ScholarDocument Fields | Ground Truth Needs |
|----------|-----------------|------------------------|-------------------|
| **Text Extraction** | Clean body text | `text`, `page_spans` | Correct text per page, without artifacts |
| **Structure** | Sections/chapters | `sections`, `section_spans` | Section titles, start/end positions, hierarchy |
| **Footnotes** | Markers + content | `footnote_refs`, `notes` | Marker positions, note content, marker-note links |
| **Citations** | In-text refs | `citation_refs` | Citation text, position, parsed fields |
| **Page Numbers** | Display pagination | `page_spans[].label` | Displayed page number per PDF page |
| **Bibliography** | Reference list | `bib_entries` | Parsed bibliography entries |
| **Sous Rature** | Under-erasure text | (not in ScholarDocument) | Text span with strikethrough |

### What's Missing From Current ScholarDocument?

Looking at `models.py`, ScholarDocument has:
- ✅ `text: str` - continuous text
- ✅ `page_spans: list[PageSpan]` - page boundaries with labels
- ✅ `sections: list[SectionSpan]` - section boundaries
- ✅ `paragraphs: list[ParagraphSpan]` - paragraph boundaries
- ✅ `footnote_refs: list[FootnoteRef]` - marker positions
- ✅ `endnote_refs: list[EndnoteRef]` - endnote markers
- ✅ `citation_refs: list[CitationRef]` - citation positions
- ✅ `notes: list[Note]` - footnote/endnote content
- ❌ No `sous_rature` - need to add if we want to extract it
- ❌ No `marginal_refs` - Stephanus/Bekker refs not modeled

**Decision needed**: Do we add sous_rature and marginal_refs to ScholarDocument, or defer?

---

## Part 3: Redesigned Ground Truth Schema

### Principle: Mirror ScholarDocument Structure

Ground truth should be structured as "expected ScholarDocument output" with:
1. Expected text (or text hash for long documents)
2. Expected spans and their positions
3. Expected annotations

### Proposed Schema v2.0

```yaml
schema_version: "2.0.0"

# Source identification (unchanged)
source:
  pdf: "Being_and_Time.pdf"
  page_range: [150, 160]  # PDF pages annotated
  title: "Being and Time"
  author: "Martin Heidegger"

# What we're evaluating
evaluation_scope:
  text_extraction: verified      # pending | annotated | verified
  page_boundaries: verified
  section_structure: annotated
  footnotes: verified
  citations: pending
  bibliography: pending

# Expected ScholarDocument output
expected:
  # Page-level expected text (for text extraction evaluation)
  pages:
    - pdf_page: 150
      label: "127"           # Expected page_span.label
      text_hash: "abc123"    # SHA256 of expected clean text (optional)
      text_sample: |         # First 500 chars for spot-checking
        The 'essence' of Dasein lies in its existence...

  # Expected sections
  sections:
    - title: "§41. Dasein's Being as Care"
      level: 2
      start_page: 150
      end_page: 160
      # Position in continuous text (if known)
      start_offset: null
      end_offset: null

  # Expected footnote markers (FootnoteRef)
  footnote_markers:
    - id: fn_1
      label: "1"
      page: 150
      # Position relative to page start or absolute in document
      char_offset_in_page: 234
      context: "...lies in its existence.¹ Accordingly..."

  # Expected footnote content (Note)
  footnote_contents:
    - id: fn_1_content
      marker_id: fn_1        # Links to marker
      label: "1"
      note_type: author      # author | translator | editor
      text: "See the analysis of care in §41..."
      page: 150              # Where content appears

  # Expected citations (CitationRef)
  citations:
    - id: cite_1
      raw_text: "(SZ, 41)"
      page: 150
      char_offset_in_page: 789
      context: "...as Heidegger notes (SZ, 41) that..."
      parsed:
        style: abbreviated
        work_abbrev: "SZ"
        section: "41"

  # Expected page numbers
  page_numbers:
    - pdf_page: 150
      displayed: "127"
      format: arabic

# Visual annotations (for UI, not evaluation)
visual_annotations:
  regions:
    - id: body_150
      page: 150
      type: body
      bbox: [0.10, 0.08, 0.90, 0.72]
      contains: [fn_1]  # References to elements in this region

    - id: footnote_region_150
      page: 150
      type: footnote_region
      bbox: [0.10, 0.75, 0.90, 0.92]
      contains: [fn_1_content]

# Metadata
metadata:
  created: "2026-01-08"
  annotator: "human"
  notes: "Complex footnotes with German terms"
```

### Key Changes from v1.1.0

1. **Organized by ScholarDocument field** - not by element type
2. **Separate markers from content** - mirrors `footnote_refs` + `notes` structure
3. **Position is relative to page** - easier to annotate, convert to document offset later
4. **Visual regions are auxiliary** - for UI rendering, not core evaluation
5. **Hierarchical regions** - `contains` field shows what's inside
6. **Explicit evaluation scope** - what's tested vs pending

---

## Part 4: Annotation UI Requirements

### Per-Element-Type Annotation Needs

| Element | Annotation Method | UI Component |
|---------|-------------------|--------------|
| **Page text** | Side-by-side PDF/text, edit mismatches | Diff viewer |
| **Sections** | Click heading in PDF, enter title | Heading detector + form |
| **Footnote markers** | Click superscript in PDF | Click-to-mark + context |
| **Footnote content** | Select text region | Text selection + form |
| **Citations** | Select text in body | Text selection + parser |
| **Page numbers** | Click page number, enter value | Click + input |
| **Sous rature** | Select strikethrough text | Text selection with style |

### Minimum Viable Annotation UI

**Phase 1: Verification Mode**
- Side-by-side: PDF page | Extracted text | Expected text
- Highlight differences
- Edit expected text where extraction is wrong
- Mark page as verified/needs-work

**Phase 2: Element Annotation**
- Click in PDF → annotate footnote marker
- Select text → annotate citation
- Draw bbox → annotate region
- Form entry for structured fields

**Phase 3: Evaluation Integration**
- Run extraction, show comparison
- Click discrepancy → edit ground truth or flag extraction bug
- Track metrics over time

---

## Part 5: Implementation Plan

### Step 1: Define ScholarDocument → Ground Truth Mapping

Before any code:
1. Document exact mapping between ground truth fields and ScholarDocument fields
2. Define what "match" means for each field (exact? fuzzy? position tolerance?)
3. Create example: one page of ground truth + expected ScholarDocument

### Step 2: Create One Real Ground Truth Document

Using existing extraction:
1. Run `convert_pdf()` on `derrida_footnote_pages_120_125.pdf`
2. Manually verify each field of ScholarDocument output
3. Create ground truth YAML with verified values
4. Document any extraction errors found

### Step 3: Build Verification UI First

Simpler than full annotation:
1. Load ScholarDocument from extraction
2. Load ground truth expected values
3. Show side-by-side comparison
4. Allow editing expected values
5. Save to ground truth format

### Step 4: Add Element Annotation

Once verification works:
1. Click-to-annotate for footnote markers
2. Text selection for citations
3. Bbox drawing for regions

### Step 5: Evaluation Integration

After annotation:
1. Revise normalize.py to use new schema
2. Update matching.py for new structure
3. Integration test: extract → compare → report

---

## Part 6: Open Questions

### Q1: What about sous_rature?
- Not in ScholarDocument model
- Is it worth adding? Or defer to future?
- **Recommendation**: Defer - focus on footnotes/citations first

### Q2: What about marginal references (Stephanus, Bekker)?
- Also not in ScholarDocument
- Important for philosophy texts
- **Recommendation**: Add to ScholarDocument as `marginal_refs` before ground truth

### Q3: Position format - document offset or page-relative?
- Document offset: matches ScholarDocument, harder to annotate
- Page-relative: easier to annotate, needs conversion
- **Recommendation**: Store page-relative, convert at evaluation time

### Q4: How to handle multi-page footnotes?
- Marker on page N, content spans pages N and N+1
- **Recommendation**: Multiple `footnote_contents` entries with `continuation: true`

### Q5: Should we abandon PR #9?
- Contains working but flawed implementation
- **Options**:
  a) Close PR, start fresh
  b) Merge as-is, iterate
  c) Amend PR with redesign
- **Recommendation**: Close PR, create new one with redesigned system

---

## Approval Checklist

Before proceeding:

- [ ] Confirm we should focus on footnotes/citations first, defer sous_rature
- [ ] Confirm page-relative positions are acceptable
- [ ] Confirm we should close PR #9 and start fresh
- [ ] Confirm verification UI is the right first step
- [ ] Review ScholarDocument fields - any missing that we need?

---

## Summary

**What went wrong**: Built schema and UI without understanding what we're evaluating.

**Fix**:
1. Start from ScholarDocument fields (the extraction target)
2. Design ground truth as "expected ScholarDocument output"
3. Build verification UI before annotation UI
4. Create one real ground truth document manually first
5. Then build tools to help create more
