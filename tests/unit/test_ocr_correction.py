"""
Tests for OCR correction module.

Based on findings from Spike 08 (embedding robustness) and Spike 05 (OCR quality survey).
"""

import pytest

from scholardoc.normalizers import (
    WORD_FREQUENCY_AVAILABLE,
    AnalyzedCorrectionResult,
    CorrectionCandidate,
    # New confidence-based correction system
    CorrectionConfig,
    OCRCorrectionNormalizer,
    analyze_correction,
    correct_known_patterns,
    correct_ocr_errors,
    correct_with_analysis,
    correct_with_spellcheck,
    get_word_frequency,
    score_ocr_quality,
)

# Check for optional dependencies
try:
    from spellchecker import SpellChecker
    HAS_SPELLCHECKER = True
except ImportError:
    HAS_SPELLCHECKER = False

# Skip decorators for optional dependencies
requires_spellchecker = pytest.mark.skipif(
    not HAS_SPELLCHECKER,
    reason="pyspellchecker not installed"
)
requires_wordfreq = pytest.mark.skipif(
    not WORD_FREQUENCY_AVAILABLE,
    reason="wordfreq not installed (multilingual extra)"
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


@requires_spellchecker
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
        # Run both modes - aggressive processes more aggressively
        correct_with_spellcheck(text, skip_capitalized=True)  # Normal mode
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
        text, quality, correction = normalizer.process_text("The beautlful rnorning was warm.")
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


# =============================================================================
# NEW: Tests for Confidence-Based Correction System
# =============================================================================


class TestCorrectionConfig:
    """Tests for CorrectionConfig dataclass."""

    def test_default_config_values(self):
        """Default config should have sensible values."""
        config = CorrectionConfig()
        assert config.apply_threshold == 0.7
        assert config.review_threshold == 0.3
        assert config.skip_threshold == 0.1
        assert config.max_edit_distance == 2
        assert config.language == "en"

    def test_conservative_preset(self):
        """Conservative preset should have stricter thresholds."""
        config = CorrectionConfig.conservative()
        assert config.apply_threshold >= 0.85
        assert config.max_edit_distance == 1
        assert config.apply_threshold > CorrectionConfig().apply_threshold

    def test_balanced_preset(self):
        """Balanced preset should match defaults."""
        config = CorrectionConfig.balanced()
        default = CorrectionConfig()
        assert config.apply_threshold == default.apply_threshold
        assert config.review_threshold == default.review_threshold

    def test_aggressive_preset(self):
        """Aggressive preset should have looser thresholds."""
        config = CorrectionConfig.aggressive()
        assert config.apply_threshold <= 0.5
        assert config.max_edit_distance >= 3
        assert config.apply_threshold < CorrectionConfig().apply_threshold

    def test_config_validation_valid(self):
        """Valid config should pass validation."""
        config = CorrectionConfig(
            apply_threshold=0.8,
            review_threshold=0.4,
            skip_threshold=0.1,
        )
        config.validate()  # Should not raise

    def test_config_validation_invalid_threshold_order(self):
        """Thresholds in wrong order should fail validation."""
        config = CorrectionConfig(
            apply_threshold=0.3,  # Lower than review!
            review_threshold=0.5,
            skip_threshold=0.1,
        )
        with pytest.raises(ValueError, match="Thresholds must be"):
            config.validate()

    def test_config_validation_invalid_edit_distance(self):
        """Invalid max_edit_distance should fail validation."""
        config = CorrectionConfig(max_edit_distance=0)
        with pytest.raises(ValueError, match="max_edit_distance"):
            config.validate()

    def test_custom_weights(self):
        """Custom weights should be accepted."""
        config = CorrectionConfig(
            frequency_weight=0.5,
            edit_distance_weight=0.3,
            ambiguity_weight=0.1,
            foreign_marker_weight=0.05,
            first_letter_weight=0.05,
        )
        assert config.frequency_weight == 0.5
        assert config.edit_distance_weight == 0.3


@requires_wordfreq
class TestWordFrequency:
    """Tests for word frequency utilities."""

    def test_word_frequency_available(self):
        """Word frequency should be available with multilingual extra."""
        assert WORD_FREQUENCY_AVAILABLE is True

    def test_real_word_has_frequency(self):
        """Real words should have non-zero frequency."""
        freq = get_word_frequency("beautiful")
        assert freq > 0
        # "beautiful" is a common word, should have zipf > 4
        assert freq > 4

    def test_ocr_error_has_zero_frequency(self):
        """OCR errors should have zero frequency."""
        freq = get_word_frequency("beautlful")
        assert freq == 0

    def test_common_words_higher_frequency(self):
        """Common words should have higher frequency than rare words."""
        the_freq = get_word_frequency("the")
        philosophy_freq = get_word_frequency("philosophy")
        assert the_freq > philosophy_freq

    def test_frequency_language_parameter(self):
        """Should accept language parameter."""
        # German word
        freq_de = get_word_frequency("und", "de")
        freq_en = get_word_frequency("und", "en")
        # "und" is common in German, rare in English
        assert freq_de > freq_en


@requires_spellchecker
class TestAnalyzeCorrection:
    """Tests for analyze_correction function."""

    def test_correct_word_returns_none(self):
        """Words in dictionary should return None (no correction needed)."""

        spell = SpellChecker()
        result = analyze_correction("beautiful", spell)
        assert result is None

    def test_scholarly_word_returns_none(self):
        """Scholarly vocabulary words should return None."""

        spell = SpellChecker()
        result = analyze_correction("dasein", spell)
        assert result is None

    def test_ocr_error_returns_candidate(self):
        """OCR errors should return a CorrectionCandidate."""

        spell = SpellChecker()
        result = analyze_correction("beautlful", spell)
        assert result is not None
        assert isinstance(result, CorrectionCandidate)
        assert result.original == "beautlful"
        assert result.suggested == "beautiful"

    def test_clear_error_high_confidence(self):
        """Clear OCR errors should have high confidence."""

        spell = SpellChecker()
        result = analyze_correction("beautlful", spell)
        assert result.confidence >= 0.9
        assert result.is_safe

    def test_ambiguous_correction_lower_confidence(self):
        """Ambiguous corrections should have lower confidence."""

        spell = SpellChecker()
        # "teh" has many possible corrections (the, tea, ten, etc.)
        result = analyze_correction("teh", spell)
        if result:
            # Should flag ambiguity concern
            assert result.candidate_count > 1

    def test_config_affects_scoring(self):
        """Different configs should affect confidence scores."""

        spell = SpellChecker()

        balanced = CorrectionConfig.balanced()
        aggressive = CorrectionConfig.aggressive()

        result_balanced = analyze_correction("struktur", spell, balanced)
        result_aggressive = analyze_correction("struktur", spell, aggressive)

        # Both should find "structure" but may have different confidence
        if result_balanced and result_aggressive:
            assert result_balanced.suggested == result_aggressive.suggested

    def test_foreign_suffix_flagged(self):
        """Words with foreign suffixes should be flagged."""

        spell = SpellChecker()
        # Word ending in German suffix "-ung"
        result = analyze_correction("bildung", spell)
        # If there's a correction candidate, it should note concerns
        # (exact behavior depends on dictionary and whether "bildung" is known)
        if result is not None:
            assert isinstance(result, CorrectionCandidate)
            # Concerns list exists even if empty
            assert isinstance(result.concerns, list)


class TestCorrectWithAnalysis:
    """Tests for correct_with_analysis function."""

    def test_returns_analyzed_result(self):
        """Should return AnalyzedCorrectionResult."""
        result = correct_with_analysis("The beautlful sunset.")
        assert isinstance(result, AnalyzedCorrectionResult)
        assert result.original_text == "The beautlful sunset."

    def test_applies_high_confidence_corrections(self):
        """High confidence corrections should be applied."""
        result = correct_with_analysis("The beautlful sunset.")
        assert "beautiful" in result.corrected_text.lower()
        assert len(result.applied_corrections) > 0

    def test_categorizes_corrections(self):
        """Corrections should be categorized by confidence."""
        text = "The beautlful phenomenology of dasein reveals the struktur."
        result = correct_with_analysis(text)

        # Should have some corrections
        total = (
            len(result.applied_corrections)
            + len(result.flagged_corrections)
            + len(result.skipped_corrections)
        )
        assert total > 0

        # Applied should have high confidence
        for c in result.applied_corrections:
            assert c.confidence >= 0.7

    def test_config_thresholds_respected(self):
        """Config thresholds should affect categorization."""
        text = "The beautlful phenomenology."

        # Conservative: higher threshold
        conservative = CorrectionConfig.conservative()
        result_cons = correct_with_analysis(text, conservative)

        # Aggressive: lower threshold
        aggressive = CorrectionConfig.aggressive()
        result_agg = correct_with_analysis(text, aggressive)

        # Aggressive should apply at least as many corrections
        assert len(result_agg.applied_corrections) >= len(result_cons.applied_corrections)

    def test_overall_confidence_calculated(self):
        """Overall confidence should be calculated from applied corrections."""
        result = correct_with_analysis("The beautlful phslosophy.")
        assert 0 <= result.overall_confidence <= 1

        # If corrections applied, confidence should reflect them
        if result.applied_corrections:
            avg_conf = sum(c.confidence for c in result.applied_corrections) / len(
                result.applied_corrections
            )
            assert abs(result.overall_confidence - avg_conf) < 0.01

    def test_scholarly_vocabulary_preserved(self):
        """Scholarly terms should not be corrected."""
        text = "The phenomenology of dasein and the cogito."
        result = correct_with_analysis(text)

        # These terms should remain unchanged
        assert "dasein" in result.corrected_text.lower()
        assert "cogito" in result.corrected_text.lower()
        assert "phenomenology" in result.corrected_text.lower()

    def test_correction_count_property(self):
        """correction_count property should match applied corrections."""
        result = correct_with_analysis("The beautlful rnorning.")
        assert result.correction_count == len(result.applied_corrections)


class TestCorrectionCandidate:
    """Tests for CorrectionCandidate dataclass."""

    def test_is_safe_property(self):
        """is_safe should check confidence and edit distance."""
        safe = CorrectionCandidate(
            original="beautlful",
            suggested="beautiful",
            confidence=0.9,
            edit_distance=1,
            candidate_count=1,
        )
        assert safe.is_safe is True

        unsafe = CorrectionCandidate(
            original="xyzzy",
            suggested="fuzzy",
            confidence=0.4,
            edit_distance=3,
            candidate_count=10,
        )
        assert unsafe.is_safe is False

    def test_needs_review_property(self):
        """needs_review should identify medium confidence corrections."""
        needs_review = CorrectionCandidate(
            original="kategorie",
            suggested="category",
            confidence=0.5,
            edit_distance=2,
            candidate_count=3,
        )
        assert needs_review.needs_review is True
        assert needs_review.is_safe is False
        assert needs_review.should_skip is False

    def test_should_skip_property(self):
        """should_skip should identify low confidence corrections."""
        skip = CorrectionCandidate(
            original="xyz",
            suggested="xxy",
            confidence=0.1,
            edit_distance=1,
            candidate_count=20,
        )
        assert skip.should_skip is True

    def test_concerns_list(self):
        """Concerns should be stored in list."""
        candidate = CorrectionCandidate(
            original="test",
            suggested="test2",
            confidence=0.5,
            edit_distance=1,
            candidate_count=5,
            concerns=["first letter changed", "ambiguous"],
        )
        assert len(candidate.concerns) == 2
        assert "first letter changed" in candidate.concerns


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""

    def test_german_philosophy_text(self):
        """German philosophical terms should be handled appropriately."""
        text = "Heidegger's analysis of dasein and Sein reveals the struktur of Being."

        # Conservative should preserve German terms
        conservative = CorrectionConfig.conservative()
        result = correct_with_analysis(text, conservative)

        assert "dasein" in result.corrected_text.lower()
        # "struktur" might be flagged but not aggressively corrected

    def test_mixed_language_scholarly_text(self):
        """Mixed language scholarly text should be handled carefully."""
        text = "The cogito ergo sum of Descartes and the Kritik of Kant."
        result = correct_with_analysis(text)

        # Latin and German terms should be preserved
        assert "cogito" in result.corrected_text.lower()
        # "Kritik" might or might not be preserved depending on vocabulary

    def test_heavily_corrupted_text(self):
        """Heavily corrupted text should still be processable."""
        text = "Teh beautlful phslosophy of rnorning reveals struktur."
        result = correct_with_analysis(text)

        # Should make some corrections
        assert result.correction_count > 0
        # Should report overall confidence
        assert result.overall_confidence > 0

    def test_clean_text_unchanged(self):
        """Clean text should not be modified."""
        text = "The beautiful philosophy of morning reveals structure."
        result = correct_with_analysis(text)

        assert result.corrected_text == text
        assert result.correction_count == 0
        assert result.overall_confidence == 1.0
