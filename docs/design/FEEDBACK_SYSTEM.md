# Feedback System Design

> **Status:** Proposal
> **Created:** December 22, 2025
> **Context:** Logging human interventions and learning across documents

---

## Design Goals

1. **Track human corrections** - Know what the system got wrong
2. **Learn from mistakes** - Improve accuracy over time
3. **Cross-document patterns** - Apply learnings to new documents
4. **Audit trail** - Understand why decisions were made
5. **Non-intrusive** - Feedback is optional, system works without it

---

## Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Feedback System                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  FeedbackLog │───▶│ PatternLib   │───▶│  Extractor   │      │
│  │  (Storage)   │    │ (Learning)   │    │  (Usage)     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         ▲                                                       │
│         │                                                       │
│  ┌──────────────┐                                              │
│  │    Human     │                                              │
│  │ Corrections  │                                              │
│  └──────────────┘                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Structures

### Correction Records

```python
@dataclass
class StructureCorrection:
    """A human correction to detected structure."""

    # Identification
    id: str                          # Unique correction ID
    timestamp: datetime
    document_id: str                 # Which document
    document_hash: str               # Content hash for deduplication

    # What was wrong
    issue_type: CorrectionType       # Enum: see below
    original: SectionSpan | None     # What the system detected
    corrected: SectionSpan | None    # What it should have been

    # Context
    source_evidence: dict            # What the system saw
    human_note: str | None           # Optional explanation
    corrector_id: str | None         # Who made the correction

    # Learning metadata
    document_profile: str            # "book", "article", etc.
    source_scores: dict[str, float]  # Confidence from each source


class CorrectionType(Enum):
    """Types of structure corrections."""

    MISSING_SECTION = "missing_section"       # System missed a real section
    FALSE_SECTION = "false_section"           # System detected non-section as section
    WRONG_LEVEL = "wrong_level"               # Correct section, wrong hierarchy level
    WRONG_TITLE = "wrong_title"               # Correct section, wrong title text
    WRONG_BOUNDARY = "wrong_boundary"         # Correct section, wrong start/end
    MERGED_SECTIONS = "merged_sections"       # Two sections incorrectly merged
    SPLIT_SECTION = "split_section"           # One section incorrectly split
```

### Annotation Corrections

```python
@dataclass
class AnnotationCorrection:
    """A correction to footnote/citation detection."""

    id: str
    timestamp: datetime
    document_id: str

    issue_type: AnnotationCorrectionType
    original: FootnoteRef | CitationRef | None
    corrected: FootnoteRef | CitationRef | None

    context_text: str                # Surrounding text for pattern learning
    human_note: str | None


class AnnotationCorrectionType(Enum):
    MISSING_FOOTNOTE = "missing_footnote"
    FALSE_FOOTNOTE = "false_footnote"
    WRONG_MARKER = "wrong_marker"
    WRONG_TARGET = "wrong_target"
    MISSING_CITATION = "missing_citation"
    FALSE_CITATION = "false_citation"
    WRONG_CITATION_PARSE = "wrong_citation_parse"
```

### Quality Corrections

```python
@dataclass
class QualityCorrection:
    """A correction to OCR quality assessment."""

    id: str
    timestamp: datetime
    document_id: str
    page_label: str

    # Quality assessment disagreement
    detected_quality: float          # What system scored
    actual_quality: float            # Human assessment
    requires_reocr: bool             # Human decision

    # Context
    sample_text: str                 # Text sample for pattern analysis
    error_examples: list[str]        # Specific errors found
    human_note: str | None
```

---

## Feedback Log

```python
class FeedbackLog:
    """Persistent storage for all corrections."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self._ensure_storage()

    def record_structure(self, correction: StructureCorrection) -> str:
        """Record a structure correction. Returns correction ID."""
        correction.id = self._generate_id()
        correction.timestamp = datetime.now()
        self._append(correction)
        return correction.id

    def record_annotation(self, correction: AnnotationCorrection) -> str:
        """Record an annotation correction."""
        correction.id = self._generate_id()
        correction.timestamp = datetime.now()
        self._append(correction)
        return correction.id

    def record_quality(self, correction: QualityCorrection) -> str:
        """Record a quality assessment correction."""
        correction.id = self._generate_id()
        correction.timestamp = datetime.now()
        self._append(correction)
        return correction.id

    # Query methods
    def get_structure_corrections(
        self,
        document_id: str | None = None,
        issue_type: CorrectionType | None = None,
        since: datetime | None = None,
    ) -> list[StructureCorrection]:
        """Query structure corrections with filters."""
        ...

    def get_corrections_for_profile(
        self,
        profile: str
    ) -> list[StructureCorrection]:
        """Get all corrections for documents of a profile type."""
        ...

    def get_correction_stats(self) -> CorrectionStats:
        """Aggregate statistics about corrections."""
        ...

    # Storage implementation
    def _append(self, correction: Any) -> None:
        """Append correction to storage."""
        # JSON Lines format for append-only efficiency
        with open(self._corrections_file, 'a') as f:
            f.write(json.dumps(asdict(correction), default=str) + '\n')

    def _ensure_storage(self) -> None:
        """Create storage directory if needed."""
        self.storage_path.mkdir(parents=True, exist_ok=True)


@dataclass
class CorrectionStats:
    """Aggregate correction statistics."""

    total_corrections: int
    corrections_by_type: dict[str, int]
    corrections_by_profile: dict[str, int]
    most_common_issues: list[tuple[str, int]]
    accuracy_over_time: list[tuple[datetime, float]]
```

---

## Pattern Library

The pattern library learns from corrections to improve future extractions.

```python
class PatternLibrary:
    """Learns and applies patterns from corrections."""

    def __init__(self, feedback_log: FeedbackLog):
        self.feedback_log = feedback_log
        self._patterns: list[LearnedPattern] = []
        self._last_update: datetime | None = None

    def update_from_feedback(self) -> int:
        """Learn new patterns from recent corrections. Returns count learned."""
        corrections = self.feedback_log.get_structure_corrections(
            since=self._last_update
        )

        new_patterns = 0
        for correction in corrections:
            pattern = self._extract_pattern(correction)
            if pattern and not self._is_duplicate(pattern):
                self._patterns.append(pattern)
                new_patterns += 1

        self._last_update = datetime.now()
        return new_patterns

    def suggest(self, doc: RawDocument) -> list[SectionCandidate]:
        """Apply learned patterns to suggest section candidates."""
        candidates = []
        for pattern in self._patterns:
            if pattern.applies_to(doc):
                matches = pattern.find_matches(doc)
                for match in matches:
                    candidates.append(SectionCandidate(
                        start=match.position,
                        end=None,
                        title=match.text,
                        level=pattern.level,
                        confidence=pattern.confidence * match.match_score,
                        source="pattern_library",
                        evidence={
                            "pattern_id": pattern.id,
                            "learned_from": pattern.source_correction_id,
                            "match_score": match.match_score,
                        }
                    ))
        return candidates

    def _extract_pattern(self, correction: StructureCorrection) -> LearnedPattern | None:
        """Extract a learnable pattern from a correction."""
        if correction.issue_type == CorrectionType.MISSING_SECTION:
            # Learn what a missed heading looks like
            return self._pattern_from_missing(correction)
        elif correction.issue_type == CorrectionType.FALSE_SECTION:
            # Learn what NOT to detect
            return self._pattern_from_false_positive(correction)
        return None

    def _pattern_from_missing(self, correction: StructureCorrection) -> LearnedPattern:
        """Learn pattern from a missed section."""
        corrected = correction.corrected
        evidence = correction.source_evidence

        return LearnedPattern(
            id=f"pat_{correction.id}",
            pattern_type="heading_positive",
            level=corrected.level,
            title_pattern=self._generalize_title(corrected.title),
            formatting_hints=evidence.get("formatting", {}),
            document_profile=correction.document_profile,
            confidence=0.7,  # Start with moderate confidence
            source_correction_id=correction.id,
            created_at=datetime.now(),
            match_count=0,
            success_count=0,
        )

    def _generalize_title(self, title: str) -> str:
        """Convert specific title to generalizable regex pattern."""
        # "Chapter 1: Introduction" -> r"Chapter \d+:.*"
        # "1.2.3 Methods" -> r"\d+\.\d+\.\d+\s+.*"

        patterns = [
            (r'Chapter \d+', r'Chapter \\d+'),
            (r'\d+\.\d+\.\d+', r'\\d+\\.\\d+\\.\\d+'),
            (r'\d+\.\d+', r'\\d+\\.\\d+'),
            (r'Part [IVX]+', r'Part [IVX]+'),
        ]

        result = title
        for specific, general in patterns:
            if re.match(specific, title, re.IGNORECASE):
                result = general + r'\s*.*'
                break

        return result


@dataclass
class LearnedPattern:
    """A pattern learned from corrections."""

    id: str
    pattern_type: str                # "heading_positive", "heading_negative"
    level: int                       # Heading level this pattern indicates
    title_pattern: str               # Regex pattern for title
    formatting_hints: dict           # Font size, bold, etc.
    document_profile: str            # Which profile this applies to
    confidence: float                # How confident in this pattern
    source_correction_id: str        # Which correction taught us this
    created_at: datetime
    match_count: int                 # Times pattern matched
    success_count: int               # Times match was correct

    def applies_to(self, doc: RawDocument) -> bool:
        """Check if pattern is relevant to document."""
        # Could check profile, formatting characteristics, etc.
        return True  # Start simple

    def find_matches(self, doc: RawDocument) -> list[PatternMatch]:
        """Find text matching this pattern in document."""
        matches = []
        for block in doc.text_blocks:
            # Check title pattern
            if re.match(self.title_pattern, block.text, re.IGNORECASE):
                match_score = self._score_match(block)
                if match_score > 0.5:
                    matches.append(PatternMatch(
                        position=block.position,
                        text=block.text,
                        match_score=match_score,
                    ))
        return matches

    def _score_match(self, block: TextBlock) -> float:
        """Score how well a block matches this pattern."""
        score = 0.5  # Base for regex match

        # Bonus for formatting match
        if self.formatting_hints:
            if block.font_size >= self.formatting_hints.get("min_font_size", 0):
                score += 0.2
            if block.is_bold == self.formatting_hints.get("is_bold", False):
                score += 0.15

        return min(1.0, score)


@dataclass
class PatternMatch:
    """A match of a learned pattern in text."""

    position: int
    text: str
    match_score: float
```

---

## Cross-Document Learning

### Pattern Generalization

```python
class CrossDocumentLearner:
    """Learns patterns that generalize across documents."""

    def __init__(self, feedback_log: FeedbackLog):
        self.feedback_log = feedback_log

    def find_common_patterns(
        self,
        min_occurrences: int = 3,
        min_success_rate: float = 0.8,
    ) -> list[GeneralizedPattern]:
        """Find patterns that work across multiple documents."""

        # Group corrections by pattern similarity
        corrections = self.feedback_log.get_structure_corrections()
        clusters = self._cluster_similar_corrections(corrections)

        patterns = []
        for cluster in clusters:
            if len(cluster) >= min_occurrences:
                pattern = self._generalize_cluster(cluster)
                if pattern.estimated_success_rate >= min_success_rate:
                    patterns.append(pattern)

        return patterns

    def _cluster_similar_corrections(
        self,
        corrections: list[StructureCorrection]
    ) -> list[list[StructureCorrection]]:
        """Group corrections that seem to be the same underlying pattern."""
        # Use title similarity, level, and formatting evidence
        clusters = []

        for correction in corrections:
            added = False
            for cluster in clusters:
                if self._is_similar(correction, cluster[0]):
                    cluster.append(correction)
                    added = True
                    break

            if not added:
                clusters.append([correction])

        return clusters

    def _is_similar(self, c1: StructureCorrection, c2: StructureCorrection) -> bool:
        """Check if two corrections represent the same pattern."""
        if c1.issue_type != c2.issue_type:
            return False

        if c1.corrected and c2.corrected:
            # Same level?
            if c1.corrected.level != c2.corrected.level:
                return False

            # Similar title structure?
            t1 = self._normalize_title(c1.corrected.title)
            t2 = self._normalize_title(c2.corrected.title)
            if t1 != t2:
                return False

        return True

    def _normalize_title(self, title: str) -> str:
        """Normalize title for pattern comparison."""
        # "Chapter 1" and "Chapter 5" -> "Chapter N"
        normalized = re.sub(r'\d+', 'N', title)
        return normalized.lower().strip()


@dataclass
class GeneralizedPattern:
    """A pattern generalized from multiple documents."""

    pattern_regex: str
    level: int
    source_documents: list[str]
    correction_count: int
    estimated_success_rate: float
    formatting_profile: dict
```

---

## Feedback UI Integration

The feedback system is designed to integrate with human review workflows.

```python
class FeedbackCollector:
    """Collects feedback during human review."""

    def __init__(self, document: ScholarDocument, feedback_log: FeedbackLog):
        self.document = document
        self.feedback_log = feedback_log
        self._pending_corrections: list = []

    def report_missing_section(
        self,
        start: int,
        end: int,
        title: str,
        level: int,
        note: str | None = None,
    ) -> None:
        """Report a section the system missed."""
        self._pending_corrections.append(StructureCorrection(
            id="",
            timestamp=None,
            document_id=self.document.id,
            document_hash=self.document.content_hash,
            issue_type=CorrectionType.MISSING_SECTION,
            original=None,
            corrected=SectionSpan(start, end, title, level, 1.0, ["human"], None),
            source_evidence=self._get_evidence_at(start),
            human_note=note,
            corrector_id=None,
            document_profile=self.document.profile,
            source_scores={},
        ))

    def report_false_section(
        self,
        section: SectionSpan,
        note: str | None = None,
    ) -> None:
        """Report a detected section that isn't real."""
        self._pending_corrections.append(StructureCorrection(
            id="",
            timestamp=None,
            document_id=self.document.id,
            document_hash=self.document.content_hash,
            issue_type=CorrectionType.FALSE_SECTION,
            original=section,
            corrected=None,
            source_evidence=self._get_evidence_at(section.start),
            human_note=note,
            corrector_id=None,
            document_profile=self.document.profile,
            source_scores={s: 0.0 for s in section.sources},
        ))

    def commit(self) -> list[str]:
        """Save all pending corrections. Returns correction IDs."""
        ids = []
        for correction in self._pending_corrections:
            correction_id = self.feedback_log.record_structure(correction)
            ids.append(correction_id)
        self._pending_corrections = []
        return ids

    def _get_evidence_at(self, position: int) -> dict:
        """Gather formatting evidence at a position."""
        # This would look up the original PDF formatting
        return {}
```

---

## Storage Format

Feedback is stored in JSON Lines format for append-only efficiency:

```
.scholardoc_feedback/
  structure_corrections.jsonl
  annotation_corrections.jsonl
  quality_corrections.jsonl
  patterns.json
  stats_cache.json
```

Example `structure_corrections.jsonl`:

```json
{"id": "sc_001", "timestamp": "2025-12-22T10:00:00", "document_id": "being_and_time", "issue_type": "missing_section", "original": null, "corrected": {"start": 5000, "end": 7500, "title": "Chapter 2", "level": 1}, "human_note": "Chapter 2 was completely missed"}
{"id": "sc_002", "timestamp": "2025-12-22T10:05:00", "document_id": "critique_pure_reason", "issue_type": "wrong_level", "original": {"start": 1000, "end": 2000, "title": "Introduction", "level": 2}, "corrected": {"start": 1000, "end": 2000, "title": "Introduction", "level": 1}, "human_note": null}
```

---

## Integration Points

### With Structure Extraction

```python
# In StructureExtractor.__init__
def __init__(self, ..., feedback_log: FeedbackLog | None = None):
    self.pattern_library = PatternLibrary(feedback_log) if feedback_log else None

# In StructureExtractor.extract
if self.pattern_library:
    self.pattern_library.update_from_feedback()
    pattern_candidates = self.pattern_library.suggest(doc)
    all_candidates.extend(pattern_candidates)
```

### With Quality Filtering

```python
# Quality filter can use feedback to adjust thresholds
def adjust_thresholds_from_feedback(feedback_log: FeedbackLog):
    corrections = feedback_log.get_quality_corrections()

    # If we're flagging too many pages unnecessarily
    false_flags = [c for c in corrections if not c.requires_reocr and c.detected_quality < 0.7]
    if len(false_flags) > 10:
        # Lower the re-OCR threshold
        ...
```

---

## Privacy and Data Handling

- Corrections contain document excerpts - may have privacy implications
- Option to anonymize/hash document content
- Corrections can be kept local or shared across team
- Export/import for sharing patterns without raw corrections

```python
class FeedbackExporter:
    """Export patterns without sensitive content."""

    def export_patterns_only(self, pattern_lib: PatternLibrary) -> dict:
        """Export learned patterns without document content."""
        return {
            "version": "1.0",
            "patterns": [
                {
                    "pattern_regex": p.title_pattern,
                    "level": p.level,
                    "confidence": p.confidence,
                    "match_count": p.match_count,
                    # No document_id, no raw text
                }
                for p in pattern_lib._patterns
            ]
        }
```

---

## Summary

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| FeedbackLog | Store corrections | Append-only, queryable, persistent |
| StructureCorrection | Correction record | Full context, evidence, audit trail |
| PatternLibrary | Learn from feedback | Regex patterns, formatting hints |
| CrossDocumentLearner | Generalize patterns | Find common mistakes across docs |
| FeedbackCollector | UI integration | Pending queue, batch commit |
