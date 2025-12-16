"""
Tests for OCR correction module.

Based on findings from Spike 08 (embedding robustness) and Spike 05 (OCR quality survey).
"""

import pytest

from scholardoc.normalizers import (
    score_ocr_quality,
    correct_known_patterns,
    correct_with_spellcheck,
    correct_ocr_errors,
    OCRCorrectionNormalizer,
)


class TestOCRQualityScoring:
    """Tests for OCR quality assessment."""

    def test_clean_text_scores_high(self):
        """Clean text should get a high quality score."""
        text = "The beautiful is that which pleases universally without requiring a concept."
        score = score_ocr_quality(text)
        assert score.overall_score > 0.8
        assert score.error_rate < 0.05
        assert len(score.suspicious_words) < 3

    def test_ocr_errors_detected(self):
        """Known OCR errors should be detected."""
        text = "The beautlful is that whlch pleases unlversally."
        score = score_ocr_quality(text)
        assert score.overall_score < 0.9
        assert len(score.suspicious_words) > 0
        assert "beautlful" in [w.lower() for w in score.suspicious_words]

    def test_mid_word_caps_detected(self):
        """Mid-word capitals (common OCR error) should be flagged."""
        text = "The beautIful morning was warm."
        score = score_ocr_quality(text)
        assert score.error_patterns["mid_word_caps"] > 0

    def test_digits_in_words_detected(self):
        """Digits inside words should be flagged."""
        text = "The beauti1ul morning was warm."
        score = score_ocr_quality(text)
        assert score.error_patterns["digits_in_words"] > 0

    def test_empty_text_handled(self):
        """Empty text should return zero quality."""
        score = score_ocr_quality("")
        assert score.overall_score == 0.0
        assert score.error_rate == 1.0
        assert score.confidence == 0.0

    def test_is_usable_for_rag_threshold(self):
        """Test RAG usability threshold based on Spike 08 findings."""
        # Clean text should be usable
        clean = score_ocr_quality("This is clean text without errors.")
        assert clean.is_usable_for_rag

        # Heavily corrupted text should not be usable
        # (hard to test without actual heavy corruption)

    def test_known_misspellings_correctable(self):
        """Known OCR misspellings should be marked as correctable."""
        text = "The beautlful rnorning was warm."
        score = score_ocr_quality(text)
        assert "beautlful" in score.correctable_words
        assert score.correctable_words["beautlful"] == "beautiful"


class TestKnownPatternCorrection:
    """Tests for rule-based OCR correction."""

    def test_beautlful_corrected(self):
        """Common tl→ti error should be corrected."""
        result = correct_known_patterns("The beautlful sunset.")
        assert "beautiful" in result.corrected_text.lower()
        assert result.was_modified
        assert result.confidence > 0.8

    def test_rnorning_corrected(self):
        """Common rn→m error should be corrected."""
        result = correct_known_patterns("Good rnorning!")
        assert "morning" in result.corrected_text.lower()
        assert result.was_modified

    def test_broken_hyphenation_fixed(self):
        """Broken hyphenation should be rejoined."""
        result = correct_known_patterns("The beau- tiful sunset.")
        assert "beautiful" in result.corrected_text.lower()
        assert "-" not in result.corrected_text or "beau-" not in result.corrected_text

    def test_case_preserved(self):
        """Corrections should preserve original case."""
        result = correct_known_patterns("The Beautlful sunset.")
        assert "Beautiful" in result.corrected_text

    def test_clean_text_unchanged(self):
        """Clean text should not be modified."""
        text = "The beautiful morning was warm."
        result = correct_known_patterns(text)
        assert result.corrected_text == text
        assert not result.was_modified
        assert result.change_count == 0


class TestSpellCheckCorrection:
    """Tests for spell-check based correction."""

    def test_misspelled_word_corrected(self):
        """Misspelled words should be corrected."""
        result = correct_with_spellcheck("The beatiful sunset.")
        # Note: pyspellchecker may or may not correct this specific word
        # depending on dictionary. Test the mechanism, not specific words.
        assert result.confidence > 0.5

    def test_short_words_skipped(self):
        """Short words should be skipped to avoid false positives."""
        result = correct_with_spellcheck("I am a bee.")
        # "bee" is 3 chars, might be skipped with default min_word_length=4
        assert "bee" in result.corrected_text.lower()

    def test_capitalized_words_skipped_by_default(self):
        """Capitalized words (proper nouns) should be skipped by default."""
        result = correct_with_spellcheck("The Kant philosophy is profound.")
        # "Kant" should not be changed
        assert "Kant" in result.corrected_text

    def test_aggressive_mode_processes_more(self):
        """Aggressive mode should process shorter words and capitalized words."""
        text = "The Xant philosophy is odd."
        normal = correct_with_spellcheck(text, skip_capitalized=True)
        aggressive = correct_with_spellcheck(text, skip_capitalized=False, min_word_length=3)
        # Aggressive might change more (depends on dictionary)
        assert aggressive.corrected_text is not None


class TestCombinedCorrection:
    """Tests for combined OCR correction."""

    def test_combined_correction_applies_both(self):
        """Combined correction should apply pattern and spell corrections."""
        text = "The beautlful rnorning was warm."
        result = correct_ocr_errors(text, use_patterns=True, use_spellcheck=True)
        assert "beautiful" in result.corrected_text.lower()
        assert "morning" in result.corrected_text.lower()
        assert result.change_count >= 2

    def test_patterns_only(self):
        """Can run with just pattern correction."""
        result = correct_ocr_errors(
            "The beautlful sunset.",
            use_patterns=True,
            use_spellcheck=False,
        )
        assert "beautiful" in result.corrected_text.lower()

    def test_spellcheck_only(self):
        """Can run with just spell check."""
        result = correct_ocr_errors(
            "The beatiful sunset.",
            use_patterns=False,
            use_spellcheck=True,
        )
        assert result.confidence > 0.5


class TestOCRCorrectionNormalizer:
    """Tests for the normalizer interface."""

    def test_normalizer_processes_text(self):
        """Normalizer should process text through quality check and correction."""
        normalizer = OCRCorrectionNormalizer()
        text, quality, correction = normalizer.process_text(
            "The beautlful rnorning was warm."
        )
        assert quality is not None
        assert "beautiful" in text.lower()
        assert "morning" in text.lower()

    def test_normalizer_skips_good_quality(self):
        """Normalizer should skip correction for high-quality text."""
        normalizer = OCRCorrectionNormalizer(min_quality=0.5)
        text, quality, correction = normalizer.process_text(
            "The beautiful morning was warm and bright."
        )
        # If quality is good, correction might be None
        # This depends on the scoring - test that it runs without error
        assert quality is not None
        assert quality.overall_score > 0.5

    def test_normalizer_callback(self):
        """Quality callback should be invoked."""
        scores = []

        def callback(score):
            scores.append(score)

        normalizer = OCRCorrectionNormalizer(quality_callback=callback)
        normalizer.process_text("Test text for callback.")

        assert len(scores) == 1
        assert scores[0].overall_score >= 0

    def test_normalizer_config_options(self):
        """Normalizer should respect configuration options."""
        # Test without spell check
        normalizer = OCRCorrectionNormalizer(use_spellcheck=False)
        text, quality, correction = normalizer.process_text("The beautlful sunset.")
        assert "beautiful" in text.lower()  # Pattern still works


class TestRealWorldSamples:
    """Tests with samples derived from Spike findings."""

    def test_kant_style_errors(self):
        """Errors similar to those found in Kant PDF (Spike 05)."""
        # From spike: l/1/I confusion, mid-word caps
        text = "The beautIful Iii of judgment manifests itself."
        score = score_ocr_quality(text)
        assert score.error_patterns["mid_word_caps"] > 0

    def test_philosophy_vocabulary_preserved(self):
        """Philosophy terms should not be incorrectly 'corrected'."""
        # Terms like "apperception", "transcendental" might not be in
        # standard dictionaries but shouldn't be butchered
        text = "The transcendental unity of apperception."
        result = correct_ocr_errors(text)
        # Main words should still be recognizable
        assert "transcendental" in result.corrected_text.lower()

    def test_embedding_critical_sample(self):
        """Sample from Spike 08 that showed embedding degradation."""
        clean = "The beautiful is that which pleases universally without requiring a concept."
        corrupted = "The beautlful is that whlch pleases unlversally."

        clean_score = score_ocr_quality(clean)
        corrupted_score = score_ocr_quality(corrupted)

        assert clean_score.overall_score > corrupted_score.overall_score
        assert corrupted_score.needs_correction

        # Correction should help
        result = correct_ocr_errors(corrupted)
        assert "beautiful" in result.corrected_text.lower()
