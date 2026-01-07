# Sample PDF Organization

> **Status:** PROPOSAL - Needs approval
> **Date:** 2026-01-06

---

## Current State

All PDFs are in `spikes/sample_pdfs/` with inconsistent naming:
- Some have spaces: `Acts of Religion (Jacques Derrida) (2016) (Z-Library).pdf`
- Some use underscores: `Kant_CritiqueOfJudgement.pdf`
- Extracts mixed with full PDFs
- No clear ID system for referencing

---

## Proposed Structure

```
test_files/
├── corpus/                    # Full PDFs for extraction
│   ├── full/                 # Complete books
│   │   ├── kant-coj.pdf      # Kant - Critique of Judgement
│   │   ├── kant-cpr.pdf      # Kant - Critique of Pure Reason (NEEDED)
│   │   ├── heidegger-bt.pdf  # Heidegger - Being and Time
│   │   ├── heidegger-dt.pdf  # Heidegger - Discourse on Thinking
│   │   ├── heidegger-pm.pdf  # Heidegger - Pathmarks
│   │   ├── derrida-wd.pdf    # Derrida - Writing and Difference
│   │   ├── derrida-mp.pdf    # Derrida - Margins of Philosophy
│   │   ├── derrida-tp.pdf    # Derrida - Truth in Painting
│   │   ├── derrida-bs1.pdf   # Derrida - Beast and Sovereign Vol 1
│   │   ├── derrida-diss.pdf  # Derrida - Dissemination
│   │   ├── derrida-acts.pdf  # Derrida - Acts of Religion
│   │   ├── derrida-rog.pdf   # Derrida - Rogues
│   │   ├── derrida-mono.pdf  # Derrida - Monolingualism
│   │   ├── comay-ms.pdf      # Comay - Mourning Sickness
│   │   └── lenin-sr.pdf      # Lenin - State and Revolution
│   │
│   └── extracts/             # Page ranges for focused testing
│       ├── kant-cpr-64-65.pdf        # Multi-page footnote test
│       ├── heidegger-bt-22-23.pdf    # Primary footnote test
│       ├── heidegger-bt-17-24.pdf    # Translator preface
│       ├── derrida-og-120-125.pdf    # Symbol corruption test
│       └── [additional extracts...]
│
├── ground_truth/             # Annotated test cases
│   ├── footnotes/
│   ├── citations/
│   ├── margins/
│   └── bibliography/
│
└── registry.yaml             # Master index of all files
```

---

## ID Slug Convention

Format: `{author}-{work_abbrev}[-{pages}]`

| ID Slug | Full Title | Author | Features |
|---------|-----------|--------|----------|
| `kant-coj` | Critique of Judgement | Kant | Ak. margins, footnotes |
| `kant-cpr` | Critique of Pure Reason | Kant | A/B pagination, Ak. margins |
| `heidegger-bt` | Being and Time | Heidegger | H. margins, translator notes |
| `heidegger-dt` | Discourse on Thinking | Heidegger | Footnotes |
| `heidegger-pm` | Pathmarks | Heidegger | Multiple essays |
| `derrida-wd` | Writing and Difference | Derrida | Endnotes |
| `derrida-mp` | Margins of Philosophy | Derrida | Page-bottom footnotes |
| `derrida-tp` | Truth in Painting | Derrida | Complex layout |
| `derrida-bs1` | Beast and Sovereign v1 | Derrida | Lecture format |
| `derrida-diss` | Dissemination | Derrida | Endnotes, bibliography |
| `derrida-acts` | Acts of Religion | Derrida | Multiple essays |
| `derrida-rog` | Rogues | Derrida | Two essays |
| `derrida-mono` | Monolingualism of Other | Derrida | Short text |
| `derrida-og` | Of Grammatology | Derrida | Symbol corruption |
| `comay-ms` | Mourning Sickness | Comay | Modern monograph, endnotes |
| `lenin-sr` | State and Revolution | Lenin | Different style baseline |

---

## Registry File Format

```yaml
# test_files/registry.yaml
version: "1.0"
last_updated: "2026-01-06"

works:
  kant-coj:
    full_title: "Critique of Judgement"
    author: "Immanuel Kant"
    translator: "Werner Pluhar"
    publisher: "Hackett"
    year: 1987
    file: "corpus/full/kant-coj.pdf"
    pages: 685
    features:
      marginal_system: "akademie"
      marginal_pattern: "Ak. \\d+"
      footnote_schema:
        author: ["*", "†", "‡"]
        translator: ["a", "b", "c"]
        editor: ["1", "2", "3"]
      has_endnotes: true
      has_bibliography: true
    extracts:
      - id: "kant-coj-intro"
        pages: "1-100"
        features: ["translator_notes", "ak_margins"]

  kant-cpr:
    full_title: "Critique of Pure Reason"
    author: "Immanuel Kant"
    status: "NEEDED"
    features:
      marginal_system: "ab_pagination"
      marginal_pattern: "[AB]\\d+"
    notes: "Need PDF with A/B margins"

  heidegger-bt:
    full_title: "Being and Time"
    author: "Martin Heidegger"
    translator: "Macquarrie & Robinson"
    publisher: "Blackwell"
    year: 1962
    file: "corpus/full/heidegger-bt.pdf"
    pages: 590
    features:
      marginal_system: "sein_und_zeit"
      marginal_pattern: "H\\.?\\s*\\d+"
      footnote_schema:
        translator: ["1", "2", "3", "a", "b", "c"]
      has_endnotes: true
    extracts:
      - id: "heidegger-bt-22-23"
        pages: "22-23"
        file: "corpus/extracts/heidegger-bt-22-23.pdf"
        features: ["h_margins", "translator_footnotes"]

  # ... additional works ...
```

---

## Additional Texts Needed

### High Priority (Citation System Testing)

| Work | Author | System | Why Needed |
|------|--------|--------|------------|
| **Critique of Pure Reason** | Kant | A/B pagination | Test dual margin numbering |
| **Republic** | Plato | Stephanus | Test classical citation system |
| **Nicomachean Ethics** | Aristotle | Bekker | Test Bekker numbers |

### Medium Priority (Feature Coverage)

| Work | Author | Why Needed |
|------|--------|------------|
| **Phenomenology of Spirit** | Hegel | Paragraph numbers, different style |
| **Either/Or** | Kierkegaard | Complex structure |
| **Tractatus** | Wittgenstein | Numbered propositions |
| **Philosophical Investigations** | Wittgenstein | Section numbers |

### Low Priority (Edge Cases)

| Work | Author | Why Needed |
|------|--------|------------|
| French edition of Derrida | Derrida | Non-English OCR |
| German edition of Heidegger | Heidegger | Original pagination |
| Bilingual edition | Various | Parallel text layout |

---

## Migration Plan

1. **Create new directory structure**
2. **Rename files to ID slugs**
3. **Create registry.yaml**
4. **Update existing ground truth paths**
5. **Update tests to use registry**
6. **Remove old symlink**

---

## Open Questions

1. Should extracts be generated on-demand from full PDFs, or pre-extracted?
2. How do we handle multiple editions of same work?
3. Should registry include download URLs for acquisition?
