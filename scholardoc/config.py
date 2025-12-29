"""
Configuration for ScholarDoc document conversion.

See SPEC.md for full documentation of options.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class OCRConfig:
    """
    Configuration for OCR error correction.

    OCR correction is DISABLED by default for backward compatibility.
    Enable it explicitly when processing scanned documents.

    Example:
        >>> config = ConversionConfig(
        ...     ocr=OCRConfig(enabled=True, enable_reocr=True)
        ... )
        >>> doc = scholardoc.convert("scanned_book.pdf", config)
    """

    # Master switch - disabled by default for backward compatibility
    enabled: bool = False

    # Re-OCR options
    enable_reocr: bool = True  # Perform re-OCR on flagged words (requires GPU/Tesseract)

    # Dictionary options
    dictionary_path: Path | None = None  # Path for dictionary persistence
    persist_dictionary: bool = False  # Save learned words between sessions

    # Detection thresholds
    min_confidence_to_flag: float = 0.5  # Minimum confidence to flag word as error
    min_word_length: int = 2  # Minimum word length to check

    # Additional vocabulary (supplements built-in scholarly terms)
    additional_vocabulary: set[str] = field(default_factory=set)

    def __post_init__(self):
        """Validate configuration."""
        if self.min_confidence_to_flag < 0.0 or self.min_confidence_to_flag > 1.0:
            raise ValueError(
                f"min_confidence_to_flag must be between 0.0 and 1.0, "
                f"got {self.min_confidence_to_flag}"
            )
        if self.min_word_length < 1:
            raise ValueError(f"min_word_length must be >= 1, got {self.min_word_length}")


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

    # OCR correction (disabled by default for backward compatibility)
    ocr: OCRConfig = field(default_factory=OCRConfig)

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
