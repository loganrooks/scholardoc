# Comprehensive Ground Truth Test Plan

## Scope: Western Philosophy + Continental Thinkers

Focus on the canon of Western philosophy and continental thinkers. Scientific papers, legal documents, and non-Western texts are deferred to future validation efforts.

## Schema Status

### ✅ Already in Schema (models.py)

| Element | Classes | Status |
|---------|---------|--------|
| **Citations** | `CitationRef`, `ParsedCitation`, `BibEntry` | ✅ Complete |
| **Footnotes** | `FootnoteRef`, `Note`, `NoteType` | ✅ Complete |
| **Endnotes** | `EndnoteRef`, `Note` | ✅ Complete |
| **Cross-refs** | `CrossRef` | ✅ Complete |
| **Page spans** | `PageSpan` (supports "A64/B93") | ✅ Complete |
| **ToC** | `ToCEntry`, `TableOfContents` | ✅ Complete |
| **Sections** | `SectionSpan` | ✅ Complete |
| **Metadata** | `DocumentMetadata` | ✅ Complete |

### ❌ Missing from Schema

1. **Marginal Reference Markers** (Proprietary Citation Systems)
   - Stephanus numbers (Plato): "245a", "245b"
   - Bekker numbers (Aristotle): "1094a1", "1094b15"
   - Akademie numbers (Kant): "A64/B93", "Ak. 4:421"
   - Standard page numbers appear in margins alongside these

   **Proposed addition:**
   ```python
   @dataclass(frozen=True)
   class MarginalRef:
       """A proprietary citation marker in the margin."""
       position: int  # Position in text
       marker: str  # "245a", "1094b15", "Ak. 4:421"
       system: str  # "stephanus", "bekker", "akademie", "custom"
       page_label: str  # Associated page label
   ```

2. **Multi-Page Footnotes** (Continuation Notes)
   - Current `Note.page_label` is singular
   - Need: `page_labels: list[str]` or `continues_from: str`

3. **Front Matter Classification**
   - Title page, copyright, dedication, preface types
   - Could extend `SectionSpan` with `section_type` enum

## Extraction Targets (All elements ScholarDoc should extract)

### 1. Notes (Footnotes & Endnotes)
- [ ] Footnote markers in body text (superscript, brackets)
- [ ] Footnote content at page bottom
- [ ] Multi-page/continuation footnotes
- [ ] Endnote markers
- [ ] Endnote sections (at chapter/book end)
- [ ] Translator's notes (often marked differently)
- [ ] Editor's notes

### 2. Citations & References
- [ ] In-text citations: "(Heidegger 1927, 45)"
- [ ] Bracketed references: "[1]", "[Heidegger]"
- [ ] Bibliography/Works Cited section
- [ ] Parsed citation structure (authors, year, pages)

### 3. Page Information
- [ ] Page numbers (Arabic: 1, 2, 3)
- [ ] Page numbers (Roman: i, ii, iii)
- [ ] Mixed pagination (front matter Roman, body Arabic)
- [ ] Marginal page references (Stephanus, Bekker, Ak.)

### 4. Document Structure
- [ ] Table of Contents
- [ ] Chapter headings
- [ ] Section headings
- [ ] Subsection headings

### 5. Front Matter
- [ ] Title page
- [ ] Copyright page
- [ ] Dedication
- [ ] Acknowledgments
- [ ] Preface (author's)
- [ ] Introduction (may be editor's)
- [ ] Abbreviations list
- [ ] Note on translation

### 6. Back Matter
- [ ] Bibliography/Works Cited
- [ ] Index
- [ ] Appendices
- [ ] Notes section (for endnotes)

### 7. Special Content
- [ ] Block quotes
- [ ] Foreign language passages (Greek, German, French, Latin)
- [ ] Mathematical notation (rare in philosophy)

## Test Categories

### Category A: Notes (15 pages)

| Subcategory | Pages | Description | Source PDFs |
|-------------|-------|-------------|-------------|
| A1: Dense footnotes | 4 | >3 FN/page | Heidegger BeingAndTime, Derrida Margins |
| A2: Moderate footnotes | 3 | 1-3 FN/page | Kant Critique |
| A3: Multi-page footnotes | 3 | Continuation across pages | Find examples |
| A4: Translator notes | 2 | Marked as [TN] or similar | Heidegger translations |
| A5: Endnotes (control) | 3 | No page footnotes | WritingAndDifference |

### Category B: Citations (10 pages)

| Subcategory | Pages | Description | Source PDFs |
|-------------|-------|-------------|-------------|
| B1: Author-date citations | 3 | "(Hegel 1807, 123)" | Academic texts |
| B2: Numeric citations | 2 | "[1]", "[23]" | If available |
| B3: Dense citations | 3 | Multiple per paragraph | Literature reviews |
| B4: Bibliography section | 2 | Reference list | Various |

### Category C: Marginal References (10 pages)

| Subcategory | Pages | Description | Source PDFs |
|-------------|-------|-------------|-------------|
| C1: Stephanus (Plato) | 3 | "245a-b" style | Need Plato edition |
| C2: Bekker (Aristotle) | 3 | "1094a1" style | Need Aristotle edition |
| C3: Akademie (Kant) | 2 | "A64/B93", "Ak. 4:421" | Kant Critique |
| C4: Custom margins | 2 | Other systems | Heidegger Sein und Zeit refs |

### Category D: Front Matter (10 pages)

| Subcategory | Pages | Description | Source PDFs |
|-------------|-------|-------------|-------------|
| D1: Title page | 2 | Title, author, publisher | Various |
| D2: Copyright page | 2 | ISBN, copyright info | Various |
| D3: Table of Contents | 3 | Different ToC styles | Various |
| D4: Preface/Introduction | 3 | Front matter text | Various |

### Category E: Page Numbers (10 pages)

| Subcategory | Pages | Description | Source PDFs |
|-------------|-------|-------------|-------------|
| E1: Arabic numbers | 3 | Standard 1, 2, 3 | Any |
| E2: Roman numerals | 3 | Front matter i, ii, iii | Any |
| E3: Transition pages | 2 | Where numbering switches | Various |
| E4: No visible number | 2 | Chapter starts, etc. | Various |

### Category F: Edge Cases (5 pages)

| Subcategory | Pages | Description | Source PDFs |
|-------------|-------|-------------|-------------|
| F1: Very long footnotes | 2 | >10 lines | Find examples |
| F2: Greek/foreign text | 2 | In footnotes | Derrida, Heidegger |
| F3: Heavily annotated | 1 | Many layers | Find examples |

## PDFs Needed

### Have (Full Books)
- ✅ Derrida: Margins of Philosophy, Writing and Difference, Dissemination, etc.
- ✅ Heidegger: Being and Time, Pathmarks, Discourse on Thinking
- ✅ Kant: Critique of Judgment
- ✅ Lenin: State and Revolution (control - political text)

### Need to Source
- ❌ **Plato** edition with Stephanus numbers
- ❌ **Aristotle** edition with Bekker numbers
- ❌ Kant **Critique of Pure Reason** (for A/B pagination)
- ❌ Any text with clear **multi-page footnotes**
- ❌ Text with **numeric citation** style

### User to Download
Please provide:
1. Plato - Any Hackett or Cambridge edition (for Stephanus)
2. Aristotle - Any edition with Bekker numbers
3. Kant - Critique of Pure Reason (Guyer/Wood or Kemp Smith)

## PDF Directory Structure

```
spikes/sample_pdfs/
├── full_books/           # Complete PDFs for reference
│   ├── derrida/
│   │   ├── MarginsOfPhilosophy.pdf
│   │   └── WritingAndDifference.pdf
│   ├── heidegger/
│   │   ├── BeingAndTime.pdf
│   │   └── Pathmarks.pdf
│   ├── kant/
│   │   ├── CritiqueOfJudgment.pdf
│   │   └── CritiqueOfPureReason.pdf  # NEEDED
│   └── classics/
│       ├── plato/                     # NEEDED
│       └── aristotle/                 # NEEDED
│
├── extracts/             # Curated test page extracts
│   ├── footnotes/
│   │   ├── dense_footnotes_derrida_margins_250.pdf
│   │   └── multipage_footnote_example.pdf
│   ├── citations/
│   │   ├── author_date_example.pdf
│   │   └── bibliography_section.pdf
│   ├── margins/
│   │   ├── stephanus_plato_republic.pdf
│   │   ├── bekker_aristotle_ethics.pdf
│   │   └── akademie_kant_cpr.pdf
│   ├── front_matter/
│   │   ├── toc_heidegger_bt.pdf
│   │   └── preface_kant.pdf
│   └── edge_cases/
│       └── greek_text_derrida.pdf
│
└── README.md             # Index of all samples
```

## Ground Truth Annotation Schema

```yaml
# ground_truth/annotations/page_XXXXX.yaml
page_id: "derrida_margins_p250"
source:
  pdf: "full_books/derrida/MarginsOfPhilosophy.pdf"
  page_index: 250
  page_label: "234"

categories: [dense_footnotes, greek_text]

# What we expect to extract
expected:
  footnotes:
    count: 4
    markers: ["1", "2", "3", "4"]
    has_continuation: false

  citations:
    count: 2
    examples:
      - original: "(Hegel 1807, 123)"
        type: author_date

  marginal_refs:
    count: 0  # No Stephanus/Bekker on this page

  page_info:
    arabic_number: "234"
    roman_number: null
    marginal_system: null

  structure:
    sections: ["The Double Session"]
    is_chapter_start: false

notes: "Contains Greek quote in footnote 2"
difficulty: medium
verified_by: null  # Human verification status
```

## Evaluation Metrics

### Per-Element Metrics

| Element | Detection Metric | Accuracy Metric |
|---------|-----------------|-----------------|
| Footnotes | Recall (% found) | Position accuracy |
| Citations | Recall + Precision | Parse accuracy |
| Marginal refs | Recall | System classification |
| Page numbers | Detection rate | Label accuracy |
| ToC | Structure match | Page ref accuracy |

### Overall Metrics
- **Coverage**: % of elements detected
- **Precision**: % of detections that are correct
- **F1 Score**: Harmonic mean of precision/recall
- **Position Accuracy**: IoU of detected vs actual boxes

## Next Steps

1. [ ] User provides missing PDFs (Plato, Aristotle, Kant CPR)
2. [ ] Reorganize existing PDFs into new directory structure
3. [ ] Add `MarginalRef` type to schema
4. [ ] Create extract PDFs for each test category
5. [ ] Begin annotation of ~60 test pages
6. [ ] Run Docling baseline on full expanded test set

## Version History

- 2026-01-07: Expanded plan with full extraction targets
