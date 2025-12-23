"""
Structure detection sources.

Each source proposes section candidates based on different evidence:
- PDFOutlineSource: PDF bookmarks (high confidence when available)
- HeadingDetectionSource: Font/style outliers (always available)
- ToCParserSource: Parsed table of contents (for title enrichment)

Based on Phase 0.5 findings: sources capture different things,
not the same structure differently. Use cascading, not fusion.
"""

from __future__ import annotations

import re
import statistics
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scholardoc.readers.pdf_reader import RawDocument, TextBlock


@dataclass
class SectionCandidate:
    """A proposed section from a detection source.

    Multiple sources can propose candidates for the same section.
    The CascadingExtractor decides which to use based on confidence.
    """

    start: int  # Position in document text
    end: int | None  # None until filled by extractor
    title: str
    level: int  # 1=chapter, 2=section, 3=subsection
    confidence: float  # 0.0 to 1.0
    source: str  # "pdf_outline", "heading_detection", "toc_parser"
    page_index: int  # PDF page where this section starts
    evidence: dict = field(default_factory=dict)


class CandidateSource(ABC):
    """Abstract base for section candidate sources."""

    name: str = "base"

    @abstractmethod
    def extract(self, doc: RawDocument) -> list[SectionCandidate]:
        """Extract section candidates from document.

        Should return empty list if source can't detect anything
        (graceful degradation).
        """
        pass


class PDFOutlineSource(CandidateSource):
    """Extract structure from PDF outline/bookmarks.

    PDF outlines are the most reliable source when present.
    Based on spike findings: 58% of PDFs have outlines, 0.95 confidence.
    """

    name = "pdf_outline"

    def __init__(self, confidence: float = 0.95):
        """Initialize with confidence level.

        Args:
            confidence: Confidence score for outline entries.
                        Default 0.95 based on spike findings.
        """
        self.confidence = confidence

    def extract(self, doc: RawDocument) -> list[SectionCandidate]:
        """Extract candidates from PDF outline."""
        if not doc.outline:
            return []  # Graceful degradation

        candidates = []
        for entry in doc.outline:
            # Map page index to text position
            position = doc.position_to_page(entry.page_index)

            candidates.append(
                SectionCandidate(
                    start=position,
                    end=None,  # Filled by CascadingExtractor
                    title=entry.title,
                    level=entry.level,
                    confidence=self.confidence,
                    source=self.name,
                    page_index=entry.page_index,
                    evidence={
                        "outline_level": entry.level,
                        "page_num": entry.page_index + 1,
                    },
                )
            )

        return candidates


class HeadingDetectionSource(CandidateSource):
    """Detect headings via statistical outlier analysis.

    Based on spike 03 findings: combined method with font size,
    bold, whitespace, and capitalization works well.

    Confidence varies from 0.5-0.8 based on evidence strength.
    """

    name = "heading_detection"

    def __init__(
        self,
        min_confidence: float = 0.5,
        max_confidence: float = 0.8,
        z_score_threshold: float = 1.5,
    ):
        """Initialize heading detector.

        Args:
            min_confidence: Minimum confidence for weak headings.
            max_confidence: Maximum confidence for strong headings.
            z_score_threshold: Font size z-score to consider heading.
        """
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence
        self.z_score_threshold = z_score_threshold

    def extract(self, doc: RawDocument) -> list[SectionCandidate]:
        """Detect headings using font statistics."""
        # Collect all text blocks
        all_blocks: list[tuple[TextBlock, int]] = []  # (block, page_idx)
        for page in doc.pages:
            for block in page.blocks:
                if block.text and len(block.text.strip()) > 0:
                    all_blocks.append((block, page.index))

        if not all_blocks:
            return []

        # Compute font statistics
        sizes = [b.font_size for b, _ in all_blocks]
        if not sizes:
            return []

        median_size = statistics.median(sizes)
        try:
            mad = self._median_absolute_deviation(sizes)
        except statistics.StatisticsError:
            mad = 1.0  # Fallback

        # Find unique sizes larger than median for level estimation
        large_sizes = sorted(set(s for s in sizes if s > median_size), reverse=True)

        candidates = []
        for block, page_idx in all_blocks:
            score, evidence = self._heading_score(block, median_size, mad)

            if score >= self.min_confidence:
                level = self._estimate_level(block.font_size, large_sizes)
                position = doc.position_to_page(page_idx)

                # Adjust confidence based on score
                confidence = min(
                    self.max_confidence,
                    self.min_confidence + (score - self.min_confidence) * 0.8,
                )

                candidates.append(
                    SectionCandidate(
                        start=position,
                        end=None,
                        title=block.text.strip(),
                        level=level,
                        confidence=confidence,
                        source=self.name,
                        page_index=page_idx,
                        evidence=evidence,
                    )
                )

        return candidates

    def _heading_score(
        self, block: TextBlock, median_size: float, mad: float
    ) -> tuple[float, dict]:
        """Score likelihood that block is a heading.

        Returns (score, evidence dict).
        """
        scores = []
        evidence = {
            "font_size": block.font_size,
            "is_bold": block.is_bold,
            "is_italic": block.is_italic,
        }

        # Font size outlier (larger = more likely heading)
        if mad > 0:
            z_score = (block.font_size - median_size) / mad
            evidence["z_score"] = round(z_score, 2)
            if z_score > self.z_score_threshold:
                scores.append(min(0.4, z_score / 5))

        # Bold text is strong indicator
        if block.is_bold:
            scores.append(0.3)

        # Short lines (headings rarely wrap)
        if len(block.text) < 100:
            scores.append(0.15)
            evidence["short_line"] = True

        # ALL CAPS
        if block.text.isupper() and len(block.text) > 3:
            scores.append(0.2)
            evidence["all_caps"] = True

        # Title Case (but not if just 1-2 words)
        if block.text.istitle() and len(block.text.split()) >= 2:
            scores.append(0.1)
            evidence["title_case"] = True

        total_score = sum(scores)
        evidence["component_scores"] = scores

        return min(1.0, total_score), evidence

    def _estimate_level(self, font_size: float, large_sizes: list[float]) -> int:
        """Estimate heading level from font size."""
        if not large_sizes:
            return 2

        try:
            idx = large_sizes.index(font_size)
            return min(idx + 1, 4)  # Cap at level 4
        except ValueError:
            # Not in list, estimate by comparison
            for i, size in enumerate(large_sizes):
                if font_size >= size:
                    return min(i + 1, 4)
            return 3  # Default to subsection

    def _median_absolute_deviation(self, data: list[float]) -> float:
        """Calculate MAD (robust measure of variability)."""
        if len(data) < 2:
            return 1.0
        median = statistics.median(data)
        deviations = [abs(x - median) for x in data]
        return statistics.median(deviations) or 1.0


class ToCParserSource(CandidateSource):
    """Parse table of contents for title enrichment.

    Based on Phase 0.5 findings: ToC parsing is fragile (0-41 entries).
    Use for title correction only, not primary section creation.

    Confidence is moderate (0.7) because parsing may have errors.
    """

    name = "toc_parser"

    def __init__(
        self,
        confidence: float = 0.7,
        max_pages_to_scan: int = 20,
    ):
        """Initialize ToC parser.

        Args:
            confidence: Confidence score for ToC entries.
            max_pages_to_scan: How many pages to check for ToC.
        """
        self.confidence = confidence
        self.max_pages_to_scan = max_pages_to_scan

    def extract(self, doc: RawDocument) -> list[SectionCandidate]:
        """Extract candidates from table of contents."""
        # Step 1: Find ToC pages
        toc_pages = self._find_toc_pages(doc)
        if not toc_pages:
            return []

        # Step 2: Parse entries from ToC pages
        entries = []
        for page_idx in toc_pages:
            page = doc.pages[page_idx]
            page_entries = self._parse_toc_entries(page.text)
            entries.extend(page_entries)

        if not entries:
            return []

        # Step 3: Resolve page references to positions
        candidates = []
        for title, page_ref, level in entries:
            # Try to find page by label
            target_page_idx = self._resolve_page_reference(doc, page_ref)
            if target_page_idx is not None:
                position = doc.position_to_page(target_page_idx)
                candidates.append(
                    SectionCandidate(
                        start=position,
                        end=None,
                        title=title,
                        level=level,
                        confidence=self.confidence,
                        source=self.name,
                        page_index=target_page_idx,
                        evidence={
                            "toc_page_ref": page_ref,
                            "resolved_page": target_page_idx,
                        },
                    )
                )

        return candidates

    def _find_toc_pages(self, doc: RawDocument) -> list[int]:
        """Detect pages that are likely table of contents."""
        candidates = []
        pages_to_check = min(self.max_pages_to_scan, len(doc.pages))

        for i in range(pages_to_check):
            text = doc.pages[i].text
            score = self._toc_likelihood(text)
            if score > 0.5:
                candidates.append(i)

        return candidates

    def _toc_likelihood(self, text: str) -> float:
        """Score how likely text is a ToC page."""
        if not text:
            return 0.0

        lower = text.lower()
        scores = []

        # Title indicators
        if "table of contents" in lower:
            scores.append(0.5)
        elif "contents" in lower:
            scores.append(0.3)

        # Dotted leaders (e.g., "Chapter 1 ......... 1")
        if re.search(r"\.{3,}", text):
            scores.append(0.3)

        # Page number references at end of lines
        lines = text.strip().split("\n")
        lines_with_page_refs = sum(
            1 for line in lines if re.search(r"\d+\s*$", line.strip())
        )
        if lines and lines_with_page_refs / len(lines) > 0.3:
            scores.append(0.3)

        return min(1.0, sum(scores))

    def _parse_toc_entries(
        self, text: str
    ) -> list[tuple[str, str, int]]:  # (title, page_ref, level)
        """Parse ToC entries from page text.

        Returns list of (title, page_reference, level) tuples.
        """
        entries = []
        lines = text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue

            # Try to match: "Title ... page_number" or "Title page_number"
            # Pattern 1: Dotted leaders
            match = re.match(r"^(.+?)\s*\.{3,}\s*(\d+)\s*$", line)
            if match:
                title, page_ref = match.groups()
                level = self._estimate_entry_level(title)
                entries.append((title.strip(), page_ref, level))
                continue

            # Pattern 2: Title followed by page number (whitespace separated)
            match = re.match(r"^(.+?)\s{2,}(\d+)\s*$", line)
            if match:
                title, page_ref = match.groups()
                # Filter out lines that are too short to be titles
                if len(title) > 3:
                    level = self._estimate_entry_level(title)
                    entries.append((title.strip(), page_ref, level))

        return entries

    def _estimate_entry_level(self, title: str) -> int:
        """Estimate heading level from ToC entry formatting."""
        # Check for indentation (leading whitespace before cleaning)
        original = title
        cleaned = title.strip()

        indent = len(original) - len(original.lstrip())
        if indent > 8:
            return 3  # Subsection
        elif indent > 4:
            return 2  # Section

        # Check for chapter/section markers
        if re.match(r"^(chapter|part)\s+", cleaned, re.IGNORECASE):
            return 1
        if re.match(r"^\d+\.\d+", cleaned):
            return 2

        return 1  # Default to chapter level

    def _resolve_page_reference(self, doc: RawDocument, page_ref: str) -> int | None:
        """Resolve a page reference string to page index.

        Handles numeric references and tries to match page labels.
        """
        # Try direct numeric interpretation
        try:
            page_num = int(page_ref)
            # PDF page numbers are often 1-based
            if 1 <= page_num <= doc.page_count:
                return page_num - 1
        except ValueError:
            pass

        # Try matching page labels
        for page in doc.pages:
            if page.label == page_ref:
                return page.index

        return None
