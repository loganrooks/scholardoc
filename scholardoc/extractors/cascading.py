"""
Cascading structure extractor.

Implements the cascade approach validated by Phase 0.5 spikes:
1. Primary: PDF Outline (0.95 confidence when available)
2. Secondary: Heading Detection (0.5-0.8 confidence)
3. Enrichment: ToC Parser (title correction only)
4. Fallback: Paragraph boundaries

Note: Probabilistic fusion was invalidated by 21% source agreement.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import TYPE_CHECKING

from scholardoc.extractors.sources import (
    CandidateSource,
    HeadingDetectionSource,
    PDFOutlineSource,
    SectionCandidate,
    ToCParserSource,
)
from scholardoc.extractors.validators import (
    HierarchyValidator,
    NoOverlapValidator,
    TitleQualityValidator,
    ValidationIssue,
    ValidationRule,
)
from scholardoc.models import SectionSpan

if TYPE_CHECKING:
    from scholardoc.readers.pdf_reader import RawDocument

logger = logging.getLogger(__name__)


@dataclass
class StructureResult:
    """Result of structure extraction."""

    sections: list[SectionSpan]
    candidates: list[SectionCandidate]  # All candidates from all sources
    validation_issues: list[ValidationIssue]
    primary_source: str  # Which source was primary
    confidence: float  # Overall confidence
    processing_log: list[str] = field(default_factory=list)


class CascadingExtractor:
    """Orchestrates structure extraction with cascading fallback.

    The cascade:
    1. Try PDF outline (high confidence)
    2. If no outline, use heading detection
    3. Enrich titles from ToC if available
    4. Validate and fill section boundaries

    Usage:
        extractor = CascadingExtractor()
        result = extractor.extract(raw_document)
        for section in result.sections:
            print(f"{section.title} (conf={section.confidence})")
    """

    def __init__(
        self,
        *,
        outline_source: PDFOutlineSource | None = None,
        heading_source: HeadingDetectionSource | None = None,
        toc_source: ToCParserSource | None = None,
        validators: list[ValidationRule] | None = None,
        min_confidence: float = 0.5,
        title_similarity_threshold: float = 0.8,
    ):
        """Initialize the extractor.

        Args:
            outline_source: PDF outline source (default creates one).
            heading_source: Heading detection source (default creates one).
            toc_source: ToC parser source for enrichment (default creates one).
            validators: Validation rules (default creates standard set).
            min_confidence: Minimum confidence to include a section.
            title_similarity_threshold: Threshold for title matching during enrichment.
        """
        self.outline_source = outline_source or PDFOutlineSource()
        self.heading_source = heading_source or HeadingDetectionSource()
        self.toc_source = toc_source or ToCParserSource()

        self.validators = validators or [
            NoOverlapValidator(),
            HierarchyValidator(),
            TitleQualityValidator(),
        ]

        self.min_confidence = min_confidence
        self.title_threshold = title_similarity_threshold

    def extract(self, doc: RawDocument) -> StructureResult:
        """Extract document structure using cascading approach.

        Args:
            doc: Raw document from PDF reader.

        Returns:
            StructureResult with sections, validation issues, etc.
        """
        log = []
        all_candidates = []

        # Step 1: Try PDF outline (primary source)
        outline_candidates = self._extract_safely(self.outline_source, doc, log)
        all_candidates.extend(outline_candidates)

        if outline_candidates:
            log.append(f"Found {len(outline_candidates)} sections from PDF outline")
            primary_source = "pdf_outline"
            primary_candidates = outline_candidates
        else:
            log.append("No PDF outline available, falling back to heading detection")
            primary_source = "heading_detection"
            primary_candidates = []

        # Step 2: If no outline, use heading detection
        if not primary_candidates:
            heading_candidates = self._extract_safely(self.heading_source, doc, log)
            all_candidates.extend(heading_candidates)

            if heading_candidates:
                log.append(f"Found {len(heading_candidates)} headings from font analysis")
                primary_candidates = heading_candidates
            else:
                log.append("No headings detected")

        # Step 3: Get ToC for enrichment (always try)
        toc_candidates = self._extract_safely(self.toc_source, doc, log)
        all_candidates.extend(toc_candidates)

        if toc_candidates:
            log.append(f"Found {len(toc_candidates)} ToC entries for enrichment")

        # Step 4: Convert candidates to SectionSpans
        sections = self._candidates_to_sections(
            primary_candidates, toc_candidates, doc, log
        )

        # Step 5: Validate
        all_issues = []
        for validator in self.validators:
            issues = validator.check(sections)
            all_issues.extend(issues)

        if all_issues:
            log.append(f"Validation found {len(all_issues)} issues")

        # Calculate overall confidence
        confidence = self._calculate_confidence(sections, all_issues, primary_source)

        return StructureResult(
            sections=sections,
            candidates=all_candidates,
            validation_issues=all_issues,
            primary_source=primary_source,
            confidence=confidence,
            processing_log=log,
        )

    def _extract_safely(
        self,
        source: CandidateSource,
        doc: RawDocument,
        log: list[str],
    ) -> list[SectionCandidate]:
        """Extract candidates with error handling."""
        try:
            return source.extract(doc)
        except Exception as e:
            log.append(f"Source {source.name} failed: {e}")
            logger.warning(f"Source {source.name} failed: {e}")
            return []

    def _candidates_to_sections(
        self,
        primary: list[SectionCandidate],
        toc: list[SectionCandidate],
        doc: RawDocument,
        log: list[str],
    ) -> list[SectionSpan]:
        """Convert candidates to SectionSpans with boundaries.

        - Filters by minimum confidence
        - Enriches titles from ToC when similar
        - Fills in end positions
        """
        if not primary:
            return []

        # Filter by confidence
        filtered = [c for c in primary if c.confidence >= self.min_confidence]
        if len(filtered) < len(primary):
            log.append(
                f"Filtered {len(primary) - len(filtered)} low-confidence candidates"
            )

        # Sort by position
        sorted_candidates = sorted(filtered, key=lambda c: c.start)

        # Create sections with enriched titles
        sections = []
        for i, candidate in enumerate(sorted_candidates):
            # Try to enrich title from ToC
            title = candidate.title
            enriched = self._enrich_title(candidate, toc)
            if enriched and enriched != title:
                log.append(f"Enriched title: '{title}' -> '{enriched}'")
                title = enriched

            # Calculate end position (next section start or document end)
            if i + 1 < len(sorted_candidates):
                end = sorted_candidates[i + 1].start
            else:
                end = len(doc.text)

            sections.append(
                SectionSpan(
                    start=candidate.start,
                    end=end,
                    title=title,
                    level=candidate.level,
                    confidence=candidate.confidence,
                )
            )

        return sections

    def _enrich_title(
        self,
        candidate: SectionCandidate,
        toc_candidates: list[SectionCandidate],
    ) -> str | None:
        """Try to find a better title from ToC entries.

        ToC entries often have cleaner formatting than detected headings.
        """
        if not toc_candidates:
            return None

        best_match = None
        best_ratio = 0.0

        for toc in toc_candidates:
            # Must be on same or adjacent page
            if abs(toc.page_index - candidate.page_index) > 1:
                continue

            # Compare titles
            ratio = SequenceMatcher(
                None,
                candidate.title.lower(),
                toc.title.lower(),
            ).ratio()

            if ratio > best_ratio and ratio >= self.title_threshold:
                best_ratio = ratio
                best_match = toc.title

        return best_match

    def _calculate_confidence(
        self,
        sections: list[SectionSpan],
        issues: list[ValidationIssue],
        primary_source: str,
    ) -> float:
        """Calculate overall extraction confidence."""
        if not sections:
            return 0.0

        # Base confidence from sections
        base = sum(s.confidence for s in sections) / len(sections)

        # Bonus for PDF outline (more reliable)
        if primary_source == "pdf_outline":
            base = min(1.0, base + 0.05)

        # Penalty for validation issues
        penalty = 0.0
        for issue in issues:
            if issue.severity == "warning":
                penalty += 0.05
            else:  # "info"
                penalty += 0.02

        return max(0.0, base - penalty)


def extract_structure(
    doc: RawDocument,
    min_confidence: float = 0.5,
) -> list[SectionSpan]:
    """Convenience function for structure extraction.

    Args:
        doc: Raw document from PDF reader.
        min_confidence: Minimum confidence threshold.

    Returns:
        List of detected sections.
    """
    extractor = CascadingExtractor(min_confidence=min_confidence)
    result = extractor.extract(doc)
    return result.sections
