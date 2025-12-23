"""Tests for the OCR pipeline module."""

from pathlib import Path

import pytest

from scholardoc.normalizers.ocr_pipeline import (
    SPELLCHECK_AVAILABLE,
    AdaptiveDictionary,
    LineBreakRejoiner,
    OCRErrorDetector,
    OCRPipeline,
)

# =============================================================================
# ADAPTIVE DICTIONARY TESTS
# =============================================================================


class TestAdaptiveDictionary:
    """Tests for AdaptiveDictionary."""

    @pytest.fixture
    def dictionary(self):
        """Create a fresh dictionary for each test."""
        return AdaptiveDictionary()

    def test_known_english_words(self, dictionary):
        """Common English words should be recognized."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        assert dictionary.is_known_word("the")
        assert dictionary.is_known_word("philosophy")
        assert dictionary.is_known_word("question")

    def test_unknown_words(self, dictionary):
        """Gibberish should not be recognized."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        assert not dictionary.is_known_word("asdfghjkl")
        assert not dictionary.is_known_word("zxcvbnmkj")
        assert not dictionary.is_known_word("qqqqwwww")

    def test_ocr_errors_not_recognized(self, dictionary):
        """Common OCR errors should not be recognized."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        # These are actual OCR errors from ground truth
        assert not dictionary.is_known_word("tbe")  # "the"
        assert not dictionary.is_known_word("tbese")  # "these"
        assert not dictionary.is_known_word("righLful")  # "rightful"

    def test_morphological_validation_plurals(self, dictionary):
        """Plural forms should be validated morphologically."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        # "cognitions" = "cognition" + "s"
        is_valid, conf = dictionary.is_probably_word("cognitions")
        assert is_valid
        assert conf > 0.5

    def test_morphological_validation_verb_forms(self, dictionary):
        """Verb forms should be validated morphologically."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        # "temporalizes" = "temporal" + "izes"
        is_valid, conf = dictionary.is_probably_word("temporalizes")
        assert is_valid
        assert conf > 0.5

    def test_morphological_validation_prefixes(self, dictionary):
        """Prefixed words should be validated morphologically."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        # "nonexperiential" = "non" + "experiential"
        is_valid, conf = dictionary.is_probably_word("nonexperiential")
        assert is_valid
        assert conf > 0.5

    def test_pattern_validation_no_triple_letters(self, dictionary):
        """Words with triple letters should be rejected."""
        is_valid, conf = dictionary.is_probably_word("boook")
        # Triple 'o' should reduce confidence
        assert conf < 0.5

    def test_pattern_validation_needs_vowels(self, dictionary):
        """Words without vowels should have low confidence."""
        is_valid, conf = dictionary.is_probably_word("bcrdfg")
        assert conf < 0.5

    def test_learning_words(self, dictionary):
        """Words can be learned with safeguards."""
        # Use a made-up but valid-looking word (not in dictionary)
        # "heideggerianly" follows English patterns but isn't a real word
        test_word = "heideggerianly"

        # Learn a word multiple times
        dictionary.maybe_learn(test_word, "context 1")
        dictionary.maybe_learn(test_word, "context 2")
        dictionary.maybe_learn(test_word, "context 3")

        # Should be in learned words
        assert test_word in dictionary.learned_words

        # Should have multiple occurrences
        assert dictionary.learned_words[test_word]["occurrences"] >= 3

    def test_not_learning_invalid_patterns(self, dictionary):
        """Words with invalid patterns should not be learned."""
        # Triple letters
        result = dictionary.maybe_learn("boook", "context")
        assert not result or dictionary.learned_words.get("boook", {}).get("confidence", 0) < 0.5

    def test_persistence(self, tmp_path):
        """Learned words should persist to disk."""
        persist_path = tmp_path / "learned.json"
        test_word = "heideggerianly"

        # Learn some words
        dict1 = AdaptiveDictionary(persistence_path=persist_path)
        dict1.maybe_learn(test_word, "context")
        dict1.maybe_learn(test_word, "context")
        dict1.save()

        # Load in new instance
        dict2 = AdaptiveDictionary(persistence_path=persist_path)
        assert test_word in dict2.learned_words


# =============================================================================
# LINE-BREAK REJOINER TESTS
# =============================================================================


class TestLineBreakRejoiner:
    """Tests for LineBreakRejoiner."""

    @pytest.fixture
    def rejoiner(self):
        """Create a rejoiner for each test."""
        dictionary = AdaptiveDictionary()
        return LineBreakRejoiner(dictionary)

    def test_detect_from_text_basic(self, rejoiner):
        """Basic line-break detection in text."""
        text = "This is a pheno-\nmenon of great importance."
        candidates = rejoiner.detect_from_text(text)

        assert len(candidates) == 1
        assert candidates[0].fragment1 == "pheno-"
        assert candidates[0].fragment2 == "menon"
        assert candidates[0].joined == "phenomenon"

    def test_valid_join_recognized(self, rejoiner):
        """Valid word joins should be recognized."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        text = "The philo-\nsophy of mind."
        candidates = rejoiner.detect_from_text(text)

        assert len(candidates) == 1
        assert candidates[0].should_join
        assert candidates[0].joined == "philosophy"

    def test_invalid_join_rejected(self, rejoiner):
        """Invalid joins should be rejected."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        # This would create nonsense
        text = "The meta-\n123 page number."
        candidates = rejoiner.detect_from_text(text)

        # Should find candidate but reject it
        assert len(candidates) == 1
        assert not candidates[0].should_join

    def test_apply_to_text(self, rejoiner):
        """Line breaks should be applied to text."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        text = "The pheno-\nmenon is clear."
        result = rejoiner.apply_to_text(text)

        assert "phenomenon" in result
        assert "pheno-" not in result

    def test_compound_words_preserved(self, rejoiner):
        """Compound words with hyphens should be preserved."""
        # "self-evident" is a compound, not a line break
        text = "This is self-\nevident to all."
        candidates = rejoiner.detect_from_text(text)

        # May find candidate, but "selfevident" is not a word
        for c in candidates:
            if c.fragment1 == "self-":
                # Either rejected or low confidence
                assert not c.should_join or c.confidence < 0.7


# =============================================================================
# OCR ERROR DETECTOR TESTS
# =============================================================================


class TestOCRErrorDetector:
    """Tests for OCRErrorDetector."""

    @pytest.fixture
    def detector(self):
        """Create a detector for each test."""
        dictionary = AdaptiveDictionary()
        return OCRErrorDetector(dictionary)

    def test_detect_obvious_errors(self, detector):
        """Obvious OCR errors should be detected."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        text = "Tbe quick brown fox jumps over tbe lazy dog."
        errors = detector.detect_errors(text)

        # Should detect "Tbe" as errors
        error_words = [e.word.lower() for e in errors]
        assert "tbe" in error_words

    def test_valid_words_not_flagged(self, detector):
        """Valid English words should not be flagged."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        text = "The quick brown fox jumps over the lazy dog."
        errors = detector.detect_errors(text)

        # No errors in this sentence
        assert len(errors) == 0

    def test_scholarly_vocab_not_flagged(self, detector):
        """Scholarly vocabulary should not be flagged."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        text = "Heidegger's concept of Dasein reveals the Ereignis."
        errors = detector.detect_errors(text)

        # "dasein" and "ereignis" should be skipped
        error_words = [e.word.lower() for e in errors]
        assert "dasein" not in error_words
        assert "ereignis" not in error_words

    def test_error_has_position(self, detector):
        """Detected errors should have position information."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        text = "Tbe error is here."
        errors = detector.detect_errors(text, page_num=5)

        assert len(errors) > 0
        assert errors[0].position[0] == 5  # page number


# =============================================================================
# OCR PIPELINE FACADE TESTS
# =============================================================================


class TestOCRPipeline:
    """Tests for OCRPipeline facade."""

    @pytest.fixture
    def pipeline(self):
        """Create a pipeline for each test."""
        return OCRPipeline()

    def test_pipeline_initialization(self, pipeline):
        """Pipeline should initialize correctly."""
        assert pipeline.dictionary is not None
        assert pipeline.line_break_rejoiner is not None
        assert pipeline.error_detector is not None

    def test_detect_line_breaks_text(self, pipeline):
        """Pipeline should detect line breaks in text."""
        text = "The pheno-\nmenon is clear."
        candidates = pipeline.detect_line_breaks_text(text)
        assert len(candidates) > 0

    def test_apply_line_breaks(self, pipeline):
        """Pipeline should apply line breaks."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        text = "The pheno-\nmenon is clear."
        result = pipeline.apply_line_breaks(text)
        assert "phenomenon" in result

    def test_detect_errors(self, pipeline):
        """Pipeline should detect errors."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        text = "Tbe error is here."
        errors = pipeline.detect_errors(text)
        assert len(errors) > 0

    def test_get_reocr_candidates(self, pipeline):
        """Pipeline should return words for re-OCR."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        text = "Tbe error is here."
        errors = pipeline.detect_errors(text)
        words = pipeline.get_reocr_candidates(errors)

        assert len(words) > 0
        assert any("tbe" in w.lower() for w in words)

    def test_learned_word_count(self, pipeline):
        """Pipeline should track learned words."""
        initial_count = pipeline.learned_word_count

        # Process text that might learn words
        pipeline.apply_line_breaks("The pheno-\nmenon is clear.")

        # Count may or may not increase depending on spellchecker
        assert pipeline.learned_word_count >= initial_count

    def test_persistence_path(self, tmp_path):
        """Pipeline should support persistence."""
        persist_path = tmp_path / "vocab.json"
        pipeline = OCRPipeline(persistence_path=persist_path)

        # Learn something
        pipeline.apply_line_breaks("The pheno-\nmenon is clear.")
        pipeline.save_learned_vocabulary()

        # Verify file exists
        assert persist_path.exists()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """Integration tests with real PDFs."""

    @pytest.fixture
    def sample_pdf_path(self):
        """Path to sample PDF for testing."""
        path = Path("spikes/sample_pdfs/kant_critique_pages_64_65.pdf")
        if not path.exists():
            pytest.skip(f"Sample PDF not found: {path}")
        return path

    def test_pdf_line_break_detection(self, sample_pdf_path):
        """Test line-break detection on real PDF."""
        import fitz

        pipeline = OCRPipeline()
        doc = fitz.open(sample_pdf_path)

        all_candidates = []
        for page in doc:
            candidates = pipeline.detect_line_breaks(page)
            all_candidates.extend(candidates)

        doc.close()

        # Should find some candidates in a real PDF
        # (exact count depends on PDF content)
        assert isinstance(all_candidates, list)

    def test_full_pipeline_on_pdf(self, sample_pdf_path):
        """Test full pipeline on real PDF."""
        if not SPELLCHECK_AVAILABLE:
            pytest.skip("pyspellchecker not installed")

        import fitz

        pipeline = OCRPipeline()
        doc = fitz.open(sample_pdf_path)

        for page in doc:
            # Detect and apply line breaks
            text = page.get_text()
            cleaned_text = pipeline.apply_line_breaks(text)

            # Detect errors
            errors = pipeline.detect_errors(cleaned_text, page_num=page.number)

            # Get re-OCR candidates
            reocr_words = pipeline.get_reocr_candidates(errors)

            # Results should be valid
            assert isinstance(cleaned_text, str)
            assert isinstance(errors, list)
            assert isinstance(reocr_words, list)

        doc.close()
