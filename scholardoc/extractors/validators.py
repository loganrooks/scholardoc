"""
Validation rules for structure extraction.

Validators check extracted sections for consistency and quality.
Issues are reported but don't block extraction (graceful degradation).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scholardoc.models import SectionSpan


@dataclass
class ValidationIssue:
    """A validation problem found in extracted structure."""

    type: str  # "overlap", "level_skip", "short_section", etc.
    message: str
    severity: str  # "warning", "info"
    section_titles: list[str]  # Affected section titles


class ValidationRule(ABC):
    """Abstract base for validation rules."""

    name: str = "base"

    @abstractmethod
    def check(self, sections: list[SectionSpan]) -> list[ValidationIssue]:
        """Check sections for issues.

        Returns list of issues found (empty if all good).
        """
        pass


class NoOverlapValidator(ValidationRule):
    """Ensure sections don't overlap incorrectly.

    Sibling sections should not overlap. Nested sections are allowed.
    """

    name = "no_overlap"

    def check(self, sections: list[SectionSpan]) -> list[ValidationIssue]:
        """Check for overlapping sections at same level."""
        issues = []

        # Group by level
        by_level: dict[int, list[SectionSpan]] = {}
        for section in sections:
            if section.level not in by_level:
                by_level[section.level] = []
            by_level[section.level].append(section)

        # Check each level for overlaps
        for _level, level_sections in by_level.items():
            sorted_sections = sorted(level_sections, key=lambda s: s.start)

            for i, s1 in enumerate(sorted_sections[:-1]):
                s2 = sorted_sections[i + 1]

                # Check if s1's end overlaps with s2's start
                if s1.end is not None and s1.end > s2.start:
                    issues.append(
                        ValidationIssue(
                            type="overlap",
                            message=f"Sections overlap: '{s1.title}' ends at {s1.end}, "
                            f"'{s2.title}' starts at {s2.start}",
                            severity="warning",
                            section_titles=[s1.title, s2.title],
                        )
                    )

        return issues


class HierarchyValidator(ValidationRule):
    """Check that section levels are consistent.

    Levels shouldn't skip (e.g., 1 -> 3 without 2).
    """

    name = "hierarchy"

    def check(self, sections: list[SectionSpan]) -> list[ValidationIssue]:
        """Check for level hierarchy issues."""
        issues = []

        if not sections:
            return issues

        sorted_sections = sorted(sections, key=lambda s: s.start)
        prev_level = 0

        for section in sorted_sections:
            # Level shouldn't jump more than 1 at a time going deeper
            if section.level > prev_level + 1:
                issues.append(
                    ValidationIssue(
                        type="level_skip",
                        message=f"Section '{section.title}' skips levels "
                        f"({prev_level} -> {section.level})",
                        severity="info",
                        section_titles=[section.title],
                    )
                )

            prev_level = section.level

        return issues


class MinimumContentValidator(ValidationRule):
    """Ensure sections have reasonable content length.

    Very short sections may indicate false positive headings.
    """

    name = "minimum_content"

    def __init__(self, min_chars: int = 100):
        """Initialize validator.

        Args:
            min_chars: Minimum characters for a valid section.
        """
        self.min_chars = min_chars

    def check(self, sections: list[SectionSpan]) -> list[ValidationIssue]:
        """Check for very short sections."""
        issues = []

        for section in sections:
            if section.end is not None:
                length = section.end - section.start
                if length < self.min_chars:
                    issues.append(
                        ValidationIssue(
                            type="short_section",
                            message=f"Section '{section.title}' is very short "
                            f"({length} chars < {self.min_chars})",
                            severity="info",
                            section_titles=[section.title],
                        )
                    )

        return issues


class TitleQualityValidator(ValidationRule):
    """Check section titles for quality issues.

    Detects potential false positives like single words or numbers.
    """

    name = "title_quality"

    def __init__(self, min_title_length: int = 3, max_title_length: int = 200):
        """Initialize validator.

        Args:
            min_title_length: Minimum characters for valid title.
            max_title_length: Maximum characters for valid title.
        """
        self.min_title_length = min_title_length
        self.max_title_length = max_title_length

    def check(self, sections: list[SectionSpan]) -> list[ValidationIssue]:
        """Check section titles for quality."""
        issues = []

        for section in sections:
            title = section.title.strip()

            # Too short
            if len(title) < self.min_title_length:
                issues.append(
                    ValidationIssue(
                        type="short_title",
                        message=f"Section title '{title}' is too short",
                        severity="info",
                        section_titles=[title],
                    )
                )

            # Too long (probably extracted wrong text)
            elif len(title) > self.max_title_length:
                issues.append(
                    ValidationIssue(
                        type="long_title",
                        message=f"Section title is too long ({len(title)} chars)",
                        severity="warning",
                        section_titles=[title[:50] + "..."],
                    )
                )

            # Just a number
            elif title.isdigit():
                issues.append(
                    ValidationIssue(
                        type="numeric_title",
                        message=f"Section title '{title}' is just a number",
                        severity="info",
                        section_titles=[title],
                    )
                )

        return issues
