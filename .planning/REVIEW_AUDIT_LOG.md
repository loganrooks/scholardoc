# Review Audit Log

> Tracks exactly where we searched, what we found, and what's still uncovered.
> Created: 2026-03-19

---

## Search Locations Checked

### Pass 1 (Initial agents — 2026-03-19)

| Location | What we looked for | What we found | Confidence |
|----------|-------------------|---------------|------------|
| scholardoc/ (this repo) | Structure, docs, code | Dual-package repo (scholardoc + scholargt). 32 spikes, 4 ADRs, extensive .planning/ | HIGH |
| scholardoc/.serena/memories/ | Prior vision discussions | 15 memory files (Dec 2025 - Jan 2026). Vision, OCR, GT schema, sessions | HIGH |
| scholardoc/.planning/ | GSD state | PROJECT.md, ROADMAP.md, STATE.md, phase plans, knowledge base | HIGH |
| ~/workspace/projects/ | All project directories | Listed but only checked philograph-mcp and philo-rag-simple at surface level | LOW |
| ~/workspace/university/ | PHL410 | Found PHL410 course at courses/2025-2026/phl410-madness/. Found .claude/ infrastructure but did NOT deeply explore | LOW |
| ~/workspace/writings/PHL410_CryptOfCogito | CryptOfCogito annotation tool | Agent mentioned it exists (2,237 lines) but did NOT read its docs/planning/ADRs | LOW |
| philograph-mcp | Cross-project deliberations | Surface check only — no deep exploration | LOW |
| philo-rag-simple | Cross-project deliberations | Surface check only — no deep exploration | LOW |
| claude-enhanced | Cross-project planning | Mentioned but NOT checked | NOT CHECKED |

### Gaps from Pass 1

- [ ] CryptOfCogito: NOT deeply explored. Has 20 ADRs, .planning/, docs/ — critical for GT and annotation tool context
- [ ] Hermeneutic workspace / broader research system: NOT searched for
- [ ] Cross-repo comparison review: NOT found — search for it
- [ ] OCR literature: NOT reviewed. GLM-OCR and recent field advances NOT checked
- [ ] philograph-mcp: Has .planning/? Deliberations? NOT deeply checked
- [ ] philo-rag-simple: Same — NOT deeply checked
- [ ] Experimental design / spike methodology: NOT critically reviewed
- [ ] GT design concerns: NOT surfaced beyond what agents reported
- [ ] audiobookify: NOT checked for cross-project context
- [ ] semantic-calibre: NOT checked
- [ ] zlibrary-mcp: Agent mentioned "reusable patterns" but NOT deeply checked for vision docs

---

## Pass 2 (Deep targeted searches — 2026-03-19)

### Agent: CryptOfCogito Deep Dive
| Location | What we looked for | What we found | Confidence |
|----------|-------------------|---------------|------------|
| ~/workspace/writings/PHL410_CryptOfCogito/ | Full project structure, ADRs, docs, code | MASSIVE project: 20 ADRs, annotation tool MVP (FastAPI + Canvas), GT schema v0.3.1, database design v0.4 (SQLAlchemy), export format spec, RAG vision doc, scholarly_annotate package proposal | HIGH |
| CryptOfCogito/.serena/memories/ | Cross-project context | scholardoc_analysis.md (comparison review!), scholarly_annotate_design.md, rag_embedding_research.md, 10+ memory files | HIGH |
| CryptOfCogito/docs/decisions/ | All 20 ADRs | Full architecture: RT-DETR layout detection, OCR library choice (Surya + EasyOCR), VLM evaluation (GOT-OCR feasible), database arch, export format, RAG vision | HIGH |
| CryptOfCogito/preprocess/ | OCR pipeline code | Different approach from scholardoc: RT-DETR regions -> crop -> upsample -> Surya/EasyOCR OCR | HIGH |

### Agent: Workspace-Wide Vision Search
| Location | What we looked for | What we found | Confidence |
|----------|-------------------|---------------|------------|
| ~/workspace/projects/hermeneutic-workspace-plugin/ | Cross-project orchestration | FOUND: MCP server with trace_downstream, validate_document, workspace_search tools. Phased rollout. codex-skills for Claude Desktop | HIGH |
| ~/workspace/projects/epistemic-agency/ | Epistemological framework | FOUND: 47 findings on agentic AI epistemology, Peirce/Dewey/Stiegler grounding, traces/, knowledge-base/ | HIGH |
| ~/workspace/projects/claude-enhanced/ | Meta-project docs | Two-level system (generator + generated). Plugin architecture vision. Init system with 9 agents | HIGH |
| ~/workspace/projects/get-shit-done-reflect/ | GSD framework deliberations | 54 deliberation files in .serena/memories/ | MEDIUM |
| All ~/workspace/projects/*/ | Vision docs, CLAUDE.md | Mapped all projects. No single ecosystem vision doc exists — vision is distributed | HIGH |
| ~/workspace/writings/ | Planning docs | CryptOfCogito found here (not in projects/) | HIGH |

### Agent: OCR & Experiment Design
| Location | What we looked for | What we found | Confidence |
|----------|-------------------|---------------|------------|
| scholardoc/spikes/ | OCR spike analysis | 32 spikes thoroughly documented. Key: 41% auto-correction damage, docTR wins re-OCR comparison, page numbers devastate embeddings (-29%) | HIGH |
| scholardoc/docs/adr/ | OCR architecture decisions | ADR-002 (spellcheck as selector), ADR-003 (line-break), ADR-004 (source tracking) all well-documented | HIGH |
| .serena/memories/*layout* | Layout segmentation | Two research memos: Docling RT-DETR only model detecting footnotes (0.95 conf). Surya v0.17 broken | HIGH |
| .planning/phases/01.1*/GAP* | Schema gaps | Two gap analyses: conservative (zero blocking) + non-conservative (7 SFPs, all adopted). Deferred: SFP-7 (content_layer) | HIGH |
| scholargt/ source code | TODO/FIXME/limitations | NOT CHECKED by agent — need manual grep | LOW |
| Experimental methodology | Rigor assessment | Ad-hoc spike scripts. No formal experiment template. No reproducibility guarantees. Validation set small (130 pairs). Phase 3 plans experimentation framework but not built | HIGH |

### Agent: Philograph & Philo-RAG Deep Dive
| Location | What we looked for | What we found | Confidence |
|----------|-------------------|---------------|------------|
| ~/workspace/projects/philograph-mcp/ | Knowledge graph project | Bootstrap phase. SPARC-V-L3 protocol. PostgreSQL + pgvector. Comprehensive vision but minimal implementation | HIGH |
| ~/workspace/projects/philo-rag-simple/ | RAG engine | HEAVILY documented: 10 ADRs validated, 3-phase rollout, structure-aware hybrid chunking, 80ms query latency proven. Pre-Phase 1 (ready but not started?) | HIGH |
| ~/workspace/projects/zlibrary-mcp/ | Pipeline source | Stable. Has reusable components: garbled_text_detection, footnote_corruption_model, note_classification | HIGH |
| ~/workspace/projects/audiobookify/ | Audio conversion | Active v2.5.0. Enhanced chapter detection, parallel processing | MEDIUM |
| ~/workspace/projects/semantic-calibre/ | Library management | Phase 4.4 complete. Semantic search, research projects, annotations | MEDIUM |

---

### Pass 3: Deep dives on remaining projects (2026-03-19)

| Location | What we looked for | What we found | Confidence |
|----------|-------------------|---------------|------------|
| ~/workspace/projects/philo-rag-simple/ | Full architecture, implementation status | HEAVILY implemented: Phase 1 COMPLETE. 6 MCP tools, 196 tests, 80ms queries. 15 ADRs. Node.js/TS + Python. Structure-aware chunking. SQLite + FAISS local-first. Uses zlibrary-mcp upstream | HIGH |
| ~/workspace/projects/philograph-mcp/ | Full architecture, implementation status | MINIMAL implementation: DB models + tests only. Ambitious vision (concept genealogy, argument mapping, influence networks). PostgreSQL + pgvector + Vertex AI. Last commit: Jan 6, 2025 (14 months ago) | HIGH |
| ~/workspace/projects/mcp-vector-database/ (PhiloGraph) | Full architecture, implementation status | SUBSTANTIALLY COMPLETE for Tier 0. PostgreSQL + pgvector + LiteLLM proxy. Full ingestion pipeline, search, acquisition. Relationship modeling (cites, responds_to, influences). BLOCKED on GCP credentials. 9 ADRs. Rhizomatic/non-hierarchical design | HIGH |
| ~/workspace/projects/philoso-roo/ | Full architecture, vision | MATURE RooCode system (V18.3.7). 14 philosophy modes. KB with RIGOR FIELDS (positive/negative determination, presuppositions, counter-arguments). DAG knowledge representation. Dynamic roles. 800-line text processor. Integration with scholardoc + zlibrary-mcp | HIGH |

### Pass 4: Final project sweep (2026-03-19)

| Location | What we looked for | What we found | Confidence |
|----------|-------------------|---------------|------------|
| ~/workspace/projects/arxiv-sanity-mcp/ | Paper discovery MCP | DIRECTLY RELEVANT: 13 tools, 493 tests, Phase 6 active. Metadata-first lazy enrichment | HIGH |
| ~/workspace/projects/PDFAgentialConversion/ | PDF conversion | DIRECTLY RELEVANT: Skill for difficult scholarly PDFs -> markdown bundles. Validation gates. Challenge corpus (Derrida, Levinas validated) | HIGH |
| claude-enhanced/mcp-servers/philpapers/ | PhilPapers MCP | FOUND: 8 tools, hybrid Semantic Scholar + PhilArchive. Configured in ~/.claude/settings.json | HIGH |
| ~/workspace/projects/f1-modeling/ | Relevance check | NOT relevant (Formula 1 modeling) | HIGH |
| ~/workspace/projects/robotic-psalms/ | Relevance check | NOT relevant (ML music generation) | HIGH |
| ~/workspace/projects/claude-notify/ | Relevance check | Infrastructure only (push notifications for dev) | HIGH |

## Still Not Checked

- [ ] **OCR literature review** — GLM-OCR and recent field advances. Need arxiv-sanity-mcp or manual search
- [ ] **scholargt/ source code quality** — grep for TODO/FIXME/limitations/concerns
- [ ] **epistemic-agency full deep dive** — 47 findings, only surface level explored
- [ ] **PDFAgentialConversion deep dive** — May overlap with scholardoc's extraction concerns

## Critical Discovery: Ecosystem Redundancy

THREE projects do some form of philosophical RAG/search:
1. **philo-rag-simple**: SQLite + FAISS, local-first, Phase 1 complete, 196 tests (MOST MATURE)
2. **mcp-vector-database (PhiloGraph)**: PostgreSQL + pgvector, cloud embeddings, Tier 0 ~80% (MOST AMBITIOUS)
3. **philograph-mcp**: PostgreSQL + pgvector + Vertex AI, minimal code (MOST PLANNED, LEAST BUILT)

Additionally, **philoso-roo** has its own KB structure with rigor fields that could inform ScholarGT's schema design

---

## Critical Discoveries (Pass 2)

### 1. THREE competing GT schemas exist
- ScholarDoc v3/v4 (ground_truth/schema_v4_comprehensive.json)
- CryptOfCogito v0.3.1 (preprocess/src/preprocess/ground_truth/schema.py)
- ScholarGT v2.0.0 (scholargt/schema/)

ScholarGT v2.0.0 was designed to unify the first two, but CryptOfCogito's v0.4 database design has features ScholarGT lacks (projects, stable IDs, export format).

### 2. TWO competing OCR approaches
- ScholarDoc: PyMuPDF text layer + spellcheck-as-selector + selective re-OCR (docTR)
- CryptOfCogito: RT-DETR layout detection + region crop + Surya/EasyOCR OCR
- VLM approach (GOT-OCR) proven feasible but not integrated
- Neither has done recent literature review (GLM-OCR etc.)

### 3. The "third prong" is likely the hermeneutic-workspace-plugin
Cross-project MCP orchestration enabling complex philosophical research workflows. But also: the broader vision of scholardoc as "atomic unit" enabling inference, citation, reading/writing workflows hasn't been captured in any single document.

### 4. Ecosystem is 10+ interconnected projects with distributed vision
No single "ecosystem vision" document exists. The pipeline description lives in ~/CLAUDE.md as a one-liner. Individual project visions are siloed.

### 5. CryptOfCogito has a scholardoc comparison analysis
In .serena/memories/scholardoc_analysis.md — this is the "review comparing them" that Logan mentioned.

### 6. scholarly_annotate package was proposed but never built
Exists only as design in CryptOfCogito's Serena memory. Would extract the annotation tool into a reusable package.
