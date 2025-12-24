# Changelog

All notable changes to ScholarDoc will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Quick Start section in CLAUDE.md for AI assistant orientation
- SuperClaude Framework Integration documentation
- Serena initial_prompt for project context
- PostToolUse hook for advisory lint feedback
- Stop hook for session verification and logging

### Changed
- Hook philosophy: all hooks now advisory-only (never block except catastrophic commands)
- Pre-commit reminder narrowed to git commit commands only
- Cleaned up settings.local.json malformed entries

### Fixed
- post-edit-quality.py no longer blocks on lint errors (now advisory)

## [0.1.0] - Unreleased

### Added
- PDF reader with PyMuPDF (ADR-001)
- Cascading text extractor with source tracking
- OCR pipeline architecture with spellcheck selector (ADR-002)
- Block-based line-break detection (ADR-003)
- Ground truth validation framework (130 error pairs, 77 correct words)
- TDD workflow commands (`/project:tdd`, `/project:implement`)
- Exploration spike framework (32 spikes)
- Pydantic data models (RawDocument, NormalizedDocument, ScholarDocument)

### Metrics
- OCR error detection rate: 99.2%
- False positive rate: 23.4%
- PyMuPDF performance: 32-57x faster than alternatives

---

## Documentation Update Protocol

When updating this changelog:
1. Add entries under `[Unreleased]` as work progresses
2. Move entries to versioned section when releasing
3. Categories: Added, Changed, Deprecated, Removed, Fixed, Security
4. Link issues/PRs where applicable
