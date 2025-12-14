"""
Configuration for ScholarDoc document conversion.

See SPEC.md for full documentation of options.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class ConversionConfig:
    """
    Configuration for document conversion.

    All options have sensible defaults. Create a config only
    if you need to customize behavior.

    Example:
        >>> config = ConversionConfig(
        ...     include_page_markers=True,
        ...     page_marker_style="comment"
        ... )
        >>> doc = scholardoc.convert("book.pdf", config)
    """

    # Output options
    include_metadata_frontmatter: bool = True
    include_page_markers: bool = True
    page_marker_style: Literal["comment", "heading", "inline"] = "comment"

    # Structure options
    detect_headings: bool = True
    heading_detection_strategy: Literal["font", "heuristic", "none"] = "heuristic"
    preserve_line_breaks: bool = False  # True = hard breaks, False = soft wrap

    # Page options
    page_label_source: Literal["auto", "index", "label"] = "auto"

    # Error handling
    on_extraction_error: Literal["raise", "warn", "skip"] = "warn"

    # Future phases (no-op for now, but documented for planning)
    extract_footnotes: bool = False  # Phase 2
    extract_tables: bool = False  # Phase 2

    def __post_init__(self):
        """Validate configuration."""
        valid_marker_styles = ("comment", "heading", "inline")
        if self.page_marker_style not in valid_marker_styles:
            raise ValueError(
                f"page_marker_style must be one of {valid_marker_styles}, "
                f"got {self.page_marker_style!r}"
            )

        valid_heading_strategies = ("font", "heuristic", "none")
        if self.heading_detection_strategy not in valid_heading_strategies:
            raise ValueError(
                f"heading_detection_strategy must be one of {valid_heading_strategies}, "
                f"got {self.heading_detection_strategy!r}"
            )
