# Structure Extraction Design

> **Status:** Proposal
> **Created:** December 22, 2025
> **Context:** Probabilistic approach for detecting document structure (sections, headings, ToC)

---

## Design Goals

1. **Handle diverse document types** - books, articles, essays, reports
2. **Graceful degradation** - work well even when some signals are missing
3. **Learn from feedback** - improve over time via human corrections
4. **Extensible architecture** - easily add new detection strategies
5. **Robust to noise** - handle OCR errors and formatting variations

---

## Core Architecture: Probabilistic Fusion

Multiple independent sources propose section candidates. A fusion strategy combines them with confidence weighting. Validators check for consistency.

```
┌─────────────────────────────────────────────────────────────────┐
│                     StructureExtractor                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PDF Outline  │  │  ToC Parser  │  │   Heading    │          │
│  │   Source     │  │    Source    │  │  Detection   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └────────────┬────┴────────────────┘                   │
│                      ▼                                          │
│              ┌──────────────┐                                   │
│              │   Fusion     │                                   │
│              │   Strategy   │                                   │
│              └──────┬───────┘                                   │
│                     ▼                                           │
│              ┌──────────────┐                                   │
│              │  Validators  │                                   │
│              └──────┬───────┘                                   │
│                     ▼                                           │
│              list[SectionSpan]                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Structures

### Section Candidates

```python
@dataclass
class SectionCandidate:
    """A proposed section from a detection source."""

    start: int                    # Position in text
    end: int                      # Position in text
    title: str                    # Detected title
    level: int                    # 1=chapter, 2=section, 3=subsection
    confidence: float             # 0.0 to 1.0
    source: str                   # "pdf_outline", "toc_parser", "heading_detection"
    evidence: dict                # Source-specific supporting data

    # Evidence examples:
    # - pdf_outline: {"pdf_dest": "page_5", "outline_level": 1}
    # - toc_parser: {"toc_entry": "Chapter 1....", "page_ref": "5"}
    # - heading_detection: {"font_size": 18, "is_bold": True, "whitespace_ratio": 0.3}


@dataclass
class SectionSpan:
    """A finalized section in the document."""

    start: int
    end: int
    title: str
    level: int
    confidence: float             # Combined confidence after fusion
    sources: list[str]            # Which sources agreed
    toc_entry: ToCEntry | None    # Link to ToC if available
```

### Table of Contents

```python
@dataclass
class ToCEntry:
    """An entry parsed from a Table of Contents."""

    title: str
    page_label: str               # "5", "xiv", etc.
    level: int
    children: list["ToCEntry"]

    # Optional enrichment
    resolved_position: int | None  # Position in text if resolved
    matched_section: SectionSpan | None


@dataclass
class TableOfContents:
    """Parsed table of contents from document."""

    entries: list[ToCEntry]
    page_range: tuple[int, int]   # Where ToC appears in PDF
    confidence: float             # How confident we are this is a real ToC
```

---

## Candidate Sources

### 1. PDF Outline Source

Uses PDF's internal outline/bookmark structure (if present).

```python
class PDFOutlineSource(CandidateSource):
    """Extract structure from PDF outline/bookmarks."""

    name = "pdf_outline"

    def extract(self, doc: RawDocument) -> list[SectionCandidate]:
        outline = doc.pdf.get_toc()  # PyMuPDF
        if not outline:
            return []  # Graceful degradation

        candidates = []
        for level, title, page_num in outline:
            # Map page to text position
            position = doc.page_to_position(page_num)
            candidates.append(SectionCandidate(
                start=position,
                end=None,  # Filled by fusion
                title=title,
                level=level,
                confidence=0.95,  # PDF outlines are highly reliable
                source=self.name,
                evidence={"page_num": page_num, "outline_level": level}
            ))
        return candidates
```

**Characteristics:**
- High confidence (0.95) when present
- Often missing in older PDFs
- May not match visible headings exactly
- Provides authoritative level hierarchy

### 2. ToC Parser Source

Detects and parses table of contents pages.

```python
class ToCParserSource(CandidateSource):
    """Parse table of contents from document text."""

    name = "toc_parser"

    def extract(self, doc: RawDocument) -> list[SectionCandidate]:
        # Step 1: Find ToC pages
        toc_pages = self._find_toc_pages(doc)
        if not toc_pages:
            return []  # Graceful degradation

        # Step 2: Parse entries
        toc = self._parse_toc(doc, toc_pages)

        # Step 3: Resolve page references to positions
        candidates = []
        for entry in toc.flatten():
            position = doc.page_label_to_position(entry.page_label)
            if position is not None:
                candidates.append(SectionCandidate(
                    start=position,
                    end=None,
                    title=entry.title,
                    level=entry.level,
                    confidence=0.85,
                    source=self.name,
                    evidence={"toc_entry": entry.title, "page_ref": entry.page_label}
                ))
        return candidates

    def _find_toc_pages(self, doc: RawDocument) -> list[int]:
        """Detect pages that are likely table of contents."""
        candidates = []
        for i, page_text in enumerate(doc.pages[:20]):  # Check first 20 pages
            score = self._toc_likelihood(page_text)
            if score > 0.7:
                candidates.append(i)
        return candidates

    def _toc_likelihood(self, text: str) -> float:
        """Score how likely text is a ToC page."""
        indicators = [
            ("contents" in text.lower(), 0.3),
            ("table of contents" in text.lower(), 0.4),
            (self._has_dotted_leaders(text), 0.3),
            (self._has_page_references(text), 0.3),
            (self._has_hierarchical_structure(text), 0.2),
        ]
        return min(1.0, sum(w for match, w in indicators if match))
```

**Characteristics:**
- Moderate confidence (0.85) - parsing may have errors
- Provides chapter-level structure
- May miss subheadings not in ToC
- Enriches other sources with semantic titles

### 3. Heading Detection Source

Statistical analysis of text formatting to find headings.

```python
class HeadingDetectionSource(CandidateSource):
    """Detect headings via statistical outlier analysis."""

    name = "heading_detection"

    def extract(self, doc: RawDocument) -> list[SectionCandidate]:
        # Step 1: Extract formatting features for all text blocks
        blocks = self._extract_blocks_with_features(doc)

        # Step 2: Compute statistics
        font_sizes = [b.font_size for b in blocks]
        median_size = statistics.median(font_sizes)
        mad = self._median_absolute_deviation(font_sizes)

        # Step 3: Find outliers (potential headings)
        candidates = []
        for block in blocks:
            score = self._heading_score(block, median_size, mad)
            if score > 0.5:
                level = self._estimate_level(block.font_size, font_sizes)
                candidates.append(SectionCandidate(
                    start=block.position,
                    end=None,
                    title=block.text.strip(),
                    level=level,
                    confidence=score,
                    source=self.name,
                    evidence={
                        "font_size": block.font_size,
                        "is_bold": block.is_bold,
                        "whitespace_before": block.whitespace_before,
                        "outlier_score": score
                    }
                ))
        return candidates

    def _heading_score(self, block: TextBlock, median: float, mad: float) -> float:
        """Score likelihood that block is a heading."""
        scores = []

        # Font size outlier (larger = more likely heading)
        if mad > 0:
            z_score = (block.font_size - median) / mad
            scores.append(min(1.0, max(0, z_score / 3)))

        # Bold text
        if block.is_bold:
            scores.append(0.3)

        # Whitespace before (headings often have vertical space)
        if block.whitespace_before > 20:
            scores.append(0.2)

        # Short line (headings rarely wrap)
        if len(block.text) < 100:
            scores.append(0.1)

        # ALL CAPS or Title Case
        if block.text.isupper() or block.text.istitle():
            scores.append(0.15)

        return min(1.0, sum(scores))

    def _estimate_level(self, font_size: float, all_sizes: list[float]) -> int:
        """Estimate heading level from font size distribution."""
        unique_sizes = sorted(set(s for s in all_sizes if s > statistics.median(all_sizes)), reverse=True)
        try:
            idx = unique_sizes.index(font_size)
            return min(idx + 1, 4)  # Cap at level 4
        except ValueError:
            return 2  # Default to section level
```

**Characteristics:**
- Variable confidence based on evidence strength
- Works without ToC or PDF outline
- Handles essays, articles, and documents with just subheadings
- May produce false positives (emphasized text that isn't a heading)

---

## Fusion Strategy

### Confidence-Weighted Voting

```python
class ConfidenceWeightedFusion(FusionStrategy):
    """Combine candidates using confidence-weighted voting."""

    def __init__(
        self,
        position_tolerance: int = 100,  # chars
        title_similarity_threshold: float = 0.8,
        min_combined_confidence: float = 0.6,
    ):
        self.position_tolerance = position_tolerance
        self.title_threshold = title_similarity_threshold
        self.min_confidence = min_combined_confidence

    def fuse(self, candidates: list[SectionCandidate]) -> list[SectionSpan]:
        # Step 1: Group candidates by approximate position
        clusters = self._cluster_by_position(candidates)

        # Step 2: For each cluster, combine or select best
        sections = []
        for cluster in clusters:
            if len(cluster) == 1:
                # Single source - use if confidence is high enough
                c = cluster[0]
                if c.confidence >= self.min_confidence:
                    sections.append(self._to_section(c))
            else:
                # Multiple sources - combine confidences
                combined = self._combine_cluster(cluster)
                if combined.confidence >= self.min_confidence:
                    sections.append(combined)

        # Step 3: Fill in end positions
        sections = sorted(sections, key=lambda s: s.start)
        for i, section in enumerate(sections):
            if i + 1 < len(sections):
                section.end = sections[i + 1].start

        return sections

    def _combine_cluster(self, cluster: list[SectionCandidate]) -> SectionSpan:
        """Combine multiple candidates for same section."""
        # Weight by confidence
        total_conf = sum(c.confidence for c in cluster)
        weighted_pos = sum(c.start * c.confidence for c in cluster) / total_conf

        # Pick best title (prefer ToC/outline over detection)
        priority = {"pdf_outline": 3, "toc_parser": 2, "heading_detection": 1}
        best = max(cluster, key=lambda c: (priority.get(c.source, 0), c.confidence))

        # Combined confidence: increases when sources agree
        # Formula: base_conf + agreement_bonus
        base_conf = max(c.confidence for c in cluster)
        agreement_bonus = 0.1 * (len(cluster) - 1)  # +0.1 per agreeing source
        combined_conf = min(1.0, base_conf + agreement_bonus)

        return SectionSpan(
            start=int(weighted_pos),
            end=None,
            title=best.title,
            level=best.level,
            confidence=combined_conf,
            sources=[c.source for c in cluster],
            toc_entry=None  # Linked later
        )
```

---

## Validation Rules

```python
class NoOverlapValidator(ValidationRule):
    """Ensure sections don't overlap incorrectly."""

    def check(self, sections: list[SectionSpan]) -> list[ValidationIssue]:
        issues = []
        for i, s1 in enumerate(sections):
            for s2 in sections[i+1:]:
                if s1.start < s2.start < s1.end:
                    issues.append(ValidationIssue(
                        type="overlap",
                        message=f"Sections '{s1.title}' and '{s2.title}' overlap",
                        sections=[s1, s2],
                        severity="warning"
                    ))
        return issues


class HierarchyValidator(ValidationRule):
    """Check that section levels are consistent."""

    def check(self, sections: list[SectionSpan]) -> list[ValidationIssue]:
        issues = []
        level_stack = []

        for section in sections:
            # Level shouldn't jump more than 1 at a time
            if level_stack and section.level > level_stack[-1] + 1:
                issues.append(ValidationIssue(
                    type="level_skip",
                    message=f"Section '{section.title}' skips levels ({level_stack[-1]} -> {section.level})",
                    sections=[section],
                    severity="info"
                ))

            # Update stack
            while level_stack and level_stack[-1] >= section.level:
                level_stack.pop()
            level_stack.append(section.level)

        return issues


class MinimumContentValidator(ValidationRule):
    """Ensure sections have reasonable content length."""

    def __init__(self, min_chars: int = 100):
        self.min_chars = min_chars

    def check(self, sections: list[SectionSpan]) -> list[ValidationIssue]:
        issues = []
        for section in sections:
            if section.end and section.end - section.start < self.min_chars:
                issues.append(ValidationIssue(
                    type="short_section",
                    message=f"Section '{section.title}' is very short ({section.end - section.start} chars)",
                    sections=[section],
                    severity="info"
                ))
        return issues
```

---

## Document Profiles

Different document types use different source configurations.

```python
@dataclass
class DocumentProfile:
    """Configuration for a document type."""

    name: str
    description: str
    sources: list[CandidateSource]
    fusion: FusionStrategy
    validators: list[ValidationRule]

    # Detection hints
    indicators: list[Callable[[RawDocument], float]]


# Standard profiles
BOOK_PROFILE = DocumentProfile(
    name="book",
    description="Multi-chapter books with ToC",
    sources=[
        PDFOutlineSource(),
        ToCParserSource(),
        HeadingDetectionSource(),
    ],
    fusion=ConfidenceWeightedFusion(min_combined_confidence=0.6),
    validators=[NoOverlapValidator(), HierarchyValidator()],
    indicators=[
        lambda doc: 0.8 if doc.page_count > 50 else 0.3,
        lambda doc: 0.9 if "contents" in doc.first_pages_text.lower() else 0.2,
    ]
)

ARTICLE_PROFILE = DocumentProfile(
    name="article",
    description="Academic articles with abstract and sections",
    sources=[
        PDFOutlineSource(),
        HeadingDetectionSource(),
    ],
    fusion=ConfidenceWeightedFusion(min_combined_confidence=0.5),
    validators=[NoOverlapValidator()],
    indicators=[
        lambda doc: 0.8 if doc.page_count < 30 else 0.3,
        lambda doc: 0.9 if "abstract" in doc.first_pages_text.lower() else 0.2,
    ]
)

ESSAY_PROFILE = DocumentProfile(
    name="essay",
    description="Essays and papers with subheadings only",
    sources=[
        HeadingDetectionSource(),
    ],
    fusion=ConfidenceWeightedFusion(min_combined_confidence=0.4),
    validators=[MinimumContentValidator(min_chars=200)],
    indicators=[
        lambda doc: 0.7 if doc.page_count < 15 else 0.2,
        lambda doc: 0.8 if not doc.has_toc_indicators else 0.3,
    ]
)

REPORT_PROFILE = DocumentProfile(
    name="report",
    description="Technical reports with numbered sections",
    sources=[
        PDFOutlineSource(),
        ToCParserSource(),
        HeadingDetectionSource(),
    ],
    fusion=ConfidenceWeightedFusion(min_combined_confidence=0.6),
    validators=[NoOverlapValidator(), HierarchyValidator()],
    indicators=[
        lambda doc: 0.8 if re.search(r'\d+\.\d+', doc.first_pages_text) else 0.2,
    ]
)

DEFAULT_PROFILE = DocumentProfile(
    name="generic",
    description="Fallback for unrecognized documents",
    sources=[
        PDFOutlineSource(),
        HeadingDetectionSource(),
    ],
    fusion=ConfidenceWeightedFusion(min_combined_confidence=0.5),
    validators=[NoOverlapValidator()],
    indicators=[]
)


def detect_profile(doc: RawDocument, profiles: list[DocumentProfile] = None) -> DocumentProfile:
    """Auto-detect the best profile for a document."""
    profiles = profiles or [BOOK_PROFILE, ARTICLE_PROFILE, ESSAY_PROFILE, REPORT_PROFILE]

    scores = []
    for profile in profiles:
        score = sum(ind(doc) for ind in profile.indicators) / max(len(profile.indicators), 1)
        scores.append((score, profile))

    best_score, best_profile = max(scores, key=lambda x: x[0])
    if best_score < 0.4:
        return DEFAULT_PROFILE
    return best_profile
```

---

## Main Orchestrator

```python
class StructureExtractor:
    """Orchestrates structure extraction with profile-based configuration."""

    def __init__(
        self,
        profile: DocumentProfile | None = None,
        feedback_log: FeedbackLog | None = None,
        pattern_library: PatternLibrary | None = None,
    ):
        self.profile = profile
        self.feedback_log = feedback_log
        self.pattern_library = pattern_library

    def extract(self, doc: RawDocument) -> StructureResult:
        # Step 1: Auto-detect profile if not provided
        profile = self.profile or detect_profile(doc)

        # Step 2: Collect candidates from all sources
        all_candidates = []
        for source in profile.sources:
            try:
                candidates = source.extract(doc)
                all_candidates.extend(candidates)
            except Exception as e:
                # Log but continue - graceful degradation
                logger.warning(f"Source {source.name} failed: {e}")

        # Step 3: Apply learned patterns (if available)
        if self.pattern_library:
            pattern_candidates = self.pattern_library.suggest(doc)
            all_candidates.extend(pattern_candidates)

        # Step 4: Fuse candidates
        sections = profile.fusion.fuse(all_candidates)

        # Step 5: Validate
        issues = []
        for validator in profile.validators:
            issues.extend(validator.check(sections))

        return StructureResult(
            sections=sections,
            candidates=all_candidates,
            validation_issues=issues,
            profile_used=profile.name,
            confidence=self._overall_confidence(sections, issues),
        )

    def _overall_confidence(
        self,
        sections: list[SectionSpan],
        issues: list[ValidationIssue]
    ) -> float:
        """Calculate overall confidence in structure extraction."""
        if not sections:
            return 0.0

        base = sum(s.confidence for s in sections) / len(sections)

        # Penalize for issues
        penalty = sum(
            0.1 if i.severity == "warning" else 0.02
            for i in issues
        )

        return max(0.0, base - penalty)
```

---

## Graceful Degradation

The system handles missing signals gracefully:

| Document Type | PDF Outline | ToC | Headings | Result |
|--------------|-------------|-----|----------|--------|
| Full book | Yes | Yes | Yes | High confidence sections |
| Book (no outline) | No | Yes | Yes | Good confidence from ToC |
| Article | Maybe | No | Yes | Heading detection only |
| Essay | No | No | Yes | Heading detection, lower confidence |
| Plain text | No | No | Maybe | Minimal or no structure |

```python
# Each source returns [] if it can't detect anything
# Fusion handles empty candidate lists gracefully
# Result includes confidence to indicate reliability
```

---

## Integration with Feedback System

See `FEEDBACK_SYSTEM.md` for full details. Key integration points:

```python
# Record human corrections
feedback_log.record(StructureCorrection(
    document_id=doc.id,
    issue_type="missing_section",
    original=None,
    corrected=SectionSpan(start=5000, end=7000, title="Chapter 2", level=1),
    source_evidence={"human_note": "Chapter 2 was missed by all sources"}
))

# Learn from corrections
pattern_library.learn_from_feedback(feedback_log.corrections)

# Apply learned patterns in future extractions
learned_candidates = pattern_library.suggest(new_doc)
```

---

## Open Questions

1. **Number of heading levels** - Cap at 4? Allow arbitrary depth?

2. **Title normalization** - How aggressively to clean up detected titles?

3. **Cross-document consistency** - Should same book series use consistent structure?

4. **Performance** - Cache intermediate results for large documents?

5. **Multi-column handling** - How to detect headings in multi-column layouts?

---

## Summary

| Component | Purpose | Extensibility |
|-----------|---------|---------------|
| CandidateSource | Extract section proposals | Add new sources |
| FusionStrategy | Combine candidates | Swap algorithms |
| ValidationRule | Check consistency | Add domain rules |
| DocumentProfile | Configure per doc type | Add new profiles |
| PatternLibrary | Learn from feedback | Automatic improvement |
