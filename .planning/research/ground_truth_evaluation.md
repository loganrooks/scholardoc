# Ground Truth Evaluation Systems for PDF Extraction Pipelines

**Project:** ScholarDoc
**Researched:** 2026-01-28
**Overall confidence:** MEDIUM-HIGH

---

## 1. Standard Approaches for Evaluating PDF Text Extraction Quality

### Character-Level Evaluation

**Character Error Rate (CER)** is the foundational metric. It measures the minimum edit distance (Levenshtein distance) between extracted text and ground truth, normalized by ground truth length:

```
CER = (Substitutions + Insertions + Deletions) / Total Ground Truth Characters
```

Key properties:
- CER can exceed 100% when insertions are numerous (e.g., GT="ABC", predicted="ABC12345" yields CER=166.7%)
- A CER of 0 means perfect extraction
- Industry target for good OCR: CER < 2%
- For scholarly PDFs with special characters (Greek, diacritics): CER < 5% is realistic

**Confidence: HIGH** -- CER is universally accepted. Sources: [TDS on CER/WER](https://towardsdatascience.com/evaluating-ocr-output-quality-with-character-error-rate-cer-and-word-error-rate-wer-853175297510/), [Docuclipper](https://www.docuclipper.com/blog/ocr-accuracy/)

### Word-Level Evaluation

**Word Error Rate (WER)** applies the same edit distance concept at the word level:

```
WER = (Word Substitutions + Word Insertions + Word Deletions) / Total Ground Truth Words
```

WER is always >= CER in absolute terms. It is more meaningful for downstream NLP tasks because a single character error corrupts an entire word. For ScholarDoc's use case (RAG pipelines, Anki generation), WER is arguably more important than CER because a misspelled philosophical term renders it unsearchable.

### Line-Level and Block-Level Evaluation

Less standardized but critical for layout-sensitive extraction:

- **Line matching accuracy**: Do extracted lines correspond 1:1 with physical lines? Important for footnote boundary detection.
- **Block segmentation F1**: Precision/recall of correctly identifying text blocks (body vs. footnote vs. header). This is where ScholarDoc's footnote detection lives.
- **Reading order accuracy**: Are blocks ordered correctly? The 2024 paper on [reading order independent metrics](https://arxiv.org/html/2404.18664v1) proposes ECER/EWER variants that eliminate sequentiality constraints -- relevant for multi-column philosophy texts.

### Structured Element Evaluation

For ScholarDoc specifically, element-level metrics matter most:

| Element | Metric | What It Measures |
|---------|--------|-----------------|
| Footnote detection | Precision/Recall/F1 | Are all footnotes found? Any false positives? |
| Marker-definition pairing | Pairing accuracy | Is marker matched to correct definition? |
| Citation extraction | Field-level accuracy | Author, year, title individually correct? |
| Text formatting | Tag F1 | Are bold/italic/sous-erasure correctly detected? |

**Recommendation for ScholarDoc:** Use a layered evaluation approach:
1. **Layer 1 (text):** CER and WER on raw extracted text per page
2. **Layer 2 (structure):** Block segmentation F1, footnote detection P/R/F1
3. **Layer 3 (semantics):** Marker-definition pairing accuracy, citation field accuracy, note classification accuracy

---

## 2. Existing GT Annotation Schemas for Scholarly PDFs

### GROBID Training Data

GROBID uses a cascade of CRF/deep learning models with 68 labels covering publication metadata, body structure, and references. Its training data uses TEI XML format with inline annotations. Key characteristics:

- **Schema**: TEI XML with rich semantic tags (title, author names decomposed to first/middle/last, affiliation components, detailed reference fields)
- **Granularity**: Token-level with sequence labeling
- **Strengths**: Excellent for bibliographic metadata, reference parsing
- **Weaknesses**: Focused on STEM papers; not designed for philosophy texts with complex footnote schemas, non-Latin scripts, or editorial apparatus

**Relevance to ScholarDoc:** LOW-MEDIUM. GROBID's reference parsing model is useful, but its training data schema does not cover translator/editor note classification, footnote marker corruption, or philosophical citation formats (Stephanus, Bekker numbers).

**Confidence: HIGH** -- Source: [GROBID documentation](https://grobid.readthedocs.io/en/latest/Principles/)

### PubLayNet and DocBank

Both are large-scale layout analysis datasets generated semi-automatically from structured source files:

- **PubLayNet** (2019): 300K+ pages from PubMed, 5 classes (text, title, list, table, figure), COCO-format bounding boxes
- **DocBank** (2020): 500K pages from arXiv, token-level annotations with 12 classes, tab-separated format with bounding box + font + label per token

These datasets enabled modern document layout detection models (Faster R-CNN, Mask R-CNN on documents). However, they are generated from LaTeX/XML source, meaning they only cover documents where structured source exists.

**Relevance to ScholarDoc:** LOW. These are layout detection datasets for training ML models, not evaluation frameworks. ScholarDoc's PDFs are scanned/digitized philosophy books without LaTeX sources.

### DocLayNet

IBM's DocLayNet (2022) is more diverse than PubLayNet:

- **Schema**: 11 class labels (Caption, Footnote, Formula, List-item, Page-footer, Page-header, Picture, Section-heading, Table, Text, Title)
- **Annotation**: Human-annotated bounding boxes in COCO format
- **Sources**: Finance, Science, Patents, Tenders, Law, Manuals -- more layout diversity
- **Size**: 80,863 pages

**Relevance to ScholarDoc:** MEDIUM. DocLayNet includes a "Footnote" class which is directly relevant. Its annotation format (COCO bounding boxes) could inform ScholarDoc's bbox annotation. However, it does not distinguish footnote types (author/translator/editor) or model marker-definition pairing.

**Confidence: HIGH** -- Source: [DocLayNet paper](https://arxiv.org/abs/2206.01062)

### S2ORC (Semantic Scholar Open Research Corpus)

S2ORC provides structured full text for 8.1M open-access PDFs:

- **Schema**: Sections, paragraphs with inline citation mentions linked to bibliography entries, figure/table references linked to captions
- **Processing**: Uses GROBID + Science Parse for PDF-to-JSON
- **Metadata**: Title, authors (first/middle/last/suffix), venue, journal, year

**Relevance to ScholarDoc:** MEDIUM. S2ORC's schema for inline citations with linked bibliography is a good model for ScholarDoc's citation extraction. The separation of metadata from parsed text (for incremental updates) is a smart architectural pattern to adopt. However, S2ORC does not model footnotes with the granularity ScholarDoc needs.

**Confidence: HIGH** -- Source: [S2ORC paper](https://aclanthology.org/2020.acl-main.447/)

### OmniDocBench (CVPR 2025)

The newest comprehensive benchmark:

- **Schema**: Markdown-to-markdown evaluation (model outputs markdown, compared against GT markdown)
- **Scope**: Text, tables, formulas, figures across diverse document types
- **Innovation**: Uses markdown as universal comparison format

**Relevance to ScholarDoc:** MEDIUM. The markdown-as-comparison-format idea aligns with ScholarDoc's vision of ScholarDocument as intermediate representation. Could inform how to evaluate final markdown output quality.

**Confidence: MEDIUM** -- Source: [OmniDocBench GitHub](https://github.com/opendatalab/OmniDocBench)

### ScholarDoc's Existing Schema (v3)

The project already has a sophisticated GT schema in `ground_truth/footnotes/schema.json` (v3.0.0) that is **more specialized than any public dataset** for its domain. It covers:

- Footnote marker corruption models (font-level symbol mapping)
- Note source classification (author/translator/editor) with confidence scoring
- Multiple classification methods (schema-based, content analysis, linguistic pattern, position-based, hybrid, manual)
- Bounding boxes for all elements
- ML features (spatial, font, schema, language, classification)
- Citation types including Stephanus and Bekker numbering
- Formatting including sous-erasure (crossed-out text in Derrida/Heidegger)

**Assessment:** This schema is already well beyond what public datasets offer for this domain. The gap is not in schema design but in **evaluation tooling** -- how to compute metrics against this schema programmatically.

---

## 3. The Bootstrap Problem

The bootstrap problem: you need ground truth to evaluate extraction quality, but creating ground truth is labor-intensive and often requires extraction tools as a starting point.

### How Mature Projects Solve This

**Approach 1: Source-Derived GT (PubLayNet, DocBank)**
Generate GT automatically from structured source (LaTeX, XML). This is the most scalable approach but only works when source exists. Not applicable to ScholarDoc's scanned philosophy PDFs.

**Approach 2: Model-Assisted Annotation (GROBID, most production systems)**
1. Run extraction pipeline on documents
2. Human annotators correct the output
3. Corrected output becomes GT
4. Use GT to evaluate/improve pipeline
5. Iterate

This is the standard approach and what ScholarDoc should use. The existing `generate_draft.py` script and Streamlit annotation UI in the implementation plan already follow this pattern.

**Approach 3: Stratified Sampling (Explosion/Prodigy)**
Rather than annotating entire documents, strategically sample:
- Select pages that represent different difficulty levels
- Annotate small but representative sets
- Use statistical methods to estimate corpus-wide quality

Rule of thumb from Explosion: 10 samples per significant figure of precision you want to report.

**Approach 4: Regression Testing (ScholarDoc's existing approach)**
The project already has `ground_truth/ocr_quality/` with samples and classified batches across multiple texts (Heidegger, Derrida, Kant, Lenin). This is a good start -- these can serve as regression tests even before a formal evaluation library exists.

### Recommendation for ScholarDoc

Use a **three-stage bootstrap**:

1. **Stage 1 (Current):** Continue building GT from the existing OCR quality samples and classified batches. These are already partially annotated. Convert the best-quality ones to the full YAML schema.

2. **Stage 2 (Evaluation Library):** Build the evaluation library (already planned in IMPLEMENTATION_PLAN.md). Run it against Stage 1 GT to get baseline metrics. This immediately tells you where the pipeline is weakest.

3. **Stage 3 (Targeted Annotation):** Use Stage 2 results to identify which document types/features need more GT. Annotate specifically where evaluation shows low confidence or high error rates. This is the "active learning" approach to GT creation -- annotate where it matters most.

---

## 4. Standard Evaluation Metrics

### Text Quality Metrics

| Metric | Formula | Use Case | Target |
|--------|---------|----------|--------|
| **CER** | edit_distance(pred, gt) / len(gt) | Raw text quality | < 2% (clean PDF), < 5% (scanned) |
| **WER** | word_edit_distance(pred, gt) / word_count(gt) | Word-level quality | < 5% (clean), < 10% (scanned) |
| **Normalized Edit Distance (NED)** | 1 - edit_distance / max(len(pred), len(gt)) | Similarity (0-1 scale) | > 0.95 |
| **BLEU** | n-gram precision with brevity penalty | Translation-style comparison | Context-dependent |

**Recommendation:** Use CER and WER as primary text metrics. NED is useful for element-level similarity scoring in the matching algorithm. Skip BLEU -- it is designed for machine translation and adds complexity without insight for extraction evaluation.

### Structure Metrics

| Metric | What It Measures | Calculation |
|--------|-----------------|-------------|
| **Detection Precision** | Of elements found, how many are real? | TP / (TP + FP) |
| **Detection Recall** | Of real elements, how many are found? | TP / (TP + FN) |
| **Detection F1** | Harmonic mean of P and R | 2PR / (P + R) |
| **Layout IoU** | Bounding box overlap accuracy | intersection_area / union_area |
| **Pairing Accuracy** | Marker-definition correctly linked? | correct_pairs / total_pairs |

### Domain-Specific Metrics for ScholarDoc

| Metric | What It Measures | Why It Matters |
|--------|-----------------|---------------|
| **Footnote Detection F1** | All footnotes found, no false positives | Core pipeline correctness |
| **Marker Corruption Recovery Rate** | How often corrupted symbols (e.g., "t" for dagger) are correctly recovered | Critical for philosophy texts with symbol footnotes |
| **Note Classification Accuracy** | Author/translator/editor correctly identified | Enables downstream filtering |
| **Foreign Term CER** | CER specifically on Greek/German/Latin terms | These are the hardest tokens and most valuable for scholars |
| **Cross-Page Continuity** | Footnotes spanning pages correctly merged | Common in dense philosophy texts |

### Metric Hierarchy

For ScholarDoc, prioritize metrics in this order:

1. **Footnote Detection F1** -- if you miss footnotes, nothing else matters
2. **Text CER/WER within detected regions** -- extraction quality of found elements
3. **Marker-Definition Pairing Accuracy** -- structural correctness
4. **Note Classification Accuracy** -- semantic layer
5. **Foreign Term CER** -- domain-specific quality indicator

---

## 5. Modular/Extensible GT Schema Design

### The Challenge

ScholarDoc needs a GT system that starts with extraction evaluation but extends to:
- Semantic annotation (concept tagging, argument structure)
- Cross-document relations (intertextual references, philosophical lineage)
- Corpus-level features (term frequency across works, citation networks)

### Patterns from Existing Systems

**Pattern 1: Layered Annotation (S2ORC model)**
Separate annotation layers that can be added independently:
```
Layer 0: Raw text (page-level character sequences)
Layer 1: Layout (bounding boxes, block types)
Layer 2: Structure (footnotes, citations, sections)
Layer 3: Semantics (note classification, concept tags)
Layer 4: Relations (cross-references, citation links)
Layer 5: Corpus (inter-document links, term networks)
```

Each layer references elements from lower layers by ID. Layers can be added incrementally without modifying existing annotations.

**Pattern 2: Standoff Annotation (NLP standard)**
Annotations stored separately from base text, referencing by character offsets:
```yaml
base_text: "The categorical imperative..."
annotations:
  - id: ann_001
    type: concept
    start: 4
    end: 27
    label: "categorical_imperative"
    layer: "semantic"
```

This avoids modifying base data when adding annotation layers. It is the standard in computational linguistics (BRAT, WebAnno, INCEpTION all use standoff).

**Pattern 3: Schema Versioning (ScholarDoc's existing approach)**
The v3 schema already includes versioning with changelog. This is good. Extend it with:
- Layer identifiers so evaluation can target specific layers
- Optional fields for higher layers (don't break existing GT when adding semantic annotations)

### Recommended Architecture for ScholarDoc

```
ground_truth/
  documents/
    heidegger_being_and_time/
      manifest.yaml          # Document metadata, layer inventory
      text_layer.yaml        # Layer 0-1: raw text + layout
      structure_layer.yaml   # Layer 2: footnotes, citations, sections
      semantic_layer.yaml    # Layer 3: note classification, concepts
      relations_layer.yaml   # Layer 4: cross-references (future)
  schemas/
    text_v1.schema.json
    structure_v1.schema.json
    semantic_v1.schema.json
    relations_v1.schema.json
  evaluation/
    configs/
      text_only.yaml         # Evaluate layers 0-1 only
      full_structure.yaml    # Evaluate layers 0-2
      with_semantics.yaml    # Evaluate layers 0-3
```

**Key design decisions:**

1. **One file per layer per document.** This allows independent annotation of different layers by different people, incremental addition of layers, and layer-specific evaluation.

2. **Manifest as registry.** Each document has a manifest listing which layers exist, their schema versions, annotation status, and annotator.

3. **Evaluation configs select layers.** The evaluation library loads a config that specifies which layers to evaluate and which metrics to compute per layer. This makes the system extensible without code changes.

4. **IDs link across layers.** Structure layer elements (footnotes, citations) have stable IDs that semantic layer annotations reference. This is the standoff annotation principle.

### Concrete Schema Extension Example

Starting from the existing v3 schema, here is how to extend for semantic annotation:

```yaml
# semantic_layer.yaml for Heidegger's Being and Time
schema_version: "semantic_v1"
document_id: "heidegger_being_and_time"
depends_on:
  structure_layer: "v1"

annotations:
  - id: "sem_001"
    references: "fn_003"  # ID from structure_layer
    layer: "semantic"
    type: "concept_tag"
    value: "Dasein"
    ontology: "heidegger_terminology"

  - id: "sem_002"
    references: "fn_007"
    layer: "semantic"
    type: "argument_role"
    value: "objection"
    target_claim: "sem_015"

  - id: "sem_003"
    references: "cite_012"
    layer: "relation"
    type: "intertextual_reference"
    target_document: "husserl_logical_investigations"
    relationship: "critique_of"
```

---

## 6. Tool and Library Recommendations

### Evaluation Computation

| Library | Purpose | Why |
|---------|---------|-----|
| **jiwer** | CER/WER computation | Purpose-built, uses RapidFuzz internally for speed, Apache 2.0 licensed |
| **rapidfuzz** | String similarity, edit distance | Fastest Python option (C++ backend), 40% faster than alternatives, MIT licensed |
| **scikit-learn** | Precision/recall/F1 | Standard, well-tested, already likely in dependency tree |

**Recommendation:** Use **jiwer** for CER/WER (it wraps RapidFuzz). Use **rapidfuzz** directly for element-level similarity scoring in the matching algorithm. Use scikit-learn's `precision_recall_fscore_support` for detection metrics.

Sources: [jiwer GitHub](https://github.com/jitsi/jiwer), [RapidFuzz GitHub](https://github.com/rapidfuzz/RapidFuzz)

### Annotation Tools

| Tool | Purpose | Fit for ScholarDoc |
|------|---------|-------------------|
| **Label Studio** | General annotation platform, supports PDF | Overkill; ScholarDoc already has a custom Streamlit UI planned |
| **BRAT** | Standoff text annotation | Good model for schema design but dated UI |
| **Prodigy** | Active-learning annotation | Commercial; good ideas but not needed |
| **Custom Streamlit UI** | Already planned in IMPLEMENTATION_PLAN.md | Best fit -- domain-specific, integrates with existing schema |

**Recommendation:** Stick with the planned Streamlit annotation UI. It integrates directly with the existing schema and can be extended for semantic annotation layers. Adopting Label Studio or similar would require schema translation and lose the domain-specific features (corruption model, note classification).

### Evaluation Reporting

| Tool | Purpose |
|------|---------|
| **tabulate** | CLI table output (already in implementation plan) |
| **matplotlib/seaborn** | Confusion matrices, per-document score distributions |
| **JSON output** | Machine-readable for CI/regression tracking |

---

## 7. Synthesis and Recommendations

### What ScholarDoc Should Build

The existing implementation plan (IMPLEMENTATION_PLAN.md) is well-designed. The evaluation library architecture (normalize -> match -> metrics -> reports) is the right abstraction. Key additions to consider:

1. **Layer-aware evaluation.** The matching and metrics modules should accept a layer parameter so evaluation can target text-only, structure, or semantics independently.

2. **Per-element-type metrics.** Don't just compute aggregate F1. Compute it per element type (footnotes, citations, formatting, xmarks) because they have different difficulty profiles.

3. **Foreign term CER as a first-class metric.** Philosophy texts live and die by correct rendering of Greek/German/Latin. Track this separately.

4. **Regression tracking.** Store evaluation results in a structured format (JSON) with timestamps so you can track pipeline quality over time as code changes.

5. **Confidence-weighted evaluation.** The v3 schema already has classification_confidence. Use this in evaluation -- weight high-confidence GT annotations more heavily, or report metrics separately for high/low confidence GT.

### What NOT to Build

- **Do not adopt COCO format or PubLayNet-style schemas.** These are for training layout detection models. ScholarDoc needs evaluation of extraction quality, not training data for object detection.
- **Do not implement BLEU.** It adds complexity for marginal insight in this domain.
- **Do not build a general annotation platform.** The Streamlit UI tailored to the domain is the right call.

### Priority Order

1. **jiwer + rapidfuzz integration** for CER/WER computation
2. **Element matching with configurable thresholds** (the matching.py in the plan)
3. **Per-type precision/recall/F1** (the metrics.py in the plan)
4. **Layer separation in GT files** (extend current schema)
5. **Regression tracking** (store results over time)
6. **Foreign term CER** (domain-specific metric)
7. **Semantic layer schema** (future, when extraction is stable)

---

## Sources

- [Evaluating OCR with CER and WER (Towards Data Science)](https://towardsdatascience.com/evaluating-ocr-output-quality-with-character-error-rate-cer-and-word-error-rate-wer-853175297510/)
- [OCR Accuracy Guide (Docuclipper)](https://www.docuclipper.com/blog/ocr-accuracy/)
- [Reading Order Independent Metrics (arXiv 2024)](https://arxiv.org/html/2404.18664v1)
- [KIEval: Evaluation Metric for Document KIE (arXiv 2025)](https://arxiv.org/pdf/2503.05488v2)
- [GROBID Documentation](https://grobid.readthedocs.io/en/latest/Principles/)
- [DocLayNet (arXiv 2022)](https://arxiv.org/abs/2206.01062)
- [S2ORC Paper (ACL 2020)](https://aclanthology.org/2020.acl-main.447/)
- [OmniDocBench (CVPR 2025)](https://github.com/opendatalab/OmniDocBench)
- [Benchmark of PDF Extraction Tools (Meuschke et al. 2023)](https://gipplab.uni-goettingen.de/wp-content/papercite-data/pdf/meuschke2023.pdf)
- [jiwer Library](https://github.com/jitsi/jiwer)
- [RapidFuzz Library](https://github.com/rapidfuzz/RapidFuzz)
- [Explosion Blog: PDFs to Structured Data](https://explosion.ai/blog/pdfs-nlp-structured-data)
- [NVIDIA: PDF Data Extraction for IR](https://developer.nvidia.com/blog/approaches-to-pdf-data-extraction-for-information-retrieval/)
