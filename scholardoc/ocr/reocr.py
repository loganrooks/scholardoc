"""
Hybrid Re-OCR Engine for selective text correction.

This module provides a multi-tier fallback OCR engine for re-OCRing
lines containing flagged words. It supports:
- docTR with GPU acceleration (best quality, ~0.45s/page)
- Tesseract CPU (good quality, ~1.35s/page)
- docTR CPU fallback (good quality, ~4.5s/page)
- Graceful degradation when no OCR is available

Architecture Decision: ADR-002 (line-level re-OCR, not word-level)
Line-level crops provide sufficient visual context for accurate recognition.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from PIL import Image

if TYPE_CHECKING:
    import fitz

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Performance targets
TARGET_GPU_TIME_PER_PAGE = 0.5  # seconds
TARGET_CPU_TIME_PER_PAGE = 1.5  # seconds

# Image rendering
DEFAULT_DPI = 300
MIN_LINE_HEIGHT_PX = 10  # Minimum line height to attempt re-OCR

# Confidence thresholds
MIN_CONFIDENCE_TO_REPLACE = 0.5  # Minimum confidence to replace original text


# =============================================================================
# ENGINE DETECTION
# =============================================================================


class OCREngine(Enum):
    """Available OCR engines."""

    DOCTR_GPU = "doctr_gpu"
    DOCTR_CPU = "doctr_cpu"
    TESSERACT = "tesseract"
    NONE = "none"


def _check_gpu_available() -> bool:
    """Check if CUDA GPU is available for PyTorch."""
    try:
        import torch

        available = torch.cuda.is_available()
        if available:
            logger.debug("CUDA GPU detected: %s", torch.cuda.get_device_name(0))
        return available
    except ImportError:
        logger.debug("PyTorch not installed; GPU detection unavailable")
        return False


def _check_doctr_available() -> bool:
    """Check if docTR is installed and usable."""
    try:
        from doctr.models import ocr_predictor  # noqa: F401

        return True
    except ImportError:
        logger.debug("docTR not installed")
        return False


def _check_tesseract_available() -> bool:
    """Check if Tesseract is installed and usable."""
    try:
        import pytesseract

        # Try to get version to verify installation
        pytesseract.get_tesseract_version()
        return True
    except ImportError:
        logger.debug("pytesseract not installed")
        return False
    except pytesseract.TesseractNotFoundError:
        logger.debug("Tesseract binary not found")
        return False


def detect_available_engines() -> list[OCREngine]:
    """
    Detect available OCR engines in priority order.

    Returns engines in the following priority:
    1. docTR GPU (best quality + speed)
    2. Tesseract CPU (good quality, widely available)
    3. docTR CPU (good quality, slower)

    Returns:
        List of available OCR engines in priority order.
    """
    engines = []

    has_doctr = _check_doctr_available()
    has_gpu = _check_gpu_available()
    has_tesseract = _check_tesseract_available()

    if has_doctr and has_gpu:
        engines.append(OCREngine.DOCTR_GPU)

    if has_tesseract:
        engines.append(OCREngine.TESSERACT)

    if has_doctr:
        engines.append(OCREngine.DOCTR_CPU)

    if not engines:
        logger.warning("No OCR engines available. Install pytesseract or doctr for re-OCR support.")

    return engines


# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass
class LineCoordinates:
    """Coordinates for a line of text in a PDF page."""

    x0: float
    y0: float
    x1: float
    y1: float
    page_width: float
    page_height: float

    def to_image_coords(self, dpi: int = DEFAULT_DPI) -> tuple[int, int, int, int]:
        """
        Convert PDF coordinates to image pixel coordinates.

        Args:
            dpi: Image DPI (default 300).

        Returns:
            Tuple of (left, top, right, bottom) in pixels.
        """
        scale = dpi / 72.0  # PDF points to pixels
        return (
            int(self.x0 * scale),
            int(self.y0 * scale),
            int(self.x1 * scale),
            int(self.y1 * scale),
        )


@dataclass
class ReOCRResult:
    """Result of re-OCR operation on a line."""

    original_text: str
    reocr_text: str
    confidence: float
    engine_used: OCREngine
    replaced: bool
    reason: str


@dataclass
class ReOCRStats:
    """Statistics for re-OCR operations."""

    lines_processed: int = 0
    lines_replaced: int = 0
    lines_kept_original: int = 0
    engine_used: OCREngine = OCREngine.NONE
    total_time_ms: float = 0.0


# =============================================================================
# RE-OCR ENGINE
# =============================================================================


@dataclass
class HybridReOCREngine:
    """
    Multi-tier fallback OCR engine for re-OCRing flagged text.

    Implements a 4-tier fallback strategy:
    1. docTR with GPU (best quality, ~0.45s/page)
    2. Tesseract CPU (good quality, ~1.35s/page)
    3. docTR CPU (good quality, ~4.5s/page)
    4. Skip re-OCR (graceful degradation)

    Attributes:
        preferred_engine: Force a specific engine (or "auto" for fallback).
        dpi: Image rendering DPI for re-OCR.
        min_confidence: Minimum confidence to replace original text.

    Example:
        >>> from scholardoc.ocr.reocr import HybridReOCREngine
        >>> engine = HybridReOCREngine()
        >>> result = engine.reocr_line(page_image, line_coords, "originl text")
        >>> if result.replaced:
        ...     print(f"Corrected to: {result.reocr_text}")
    """

    preferred_engine: str = "auto"
    dpi: int = DEFAULT_DPI
    min_confidence: float = MIN_CONFIDENCE_TO_REPLACE

    # Internal state
    _available_engines: list[OCREngine] = field(default_factory=list)
    _doctr_predictor: Any = field(default=None, repr=False)
    _initialized: bool = field(default=False, repr=False)

    def __post_init__(self) -> None:
        """Detect available engines."""
        self._available_engines = detect_available_engines()
        self._initialized = True

    def _get_active_engine(self) -> OCREngine:
        """Get the engine to use based on preference and availability."""
        if self.preferred_engine == "auto":
            return self._available_engines[0] if self._available_engines else OCREngine.NONE

        # Map string to engine
        engine_map = {
            "doctr_gpu": OCREngine.DOCTR_GPU,
            "doctr": OCREngine.DOCTR_GPU,  # Default doctr to GPU if available
            "tesseract": OCREngine.TESSERACT,
            "doctr_cpu": OCREngine.DOCTR_CPU,
        }

        preferred = engine_map.get(self.preferred_engine.lower(), OCREngine.NONE)
        if preferred in self._available_engines:
            return preferred

        # Fall back to auto selection
        logger.warning(
            "Preferred engine '%s' not available; falling back to auto",
            self.preferred_engine,
        )
        return self._available_engines[0] if self._available_engines else OCREngine.NONE

    def _get_doctr_predictor(self, use_gpu: bool = True) -> Any:
        """Get or initialize docTR predictor."""
        if self._doctr_predictor is not None:
            return self._doctr_predictor

        try:
            from doctr.models import ocr_predictor

            device = "cuda" if use_gpu else "cpu"
            logger.info("Initializing docTR predictor on %s...", device)
            self._doctr_predictor = ocr_predictor(pretrained=True).to(device)
            return self._doctr_predictor
        except Exception as e:
            logger.error("Failed to initialize docTR: %s", e)
            return None

    def render_page_to_image(self, page: fitz.Page) -> Image.Image:
        """
        Render a PDF page to PIL Image.

        Args:
            page: PyMuPDF page object.

        Returns:
            PIL Image of the rendered page.
        """
        mat_scale = self.dpi / 72.0
        import fitz as fitz_module

        mat = fitz_module.Matrix(mat_scale, mat_scale)
        pix = page.get_pixmap(matrix=mat)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    def crop_line_from_image(
        self, page_image: Image.Image, coords: LineCoordinates, padding: int = 5
    ) -> Image.Image | None:
        """
        Crop a line region from a page image.

        Args:
            page_image: Full page image.
            coords: Line coordinates.
            padding: Pixels to add around the crop.

        Returns:
            Cropped line image, or None if crop fails.
        """
        left, top, right, bottom = coords.to_image_coords(self.dpi)

        # Add padding
        left = max(0, left - padding)
        top = max(0, top - padding)
        right = min(page_image.width, right + padding)
        bottom = min(page_image.height, bottom + padding)

        # Validate dimensions
        if bottom - top < MIN_LINE_HEIGHT_PX:
            logger.debug("Line height too small (%d px), skipping", bottom - top)
            return None

        if right <= left:
            logger.debug("Invalid crop dimensions: left=%d, right=%d", left, right)
            return None

        try:
            return page_image.crop((left, top, right, bottom))
        except Exception as e:
            logger.warning("Failed to crop line: %s", e)
            return None

    def _reocr_with_tesseract(self, line_image: Image.Image) -> tuple[str, float]:
        """
        Re-OCR a line image with Tesseract.

        Returns:
            Tuple of (text, confidence).
        """
        try:
            import pytesseract

            # Get OCR result with confidence data
            data = pytesseract.image_to_data(
                line_image, lang="eng", output_type=pytesseract.Output.DICT
            )

            # Extract text and calculate average confidence
            words = []
            confidences = []
            for i, text in enumerate(data["text"]):
                if text.strip():
                    words.append(text)
                    conf = data["conf"][i]
                    if conf > 0:  # -1 means no confidence
                        confidences.append(conf / 100.0)

            result_text = " ".join(words)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return result_text, avg_confidence

        except Exception as e:
            logger.warning("Tesseract re-OCR failed: %s", e)
            return "", 0.0

    def _reocr_with_doctr(self, line_image: Image.Image, use_gpu: bool = True) -> tuple[str, float]:
        """
        Re-OCR a line image with docTR.

        Returns:
            Tuple of (text, confidence).
        """
        predictor = self._get_doctr_predictor(use_gpu)
        if predictor is None:
            return "", 0.0

        try:
            from doctr.io import DocumentFile

            # Convert PIL image to bytes for docTR
            buf = io.BytesIO()
            line_image.save(buf, format="PNG")
            buf.seek(0)

            # Process with docTR
            doc_input = DocumentFile.from_images([buf.read()])
            result = predictor(doc_input)

            # Extract text and confidence
            words = []
            confidences = []
            for page in result.pages:
                for block in page.blocks:
                    for line in block.lines:
                        for word in line.words:
                            words.append(word.value)
                            confidences.append(word.confidence)

            result_text = " ".join(words)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return result_text, avg_confidence

        except Exception as e:
            logger.warning("docTR re-OCR failed: %s", e)
            return "", 0.0

    def reocr_line(
        self,
        page_image: Image.Image,
        coords: LineCoordinates,
        original_text: str,
    ) -> ReOCRResult:
        """
        Re-OCR a single line and decide whether to replace.

        Args:
            page_image: Full page image.
            coords: Line coordinates.
            original_text: Original OCR text for the line.

        Returns:
            ReOCRResult with replacement decision.
        """
        engine = self._get_active_engine()

        if engine == OCREngine.NONE:
            return ReOCRResult(
                original_text=original_text,
                reocr_text="",
                confidence=0.0,
                engine_used=OCREngine.NONE,
                replaced=False,
                reason="No OCR engine available",
            )

        # Crop line from image
        line_image = self.crop_line_from_image(page_image, coords)
        if line_image is None:
            return ReOCRResult(
                original_text=original_text,
                reocr_text="",
                confidence=0.0,
                engine_used=engine,
                replaced=False,
                reason="Failed to crop line image",
            )

        # Perform re-OCR based on engine
        if engine == OCREngine.DOCTR_GPU:
            reocr_text, confidence = self._reocr_with_doctr(line_image, use_gpu=True)
        elif engine == OCREngine.DOCTR_CPU:
            reocr_text, confidence = self._reocr_with_doctr(line_image, use_gpu=False)
        elif engine == OCREngine.TESSERACT:
            reocr_text, confidence = self._reocr_with_tesseract(line_image)
        else:
            reocr_text, confidence = "", 0.0

        # Decide whether to replace
        if not reocr_text.strip():
            return ReOCRResult(
                original_text=original_text,
                reocr_text="",
                confidence=0.0,
                engine_used=engine,
                replaced=False,
                reason="Re-OCR returned empty text",
            )

        if confidence < self.min_confidence:
            return ReOCRResult(
                original_text=original_text,
                reocr_text=reocr_text,
                confidence=confidence,
                engine_used=engine,
                replaced=False,
                reason=f"Confidence {confidence:.2f} below threshold {self.min_confidence}",
            )

        # Replace if re-OCR result is different and confident
        if reocr_text.strip() != original_text.strip():
            return ReOCRResult(
                original_text=original_text,
                reocr_text=reocr_text,
                confidence=confidence,
                engine_used=engine,
                replaced=True,
                reason=f"Replaced with confidence {confidence:.2f}",
            )

        return ReOCRResult(
            original_text=original_text,
            reocr_text=reocr_text,
            confidence=confidence,
            engine_used=engine,
            replaced=False,
            reason="Re-OCR matches original",
        )

    def reocr_lines(
        self,
        page_image: Image.Image,
        lines: list[tuple[LineCoordinates, str]],
    ) -> tuple[list[ReOCRResult], ReOCRStats]:
        """
        Re-OCR multiple lines from a page.

        Args:
            page_image: Full page image.
            lines: List of (coordinates, original_text) tuples.

        Returns:
            Tuple of (results list, statistics).
        """
        import time

        start_time = time.time()
        results = []
        stats = ReOCRStats(engine_used=self._get_active_engine())

        for coords, original_text in lines:
            result = self.reocr_line(page_image, coords, original_text)
            results.append(result)

            stats.lines_processed += 1
            if result.replaced:
                stats.lines_replaced += 1
            else:
                stats.lines_kept_original += 1

        stats.total_time_ms = (time.time() - start_time) * 1000
        return results, stats

    @property
    def is_available(self) -> bool:
        """Check if any OCR engine is available."""
        return len(self._available_engines) > 0

    @property
    def active_engine(self) -> OCREngine:
        """Get the currently active engine."""
        return self._get_active_engine()

    def get_engine_info(self) -> dict[str, Any]:
        """Get information about available engines."""
        return {
            "available_engines": [e.value for e in self._available_engines],
            "active_engine": self._get_active_engine().value,
            "preferred_engine": self.preferred_engine,
            "gpu_available": _check_gpu_available(),
            "doctr_available": _check_doctr_available(),
            "tesseract_available": _check_tesseract_available(),
        }
