---
phase: quick-1
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md
autonomous: true
requirements: []

must_haves:
  truths:
    - "Every structural phenomena category (9 categories, ~85 phenomena) is mapped to Phase 1.1 schema capabilities"
    - "Each gap is rated by severity (blocking: cannot represent at all, degraded: representable with workarounds, nice-to-have: would improve but not required)"
    - "The gap analysis distinguishes between gaps addressable within Phase 1.1 plans vs requiring Phase 1.2"
    - "A clear recommendation exists for whether Phase 1.2 is needed with specific scope if so"
  artifacts:
    - path: ".planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md"
      provides: "Complete gap analysis mapping phenomena to schema capabilities"
      contains: "Phase 1.2 Recommendation"
  key_links: []
---

<objective>
Produce a gap analysis document that systematically maps each structural phenomenon from the DifficultTexts corpus inventory against the Phase 1.1 schema (5 plans), identifies representation gaps, rates severity, and recommends whether Phase 1.2 is needed.

Purpose: Before executing Phase 1.1's 5 plans, we need confidence that the redesigned schema can represent the ~85 structural phenomena discovered across ~5,272 pages of difficult scholarly texts. If critical gaps exist, we should know before committing to execution -- either adjusting Phase 1.1 plans or scoping a follow-up Phase 1.2.

Output: A single gap analysis document at `.planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md`
</objective>

<execution_context>
@/home/rookslog/.claude/get-shit-done/workflows/execute-plan.md
@/home/rookslog/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/STATE.md
@spikes/sample_pdfs/DifficultTexts/samples/structural_phenomena.md
@spikes/sample_pdfs/DifficultTexts/samples/corpus_inventory.md
@.planning/phases/01.1-schema-taxonomy-review-revision/01.1-CONTEXT.md
@.planning/phases/01.1-schema-taxonomy-review-revision/01.1-01-PLAN.md
@.planning/phases/01.1-schema-taxonomy-review-revision/01.1-02-PLAN.md
@.planning/phases/01.1-schema-taxonomy-review-revision/01.1-03-PLAN.md
@.planning/phases/01.1-schema-taxonomy-review-revision/01.1-04-PLAN.md
@.planning/phases/01.1-schema-taxonomy-review-revision/01.1-05-PLAN.md
@scholargt/schema/labels.py
@scholargt/schema/semantic.py
@scholargt/schema/spatial.py
@scholargt/schema/base.py
@scholargt/schema/page.py
@scholargt/schema/document.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Produce gap analysis mapping phenomena to Phase 1.1 schema capabilities</name>
  <files>.planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md</files>
  <action>
  Create a comprehensive gap analysis document with this structure:

  **Header Section:**
  - Title: "Phase 1.1 Gap Analysis: Schema vs Structural Phenomena"
  - Date, corpus size (~5,272 pages, 15 texts, ~85 phenomena in 9 categories)
  - Methodology: For each phenomenon, determine which Phase 1.1 schema model/field/enum represents it. Rate gaps.

  **Schema Capabilities Inventory (brief):**
  Summarize what Phase 1.1 (after all 5 plans) provides:
  - SpatialLabel: 20 values (NOTE_AREA, NOTE_CONTINUATION, TOC_AREA, ABSTRACT, CODE_BLOCK, UNKNOWN, etc.)
  - SemanticType: 9 values (NOTE, COMMENTARY, CITATION, etc.)
  - Note model: body_marker (LocationRef), content_marker, placement, scope, note_source, note_schema_id, marker_text
  - Commentary model: source, passage_ref, reference_system (ReferenceSystem), target_location (LocationRef), content, layer
  - NoteSchema: marker_type, symbol_sequence, reset_boundary, placement, note_source
  - Region: is_continuation, continues_to_next, semantic_element_ids, children (self-referential)
  - PageDependency: continues_from_previous, continues_to_next, unresolved_markers, orphan_continuations
  - SectionContextEntry: section_id, title, level, starts_on_this_page, ends_on_this_page
  - PageQuality: hybrid (overall, is_scan, artifacts, dpi_estimate, contrast_ratio, skew_angle, noise_level, ocr_difficulty, difficulty_factors)
  - CitationFormat x ReferenceSystem x CitationStyle: orthogonal citation decomposition
  - FormattingAnnotation: language field (BCP 47)
  - LocationRef: page, region_id, char_offset, char_length
  - ContentSpan: char_offset, char_length added
  - GTElement: extra="allow" for forward compatibility

  **Category-by-Category Analysis (9 sections):**

  For EACH of the 9 categories in structural_phenomena.md, create a section with:

  1. **Category name and phenomena count**
  2. **Coverage table:**

     | Phenomenon | Schema Coverage | Mechanism | Gap? | Severity |
     |-----------|----------------|-----------|------|----------|

     Where:
     - Schema Coverage: "Full", "Partial", "None", or "Implicit"
     - Mechanism: Which specific model/field covers it (e.g., "Note.placement='page_bottom' + Note.note_source='translator'")
     - Gap: Yes/No -- does the schema lack explicit representation?
     - Severity: "blocking" (cannot represent), "degraded" (workaround possible via tags/extra fields), "nice-to-have" (enhancement), "N/A" (no gap)

  3. **Gap details** for any phenomena rated "blocking" or "degraded" -- what specifically is missing and what would fix it.

  The analysis should cover these specific mappings (not exhaustive -- the executor should work through all ~85):

  **Category 1 (Dual/Multi-Register Layouts):**
  - Dual-column layouts -> Region with bbox positioning, potentially children for sub-regions
  - Horizontal register division -> Region with bbox + separator detection is extractor concern, not schema
  - Facing-page layout -> PageDependency (conceptual pairs across pages)
  - Multi-layer commentary -> Commentary model with source + layer fields
  - Variable-geometry blocks -> Region with bbox (dynamic geometry is extractor concern)
  - Bilingual side-by-side -> FormattingAnnotation.language + Region per language block

  Identify: Does the schema have a concept of "register" or "column identity"? Can two regions on the same page be marked as belonging to different parallel reading streams?

  **Category 2 (Footnote/Endnote Apparatus):**
  - Column-specific footnotes -> Note + LocationRef (region_id scopes to column)
  - Independent footnote systems -> NoteSchema (multiple schemas per document)
  - Per-page footnote reset -> NoteSchema.reset_boundary = "page"
  - Multi-page continuations -> Region.continues_to_next + ContentSpan.is_continuation
  - Endnote systems -> Note.placement = "end_of_book" + Note.scope = "document"
  - Translator vs author notes -> Note.note_source = "translator" vs "author"
  - Dense footnote apparatus -> No special schema need (density is annotation volume)

  **Category 3 (Typography and Semantic Encoding):**
  - Register-specific typography -> FormattingAnnotation per region
  - Typographic voice separation -> FormattingAnnotation + language/extra fields
  - Color-coded elements -> FormattingType lacks COLOR value
  - Multi-typeface semantic encoding -> FormattingType covers bold/italic/etc., but no TYPEFACE_CHANGE or SCRIPT_TYPE value

  Identify: Can the schema distinguish Rashi script from square Hebrew? Is "typeface as semantic signal" representable?

  **Category 4 (Quotations and Indentation):**
  - Block quotations -> SpatialLabel.BLOCK_QUOTE
  - Foreign language quotes -> BLOCK_QUOTE + FormattingAnnotation.language
  - Cross-page continuation -> Region.is_continuation + continues_to_next
  - Bracketed discourse -> SpatialLabel.BLOCK_QUOTE or TEXT_BLOCK with formatting

  **Category 5 (Foreign Language and Script Systems):**
  - Inline foreign passages -> FormattingAnnotation.language (BCP 47)
  - Greek/Latin in running text -> FormattingAnnotation.language = "el"/"la"
  - Rashi script -> FormattingAnnotation.language = "he-Hebr" (but script variant not modeled)
  - RTL base direction -> No explicit text_direction field on Region or Page
  - Bidirectional mixing -> No bidi field

  Identify: Does BCP 47 cover script variants (Rashi vs square Hebrew)? Is text direction modeled?

  **Category 6 (Reference Systems and Cross-Linking):**
  - Cross-page register continuity -> Region.is_continuation + PageDependency
  - Catchword anchoring -> Commentary.passage_ref (but no catchword-specific mechanism)
  - Verse-level anchoring -> Commentary.passage_ref + ReferenceSystem.CHAPTER_VERSE
  - Marginal edition pagination -> MarginalReference + ReferenceSystem.SZ_PAGINATION (and similar)
  - Commentary identification/attribution -> Commentary.source field
  - Traditional positioning conventions -> Extractor concern, not schema

  **Category 7 (Structural and Organizational):**
  - Page numbering/headers -> SpatialLabel.PAGE_HEADER, PAGE_FOOTER, PAGE_NUMBER
  - Section hierarchy -> Section model with level + children
  - Essay boundaries -> Section model
  - Indexes -> SpatialLabel.TOC_AREA (but no INDEX_AREA?)
  - Verse numbering -> Commentary references via ReferenceSystem.CHAPTER_VERSE
  - Parashah boundaries -> Section model with extra fields

  Identify: Is there a distinction between TOC and INDEX? Are there domain-specific section types (parashah, tractate, perek)?

  **Category 8 (Special Layout Phenomena):**
  - Text density variation -> PageQuality.difficulty_factors can note "variable_density"
  - Variable text block geometry -> Region bbox captures actual geometry
  - Synchronized column flow -> No explicit synchronization model
  - Page position effects -> SectionContextEntry gives context

  **Category 9 (Special and Unique):**
  - Handwritten annotations -> PageQuality.artifacts could flag "handwritten_overlay" but no annotation layer model
  - Mathematical notation -> FormattingType lacks MATH/FORMULA_INLINE (SpatialLabel.FORMULA is region-level)
  - Sous rature -> SousRature model exists
  - Scanned image format -> PageQuality.is_scan + artifacts
  - Parallel text enrichment -> No explicit "parallel reading" or "synchronized content" concept

  **Gap Summary Table:**

  | # | Gap Description | Category | Severity | Fix Location |
  |---|----------------|----------|----------|--------------|

  Consolidate all identified gaps into a single ranked table. For each gap:
  - Severity: blocking / degraded / nice-to-have
  - Fix Location: "Phase 1.1 plan adjustment" / "Phase 1.2" / "Phase 2+" / "Extractor concern" / "Not schema"

  **Phase 1.2 Recommendation:**

  Based on the gap analysis, provide a clear recommendation:
  - Is Phase 1.2 needed? (Yes/No/Conditional)
  - If yes: What specific scope should it cover? List specific additions.
  - If no: Explain why Phase 1.1 as planned is sufficient.
  - If conditional: What gaps are "blocking" vs "nice-to-have"?

  Consider these factors in the recommendation:
  1. GTElement uses extra="allow" -- any model can carry additional fields without schema change
  2. The schema is designed for progressive annotation -- not everything needs first-class modeling
  3. Some phenomena are extractor/pipeline concerns, not schema concerns
  4. Phase 2 (Extractor Interface) may naturally address some gaps
  5. The schema should represent what annotators need to MARK, not every parsing challenge

  **Writing guidelines:**
  - Be specific: cite the exact model, field, or enum value that covers each phenomenon
  - Be honest about gaps: if something requires a workaround, say so
  - Distinguish schema gaps from extractor gaps: the schema defines WHAT to annotate, extractors determine HOW to detect
  - Keep severity assessments grounded: "blocking" means an annotator literally cannot represent the phenomenon in GT
  </action>
  <verify>
  Verify the document exists, has all 9 category sections, a gap summary table, and a Phase 1.2 recommendation:

  ```bash
  # Check file exists and has expected sections
  test -f .planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md && echo "File exists"
  grep -c "## Category" .planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md
  grep -l "Phase 1.2 Recommendation" .planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md && echo "Has recommendation"
  grep -l "Gap Summary" .planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md && echo "Has gap summary"
  wc -l .planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md
  ```
  </verify>
  <done>
  A complete gap analysis document exists at `.planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md` that:
  1. Maps all 9 phenomenon categories (~85 phenomena) to Phase 1.1 schema capabilities
  2. Identifies every gap with specific severity rating (blocking/degraded/nice-to-have)
  3. Provides a consolidated gap summary table
  4. Makes a clear Phase 1.2 recommendation with specific scope (if needed)
  5. Distinguishes schema gaps from extractor/pipeline concerns
  </done>
</task>

</tasks>

<verification>
```bash
# Verify document completeness
test -f .planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md && echo "PASS: File exists"

# Verify all 9 categories covered
COUNT=$(grep -c "^## Category\|^### Category" .planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md 2>/dev/null || echo 0)
[ "$COUNT" -ge 9 ] && echo "PASS: All 9 categories present ($COUNT)" || echo "FAIL: Only $COUNT categories"

# Verify key sections present
grep -q "Gap Summary" .planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md && echo "PASS: Gap Summary section"
grep -q "Phase 1.2" .planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md && echo "PASS: Phase 1.2 recommendation"
grep -q "blocking\|degraded\|nice-to-have" .planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md && echo "PASS: Severity ratings present"

# Verify document is substantial (expect 300+ lines for thorough analysis)
LINES=$(wc -l < .planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md)
[ "$LINES" -ge 200 ] && echo "PASS: Substantial document ($LINES lines)" || echo "WARN: Only $LINES lines -- may be too brief"
```
</verification>

<success_criteria>
1. Gap analysis document exists with all 9 structural phenomena categories mapped
2. Each phenomenon has schema coverage assessment with specific mechanism cited
3. Gaps identified with severity ratings (blocking / degraded / nice-to-have)
4. Consolidated gap summary table present
5. Clear Phase 1.2 recommendation with rationale
6. Document distinguishes schema gaps from extractor concerns
</success_criteria>

<output>
After completion, create `.planning/quick/1-review-phase-1-1-gt-schema-against-diffi/1-SUMMARY.md`
</output>
