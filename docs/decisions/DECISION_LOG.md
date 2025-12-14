# Decision Log

Track decisions made during development for future reference.

Format: `- [DATE] DECISION - RATIONALE`

---

## December 2025

### Architecture
- [2025-12-14] Use PyMuPDF for PDF extraction - Best balance of speed, features, and font info (pending spike validation in ADR-001)
- [2025-12-14] Defer footnotes to Phase 2 - Complex detection, not essential for MVP
- [2025-12-14] Custom OCR as Phase 4 - Existing text layers often bad, but need data on prevalence first

### Process
- [2025-12-14] TDD enforcement via hooks - Prevents implementation without tests
- [2025-12-14] Claude + Human ground truth workflow - Claude proposes, humans verify uncertain items
- [2025-12-14] Exploration spikes before implementation - Validate assumptions with real PDFs

### Scope
- [2025-12-14] No chunking in library - Out of scope, leave to downstream RAG systems
- [2025-12-14] Philosophy texts as primary target - Drives requirements (footnotes, Greek, citations)

---

## How to Add Decisions

When making a significant decision:
1. Add entry here with date and rationale
2. If architectural, create ADR in `docs/adr/`
3. If implementation, update SPEC.md
4. If open question resolved, update QUESTIONS.md
