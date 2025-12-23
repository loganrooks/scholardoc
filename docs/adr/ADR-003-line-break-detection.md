# ADR-003: Line-Break Hyphenation Detection

**Status:** VALIDATED - Based on spike testing
**Date:** December 2025
**Validation:** `spikes/29_ocr_pipeline_design.py`

---

## Context

Scholarly PDFs frequently contain hyphenated words split across line breaks. When text is extracted, these appear as:
- `pheno-` on one line
- `menon` on the next line

These need to be rejoined to `phenomenon` for proper text processing. However, we must distinguish:
- **Real hyphenation:** Word split for line wrapping → rejoin
- **Compound words:** `self-evident`, `well-known` → keep hyphen
- **Margin content:** Page numbers, headers that happen to follow hyphenated text → don't join

**Problem found:** Initial implementation incorrectly matched margin content (e.g., `meta-` + `a x` where "a x" is a page marker in roman numerals).

---

## Options Considered

### Option 1: Regex-Based Detection

**Description:** Use patterns like `\w+-\n\w+` to find hyphenated line breaks.

**Pros:**
- Simple implementation
- Fast processing
- No PDF structure needed

**Cons:**
- Can't distinguish line-end from mid-line hyphens
- Matches compound words incorrectly
- No way to filter margin content
- High false positive rate

**Verdict:** Rejected - Too imprecise

### Option 2: Dictionary-Only Validation

**Description:** Try joining and check if result is a valid word.

**Pros:**
- High precision when word is known
- No position data needed

**Cons:**
- Fails on specialized vocabulary
- Can't handle words not in dictionary
- Still matches margin content

**Verdict:** Rejected - Dictionary coverage insufficient

### Option 3: Position-Based with Block Filtering (Chosen)

**Description:** Use PyMuPDF position data to detect hyphen at line end, with block number filtering to exclude margin content.

**Pros:**
- Uses actual PDF layout information
- Block filtering prevents margin matches
- Dictionary validation for confidence
- Can learn unknown words

**Cons:**
- Requires PyMuPDF (not pure Python)
- More complex implementation
- Depends on PDF structure quality

**Verdict:** Selected - Most accurate approach

---

## Decision

### Algorithm

```python
def detect_line_breaks(page):
    words = page.get_text("words")
    # Format: (x0, y0, x1, y1, text, block_no, line_no, word_no)

    # Group by (block, line)
    lines = group_by_block_and_line(words)

    # Sort by block, then y-position
    sorted_lines = sort_by_block_then_position(lines)

    candidates = []
    prev_line, prev_block = None, None

    for (block, line_no), line_words in sorted_lines:
        if prev_line and line_words:
            # CRITICAL: Only if SAME block
            if prev_block == block:
                last_word = prev_line[-1]['text']
                first_word = line_words[0]['text']

                if last_word.endswith('-') and len(last_word) > 2:
                    candidate = evaluate_join(last_word, first_word)
                    candidates.append(candidate)

        prev_line = line_words
        prev_block = block

    return candidates
```

### Block Filtering Rationale

PyMuPDF assigns block numbers to distinct text regions:
- Main body text: typically blocks 0-3
- Margin content: separate blocks (headers, footers, page numbers)

**Example of prevented false match:**
```
Block 2, Line 5: "...metaphysics and meta-"
Block 4, Line 1: "a x"  ← Page marker "a x" (roman numeral)
```

Without block filtering: `meta-` + `a x` → incorrectly attempted join
With block filtering: Different blocks, no join attempted

### Validation Logic

When considering a join:

1. **Strip hyphen:** `pheno-` → `pheno`
2. **Strip punctuation:** `menon.` → `menon`
3. **Join:** `pheno` + `menon` → `phenomenon`
4. **Validate:**
   - Direct dictionary lookup
   - Morphological check (base forms)
   - Pattern check (has vowels, reasonable length)
5. **If valid:** Join and learn word
6. **If position-strong but validation weak:** Join anyway (position signal is strong)
7. **If neither:** Don't join

---

## Consequences

### Positive
- Correctly handles line-break hyphenation
- Filters out margin content (page markers, headers)
- Learns specialized vocabulary for future detection
- High precision on validated test set

### Negative
- Requires PyMuPDF position data
- Block structure must be reliable in PDF
- More complex than simple regex

### Mitigations
- Fall back to regex if position data unavailable
- Validate joins before accepting
- Log rejected candidates for debugging

---

## Test Results

**Before fix (no block filtering):**
- `meta-` + `a x` → Incorrectly attempted join
- `with-` + `a xi` → Incorrectly attempted join

**After fix (with block filtering):**
- Both cases correctly filtered (different blocks)
- Only same-block line breaks considered

**On Heidegger Being and Time (50 pages):**
- Valid joins: 1 (`func-` + `tion.` → `function`)
- Correctly rejected: 4 (page references like `know-8`)

---

## Implementation

See `spikes/29_ocr_pipeline_design.py`:
- `LineBreakRejoiner` class
- `detect_from_pdf_page()` method with block filtering
- `_evaluate_join()` method with validation logic

---

## References

- PyMuPDF `get_text("words")` documentation
- Spike 29: OCR pipeline design
- Ground truth testing on Heidegger, Kant, Derrida texts
