# Multi-Stage Quality Filtering

> **Status:** Proposal
> **Created:** December 19, 2025
> **Context:** Efficiently identify pages needing neural OCR without processing everything

## The Insight

Use spell-check as a **filter**, not a **corrector**:
- High unknown word rate → flag for re-OCR
- Never auto-correct (avoids 41% damage risk)
- Reduces expensive neural OCR to only pages that need it

---

## Empirical Validation (Spike 14)

### Cross-Document Results

| Document | Type | Mean Error | Median | Range | Whitelist Impact | Auto-Candidates |
|----------|------|------------|--------|-------|------------------|-----------------|
| **Kant** | OCR scan | 4.0% | 3.1% | 0-18.6% | -1.6% | 26 |
| **Comay** | Born-digital | 7.2% | 5.1% | 0-41.0% | -1.9% | 14 |
| **Derrida W&D** | Born-digital | 4.6% | 3.7% | 0-26.6% | +2.4% | 11 |
| **Heidegger** | Mixed | 7.0% | 6.1% | 0-23.1% | **+13.3%** | 27 |
| **Lenin** | Scanned | 3.7% | 3.5% | 0-10.0% | 0% | 14 |
| **Derrida Margins** | Complex | 5.9% | 4.5% | 0-38.5% | **+9.6%** | 17 |

### Validated Settings

| Parameter | Tested Values | Optimal | Rationale |
|-----------|---------------|---------|-----------|
| **Sample size** | 25, 50, 100, 200 | **50** | Variance < 0.001, sufficient accuracy |
| **Philosophy whitelist** | with/without | **Required** | 13% error reduction for German texts |
| **Auto-whitelist threshold** | 3, 5, 10 | **5** | Balances coverage vs noise |

### Critical Finding: Use Percentile-Based Thresholds

**Problem:** Absolute thresholds don't generalize.
- Born-digital Comay: 7.2% error rate (French/Latin vocabulary)
- OCR'd Kant: 4.0% error rate (simpler vocabulary)

**Solution:** Use document-relative (percentile-based) thresholds:

```python
def calculate_dynamic_thresholds(page_error_rates: list[float]) -> dict:
    """Calculate document-specific thresholds from distribution."""
    return {
        "good": np.percentile(page_error_rates, 50),      # Median
        "marginal": np.percentile(page_error_rates, 75),  # 75th percentile
        "reocr": np.percentile(page_error_rates, 90),     # 90th percentile (outliers)
    }
```

This means: "Re-OCR the worst 10% of pages" rather than "Re-OCR pages above 5%".

---

## Ground Truth Protocol

### The Problem

We need to know which pages **actually** have OCR errors to validate our thresholds.
But manually reviewing every page is impractical.

### Solution: Zero False Negatives Pre-Filter

**Key insight:** Use an extremely conservative threshold to catch ALL potentially bad pages,
then manually review only that reduced set.

```
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: CONSERVATIVE PRE-FILTER                                    │
│  ──────────────────────────────────                                 │
│  Use threshold = 1% error rate (catches almost everything)         │
│  Result: ~80% of pages flagged, but ZERO false negatives           │
│                                                                     │
│  For 500-page book: ~400 pages flagged                              │
│  But this is still 400 pages to review manually...                  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2: STRATIFIED SAMPLING                                        │
│  ───────────────────────────────                                    │
│  Group flagged pages by error rate buckets:                         │
│    Bucket A: 1-3%   (likely fine)    → Sample 10%                   │
│    Bucket B: 3-5%   (probably fine)  → Sample 20%                   │
│    Bucket C: 5-10%  (marginal)       → Sample 50%                   │
│    Bucket D: 10%+   (likely bad)     → Review 100%                  │
│                                                                     │
│  For 400 flagged pages:                                             │
│    - Bucket A (200): sample 20 pages                                │
│    - Bucket B (120): sample 24 pages                                │
│    - Bucket C (60):  sample 30 pages                                │
│    - Bucket D (20):  review all 20 pages                            │
│  Total manual review: ~94 pages (19% of flagged, 19% of book)       │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 3: HUMAN REVIEW                                               │
│  ─────────────────────                                              │
│  For each sampled page, human marks:                                │
│    ✅ GOOD - No significant OCR errors                              │
│    ⚠️  MARGINAL - Minor errors, usable for RAG                      │
│    ❌ BAD - Significant errors, needs re-OCR                        │
│                                                                     │
│  Review criteria:                                                   │
│    - 3+ character-level errors in key terms → BAD                   │
│    - Misspelled proper nouns → BAD                                  │
│    - Only foreign terms flagged → GOOD (false alarm)                │
│    - Page numbers/headers garbled → MARGINAL                        │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 4: EXTRAPOLATE TO FULL DOCUMENT                               │
│  ─────────────────────────────────────                              │
│  From sampled results, estimate:                                    │
│    - What % of Bucket A are actually BAD?                           │
│    - What threshold captures 95% of BAD pages?                      │
│    - What's the expected precision/recall at each threshold?        │
└─────────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
def generate_ground_truth_review_list(
    pdf_path: Path,
    conservative_threshold: float = 0.01,  # 1% - catch everything
    bucket_sample_rates: dict = None,
) -> GroundTruthReviewList:
    """
    Generate a stratified sample of pages for manual ground truth review.

    Returns list of pages to review with expected effort estimate.
    """
    bucket_sample_rates = bucket_sample_rates or {
        (0.01, 0.03): 0.10,   # 1-3%: sample 10%
        (0.03, 0.05): 0.20,   # 3-5%: sample 20%
        (0.05, 0.10): 0.50,   # 5-10%: sample 50%
        (0.10, 1.00): 1.00,   # 10%+: review all
    }

    # Analyze all pages
    page_metrics = analyze_all_pages(pdf_path)

    # Bucket pages by error rate
    buckets = defaultdict(list)
    for page in page_metrics:
        if page.error_rate < conservative_threshold:
            continue  # Below threshold, assume good
        for (low, high), sample_rate in bucket_sample_rates.items():
            if low <= page.error_rate < high:
                buckets[(low, high)].append(page)
                break

    # Sample from each bucket
    review_pages = []
    for (low, high), pages in buckets.items():
        sample_rate = bucket_sample_rates[(low, high)]
        n_sample = max(1, int(len(pages) * sample_rate))
        sampled = random.sample(pages, min(n_sample, len(pages)))
        review_pages.extend(sampled)

    return GroundTruthReviewList(
        pages=review_pages,
        total_flagged=sum(len(p) for p in buckets.values()),
        buckets={k: len(v) for k, v in buckets.items()},
    )
```

### Review Interface Output

```
GROUND TRUTH REVIEW LIST: Kant_CritiqueOfJudgement.pdf
=========================================================

Pages flagged (>1% error): 348 of 685 (51%)
Pages to review: 87 (13% of book)

BUCKET A (1-3% error): 180 pages, reviewing 18
BUCKET B (3-5% error): 98 pages, reviewing 20
BUCKET C (5-10% error): 52 pages, reviewing 26
BUCKET D (10%+ error): 18 pages, reviewing 18 (all)

Estimated review time: 15-30 minutes

─────────────────────────────────────────────────────────
PAGE 47 (Bucket C, error rate: 7.2%)
─────────────────────────────────────────────────────────
Unknown words: beautlful, questlon, judg-ment, tbe

Sample text:
"The beautlful in nature concerns tbe form of the object,
which consists in [its] limitation. The sublime, on tbe
other hand, can also be found in a formless object..."

Mark: [G]ood / [M]arginal / [B]ad ? _
─────────────────────────────────────────────────────────
```

### Calculating Threshold Performance

After review, calculate metrics:

```python
def calculate_threshold_performance(
    ground_truth: list[tuple[int, str]],  # [(page_num, "GOOD"|"MARGINAL"|"BAD")]
    page_metrics: list[PageMetrics],
    test_thresholds: list[float] = [0.02, 0.03, 0.05, 0.07, 0.10],
) -> pd.DataFrame:
    """
    Calculate precision/recall/F1 for each threshold.

    "Positive" = page needs re-OCR (BAD in ground truth)
    "Negative" = page is fine (GOOD or MARGINAL)
    """
    results = []

    for threshold in test_thresholds:
        # Pages flagged at this threshold
        flagged = {p.page_num for p in page_metrics if p.error_rate > threshold}

        # Ground truth: which pages are actually BAD
        actually_bad = {page for page, label in ground_truth if label == "BAD"}
        actually_ok = {page for page, label in ground_truth if label != "BAD"}

        # Calculate metrics
        true_positives = len(flagged & actually_bad)
        false_positives = len(flagged & actually_ok)
        false_negatives = len(actually_bad - flagged)

        precision = true_positives / (true_positives + false_positives) if flagged else 0
        recall = true_positives / len(actually_bad) if actually_bad else 1.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        results.append({
            "threshold": threshold,
            "flagged": len(flagged),
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "false_negatives": false_negatives,
        })

    return pd.DataFrame(results)
```

### Expected Output

```
THRESHOLD PERFORMANCE (after ground truth review)
=================================================

Threshold   Flagged   Precision   Recall    F1      FN
──────────────────────────────────────────────────────
2%          320       0.15        1.00      0.26    0   ← Zero FN, but lots of wasted re-OCR
3%          258       0.19        1.00      0.32    0
5%          142       0.34        0.96      0.50    2   ← Good balance
7%          78        0.58        0.90      0.71    5
10%         35        0.80        0.70      0.74    15  ← High precision, but missing 30% of bad pages

RECOMMENDATION: Use 5% threshold
- Catches 96% of genuinely bad pages
- Only 2 false negatives (missed bad pages)
- 142 pages to re-OCR (21% of book) vs 348 at 1%
```

### Zero False Negatives Mode

For users who want maximum safety:

```python
def find_zero_fn_threshold(
    ground_truth: list[tuple[int, str]],
    page_metrics: list[PageMetrics],
) -> float:
    """Find the highest threshold that still catches ALL bad pages."""
    actually_bad = {page for page, label in ground_truth if label == "BAD"}

    # Try thresholds from high to low
    for threshold in [0.20, 0.15, 0.10, 0.07, 0.05, 0.03, 0.02, 0.01]:
        flagged = {p.page_num for p in page_metrics if p.error_rate > threshold}
        if actually_bad.issubset(flagged):
            return threshold

    return 0.01  # Fall back to most conservative
```

---

## Multi-Stage Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 1: INSTANT HEURISTICS (< 1ms/page)                           │
│  ─────────────────────────────────────────                          │
│  • Garbage character ratio > 1%?                                    │
│  • No text layer at all?                                            │
│  • Font count > 100? (OCR artifact signature)                       │
│                                                                     │
│  NOTE: Image presence does NOT predict OCR quality (empirically     │
│        validated - born-digital PDFs often have images too)         │
│                                                                     │
│  → PASS: Move to Stage 2                                            │
│  → FAIL (no text/garbage): Flag for re-OCR immediately              │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 2: SPELL-CHECK SAMPLING (~10ms/page)                         │
│  ───────────────────────────────────────────                        │
│  • Sample 50 words per page (empirically validated as sufficient)   │
│  • Check against spell-checker                                      │
│  • EXCLUDE: Profile whitelist + auto-detected terms                 │
│  • Calculate: error_rate = unknown / (total - excluded)             │
│                                                                     │
│  DYNAMIC THRESHOLDS (percentile-based):                             │
│  → Below 50th percentile: GOOD (use existing text)                  │
│  → 50th-75th percentile: MARGINAL (use existing, flag warning)      │
│  → Above 90th percentile: Flag for re-OCR (worst 10%)               │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 3: NEURAL OCR (0.6s/page GPU)                                │
│  ───────────────────────────────────                                │
│  • Only for flagged pages (typically 5-15% of scanned docs)         │
│  • docTR with GPU acceleration                                      │
│  • Replace existing text layer for these pages only                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Efficiency Gains

| Document Type | Pages | Stage 1 | Stage 2 | Stage 3 | Total Time |
|--------------|-------|---------|---------|---------|------------|
| Born-digital | 500 | 500 pass | 500 pass | 0 | ~5 seconds |
| Good scan | 500 | 500 pass | 480 pass, 20 flag | 20 re-OCR | ~17 seconds |
| Poor scan | 500 | 500 pass | 100 pass, 400 flag | 400 re-OCR | ~4.5 minutes |
| No OCR | 500 | 500 fail | skip | 500 re-OCR | ~5.5 minutes |

**Savings:** For a typical mixed-quality 500-page book with 10% bad pages:
- Without filtering: 5 minutes (all pages re-OCR'd)
- With filtering: 35 seconds (only 50 pages re-OCR'd)

---

## Profile System

### Built-in Profiles

```python
@dataclass
class QualityProfile:
    """Domain-specific configuration for quality filtering."""

    name: str

    # Words to EXCLUDE from error counting (not errors for this domain)
    vocabulary_whitelist: set[str]

    # Patterns to exclude (regex)
    exclude_patterns: list[str]

    # Thresholds (domain may tolerate more "unknown" words)
    error_threshold_good: float = 0.02      # Below this = good
    error_threshold_marginal: float = 0.05  # Below this = marginal

    # Auto-detection hints
    detection_keywords: set[str]  # If found, suggest this profile


# Built-in profiles
PROFILES = {
    "philosophy": QualityProfile(
        name="philosophy",
        vocabulary_whitelist={
            # German phenomenology
            "dasein", "sein", "seiendes", "zeitlichkeit", "aufhebung",
            "sorge", "mitsein", "zuhandenheit", "vorhandenheit", "lebenswelt",
            # Greek terms
            "logos", "physis", "aletheia", "eidos", "nous", "telos",
            "aporia", "ousia", "techne", "episteme", "phronesis", "praxis",
            # French theory
            "differance", "jouissance", "ecriture", "arche", "bricolage",
            # Adjective forms
            "heideggerian", "husserlian", "derridean", "foucauldian",
            "deleuzian", "nietzschean", "kantian", "hegelian",
            # Technical terms
            "phenomenological", "hermeneutic", "ontological", "epistemological",
            "apophantic", "noematic", "eidetic", "hyletic", "noetic",
            # Common philosopher names (lowercase in possessives)
            "heidegger", "husserl", "derrida", "levinas", "merleau",
            "gadamer", "ricoeur", "sartre", "foucault", "deleuze",
        },
        exclude_patterns=[
            r"p+\.\s*\d+",      # Page references
            r"\(\d{4}\)",       # Year citations
            r"[ivxlc]+",        # Roman numerals (case insensitive)
        ],
        detection_keywords={"phenomenology", "ontology", "hermeneutic", "dasein"},
    ),

    "linguistics": QualityProfile(
        name="linguistics",
        vocabulary_whitelist={
            # Grammatical abbreviations
            "nom", "acc", "dat", "gen", "abl", "voc",
            "sg", "pl", "pst", "prs", "fut", "perf",
            "masc", "fem", "neut",
            # IPA and phonology (will appear as unknown)
            "phoneme", "allophone", "morpheme", "lexeme",
        },
        exclude_patterns=[
            r"/[^/]+/",         # Phonemic transcription
            r"\[[^\]]+\]",      # Phonetic transcription
            r"\w+-\w+",         # Morpheme glosses
        ],
        detection_keywords={"phoneme", "morpheme", "syntax", "phonology"},
    ),

    "generic": QualityProfile(
        name="generic",
        vocabulary_whitelist=set(),  # Minimal
        exclude_patterns=[],
        error_threshold_good=0.03,    # Slightly more tolerant
        error_threshold_marginal=0.07,
    ),
}
```

### Profile Selection

```python
def select_profile(doc, user_profile=None) -> QualityProfile:
    """Select quality profile - explicit, auto-detected, or generic."""

    # 1. User explicitly specified
    if user_profile:
        return PROFILES.get(user_profile, PROFILES["generic"])

    # 2. Auto-detect from content
    sample_text = extract_sample(doc, pages=5)

    for name, profile in PROFILES.items():
        if name == "generic":
            continue
        keyword_matches = sum(1 for kw in profile.detection_keywords
                             if kw.lower() in sample_text.lower())
        if keyword_matches >= 2:
            return profile

    # 3. Fall back to generic
    return PROFILES["generic"]
```

---

## Automated Whitelist Building

### The Frequency Heuristic

If a word appears many times in a document and is always flagged as "unknown", it's probably a valid term, not an OCR error.

```python
def build_document_whitelist(doc, base_profile: QualityProfile) -> set[str]:
    """
    Automatically extend whitelist based on document content.

    Heuristic: Words that appear 5+ times and are consistently
    "unknown" are probably valid terms, not errors.
    """
    from collections import Counter
    from spellchecker import SpellChecker

    spell = SpellChecker()
    word_counts = Counter()
    unknown_counts = Counter()

    # First pass: count all words
    for page in doc.pages:
        words = extract_words(page.text)
        for word in words:
            clean = word.lower().strip(".,;:!?\"'()")
            if len(clean) < 3:
                continue
            word_counts[clean] += 1
            if clean not in spell and clean not in base_profile.vocabulary_whitelist:
                unknown_counts[clean] += 1

    # Build auto-whitelist
    auto_whitelist = set()
    for word, count in unknown_counts.items():
        total = word_counts[word]
        # Word appears 5+ times and is ALWAYS unknown
        if total >= 5 and count == total:
            # Additional check: not an OCR pattern
            if not looks_like_ocr_error(word):
                auto_whitelist.add(word)

    return auto_whitelist


def looks_like_ocr_error(word: str) -> bool:
    """
    Heuristic: Does this look like an OCR error rather than a real word?
    """
    # Common OCR confusion patterns
    ocr_patterns = [
        r"rn",       # rn often misread as m
        r"[0-9]",    # Mixed numbers in words
        r"l1I",      # l/1/I confusion
        r"(.)\1{3,}", # Same char repeated 4+ times
    ]

    import re
    for pattern in ocr_patterns:
        if re.search(pattern, word):
            return True

    # Unusual character sequences
    if re.search(r"[^aeiou]{5,}", word.lower()):  # 5+ consonants
        return True

    return False
```

### Example Auto-Detection

```
Document: "Being and Time" (Heidegger translation)

Spell-checker flags as unknown:
  - "Dasein" (appears 847 times) → AUTO-WHITELIST ✓
  - "Zuhandenheit" (appears 52 times) → AUTO-WHITELIST ✓
  - "temporalität" (appears 31 times) → AUTO-WHITELIST ✓
  - "beautlful" (appears 1 time) → NOT whitelisted (low frequency)
  - "tbe" (appears 3 times) → NOT whitelisted (has OCR pattern)

Result: These 3 terms added to document-specific whitelist,
        reducing false "error" count for quality scoring.
```

---

## User Perspectives

### 1. Scholar (Domain Expert)

**Need:** Process philosophy texts accurately with minimal config

```python
# Explicit profile selection
doc = load("being_and_time.pdf", profile="philosophy")

# High-quality output, philosophy terms preserved
```

**Experience:**
- Selects their domain profile once
- System respects their vocabulary
- Rare false positives in quality scoring

### 2. Student (Reading Selection)

**Need:** Just works, no configuration required

```python
# Zero config - auto-detection kicks in
doc = load("heidegger_excerpt.pdf")

# System auto-detects philosophy content
# Auto-builds whitelist from frequent terms
```

**Experience:**
- No profile selection needed
- System figures it out from content
- Good enough quality without tuning

### 3. Librarian (Bulk Processing)

**Need:** Process 1000s of PDFs with consistent quality, no per-document config

```python
# Batch processing with auto-detection
for pdf in library_collection:
    doc = load(pdf, profile="auto")  # Auto-detect per document
    chunks = doc.to_rag_chunks()
    store(chunks)
```

**Experience:**
- Set and forget
- Auto-detection handles mixed domains
- Quality scores flag documents needing review
- Processing log shows what was done

### 4. Power User (Custom Domain)

**Need:** Process medieval Latin manuscripts with custom vocabulary

```python
# Create custom profile
medieval_latin = QualityProfile(
    name="medieval_latin",
    vocabulary_whitelist={
        "quod", "enim", "autem", "ergo", "igitur",
        "praedicatur", "subiectum", "universale",
        # ... hundreds more
    },
    exclude_patterns=[
        r"f\.\s*\d+[rv]",  # Folio references (f. 23r)
    ],
    detection_keywords={"quod", "praedicatur", "universale"},
)

# Register and use
register_profile(medieval_latin)
doc = load("aquinas_manuscript.pdf", profile="medieval_latin")
```

**Experience:**
- Full control over vocabulary
- Can share profile with colleagues
- Consistent processing for their niche

---

## Configuration API

```python
@dataclass
class QualityConfig:
    """Configuration for quality filtering."""

    # Profile selection
    profile: str | QualityProfile = "auto"  # "auto", "philosophy", "generic", or custom

    # Auto-detection settings
    auto_detect_profile: bool = True      # Try to detect domain from content
    auto_build_whitelist: bool = True     # Learn terms from document frequency
    auto_whitelist_threshold: int = 5     # Min occurrences to auto-whitelist

    # Stage 1 thresholds
    garbage_char_threshold: float = 0.01  # Flag if > 1% garbage chars
    max_fonts_normal: int = 100           # Above this suggests OCR

    # Stage 2 thresholds (can be overridden by profile)
    error_threshold_good: float = 0.02
    error_threshold_marginal: float = 0.05
    sample_words_per_page: int = 100

    # Stage 3 settings
    reocr_engine: Literal["doctr", "tesseract"] = "doctr"
    use_gpu: bool = True


# Usage examples
doc = load("kant.pdf")  # Full auto mode

doc = load("kant.pdf", quality=QualityConfig(
    profile="philosophy",
    auto_build_whitelist=True,
))

doc = load("kant.pdf", quality=QualityConfig(
    profile="generic",
    auto_detect_profile=False,
    auto_build_whitelist=False,  # Strict mode, no learning
))
```

---

---

## Adaptive Profiles (Warm-Start + Learning)

### The Idea

Profiles aren't static - they evolve with usage:

```
┌─────────────────────────────────────────────────────────────────────┐
│  BASE PROFILE (Preset)                                              │
│  ─────────────────────                                              │
│  philosophy: {dasein, aufhebung, différance, ...}                   │
│                          │                                          │
│                          ▼                                          │
│  PROCESS DOCUMENT 1: "Being and Time"                               │
│  ─────────────────────────────────────                              │
│  Auto-learns: {zuhandenheit, vorhandenheit, temporalität}           │
│                          │                                          │
│                          ▼                                          │
│  PROCESS DOCUMENT 2: "Of Grammatology"                              │
│  ─────────────────────────────────────                              │
│  Auto-learns: {arche-writing, logocentrism, phonocentrism}          │
│                          │                                          │
│                          ▼                                          │
│  EVOLVED PROFILE                                                    │
│  ───────────────                                                    │
│  philosophy: {dasein, aufhebung, différance, zuhandenheit,          │
│               vorhandenheit, temporalität, arche-writing,           │
│               logocentrism, phonocentrism, ...}                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
@dataclass
class AdaptiveProfile:
    """A profile that learns from documents it processes."""

    # Base configuration (immutable)
    base: QualityProfile

    # Learned terms (grows over time)
    learned_terms: set[str] = field(default_factory=set)

    # Learning metadata
    documents_processed: int = 0
    last_updated: datetime | None = None

    # Persistence
    storage_path: Path | None = None  # Where to save learned terms

    @property
    def vocabulary_whitelist(self) -> set[str]:
        """Combined base + learned vocabulary."""
        return self.base.vocabulary_whitelist | self.learned_terms

    def learn_from_document(self, doc: ScholarDocument, min_occurrences: int = 5):
        """
        Add frequently-occurring unknown terms to learned vocabulary.
        """
        new_terms = build_document_whitelist(doc, self)

        # Add to learned terms
        self.learned_terms |= new_terms
        self.documents_processed += 1
        self.last_updated = datetime.now()

        # Persist if storage configured
        if self.storage_path:
            self.save()

        return new_terms  # Return what was learned (for logging)

    def save(self):
        """Persist learned terms to disk."""
        data = {
            "base_profile": self.base.name,
            "learned_terms": sorted(self.learned_terms),
            "documents_processed": self.documents_processed,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }
        self.storage_path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> "AdaptiveProfile":
        """Load a saved adaptive profile."""
        data = json.loads(path.read_text())
        base = PROFILES[data["base_profile"]]
        return cls(
            base=base,
            learned_terms=set(data["learned_terms"]),
            documents_processed=data["documents_processed"],
            last_updated=datetime.fromisoformat(data["last_updated"]) if data["last_updated"] else None,
            storage_path=path,
        )
```

### Usage Patterns

#### Pattern 1: Personal Evolving Profile

```python
# First use - create from base
my_profile = AdaptiveProfile(
    base=PROFILES["philosophy"],
    storage_path=Path("~/.scholardoc/my_philosophy_profile.json")
)

# Process documents - profile learns
doc1 = load("being_and_time.pdf", profile=my_profile)
# Learns: zuhandenheit, vorhandenheit, befindlichkeit

doc2 = load("of_grammatology.pdf", profile=my_profile)
# Learns: arche-writing, phonocentrism, grammatology

doc3 = load("totality_and_infinity.pdf", profile=my_profile)
# Learns: illeity, fecundity, eschatology

# Later session - load evolved profile
my_profile = AdaptiveProfile.load(Path("~/.scholardoc/my_philosophy_profile.json"))
# Now has 150+ learned terms from previous processing
```

#### Pattern 2: Institutional Shared Profile

```python
# Library creates shared profile
library_philosophy = AdaptiveProfile(
    base=PROFILES["philosophy"],
    storage_path=Path("/shared/profiles/continental_philosophy.json")
)

# Multiple librarians process books
# Profile evolves with the collection
for pdf in philosophy_collection:
    doc = load(pdf, profile=library_philosophy)
    # Each book contributes learned terms

# Eventually: comprehensive vocabulary for that collection
# New books process faster (fewer false "errors")
```

#### Pattern 3: Project-Specific Profile

```python
# Dissertation on Heidegger
heidegger_project = AdaptiveProfile(
    base=PROFILES["philosophy"],
    storage_path=Path("./project/heidegger_profile.json")
)

# Process primary sources
for pdf in heidegger_primary_sources:
    load(pdf, profile=heidegger_project)

# Process secondary literature
for pdf in heidegger_secondary_literature:
    load(pdf, profile=heidegger_project)

# Profile now specialized for Heidegger scholarship
# Knows: seinsfrage, seinsgeschichte, ereignis, geviert, ...
```

### Profile Lifecycle

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   CREATE     │────▶│   EVOLVE     │────▶│   MATURE     │
│              │     │              │     │              │
│ Start from   │     │ Learn from   │     │ Stable, few  │
│ base profile │     │ each doc     │     │ new terms    │
└──────────────┘     └──────────────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   SHARE      │
                    │              │
                    │ Export for   │
                    │ colleagues   │
                    └──────────────┘
```

### Learning Controls

```python
@dataclass
class LearningConfig:
    """Control how profiles learn."""

    # Whether to learn at all
    enabled: bool = True

    # Minimum occurrences to add a term
    min_occurrences: int = 5

    # Maximum terms to learn per document (prevent noise)
    max_terms_per_doc: int = 50

    # Require term to appear across multiple pages
    min_pages: int = 2

    # Filter out likely OCR errors
    filter_ocr_patterns: bool = True

    # Filter out very short terms (likely abbreviations)
    min_term_length: int = 4

    # Persist after each document or batch
    persist_frequency: Literal["document", "batch", "manual"] = "document"


# Usage
my_profile = AdaptiveProfile(
    base=PROFILES["philosophy"],
    storage_path=Path("./my_profile.json"),
)

doc = load("kant.pdf", profile=my_profile, learning=LearningConfig(
    min_occurrences=10,       # More conservative
    max_terms_per_doc=20,     # Limit noise
    persist_frequency="batch", # Don't save every doc
))
```

### Export and Sharing

```python
# Export learned terms for sharing
my_profile.export_learned_terms("learned_continental_philosophy.txt")

# Colleague imports your learned terms
colleague_profile = AdaptiveProfile(base=PROFILES["philosophy"])
colleague_profile.import_terms("learned_continental_philosophy.txt")

# Or: propose additions to base profile
my_profile.propose_base_additions(min_documents=3)
# Returns terms that appeared in 3+ documents
# → Could be added to official philosophy profile
```

### Quality Safeguards

```python
def should_learn_term(term: str, occurrences: int, config: LearningConfig) -> bool:
    """Decide if a term should be added to learned vocabulary."""

    # Basic thresholds
    if occurrences < config.min_occurrences:
        return False
    if len(term) < config.min_term_length:
        return False

    # Filter OCR patterns
    if config.filter_ocr_patterns and looks_like_ocr_error(term):
        return False

    # Filter unlikely vocabulary
    if term.isdigit():
        return False
    if not term.isalpha():  # Has punctuation/numbers
        return False

    # Filter very common words that might be misspelled variants
    if term.lower() in {"tbe", "tlie", "tliis", "wliich"}:  # Common OCR errors
        return False

    return True
```

---

## Complete Example: Student Workflow

```python
# Student gets reading list for "Continental Philosophy 101"
readings = [
    "heidegger_being_and_time_excerpt.pdf",
    "derrida_structure_sign_play.pdf",
    "levinas_totality_infinity_preface.pdf",
    "merleau_ponty_phenomenology_perception_intro.pdf",
]

# Create evolving profile for the course
course_profile = AdaptiveProfile(
    base=PROFILES["philosophy"],  # Warm start
    storage_path=Path("./continental_101_profile.json"),
)

# Process readings - profile learns along the way
for pdf in readings:
    doc = load(pdf, profile=course_profile)

    # First reading: learns Heideggerian terms
    # Second reading: learns Derridean terms
    # etc.

    chunks = doc.to_rag_chunks()
    store_for_rag(chunks)

# By end of semester:
print(f"Profile learned {len(course_profile.learned_terms)} terms")
print(f"From {course_profile.documents_processed} documents")

# Profile now excellent for continental philosophy
# Future processing is faster and more accurate
```

---

## Summary

| Feature | Benefit |
|---------|---------|
| **Multi-stage filtering** | 10x faster than blanket re-OCR |
| **Spell-check as filter** | Safe (no corrections), efficient flagging |
| **Profile whitelists** | Domain experts get accurate quality scores |
| **Auto-detection** | Students/general users need no config |
| **Auto-whitelist building** | Handles unknown terms in any domain |
| **Adaptive profiles** | Learn and improve over time |
| **Warm-start + learning** | Best of both: expertise + adaptation |
| **Shareable profiles** | Colleagues benefit from each other's processing |
| **Processing log** | Transparency about what was done |

**Key insight:** Spell-check is dangerous for *correction* but safe for *filtering*. The downside of a false positive (flagging a good page for re-OCR) is just wasted compute, not damaged text.

**Bonus insight:** Profiles that learn create a virtuous cycle - the more you process, the better future processing becomes.
