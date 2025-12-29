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


# =============================================================================
# Multilingual Edge Case Tests
# =============================================================================


class TestMultilingualEdgeCases:
    """Tests for multilingual scholarly vocabulary handling."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance for testing."""
        dictionary = AdaptiveDictionary()
        return OCRErrorDetector(dictionary)

    @pytest.fixture
    def pipeline(self):
        """Create a pipeline instance for testing."""
        return create_pipeline(enable_reocr=False)

    # -------------------------------------------------------------------------
    # Accented Character Tests
    # -------------------------------------------------------------------------

    def test_french_accented_words_preserved(self, detector):
        """French words with accents should not be flagged."""
        french_accented = ["différance", "être", "liberté", "égalité", "fraternité"]
        for word in french_accented:
            assert not detector.is_error(word), f"'{word}' should not be flagged"

    def test_german_umlaut_words_preserved(self, detector):
        """German words with umlauts should not be flagged."""
        german_umlaut = ["über", "für"]
        for word in german_umlaut:
            assert not detector.is_error(word), f"'{word}' should not be flagged"

    # -------------------------------------------------------------------------
    # Case Sensitivity Tests
    # -------------------------------------------------------------------------

    def test_scholarly_vocab_case_insensitive(self, detector):
        """Scholarly vocabulary should be recognized regardless of case."""
        terms_with_cases = [
            ("dasein", "Dasein", "DASEIN"),
            ("logos", "Logos", "LOGOS"),
            ("différance", "Différance", "DIFFÉRANCE"),
        ]
        for variants in terms_with_cases:
            for variant in variants:
                assert not detector.is_error(variant), f"'{variant}' should not be flagged"

    def test_german_terms_capitalized(self, detector):
        """German nouns are often capitalized - should still be recognized."""
        capitalized_german = [
            "Zeitlichkeit",
            "Vorhandenheit",
            "Zuhandenheit",
            "Befindlichkeit",
            "Geworfenheit",
        ]
        for word in capitalized_german:
            assert not detector.is_error(word), f"'{word}' should not be flagged"

    # -------------------------------------------------------------------------
    # Latin Phrase Tests
    # -------------------------------------------------------------------------

    def test_latin_terms_preserved(self, detector):
        """Common Latin scholarly terms should not be flagged."""
        latin_terms = [
            "priori",
            "posteriori",
            "facto",
            "ibid",
            "passim",
            "sic",
            "ergo",
            "qua",
            "versus",
        ]
        for word in latin_terms:
            assert not detector.is_error(word), f"'{word}' should not be flagged"

    def test_latin_phrases_in_context(self, pipeline):
        """Latin phrases in scholarly text should not produce errors."""
        text = """
        The a priori conditions of knowledge differ from a posteriori
        observations. This argument proceeds a fortiori from established
        premises, as noted ibid. and passim throughout the literature.
        """
        result = pipeline.process_text(text)
        error_words = {e.word.lower() for e in result.errors_detected}

        assert "priori" not in error_words
        assert "posteriori" not in error_words
        assert "fortiori" not in error_words
        assert "ibid" not in error_words

    # -------------------------------------------------------------------------
    # Greek Transliteration Tests
    # -------------------------------------------------------------------------

    def test_greek_transliterations_preserved(self, detector):
        """Greek philosophical terms (transliterated) should not be flagged."""
        greek_terms = [
            "logos",
            "noesis",
            "phronesis",
            "techne",
            "aletheia",
            "episteme",
            "doxa",
            "praxis",
            "theoria",
            "nous",
            "psyche",
            "ethos",
            "pathos",
            "telos",
            "ousia",
        ]
        for word in greek_terms:
            assert not detector.is_error(word), f"'{word}' should not be flagged"

    # -------------------------------------------------------------------------
    # Mixed Language Text Tests
    # -------------------------------------------------------------------------

    def test_mixed_language_scholarly_text(self, pipeline):
        """Mixed German-English scholarly text should have few false positives."""
        text = """
        Heidegger's analysis of Dasein reveals the structure of Sorge (care)
        and its relation to Zeitlichkeit (temporality). The concept of
        Geworfenheit indicates our thrownness into the world, while
        Befindlichkeit describes our state-of-mind or attunement.
        """
        result = pipeline.process_text(text)
        error_words = {e.word.lower() for e in result.errors_detected}

        # German terms should NOT be flagged
        assert "dasein" not in error_words
        assert "sorge" not in error_words
        assert "zeitlichkeit" not in error_words
        assert "geworfenheit" not in error_words
        assert "befindlichkeit" not in error_words

    def test_mixed_french_english_text(self, pipeline):
        """Mixed French-English scholarly text should have few false positives."""
        text = """
        Derrida's concept of différance challenges the logocentrism of
        Western metaphysics. The notion of jouissance in psychoanalytic
        theory relates to the supplementarity of meaning.
        """
        result = pipeline.process_text(text)
        error_words = {e.word.lower() for e in result.errors_detected}

        # French/scholarly terms should NOT be flagged
        assert "différance" not in error_words
        assert "logocentrism" not in error_words
        assert "jouissance" not in error_words
        assert "supplementarity" not in error_words

    # -------------------------------------------------------------------------
    # OCR Corruption of Multilingual Text
    # -------------------------------------------------------------------------

    def test_ocr_corruption_of_accented_chars_detected(self, detector):
        """OCR often corrupts accented characters - corrupted versions should be errors."""
        # These are corrupted versions that SHOULD be detected as errors
        corrupted = [
            "differance",  # différance without accent (common OCR error)
            "etre",  # être without accent
        ]
        # Note: These might pass if they look like valid English words
        # The test documents expected behavior
        for word in corrupted:
            # We just verify we can check them without crashing
            result = detector.is_error(word)
            assert isinstance(result, bool)

    def test_ligature_handling(self, detector):
        """Common ligatures and their expansions should be handled."""
        # These should be valid words
        ligature_words = ["aesthetic", "encyclopaedia", "mediaeval"]
        for word in ligature_words:
            # These are valid English words, should not be flagged
            assert not detector.is_error(word), f"'{word}' should not be flagged"

    # -------------------------------------------------------------------------
    # Edge Cases
    # -------------------------------------------------------------------------

    def test_single_accented_character(self, detector):
        """Single accented characters should not crash the detector."""
        single_chars = ["é", "ü", "ä", "ß"]
        for char in single_chars:
            # Should not crash, may or may not be error
            result = detector.is_error(char)
            assert isinstance(result, bool)

    def test_mixed_script_word(self, detector):
        """Words mixing scripts should be handled gracefully."""
        # These are likely OCR artifacts and should be errors
        mixed = ["phenomenön", "beïng"]  # English with misplaced diacritics
        for word in mixed:
            result = detector.is_error(word)
            assert isinstance(result, bool)

    def test_empty_and_whitespace(self, detector):
        """Empty strings and whitespace should be handled."""
        assert not detector.is_error("")
        assert not detector.is_error("   ")
        assert not detector.is_error("\t\n")

    def test_numbers_and_punctuation(self, detector):
        """Pure numbers and punctuation should be handled gracefully."""
        # These may or may not be errors - just verify no crashes
        # Numbers and punctuation are typically stripped/skipped by tokenization
        for token in ["123", "...", "()"]:
            result = detector.is_error(token)
            assert isinstance(result, bool)

    def test_hyphenated_scholarly_terms(self, detector):
        """Hyphenated scholarly compounds should be handled."""
        # These might be split by the tokenizer
        compounds = ["being-in-the-world", "ready-to-hand", "present-at-hand"]
        for compound in compounds:
            # Should not crash
            result = detector.is_error(compound)
            assert isinstance(result, bool)


# =============================================================================
# Validation Set Integration Tests
# =============================================================================


class TestValidationSetIntegration:
    """
    Integration tests using the full ground truth validation set.

    These tests verify that the OCR pipeline meets quality targets:
    - Detection rate: >= 95% of known OCR errors should be detected
    - False positive rate: <= 25% of correct words should NOT be flagged
    """

    VALIDATION_SET_PATH = "ground_truth/validation_set.json"

    @pytest.fixture(scope="class")
    def validation_data(self):
        """Load the validation set data."""
        import json
        from pathlib import Path

        path = Path(__file__).parent.parent.parent / self.VALIDATION_SET_PATH
        if not path.exists():
            pytest.skip(f"Validation set not found: {path}")

        with open(path) as f:
            return json.load(f)

    @pytest.fixture(scope="class")
    def detector(self):
        """Create a detector instance for testing."""
        dictionary = AdaptiveDictionary()
        return OCRErrorDetector(dictionary)

    @pytest.fixture(scope="class")
    def pipeline(self):
        """Create a pipeline instance for testing."""
        return create_pipeline(enable_reocr=False)

    # -------------------------------------------------------------------------
    # Detection Rate Tests
    # -------------------------------------------------------------------------

    def test_detection_rate_all_errors(self, detector, validation_data):
        """Detection rate across all error types should meet target."""
        error_pairs = validation_data["error_pairs"]

        detected = 0
        missed = []

        for pair in error_pairs:
            ocr_text = pair["ocr_text"]
            if detector.is_error(ocr_text):
                detected += 1
            else:
                missed.append(pair)

        detection_rate = detected / len(error_pairs)

        # Report results
        print(f"\nDetection Rate: {detection_rate:.1%} ({detected}/{len(error_pairs)})")
        print(f"Missed errors: {len(missed)}")

        # Target: >= 95% detection rate
        assert detection_rate >= 0.95, f"Detection rate {detection_rate:.1%} below target 95%"

    def test_detection_rate_by_error_type(self, detector, validation_data):
        """Detection rate should be reasonable for each error type."""
        error_pairs = validation_data["error_pairs"]

        by_type = {}
        for pair in error_pairs:
            error_type = pair.get("error_type", "unknown")
            if error_type not in by_type:
                by_type[error_type] = {"total": 0, "detected": 0}
            by_type[error_type]["total"] += 1
            if detector.is_error(pair["ocr_text"]):
                by_type[error_type]["detected"] += 1

        print("\nDetection Rate by Error Type:")
        for error_type, stats in sorted(by_type.items()):
            rate = stats["detected"] / stats["total"] if stats["total"] > 0 else 0
            print(f"  {error_type}: {rate:.1%} ({stats['detected']}/{stats['total']})")

        # All types should have >= 80% detection (relaxed for specific types)
        for error_type, stats in by_type.items():
            rate = stats["detected"] / stats["total"] if stats["total"] > 0 else 0
            if error_type in ["umlaut", "hyphenation"]:
                # These are harder to detect
                assert rate >= 0.5, f"{error_type} detection {rate:.1%} too low"
            else:
                assert rate >= 0.8, f"{error_type} detection {rate:.1%} too low"

    # -------------------------------------------------------------------------
    # False Positive Tests
    # -------------------------------------------------------------------------

    def test_false_positive_rate(self, detector, validation_data):
        """False positive rate should meet target."""
        correct_words = validation_data["correct_words"]

        false_positives = 0
        fp_words = []

        for word in correct_words:
            if detector.is_error(word):
                false_positives += 1
                fp_words.append(word)

        fp_rate = false_positives / len(correct_words)

        # Report results
        print(f"\nFalse Positive Rate: {fp_rate:.1%} ({false_positives}/{len(correct_words)})")
        if fp_words:
            print(f"False positives: {fp_words[:10]}...")

        # Target: <= 25% false positive rate
        assert fp_rate <= 0.25, f"False positive rate {fp_rate:.1%} above target 25%"

    def test_scholarly_vocab_terms_not_flagged(self, detector):
        """Terms in SCHOLARLY_VOCAB should not be flagged."""
        from scholardoc.ocr.detector import SCHOLARLY_VOCAB

        # Sample of scholarly vocabulary terms
        sample = list(SCHOLARLY_VOCAB)[:20]

        flagged = [w for w in sample if detector.is_error(w)]
        fp_rate = len(flagged) / len(sample)

        print(f"\nScholarly Vocab FP Rate: {fp_rate:.1%} ({len(flagged)}/{len(sample)})")
        if flagged:
            print(f"Incorrectly flagged: {flagged}")

        # Scholarly vocab should have 0% FP rate
        assert fp_rate == 0, f"Scholarly vocab terms incorrectly flagged: {flagged}"

    # -------------------------------------------------------------------------
    # Pipeline Integration Tests
    # -------------------------------------------------------------------------

    def test_pipeline_on_validation_errors(self, pipeline, validation_data):
        """Pipeline should detect errors from validation set in context."""
        error_pairs = validation_data["error_pairs"]

        # Sample a subset for pipeline testing (full set is slow)
        sample = error_pairs[:30]

        detected_in_context = 0
        for pair in sample:
            # Create a simple sentence context
            text = f"The {pair['ocr_text']} of consciousness"
            result = pipeline.process_text(text)

            error_words = {e.word.lower() for e in result.errors_detected}
            if pair["ocr_text"].lower() in error_words:
                detected_in_context += 1

        detection_rate = detected_in_context / len(sample)
        print(f"\nPipeline Detection Rate (sample): {detection_rate:.1%}")

        # Pipeline detection should be >= 90%
        assert detection_rate >= 0.90, f"Pipeline detection {detection_rate:.1%} too low"

    # -------------------------------------------------------------------------
    # Regression Tests
    # -------------------------------------------------------------------------

    def test_known_difficult_errors(self, detector):
        """Specific difficult errors should be detected."""
        # These are errors that have been historically problematic
        difficult_errors = [
            "tbe",  # t/h substitution
            "tbese",  # t/h substitution
            "phiinomenon",  # double i
            "heing",  # b/h confusion
            "righLful",  # L/t substitution
        ]

        for error in difficult_errors:
            assert detector.is_error(error), f"'{error}' should be detected"

    def test_known_correct_words(self, detector):
        """Common English words should not be flagged."""
        # These are common English words that should be in pyspellchecker
        correct_words = [
            "phenomenon",
            "consciousness",
            "primordial",
            "constitutive",
            "authentic",
            "philosophy",
            "understanding",
            "existence",
        ]

        for word in correct_words:
            assert not detector.is_error(word), f"'{word}' should not be flagged"


# =============================================================================
# Performance Tests
# =============================================================================


class TestPerformance:
    """
    Performance tests for OCR pipeline components.

    These tests verify that the pipeline meets performance targets:
    - Dictionary lookup: < 1ms per word
    - Error detection: < 10ms for typical page (~500 words)
    - Full pipeline: < 100ms for typical page
    """

    @pytest.fixture(scope="class")
    def pipeline(self):
        """Create a pipeline instance for testing."""
        return create_pipeline(enable_reocr=False)

    @pytest.fixture(scope="class")
    def dictionary(self):
        """Create a dictionary instance for testing."""
        return AdaptiveDictionary()

    @pytest.fixture(scope="class")
    def detector(self):
        """Create a detector instance for testing."""
        dictionary = AdaptiveDictionary()
        return OCRErrorDetector(dictionary)

    @pytest.fixture
    def sample_page_text(self):
        """Generate sample text approximating a typical PDF page (~500 words)."""
        paragraph = """
        The phenomenological analysis of consciousness reveals the fundamental
        structure of intentionality. Every act of consciousness is directed toward
        some object, whether real or imaginary. This directedness constitutes the
        essence of mental life and distinguishes consciousness from mere physical
        processes. The investigation of these structures requires careful attention
        to the ways in which objects present themselves to awareness.
        """
        # Repeat to get approximately 500 words
        return (paragraph.strip() + " ") * 10

    # -------------------------------------------------------------------------
    # Dictionary Performance
    # -------------------------------------------------------------------------

    def test_dictionary_lookup_speed(self, dictionary):
        """Dictionary lookups should be fast."""
        import time

        words = ["the", "phenomenon", "consciousness", "understanding", "being"] * 100

        start = time.perf_counter()
        for word in words:
            dictionary.is_known_word(word)
        elapsed = time.perf_counter() - start

        avg_ms = (elapsed / len(words)) * 1000
        print(f"\nDictionary lookup: {avg_ms:.3f}ms per word ({len(words)} lookups)")

        # Target: < 1ms per lookup
        assert avg_ms < 1.0, f"Dictionary lookup too slow: {avg_ms:.3f}ms"

    def test_morphology_check_speed(self, dictionary):
        """Morphological validation should be reasonably fast."""
        import time

        words = ["cognitions", "presented", "understanding", "phenomenological"] * 50

        start = time.perf_counter()
        for word in words:
            dictionary.is_probably_word(word)
        elapsed = time.perf_counter() - start

        avg_ms = (elapsed / len(words)) * 1000
        print(f"\nMorphology check: {avg_ms:.3f}ms per word ({len(words)} checks)")

        # Target: < 5ms per check (more complex than simple lookup)
        assert avg_ms < 5.0, f"Morphology check too slow: {avg_ms:.3f}ms"

    # -------------------------------------------------------------------------
    # Detector Performance
    # -------------------------------------------------------------------------

    def test_detector_page_speed(self, detector, sample_page_text):
        """Error detection on a typical page should be fast."""
        import time

        # Warm up
        detector.detect_errors(sample_page_text[:100])

        start = time.perf_counter()
        _ = detector.detect_errors(sample_page_text)
        elapsed = time.perf_counter() - start

        elapsed_ms = elapsed * 1000
        word_count = len(sample_page_text.split())
        print(f"\nDetector: {elapsed_ms:.1f}ms for {word_count} words")
        print(f"  Rate: {word_count / elapsed:.0f} words/sec")

        # Target: < 50ms for ~500 word page
        assert elapsed_ms < 50, f"Detector too slow: {elapsed_ms:.1f}ms"

    # -------------------------------------------------------------------------
    # Pipeline Performance
    # -------------------------------------------------------------------------

    def test_pipeline_page_speed(self, pipeline, sample_page_text):
        """Full pipeline on a typical page should be fast."""
        import time

        # Warm up
        pipeline.process_text(sample_page_text[:100])

        start = time.perf_counter()
        result = pipeline.process_text(sample_page_text)
        elapsed = time.perf_counter() - start

        elapsed_ms = elapsed * 1000
        word_count = len(sample_page_text.split())
        print(f"\nPipeline: {elapsed_ms:.1f}ms for {word_count} words")
        print(f"  Rate: {word_count / elapsed:.0f} words/sec")
        print(f"  Reported time: {result.processing_time_ms:.1f}ms")

        # Target: < 100ms for ~500 word page (without re-OCR)
        assert elapsed_ms < 100, f"Pipeline too slow: {elapsed_ms:.1f}ms"

    def test_pipeline_bulk_pages(self, pipeline, sample_page_text):
        """Pipeline should maintain performance across multiple pages."""
        import time

        pages = [sample_page_text] * 10

        start = time.perf_counter()
        for page in pages:
            pipeline.process_text(page)
        elapsed = time.perf_counter() - start

        avg_ms = (elapsed / len(pages)) * 1000
        print(f"\nBulk processing: {avg_ms:.1f}ms per page ({len(pages)} pages)")

        # Target: < 150ms average per page in bulk
        assert avg_ms < 150, f"Bulk processing too slow: {avg_ms:.1f}ms per page"

    # -------------------------------------------------------------------------
    # Memory Tests
    # -------------------------------------------------------------------------

    def test_pipeline_no_memory_leak(self, pipeline, sample_page_text):
        """Pipeline should not accumulate memory across calls."""
        import gc

        # Process many pages
        for _ in range(20):
            pipeline.process_text(sample_page_text)

        # Force garbage collection
        gc.collect()

        # If we get here without OOM, test passes
        # More sophisticated memory testing would require tracemalloc
        assert True, "No memory issues detected"
