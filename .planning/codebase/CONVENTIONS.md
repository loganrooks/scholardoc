# Coding Conventions

**Analysis Date:** 2026-01-28

## Naming Patterns

**Files:**
- snake_case for all Python files: `pdf_reader.py`, `ocr_pipeline.py`, `test_models.py`
- Test files prefixed with `test_`: `test_models.py`, `test_extractors.py`
- Module names match directory names: `scholardoc/readers/pdf_reader.py`, `scholardoc/extractors/cascading.py`

**Classes:**
- PascalCase for all classes: `ScholarDocument`, `PDFReader`, `CascadingExtractor`
- Suffix pattern for types: `*Error` for exceptions (`ScholarDocError`, `UnsupportedFormatError`), `*Config` for configuration (`ConversionConfig`, `OCRConfig`)
- Dataclasses named descriptively: `PageData`, `TextBlock`, `OutlineEntry`, `PipelineResult`

**Functions:**
- snake_case for all functions: `convert_pdf()`, `detect_body_font_size()`, `estimate_document_type()`
- Verb-noun pattern for actions: `get_font_statistics()`, `load_ground_truth_elements()`, `compute_metrics()`
- Query methods use descriptive prefixes: `page_for_position()`, `section_for_position()`, `has_outline`

**Variables:**
- snake_case for variables: `raw_doc`, `page_count`, `font_size`
- Descriptive names preferred over abbreviations: `confidence` not `conf`, `candidates` not `cands`
- Constants in UPPERCASE: `THRESHOLDS`, `SAMPLE_PDFS`, `SPELLCHECK_AVAILABLE`
- Private attributes prefixed with underscore: `_text_cache`, `_page_positions`

**Types/Enums:**
- PascalCase enum classes: `DocumentType`, `NoteType`, `ChunkStrategy`, `QualityLevel`, `OCRErrorType`
- UPPERCASE enum values: `DocumentType.BOOK`, `NoteType.FOOTNOTE`, `QualityLevel.GOOD`

## Code Style

**Formatting:**
- Tool: ruff (version 0.4.0+)
- Config: `pyproject.toml` lines 113-129
- Line length: 100 characters
- Target: Python 3.11+

**Linting:**
- Tool: ruff with these rules enabled:
  - E (pycodestyle errors)
  - W (pycodestyle warnings)
  - F (Pyflakes)
  - I (isort)
  - B (flake8-bugbear)
  - UP (pyupgrade)
- Known first-party: `scholardoc`

**String Quotes:**
- Double quotes for strings: `"text"` not `'text'`
- Triple double-quotes for docstrings: `"""Docstring."""`

## Import Organization

**Order:**
1. `from __future__ import annotations` (always first when present)
2. Standard library imports
3. Third-party imports
4. Local imports
5. TYPE_CHECKING conditional imports last

**Pattern Example:**
```python
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import fitz  # PyMuPDF

from scholardoc.models import ScholarDocument
from scholardoc.readers import PDFReader

if TYPE_CHECKING:
    from collections.abc import Iterator
```

**Path Aliases:**
- Known first-party: `scholardoc`
- No path aliases configured (use relative imports within package)
- Test imports use absolute: `from scholardoc.models import ScholarDocument`

**Import Style:**
- Explicit imports preferred: `from scholardoc.models import ScholarDocument`
- Wildcard imports avoided
- TYPE_CHECKING used for type-only imports to avoid circular dependencies

## Type Annotations

**Usage:**
- Type hints required for all function signatures
- Return types always specified: `def read(path: Path) -> RawDocument:`
- Optional types use `| None` syntax (not `Optional`): `str | None`
- Modern union syntax: `int | str` (not `Union[int, str]`)
- Generic types fully annotated: `list[str]`, `dict[str, int]`

**Pattern:**
```python
def page_for_position(self, pos: int) -> int | None:
    """Find page index containing a text position."""
    for i, (start, end) in enumerate(self.page_positions):
        if start <= pos < end:
            return i
    return None
```

**TYPE_CHECKING imports:**
Used to avoid runtime import overhead and circular dependencies:
```python
if TYPE_CHECKING:
    from collections.abc import Iterator
    import fitz
```

## Docstrings

**Style:**
- Google-style docstrings
- Always triple double-quotes: `"""Docstring."""`
- One-line for simple functions: `"""Return page index."""`
- Multi-line for complex functions with Args/Returns sections

**Module-level:**
```python
"""
PDF Reader using PyMuPDF (fitz).

Extracts text, positions, fonts, and structure from PDFs.
Based on ADR-001 findings: PyMuPDF is 32-57x faster than alternatives.
"""
```

**Class-level:**
```python
"""
Main OCR correction pipeline.

Orchestrates three stages:
1. LineBreakRejoiner: Prepares text by rejoining hyphenated words
2. OCRErrorDetector: Flags suspicious words using spellcheck
3. HybridReOCREngine: Re-OCRs lines containing flagged words

Example:
    >>> pipeline = OCRPipeline()
    >>> result = pipeline.process_text("Text with tbe errors")
"""
```

**Function-level:**
```python
def page_for_position(self, pos: int) -> int | None:
    """Find page index containing a text position."""
```

**When to document:**
- All public functions and classes
- Complex algorithms with explanation
- Usage examples for main API functions
- No docstring needed for obvious property methods or simple helpers

## Error Handling

**Exception Hierarchy:**
- Base: `ScholarDocError` in `scholardoc/exceptions.py`
- Specific: `UnsupportedFormatError`, `ExtractionError`, `ConfigurationError`
- All inherit from base for easy catching

**Pattern:**
```python
if not path.exists():
    raise FileNotFoundError(f"PDF not found: {path}")

if format not in SUPPORTED_FORMATS:
    raise UnsupportedFormatError(
        f"Format {format!r} is not supported. Supported: {', '.join(SUPPORTED_FORMATS)}"
    )
```

**Validation:**
- Pydantic for data validation in models
- `__post_init__` for dataclass validation
- Explicit ValueError for invalid parameters

**Error messages:**
- Descriptive with context
- Include actual vs expected values
- Use f-strings for formatting

## Pydantic Model Patterns

**Base Usage:**
```python
@dataclass(frozen=True)
class Span:
    """Base class for position spans in text."""

    start: int  # Start position in text (inclusive)
    end: int  # End position in text (exclusive)

    def __post_init__(self):
        if self.start < 0:
            raise ValueError(f"start must be >= 0, got {self.start}")
        if self.end < self.start:
            raise ValueError(f"end ({self.end}) must be >= start ({self.start})")
```

**Frozen Dataclasses:**
- Use `frozen=True` for immutable types: `Span`, `FootnoteRef`, `TextBlock`
- Ensures safety for position-based annotations
- Allows use as dictionary keys

**Field Factories:**
```python
@dataclass
class OCRConfig:
    additional_vocabulary: set[str] = field(default_factory=set)

@dataclass
class PipelineStats:
    engine_used: OCREngine = OCREngine.NONE
```

**Cached Properties:**
```python
@cached_property
def paragraph_texts(self) -> list[str]:
    """Paragraph strings (cached)."""
    return [self.text[p.start:p.end] for p in self.paragraphs]
```

## Logging

**Framework:** Python standard `logging` module

**Patterns:**
```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Processing page %d", page_index)
logger.warning("No outline found, falling back to heading detection")
logger.error("Extraction failed: %s", error_msg)
```

**When to log:**
- Debug: Processing steps, intermediate values
- Info: Major phase transitions, success messages
- Warning: Fallback behavior, missing optional data
- Error: Extraction failures, validation errors

**NOT used:**
- No print statements in production code
- Console output only in scripts (e.g., `ground_truth/scripts/`)

## Comments

**When to Comment:**
- Complex algorithms with non-obvious logic
- ADR references: `# Based on ADR-001 findings`
- Workarounds: `# Workaround for PyMuPDF issue #123`
- Magic numbers: `threshold = 0.8  # Based on validation data`
- TODO/FIXME markers (though minimal in this codebase)

**Style:**
- Inline comments start with `# ` (space after hash)
- Block comments for sections:
```python
# =============================================================================
# OCR PIPELINE
# =============================================================================
```

**JSDoc/TSDoc:**
Not applicable (Python project)

## Function Design

**Size:**
- Small, focused functions preferred
- Most functions under 50 lines
- Extract complex logic into helper functions

**Parameters:**
- Use keyword-only args for clarity: `def __init__(self, *, profile: DocumentProfile | None = None)`
- Default values for optional parameters
- Type hints for all parameters

**Return Values:**
- Explicit return type annotations
- Return `None` explicitly when no value
- Use dataclasses for complex return values: `PipelineResult`, `StructureResult`

## Module Design

**Exports:**
- `__init__.py` controls public API
- Use `__all__` to declare exports explicitly (see `scholardoc/__init__.py`)
- Import order: enums, base types, concrete types, functions

**Package structure:**
```python
# scholardoc/__init__.py
from scholardoc.models import ScholarDocument, DocumentType, ...
from scholardoc.convert import convert, convert_batch, ...
from scholardoc.config import ConversionConfig

__version__ = "0.1.0"
__all__ = ["convert", "ScholarDocument", ...]
```

**Barrel Files:**
- Package `__init__.py` files export key types: `scholardoc/readers/__init__.py`, `scholardoc/extractors/__init__.py`
- Simplifies imports: `from scholardoc.extractors import CascadingExtractor`

**Module Organization:**
- One class per file for major types: `pdf_reader.py`, `cascading.py`
- Related utilities grouped: `validators.py`, `sources.py`
- Clear separation: `readers/`, `extractors/`, `normalizers/`, `ocr/`, `writers/`

---

*Convention analysis: 2026-01-28*
