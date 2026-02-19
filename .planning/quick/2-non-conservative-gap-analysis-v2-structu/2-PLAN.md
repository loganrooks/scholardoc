---
phase: quick-2
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS-v2.md
autonomous: true
requirements: []
must_haves:
  truths:
    - "Every v1 'degraded' gap (G1-G5, G9) has a structural fix proposal, not just extra-field workarounds"
    - "Every v1 'nice-to-have' gap (G4, G6, G7, G8, G10, G11) is reassessed with non-conservative lens"
    - "Standard philosophy texts (Specters of Marx, Of Grammatology, Being and Time) are shown as first-class use cases, not afterthoughts"
    - "Talmudic and Derridean texts are treated as core use cases deserving dedicated modeling"
    - "Document produces concrete model proposals (new models, model redesigns, enum additions) not just field additions"
  artifacts:
    - path: ".planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS-v2.md"
      provides: "Non-conservative structural gap analysis with model proposals"
      min_lines: 400
  key_links:
    - from: "01.1-GAP-ANALYSIS-v2.md"
      to: "Phase 1.1 plans"
      via: "Structural fix proposals that inform whether plans need revision"
      pattern: "Structural Fix|Model Proposal|Enum Addition"
---

<objective>
Produce a non-conservative gap analysis (v2) of the Phase 1.1 schema against all 85 structural phenomena in the corpus. Unlike v1 which dismissed all gaps as "extra fields cover it," v2 treats every corpus phenomenon as a MUST-HANDLE case and proposes STRUCTURAL fixes (new models, model redesigns, enum additions) for every Partial/degraded gap.

Purpose: The user rejected v1's conservative approach. 30% of corpus pages are RTL multi-layer commentary in Rashi script -- that is a core use case deserving dedicated modeling, not extra-field workarounds. This analysis must redesign the schema to be DESIGNED for this corpus.

Output: `.planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS-v2.md`
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/execute-plan.md
@./.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Produce non-conservative gap analysis v2</name>
  <files>.planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS-v2.md</files>
  <action>
Read the following files to build full context:

1. **Current schema source files** (the actual code, not just descriptions):
   - `scholargt/schema/labels.py` -- current enums (SpatialLabel, SemanticType, FormattingType, CitationType, MarginalRefType)
   - `scholargt/schema/base.py` -- GTElement, BBox, VerificationRecord
   - `scholargt/schema/spatial.py` -- Region model
   - `scholargt/schema/semantic.py` -- Footnote, Endnote, Citation, BibEntry, Section, SousRature, CrossReference, MarginalReference, PageNumberAnnotation, ContentSpan, MarkerInfo
   - `scholargt/schema/formatting.py` -- FormattingAnnotation
   - `scholargt/schema/page.py` -- PageGT, PageQuality
   - `scholargt/schema/document.py` -- DocumentGT, DocumentSource, DocumentStructure, DocumentRelationships

2. **Structural phenomena catalogue**: `spikes/sample_pdfs/DifficultTexts/samples/structural_phenomena.md` -- all 85 phenomena in 9 categories

3. **v1 gap analysis**: `.planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS.md` -- to understand what was too conservative and explicitly do better

4. **Phase 1.1 plans** (to understand what's proposed but not yet executed):
   - `.planning/phases/01.1-schema-taxonomy-review-revision/01.1-01-PLAN.md`
   - `.planning/phases/01.1-schema-taxonomy-review-revision/01.1-02-PLAN.md`
   - `.planning/phases/01.1-schema-taxonomy-review-revision/01.1-03-PLAN.md`

Then write `01.1-GAP-ANALYSIS-v2.md` with this EXACT structure and approach:

---

### DOCUMENT HEADER

```
# Phase 1.1 Gap Analysis v2: Structural Schema Review
# Non-Conservative Analysis — Corpus Phenomena as Must-Handle Cases

Date: 2026-02-19
Methodology: NON-CONSERVATIVE
```

**Methodology statement** (2-3 paragraphs): Explain that v1 treated all gaps as "extra fields cover it." v2 takes the opposite stance: every phenomenon in this corpus is a FIRST-CLASS use case. If 30% of pages are RTL multi-layer commentary, that needs a Register model, not a tag. If Derrida's dual-column texts are 7 of 15 books, columns need first-class identity. The schema should be DESIGNED for these texts, not merely tolerant.

**Assessment framework** -- for each phenomenon, rate as:
- **Full**: Schema models this phenomenon with dedicated structure
- **Partial-Structural**: Schema can represent it but through workarounds/extra fields -- needs a STRUCTURAL fix
- **Partial-Adequate**: Schema represents it well enough that a structural fix would be over-engineering
- **None**: Cannot represent at all

For every **Partial-Structural** or **None**, produce a **Structural Fix Proposal** with:
1. What model/enum change is needed
2. Why extra fields are NOT sufficient for this use case
3. Concrete Pydantic-style field/model sketch
4. Which corpus texts benefit
5. Impact on Phase 1.1 plans (which plan would need revision)

---

### SCHEMA CAPABILITIES INVENTORY

List the CURRENT schema (v1.0.0, what exists in code NOW) and the PROPOSED schema (v2.0.0, what Phase 1.1 plans will create). Be precise about what exists vs what is proposed.

**Current schema (v1.0.0) -- what actually exists in code:**

Region model (from `spatial.py`):
- label: SpatialLabel (17 values: TEXT_BLOCK, FOOTNOTE_AREA, ENDNOTE_AREA, PAGE_HEADER, PAGE_FOOTER, PAGE_NUMBER, SECTION_HEADER, TITLE, BLOCK_QUOTE, LIST_ITEM, TABLE, FIGURE, CAPTION, FORMULA, MARGINAL_NOTE, BIBLIOGRAPHY_AREA, FOOTNOTE_CONTINUATION)
- bbox: BBox, text: str|None, text_anchors: list[str], semantic_labels: list[SemanticType], reading_order_index: int|None
- NO children, NO is_continuation, NO continues_to_next, NO semantic_element_ids

SpatialLabel enum (17 values): TEXT_BLOCK, FOOTNOTE_AREA, ENDNOTE_AREA, PAGE_HEADER, PAGE_FOOTER, PAGE_NUMBER, SECTION_HEADER, TITLE, BLOCK_QUOTE, LIST_ITEM, TABLE, FIGURE, CAPTION, FORMULA, MARGINAL_NOTE, BIBLIOGRAPHY_AREA, FOOTNOTE_CONTINUATION

SemanticType enum (9 values): FOOTNOTE, ENDNOTE, CITATION, BIBLIOGRAPHY_ENTRY, SECTION, SOUS_RATURE, CROSS_REFERENCE, MARGINAL_REFERENCE, PAGE_NUMBER_ANNOTATION

FormattingType enum (6 values): BOLD, ITALIC, UNDERLINE, STRIKETHROUGH, SMALL_CAPS, SUPERSCRIPT
- NO SUBSCRIPT, NO MONOSPACE

FormattingAnnotation: formatting_type, page, region_id, char_offset, char_length, text
- NO language field

Semantic models: Footnote, Endnote (separate models), Citation (uses CitationType 7-value enum), BibEntry, Section, SousRature, CrossReference, MarginalReference (uses MarginalRefType 4-value enum), PageNumberAnnotation

CitationType enum (7 values): AUTHOR_DATE, NUMERIC, ABBREVIATED, FOOTNOTE_STYLE, STEPHANUS, BEKKER, AK_REFERENCE

MarginalRefType enum (4 values): STEPHANUS, BEKKER, AKADEMIE, CUSTOM

PageQuality: scan_quality (low/medium/high), difficulty (easy/medium/hard) -- two categorical fields, no numeric metrics

PageGT: page_index, page_label, dimensions, regions, reading_order, quality, verifications
- NO section_context, NO page_dependency

DocumentGT: schema_version, document_id, source, page_range, elements, formatting, structure, relationships, config_profile, verifications
- NO note_schemas, NO citation_style

**Proposed schema (v2.0.0) -- what Phase 1.1 plans will add (NOT YET EXECUTED):**

Plan 01 adds: LocationRef model, SpatialLabel cleanup (NOTE_AREA/NOTE_CONTINUATION replacing FOOTNOTE_AREA/ENDNOTE_AREA/FOOTNOTE_CONTINUATION, plus TOC_AREA/ABSTRACT/CODE_BLOCK/UNKNOWN), SemanticType cleanup (NOTE replacing FOOTNOTE/ENDNOTE, plus COMMENTARY), new enums (CitationFormat x5, ReferenceSystem x12, CitationStyle x7), FormattingType adds SUBSCRIPT/MONOSPACE, schema version 2.0.0

Plan 02 adds: Note model (replacing Footnote/Endnote), Commentary model, NoteSchema model, updated Citation/BibEntry/MarginalReference, Region gains is_continuation/continues_to_next/semantic_element_ids/children, FormattingAnnotation gains language field

Plan 03 adds: PageQuality hybrid (overall + is_scan + artifacts + metrics), PageDependency model, SectionContextEntry model, PageGT gains section_context/page_dependency, DocumentGT gains note_schemas/citation_style

---

### GAP ANALYSIS BY CATEGORY

For each of the 9 categories from the structural phenomena catalogue, create a table and detailed analysis. The 9 categories are:

**Category 1: Dual/Multi-Register Layouts (8 phenomena: 1.1-1.8)**

Phenomena to analyze:
- 1.1: Asymmetric dual-column structure (Glas -- Hegel vs Genet columns)
- 1.2: Horizontal register division (Circumfession -- Bennington upper, Derrida lower)
- 1.3: Facing-page horizontal layout (Of Hospitality -- verso/recto pairing)
- 1.4: Vertical column separation (Tympan -- left/right columns)
- 1.5: Central Gemara with multi-layer commentary (Vilna Shas -- central text + Rashi + Tosafot)
- 1.6: Variable-geometry commentary blocks (Mikraot Gedolot -- frame layout)
- 1.7: Bilingual side-by-side layout (Koren -- Hebrew/English; Gibbs)
- 1.8: Central text with peripheral apparatus (Gibbs -- talmudic evocation)

KEY STRUCTURAL GAP HERE: The schema has NO concept of a "register" or "column identity." Two regions on the same page cannot be explicitly linked as belonging to different reading streams. This affects 1.1, 1.2, 1.3, 1.4, 1.5, 1.7, 1.8 -- the MAJORITY of the corpus.

Structural Fix Proposal needed: A `LayoutRegister` model at the document level (or page level) that maps register IDs to metadata (author, language, reading direction, position convention). Region gains a `register_id: str | None` field. This is NOT "just a field addition" -- it requires a new model and fundamentally changes how multi-column/multi-register texts are represented.

**Category 2: Footnote/Endnote Apparatus (11 phenomena: 2.1-2.11)**

Phenomena to analyze: 2.1 through 2.11 (column-specific footnotes, independent systems, per-page regions, complex architecture, dense apparatus, per-page reset, multi-page continuations, endnote systems, marker density, translator vs author, dual streams).

The Phase 1.1 Note/NoteSchema redesign likely handles most of these well. Confirm Full coverage or identify remaining gaps.

**Category 3: Typography and Semantic Encoding (9 phenomena: 3.1-3.9)**

Phenomena: 3.1 (register-specific typography), 3.2 (typographic voice separation), 3.3 (differential typeface registers), 3.4 (typographic variation as semantic signal), 3.5 (emphasis combinations), 3.6 (complex hierarchy), 3.7 (multi-typeface semantic encoding -- Rashi vs square Hebrew), 3.8 (typography as hierarchical indicator), 3.9 (color-coded elements -- Koren)

KEY STRUCTURAL GAPS:
- No font/typeface annotation model. FormattingType covers decoration (bold, italic) but NOT typeface identity. For Rashi script vs square Hebrew, the typeface IS the semantic signal. Affects ~1,483 pages of Talmudic texts.
- No color model. Color is semantic in Koren (449 pages).
- No script variant distinction. BCP 47 cannot distinguish Rashi from square Hebrew.

Structural Fix Proposals needed:
1. A `ScriptVariant` or `TypefaceAnnotation` model/enum for script variant distinction
2. A `COLOR` addition to FormattingType with a color value field on FormattingAnnotation
3. Consider whether FormattingAnnotation itself needs redesign to handle font-level properties

**Category 4: Quotations and Indentation (7 phenomena: 4.1-4.7)**

Phenomena: 4.1-4.7. The BLOCK_QUOTE label + FormattingAnnotation.language + Region continuation flags likely handle these well. Confirm coverage.

**Category 5: Foreign Language and Script Systems (9 phenomena: 5.1-5.9)**

Phenomena: 5.1 (italicized foreign passages), 5.2 (Greek/Latin in running text), 5.3 (interpolated German terms), 5.4 (mixed language/transliteration), 5.5 (Rashi script), 5.6 (RTL with nested complexity), 5.7 (RTL directionality), 5.8 (script differentiation), 5.9 (multilingual apparatus)

KEY STRUCTURAL GAPS:
- No text_direction field on Region or Page. RTL is a base property for ~1,483 pages of Hebrew/Aramaic text. Language tags "imply" direction but do not DECLARE it. For ground truth evaluation of extraction quality, you need to KNOW the expected direction, not derive it.
- Script variant gap (cross-reference with Category 3)

Structural Fix Proposals needed:
1. `text_direction: Literal["ltr", "rtl", "bidi"] | None` on Region
2. `base_direction: Literal["ltr", "rtl"] | None` on PageGT

**Category 6: Reference Systems and Cross-Linking (11 phenomena: 6.1-6.11)**

Phenomena: 6.1-6.11. The ReferenceSystem enum (12 values) and Commentary model should handle most. Check catchword anchoring (6.6) -- is CUSTOM sufficient or does it need a CATCHWORD value?

**Category 7: Structural and Organizational Features (11 phenomena: 7.1-7.11)**

Phenomena: 7.1-7.11. Check INDEX_AREA gap (7.6, 7.7). With non-conservative lens, is UNKNOWN + tags really acceptable for a back-of-book index that appears in 2 major texts?

**Category 8: Special Layout Phenomena (8 phenomena: 8.1-8.8)**

Phenomena: 8.1-8.8. Check synchronized column flow (8.5) -- does it need structural modeling or is it genuinely an analysis concern?

**Category 9: Special and Unique Phenomena (9 phenomena: 9.1-9.9)**

Phenomena: 9.1-9.9. Check handwritten annotations (9.1), mathematical notation (9.3). With non-conservative lens, does handwritten annotation need a dedicated model even though it appears in only 4 pages?

---

### REVISED GAP SUMMARY TABLE

Reissue all gaps with new severity ratings using the non-conservative framework. For each gap:
- Gap ID (G1, G2, ... reuse v1 IDs where applicable, add new ones)
- Description
- Category
- v1 Severity vs v2 Severity
- v2 Assessment (why the severity changed or didn't)
- Structural Fix Proposal (brief)
- Corpus Impact (how many pages/texts affected)
- Phase 1.1 Plan Impact (which plan needs revision, if any)

---

### STRUCTURAL FIX PROPOSALS -- DETAILED

For each Partial-Structural gap, provide a DETAILED structural fix proposal:

**Proposal format:**
```
### SFP-N: [Title]
**Addresses gaps:** G1, G4, ...
**Corpus impact:** N pages across M texts
**Why extra fields are insufficient:** [explanation]

**Proposed model/enum changes:**
[Pydantic-style pseudocode showing the actual model]

**Phase 1.1 plan impact:**
- Plan NN would need to add [specific changes]
- OR: New plan NN needed for [specific work]

**Texts that benefit:**
- [List of specific texts and how they benefit]
```

Expected structural fix proposals (minimum -- add more if analysis reveals them):

SFP-1: LayoutRegister model + Region.register_id
- For dual-column, multi-register, commentary layouts
- Affects: Glas, Circumfession, Tympan, Of Hospitality, Vilna Shas, Mikraot Gedolot, Koren, Gibbs

SFP-2: Text direction on Region and Page
- For RTL/bidi text
- Affects: All Talmudic texts, Mikraot Gedolot, Koren

SFP-3: Script variant / typeface annotation
- For Rashi vs square Hebrew, typeface-as-semantic-signal
- Affects: Vilna Shas, Mikraot Gedolot, Koren

SFP-4: Color annotation
- For color-coded semantic elements
- Affects: Koren Talmud

SFP-5: INDEX_AREA spatial label
- For back-of-book indexes
- Affects: Of Grammatology, Being and Time

SFP-6: Catchword reference system
- For dibbur ha-matchil anchoring
- Affects: Vilna Shas, Mikraot Gedolot

Potentially also:
- SFP-7: Handwritten annotation layer model
- SFP-8: Inline math/formula formatting type
- SFP-9: Synchronized column flow annotation

---

### IMPACT ON PHASE 1.1 PLANS

Table showing which Phase 1.1 plans would need revision if structural fixes are adopted. For each plan:
- What changes would be needed
- Estimated additional complexity
- Whether the plan can absorb the changes or needs a new plan

---

### RECOMMENDATIONS

Three-tier recommendation:

**Tier 1 -- Must adopt (schema is fundamentally under-designed without these):**
List the SFPs that address the most widespread corpus gaps affecting the most pages.

**Tier 2 -- Should adopt (significantly improves schema for core use cases):**
List SFPs that address important but less pervasive gaps.

**Tier 3 -- Consider deferring (real but narrow gaps):**
List SFPs where extra fields truly are acceptable because the phenomenon is very rare or analytical rather than annotatable.

---

### COMPARISON WITH v1

Brief section showing how v2 differs from v1:
- How many gaps changed severity
- Which gaps were newly identified
- What the v1 "extra fields cover it" approach missed

---

**CRITICAL INSTRUCTIONS FOR THE EXECUTOR:**

1. Do NOT dismiss any gap as "extra fields cover it" unless you can genuinely argue that the phenomenon is (a) extremely rare (<10 pages total) AND (b) genuinely not a structural annotation concern. Even then, say so explicitly and defend it.

2. When you assess a phenomenon as "Full" coverage, explain HOW the schema models it. Do not just say "Full" without showing the mechanism.

3. When you assess a phenomenon as "Partial-Structural," you MUST produce a concrete structural fix proposal. No hand-waving.

4. Standard philosophy texts (Specters of Marx, Of Grammatology, Being and Time) should be shown as WELL-SERVED by the schema. They are the baseline. The analysis should show that even these "standard" texts have phenomena that benefit from structural modeling (dual footnote streams in Being and Time, dense endnote apparatus in Specters, translator notes in Of Grammatology).

5. The tone should be: "This corpus demands these models. Here is exactly what we need." Not: "These are nice-to-have enhancements for edge cases."

6. Maintain the v1 gap IDs (G1-G11) where the same gap applies, but feel free to add new gap IDs (G12, G13, ...) for newly identified structural gaps.

7. The document should be 500-800 lines. Be thorough but not repetitive.
  </action>
  <verify>
Verify the output file exists and has the expected structure:
```bash
# File exists and is substantial
wc -l .planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS-v2.md

# Contains key structural sections
grep -c "Structural Fix Proposal\|SFP-\|Partial-Structural\|LayoutRegister\|text_direction\|ScriptVariant\|Tier 1\|Tier 2\|Tier 3" .planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS-v2.md
```

Both commands should show: file is 400+ lines, and contains multiple instances of structural fix keywords.
  </verify>
  <done>
01.1-GAP-ANALYSIS-v2.md exists in the Phase 1.1 directory alongside v1. It contains:
- Non-conservative assessment of all 85 phenomena across 9 categories
- "Partial-Structural" ratings (not "degraded") with concrete structural fix proposals for each
- At minimum SFP-1 through SFP-6 with Pydantic-style model sketches
- Impact analysis on Phase 1.1 plans
- Three-tier recommendations (must/should/consider)
- Comparison with v1 showing what changed
- Standard philosophy texts shown as first-class use cases
- 400+ lines of substantive analysis
  </done>
</task>

</tasks>

<verification>
- File `.planning/phases/01.1-schema-taxonomy-review-revision/01.1-GAP-ANALYSIS-v2.md` exists
- File is 400+ lines
- Contains structural fix proposals (SFP-1 through SFP-6 minimum)
- Every v1 degraded gap (G1-G5, G9) has a structural fix, not just "extra fields"
- Every v1 nice-to-have gap reassessed with non-conservative lens
- Standard texts (Specters, Grammatology, Being and Time) covered as first-class
- Three-tier recommendations present
- v1 comparison section present
</verification>

<success_criteria>
The document enables the user to make an informed decision about which structural fixes to adopt before executing Phase 1.1 plans. Each proposal is concrete enough (model sketches, enum values, field definitions) that it could be incorporated into a revised Phase 1.1 plan without further research.
</success_criteria>

<output>
After completion, create `.planning/quick/2-non-conservative-gap-analysis-v2-structu/2-SUMMARY.md`
</output>
