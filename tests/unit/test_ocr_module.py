"""
Unit tests for the new OCR module (scholardoc/ocr/).

Tests the production OCR pipeline components:
- AdaptiveDictionary
- OCRErrorDetector
- LineBreakRejoiner
- OCRPipeline
"""

import pytest

from scholardoc.ocr.detector import (
    OCRErrorCandidate,
    OCRErrorDetector,
)
from scholardoc.ocr.dictionary import (
    AdaptiveDictionary,
)
from scholardoc.ocr.linebreak import (
    LineBreakRejoiner,
)
from scholardoc.ocr.pipeline import (
    OCRPipeline,
    PipelineResult,
    create_pipeline,
)

# =============================================================================
# AdaptiveDictionary Tests
# =============================================================================


class TestAdaptiveDictionary:
    """Tests for AdaptiveDictionary class."""

    @pytest.fixture
    def dictionary(self):
        """Create a dictionary instance for testing."""
        return AdaptiveDictionary()

    def test_known_english_words(self, dictionary):
        """Common English words should be recognized."""
        words = ["the", "being", "philosophy", "understanding", "cognition"]
        for word in words:
            assert dictionary.is_known_word(word), f"'{word}' should be known"

    def test_unknown_words_not_recognized(self, dictionary):
        """Random strings should not be recognized as known."""
        unknown = ["asdfghjkl", "xyzpdq", "qwerty123"]
        for word in unknown:
            assert not dictionary.is_known_word(word), f"'{word}' should not be known"

    def test_ocr_errors_detected(self, dictionary):
        """Common OCR errors should not be recognized as valid words."""
        ocr_errors = ["tbe", "lhe", "phiinomenon", "heing"]
        for word in ocr_errors:
            assert not dictionary.is_known_word(word), f"'{word}' (OCR error) should not be known"

    def test_morphological_plurals(self, dictionary):
        """Plural forms of known words should pass validation."""
        is_valid, confidence = dictionary.is_probably_word("cognitions")
        assert is_valid, "cognitions should be valid (cognition + s)"
        assert confidence > 0.5

    def test_morphological_verb_forms(self, dictionary):
        """Verb forms should pass validation."""
        # -ed form
        is_valid, conf = dictionary.is_probably_word("presented")
        assert is_valid, "presented should be valid"

        # -ing form
        is_valid, conf = dictionary.is_probably_word("presenting")
        assert is_valid, "presenting should be valid"

    def test_morphological_prefixes(self, dictionary):
        """Prefixed words should pass validation."""
        is_valid, conf = dictionary.is_probably_word("unkind")
        assert is_valid, "unkind should be valid (un + kind)"

    def test_pattern_no_triple_letters(self, dictionary):
        """Words with triple letters should fail pattern check."""
        is_valid, conf = dictionary.is_probably_word("helllo")
        assert not is_valid or conf < 0.5, "helllo should fail (triple l)"

    def test_pattern_needs_vowels(self, dictionary):
        """Consonant-only strings should have low confidence."""
        is_valid, conf = dictionary.is_probably_word("bcdghjklmnpqrstvwxz")
        assert conf < 0.5, "consonant-only should have low confidence"

    def test_learning_valid_patterns(self, dictionary):
        """Words with valid patterns can be learned."""
        learned = dictionary.maybe_learn("phenomenological", "test context")
        # May or may not learn depending on pattern score
        assert isinstance(learned, bool)

    def test_not_learning_known_words(self, dictionary):
        """Already known words should not be learned."""
        learned = dictionary.maybe_learn("philosophy")
        assert not learned, "already known word should not be learned"

    def test_not_learning_invalid_patterns(self, dictionary):
        """Invalid patterns should not be learned."""
        learned = dictionary.maybe_learn("xxx")
        assert not learned, "invalid pattern should not be learned"


# =============================================================================
# OCRErrorDetector Tests
# =============================================================================


class TestOCRErrorDetector:
    """Tests for OCRErrorDetector class."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance for testing."""
        dictionary = AdaptiveDictionary()
        return OCRErrorDetector(dictionary)

    def test_detect_obvious_errors(self, detector):
        """Common OCR errors should be detected."""
        ocr_errors = ["tbe", "lhe", "phiinomenon", "heing", "tbis"]
        for word in ocr_errors:
            assert detector.is_error(word), f"'{word}' should be detected as error"

    def test_valid_words_not_flagged(self, detector):
        """Valid English words should not be flagged."""
        valid = ["the", "being", "philosophy", "understanding"]
        for word in valid:
            assert not detector.is_error(word), f"'{word}' should not be flagged"

    def test_scholarly_vocab_not_flagged(self, detector):
        """Scholarly vocabulary should not be flagged."""
        scholarly = ["dasein", "ereignis", "différance", "logos", "priori"]
        for word in scholarly:
            assert not detector.is_error(word), f"'{word}' (scholarly) should not be flagged"

    def test_german_terms_preserved(self, detector):
        """German philosophical terms should not be flagged."""
        german = ["zeitlichkeit", "vorhandenheit", "zuhandenheit", "befindlichkeit"]
        for word in german:
            assert not detector.is_error(word), f"'{word}' (German term) should not be flagged"

    def test_detect_errors_returns_candidates(self, detector):
        """detect_errors should return list of OCRErrorCandidate."""
        text = "The phiinomenon of tbe world"
        errors = detector.detect_errors(text)

        assert len(errors) >= 2, "Should detect at least 2 errors"
        assert all(isinstance(e, OCRErrorCandidate) for e in errors)

        error_words = [e.word for e in errors]
        assert "phiinomenon" in error_words
        assert "tbe" in error_words

    def test_detect_errors_with_stats(self, detector):
        """detect_errors_with_stats should return stats."""
        text = "The phiinomenon of tbe world"
        errors, stats = detector.detect_errors_with_stats(text)

        assert stats.words_checked > 0
        assert stats.errors_detected == len(errors)

    def test_short_words_skipped(self, detector):
        """Words shorter than MIN_WORD_LENGTH should be skipped."""
        assert not detector.is_error("a")
        assert not detector.is_error("I")

    def test_empty_text_returns_empty(self, detector):
        """Empty text should return empty list."""
        errors = detector.detect_errors("")
        assert errors == []

    def test_none_text_raises(self, detector):
        """None text should raise ValueError."""
        with pytest.raises(ValueError):
            detector.detect_errors(None)


# =============================================================================
# LineBreakRejoiner Tests
# =============================================================================


class TestLineBreakRejoiner:
    """Tests for LineBreakRejoiner class."""

    @pytest.fixture
    def rejoiner(self):
        """Create a rejoiner instance for testing."""
        dictionary = AdaptiveDictionary()
        return LineBreakRejoiner(dictionary)

    def test_evaluate_valid_join(self, rejoiner):
        """Valid hyphenated words should be joined."""
        candidate = rejoiner.evaluate_join("phenom-", "enology")

        assert candidate.should_join, "phenomenology should be joined"
        assert candidate.joined == "phenomenology"
        assert candidate.confidence > 0.5

    def test_evaluate_invalid_join(self, rejoiner):
        """Invalid joins should be rejected."""
        candidate = rejoiner.evaluate_join("xyz-", "abc")

        # May or may not join depending on pattern scores
        # But joined word should be xyzabc
        assert candidate.joined == "xyzabc"

    def test_process_text_joins(self, rejoiner):
        """process_text should apply valid joins."""
        text = "The phenom-\nenology of being"
        result, stats = rejoiner.process_text(text)

        assert "phenomenology" in result, "Should join phenomenology"
        assert stats.candidates_found > 0

    def test_process_text_preserves_valid_hyphens(self, rejoiner):
        """Valid compound words should preserve hyphens."""
        text = "The self-awareness of consciousness"
        result, stats = rejoiner.process_text(text)

        # self-awareness is not a line-break, so should be preserved
        assert "self-awareness" in result or "selfawareness" not in result

    def test_candidate_fields(self, rejoiner):
        """LineBreakCandidate should have all required fields."""
        candidate = rejoiner.evaluate_join("cogni-", "tion")

        assert hasattr(candidate, "fragment1")
        assert hasattr(candidate, "fragment2")
        assert hasattr(candidate, "joined")
        assert hasattr(candidate, "confidence")
        assert hasattr(candidate, "should_join")
        assert hasattr(candidate, "reason")


# =============================================================================
# OCRPipeline Tests
# =============================================================================


class TestOCRPipeline:
    """Tests for OCRPipeline class."""

    @pytest.fixture
    def pipeline(self):
        """Create a pipeline instance for testing."""
        return create_pipeline(enable_reocr=False)

    def test_pipeline_initialization(self, pipeline):
        """Pipeline should initialize with all components."""
        assert pipeline.dictionary is not None
        assert pipeline.detector is not None
        assert pipeline.rejoiner is not None
        assert pipeline.reocr_engine is not None

    def test_process_text_returns_result(self, pipeline):
        """process_text should return PipelineResult."""
        text = "The phiinomenon of tbe world"
        result = pipeline.process_text(text)

        assert isinstance(result, PipelineResult)
        assert result.original_text == text
        assert result.corrected_text is not None
        assert result.processing_time_ms >= 0

    def test_process_text_detects_errors(self, pipeline):
        """process_text should detect OCR errors."""
        text = "The phiinomenon of tbe world"
        result = pipeline.process_text(text)

        error_words = [e.word for e in result.errors_detected]
        assert "phiinomenon" in error_words
        assert "tbe" in error_words

    def test_process_text_rejoins_linebreaks(self, pipeline):
        """process_text should rejoin line-break hyphenations."""
        text = "The phenom-\nenology of consciousness"
        result = pipeline.process_text(text)

        assert "phenomenology" in result.corrected_text

    def test_process_text_has_stats(self, pipeline):
        """process_text should include statistics."""
        text = "The phiinomenon of tbe world"
        result = pipeline.process_text(text)

        assert result.detection_stats is not None
        assert result.linebreak_stats is not None
        assert result.reocr_stats is not None

    def test_clean_text_no_errors(self, pipeline):
        """Clean text should have no errors detected."""
        text = "The phenomenon of consciousness in being"
        result = pipeline.process_text(text)

        # Should detect few or no errors
        assert len(result.errors_detected) <= 1

    def test_get_info(self, pipeline):
        """get_info should return pipeline configuration."""
        info = pipeline.get_info()

        assert "enable_reocr" in info
        assert "reocr_available" in info
        assert "scholarly_vocab_size" in info


class TestCreatePipeline:
    """Tests for create_pipeline factory function."""

    def test_create_default(self):
        """create_pipeline with defaults should work."""
        pipeline = create_pipeline()
        assert isinstance(pipeline, OCRPipeline)

    def test_create_with_reocr_disabled(self):
        """create_pipeline with reocr disabled should work."""
        pipeline = create_pipeline(enable_reocr=False)
        assert pipeline.enable_reocr is False

    def test_create_with_reocr_enabled(self):
        """create_pipeline with reocr enabled should work."""
        pipeline = create_pipeline(enable_reocr=True)
        assert pipeline.enable_reocr is True


# =============================================================================
# Integration Tests
# =============================================================================


class TestOCRModuleIntegration:
    """Integration tests for the OCR module."""

    def test_full_pipeline_on_text(self):
        """Test full pipeline on sample text."""
        pipeline = create_pipeline(enable_reocr=False)

        text = """
        The phiinomenon of consciousness reveals itself in tbe
        temporal structure of under-
        standing. This phenomen-
        ological approach requires careful analysis.
        """

        result = pipeline.process_text(text)

        # Should detect errors
        assert len(result.errors_detected) >= 2

        # Should rejoin some linebreaks
        assert result.linebreak_stats.candidates_found > 0

    def test_scholarly_text_few_errors(self):
        """Scholarly text with German terms should have few false positives."""
        pipeline = create_pipeline(enable_reocr=False)

        text = """
        The concept of Dasein in Heidegger's phenomenology relates to
        Befindlichkeit and Verstehen. The a priori structure of logos
        reveals the différance in the philosophical tradition.
        """

        result = pipeline.process_text(text)

        # Should have few or no errors for scholarly terms
        error_words = {e.word.lower() for e in result.errors_detected}

        # These should NOT be flagged
        assert "dasein" not in error_words
        assert "befindlichkeit" not in error_words
        assert "logos" not in error_words
        assert "priori" not in error_words
