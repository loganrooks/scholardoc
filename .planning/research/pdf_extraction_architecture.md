# PDF Extraction Library Architectures and Best Practices

**Researched:** 2026-01-28
**Overall confidence:** MEDIUM-HIGH
**Relevance:** Direct — informs ScholarDoc IR design, serialization, extensibility

---

## 1. How Modern PDF Extraction Libraries Structure Their Pipelines

### The Universal Pattern: Reader -> IR -> Writer

Every serious extraction library converges on the same three-stage pipeline, though they name the stages differently:

| Library | Stage 1 (Input) | Stage 2 (Transform/IR) | Stage 3 (Output) |
|---------|----------------|----------------------|------------------|
| GROBID | pdfalto (PDF->ALTO XML) | Cascade of CRF/DL sequence labelers | TEI XML assembly |
| Docling | PDF pipeline (per-page AI models) | DoclingDocument (Pydantic) | Markdown, HTML, JSON, DocTags |
| Marker | pdftext/pypdfium2 + Surya models | Internal document model | Markdown, JSON, HTML |
| Nougat | Swin Transformer encoder (image-only) | Autoregressive decoder tokens | Markdown (direct) |
| Unstructured | Partitioners (pdfminer or Detectron2) | Element list (Title, NarrativeText, Table...) | JSON, Markdown, HTML, Arrow |
| pypdf/PyMuPDF | Direct PDF parsing | Page/block objects | Text, dict, HTML |

**Key insight for ScholarDoc:** The RawDocument -> NormalizedDocument -> Writer pattern in SPEC.md is exactly right. This is the consensus architecture. The only question is how rich the IR should be.

### Pipeline Orchestration Patterns

**Sequential with enrichment (GROBID, Docling, Marker):** Each stage adds information. GROBID runs 68 labels across cascading models. Docling runs layout detection, table extraction, OCR independently per page, then aggregates. Marker runs Surya models sequentially, each builder adding to the document structure.

**End-to-end neural (Nougat, Granite-Docling VLM):** Skip the pipeline entirely. Feed page images to a transformer, get markup out. Simpler architecture but less controllable and harder to extend.

**Partitioning with strategies (Unstructured):** Multiple strategies (FAST, HI_RES, VLM) that trade speed for accuracy. The consumer picks the strategy.

**Recommendation for ScholarDoc:** Stay with the sequential enrichment pattern. It is the most extensible, debuggable, and appropriate for a library (vs. an application). ScholarDoc's cascading extractor already follows this pattern. The Normalizer chain is the right abstraction for adding new extraction capabilities.

### GROBID's Cascade Model (Relevant Detail)

GROBID's architecture is particularly instructive because it handles scholarly documents specifically. It uses a cascade of sequence labeling models:
1. First pass: segment header, body, references
2. Second pass: within header, label title, authors, affiliations, abstract
3. Third pass: within body, label sections, paragraphs, figures, citations
4. Each model is trained independently on small, high-quality labeled data

This cascade approach maps well to ScholarDoc's normalizer chain. Each normalizer can be thought of as a labeling pass that enriches the document.

---

## 2. Intermediate Representations: How Rich and How Extensible

### Docling's DoclingDocument (The Gold Standard for IR Design)

Docling's IR is the most relevant reference for ScholarDoc. Key design decisions:

- **Pydantic model** — same technology ScholarDoc already uses
- **Element collections** — content organized as typed lists (texts, tables, pictures, etc.)
- **Reference system** — JSON Pointer-like refs (`#/texts/0`) encode hierarchy and relationships between elements
- **Parent/children relationships** — each element has `self_ref`, `parent` (RefItem), and `children` (RefItem list)
- **Lossless JSON serialization** — the Pydantic model round-trips perfectly to/from JSON
- **Extensible serialization API** — different serializers can be plugged in for different consumers

**Confidence: HIGH** (verified via official Docling documentation and GitHub)

### GROBID's TEI XML

GROBID outputs TEI (Text Encoding Initiative) XML, which is extremely rich:
- 68 distinct labels for fine-grained structure
- Bounding box coordinates synchronized with sequence labels
- Full bibliographic metadata
- Cross-references between citations and reference list

TEI XML is verbose but lossless. It's the academic standard for document markup.

### Unstructured's Element Model

Unstructured uses a flat list of typed elements (Title, NarrativeText, Table, ListItem, PageBreak) with metadata:
- Coordinates (bounding boxes)
- Page numbers
- Language detection
- SHA hashes for deduplication
- Parent-child relationships via `parent_id`

Simpler than Docling but less expressive. Works well for RAG chunking where hierarchy matters less.

### Nougat's Approach: No IR

Nougat has no intermediate representation. It goes directly from page image to Markdown. This makes it fast and simple but:
- No programmatic access to document structure
- No metadata preservation
- No ability to serialize/query the extracted structure
- Useless as a library IR

### Annotation Layers / Extensibility in IRs

**Docling:** The DoclingDocument model supports adding custom metadata to elements via Pydantic model extension. The reference system allows arbitrary cross-references. However, it does not have a formal "annotation layer" concept — you extend by subclassing or adding fields.

**GROBID:** TEI XML supports custom attributes and namespaces, making it naturally extensible. You can add domain-specific annotations without breaking the schema.

**Unstructured:** Elements have a generic `metadata` dict that can carry arbitrary key-value pairs. Simple but untyped.

**Recommendation for ScholarDoc:** The current `attributes: dict[str, Any]` on ContentElement is the Unstructured approach — simple but untyped. Consider moving toward Docling's approach:

1. Use Pydantic models (already planned) with typed fields for known attributes
2. Keep an `extra: dict[str, Any]` for truly dynamic metadata
3. Add a reference/pointer system for cross-element relationships (e.g., footnote->endnote, citation->bibliography entry)
4. Consider an annotation layer pattern where consumers can attach typed annotations without modifying the core model

```python
# Annotation layer concept
class Annotation(BaseModel):
    """Consumer-attached metadata on a content element."""
    source: str  # "cryptofcogito", "anki-generator", etc.
    annotation_type: str
    data: dict[str, Any]

class ContentElement(BaseModel):
    # ... core fields ...
    annotations: list[Annotation] = []  # extensible without schema changes
```

This lets CryptOfCogito attach philosophy-specific metadata (Stephanus numbers, Bekker numbers) without ScholarDoc needing to know about those concepts.

---

## 3. Serialization: The Extraction -> Storage -> Consumption Pattern

### What the Ecosystem Uses

| Library | Primary Serialization | Secondary | Notes |
|---------|----------------------|-----------|-------|
| Docling | JSON (lossless Pydantic) | Markdown, HTML, DocTags | JSON is the canonical format |
| GROBID | TEI XML | BibTeX (references only) | XML is the canonical format |
| Unstructured | JSON | Markdown, HTML, Arrow/Parquet | JSON elements with metadata |
| Marker | Markdown | JSON | Markdown-first |
| Nougat | Markdown | None | Markdown-only |

### JSON as Canonical Format (Consensus)

The clear consensus: **JSON is the canonical lossless serialization format for modern extraction IRs.** Docling, Unstructured, and Marker all use JSON as their lossless format, with Markdown/HTML as lossy presentation formats.

Why JSON wins:
- Pydantic models serialize/deserialize natively
- Human-readable and debuggable
- Schema-validatable (JSON Schema from Pydantic)
- Language-agnostic consumption
- Git-diffable for ground truth datasets

### SQLite as a Query Layer (Not a Serialization Format)

No major extraction library uses SQLite as a primary serialization format. However, SQLite is used downstream:
- **LlamaIndex/LangChain** store chunks in SQLite-backed vector stores
- **Zotero** stores bibliographic metadata in SQLite
- **Research corpus tools** use SQLite for querying across documents

**Recommendation:** ScholarDoc's plan of JSON + SQLite is correct, but clarify the roles:
- **JSON**: Canonical serialization of ScholarDocument. One `.json` file per document. Lossless round-trip. This is what the library produces.
- **SQLite**: A corpus-level query layer that a consumer (like CryptOfCogito) builds by importing multiple ScholarDocuments. This is NOT ScholarDoc's responsibility — it belongs in the consuming application.

ScholarDoc should provide:
1. `document.to_json()` / `ScholarDocument.from_json()` — always
2. `document.to_markdown()` — lossy presentation format
3. Optional: `document.to_dict()` for programmatic access without serialization

ScholarDoc should NOT provide:
- SQLite storage (that's CryptOfCogito's job)
- Vector embeddings (that's a RAG pipeline's job)
- Chunking strategies (that's an LLM pipeline's job)

### Docling's Serialization API Pattern

Docling separates serialization into a pluggable API:

```
DoclingDocument -> Serializer -> Output Format
                  MarkdownSerializer -> str
                  HTMLSerializer -> str
                  JSONSerializer -> str (lossless)
                  DocTagsSerializer -> str
```

Each serializer can be configured (e.g., include/exclude images, table format). This is clean and extensible.

**Recommendation:** ScholarDoc's Writer pattern in SPEC.md already follows this. Keep it. The key addition from Docling's approach: make serializers configurable (what to include/exclude, formatting options) rather than one-size-fits-all.

---

## 4. Plugin/Extension Architectures

### Approaches in the Ecosystem

**Marker: Module path overrides.** You can override default processors by providing module paths. Simple but limited — you replace existing processors, you don't add new ones alongside them.

**Unstructured: Connector architecture.** Source connectors (40+ input sources) and destination connectors are pluggable. The core partitioning is less pluggable — you pick a strategy, not extend one.

**Docling: Pipeline composition.** Docling pipelines compose AI models. You can swap models but the pipeline structure is fixed.

**GROBID: Model training.** Extension happens by training new models for new label types. The cascade structure is fixed in code.

### What Works for a Library (vs. an Application)

For ScholarDoc as a library consumed by other projects, the right extensibility points are:

1. **Reader plugins** (already in SPEC.md): Register new input format handlers. Protocol/ABC-based.
2. **Normalizer chain** (already in SPEC.md): Add/remove/reorder normalizers. This is the primary extension point.
3. **Writer plugins** (already in SPEC.md): Register new output format handlers.

What to add:

4. **Extractor plugins**: Within a Reader, allow pluggable extraction strategies. E.g., a PDFReader could delegate heading detection to different extractors (font-based, ML-based, rule-based) selected by configuration.
5. **Post-processing hooks**: Allow consumers to register callbacks that run after normalization but before writing. This is where CryptOfCogito would add Stephanus number detection.

**Recommended pattern:**

```python
# Protocol-based extensibility
class Normalizer(Protocol):
    def normalize(self, doc: RawDocument, config: Config) -> RawDocument: ...

class Writer(Protocol):
    def write(self, doc: NormalizedDocument, config: Config) -> str: ...

# Registration
pipeline = Pipeline(
    reader=PDFReader(),
    normalizers=[
        StructureNormalizer(),
        PageMapper(),
        OCRQualityNormalizer(),
        # Consumer adds their own:
        StephanusDetector(),  # CryptOfCogito-specific
    ],
    writer=MarkdownWriter(),
)
```

This is simple, composable, and doesn't require a plugin registry or dynamic loading. The consumer constructs the pipeline they want.

---

## 5. Multi-Format Output from a Single IR

### The Pattern

Every library that supports multiple output formats follows the same pattern:

```
Extraction -> Rich IR -> Lossy serializers (Markdown, HTML)
                      -> Lossless serializer (JSON, XML)
```

The IR is always richer than any single output format. Markdown can't represent bounding boxes. JSON can't represent visual layout as naturally as HTML. The IR holds everything; serializers select and format subsets.

### Docling's Approach (Best in Class)

Docling's DoclingDocument holds:
- Text content with hierarchy
- Table structures (cell-level)
- Image references with captions
- Mathematical formulas
- Reading order
- Bounding boxes and coordinates
- Font/style information

Then serializers extract what they need:
- Markdown: text + tables (as pipe tables) + headings
- HTML: text + tables + basic styling
- JSON: everything (lossless)
- DocTags: structural tags for ML training

### Recommendation for ScholarDoc

ScholarDoc's NormalizedDocument should be **richer than the richest planned output format**. Currently, the model is roughly at parity with Markdown output. To support JSON and future formats well, consider enriching:

| Currently in NormalizedDocument | Should Add |
|-------------------------------|------------|
| Element type, text, level | Bounding boxes (from RawDocument) |
| Page index/label | Font information (preserved from extraction) |
| Generic attributes dict | Confidence scores (from heading detection, OCR) |
| Document structure (sections) | Cross-references (footnotes, citations) |
| Basic metadata | Quality assessment (from OCR pipeline) |

The principle: **preserve everything during extraction, discard during serialization.** A Markdown writer ignores bounding boxes. A JSON writer preserves them. The IR should not be the bottleneck.

---

## 6. Library vs. Application Boundaries

### What Stays in the Extraction Library

Based on ecosystem consensus, an extraction library should provide:

| Responsibility | In Library | Evidence |
|---------------|-----------|---------|
| PDF parsing and text extraction | Yes | All libraries |
| Layout detection (headings, paragraphs) | Yes | All libraries |
| Table extraction | Yes | Docling, GROBID, Unstructured |
| OCR and quality assessment | Yes | All libraries |
| Metadata extraction (title, authors) | Yes | All libraries |
| Intermediate representation | Yes | Docling, Unstructured |
| Lossless serialization (JSON) | Yes | Docling, Unstructured |
| Lossy serialization (Markdown) | Yes | All libraries |
| Page/section structure | Yes | All libraries |

### What Consumers Build

| Responsibility | In Consumer | Why |
|---------------|------------|-----|
| Corpus management (multi-doc) | Consumer | Domain-specific (philosophy vs. medical vs. legal) |
| SQLite/database storage | Consumer | Schema depends on use case |
| Vector embeddings | Consumer | Model choice is consumer's decision |
| Chunking strategies | Consumer | Chunk size/overlap depends on downstream LLM |
| Domain-specific annotations | Consumer | Stephanus numbers are philosophy-specific |
| Search/retrieval | Consumer | Query patterns are application-specific |
| Citation management | Consumer | Format requirements vary |
| Anki card generation | Consumer | Presentation logic |

### The Gray Zone

Some features sit at the boundary:

| Feature | Recommendation | Rationale |
|---------|---------------|-----------|
| Chunking | Library provides chunk-friendly structure; consumer chunks | Docling approach: IR preserves boundaries, consumer decides chunk size |
| Citation parsing | Library extracts raw citations; consumer resolves them | GROBID does both, but ScholarDoc is narrower scope |
| Cross-document references | Consumer only | Requires corpus-level knowledge |
| Footnote/endnote linking | Library (within-document linking) | Structural relationship, not domain-specific |
| Reading order detection | Library | Fundamental to correct extraction |

### Recommendation for ScholarDoc

ScholarDoc's current boundary is approximately correct. Specific adjustments:

1. **Keep in ScholarDoc:** JSON serialization, Markdown serialization, within-document cross-references (footnotes), quality assessment, page label mapping
2. **Move out of ScholarDoc:** Any SQLite logic, any corpus-level features, any domain-specific annotation (Stephanus, Bekker)
3. **Provide hooks for:** Consumer-specific normalizers (via pipeline composition), consumer-specific annotations (via annotation layer on IR), consumer-specific writers (via Writer protocol)

---

## Summary of Recommendations for ScholarDoc

### IR Design
- Enrich NormalizedDocument to preserve bounding boxes, font info, and confidence scores
- Add a reference/pointer system for cross-element relationships (follow Docling's `RefItem` pattern)
- Add an annotation layer for consumer-extensible metadata
- Use Pydantic models throughout (consistent with Docling, already planned)

### Serialization
- JSON as canonical lossless format (Pydantic `.model_dump_json()` / `.model_validate_json()`)
- Markdown as lossy presentation format
- Do NOT build SQLite into ScholarDoc — that's CryptOfCogito's responsibility
- Make serializers configurable (include/exclude options)

### Extensibility
- Protocol-based Reader/Normalizer/Writer interfaces
- Pipeline composition (consumer constructs their pipeline)
- No plugin registry or dynamic loading needed at this scale
- Post-processing hooks for consumer-specific enrichment

### Library Boundary
- ScholarDoc extracts and serializes single documents
- Consumers handle corpus management, storage, search, and domain annotations
- Provide rich IR so consumers don't need to re-extract

---

## Sources

- [GROBID Documentation - How GROBID Works](https://grobid.readthedocs.io/en/latest/Principles/)
- [GROBID GitHub](https://github.com/kermitt2/grobid)
- [GROBID DeepWiki - Document Processing Pipeline](https://deepwiki.com/kermitt2/grobid/4-using-grobid)
- [Docling Documentation - DoclingDocument](https://docling-project.github.io/docling/concepts/docling_document/)
- [Docling Core GitHub](https://github.com/docling-project/docling-core)
- [Docling Arxiv Paper](https://arxiv.org/html/2501.17887v1)
- [DoclingDocument DeepWiki](https://deepwiki.com/docling-project/docling-core/2.1-doclingdocument)
- [Marker GitHub](https://github.com/datalab-to/marker)
- [Marker DeepWiki - Python API](https://deepwiki.com/datalab-to/marker/3.2-python-api)
- [Unstructured Documentation](https://docs.unstructured.io/open-source/introduction/overview)
- [Unstructured GitHub](https://github.com/Unstructured-IO/unstructured)
- [Nougat - Meta AI](https://facebookresearch.github.io/nougat/)
- [IBM Granite-Docling Announcement](https://www.ibm.com/new/announcements/granite-docling-end-to-end-document-conversion)
