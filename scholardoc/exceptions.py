"""
Exception classes for ScholarDoc.

All ScholarDoc exceptions inherit from ScholarDocError,
making it easy to catch all library errors.

Example:
    >>> try:
    ...     doc = scholardoc.convert("file.xyz")
    ... except scholardoc.UnsupportedFormatError as e:
    ...     print(f"Format not supported: {e}")
    ... except scholardoc.ScholarDocError as e:
    ...     print(f"ScholarDoc error: {e}")
"""


class ScholarDocError(Exception):
    """
    Base exception for all ScholarDoc errors.

    Catch this to handle any ScholarDoc-specific error.
    """

    pass


class UnsupportedFormatError(ScholarDocError):
    """
    Raised when document format is not supported.

    Example:
        >>> scholardoc.convert("file.docx")
        UnsupportedFormatError: Format 'docx' is not supported. Supported: pdf
    """

    pass


class ExtractionError(ScholarDocError):
    """
    Raised when extraction fails.

    This is only raised when config.on_extraction_error == "raise".
    Otherwise, extraction errors are logged as warnings.
    """

    pass


class ConfigurationError(ScholarDocError):
    """
    Raised for invalid configuration.

    Example:
        >>> ConversionConfig(page_marker_style="invalid")
        ConfigurationError: page_marker_style must be one of ('comment', 'heading', 'inline')
    """

    pass
