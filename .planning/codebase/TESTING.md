# Testing Patterns

**Analysis Date:** 2026-01-28

## Test Framework

**Runner:**
- pytest 8.0.0+
- Config: `pyproject.toml` lines 130-132

**Assertion Library:**
- pytest built-in assertions
- No additional assertion libraries

**Run Commands:**
```bash
uv run pytest                    # Run all tests
uv run pytest -v                 # Verbose output
uv run pytest --cov              # With coverage
uv run pytest -k test_name       # Run specific test
uv run pytest tests/unit/        # Run unit tests only
uv run pytest tests/integration/ # Run integration tests only
```

**Current Status:**
- 395 tests passing
- 6 tests skipped (ground truth regression tests when no verified documents)
- 2 warnings (unregistered `@pytest.mark.slow`)
- ~5,416 lines of test code

## Test File Organization

**Location:**
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Ground truth tests: `tests/unit/ground_truth/`
- Co-located with source (NO) - tests are in separate `tests/` directory

**Naming:**
- Test files: `test_*.py` (e.g., `test_models.py`, `test_pdf_reader.py`)
- Test classes: `Test*` (e.g., `TestScholarDocumentCreation`, `TestPDFReaderBasics`)
- Test functions: `test_*` (e.g., `test_span_creation`, `test_read_returns_raw_document`)

**Structure:**
```
tests/
├── conftest.py                              # Shared fixtures
├── unit/
│   ├── test_models.py                       # Core data model tests
│   ├── test_pdf_reader.py                   # PDF reader tests
│   ├── test_extractors.py                   # Structure extraction tests
│   ├── test_ocr_pipeline.py                 # OCR pipeline tests
│   ├── test_profiles.py                     # Document profile tests
│   └── ground_truth/
│       ├── test_metrics.py                  # Evaluation metrics tests
│       ├── test_matching.py                 # Element matching tests
│       └── test_normalize.py                # Normalization tests
├── integration/
│   ├── test_convert.py                      # End-to-end conversion tests
│   └── test_ground_truth_regression.py      # Regression tests against verified data
└── fixtures/                                # Test data (PDFs, YAMLs)
```

## Test Structure

**Class Organization:**
```python
class TestScholarDocumentCreation:
    """Test ScholarDocument creation and basic operations."""

    @pytest.fixture
    def sample_document(self) -> ScholarDocument:
        """Create a sample document for testing."""
        return ScholarDocument(
            text="The question of Being has been forgotten.",
            pages=[PageSpan(start=0, end=41, label="1", index=0)],
            metadata=DocumentMetadata(title="Being and Time"),
        )

    def test_basic_creation(self, sample_document):
        """Can create ScholarDocument with basic fields."""
        doc = sample_document
        assert doc.text == "The question of Being has been forgotten."
        assert len(doc.pages) == 1

    def test_document_length(self, sample_document):
        """len() returns text length."""
        assert len(sample_document) == 41
```

**Patterns:**
- One test class per major feature area
- Descriptive test class docstrings
- Fixtures as class methods for test-specific data
- Clear test names describing behavior being tested

**Test Naming Convention:**
- `test_<behavior>_<condition>`: `test_span_validation_negative_start`, `test_precision_zero_denominator`
- `test_<method>_<behavior>`: `test_page_for_position_not_found`, `test_to_markdown_with_footnotes`
- Verb-based: "can create", "returns", "raises", "detects"

## Fixtures

**Shared Fixtures** (`tests/conftest.py`):
```python
@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture(scope="session")
def sample_config():
    """Return a sample ConversionConfig for testing."""
    from scholardoc import ConversionConfig
    return ConversionConfig()
```

**Test-Specific Fixtures:**
```python
# In test_pdf_reader.py
@pytest.fixture
def small_pdf() -> Path:
    """Small 2-page Kant sample for fast tests."""
    return SAMPLE_PDFS / "kant_critique_pages_64_65.pdf"

@pytest.fixture
def reader() -> PDFReader:
    """Default PDF reader instance."""
    return PDFReader()

# In test_models.py
@pytest.fixture
def sample_document(self) -> ScholarDocument:
    """Create a sample document for testing."""
    return ScholarDocument(text="...", pages=[...])
```

**Fixture Scope:**
- `scope="session"`: For expensive setup (shared config, directory paths)
- Default (function scope): For test data that needs fresh instances
- Use fixtures for complex object creation, not simple values

**Fixture Locations:**
- `conftest.py`: Shared across all tests
- Test class methods: Test-specific fixtures
- Module-level: Fixtures shared within a test file

## Mocking

**Framework:**
- pytest built-in mocking (via `unittest.mock`)
- Minimal mocking - prefer real objects with test data

**Patterns:**
Not heavily used in this codebase. Most tests use:
- Real PDF files from `spikes/sample_pdfs/`
- Actual objects with test data
- Integration-style tests even in unit tests

**When Mocking is Used:**
- External dependencies (file systems via `tmp_path` fixture)
- Slow operations in unit tests
- Error conditions that are hard to trigger

**Example with tmp_path:**
```python
def test_save_and_load_roundtrip(self, complete_document, tmp_path):
    """Document survives save/load roundtrip."""
    save_path = tmp_path / "test.scholardoc"
    doc.save(save_path)
    loaded = ScholarDocument.load(save_path)
    assert loaded.text == doc.text
```

## Test Data and Fixtures

**Sample PDFs:**
- Location: `spikes/sample_pdfs/`
- Small samples for fast tests: `kant_critique_pages_64_65.pdf` (2 pages)
- Multi-page samples: `derrida_footnote_pages_120_125.pdf` (6 pages)
- Referenced as constants: `SAMPLE_PDFS = Path(__file__).parent.parent.parent / "spikes" / "sample_pdfs"`

**Ground Truth Data:**
- Location: `ground_truth/documents/`
- Format: YAML files with verified annotations
- Used for regression tests
- Pattern: `{pdf_name}.yaml` with annotation status tracking

**Test Data Creation:**
```python
# Helper functions for test data
def make_element(element_id: str = "test") -> NormalizedElement:
    """Helper to create minimal test element."""
    return NormalizedElement(
        element_type="footnote",
        element_id=element_id,
        pages=[0],
        text="Test",
    )

# In-line test data for simple cases
def test_span_creation(self):
    """Can create a basic span."""
    span = Span(start=10, end=20)
    assert span.start == 10
```

## Coverage

**Requirements:**
- No explicit coverage threshold enforced
- pytest-cov plugin available: `pytest-cov>=4.1.0`

**View Coverage:**
```bash
uv run pytest --cov=scholardoc --cov-report=html
uv run pytest --cov=scholardoc --cov-report=term
```

**Coverage Focus:**
- Core models: `scholardoc/models.py` (well-covered)
- PDF reader: `scholardoc/readers/pdf_reader.py` (well-covered)
- Extractors: `scholardoc/extractors/` (well-covered)
- Integration: End-to-end conversion flows tested

## Test Types

**Unit Tests** (`tests/unit/`):
- Scope: Individual classes and functions
- Fast execution (<1s per test typically)
- Use small test data (2-8 page PDFs)
- Test individual components in isolation
- Examples:
  - `test_models.py`: Data model behavior, validation, serialization
  - `test_pdf_reader.py`: PDF reading, text extraction, metadata
  - `test_ocr_pipeline.py`: OCR components (dictionary, detector, rejoiner)

**Integration Tests** (`tests/integration/`):
- Scope: Full pipeline from PDF to ScholarDocument
- Use realistic PDFs
- Test component interactions
- Examples:
  - `test_convert.py`: End-to-end conversion, config application, output formats
  - `test_ground_truth_regression.py`: Quality metrics against verified data

**Ground Truth Evaluation Tests** (`tests/unit/ground_truth/`):
- Scope: Evaluation library correctness
- Test metrics computation, element matching, normalization
- Examples:
  - `test_metrics.py`: Precision, recall, F1 calculation
  - `test_matching.py`: Element matching algorithms
  - `test_normalize.py`: Ground truth and prediction normalization

**E2E Tests:**
- Not a separate category - integration tests serve this purpose
- `test_convert.py` covers full conversion pipeline

## Property-Based Testing (Hypothesis)

**Framework:**
- hypothesis 6.100.0+
- Available but not heavily used yet

**Usage:**
- Currently minimal in codebase
- Intended for future use on validation logic and edge cases

**Potential Applications:**
- Span overlap detection
- Text position calculations
- Metrics computation edge cases

## Ground Truth Evaluation Testing

**Approach:**
Tests ensure extraction quality doesn't regress below baseline thresholds.

**Baseline Thresholds** (`test_ground_truth_regression.py`):
```python
THRESHOLDS = {
    "footnote": {"precision": 0.75, "recall": 0.70, "f1": 0.72},
    "citation": {"precision": 0.70, "recall": 0.65, "f1": 0.67},
    "marginal_ref": {"precision": 0.75, "recall": 0.75, "f1": 0.75},
    "page_number": {"precision": 0.90, "recall": 0.90, "f1": 0.90},
}
OVERALL_F1_THRESHOLD = 0.70
```

**Pattern:**
```python
@skip_no_verified
class TestGroundTruthRegression:
    """Regression tests against ground truth documents."""

    @pytest.mark.parametrize("yaml_path,pdf_path", verified_docs)
    def test_extraction_meets_thresholds(
        self, yaml_path: Path, pdf_path: Path, evaluation_modules, convert_pdf
    ):
        """Test that extraction meets minimum quality thresholds."""
        # Load ground truth
        gt_elements = load_ground_truth_elements(yaml_path)

        # Run extraction
        doc = convert_pdf(pdf_path)
        pred_elements = scholar_doc_to_elements(doc)

        # Compute metrics and assert thresholds
        for element_type in element_types:
            metrics = compute_metrics(matches)
            assert metrics.precision >= threshold["precision"]
```

**Skip Conditions:**
- Tests skipped if no verified ground truth documents exist
- Tests skipped if required PDFs not available
- Conditional imports with `pytest.skip()` for optional dependencies

## Common Patterns

**Parametrized Tests:**
```python
@pytest.mark.parametrize(
    "pdf_name",
    [
        "kant_critique_pages_64_65.pdf",
        "derrida_footnote_pages_120_125.pdf",
        "heidegger_pages_22-23_primary_footnote_test.pdf",
    ],
)
class TestMultiplePDFs:
    """Test reader works across different PDF types."""

    def test_read_succeeds(self, reader, pdf_name):
        """Reader can read the PDF without error."""
        pdf_path = SAMPLE_PDFS / pdf_name
        if not pdf_path.exists():
            pytest.skip(f"Sample PDF not found: {pdf_name}")
        raw = reader.read(pdf_path)
        assert raw.page_count > 0
```

**Exception Testing:**
```python
def test_span_validation_negative_start(self):
    """Span rejects negative start."""
    with pytest.raises(ValueError, match="start must be >= 0"):
        Span(start=-1, end=10)

def test_file_not_found_raises(self, reader):
    """read() raises for missing file."""
    with pytest.raises(FileNotFoundError):
        reader.read("/nonexistent/path.pdf")
```

**Testing Properties:**
```python
def test_document_length(self, sample_document):
    """len() returns text length."""
    doc = sample_document
    assert len(doc) == 41

def test_document_getitem(self, sample_document):
    """Can slice document text."""
    doc = sample_document
    assert doc[0:12] == "The question"
```

**Round-trip Testing:**
```python
def test_save_and_load_roundtrip(self, complete_document, tmp_path):
    """Document survives save/load roundtrip."""
    doc = complete_document
    save_path = tmp_path / "test.scholardoc"

    doc.save(save_path)
    loaded = ScholarDocument.load(save_path)

    # Verify all fields preserved
    assert loaded.text == doc.text
    assert len(loaded.footnote_refs) == 1
    assert loaded.metadata.title == "Test Philosophy Book"
```

**Conditional Skipping:**
```python
def test_known_english_words(self, dictionary):
    """Common English words should be recognized."""
    if not SPELLCHECK_AVAILABLE:
        pytest.skip("pyspellchecker not installed")

    assert dictionary.is_known_word("the")
```

**Helper Functions:**
```python
# In test files
def make_element(element_id: str = "test") -> NormalizedElement:
    """Helper to create minimal test element."""
    return NormalizedElement(...)

def make_match(match_type: str, text_sim: float = 0.0) -> ElementMatch:
    """Helper to create test matches."""
    return ElementMatch(...)
```

## Test Execution

**Fast Feedback:**
- Most tests under 100ms
- Small PDF samples for fast execution
- Total suite runs in ~42 seconds

**Slow Tests:**
- Marked with `@pytest.mark.slow` (2 warnings about unregistered marker)
- Can be excluded: `pytest -m "not slow"`

**Test Selection:**
```bash
# Run specific test file
uv run pytest tests/unit/test_models.py

# Run specific test class
uv run pytest tests/unit/test_models.py::TestSpanBasics

# Run specific test
uv run pytest tests/unit/test_models.py::TestSpanBasics::test_span_creation

# Run by keyword
uv run pytest -k "span"

# Run integration tests only
uv run pytest tests/integration/
```

---

*Testing analysis: 2026-01-28*
