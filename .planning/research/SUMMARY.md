# Project Research Summary

**Project:** ScholarDoc
**Domain:** Scholarly PDF extraction library with ground truth evaluation infrastructure
**Researched:** 2026-01-28
**Confidence:** MEDIUM-HIGH

## Executive Summary

ScholarDoc is a mature extraction library (395 tests, 87% coverage) that needs to close three gaps: verified ground truth for evaluation, serialization (Writers module), and a clear architectural boundary with its ecosystem (CryptOfCogito, scholarly_annotate). Research confirms the existing pipeline architecture (Reader -> IR -> Writer) matches the consensus pattern used by Docling, GROBID, Marker, and Unstructured. The project's extraction pipeline is solid; the bottleneck is the absence of verified ground truth documents and the empty Writers module -- without these, quality cannot be measured and output cannot be consumed.

The recommended approach is to prioritize ground truth creation and evaluation infrastructure first, then enrich the intermediate representation and build serializers, and finally restructure the repository into a uv workspace monorepo. This ordering is deliberate: you cannot improve extraction without measurement, you cannot serialize without a rich enough IR, and you should not restructure the repo until the library's boundaries are clear from use.

Key risks: (1) the chicken-and-egg problem between GT annotation and extraction quality -- solved by using ScholarDoc's own extraction as draft GT with human correction; (2) over-engineering the GT schema before knowing what evaluation actually reveals -- solved by the layered annotation architecture where layers are added incrementally; (3) OCR false positive rate of 23.4% on philosophical terms -- requires foreign-term-aware evaluation metrics to track improvement.

## Key Findings

### Pipeline Architecture (from pdf_extraction_architecture.md)

Every serious extraction library converges on **Reader -> IR -> Writer**. ScholarDoc's existing architecture matches this consensus. Key enhancements needed:

- **Enrich NormalizedDocument**: Preserve bounding boxes, font info, confidence scores from extraction. Current IR is at parity with Markdown output -- it should be richer than any single output format.
- **Add cross-element references**: Follow Docling's RefItem pattern for footnote-to-marker, citation-to-bibliography links.
- **Add annotation layer**: A typed `Annotation` model on ContentElement for consumer-extensible metadata (Stephanus numbers, Bekker numbers) without modifying the core schema.
- **JSON as canonical serialization**: Pydantic `.model_dump_json()` / `.model_validate_json()`. Markdown as lossy presentation. No SQLite in the library -- that belongs to consumers.
- **Protocol-based extensibility**: Reader/Normalizer/Writer as Protocols. Pipeline composition by the consumer. No plugin registry needed.

### Ground Truth Evaluation (from ground_truth_evaluation.md)

The existing v3 GT schema is more specialized than any public dataset for this domain. The gap is evaluation tooling, not schema design.

- **Layered evaluation**: Layer 1 (text: CER/WER), Layer 2 (structure: footnote detection F1), Layer 3 (semantics: note classification accuracy).
- **Priority metrics**: Footnote Detection F1 > Text CER/WER > Marker-Definition Pairing > Note Classification > Foreign Term CER.
- **Three-stage bootstrap**: (1) Convert existing OCR quality samples to full schema, (2) Run evaluation library for baseline metrics, (3) Use results to target annotation where error rates are highest.
- **Tools**: jiwer for CER/WER, rapidfuzz for element-level similarity, scikit-learn for P/R/F1. Stick with custom Streamlit annotation UI.

### Experimentation Framework (from experimentation_frameworks.md)

ScholarDoc is not an ML training project -- heavyweight trackers (MLflow, W&B) are wrong. Extend the existing ground truth framework instead.

- **CI regression gate**: Run evaluation on every commit, fail on regression. Highest-value, lowest-effort addition.
- **Structured experiment protocol**: YAML spec with hypothesis, parameter changes, success criteria. JSONL log for tracking runs.
- **Stratified metrics**: Track per-element-type metrics over time, not just aggregate F1.
- **Dev/validation split**: 70/30 split of GT corpus to prevent overfitting to annotated pages.
- **Agent protocols**: Hypothesis -> Execute -> Evaluate -> Decide workflow for Claude Code agents. Novel but well-structured.

### Repository Structure (from repo_structure.md)

**Monorepo with uv workspaces** is the clear recommendation for ScholarDoc + CryptOfCogito + scholarly_annotate.

- **uv workspaces**: Single lockfile, cross-package dependencies, independent publishing. Zero migration cost since ScholarDoc already uses uv.
- **Migration**: git subtree merge of CryptOfCogito into packages/ subdirectory, preserving history.
- **Shared GT package** (`scholarly_testdata`): Pydantic schemas for GT format, pytest fixtures, sample PDFs via Git LFS.
- **Defer Pants/Bazel**: Not needed at ~400 tests. Revisit at 1000+ tests.

## Cross-Cutting Themes

1. **Layered architecture everywhere**: The IR has layers (raw -> normalized -> annotated). GT has layers (text -> structure -> semantics). Evaluation has layers (CER -> F1 -> domain metrics). This consistency is a strength -- lean into it.

2. **JSON as the universal interchange**: Canonical IR serialization, GT files, experiment metrics, baseline tracking -- all JSON/YAML. No databases in the library layer.

3. **Existing work is better than researchers expected**: The v3 GT schema, the evaluation library architecture, the cascading extractor -- all align with industry best practices. The gaps are in wiring and verification, not design.

4. **Tensions identified**:
   - GT schema research suggests YAML layered files per document, but the existing schema is a single JSON. Migration needed.
   - Repo structure research assumes monorepo migration, but PROJECT.md lists it as a pending decision. Recommend deciding before roadmap execution.
   - Experimentation research proposes agent protocols that depend on CI infrastructure that does not exist yet. CI gate must come first.

## Implications for Roadmap

### Phase 1: Ground Truth Bootstrap and Evaluation Pipeline
**Rationale:** Cannot improve what you cannot measure. Zero verified GT documents exist despite a built evaluation library.
**Delivers:** 10-20 verified GT pages across 3+ texts, automated evaluation pipeline, baseline metrics, CI regression gate.
**Addresses:** Verified GT corpus, automated evaluation pipeline, CI integration.
**Avoids:** Over-annotating before knowing where errors concentrate (use three-stage bootstrap).

### Phase 2: IR Enrichment and Writers Module
**Rationale:** Depends on Phase 1 metrics to know what the IR is missing. Writers module is empty -- ScholarDoc produces no persistent output.
**Delivers:** Enriched NormalizedDocument (bboxes, fonts, confidence, cross-references), JSON serializer (lossless), Markdown serializer (lossy), annotation layer on ContentElement.
**Addresses:** ScholarDocument representation review, Writers module, rich IR for consumers.
**Avoids:** Building SQLite into the library (consumer responsibility per architecture research).

### Phase 3: Experimentation Framework
**Rationale:** With GT and evaluation from Phase 1 and serialization from Phase 2, systematic experimentation becomes possible.
**Delivers:** Experiment spec YAML template, JSONL run log, stratified metrics dashboard, dev/validation corpus split, comparison scripts.
**Addresses:** Experimentation framework, evidence-based ADR workflow.
**Avoids:** Adopting MLflow/W&B (wrong tool for deterministic pipeline tuning).

### Phase 4: Re-OCR Pipeline Integration
**Rationale:** Designed but not wired. Phase 1 metrics will reveal exactly which document types need re-OCR most.
**Delivers:** Neural re-OCR for flagged words integrated into main pipeline, foreign term CER tracking.
**Addresses:** Re-OCR pipeline integration, OCR false positive rate reduction.
**Avoids:** Blanket re-OCR (use evaluation metrics to target worst performers).

### Phase 5: Monorepo Migration
**Rationale:** Defer until library boundaries are proven through Phases 1-4. Migration is disruptive and should happen when the package interfaces are stable.
**Delivers:** uv workspace with packages/ structure, shared scholarly_testdata package, Git LFS for binary test data, archived CryptOfCogito repo.
**Addresses:** Repo structure decision, unified architecture plan, shared GT package.
**Avoids:** Premature migration before knowing what the package boundary looks like in practice.

### Phase Ordering Rationale

- Phases 1-2 are the critical path: measurement before improvement, IR before serialization.
- Phase 3 builds on Phase 1's evaluation infrastructure -- cannot experiment without metrics.
- Phase 4 is the first extraction improvement phase, informed by all prior measurement.
- Phase 5 is intentionally last -- repo structure is organizational, not functional. Doing it earlier risks restructuring before boundaries are clear.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** IR enrichment needs concrete Docling DoclingDocument analysis to determine exactly which fields to add. Cross-reference system design is non-trivial.
- **Phase 4:** Re-OCR integration needs spike on GOT-OCR vs Tesseract for philosophy-specific terms on 11GB VRAM hardware.

Phases with standard patterns (skip research-phase):
- **Phase 1:** GT bootstrap and evaluation are well-documented patterns. The existing evaluation library architecture is sound.
- **Phase 3:** Experimentation framework is custom JSON tooling -- no external research needed.
- **Phase 5:** uv workspaces are well-documented with multiple reference implementations.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Pipeline Architecture | HIGH | Consensus pattern across 6+ libraries, directly verified |
| Ground Truth Evaluation | MEDIUM-HIGH | Metrics are standard; layered GT schema is synthesized recommendation |
| Experimentation Framework | MEDIUM | Sound principles but agent protocols are novel/unproven |
| Repository Structure | MEDIUM-HIGH | uv workspaces well-documented; migration mechanics standard |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **No verified GT documents exist**: Phase 1 is entirely about closing this gap. Until it is closed, all quality claims are unverified.
- **IR richness unknown**: Need to attempt JSON serialization of current ScholarDocument to discover what information is lost. A spike in Phase 2.
- **CryptOfCogito integration untested**: The proposed monorepo structure assumes CryptOfCogito can consume ScholarDoc as a workspace dependency. Needs validation before Phase 5.
- **Agent experiment protocols unproven**: Phase 3's agent workflow is novel. Start with manual experiments, then automate.
- **Foreign term handling**: 23.4% OCR false positive rate on philosophical terms is the hardest unsolved problem. Phase 4 research spike needed.

## Sources

### Primary (HIGH confidence)
- Docling documentation and DoclingDocument API -- IR design, serialization patterns
- GROBID documentation -- cascade architecture, scholarly document processing
- uv workspaces official docs -- monorepo tooling
- jiwer/rapidfuzz libraries -- CER/WER computation

### Secondary (MEDIUM confidence)
- DocLayNet, S2ORC, OmniDocBench -- GT schema patterns
- Explosion blog on PDFs -- bootstrap problem approaches
- Apache Airflow uv workspace usage -- monorepo at scale
- AI Scientist-v2, Agent Laboratory -- experimentation agent patterns

### Tertiary (LOW confidence)
- Agent protocol specifications -- synthesized from emerging literature, no established standard
- Needle insertion testing -- newer technique, needs validation for document extraction

---
*Research completed: 2026-01-28*
*Ready for roadmap: yes*
