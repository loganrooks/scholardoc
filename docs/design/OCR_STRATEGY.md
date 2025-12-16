# OCR Strategy for ScholarDoc

> **Purpose:** Design OCR correction and custom OCR approaches for scholarly PDFs
> **Status:** DRAFT
> **Created:** December 15, 2025

---

## Context

**Problem:** OCR character errors significantly degrade embedding similarity (see Spike 08).
- 5% character error rate → 0.65 cosine similarity (below usable threshold)
- Single-word errors like "Beautlful"→"Beautiful" drop similarity to 0.515
- Kant PDF has ~1.6% word error rate with 4,428 suspicious words

**Goal:** Improve OCR quality to maintain embedding similarity >0.9 for RAG applications.

---

## Option 1: OCR Post-Correction (Recommended for Phase 1)

### Approach

Add a correction layer after extracting text from existing PDF text layers.

```
PDF → PyMuPDF extraction → Error Detection → Correction → Clean text
```

### Correction Methods (Simplest to Most Complex)

#### 1A. Rule-Based Correction
**Effort:** Low (days)
**Accuracy:** Limited

```python
# Common OCR substitution patterns
CORRECTIONS = {
    'tl': 'ti',  # "beautlful" → "beautiful"
    'rn': 'm',   # "rnorning" → "morning"
    '0': 'O',    # context-dependent
    '1': 'l',    # context-dependent
}
```

**Pros:** Fast, predictable, no dependencies
**Cons:** Limited scope, can introduce errors, needs extensive pattern library

#### 1B. Spell Checker (Dictionary-Based)
**Effort:** Low (days)
**Accuracy:** Moderate

Libraries:
- [pyspellchecker](https://pypi.org/project/pyspellchecker/) - simple frequency-based
- [SymSpell](https://github.com/wolfgarbe/SymSpell) - fast, handles multi-edit errors
- [hunspell](https://github.com/hunspell/hunspell) - used by LibreOffice/Firefox

```python
from spellchecker import SpellChecker
spell = SpellChecker()
corrected = spell.correction("beautlful")  # "beautiful"
```

**Pros:** Fast, no GPU needed, handles standard errors
**Cons:** No context awareness, fails on proper nouns, philosophy terms

#### 1C. Contextual Spell Checker (BERT-Based)
**Effort:** Medium (weeks)
**Accuracy:** Good

Libraries:
- [OCRfixr](https://pypi.org/project/OCRfixr/) - BERT-based, designed for OCR
- [NeuSpell](https://pypi.org/project/neuspell/) - EMNLP 2020, HuggingFace model
- [Spark NLP ContextSpellChecker](https://www.johnsnowlabs.com/easily-correcting-typos-and-spelling-errors-on-texts-with-spark-nlp-and-python/)

```python
from ocrfixr import spellcheck
text = "The beautlful is that which pleases"
result = spellcheck(text).fix()  # "The beautiful is that which pleases"
```

**Pros:** Context-aware, handles ambiguous corrections better
**Cons:** Slower, requires model download (~400MB), may overcorrect

#### 1D. LLM-Based Correction
**Effort:** Medium (weeks)
**Accuracy:** Best (but risky)

Use GPT-4, Claude, or local LLMs (Llama) to correct OCR errors.

Research shows:
- [GPT models improve CER by 18-39%](https://dl.acm.org/doi/10.1145/3685650.3685669) on historical texts
- **Risk:** LLMs can hallucinate new text not in original

```python
prompt = """Fix OCR errors in this text. Only fix obvious character errors.
Do not add, remove, or rephrase any content.

Text: The beautlful is that whlch pleases unlversally

Corrected:"""
```

**Pros:** Best at understanding context, handles edge cases
**Cons:** Hallucination risk, cost, latency, requires careful prompting

### Recommended Phase 1 Approach

```
1. Dictionary spell check (fast, catches 60-70% of errors)
2. OCRfixr for remaining uncertain words (BERT context)
3. Flag low-confidence corrections for human review
```

---

## Option 2: Re-OCR with Better Engines

### Approach

Extract page images from PDF and run through better OCR engine.

```
PDF → Page images → Modern OCR engine → New text layer
```

### OCR Engine Comparison

| Engine | Accuracy | Speed | Languages | Training | Best For |
|--------|----------|-------|-----------|----------|----------|
| **Tesseract 5** | 95-98% (clean) | Fast (CPU) | 100+ | Hard | Printed text |
| **EasyOCR** | Good | Fast (GPU) | 80+ | Easy | Receipts, multi-line |
| **TrOCR** | Best | Fast (GPU) | English | HuggingFace | Handwritten, complex |
| **PaddleOCR** | Good | Fast | Chinese focus | Medium | Asian languages |
| **Google Vision** | Excellent | API | 100+ | N/A | Cloud, production |
| **AWS Textract** | Excellent | API | Limited | N/A | Documents, forms |

### For Philosophy Texts Specifically

**Challenges:**
- Greek characters (αβγδ, etc.)
- German umlauts (ü, ö, ä)
- Special typography in older texts
- Footnote markers and superscripts
- Mixed fonts

**Recommended:** TrOCR or fine-tuned Tesseract

---

## Option 3: Custom OCR (Fine-Tuning)

### What's Involved

#### Requirements

1. **Training Data**
   - Pairs of (page image, correct text)
   - Need 1,000-10,000+ examples for good results
   - Ground truth must be manually verified

2. **Compute**
   - GPU required (RTX 3080+ recommended)
   - Fine-tuning TrOCR: 4-8 hours on good GPU
   - Full training: days to weeks

3. **Tools**
   - HuggingFace Transformers
   - PyTorch
   - TrOCR base model (`microsoft/trocr-base-printed`)

#### Fine-Tuning TrOCR (Easiest Custom Approach)

```python
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from transformers import Trainer, TrainingArguments

# Load pre-trained model
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-printed")

# Prepare dataset
# Each example: {"image": PIL.Image, "text": "ground truth text"}
train_dataset = load_my_dataset()

# Fine-tune
training_args = TrainingArguments(
    output_dir="./trocr-philosophy",
    num_train_epochs=10,
    per_device_train_batch_size=8,
    learning_rate=5e-5,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
)
trainer.train()
```

#### Expected Results

From research:
- [TrOCR fine-tuned on 495 pages](https://arxiv.org/html/2508.11499v1): CER 1.83%, WER 7.82%
- [16th-century manuscript](https://link.springer.com/chapter/10.1007/978-3-031-41685-9_16): CER improved from 3.0% to 1.6%
- Fine-tuning generally achieves 30-50% error reduction

### Full Custom Training (Most Effort)

Only consider if:
- Fine-tuning doesn't achieve target accuracy
- Unique script/language not covered by existing models
- Very large document corpus justifies investment

Requirements:
- 50,000+ training examples
- Multiple GPUs, weeks of training
- ML engineering expertise
- Continuous iteration and evaluation

---

## Recommendation

### Phase 1 (Immediate)

1. **Add error detection** to pipeline
   - Flag documents with high error rates
   - Provide quality score to users

2. **Add dictionary spell check**
   - Fast, catches obvious errors
   - Low risk of introducing new errors

3. **Integrate OCRfixr** for contextual correction
   - BERT-based, good accuracy
   - Reasonable speed

### Phase 2 (Medium-term)

4. **Re-OCR scanned documents** with TrOCR
   - Better baseline than Adobe Paper Capture
   - One-time processing per document

5. **Build ground truth corpus**
   - Manual verification of 100-500 pages
   - Enables accuracy measurement

### Phase 3 (Long-term, if needed)

6. **Fine-tune TrOCR** on philosophy texts
   - If Phase 2 doesn't achieve >95% accuracy
   - Requires ground truth corpus from Phase 2

---

## Decision Matrix

| Approach | Effort | Accuracy Gain | Risk | When to Use |
|----------|--------|---------------|------|-------------|
| Rule-based | Days | 10-20% | Low | Quick wins |
| Spell check | Days | 30-50% | Low | Standard errors |
| OCRfixr (BERT) | Weeks | 50-70% | Medium | Context-dependent |
| LLM correction | Weeks | 70-90% | High | Complex cases |
| Re-OCR (TrOCR) | Weeks | 60-80% | Low | Bad source OCR |
| Fine-tune TrOCR | Months | 80-95% | Medium | Specific domains |
| Full custom | 6+ months | Variable | High | Unique requirements |

---

## Implementation Plan

### Sprint 1: Detection + Simple Correction
```
[ ] Add OCR quality scoring to extraction
[ ] Integrate pyspellchecker for basic correction
[ ] Add "quality_score" field to document metadata
[ ] Flag documents below quality threshold
```

### Sprint 2: Contextual Correction
```
[ ] Integrate OCRfixr for BERT-based correction
[ ] Add confidence scores to corrections
[ ] Create review queue for low-confidence fixes
[ ] Benchmark accuracy improvement
```

### Sprint 3: Re-OCR Pipeline (Optional)
```
[ ] Add image extraction from PDF pages
[ ] Integrate TrOCR for re-OCR
[ ] Compare new vs original text layers
[ ] Use best version per page
```

---

## References

### OCR Post-Correction
- [GPT for OCR correction (ACM 2024)](https://dl.acm.org/doi/10.1145/3685650.3685669)
- [Synthetic data for post-OCR (arXiv 2024)](https://arxiv.org/html/2408.02253v1)
- [OCRfixr on PyPI](https://pypi.org/project/OCRfixr/)
- [NeuSpell (EMNLP 2020)](https://pypi.org/project/neuspell/)

### Custom OCR
- [TrOCR overview (Medium)](https://medium.com/@tejpal.abhyuday/trocr-transformer-based-optical-recognition-model-811f7b3217da)
- [Fine-tuning TrOCR (HuggingFace)](https://discuss.huggingface.co/t/fine-tuning-trocr-on-custom-dataset/39108)
- [Historical HTR with transformers (Springer)](https://link.springer.com/chapter/10.1007/978-3-031-41685-9_16)
- [LLMs for historical OCR (arXiv 2025)](https://arxiv.org/html/2510.06743v1)

### OCR Engine Comparisons
- [TrOCR vs Tesseract](https://mljourney.com/trocr-vs-tesseract-comparison-of-ocr-tools-for-modern-applications/)
- [OCR comparison (Medium)](https://toon-beerten.medium.com/ocr-comparison-tesseract-versus-easyocr-vs-paddleocr-vs-mmocr-a362d9c79e66)
- [Best OCR models (Roboflow)](https://blog.roboflow.com/best-ocr-models-text-recognition/)
